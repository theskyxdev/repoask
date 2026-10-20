"use client";

import React, { useState, useEffect } from "react";
import { Folder, File, ChevronRight, ChevronDown, Layers, Shield, Database, ArrowRight, Activity, Terminal } from "lucide-react";
import { ArchitectureSummary, FileTreeItem, ArchitectureFlow } from "@/types";
import { api } from "@/lib/api";
import { formatBytes } from "@/lib/utils";

interface ArchitectureExplorerProps {
  repoId: string;
  onOpenFile: (filePath: string) => void;
}

export function ArchitectureExplorer({ repoId, onOpenFile }: ArchitectureExplorerProps) {
  const [arch, setArch] = useState<ArchitectureSummary | null>(null);
  const [fileTree, setFileTree] = useState<FileTreeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"flows" | "tree">("flows");
  const [selectedFlow, setSelectedFlow] = useState<"request" | "auth" | "db">("request");

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    Promise.all([api.getArchitecture(repoId), api.getFileTree(repoId)])
      .then(([archData, treeData]) => {
        if (!mounted) return;
        setArch(archData);
        setFileTree(treeData);
        setLoading(false);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error("Architecture load error:", err);
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [repoId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 font-mono text-xs gap-3">
        <div className="h-5 w-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
        <span>Synthesizing system architecture & AST hierarchy...</span>
      </div>
    );
  }

  const currentFlow: ArchitectureFlow | undefined =
    selectedFlow === "request"
      ? arch?.request_flow
      : selectedFlow === "auth"
      ? arch?.auth_flow
      : arch?.database_flow;

  return (
    <div className="space-y-6">
      {/* Top High-Level Architectural Card */}
      <div className="p-6 rounded-2xl border border-white/10 bg-[#0a0f1d] shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">System Architecture Overview</h3>
              <p className="text-xs text-slate-400 font-mono">Synthesized from AST component boundaries</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("flows")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
                activeTab === "flows"
                  ? "bg-white text-black font-semibold shadow-md"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              Execution Flows
            </button>
            <button
              onClick={() => setActiveTab("tree")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
                activeTab === "tree"
                  ? "bg-white text-black font-semibold shadow-md"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              Interactive Folder Tree
            </button>
          </div>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed mb-6 font-sans">
          {arch?.overview}
        </p>

        {/* Badges for Tech Stack & Patterns */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/10">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
              Detected Tech Stack:
            </span>
            <div className="flex flex-wrap gap-2">
              {arch?.tech_stack.map((tech, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md text-xs font-mono bg-white/5 border border-white/10 text-slate-200"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
              Architectural Patterns:
            </span>
            <div className="flex flex-wrap gap-2">
              {arch?.design_patterns.map((pat, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md text-xs font-mono bg-blue-500/10 border border-blue-500/20 text-blue-300"
                >
                  {pat}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area: Flows vs Tree */}
      {activeTab === "flows" ? (
        <div className="p-6 rounded-2xl border border-white/10 bg-[#070b14] space-y-6">
          {/* Flow Selector */}
          <div className="flex flex-wrap items-center gap-3 border-b border-white/10 pb-4">
            <button
              onClick={() => setSelectedFlow("request")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono transition-all ${
                selectedFlow === "request"
                  ? "bg-blue-600 text-white font-medium shadow-md"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              <Activity className="h-4 w-4" />
              <span>HTTP Request Flow</span>
            </button>
            <button
              onClick={() => setSelectedFlow("auth")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono transition-all ${
                selectedFlow === "auth"
                  ? "bg-blue-600 text-white font-medium shadow-md"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              <Shield className="h-4 w-4" />
              <span>Authentication & JWT Flow</span>
            </button>
            <button
              onClick={() => setSelectedFlow("db")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono transition-all ${
                selectedFlow === "db"
                  ? "bg-blue-600 text-white font-medium shadow-md"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              <Database className="h-4 w-4" />
              <span>Database Query Flow</span>
            </button>
          </div>

          {/* Current Flow Description */}
          {currentFlow && (
            <div>
              <div className="mb-6">
                <h4 className="text-base font-semibold text-white mb-1">{currentFlow.title}</h4>
                <p className="text-xs text-slate-400 font-mono">{currentFlow.description}</p>
              </div>

              {/* Step by Step Flow Visualizer */}
              <div className="space-y-4">
                {currentFlow.steps.map((st) => (
                  <div
                    key={st.step}
                    className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-all gap-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-8 w-8 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-300 flex items-center justify-center font-mono font-bold text-xs shrink-0">
                        {st.step}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 text-xs font-mono mb-1">
                          <span className="text-blue-400 font-semibold">{st.actor}</span>
                          <ArrowRight className="h-3 w-3 text-slate-500" />
                          <span className="text-slate-300">{st.target}</span>
                        </div>
                        <p className="text-xs text-slate-300 font-sans">{st.action}</p>
                      </div>
                    </div>

                    {st.file_reference && (
                      <button
                        onClick={() => onOpenFile(st.file_reference!)}
                        className="px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 hover:bg-white/10 text-slate-300 hover:text-white font-mono text-[11px] transition-colors flex items-center gap-1.5 shrink-0"
                      >
                        <Terminal className="h-3.5 w-3.5 text-amber-300" />
                        <span>{st.file_reference}</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Interactive Folder Tree */
        <div className="p-6 rounded-2xl border border-white/10 bg-[#070b14]">
          <h4 className="text-sm font-semibold text-white mb-1">Repository Folder Hierarchy</h4>
          <p className="text-xs text-slate-400 font-mono mb-4">Click any file to inspect full source and line numbers</p>
          <div className="p-4 rounded-xl bg-black/40 border border-white/5 font-mono text-xs">
            {fileTree.map((item, idx) => (
              <FileTreeNode key={idx} item={item} onOpenFile={onOpenFile} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FileTreeNode({ item, onOpenFile }: { item: FileTreeItem; onOpenFile: (path: string) => void }) {
  const [expanded, setExpanded] = useState(true);

  if (item.type === "directory") {
    return (
      <div className="my-1">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 py-1 px-1.5 rounded hover:bg-white/5 text-slate-300 hover:text-white w-full text-left transition-colors"
        >
          {expanded ? <ChevronDown className="h-3.5 w-3.5 text-slate-500" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-500" />}
          <Folder className="h-3.5 w-3.5 text-amber-400/80" />
          <span className="font-semibold">{item.name}</span>
        </button>

        {expanded && item.children && (
          <div className="pl-5 border-l border-white/10 ml-2">
            {item.children.map((child, i) => (
              <FileTreeNode key={i} item={child} onOpenFile={onOpenFile} />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="my-0.5">
      <button
        onClick={() => onOpenFile(item.path)}
        className="flex items-center justify-between gap-2 py-1 px-1.5 rounded hover:bg-white/5 text-slate-400 hover:text-white w-full text-left transition-colors group"
      >
        <div className="flex items-center gap-2">
          <File className="h-3.5 w-3.5 text-slate-500 group-hover:text-blue-400 transition-colors" />
          <span className="group-hover:text-slate-100">{item.name}</span>
        </div>
        {item.size && (
          <span className="text-[10px] text-slate-600 group-hover:text-slate-400 font-mono">
            {formatBytes(item.size)}
          </span>
        )}
      </button>
    </div>
  );
}
