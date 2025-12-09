import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Zap, Brain, BarChart3, ArrowRight } from "lucide-react";
import FeatureCard from "@/components/FeatureCard";
import Navigation from "@/components/Navigation";

const Home = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      
      <main className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <section className="text-center space-y-8 mb-20">
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-6 duration-700">
            <h1 className="text-5xl md:text-7xl font-bold gradient-text-blue leading-tight">
              AI-Powered Review Intelligence
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto">
              Analyze thousands of product reviews instantly using AI to make smarter purchase decisions.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
            <Link to="/ebay">
              <Button variant="neon" size="xl" className="group">
                Analyze eBay Reviews
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/bestbuy">
              <Button variant="neonOrange" size="xl" className="group">
                Analyze BestBuy Reviews
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section className="space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Powerful Features</h2>
            <p className="text-muted-foreground text-lg">Everything you need to make informed decisions</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-300">
            <FeatureCard
              icon={Zap}
              title="Instant Sentiment Detection"
              description="Get immediate insights into customer satisfaction with advanced AI sentiment analysis"
            />
            <FeatureCard
              icon={Brain}
              title="AI-Powered Insights"
              description="Understand review patterns and trends with machine learning algorithms"
            />
            <FeatureCard
              icon={BarChart3}
              title="Smart Comparison"
              description="Compare products side-by-side with intelligent review aggregation"
            />
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 mt-20 py-8">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>&copy; 2024 AI Review Analyzer. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
