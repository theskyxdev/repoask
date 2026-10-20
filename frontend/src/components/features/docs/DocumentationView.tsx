"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, FileText, Download, Copy, Check, Sparkles, RefreshCw } from "lucide-react";
import { GeneratedDoc } from "@/types";
import { api } from "@/lib/api";

interface DocumentationViewProps {
  repoId: string;
  geminiApiKey?: string;
}

export function DocumentationView({ repoId, geminiApiKey }: DocumentationViewProps) {
  const [docType, setDocType] = useState<string>("readme");
  const [currentDoc, setCurrentDoc] = useState<GeneratedDoc | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const docOptions = [
    { id: "readme", label: "README.md", desc: "Production repository readme with badges and quickstart" },
    { id: "architecture", label: "Architecture Guide", desc: "Component boundaries, data flow & patterns" },
    { id: "folder_structure", label: "Folder Tree Guide", desc: "Annotated directory structure explanation" },
    { id: "api", label: "API Specification", desc: "Endpoints, interfaces, and function signatures" },
    { id: "developer_guide", label: "Developer Guide", desc: "Local setup, prerequisites, and test guidelines" },
  ];

  const handleGenerate = async (typeToGen = docType) => {
    setLoading(true);
    try {
      const doc = await api.generateDoc(repoId, typeToGen, geminiApiKey);
      setCurrentDoc(doc);
    } catch (err) {
      console.error("Doc gen error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleGenerate(docType);
  }, [repoId, docType]);

  const handleCopy = () => {
    if (!currentDoc) return;
    navigator.clipboard.writeText(currentDoc.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!currentDoc) return;
    const blob = new Blob([currentDoc.markdown_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${repoId}_${currentDoc.doc_type}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Top Selector Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {docOptions.map((opt) => (
          <button
            key={opt.id}
            onClick={() => setDocType(opt.id)}
            className={`p-4 rounded-xl border text-left transition-all ${
              docType === opt.id
                ? "border-blue-500 bg-blue-500/10 ring-1 ring-blue-500/30"
                : "border-white/10 bg-[#0a0f1d] hover:border-white/20"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <FileText className={`h-4 w-4 ${docType === opt.id ? "text-blue-400" : "text-slate-400"}`} />
              <span className="font-mono text-xs font-semibold text-white">{opt.label}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug line-clamp-2">{opt.desc}</p>
          </button>
        ))}
      </div>

      {/* Document Viewer Container */}
      <div className="rounded-2xl border border-white/10 bg-[#070b14] overflow-hidden shadow-2xl">
        {/* Document Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-[#0a0f1d]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-300">
              <BookOpen className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white font-mono">{currentDoc?.title || "Generating Document..."}</h3>
              <span className="text-[11px] text-slate-400 font-mono">Export-ready Markdown</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleGenerate(docType)}
              disabled={loading}
              className="p-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
              title="Regenerate"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={handleCopy}
              disabled={!currentDoc}
              className="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white font-mono text-xs flex items-center gap-1.5 transition-colors"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? "Copied" : "Copy Markdown"}</span>
            </button>
            <button
              onClick={handleDownload}
              disabled={!currentDoc}
              className="px-3 py-1.5 rounded-lg bg-white text-black hover:bg-slate-200 font-mono text-xs flex items-center gap-1.5 transition-colors font-medium"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download .md</span>
            </button>
          </div>
        </div>

        {/* Markdown Document Content */}
        <div className="p-8 font-sans text-sm text-slate-200 leading-relaxed max-w-4xl mx-auto overflow-y-auto max-h-[650px]">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3 font-mono text-xs">
              <div className="h-5 w-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              <span>Extracting AST signatures & compiling documentation...</span>
            </div>
          ) : (
            <div className="prose prose-invert max-w-none whitespace-pre-wrap font-mono text-xs sm:text-sm bg-black/40 p-6 rounded-xl border border-white/5">
              {currentDoc?.markdown_content}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
