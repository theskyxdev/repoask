"use client";

import React, { useState, useEffect, useRef } from "react";
import { GitGraph, AlertTriangle, Layers, ExternalLink, RefreshCw, ZoomIn, ZoomOut, Filter } from "lucide-react";
import { DependencyGraphData, DependencyNode } from "@/types";
import { api } from "@/lib/api";

interface DependencyGraphViewerProps {
  repoId: string;
  onOpenFile: (filePath: string) => void;
}

export function DependencyGraphViewer({ repoId, onOpenFile }: DependencyGraphViewerProps) {
  const [data, setData] = useState<DependencyGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<DependencyNode | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [filterQuery, setFilterQuery] = useState("");

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    api
      .getDependencyGraph(repoId)
      .then((res) => {
        if (!mounted) return;
        setData(res);
        if (res.nodes.length > 0) {
          setSelectedNode(res.nodes[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error("Dependency graph error:", err);
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
        <span>Calculating NetworkX dependency topology...</span>
      </div>
    );
  }

  const nodes = data?.nodes || [];
  const edges = data?.edges || [];
  const circulars = data?.circular_dependencies || [];
  const hubModules = data?.hub_modules || [];

  const filteredNodes = filterQuery
    ? nodes.filter((n) => n.name.toLowerCase().includes(filterQuery.toLowerCase()) || n.path.toLowerCase().includes(filterQuery.toLowerCase()))
    : nodes;

  return (
    <div className="space-y-6">
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-white/10 bg-[#0a0f1d] shadow-lg">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>Total Modules</span>
            <Layers className="h-4 w-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-white">{nodes.length}</p>
          <span className="text-[11px] text-slate-500 font-mono">Discovered source files</span>
        </div>

        <div className="p-4 rounded-xl border border-white/10 bg-[#0a0f1d] shadow-lg">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>Import Edges</span>
            <GitGraph className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-white">{edges.length}</p>
          <span className="text-[11px] text-slate-500 font-mono">Inter-module relations</span>
        </div>

        <div className="p-4 rounded-xl border border-white/10 bg-[#0a0f1d] shadow-lg">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>Circular Dependencies</span>
            <AlertTriangle className={`h-4 w-4 ${circulars.length > 0 ? "text-amber-400" : "text-emerald-400"}`} />
          </div>
          <p className="text-2xl font-bold font-mono text-white">{circulars.length}</p>
          <span className={`text-[11px] font-mono ${circulars.length > 0 ? "text-amber-400 font-medium" : "text-slate-500"}`}>
            {circulars.length > 0 ? "Requires decoupling" : "Zero circular loops"}
          </span>
        </div>
      </div>

      {/* Circular Dependencies Alert if any */}
      {circulars.length > 0 && (
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-200 text-xs font-mono flex items-start gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Detected Cyclic Dependency Loop:</span>
            <p className="text-[11px] text-amber-300/80 mt-1">
              {circulars.map((c, i) => (
                <span key={i} className="block">{c.join(" ➔ ")}</span>
              ))}
            </p>
          </div>
        </div>
      )}

      {/* Main Interactive Graph & Inspector Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Graph Canvas */}
        <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-[#070b14] overflow-hidden flex flex-col shadow-2xl h-[520px]">
          {/* Controls bar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-[#0a0f1d]">
            <div className="flex items-center gap-2">
              <Filter className="h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                placeholder="Filter module by name..."
                className="bg-black/40 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-white placeholder-slate-500 outline-none font-mono w-44"
              />
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.2))}
                className="p-1.5 rounded border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300"
                title="Zoom Out"
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <span className="text-xs font-mono text-slate-400 w-12 text-center">{Math.round(zoomLevel * 100)}%</span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(1.8, z + 0.2))}
                className="p-1.5 rounded border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300"
                title="Zoom In"
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* SVG Canvas */}
          <div className="flex-1 overflow-auto p-8 relative flex items-center justify-center bg-[radial-gradient(#ffffff08_1px,transparent_1px)] [background-size:16px_16px]">
            <div
              className="flex flex-wrap items-center justify-center gap-6 transition-transform duration-200"
              style={{ transform: `scale(${zoomLevel})` }}
            >
              {filteredNodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                const isHub = hubModules.includes(node.id);

                return (
                  <button
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`p-3.5 rounded-xl border text-left transition-all duration-150 flex flex-col gap-1 w-48 shadow-lg ${
                      isSelected
                        ? "border-blue-400 bg-blue-600/20 ring-2 ring-blue-500/20"
                        : isHub
                        ? "border-amber-400/50 bg-[#0d152b] hover:border-amber-400"
                        : "border-white/10 bg-[#0a0f1d] hover:border-white/30"
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className="font-mono text-xs font-semibold text-white truncate">{node.name}</span>
                      {isHub && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">
                          HUB
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-[10px] text-slate-400 truncate">{node.path}</span>
                    <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500 mt-1 pt-1 border-t border-white/5">
                      <span>Imports: {node.imports_count}</span>
                      <span>By: {node.imported_by_count}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Selected Node Inspector */}
        <div className="rounded-2xl border border-white/10 bg-[#0a0f1d] p-6 flex flex-col justify-between shadow-2xl h-[520px]">
          {selectedNode ? (
            <div className="space-y-4 overflow-y-auto">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Module Inspector</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20">
                  {selectedNode.type}
                </span>
              </div>

              <div>
                <h4 className="text-base font-semibold text-white font-mono">{selectedNode.name}</h4>
                <p className="text-xs text-slate-400 font-mono mt-0.5 break-all">{selectedNode.path}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2">
                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <span className="text-[10px] font-mono text-slate-500 block">Dependencies (Out)</span>
                  <span className="text-lg font-bold font-mono text-white">{selectedNode.imports_count}</span>
                </div>
                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <span className="text-[10px] font-mono text-slate-500 block">Dependents (In)</span>
                  <span className="text-lg font-bold font-mono text-white">{selectedNode.imported_by_count}</span>
                </div>
              </div>

              {/* Connected edges */}
              <div className="pt-2">
                <span className="text-xs font-mono text-slate-400 block mb-2">Connected Target Modules:</span>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge, i) => (
                      <div
                        key={i}
                        className="p-2 rounded-lg bg-white/[0.02] border border-white/5 text-[11px] font-mono flex items-center justify-between"
                      >
                        <span className="text-slate-300 truncate">
                          {edge.source === selectedNode.id ? `➔ ${edge.target}` : `⬅ from ${edge.source}`}
                        </span>
                        <span className="text-[10px] text-slate-500 uppercase">{edge.type}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs font-mono">
              <span>Select any module to inspect dependencies</span>
            </div>
          )}

          {selectedNode && (
            <button
              onClick={() => onOpenFile(selectedNode.path)}
              className="w-full mt-4 py-2.5 rounded-xl bg-white text-black text-xs font-medium hover:bg-slate-200 transition-colors flex items-center justify-center gap-2"
            >
              <span>Inspect Source Code</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
