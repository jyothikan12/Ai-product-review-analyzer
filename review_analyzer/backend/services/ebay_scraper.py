import requests
import json
import os
import re
import time
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os

BESTBUY_API_KEY = os.getenv("BESTBUY_API_KEY")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")


# ========== CONFIG ==========
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY") # Replace with your key
SCRAPER_BASE = "https://api.scraperapi.com"
SAVE_DIR = "data"
os.makedirs(SAVE_DIR, exist_ok=True)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
# try:
#     client.admin.command("ping")
#     print("✅ MongoDB connection successful.")
# except Exception as e:
#     print("❌ MongoDB connection failed:", e)
raw_db = client["review_system"]
raw_collection = raw_db["reviews_raw"]
title_collection = raw_db["product_titles"]


# ---------- HELPERS ----------
def extract_product_id(url: str):
    match = re.search(r"/itm/(\d+)", url)
    return match.group(1) if match else "unknown"

def safe_get(url, render=False, retries=3):
    """Uses ScraperAPI with retries and optional JS rendering"""
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url
    }
    if render:
        params["render"] = "true"
    for i in range(retries):
        try:
            resp = requests.get(SCRAPER_BASE, params=params, timeout=60)
            if resp.status_code == 200:
                return resp
            else:
                print(f"⚠️ HTTP {resp.status_code}, retry {i+1}")
        except requests.RequestException as e:
            print(f"⚠️ {e}, retry {i+1}")
        time.sleep(2)
    return None

