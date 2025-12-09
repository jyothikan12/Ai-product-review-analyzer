import os
import re
import time
import requests
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient, errors
from dotenv import load_dotenv

# -----------------------------------
# 1️⃣ Setup
# -----------------------------------
load_dotenv()

BESTBUY_API_KEY = os.getenv("BESTBUY_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")


# ✅ Unified DB + Collection (Same as eBay + NLP Utils)
MONGO_DB = "review_system"
MONGO_COLLECTION = "reviews_raw"

API_BASE = "https://api.bestbuy.com/v1/reviews"

# -----------------------------------
# 2️⃣ MongoDB Helper
# -----------------------------------
def get_mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    col = db[MONGO_COLLECTION]

    # ✅ Safe index for faster lookups
    col.create_index([("product_id", 1)], name="product_id_index")
    return col

# -----------------------------------
# 3️⃣ SKU Extractor
# -----------------------------------
def extract_sku(url_or_sku: str) -> str:
    """Attempt to extract a BestBuy SKU from:
    - Direct numeric input (6–8 digits)
    - URL query parameter skuId=1234567
    - URL path segment ending with /1234567.p
    - Legacy pattern /sku/1234567
    Raises ValueError if no SKU can be found.
    """
    raw = (url_or_sku or "").strip()
    if not raw:
        raise ValueError("❌ Empty input. Provide a BestBuy product URL or SKU number.")

    # Direct numeric SKU
    if re.fullmatch(r"\d{6,8}", raw):
        return raw

    # Parse URL components
    try:
        parsed = urlparse(raw)
        # Query param skuId
        qs = parse_qs(parsed.query)
        if "skuId" in qs and qs["skuId"]:
            candidate = qs["skuId"][0]
            if re.fullmatch(r"\d{6,8}", candidate):
                return candidate
        # Path pattern /1234567.p
        path_match = re.search(r"/(\d{6,8})\.p", parsed.path)
        if path_match:
            return path_match.group(1)
    except Exception:
        # If urlparse fails, continue to regex attempts below
        pass

    # Legacy /sku/1234567 pattern
    legacy_match = re.search(r"/sku/(\d{6,8})", raw)
    if legacy_match:
        return legacy_match.group(1)

    raise ValueError("❌ Could not extract SKU. Provide a BestBuy URL containing skuId= or /<digits>.p or a raw numeric SKU.")

# -----------------------------------
# 4️⃣ Fetch Reviews
# -----------------------------------
def fetch_reviews_page(sku: str, page: int = 1, page_size: int = 10):
    params = {
        "apiKey": BESTBUY_API_KEY,
        "format": "json",
        "page": page,
        "pageSize": page_size,
    }
    url = f"{API_BASE}(sku={sku})"
    try:
        if not BESTBUY_API_KEY:
            raise ValueError("❌ BESTBUY_API_KEY not set in environment. Create a .env with BESTBUY_API_KEY=YOUR_KEY.")
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {e}")
        return None
    except ValueError as ve:
        # Propagate configuration errors upward for clearer client message
        raise ve

# -----------------------------------
# 5️⃣ Normalize Review Object
# -----------------------------------
def normalize_review(r: dict, sku: str) -> dict:
    """Convert BestBuy API review into consistent schema (like eBay)."""
    return {
        "id": r.get("id"),
        "sku": sku,
        "product_id": sku,
        "source": "bestbuy",
        "reviewer": r.get("reviewer", {}).get("name", "Anonymous") if isinstance(r.get("reviewer"), dict) else "Anonymous",
        "rating": r.get("rating"),
        "title": r.get("title"),
        "text": r.get("comment") or "",
        "date": r.get("submissionTime", ""),
    }

# -----------------------------------
# 6️⃣ Save to MongoDB
# -----------------------------------
def save_reviews_to_mongo(reviews: list):
    col = get_mongo_collection()
    inserted = 0
    for r in reviews:
        try:
            if not col.find_one({"product_id": r["product_id"], "text": r["text"]}):
                col.insert_one(r)
                inserted += 1
        except errors.DuplicateKeyError:
            continue
    return inserted

# -----------------------------------
# 7️⃣ Scraper with Caching
# -----------------------------------
def scrape_and_store_reviews(link_or_sku: str, page_size: int = 10, delay: float = 1.0):
    col = get_mongo_collection()
    sku = extract_sku(link_or_sku)

    # ✅ Step 1: Check Mongo cache
    existing = list(col.find({"sku": sku}))
    if existing:
        print(f"💾 Found {len(existing)} cached reviews for SKU {sku}. Skipping API call.")
        # 🔧 Ensure cached docs have product_id set (backfill old records)
        needs_backfill = any("product_id" not in doc or not doc.get("product_id") for doc in existing)
        if needs_backfill:
            try:
                col.update_many({"sku": sku, "product_id": {"$exists": False}}, {"$set": {"product_id": sku}})
                col.update_many({"sku": sku, "product_id": None}, {"$set": {"product_id": sku}})
                print(f"🛠️ Backfilled product_id for cached SKU {sku}.")
            except Exception as e:
                print(f"⚠️ Backfill failed for SKU {sku}: {e}")
            # Refresh cache after backfill
            existing = list(col.find({"sku": sku}))
        # ✅ Normalize shape for response
        normalized_existing = [
            {
                "id": doc.get("id"),
                "sku": sku,
                "product_id": doc.get("product_id") or sku,
                "source": doc.get("source", "bestbuy"),
                "reviewer": (doc.get("reviewer") or "Anonymous"),
                "rating": doc.get("rating"),
                "title": doc.get("title"),
                "text": doc.get("text") or doc.get("comment") or "",
                "date": doc.get("date") or doc.get("submissionTime", ""),
            }
            for doc in existing
        ]
        return normalized_existing

    print(f"🆔 Extracted SKU: {sku}")
    print(f"🔍 No cache found — Fetching reviews using BestBuy Developer API...\n")

    # ✅ Step 2: Fetch from API
    data = fetch_reviews_page(sku, 1, page_size)
    if not data:
        print("❌ Failed to fetch first page.")
        return []

    total = data.get("total", 0)
    total_pages = data.get("totalPages", 1)
    print(f"✅ Total reviews: {total} | Total pages: {total_pages}\n")

    all_reviews = []
    inserted_total = 0

    for page in range(1, total_pages + 1):
        d = fetch_reviews_page(sku, page, page_size)
        if not d:
            print(f"⚠️ Skipping page {page}")
            continue

        reviews = d.get("reviews", [])
        normalized = [normalize_review(r, sku) for r in reviews]
        inserted = save_reviews_to_mongo(normalized)
        inserted_total += inserted
        all_reviews.extend(normalized)
        print(f"📄 Page {page}/{total_pages} | Inserted: {inserted}")

        time.sleep(delay)

    print(f"\n✅ Done. Total {inserted_total} new reviews added for SKU {sku}.")
    return all_reviews

# -----------------------------------
# 8️⃣ CLI Entry
# -----------------------------------
if __name__ == "__main__":
    user_input = input("🔗 Enter BestBuy product URL or SKU: ").strip()
    scrape_and_store_reviews(user_input)
