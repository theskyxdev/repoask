"use client";

import React, { useState } from "react";
import { Settings, Key, Database, Cpu, Check, X, Shield } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  geminiApiKey: string;
  onSaveKey: (key: string) => void;
}

export function SettingsModal({ isOpen, onClose, geminiApiKey, onSaveKey }: SettingsModalProps) {
  const [keyInput, setKeyInput] = useState(geminiApiKey);
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onSaveKey(keyInput.trim());
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-150 p-4">
      <div className="w-full max-w-lg rounded-2xl border border-white/15 bg-[#0a0f1d] shadow-2xl p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-white/5 border border-white/10 text-slate-300">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Engine Configuration</h3>
              <p className="text-xs text-slate-400 font-mono">RepoAsk LLM & Vector Store Parameters</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Key className="h-3.5 w-3.5 text-amber-300" />
              <span>Gemini API Key (Optional)</span>
            </label>
            <input
              type="password"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              placeholder="AIzaSy... (Leave empty to use RepoAsk Local Engine)"
              className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white placeholder-slate-500 font-mono outline-none focus:border-white/30"
            />
            <p className="text-[11px] text-slate-500 font-mono mt-1">
              Keys are stored securely in your browser session and passed in queries.
            </p>
          </div>

          {/* Engine Specs */}
          <div className="space-y-2 pt-2 border-t border-white/10">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
              Active Engine Capabilities:
            </span>
            <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5 text-blue-400" /> Model:
                </span>
                <span className="text-white font-medium">Gemini 2.5 Flash / Local AST Fallback</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-emerald-400" /> Vector Database:
                </span>
                <span className="text-emerald-400 font-medium">ChromaDB (Cosine HNSW)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5 text-purple-400" /> Embeddings:
                </span>
                <span className="text-purple-300 font-medium">BAAI/bge-small-en-v1.5</span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:text-white text-xs font-mono"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-white text-black text-xs font-semibold hover:bg-slate-200 transition-colors flex items-center gap-1.5"
            >
              {saved ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-600" />
                  <span>Saved!</span>
                </>
              ) : (
                <span>Save Configuration</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
