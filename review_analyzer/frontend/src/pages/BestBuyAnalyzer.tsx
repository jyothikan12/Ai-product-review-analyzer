import { useState } from "react";
import Navigation from "@/components/Navigation";
import AnalyzerForm from "@/components/AnalyzerForm";
import ResultsDisplay from "@/components/ResultsDisplay";
import { scrapeBestBuy, processProduct, getSummary } from "@/lib/api";

const BestBuyAnalyzer = () => {
  const [showResults, setShowResults] = useState(false);
  const [sentiment, setSentiment] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [productId, setProductId] = useState<string | null>(null);

  const handleAnalyze = async (url: string) => {
    console.log("🔍 Analyzing BestBuy URL:", url);
    if (!url.trim()) {
      alert("Please enter a valid BestBuy URL!");
      return;
    }

    setLoading(true);
    setShowResults(false);
    setSummary("");
    setSentiment("");
    setProductId(null);

    try {
      // ✅ Step 1: Scrape BestBuy reviews
      const data = await scrapeBestBuy(url);
      console.log("📦 BestBuy scrape response:", data);

      if (!data?.reviews?.length) {
        alert("No reviews found for this product. Try a different URL or SKU.");
        return;
      }

      const pid = data.reviews[0].product_id;
      setProductId(pid);

      // ✅ Step 2: Process NLP
      const nlpResult = await processProduct(pid);
      console.log("🧠 NLP Processing Complete:", nlpResult);

      // ✅ Step 3: Generate AI summary
      const summaryData = await getSummary(pid);
      console.log("🧾 AI Summary:", summaryData);

      setSummary(summaryData.summary || "No summary available.");
      setSentiment("Positive"); // (Later can compute actual based on NLP)
      setShowResults(true);
    } catch (error) {
      console.error("❌ BestBuy analysis failed:", error);
      alert("Something went wrong while analyzing the BestBuy product.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen text-white bg-gradient-to-b from-[#0b0b17] to-[#111827]">
      <Navigation />

      <main className="container mx-auto px-4 py-12 max-w-4xl">
        <div className="space-y-12">
          {/* ✅ Analyzer Form */}
          <AnalyzerForm
            platform="bestbuy"
            onAnalyze={handleAnalyze}
            isLoading={loading}
          />

          {/* ✅ Show results once productId is available */}
          {productId && (
            <ResultsDisplay
              show={showResults}
              sentiment={sentiment}
              summary={summary}
              productId={productId}
            />
          )}
        </div>
      </main>
    </div>
  );
};

export default BestBuyAnalyzer;
