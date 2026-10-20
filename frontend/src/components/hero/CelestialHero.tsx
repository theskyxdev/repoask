"use client";

import React, { useState } from "react";
import Image from "next/image";
import { GitBranch, Sparkles, ArrowRight, Terminal, Shield, Cpu, Layers } from "lucide-react";

function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
    </svg>
  );
}
const PARTICLES = Array.from({ length: 24 }, (_, i) => ({
  id: i,
  width: `${((i * 7) % 3) + 2}px`,
  height: `${((i * 7) % 3) + 2}px`,
  top: `${35 + ((i * 13) % 55)}%`,
  left: `${5 + ((i * 17) % 90)}%`,
  duration: `${3.5 + (i % 4)}s`,
  delay: `${(i * 0.3).toFixed(1)}s`,
  color: i % 3 === 0 ? "bg-cyan-300/80" : (i % 3 === 1 ? "bg-amber-200/80" : "bg-blue-300/80"),
}));

const STARS = Array.from({ length: 32 }, (_, i) => ({
  id: `star-${i}`,
  width: `${((i * 5) % 2) + 1.5}px`,
  height: `${((i * 5) % 2) + 1.5}px`,
  top: `${4 + ((i * 11) % 40)}%`,
  left: `${3 + ((i * 19) % 94)}%`,
  duration: `${2.5 + (i % 4)}s`,
  delay: `${(i * 0.2).toFixed(2)}s`,
}));

const SHOOTING_STARS = [
  { id: 1, top: "12%", left: "85%", delay: "0s", duration: "6s" },
  { id: 2, top: "22%", left: "95%", delay: "2.8s", duration: "7.5s" },
  { id: 3, top: "8%", left: "65%", delay: "4.5s", duration: "6.2s" },
];

interface CelestialHeroProps {
  onAnalyze: (url: string) => void;
  onSelectDemo: () => void;
  isLoading: boolean;
}

