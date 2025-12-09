import re
import json
from collections import defaultdict
from pymongo import MongoClient
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from transformers import pipeline

# =====================================================
# 🔧 Setup
# =====================================================
load_dotenv()

# MongoDB connection
import os
MONGO_URI = os.getenv("MONGO_URI")


client = MongoClient(MONGO_URI)
raw_db = client["review_system"]
raw_collection = raw_db["reviews_raw"]

processed_db = client["review_system_processed"]
processed_collection = processed_db["reviews"]

# =====================================================
# 🧠 Load Sentiment Model (VADER)
# =====================================================
nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

# =====================================================
# 🧩 Local Summarization Model (DistilBART) — Lazy Load
# =====================================================
summarizer = None  # will be loaded on first use

def get_summarizer():
    """Lazily load summarizer; allow disabling via NLP_DISABLE_SUMMARIZER."""
    global summarizer
    try:
        if os.getenv("NLP_DISABLE_SUMMARIZER", "").lower() in ("1", "true", "yes"):
            return None
        if summarizer is None:
            print("⚙️ Loading local summarization model (DistilBART)...")
            tmp = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-12-6",
                device=-1  # change to 0 if you have GPU
            )
            summarizer = tmp
            print("✅ Local summarizer ready!")
        return summarizer
    except Exception as e:
        print("⚠️ Failed to load summarizer:", e)
        summarizer = None
        return None

# =====================================================
# 🔍 Aspect Keywords
# =====================================================
ASPECT_KEYWORDS = {
    "Price": ["price", "cost", "expensive", "cheap", "value"],
    "Quality": ["quality", "durable", "broken", "excellent", "bad"],
    "Delivery": ["delivery", "shipping", "late", "fast", "slow"],
    "Packaging": ["packaging", "box", "seal", "damaged"],
    "Usability": ["use", "performance", "speed", "battery"],
}

# =====================================================
# 🧠 Sentiment & Aspect Processing
# =====================================================
def analyze_sentiment(text):
    score = sia.polarity_scores(text)["compound"]
    if score >= 0.05:
        sentiment = "Positive"
    elif score <= -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    return sentiment, abs(score)


def analyze_aspects(text):
    text = text.lower()
    found_aspects = []
    for aspect, keywords in ASPECT_KEYWORDS.items():
        if any(re.search(rf"\b{k}\b", text) for k in keywords):
            found_aspects.append(aspect)
    return found_aspects


# =====================================================
# 🧩 Process Reviews and Save to Mongo
# =====================================================
def process_reviews(product_id: str = None, force: bool = False):
    query = {"product_id": product_id} if product_id else {}

    if not force and product_id:
        existing = processed_collection.count_documents({"product_id": product_id})
        if existing > 0:
            print(f"💾 Found {existing} processed reviews for {product_id}. Skipping NLP re-run.")
            return list(processed_collection.find(query))

    raw_reviews = list(raw_collection.find(query))
    if not raw_reviews:
        print(f"⚠️ No raw reviews found for {product_id}. Run scraper first.")
        return []

    print(f"🔹 Found {len(raw_reviews)} raw reviews for {product_id}")
    print(f"🧠 Starting NLP for product_id={product_id}")

    inserted = 0
    for r in raw_reviews:
        text = r.get("text", "").strip()
        if not text:
            continue

        sentiment, confidence = analyze_sentiment(text)
        aspects = analyze_aspects(text)

        processed_review = {
            "product_id": r.get("product_id"),
            "source": r.get("source", "ebay"),
            "reviewer": r.get("reviewer", "Anonymous"),
            "rating": r.get("rating"),
            "text": text,
            "date": r.get("date", ""),
            "sentiment": sentiment,
            "confidence": confidence,
            "aspects": aspects,
        }

        if not processed_collection.find_one(
            {"product_id": processed_review["product_id"], "text": processed_review["text"]}
        ):
            processed_collection.insert_one(processed_review)
            inserted += 1

    print(f"✅ Inserted {inserted} new processed reviews for {product_id}")
    return list(processed_collection.find(query))

