"use client";

import React, { useState, useEffect } from "react";
import { Shield, ShieldAlert, ShieldCheck, AlertCircle, Terminal, ExternalLink, CheckCircle } from "lucide-react";
import { SecurityScanReport, SecurityVulnerability } from "@/types";
import { api } from "@/lib/api";

interface SecurityScannerViewProps {
  repoId: string;
  onOpenFile: (filePath: string, startLine?: number) => void;
}

export function SecurityScannerView({ repoId, onOpenFile }: SecurityScannerViewProps) {
  const [report, setReport] = useState<SecurityScanReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    api
      .getSecurityReport(repoId)
      .then((data) => {
        if (!mounted) return;
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error("Security scan error:", err);
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [repoId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 font-mono text-xs gap-3">
        <div className="h-5 w-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
        <span>Executing AST security rules (Secrets, Injections, Weak JWTs)...</span>
      </div>
    );
  }

  const score = report?.security_score ?? 100;
  const vulns = report?.vulnerabilities || [];
  const filtered = filterSeverity === "ALL" ? vulns : vulns.filter((v) => v.severity === filterSeverity);

  return (
    <div className="space-y-6">
      {/* Top Score Banner */}
      <div className="p-6 rounded-2xl border border-white/10 bg-[#0a0f1d] shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div
            className={`h-16 w-16 rounded-2xl border flex items-center justify-center font-mono text-2xl font-bold shadow-lg ${
              score >= 85
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : score >= 60
                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                : "bg-red-500/10 border-red-500/30 text-red-400"
            }`}
          >
            {score}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-white">Repository Security Health</h3>
              {score >= 85 ? (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono">
                  <ShieldCheck className="h-3.5 w-3.5" /> High Assurance
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-mono">
                  <ShieldAlert className="h-3.5 w-3.5" /> Attention Required
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">{report?.summary}</p>
          </div>
        </div>

        {/* Severity Count Pills */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="px-3 py-1.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex flex-col items-center">
            <span className="font-bold text-sm">{report?.critical_count || 0}</span>
            <span className="text-[10px]">CRITICAL</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex flex-col items-center">
            <span className="font-bold text-sm">{report?.high_count || 0}</span>
            <span className="text-[10px]">HIGH</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-300 flex flex-col items-center">
            <span className="font-bold text-sm">{report?.medium_count || 0}</span>
            <span className="text-[10px]">MEDIUM</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex flex-col items-center">
            <span className="font-bold text-sm">{report?.low_count || 0}</span>
            <span className="text-[10px]">LOW</span>
          </div>
        </div>
      </div>

      {/* Vulnerabilities Filter Bar */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
          Findings ({filtered.length})
        </span>

        <div className="flex items-center gap-1.5 font-mono text-xs">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1 rounded-lg transition-all ${
                filterSeverity === sev
                  ? "bg-white text-black font-semibold shadow"
                  : "bg-white/5 text-slate-400 hover:bg-white/10"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Vulnerabilities List */}
      {filtered.length === 0 ? (
        <div className="p-12 rounded-2xl border border-white/10 bg-[#070b14] text-center flex flex-col items-center justify-center">
          <div className="p-3 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-3">
            <CheckCircle className="h-6 w-6" />
          </div>
          <h4 className="text-sm font-semibold text-white mb-1">No Security Vulnerabilities Detected</h4>
          <p className="text-xs text-slate-400 max-w-md font-mono">
            Static AST analysis verified zero instances of exposed secrets, raw SQL injection string concatenation, or unsafe dynamic evaluations.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((v) => (
            <div
              key={v.id}
              className="p-5 rounded-2xl border border-white/10 bg-[#0a0f1d] hover:border-white/20 transition-all shadow-lg space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      v.severity === "CRITICAL"
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : v.severity === "HIGH"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                    }`}
                  >
                    {v.severity}
                  </span>
                  <h4 className="text-sm font-semibold text-white font-sans">{v.title}</h4>
                  <span className="text-xs text-slate-500 font-mono">• {v.category}</span>
                </div>

                <button
                  onClick={() => onOpenFile(v.file_path, v.line_number)}
                  className="px-3 py-1 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white font-mono text-xs flex items-center gap-1.5 transition-colors"
                >
                  <Terminal className="h-3.5 w-3.5 text-blue-400" />
                  <span>{v.file_path}:{v.line_number}</span>
                </button>
              </div>

              <p className="text-xs text-slate-300 font-sans leading-relaxed">{v.description}</p>

              {/* Code Snippet Box */}
              <div className="p-3 rounded-xl bg-black/60 border border-white/5 font-mono text-xs text-slate-300 overflow-x-auto">
                <span className="text-[10px] text-slate-500 block mb-1">Detected Pattern:</span>
                <code>{v.snippet}</code>
              </div>

              {/* Remediation Guide */}
              <div className="p-3 rounded-xl bg-blue-500/5 border border-blue-500/10 text-xs text-slate-300 font-sans flex items-start gap-2.5">
                <ShieldCheck className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-blue-300">Recommended Remediation: </span>
                  <span>{v.remediation}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
