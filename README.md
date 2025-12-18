# 🧠 AI Review Insight Engine  
### Sentiment, Emotion & Aspect Analysis for E-Commerce Reviews

AI Review Insight Engine is a full-stack NLP application that analyzes and summarizes customer reviews from **eBay** and **BestBuy**.  
It extracts **sentiment**, **aspect-level insights**, and **AI-generated summaries**, presenting them through an interactive web dashboard.

---

## 🚀 Features
- 🔍 Scrapes product reviews from **eBay** and **BestBuy**
- 😊 Sentiment classification (Positive / Neutral / Negative)
- 🧩 Aspect-based analysis (Price, Quality, Delivery, Packaging, Usability)
- 🤖 AI-generated review summaries using Transformer models
- 📊 Interactive visualizations (Pie & Bar charts)
- ⚔️ Side-by-side product comparison
- 💾 MongoDB-based caching for fast repeated analysis

---

## 🏗️ System Architecture
**User → Frontend (React) → Backend (Flask) → NLP Engine → MongoDB → Visualization Dashboard**

- **Frontend:** React (Vite), TypeScript, Recharts, TailwindCSS  
- **Backend:** Python, Flask, REST APIs  
- **NLP:** VADER (Sentiment), Regex-based Aspect Extraction, Transformers (Summarization)  
- **Database:** MongoDB Atlas  
- **Scraping:**  
  - eBay → ScraperAPI + BeautifulSoup  
  - BestBuy → Official BestBuy Developer API (SKU-based)

---

## 🔗 Supported URL Formats
- **eBay:**  
# 🧠 AI Review Insight Engine  
### Sentiment, Emotion & Aspect Analysis for E-Commerce Reviews

AI Review Insight Engine is a full-stack NLP application that analyzes and summarizes customer reviews from **eBay** and **BestBuy**.  
It extracts **sentiment**, **aspect-level insights**, and **AI-generated summaries**, presenting them through an interactive web dashboard.

---

## 🚀 Features
- 🔍 Scrapes product reviews from **eBay** and **BestBuy**
- 😊 Sentiment classification (Positive / Neutral / Negative)
- 🧩 Aspect-based analysis (Price, Quality, Delivery, Packaging, Usability)
- 🤖 AI-generated review summaries using Transformer models
- 📊 Interactive visualizations (Pie & Bar charts)
- ⚔️ Side-by-side product comparison
- 💾 MongoDB-based caching for fast repeated analysis

---

## 🏗️ System Architecture
**User → Frontend (React) → Backend (Flask) → NLP Engine → MongoDB → Visualization Dashboard**

- **Frontend:** React (Vite), TypeScript, Recharts, TailwindCSS  
- **Backend:** Python, Flask, REST APIs  
- **NLP:** VADER (Sentiment), Regex-based Aspect Extraction, Transformers (Summarization)  
- **Database:** MongoDB Atlas  
- **Scraping:**  
  - eBay → ScraperAPI + BeautifulSoup  
  - BestBuy → Official BestBuy Developer API (SKU-based)

---

## 🔗 Supported URL Formats
- **eBay:**  
https://www.ebay.com/itm/
<product_id>
- **BestBuy:**  
https://www.bestbuy.com/.../sku/
<sku_id>

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/ai-review-insight-engine.git
cd ai-review-insight-engine
Backend Setup (Flask)
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
Create a .env file:
MONGO_URI=your_mongodb_uri
BESTBUY_API_KEY=your_bestbuy_api_key
SCRAPER_API_KEY=your_scraperapi_key
python app.py
Frontend Setup (React)
cd frontend
npm install
npm run dev
NLP Pipeline

Review scraping from source platform

Text preprocessing & deduplication

Sentiment analysis using VADER

Aspect detection using keyword & regex matching

AI summarization using Transformer models

Visualization of insights in frontend
Use Cases

Faster product review analysis for customers

Market research and competitor comparison

Feature-level customer feedback insights

AI-assisted decision making

🔮 Future Enhancements

Emotion detection (joy, anger, trust, fear)

Multi-language review support

LLM-based per-aspect explanations

Cloud deployment & scalability