# =====================================================
# 📊 Sentiment + Aspect Summary
# =====================================================
def _compute_sentiment_summary(docs):
    total = len(docs)
    pos = sum(1 for d in docs if d.get("sentiment") == "Positive")
    neg = sum(1 for d in docs if d.get("sentiment") == "Negative")
    neu = sum(1 for d in docs if d.get("sentiment") == "Neutral")
    pct = lambda x: round(100 * x / total, 2) if total else 0
    overall_score = round(pct(pos) - pct(neg), 2)
    return {
        "total_reviews": total,
        "positive_%": pct(pos),
        "negative_%": pct(neg),
        "neutral_%": pct(neu),
        "overall_score": overall_score,
    }


def _compute_aspect_summary(docs):
    agg = defaultdict(lambda: {"Positive": 0, "Negative": 0, "Neutral": 0, "Total": 0})
    for d in docs:
        aspects = d.get("aspects") or []
        sent = d.get("sentiment")
        if not aspects or sent not in ("Positive", "Negative", "Neutral"):
            continue
        for a in aspects:
            agg[a][sent] += 1
            agg[a]["Total"] += 1
    return dict(agg)

# =====================================================
# ⚔️ Compare Two Products (Sentiment & Aspect)
# =====================================================
def compare_products(product_ids):
    results = []
    for pid in product_ids:
        docs = list(processed_collection.find({"product_id": pid}))
        sentiment = _compute_sentiment_summary(docs)
        aspects = _compute_aspect_summary(docs)
        results.append({"product_id": pid, "sentiment": sentiment, "aspects": aspects})

    all_aspects = set()
    for p in results:
        all_aspects.update(p["aspects"].keys())

    aspect_table = {}
    for aspect in sorted(all_aspects):
        aspect_table[aspect] = {}
        for p in results:
            pid = p["product_id"]
            counts = p["aspects"].get(aspect, {"Positive": 0, "Negative": 0, "Neutral": 0, "Total": 0})
            aspect_table[aspect][pid] = counts

    summary_rows = []
    for p in results:
        summary_rows.append({"product_id": p["product_id"], **p["sentiment"]})

    return {"summary": summary_rows, "aspect_table": aspect_table, "product_ids": product_ids}

