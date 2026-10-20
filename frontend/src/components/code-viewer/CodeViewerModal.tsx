"use client";

import React, { useEffect, useState, useRef } from "react";
import { X, Copy, Check, FileCode, ExternalLink, Code } from "lucide-react";
import { api } from "@/lib/api";

interface CodeViewerModalProps {
  repoId: string;
  filePath: string | null;
  startLine?: number;
  endLine?: number;
  symbolName?: string;
  onClose: () => void;
}

export function CodeViewerModal({
  repoId,
  filePath,
  startLine,
  endLine,
  symbolName,
  onClose,
}: CodeViewerModalProps) {
  const [content, setContent] = useState<string>("");
  const [lines, setLines] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const highlightedRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!filePath || !repoId) return;

    let isMounted = true;
    setLoading(true);

    api
      .getFileContent(repoId, filePath)
      .then((data) => {
        if (!isMounted) return;
        setContent(data.content);
        setLines(data.lines);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setContent(`// Error loading file: ${err.message}`);
        setLines([`// Error loading file: ${err.message}`]);
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [repoId, filePath]);

  useEffect(() => {
    if (highlightedRef.current) {
      highlightedRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [lines, startLine]);

  if (!filePath) return null;

  const handleCopy = () => {
    let copyText = content;
    if (startLine && endLine && lines.length >= endLine) {
      copyText = lines.slice(startLine - 1, endLine).join("\n");
    }
    navigator.clipboard.writeText(copyText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl h-full bg-[#0a0f1d] border-l border-white/10 flex flex-col shadow-2xl animate-in slide-in-from-right duration-250">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-[#0d1326]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-300">
              <FileCode className="h-5 w-5" />
            </div>
            <div className="truncate">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-semibold text-white truncate">{filePath}</span>
                {startLine && endLine && (
                  <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-mono">
                    L{startLine}–L{endLine}
                  </span>
                )}
              </div>
              {symbolName && (
                <p className="text-xs text-slate-400 font-mono mt-0.5">Symbol: <span className="text-amber-300">{symbolName}</span></p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="p-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
              title="Copy snippet"
            >
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
              title="Close viewer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Code Content Body */}
        <div className="flex-1 overflow-auto p-4 font-mono text-xs leading-relaxed bg-[#060911]">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-3">
              <div className="h-6 w-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Retrieving source file...</span>
            </div>
          ) : (
            <div className="table w-full">
              {lines.map((lineText, idx) => {
                const lineNum = idx + 1;
                const isHighlighted = startLine && endLine ? lineNum >= startLine && lineNum <= endLine : false;
                const isFirstHighlight = startLine ? lineNum === startLine : false;

                return (
                  <div
                    key={lineNum}
                    ref={isFirstHighlight ? highlightedRef : null}
                    className={`table-row transition-colors duration-150 ${
                      isHighlighted
                        ? "bg-blue-500/15 border-l-2 border-blue-400 text-blue-100 font-medium"
                        : "hover:bg-white/[0.03] text-slate-300"
                    }`}
                  >
                    {/* Line number */}
                    <span
                      className={`table-cell pr-4 pl-2 select-none text-right w-12 font-mono ${
                        isHighlighted ? "text-blue-400 font-bold" : "text-slate-600"
                      }`}
                    >
                      {lineNum}
                    </span>
                    {/* Code text */}
                    <span className="table-cell whitespace-pre font-mono pl-2">
                      {lineText || " "}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="px-6 py-3 border-t border-white/10 bg-[#0d1326] flex items-center justify-between text-xs text-slate-400 font-mono">
          <span>Total lines: {lines.length}</span>
          <span>RepoAsk AST Code Intelligence</span>
        </div>
      </div>
    </div>
  );
}
