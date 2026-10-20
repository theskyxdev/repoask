"use client";

import React, { useState, useEffect } from "react";
import { CheckSquare, AlertTriangle, Zap, FileText, Trash2, BookOpen, Terminal, Sparkles } from "lucide-react";
import { CodeReviewReport, CodeReviewItem } from "@/types";
import { api } from "@/lib/api";

interface CodeReviewViewProps {
  repoId: string;
  onOpenFile: (filePath: string, line?: number) => void;
}

export function CodeReviewView({ repoId, onOpenFile }: CodeReviewViewProps) {
  const [report, setReport] = useState<CodeReviewReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string>("ALL");

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    api
      .getCodeReview(repoId)
      .then((data) => {
        if (!mounted) return;
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error("Code review error:", err);
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [repoId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 font-mono text-xs gap-3">
        <div className="h-5 w-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
        <span>Analyzing code health, cyclomatic complexity, dead code & large files...</span>
      </div>
    );
  }

  const items = report?.items || [];
  const score = report?.review_score ?? 90;

  const categories = [
    { id: "ALL", label: "All Items" },
    { id: "performance", label: "Performance" },
    { id: "dead_code", label: "Dead Code" },
    { id: "large_file", label: "Large Files" },
    { id: "unused_import", label: "Unused Imports" },
    { id: "best_practice", label: "Best Practices" },
  ];

  const filtered = activeCategory === "ALL" ? items : items.filter((it) => it.category === activeCategory);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl border border-white/10 bg-[#0a0f1d] shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div className="h-16 w-16 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center font-mono text-2xl font-bold shadow-lg">
            {score}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-white">Automated Code Quality Audit</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 font-mono border border-purple-500/20">
                Staff Reviewer v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">{report?.summary}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Total Action Items:</span>
          <span className="text-sm font-bold font-mono text-white px-3 py-1 rounded-lg bg-white/5 border border-white/10">
            {items.length}
          </span>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-3.5 py-1.5 rounded-xl transition-all ${
              activeCategory === cat.id
                ? "bg-white text-black font-semibold shadow"
                : "bg-white/5 text-slate-400 hover:bg-white/10"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Suggestions List */}
      {filtered.length === 0 ? (
        <div className="p-12 rounded-2xl border border-white/10 bg-[#070b14] text-center flex flex-col items-center justify-center">
          <Sparkles className="h-6 w-6 text-purple-400 mb-2" />
          <h4 className="text-sm font-semibold text-white mb-1">Clean Implementation</h4>
          <p className="text-xs text-slate-400 font-mono">No items found matching the selected category filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl border border-white/10 bg-[#0a0f1d] hover:border-white/20 transition-all shadow-lg space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-purple-500/15 text-purple-300 border border-purple-500/25">
                    {item.category.replace("_", " ")}
                  </span>
                  <h4 className="text-sm font-semibold text-white font-sans">{item.title}</h4>
                </div>

                <button
                  onClick={() => onOpenFile(item.file_path, item.line_number)}
                  className="px-3 py-1 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white font-mono text-xs flex items-center gap-1.5 transition-colors"
                >
                  <Terminal className="h-3.5 w-3.5 text-purple-400" />
                  <span>{item.file_path}:{item.line_number}</span>
                </button>
              </div>

              <p className="text-xs text-slate-300 font-sans leading-relaxed">{item.suggestion}</p>

              {item.code_snippet && (
                <div className="p-2.5 rounded-lg bg-black/50 border border-white/5 font-mono text-[11px] text-slate-400">
                  <code>{item.code_snippet}</code>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