# =====================================================
# 🧠 Local Summary for Single Product
# =====================================================
def generate_ai_summary_api(product_id: str, max_reviews: int = 150):
    """Generate AI summary using local DistilBART model."""
    try:
        reviews = list(processed_collection.find({"product_id": product_id}).limit(max_reviews))
        if not reviews:
            return "No processed reviews found for summarization."

        sum_model = get_summarizer()
        all_text = " ".join(r.get("text", "") for r in reviews if r.get("text"))
        # Hard cap to prevent OOM
        max_chars = int(os.getenv("SUMMARY_MAX_CHARS", "120000"))
        if len(all_text) > max_chars:
            all_text = all_text[:max_chars]
        print(f"🧾 Total text length used: {len(all_text)} characters")

        if sum_model is None:
            # Fallback: simple extractive text
            fallback = " ".join((r.get("text", "").strip() for r in reviews[:5]))
            final_summary = (fallback[:1500] + ("…" if len(fallback) > 1500 else "")).strip()
        else:
            # Split text into chunks
            chunk_size = int(os.getenv("SUMMARY_CHUNK_SIZE", "2500"))
            chunks = [all_text[i:i + chunk_size] for i in range(0, len(all_text), chunk_size)]

            summaries = []
            for i, chunk in enumerate(chunks, 1):
                print(f"✍️ Summarizing chunk {i}/{len(chunks)}...")
                partial = sum_model(chunk, max_length=150, min_length=60, do_sample=False)[0]["summary_text"]
                summaries.append(partial)
            final_summary = " ".join(summaries)

        # Save to Mongo
        summary_col = processed_db["review_summaries"]
        doc = {
            "product_id": product_id,
            "summary": final_summary,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        summary_col.update_one({"product_id": product_id}, {"$set": doc}, upsert=True)

        print("✅ Summary saved successfully.")
        return final_summary

    except Exception as e:
        print("⚠️ Local summarizer error:", e)
        return f"Summarization failed: {e}"

# =====================================================
# ⚔️ Local Competitor Summary (New)
# =====================================================
def generate_competitor_summary_api(pid1: str, pid2: str, title1: str, title2: str, max_reviews: int = 100):
    """Compare two products using summarization and aspect sentiment scores."""
    from collections import defaultdict

    try:
        reviews1 = list(processed_collection.find({"product_id": pid1}).limit(max_reviews))
        reviews2 = list(processed_collection.find({"product_id": pid2}).limit(max_reviews))

        if not reviews1 or not reviews2:
            return {"error": "Not enough processed reviews for both products."}

        # ✅ Summarization Part (keep as before)
        text1 = " ".join(r.get("text", "") for r in reviews1)
        text2 = " ".join(r.get("text", "") for r in reviews2)

        print(f"🧠 Generating competitor summaries for {title1} vs {title2}")
        sum_model = get_summarizer()
        if sum_model is None:
            summary1 = (text1[:1200] + ("…" if len(text1) > 1200 else "")) or "No summary available."
            summary2 = (text2[:1200] + ("…" if len(text2) > 1200 else "")) or "No summary available."
        else:
            summary1 = sum_model(text1[:2500], max_length=130, min_length=60, do_sample=False)[0]["summary_text"]
            summary2 = sum_model(text2[:2500], max_length=130, min_length=60, do_sample=False)[0]["summary_text"]

        # ✅ Aspect Scoring Part
        def get_aspect_scores(docs):
            aspect_map = defaultdict(lambda: {"Positive": 0, "Neutral": 0, "Negative": 0})
            for d in docs:
                for aspect in d.get("aspects", []):
                    s = d.get("sentiment", "Neutral")
                    aspect_map[aspect][s] += 1

            scores = {}
            for aspect, vals in aspect_map.items():
                total = vals["Positive"] + vals["Neutral"] + vals["Negative"]
                if total == 0:
                    continue
                score = (vals["Positive"] - vals["Negative"]) / total
                scores[aspect] = round(score, 3)
            return scores

        scores1 = get_aspect_scores(reviews1)
        scores2 = get_aspect_scores(reviews2)

        # ✅ Determine winners per aspect
        comparison = []
        for aspect in set(scores1.keys()) | set(scores2.keys()):
            a1 = scores1.get(aspect, 0)
            a2 = scores2.get(aspect, 0)
            if abs(a1 - a2) < 0.05:
                winner = "Tie"
            elif a1 > a2:
                winner = title1
            else:
                winner = title2
            comparison.append({
                "aspect": aspect,
                title1: a1,
                title2: a2,
                "winner": winner
            })

        # ✅ Compute overall scores
        overall1 = round(sum(scores1.values()) / len(scores1), 3) if scores1 else 0
        overall2 = round(sum(scores2.values()) / len(scores2), 3) if scores2 else 0
        if abs(overall1 - overall2) < 0.05:
            overall_winner = "Tie"
        elif overall1 > overall2:
            overall_winner = title1
        else:
            overall_winner = title2

        # ✅ Build Final Combined Output
        combined_summary = {
            "summary": (
                f"📦 {title1} Summary:\n{summary1}\n\n"
                f"🛒 {title2} Summary:\n{summary2}\n\n"
                f"🏁 Overall Comparison:\nBoth products have unique strengths. "
                f"{title1} may appeal more to users valuing {', '.join([a['aspect'] for a in comparison if a['winner']==title1][:2])}, "
                f"while {title2} performs better for {', '.join([a['aspect'] for a in comparison if a['winner']==title2][:2])}."
            ),
            "comparison": comparison,
            "overall": {
                title1: overall1,
                title2: overall2,
                "winner": overall_winner
            }
        }

        return combined_summary

    except Exception as e:
        print("⚠️ Local competitor summary error:", e)
        return {"error": str(e)}

