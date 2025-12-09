import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";

interface ResultsDisplayProps {
  show: boolean;
  sentiment?: string;
  summary?: string;
  productId?: string;
}

export default function ResultsDisplay({
  show,
  sentiment,
  summary,
  productId,
}: ResultsDisplayProps) {
  const [sentimentData, setSentimentData] = useState<any[]>([]);
  const [aspectChartData, setAspectChartData] = useState<any[]>([]);
  const [aspectsRaw, setAspectsRaw] = useState<Record<string, any>>({});
  const [topPositive, setTopPositive] = useState<any[]>([]);
  const [topNegative, setTopNegative] = useState<any[]>([]);
  const [expandedPos, setExpandedPos] = useState<Record<number, boolean>>({});
  const [expandedNeg, setExpandedNeg] = useState<Record<number, boolean>>({});
  const [aspectExamples, setAspectExamples] = useState<
    Record<string, { Positive: any[]; Neutral: any[]; Negative: any[] }>
  >({});
  const [expandedAspect, setExpandedAspect] = useState<Record<string, boolean>>({});
  const [selectedAspect, setSelectedAspect] = useState<string>("");

useEffect(() => {
  if (!productId) return;

  let isFetched = false;

  const fetchNLPData = async () => {
    if (isFetched) return;
    isFetched = true;
    try {
      const res = await fetch(`http://127.0.0.1:5000/api/process/${productId}`);
      const data = await res.json();

      if (data.error) throw new Error(data.error);
      console.log("Fetched NLP Data:", data);

      // Sentiment data for pie chart
      const sents = data.sentiments || {};
      const sentimentArray = Object.entries(sents).map(([key, value]) => ({
        name: key,
        value,
      }));
      setSentimentData(sentimentArray);

      // Aspect data for bar chart
      const aspects = data.aspects || {};
      const aspectArray = Object.entries(aspects).map(
        ([aspect, values]: any) => ({
          aspect,
          Positive: values.Positive,
          Neutral: values.Neutral,
          Negative: values.Negative,
        })
      );
      setAspectChartData(aspectArray);
      setAspectsRaw(aspects);
      const aspectKeys = Object.keys(aspects || {});
      setSelectedAspect((prev) => prev || (aspectKeys.sort()[0] || ""));

      // ✅ Top positive & negative
      setTopPositive(data.top_positive || []);
      setTopNegative(data.top_negative || []);

      // ✅ Aspect-based examples
      setAspectExamples(data.aspect_examples || {});
    } catch (error) {
      console.error("Error fetching NLP data:", error);
    }
  };

  fetchNLPData();
}, [productId]); // ❗ remove 'show'


  if (!show) return null;

  const COLORS = ["#22c55e", "#facc15", "#ef4444"];

  return (
    <div className="space-y-10 bg-white/10 p-8 rounded-xl backdrop-blur-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-6 text-white">AI Insights</h2>

      {/* Sentiment Chart */}
      {sentimentData.length > 0 && (
        <Card className="p-6 bg-white/5 border border-white/10">
          <h3 className="text-xl font-semibold mb-4 text-white/90">
            Sentiment Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={110}
                dataKey="value"
              >
                {sentimentData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Aspect Chart */}
      {aspectChartData.length > 0 && (
        <Card className="p-6 bg-white/5 border border-white/10">
          <h3 className="text-xl font-semibold mb-4 text-white/90">
            Aspect Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={aspectChartData}>
              <XAxis dataKey="aspect" stroke="#ddd" />
              <YAxis stroke="#ddd" />
              <Tooltip />
              <Legend />
              <Bar dataKey="Positive" fill="#22c55e" />
              <Bar dataKey="Neutral" fill="#facc15" />
              <Bar dataKey="Negative" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* ✅ Top Reviews Section (Refactored with expandable translucent cards) */}
      {(topPositive.length > 0 || topNegative.length > 0) && (
        <Card className="p-6 bg-white/5 border border-white/10">
          <h3 className="text-xl font-semibold mb-6 text-white/90">
            Top Reviews
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Positive Column */}
            <div className="space-y-4">
              <h4 className="text-green-400 font-bold mb-2">Positive Highlights</h4>
              {topPositive.map((r, i) => {
                const isExpanded = expandedPos[i];
                const text = r.text || "";
                const previewLimit = 160;
                const shouldTruncate = text.length > previewLimit;
                const displayText = !shouldTruncate
                  ? text
                  : isExpanded
                    ? text
                    : text.slice(0, previewLimit) + "…";
                return (
                  <div
                    key={`pos-${i}`}
                    className={cn(
                      "group relative rounded-xl border border-green-400/20 bg-green-400/5 backdrop-blur-sm p-4 shadow-sm transition",
                      "hover:border-green-400/40 hover:shadow-green-400/10"
                    )}
                  >
                    <p className="text-sm leading-relaxed text-white/90 italic">
                      “{displayText}”
                    </p>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-xs font-medium text-green-300">
                        Confidence: {(r.confidence * 100).toFixed(1)}%
                      </span>
                      {shouldTruncate && (
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedPos((prev) => ({ ...prev, [i]: !isExpanded }))
                          }
                          className="text-xs px-2 py-1 rounded-md bg-green-500/10 text-green-300 hover:bg-green-500/20 focus:outline-none focus:ring-2 focus:ring-green-300/40"
                        >
                          {isExpanded ? "Show less" : "Show more"}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Negative Column */}
            <div className="space-y-4">
              <h4 className="text-red-400 font-bold mb-2">Negative Highlights</h4>
              {topNegative.map((r, i) => {
                const isExpanded = expandedNeg[i];
                const text = r.text || "";
                const previewLimit = 160;
                const shouldTruncate = text.length > previewLimit;
                const displayText = !shouldTruncate
                  ? text
                  : isExpanded
                    ? text
                    : text.slice(0, previewLimit) + "…";
                return (
                  <div
                    key={`neg-${i}`}
                    className={cn(
                      "group relative rounded-xl border border-red-400/20 bg-red-400/5 backdrop-blur-sm p-4 shadow-sm transition",
                      "hover:border-red-400/40 hover:shadow-red-400/10"
                    )}
                  >
                    <p className="text-sm leading-relaxed text-white/90 italic">
                      “{displayText}”
                    </p>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-xs font-medium text-red-300">
                        Confidence: {(r.confidence * 100).toFixed(1)}%
                      </span>
                      {shouldTruncate && (
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedNeg((prev) => ({ ...prev, [i]: !isExpanded }))
                          }
                          className="text-xs px-2 py-1 rounded-md bg-red-500/10 text-red-300 hover:bg-red-500/20 focus:outline-none focus:ring-2 focus:ring-red-300/40"
                        >
                          {isExpanded ? "Show less" : "Show more"}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      )}

      {/* Summary */}
      <Card className="p-6 bg-white/5 border border-white/10">
        <h3 className="text-xl font-semibold mb-4 text-white/90">
          AI Summary
        </h3>
        <p className="text-white/90 text-lg leading-relaxed">
          {summary || "No summary available."}
        </p>
      </Card>

      {/* ✅ Aspect-based highlights with dropdown filter */}
      {Object.keys(aspectExamples || {}).length > 0 && (
        <Card className="p-6 bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-4 gap-4">
            <h3 className="text-xl font-semibold text-white/90">Aspect-based highlights</h3>
            <div className="w-56">
              <Select value={selectedAspect} onValueChange={(v) => setSelectedAspect(v)}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue placeholder="Select aspect" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 text-white border-white/10">
                  {Object.keys(aspectExamples)
                    .sort((a, b) => a.localeCompare(b))
                    .map((a) => (
                      <SelectItem key={a} value={a} className="cursor-pointer">
                        {a}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {selectedAspect && (
            <div className="space-y-4">
              {(() => {
                const aspect = selectedAspect;
                const buckets: any = (aspectExamples as any)[aspect] || { Positive: [], Neutral: [], Negative: [] };
                const counts = aspectsRaw[aspect] || { Positive: 0, Neutral: 0, Negative: 0 };
                const sectionKey = (s: string, i: number) => `${aspect}:${s}:${i}`;
                const renderBucket = (label: "Positive" | "Neutral" | "Negative") => (
                  <div className="space-y-2">
                    <h5
                      className={cn(
                        "text-sm font-semibold",
                        label === "Positive" && "text-green-300",
                        label === "Neutral" && "text-yellow-300",
                        label === "Negative" && "text-red-300"
                      )}
                    >
                      {label} ({counts[label] ?? 0})
                    </h5>
                    <div className="space-y-3">
                      {(buckets as any)[label].map((r: any, i: number) => {
                        const key = sectionKey(label, i);
                        const isExp = !!expandedAspect[key];
                        const text: string = r.text || "";
                        const previewLimit = 160;
                        const shouldTruncate = text.length > previewLimit;
                        const displayText = !shouldTruncate ? text : isExp ? text : text.slice(0, previewLimit) + "…";
                        return (
                          <div
                            key={key}
                            className={cn(
                              "rounded-lg border backdrop-blur-sm p-3 text-sm",
                              label === "Positive" && "border-green-400/20 bg-green-400/5",
                              label === "Neutral" && "border-yellow-400/20 bg-yellow-400/5",
                              label === "Negative" && "border-red-400/20 bg-red-400/5"
                            )}
                          >
                            <p className="text-white/90 italic">“{displayText}”</p>
                            <div className="mt-2 flex items-center justify-between">
                              <span
                                className={cn(
                                  "text-xs font-medium",
                                  label === "Positive" && "text-green-300",
                                  label === "Neutral" && "text-yellow-300",
                                  label === "Negative" && "text-red-300"
                                )}
                              >
                                Confidence: {(r.confidence * 100).toFixed(1)}%
                              </span>
                              {shouldTruncate && (
                                <button
                                  type="button"
                                  onClick={() => setExpandedAspect((p) => ({ ...p, [key]: !isExp }))}
                                  className={cn(
                                    "text-xs px-2 py-1 rounded-md focus:outline-none focus:ring-2",
                                    label === "Positive" && "bg-green-500/10 text-green-300 hover:bg-green-500/20 focus:ring-green-300/40",
                                    label === "Neutral" && "bg-yellow-500/10 text-yellow-300 hover:bg-yellow-500/20 focus:ring-yellow-300/40",
                                    label === "Negative" && "bg-red-500/10 text-red-300 hover:bg-red-500/20 focus:ring-red-300/40"
                                  )}
                                >
                                  {isExp ? "Show less" : "Show more"}
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
                return (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h4 className="text-lg font-semibold text-white/90">{aspect}</h4>
                      <div className="text-xs text-white/70">
                        <span className="mr-3">P: {counts.Positive ?? 0}</span>
                        <span className="mr-3">N: {counts.Negative ?? 0}</span>
                        <span>U: {counts.Neutral ?? 0}</span>
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                      {renderBucket("Positive")}
                      {renderBucket("Neutral")}
                      {renderBucket("Negative")}
                    </div>
                  </div>
                );
              })()}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
