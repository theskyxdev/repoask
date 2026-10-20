"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  GitBranch,
  Search,
  Settings,
  MessageSquare,
  Layers,
  GitGraph,
  Shield,
  FileCheck2,
  BookOpen,
  Code2,
  ArrowUpRight,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
    </svg>
  );
}
import { RepoMetadata } from "@/types";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

import { CelestialHero } from "@/components/hero/CelestialHero";
import { ChatInterface } from "@/components/features/chat/ChatInterface";
import { ArchitectureExplorer } from "@/components/features/architecture/ArchitectureExplorer";
import { DependencyGraphViewer } from "@/components/features/dependency-graph/DependencyGraphViewer";
import { SecurityScannerView } from "@/components/features/security/SecurityScannerView";
import { CodeReviewView } from "@/components/features/review/CodeReviewView";
import { DocumentationView } from "@/components/features/docs/DocumentationView";
import { CodeViewerModal } from "@/components/code-viewer/CodeViewerModal";
import { CodeSearchModal } from "@/components/features/search/CodeSearchModal";
import { SettingsModal } from "@/components/features/settings/SettingsModal";

export default function Home() {
  const [repos, setRepos] = useState<RepoMetadata[]>([]);
  const [selectedRepoId, setSelectedRepoId] = useState<string>("repoask_enterprise_auth");
  const [currentRepo, setCurrentRepo] = useState<RepoMetadata | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "architecture" | "dependency" | "security" | "review" | "docs">("chat");

  // Modals state
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [viewerPath, setViewerPath] = useState<string | null>(null);
  const [viewerStartLine, setViewerStartLine] = useState<number | undefined>(undefined);
  const [viewerEndLine, setViewerEndLine] = useState<number | undefined>(undefined);
  const [viewerSymbol, setViewerSymbol] = useState<string | undefined>(undefined);

  // Settings
  const [geminiApiKey, setGeminiApiKey] = useState<string>("");
  const [isIndexing, setIsIndexing] = useState(false);

  const workspaceRef = useRef<HTMLDivElement | null>(null);

  // Load saved API Key from localStorage
  useEffect(() => {
    try {
      const savedKey = localStorage.getItem("repoask_gemini_key") || "";
      setGeminiApiKey(savedKey);
    } catch {}
  }, []);

  const handleSaveApiKey = (key: string) => {
    setGeminiApiKey(key);
    try {
      localStorage.setItem("repoask_gemini_key", key);
    } catch {}
  };

  // Keyboard shortcut for search (Cmd/Ctrl + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Fetch repositories list
  const fetchRepos = async () => {
    try {
      const list = await api.listRepos();
      setRepos(list);
      if (list.length > 0 && !list.some((r) => r.id === selectedRepoId)) {
        setSelectedRepoId(list[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch repos:", err);
    }
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  // Poll current repository status if indexing
  useEffect(() => {
    if (!selectedRepoId) return;

    let interval: NodeJS.Timeout | null = null;

    const checkStatus = async () => {
      try {
        const repo = await api.getRepo(selectedRepoId);
        setCurrentRepo(repo);
        if (repo.status === "cloning" || repo.status === "parsing" || repo.status === "indexing") {
          setIsIndexing(true);
        } else {
          setIsIndexing(false);
          if (interval) clearInterval(interval);
        }
      } catch (err) {
        console.error("Status fetch error:", err);
      }
    };

    checkStatus();
    interval = setInterval(checkStatus, 2500);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedRepoId]);

  // Clone & Analyze new repo
  const handleAnalyzeRepo = async (url: string) => {
    setIsIndexing(true);
    try {
      const res = await api.cloneRepo(url);
      setSelectedRepoId(res.repo_id);
      fetchRepos();
      // Smooth scroll to workspace
      workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
    } catch (err: any) {
      alert(`Error starting analysis: ${err.message}`);
      setIsIndexing(false);
    }
  };

  // Seed / Launch Demo
  const handleSelectDemo = async () => {
    try {
      const res = await api.seedDemoRepo();
      setSelectedRepoId(res.repo_id);
      await fetchRepos();
      workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
    } catch (err: any) {
      // If already seeded, just select it
      setSelectedRepoId("repoask_enterprise_auth");
      workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Open Code Viewer helper
  const handleOpenCodeViewer = (path: string, startLine?: number, endLine?: number, symbol?: string) => {
    setViewerPath(path);
    setViewerStartLine(startLine);
    setViewerEndLine(endLine || startLine);
    setViewerSymbol(symbol);
  };

  return (
    <div className="min-h-screen bg-[#060911] text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
      {/* 1. CINEMATIC HERO SECTION */}
      <CelestialHero
        onAnalyze={handleAnalyzeRepo}
        onSelectDemo={handleSelectDemo}
        isLoading={isIndexing}
      />

      {/* 2. REPOSITORY WORKSPACE DASHBOARD */}
      <main ref={workspaceRef} className="max-w-7xl mx-auto px-4 sm:px-6 py-12 space-y-8">
        {/* Workspace Top Control Bar */}
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 p-5 rounded-2xl border border-white/10 bg-[#0a0f1d] shadow-2xl">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10">
              <GithubIcon className="h-4 w-4 text-slate-400" />
              <select
                value={selectedRepoId}
                onChange={(e) => setSelectedRepoId(e.target.value)}
                className="bg-transparent text-sm font-semibold text-white outline-none font-mono cursor-pointer"
              >
                {repos.map((r) => (
                  <option key={r.id} value={r.id} className="bg-[#0a0f1d] text-white">
                    {r.owner}/{r.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Status indicator badge */}
            {currentRepo && (
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium ${
                    currentRepo.status === "ready"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : currentRepo.status === "error"
                      ? "bg-red-500/10 text-red-400 border border-red-500/20"
                      : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      currentRepo.status === "ready"
                        ? "bg-emerald-400"
                        : currentRepo.status === "error"
                        ? "bg-red-400"
                        : "bg-blue-400 animate-pulse"
                    }`}
                  />
                  {currentRepo.status === "ready"
                    ? "AST Indexed"
                    : currentRepo.status === "error"
                    ? "Error"
                    : `${currentRepo.status.toUpperCase()} (${currentRepo.progress}%)`}
                </span>
              </div>
            )}
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center gap-2 w-full lg:w-auto justify-end">
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white text-xs font-mono transition-colors"
            >
              <Search className="h-3.5 w-3.5 text-slate-400" />
              <span>Search Code</span>
              <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-black/40 text-slate-400 border border-white/10">
                ⌘K
              </kbd>
            </button>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
              title="Settings & API Key"
            >
              <Settings className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Real-time Progress Bar if currently indexing */}
        {currentRepo && (currentRepo.status === "cloning" || currentRepo.status === "parsing" || currentRepo.status === "indexing") && (
          <div className="p-5 rounded-2xl border border-blue-500/30 bg-blue-500/10 space-y-3 animate-in fade-in">
            <div className="flex items-center justify-between text-xs font-mono text-blue-300">
              <span className="flex items-center gap-2">
                <span className="h-3.5 w-3.5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                {currentRepo.current_step}
              </span>
              <span>{currentRepo.progress}%</span>
            </div>
            <div className="w-full h-1.5 bg-blue-950/60 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-400 transition-all duration-300 rounded-full"
                style={{ width: `${currentRepo.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Repository Metadata Metric Cards */}
        {currentRepo && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl border border-white/5 bg-[#0a0f1d]">
              <span className="text-[11px] font-mono text-slate-500 block">Total Files</span>
              <span className="text-xl font-bold font-mono text-white">
                {formatNumber(currentRepo.stats.total_files)}
              </span>
            </div>
            <div className="p-4 rounded-xl border border-white/5 bg-[#0a0f1d]">
              <span className="text-[11px] font-mono text-slate-500 block">Lines of Code</span>
              <span className="text-xl font-bold font-mono text-white">
                {formatNumber(currentRepo.stats.total_lines)}
              </span>
            </div>
            <div className="p-4 rounded-xl border border-white/5 bg-[#0a0f1d]">
              <span className="text-[11px] font-mono text-slate-500 block">AST Functions</span>
              <span className="text-xl font-bold font-mono text-blue-400">
                {formatNumber(currentRepo.stats.total_functions)}
              </span>
            </div>
            <div className="p-4 rounded-xl border border-white/5 bg-[#0a0f1d]">
              <span className="text-[11px] font-mono text-slate-500 block">AST Classes</span>
              <span className="text-xl font-bold font-mono text-amber-400">
                {formatNumber(currentRepo.stats.total_classes)}
              </span>
            </div>
            <div className="p-4 rounded-xl border border-white/5 bg-[#0a0f1d]">
              <span className="text-[11px] font-mono text-slate-500 block">Primary Stack</span>
              <span className="text-xl font-bold font-mono text-emerald-400">
                {currentRepo.stats.primary_language}
              </span>
            </div>
            <div className="p-4 rounded-xl border border-white/5 bg-[#0a0f1d]">
              <span className="text-[11px] font-mono text-slate-500 block">Vector Index</span>
              <span className="text-xl font-bold font-mono text-purple-400">ChromaDB</span>
            </div>
          </div>
        )}

        {/* Linear/Apple Tab Navigation */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl border border-white/10 bg-[#0a0f1d] max-w-fit overflow-x-auto">
          {[
            { id: "chat", label: "Evidence Chat", icon: MessageSquare },
            { id: "architecture", label: "Architecture", icon: Layers },
            { id: "dependency", label: "Dependency Graph", icon: GitGraph },
            { id: "security", label: "Security Scanner", icon: Shield },
            { id: "review", label: "Code Review", icon: FileCheck2 },
            { id: "docs", label: "Documentation", icon: BookOpen },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono transition-all duration-150 whitespace-nowrap ${
                  isActive
                    ? "bg-white text-black font-semibold shadow-md"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab View Content */}
        <div className="min-h-[600px]">
          {activeTab === "chat" && (
            <ChatInterface
              repoId={selectedRepoId}
              onOpenCitation={handleOpenCodeViewer}
              geminiApiKey={geminiApiKey}
            />
          )}

          {activeTab === "architecture" && (
            <ArchitectureExplorer
              repoId={selectedRepoId}
              onOpenFile={(f) => handleOpenCodeViewer(f)}
            />
          )}

          {activeTab === "dependency" && (
            <DependencyGraphViewer
              repoId={selectedRepoId}
              onOpenFile={(f) => handleOpenCodeViewer(f)}
            />
          )}

          {activeTab === "security" && (
            <SecurityScannerView
              repoId={selectedRepoId}
              onOpenFile={(f, line) => handleOpenCodeViewer(f, line, line)}
            />
          )}

          {activeTab === "review" && (
            <CodeReviewView
              repoId={selectedRepoId}
              onOpenFile={(f, line) => handleOpenCodeViewer(f, line, line)}
            />
          )}

          {activeTab === "docs" && (
            <DocumentationView
              repoId={selectedRepoId}
              geminiApiKey={geminiApiKey}
            />
          )}
        </div>
      </main>

      {/* FOOTER */}
      <footer className="border-t border-white/10 py-8 px-6 text-center text-xs text-slate-500 font-mono mt-20">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-serif text-white font-normal">RepoAsk</span>
            <span>• Understand any GitHub repository in minutes—not hours.</span>
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>FastAPI + ChromaDB</span>
            <span>Next.js 15 + Tailwind</span>
            <span>NetworkX + AST</span>
          </div>
        </div>
      </footer>

      {/* MODALS */}
      <CodeViewerModal
        repoId={selectedRepoId}
        filePath={viewerPath}
        startLine={viewerStartLine}
        endLine={viewerEndLine}
        symbolName={viewerSymbol}
        onClose={() => setViewerPath(null)}
      />

      <CodeSearchModal
        repoId={selectedRepoId}
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelectResult={(filePath, line) => handleOpenCodeViewer(filePath, line, line)}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        geminiApiKey={geminiApiKey}
        onSaveKey={handleSaveApiKey}
      />
    </div>
  );
}
