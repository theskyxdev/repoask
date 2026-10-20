"use client";

import React, { useState, useEffect } from "react";
import { Search, Code2, Box, FileText, ArrowRight, CornerDownRight, X } from "lucide-react";
import { SearchResultItem } from "@/types";
import { api } from "@/lib/api";

interface CodeSearchModalProps {
  repoId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectResult: (filePath: string, line: number) => void;
}

export function CodeSearchModal({ repoId, isOpen, onClose, onSelectResult }: CodeSearchModalProps) {
  const [query, setQuery] = useState("");
  const [searchType, setSearchType] = useState<"all" | "functions" | "classes" | "imports">("all");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query.trim() || !isOpen) {
      setResults([]);
      return;
    }

    const timer = setTimeout(() => {
      setLoading(true);
      api
        .searchRepo(repoId, query.trim(), searchType)
        .then((res) => {
          setResults(res);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }, 200);

    return () => clearTimeout(timer);
  }, [query, searchType, repoId, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150 p-4">
      <div className="w-full max-w-2xl rounded-2xl border border-white/15 bg-[#0a0f1d] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-white/10 bg-[#0d1326] gap-3">
          <Search className="h-5 w-5 text-slate-400 shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search functions, classes, imports (e.g. login, JWTAuthMiddleware, router)..."
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none font-mono"
          />
          {query && (
            <button onClick={() => setQuery("")} className="text-slate-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          )}
          <button onClick={onClose} className="text-xs px-2 py-1 rounded bg-white/5 border border-white/10 text-slate-400 hover:text-white font-mono">
            ESC
          </button>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-white/10 bg-[#080c18] font-mono text-xs">
          {(["all", "functions", "classes", "imports"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setSearchType(type)}
              className={`px-2.5 py-1 rounded-md capitalize transition-colors ${
                searchType === type
                  ? "bg-blue-600 text-white font-semibold"
                  : "bg-white/5 text-slate-400 hover:bg-white/10"
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2">
          {loading && (
            <div className="flex items-center justify-center py-12 text-xs font-mono text-slate-400 gap-2">
              <div className="h-4 w-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              <span>Scanning AST symbol index...</span>
            </div>
          )}

          {!loading && results.length === 0 && query && (
            <div className="py-12 text-center text-xs text-slate-500 font-mono">
              No symbols matching &quot;{query}&quot;
            </div>
          )}

          {!loading && !query && (
            <div className="py-12 text-center text-xs text-slate-500 font-mono">
              Type to search functions, classes, and imported modules.
            </div>
          )}

          {results.map((res, i) => (
            <button
              key={i}
              onClick={() => {
                onSelectResult(res.file_path, res.line_number);
                onClose();
              }}
              className="w-full p-3 rounded-xl hover:bg-white/[0.06] transition-colors flex items-center justify-between text-left group"
            >
              <div className="flex items-center gap-3 truncate">
                <div className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 group-hover:text-blue-400 shrink-0">
                  {res.type === "class" ? <Box className="h-4 w-4" /> : <Code2 className="h-4 w-4" />}
                </div>
                <div className="truncate">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-white group-hover:text-blue-200">
                      {res.name}
                    </span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-white/5 text-slate-400 border border-white/10">
                      {res.type}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-slate-500 truncate block">
                    {res.file_path}:{res.line_number}
                  </span>
                </div>
              </div>

              <CornerDownRight className="h-4 w-4 text-slate-600 group-hover:text-white shrink-0 ml-2" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
