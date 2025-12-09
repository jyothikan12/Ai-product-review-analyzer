import { Link, useLocation } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const Navigation = () => {
  const location = useLocation();
  
  const navLinks = [
    { path: "/", label: "Home" },
    { path: "/ebay", label: "eBay" },
    { path: "/bestbuy", label: "BestBuy" },
    { path: "/compare", label: "Compare" },
  ];

  return (
    <nav className="border-b border-border/50 backdrop-blur-sm bg-background/50 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 group">
            <Sparkles className="w-6 h-6 text-primary group-hover:glow-blue transition-all" />
            <span className="text-xl font-bold gradient-text-blue">AI Review Analyzer</span>
          </Link>
          
          <div className="flex items-center gap-1 md:gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={cn(
                  "px-3 md:px-4 py-2 rounded-md text-sm font-medium transition-all duration-300",
                  location.pathname === link.path
                    ? "bg-primary/20 text-primary glow-blue"
                    : "text-muted-foreground hover:text-foreground hover:bg-card"
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
