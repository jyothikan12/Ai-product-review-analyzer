import axios from "axios";

/* -----------------------------
   📦 Type Definitions
----------------------------- */
export interface Review {
  product_id: string;
  source: string;
  reviewer: string;
  text: string;
  date: string;
}

export interface ScrapeResponse {
  count: number;
  reviews: Review[];
}

export interface SummaryResponse {
  summary: string;
}

/* -----------------------------
   🌐 API Configuration
----------------------------- */
const API_BASE = "http://127.0.0.1:5000/api"; // Flask backend URL

/* -----------------------------
   🛍️ eBay Scraper
----------------------------- */
export async function scrapeEbay(url: string): Promise<ScrapeResponse> {
  const res = await axios.post(`${API_BASE}/scrape_ebay`, { url });
  return res.data as ScrapeResponse;
}

/* -----------------------------
   🛒 BestBuy Scraper
----------------------------- */
export async function scrapeBestBuy(url: string): Promise<ScrapeResponse> {
  const res = await axios.post(`${API_BASE}/scrape_bestbuy`, { url });
  return res.data as ScrapeResponse;
}

/* -----------------------------
   🧠 NLP Processor
----------------------------- */
export async function processProduct(product_id: string): Promise<{ processed: number }> {
  const res = await axios.get(`${API_BASE}/process/${product_id}`);
  return res.data as { processed: number };
}

/* -----------------------------
   🤖 AI Summary
----------------------------- */
export async function getSummary(product_id: string): Promise<SummaryResponse> {
  const res = await axios.get(`${API_BASE}/summary/${product_id}`);
  return res.data as SummaryResponse;
}

/* -----------------------------
   ⚔️ Product Comparison
----------------------------- */
export async function compareProducts(
  pid1: string,
  pid2: string,
  title1: string,
  title2: string
): Promise<{ comparison: string }> {
  const res = await axios.post(`${API_BASE}/compare`, { pid1, pid2, title1, title2 });
  return res.data as { comparison: string };
}
