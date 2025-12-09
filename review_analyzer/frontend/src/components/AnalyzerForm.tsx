import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface AnalyzerFormProps {
  platform: string;
  onAnalyze: (url: string) => void;
  isLoading?: boolean;
}


const AnalyzerForm = ({ platform, onAnalyze }: AnalyzerFormProps) => {
  const [url, setUrl] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      toast.error("Please enter a product URL");
      return;
    }

    setIsAnalyzing(true);
    
    // Simulate API call
    setTimeout(() => {
      setIsAnalyzing(false);
      toast.success("Analysis complete!");
      onAnalyze?.(url);
    }, 2000);
  };

  const platformConfig = {
    ebay: {
      title: "eBay Review Analyzer",
      subtitle: "Analyze eBay product reviews with AI",
      buttonVariant: "neon" as const,
      placeholder: "https://www.ebay.com/itm/...",
    },
    bestbuy: {
      title: "BestBuy Review Analyzer",
      subtitle: "Analyze BestBuy product reviews with AI",
      buttonVariant: "neonOrange" as const,
      placeholder: "https://www.bestbuy.com/site/...",
    },
  };

  const config = platformConfig[platform];

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className={`text-4xl md:text-5xl font-bold ${platform === "ebay" ? "gradient-text-blue" : "gradient-text-orange"}`}>
          {config.title}
        </h1>
        <p className="text-muted-foreground text-lg">{config.subtitle}</p>
      </div>

      <Card className="p-8 bg-card/50 backdrop-blur-sm border-border">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="product-url" className="text-sm font-medium">
              Product URL
            </label>
            <Input
              id="product-url"
              type="url"
              placeholder={config.placeholder}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="bg-input border-border focus:border-primary transition-colors"
              disabled={isAnalyzing}
            />
          </div>

          <Button
            type="submit"
            variant={config.buttonVariant}
            size="xl"
            className="w-full"
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="animate-spin" />
                Analyzing Reviews...
              </>
            ) : (
              <>Analyze Reviews</>
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default AnalyzerForm;