export function CelestialHero({ onAnalyze, onSelectDemo, isLoading }: CelestialHeroProps) {
  const [repoUrl, setRepoUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (repoUrl.trim()) {
      onAnalyze(repoUrl.trim());
    }
  };

  const sampleRepos = [
    { name: "enterprise-auth-service", label: "Instant Demo (Seeded)", isDemo: true },
    { name: "fastapi/fastapi", url: "https://github.com/fastapi/fastapi" },
    { name: "expressjs/express", url: "https://github.com/expressjs/express" },
    { name: "psf/requests", url: "https://github.com/psf/requests" },
  ];

  return (
    <div className="relative min-h-[92vh] w-full flex flex-col justify-between overflow-hidden bg-[#060911] text-white">
      {/* Background Image Container with Ken Burns Moving Animation */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="relative w-full h-full animate-ken-burns will-change-transform scale-105">
          <Image
            src="/hero_bg.jpg"
            alt="RepoAsk Code Intelligence Universe"
            fill
            priority
            className="object-cover object-center opacity-85 brightness-95"
            sizes="100vw"
          />
        </div>

        {/* Floating Glowing Nebula Orbs for Deep Space Atmospheric Motion */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-blue-600/20 blur-[100px] pointer-events-none animate-aurora-drift" />
        <div className="absolute top-1/3 right-1/4 w-[30rem] h-[30rem] rounded-full bg-purple-600/15 blur-[120px] pointer-events-none animate-celestial-pulse" />
        <div className="absolute bottom-1/4 left-1/3 w-80 h-80 rounded-full bg-cyan-500/15 blur-[90px] pointer-events-none animate-aurora-drift" style={{ animationDelay: "-7s" }} />

        {/* Cinematic Vignette and Dark Gradient Overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#060911] via-[#060911]/40 to-black/60" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_20%,rgba(6,9,17,0.85)_90%)]" />

        {/* Dynamic Celestial Particles / Floating Embers & Fireflies */}
        <div className="absolute inset-0 pointer-events-none">
          {PARTICLES.map((p) => (
            <div
              key={p.id}
              className={`absolute rounded-full ${p.color} blur-[1px]`}
              style={{
                width: p.width,
                height: p.height,
                top: p.top,
                left: p.left,
                animation: `floatParticle ${p.duration} ease-in-out infinite`,
                animationDelay: p.delay,
              }}
            />
          ))}

          {/* Twinkling Celestial Stars */}
          {STARS.map((s) => (
            <div
              key={s.id}
              className="absolute rounded-full bg-blue-100 shadow-[0_0_6px_rgba(191,219,254,0.8)]"
              style={{
                width: s.width,
                height: s.height,
                top: s.top,
                left: s.left,
                animation: `twinkleStar ${s.duration} ease-in-out infinite`,
                animationDelay: s.delay,
              }}
            />
          ))}

          {/* Shooting Stars / Meteor Streaks */}
          {SHOOTING_STARS.map((star) => (
            <div
              key={star.id}
              className="absolute h-[2px] w-[140px] bg-gradient-to-r from-transparent via-cyan-200 to-white rounded-full shadow-[0_0_8px_rgba(255,255,255,0.9)]"
              style={{
                top: star.top,
                left: star.left,
                animation: `shootingStar ${star.duration} ease-in-out infinite`,
                animationDelay: star.delay,
              }}
            />
          ))}
        </div>
      </div>

      {/* Top Navigation Bar in Hero */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-6 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center font-serif text-lg tracking-wider shadow-inner">
            R
          </div>
          <span className="font-serif text-xl tracking-wide font-normal text-white">RepoAsk</span>
          <span className="text-xs px-2 py-0.5 rounded-full border border-white/15 bg-white/5 text-slate-300 font-mono">
            v1.0 Staff Engine
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm text-slate-300/80 font-normal">
          <a href="#overview" className="hover:text-white transition-colors duration-150">Overview</a>
          <a href="#architecture" className="hover:text-white transition-colors duration-150">Architecture</a>
          <a href="#security" className="hover:text-white transition-colors duration-150">Security</a>
          <a href="#docs" className="hover:text-white transition-colors duration-150">Documentation</a>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onSelectDemo}
            className="text-xs sm:text-sm px-4 py-1.5 rounded-full border border-white/20 bg-white/10 backdrop-blur-md hover:bg-white/20 hover:border-white/40 transition-all duration-200 text-slate-100 font-medium hover:shadow-[0_0_15px_rgba(255,255,255,0.2)]"
          >
            Launch Demo Workspace
          </button>
        </div>
      </nav>

      {/* Main Hero Content */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 max-w-4xl mx-auto my-auto pt-8 pb-12">
        {/* Animated Subheading Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/15 bg-black/40 backdrop-blur-md mb-6 shadow-lg hover:border-amber-400/40 transition-colors">
          <Sparkles className="h-3.5 w-3.5 text-amber-300 animate-pulse" />
          <span className="text-xs text-slate-200 tracking-wider uppercase font-medium">
            AST Code Intelligence & Retrieval
          </span>
        </div>

        {/* Hero Title */}
        <h1 className="font-serif text-4xl sm:text-6xl md:text-7xl font-normal tracking-tight text-white leading-[1.1] mb-6 drop-shadow-2xl">
          Understand Any Codebase. <br />
          <span className="italic font-light bg-gradient-to-r from-blue-300 via-indigo-100 to-purple-300 bg-clip-text text-transparent">
            In minutes, not hours.
          </span>
        </h1>

        <p className="max-w-2xl text-base sm:text-lg text-slate-200/90 font-normal leading-relaxed mb-10 drop-shadow">
          Understand any GitHub repository in minutes—not hours. Powered by language-aware AST parsing,
          NetworkX dependency mapping, and evidence-backed code citations.
        </p>

        {/* Central Repository Input Bar */}
        <div className="w-full max-w-2xl mx-auto">
          <form
            onSubmit={handleSubmit}
            className="relative flex items-center p-1.5 rounded-2xl bg-black/60 backdrop-blur-xl border border-white/20 shadow-2xl transition-all focus-within:border-blue-400/60 focus-within:ring-2 focus-within:ring-blue-500/20 animate-border-glow"
          >
            <div className="pl-4 pr-2 text-slate-400">
              <GithubIcon className="h-5 w-5" />
            </div>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="Paste public GitHub repository URL (e.g. https://github.com/fastapi/fastapi)..."
              className="flex-1 bg-transparent py-3 text-sm text-white placeholder-slate-400 outline-none font-mono"
            />
            <button
              type="submit"
              disabled={isLoading || !repoUrl.trim()}
              className="px-6 py-3 rounded-xl bg-white text-black text-sm font-medium hover:bg-slate-200 transition-all duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  Indexing...
                </span>
              ) : (
                <>
                  <span>Begin Journey</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Select Popular Samples */}
          <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-xs">
            <span className="text-slate-400 mr-1">Quick Explore:</span>
            {sampleRepos.map((sample) => (
              <button
                key={sample.name}
                type="button"
                onClick={() => {
                  if (sample.isDemo) {
                    onSelectDemo();
                  } else if (sample.url) {
                    setRepoUrl(sample.url);
                    onAnalyze(sample.url);
                  }
                }}
                className="px-3 py-1 rounded-full border border-white/15 bg-white/5 backdrop-blur-md text-slate-300 hover:text-white hover:border-white/30 hover:bg-white/10 transition-all duration-150 font-mono text-[11px]"
              >
                {sample.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Hero Bottom Architectural Badges */}
      <div className="relative z-10 border-t border-white/10 bg-black/40 backdrop-blur-md py-4 px-6">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-around gap-6 text-xs text-slate-400 font-mono">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-slate-300" />
            <span>AST Semantic Chunking</span>
          </div>
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-slate-300" />
            <span>NetworkX Graph Architecture</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-slate-300" />
            <span>Static Security Engine</span>
          </div>
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-slate-300" />
            <span>Evidence-Backed Citations</span>
          </div>
        </div>
      </div>
    </div>
  );
}
