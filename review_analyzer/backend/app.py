from flask import Flask, request, jsonify
from flask_cors import CORS
from services.ebay_scraper import fetch_and_save_reviews
from services.bestbuy_reviews_to_mongo import scrape_and_store_reviews
from services.nlp_utils import (
    process_reviews,
    generate_ai_summary_api,
    compare_products,
    generate_competitor_summary_api,
)
from bson import ObjectId
from services import nlp_utils as nlp

app = Flask(__name__)
CORS(app)

# ✅ Helper — clean MongoDB documents for JSON output
def clean_mongo_docs(docs):
    cleaned = []
    for d in docs:
        d = dict(d)  # ensure it's a regular dict
        if "_id" in d:
            d["_id"] = str(d["_id"])  # convert ObjectId → string
        cleaned.append(d)
    return cleaned


# ✅ Route 1: Scrape BestBuy reviews
@app.route('/api/scrape_bestbuy', methods=['POST'])
def scrape_bestbuy():
    data = request.get_json() or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    try:
        reviews = scrape_and_store_reviews(url)
        reviews = clean_mongo_docs(reviews)
        return jsonify({"count": len(reviews), "reviews": reviews})
    except ValueError as ve:
        # SKU extraction / missing API key etc.
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print("⚠️ BestBuy route error:", e)
        return jsonify({"error": str(e)}), 500


# ✅ Route 2: Scrape eBay reviews (with safe JSON serialization)
@app.route('/api/scrape_ebay', methods=['POST'])
def scrape_ebay():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    try:
        reviews = fetch_and_save_reviews(url)
        reviews = clean_mongo_docs(reviews)
        return jsonify({"count": len(reviews), "reviews": reviews})
    except Exception as e:
        print("⚠️ eBay route error:", e)
        return jsonify({"error": str(e)}), 500


# ✅ Route 3: Run NLP sentiment/aspect processing (enhanced)
@app.route('/api/process/<product_id>', methods=['GET'])
def process_product(product_id):
    try:
        from collections import Counter, defaultdict
        docs = process_reviews(product_id)

        # ---- Sentiment and Aspect Summary ----
        sentiments = Counter([d.get("sentiment") for d in docs if "sentiment" in d])
        aspect_map = defaultdict(lambda: {"Positive": 0, "Negative": 0, "Neutral": 0})

        for d in docs:
            for aspect in d.get("aspects", []):
                s = d.get("sentiment", "Neutral")
                aspect_map[aspect][s] += 1

        # ---- Aspect-based sample reviews (top by confidence) ----
        aspect_examples = defaultdict(lambda: {"Positive": [], "Neutral": [], "Negative": []})
        for d in docs:
            text = (d.get("text") or "").strip()
            if not text:
                continue
            conf = float(d.get("confidence") or 0.0)
            s = d.get("sentiment", "Neutral")
            for aspect in d.get("aspects", []) or []:
                aspect_examples[aspect][s].append({"text": text, "confidence": conf})

        # keep only top 3 per sentiment per aspect
        for a, buckets in aspect_examples.items():
            for s in ("Positive", "Neutral", "Negative"):
                buckets[s] = sorted(buckets[s], key=lambda x: x["confidence"], reverse=True)[:3]

        # ---- Top 5 Positive and Negative Reviews ----
        positive_comments = [
            {"text": d.get("text"), "confidence": d.get("confidence", 0)}
            for d in docs if d.get("sentiment") == "Positive"
        ]
        negative_comments = [
            {"text": d.get("text"), "confidence": d.get("confidence", 0)}
            for d in docs if d.get("sentiment") == "Negative"
        ]

        # Sort by confidence (strongest sentiments first)
        positive_comments = sorted(positive_comments, key=lambda x: x["confidence"], reverse=True)[:5]
        negative_comments = sorted(negative_comments, key=lambda x: x["confidence"], reverse=True)[:5]

        # ---- Final JSON ----
        return jsonify({
            "product_id": product_id,
            "total_reviews": len(docs),
            "sentiments": dict(sentiments),
            "aspects": {k: dict(v) for k, v in aspect_map.items()},
            "aspect_examples": {k: v for k, v in aspect_examples.items()},
            "top_positive": positive_comments,
            "top_negative": negative_comments
        })

    except Exception as e:
        print("⚠️ Error in process_product:", e)
        return jsonify({"error": str(e)}), 500