# ---------- CORE SCRAPER ----------
def fetch_ebay_reviews(product_url: str, max_pages: int = 2):
    """Hybrid scraper: product page → mweb_profile → seller feedback"""
    product_id = extract_product_id(product_url)
    all_reviews = []

    # ===== STEP 1: PRODUCT PAGE (old working approach) =====
    print(f"🔎 Trying product page (ScraperAPI HTML) for {product_id}")
    for page in range(1, max_pages + 1):
        url = f"{product_url}?pgn={page}"
        resp = safe_get(url)
        if not resp:
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("li.fdbk-container")
        print(f"👉 Found {len(cards)} reviews on page {page}")
        for card in cards:
            reviewer = card.select_one(".fdbk-container__details__info__username span")
            text_elem = card.select_one(".fdbk-container__details__comment span")
            date_elem = card.select_one(".fdbk-container__details__info__divide__time span")
            if text_elem and text_elem.text.strip():
                all_reviews.append({
                    "product_id": product_id,
                    "source": "ebay_product_html",
                    "reviewer": reviewer.text.strip() if reviewer else "Anonymous",
                    "text": text_elem.text.strip(),
                    "date": date_elem.text.strip() if date_elem else ""
                })
        if cards:
            break

    # ===== STEP 2: MWB PROFILE (item feedback API) =====
    if not all_reviews:
        print("⚠️ No reviews in product HTML. Trying mweb_profile endpoint...")
        try:
            resp = safe_get(product_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            seller_elem = soup.select_one("a[href*='/usr/']")
            if seller_elem:
                seller_name = seller_elem["href"].split("/usr/")[-1]
                mweb_url = (
                    f"https://www.ebay.com/fdbk/mweb_profile?"
                    f"fdbkType=FeedbackReceivedAsSeller&item_id={product_id}"
                    f"&username={seller_name}&filter=feedback_page:RECEIVED_AS_SELLER"
                    f"&q={product_id}&sort=RELEVANCEV2"
                )
                print(f"🔎 Fetching mweb_profile for {seller_name}")
                resp2 = safe_get(mweb_url)
                if resp2:
                    soup2 = BeautifulSoup(resp2.text, "html.parser")
                    cards = soup2.select("li.fdbk-container")
                    print(f"👉 Found {len(cards)} reviews in mweb_profile")
                    for card in cards:
                        reviewer = card.select_one(".fdbk-container__details__info__username span")
                        text_elem = card.select_one(".fdbk-container__details__comment span")
                        date_elem = card.select_one(".fdbk-container__details__info__divide__time span")
                        if text_elem and text_elem.text.strip():
                            all_reviews.append({
                                "product_id": product_id,
                                "source": "mweb_profile",
                                "reviewer": reviewer.text.strip() if reviewer else "Anonymous",
                                "text": text_elem.text.strip(),
                                "date": date_elem.text.strip() if date_elem else ""
                            })
        except Exception as e:
            print(f"⚠️ MWB Profile failed: {e}")

    # ===== STEP 3: SELLER FEEDBACK PAGE =====
    if not all_reviews:
        print("⚠️ No reviews yet. Trying seller feedback profile page...")
        try:
            resp = safe_get(product_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            seller_elem = soup.select_one("a[href*='/usr/']")
            if seller_elem:
                seller_name = seller_elem["href"].split("/usr/")[-1]
                fb_url = f"https://www.ebay.com/fdbk/feedback_profile/{seller_name}?filter=feedback_page:RECEIVED_AS_SELLER"
                print(f"🔎 Fetching {fb_url}")
                resp3 = safe_get(fb_url)
                if resp3:
                    soup3 = BeautifulSoup(resp3.text, "html.parser")
                    cards = soup3.select("li.fdbk-container")
                    print(f"👉 Found {len(cards)} reviews in seller feedback")
                    for card in cards:
                        reviewer = card.select_one(".fdbk-container__details__info__username span")
                        text_elem = card.select_one(".fdbk-container__details__comment span")
                        date_elem = card.select_one(".fdbk-container__details__info__divide__time span")
                        if text_elem and text_elem.text.strip():
                            all_reviews.append({
                                "product_id": product_id,
                                "source": "seller_feedback_profile",
                                "reviewer": reviewer.text.strip() if reviewer else "Anonymous",
                                "text": text_elem.text.strip(),
                                "date": date_elem.text.strip() if date_elem else ""
                            })
        except Exception as e:
            print(f"⚠️ Seller feedback failed: {e}")

    # ===== STEP 4: SAVE DEBUG IF ALL FAIL =====
    if not all_reviews:
        debug_path = os.path.join(SAVE_DIR, f"debug_{product_id}.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(resp.text if resp else "")
        print(f"💾 Saved debug HTML to {debug_path}")

    # Deduplicate
    unique = []
    seen = set()
    for r in all_reviews:
        if r["text"] not in seen:
            unique.append(r)
            seen.add(r["text"])

    print(f"✅ Total unique reviews: {len(unique)}")
    return unique

def save_reviews(product_id: str, reviews: list):
    """Save reviews to JSON file and MongoDB (deduplicated + product_id added)."""
    # 1️⃣ Save locally
    path = os.path.join(SAVE_DIR, f"ebay_reviews_{product_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {len(reviews)} reviews → {path}")

    # 2️⃣ Ensure all reviews have product_id field
    for r in reviews:
        r["product_id"] = product_id

    # 3️⃣ Find existing review texts for this product
    existing_texts = set(
        r["text"] for r in raw_collection.find({"product_id": product_id}, {"text": 1})
    )

    # 4️⃣ Filter only new reviews (by text)
    new_reviews = [r for r in reviews if r["text"] not in existing_texts]

    # 5️⃣ Insert new reviews if any
    if new_reviews:
        raw_collection.insert_many(new_reviews)
        print(f"✅ Inserted {len(new_reviews)} new reviews into MongoDB for {product_id}")
    else:
        print(f"💾 No new reviews to insert for {product_id} (all duplicates skipped).")

# def save_reviews(product_id: str, reviews: list):
#     """Save to JSON and MongoDB"""
#     path = os.path.join(SAVE_DIR, f"ebay_reviews_{product_id}.json")
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(reviews, f, indent=2, ensure_ascii=False)
#     print(f"💾 Saved {len(reviews)} reviews → {path}")

#     inserted = 0
#     for r in reviews:
#         if not raw_collection.find_one({"text": r["text"]}):
#             raw_collection.insert_one(r)
#             inserted += 1
#     print(f"✅ Inserted {inserted} new reviews into MongoDB")


def fetch_and_save_reviews(product_url: str):
    """Streamlit-compatible function"""
    
    product_id = extract_product_id(product_url)
     # 1️⃣ Check if product already exists in MongoDB
    existing_reviews = list(raw_collection.find({"product_id": product_id}))
    if existing_reviews:
        print(f"💾 Found {len(existing_reviews)} cached reviews for product_id {product_id}. Skipping scrape.")
        return existing_reviews
    else:
        print(f"🌐 No existing cache found for {product_id}. Scraping from eBay...")

    # 2️⃣ If not, fetch reviews
    reviews = fetch_ebay_reviews(product_url)
    if reviews:
        save_reviews(product_id, reviews)
        return reviews
    else:
        print("❌ No reviews found.")
        return []

def fetch_product_title(product_url: str) -> str:
    """Fetch product title from an eBay item page with MongoDB caching."""
    try:
        product_id = extract_product_id(product_url)

        # 🔹 Check if title already cached
        existing = title_collection.find_one({"product_id": product_id})
        if existing and existing.get("title"):
            print(f"💾 Cached title found for {product_id}")
            return existing["title"]

        # 🔹 If not cached, scrape title
        print(f"🌐 Fetching title for {product_id} from eBay...")
        resp = safe_get(product_url)
        if not resp:
            return "Unknown Product"
        soup = BeautifulSoup(resp.text, "html.parser")

        title_elem = (
            soup.select_one("#itemTitle")
            or soup.select_one("h1 span")
            or soup.select_one("h1")
        )
        if title_elem:
            title = title_elem.get_text(strip=True)
            title = title.replace("Details about  ", "").replace("Details about", "").strip()
        elif soup.title:
            title = soup.title.text.replace("| eBay", "").strip()
        else:
            title = "Unknown Product"

        # 🔹 Cache the title in MongoDB
        title_doc = {"product_id": product_id, "title": title}
        title_collection.update_one({"product_id": product_id}, {"$set": title_doc}, upsert=True)
        print(f"✅ Cached title for {product_id}: {title}")
        return title

    except Exception as e:
        print(f"⚠️ Error fetching title: {e}")
        return "Unknown Product"



if __name__ == "__main__":
        product_url = "https://www.ebay.com/itm/167044122483"  # 👈 Replace with your new link
        product_id = re.search(r"/itm/(\d+)", product_url)
        product_id = product_id.group(1) if product_id else "unknown"

        reviews = fetch_ebay_reviews(product_url, max_pages=2)
        save_reviews(product_id, reviews)