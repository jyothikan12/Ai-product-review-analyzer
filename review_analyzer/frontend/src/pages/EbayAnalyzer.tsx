import { useState } from "react";
import Navigation from "@/components/Navigation";
import AnalyzerForm from "@/components/AnalyzerForm";
import ResultsDisplay from "@/components/ResultsDisplay";
import { scrapeEbay, processProduct, getSummary } from "@/lib/api";

const EbayAnalyzer = () => {
  const [showResults, setShowResults] = useState(false);
  const [sentiment, setSentiment] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [productId, setProductId] = useState<string | null>(null);

  const handleAnalyze = async (url: string) => {
    console.log("🔍 Analyzing eBay URL:", url);
    if (!url.trim()) {
      alert("Please enter a valid eBay URL!");
      return;
    }

    setLoading(true);
    setShowResults(false);
    setSummary("");
    setSentiment("");
    setProductId(null);

    try {
      // ✅ Step 1: Scrape reviews
      const data = await scrapeEbay(url);
      if (!data?.reviews?.length) {
        alert("No reviews found for this product.");
        return;
      }

      const pid = data.reviews[0].product_id;
      setProductId(pid);

      // ✅ Step 2: Run NLP processing
      await processProduct(pid);

      // ✅ Step 3: Get AI summary
      const summaryData = await getSummary(pid);

      // ✅ Update UI
      setSummary(summaryData.summary || "No summary available.");
      setSentiment("Positive"); // You can update dynamically later
      setShowResults(true);

    } catch (error) {
      console.error("❌ Analysis failed:", error);
      alert("Something went wrong while analyzing the product.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen text-white bg-gradient-to-b from-[#020617] to-[#0f172a]">
      <Navigation />

      <main className="container mx-auto px-4 py-12 max-w-4xl">
        <div className="space-y-12">
          <AnalyzerForm
            platform="ebay"
            onAnalyze={handleAnalyze}
            isLoading={loading}
          />

          {/* ✅ Pass productId properly to ResultsDisplay */}
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

export default EbayAnalyzer;