# ✅ Route 4: Get AI summary for one product
@app.route('/api/summary/<product_id>', methods=['GET'])
def summary(product_id):
    try:
        summary_text = generate_ai_summary_api(product_id)
        return jsonify({"summary": summary_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Route 5: Compare two products
@app.route('/api/compare', methods=['POST'])
def compare_api():
    data = request.get_json()
    pid1, pid2 = data.get("pid1"), data.get("pid2")
    title1, title2 = data.get("title1", ""), data.get("title2", "")
    if not pid1 or not pid2:
        return jsonify({"error": "Missing product IDs"}), 400
    try:
        # ✅ Textual comparison summary (local summarizer)
        comp_raw = generate_competitor_summary_api(pid1, pid2, title1, title2)
        # Backward compatible: ensure `comparison` is a string for the frontend
        if isinstance(comp_raw, dict):
            comparison_text = comp_raw.get("summary") or comp_raw.get("comparison") or ""
        elif isinstance(comp_raw, str):
            comparison_text = comp_raw
        else:
            comparison_text = str(comp_raw)

        # ✅ Structured comparison using processed aspect/sentiment data
        comp = compare_products([pid1, pid2])  # returns { summary, aspect_table, product_ids }

        # Compute winners per aspect using net score: Positive - Negative
        aspect_winners = {}
        for aspect, by_pid in comp.get("aspect_table", {}).items():
            scores = {}
            for pid, counts in by_pid.items():
                pos = counts.get("Positive", 0) or 0
                neg = counts.get("Negative", 0) or 0
                scores[pid] = pos - neg
            # decide winner
            if len(scores) == 2:
                (a_pid, a_score), (b_pid, b_score) = list(scores.items())
                if a_score == b_score:
                    winner = "tie"
                else:
                    winner = a_pid if a_score > b_score else b_pid
            else:
                # Fallback: pick max or tie
                if scores:
                    max_score = max(scores.values())
                    winners = [pid for pid, sc in scores.items() if sc == max_score]
                    winner = winners[0] if len(winners) == 1 else "tie"
                else:
                    winner = "tie"

            aspect_winners[aspect] = {
                "winner": winner,
                "scores": scores,
            }

        # Overall winner based on overall sentiment score (positive% - negative%)
        overall_winner = "tie"
        overall_scores = {}
        for row in comp.get("summary", []):
            pid = row.get("product_id")
            score = row.get("overall_score", 0)
            overall_scores[pid] = score
        if len(overall_scores) >= 2:
            items = list(overall_scores.items())
            items.sort(key=lambda x: x[1], reverse=True)
            if len(items) >= 2 and items[0][1] == items[1][1]:
                overall_winner = "tie"
            else:
                overall_winner = items[0][0]

        return jsonify({
            "comparison": comparison_text,
            "aspect_winners": aspect_winners,
            "overall_scores": overall_scores,
            "overall_winner": overall_winner,
            "product_ids": comp.get("product_ids", [pid1, pid2])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Flask backend ready — using local AI summarizer for summaries and comparisons.")
    app.run(debug=False)

# ✅ Health endpoint (placed after main guard for clarity if imported elsewhere)
@app.route('/api/health', methods=['GET'])
def health():
    try:
        # summarizer status
        sum_available = bool(getattr(nlp, 'summarizer', None)) or bool(nlp.get_summarizer())
        return jsonify({
            "status": "ok",
            "summarizer_loaded": sum_available
        })
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e) }), 500
