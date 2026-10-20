"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Code2, Bot, User, Copy, Check, FileText, CornerDownRight } from "lucide-react";
import { ChatMessage, Citation } from "@/types";
import { api } from "@/lib/api";

interface ChatInterfaceProps {
  repoId: string;
  onOpenCitation: (filePath: string, startLine?: number, endLine?: number, symbolName?: string) => void;
  geminiApiKey?: string;
}

export function ChatInterface({ repoId, onOpenCitation, geminiApiKey }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const samplePrompts = [
    "Where is JWT implemented?",
    "Explain the login flow and authentication middleware.",
    "Where is database session management configured?",
    "Show all domain models and schemas.",
    "Where are background tasks or asynchronous handlers defined?",
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || loading) return;

    setInputQuery("");
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: q,
      citations: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const response = await api.chatQuery(repoId, q, conversationId, geminiApiKey);
      setConversationId(response.conversation_id);
      setMessages((prev) => [...prev, response.message]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `Error retrieving answer: ${err.message || "Failed to communicate with index engine."}`,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-[750px] w-full rounded-2xl border border-white/10 bg-[#070b14] overflow-hidden shadow-2xl">
      {/* Top Chat Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-white/10 bg-[#0a0f1d]">
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">Repository Code Intelligence</h3>
            <p className="text-[11px] text-slate-400 font-mono">AST semantic index • Evidence-backed answers only</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Verified Citations Active
          </span>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto py-12">
            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 text-slate-300 mb-4">
              <Sparkles className="h-6 w-6 text-amber-300" />
            </div>
            <h4 className="text-base font-medium text-white mb-2">Ask anything about this codebase</h4>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              RepoAsk answers strictly using retrieved AST structures. Every claim includes clickable evidence
              citing exact files and line numbers.
            </p>

            <div className="w-full space-y-2 text-left">
              <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block mb-1">
                Suggested Natural Language Queries:
              </span>
              {samplePrompts.map((prompt, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSend(prompt)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.08] hover:border-white/15 text-left text-xs text-slate-300 transition-all flex items-center justify-between group"
                >
                  <span className="font-mono truncate">{prompt}</span>
                  <CornerDownRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-white transition-colors" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
          >
            <div className="flex items-center gap-2 mb-1.5 text-xs text-slate-400 font-mono">
              {msg.role === "user" ? (
                <>
                  <span>Developer</span>
                  <User className="h-3.5 w-3.5 text-slate-400" />
                </>
              ) : (
                <>
                  <Bot className="h-3.5 w-3.5 text-blue-400" />
                  <span className="text-blue-300 font-medium">RepoAsk Assistant</span>
                </>
              )}
            </div>

            <div
              className={`max-w-[85%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-blue-600/90 text-white border border-blue-500/30 font-medium"
                  : "bg-[#0f1527] text-slate-200 border border-white/10 shadow-lg"
              }`}
            >
              <div className="whitespace-pre-wrap font-sans space-y-2">
                {msg.content}
              </div>

              {/* Citations Box (Clickable Evidence) */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-white/10">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono font-semibold text-slate-300 mb-2">
                    <Code2 className="h-3.5 w-3.5 text-amber-300" />
                    <span>Evidence & Verified Code References (Click to inspect):</span>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {msg.citations.map((citation, citIdx) => (
                      <button
                        key={citIdx}
                        type="button"
                        onClick={() =>
                          onOpenCitation(
                            citation.file_path,
                            citation.start_line,
                            citation.end_line,
                            citation.symbol_name
                          )
                        }
                        className="group flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 hover:bg-blue-500/10 hover:border-blue-400/50 transition-all duration-150 text-left"
                      >
                        <FileText className="h-3.5 w-3.5 text-slate-400 group-hover:text-blue-400 transition-colors" />
                        <div className="flex flex-col font-mono text-[11px]">
                          <span className="text-slate-200 font-medium group-hover:text-blue-200 truncate max-w-[200px]">
                            {citation.file_path}
                          </span>
                          <span className="text-slate-400 text-[10px]">
                            Lines {citation.start_line}–{citation.end_line}
                            {citation.symbol_name ? ` • ${citation.symbol_name}` : ""}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Copy message button */}
              {msg.role === "assistant" && (
                <div className="mt-3 flex justify-end">
                  <button
                    onClick={() => handleCopyText(msg.id, msg.content)}
                    className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-white transition-colors"
                  >
                    {copiedId === msg.id ? (
                      <>
                        <Check className="h-3 w-3 text-emerald-400" />
                        <span>Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        <span>Copy Answer</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 text-slate-400 text-xs font-mono py-2">
            <div className="h-4 w-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
            <span>Parsing AST context and generating evidence citations...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-white/10 bg-[#0a0f1d]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center rounded-xl bg-black/50 border border-white/10 focus-within:border-white/30 transition-all p-1"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask a question about this repository (e.g. 'Where is JWT implemented?', 'Explain login flow')..."
            className="flex-1 bg-transparent px-4 py-2.5 text-xs sm:text-sm text-white placeholder-slate-500 outline-none font-mono"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="p-2.5 rounded-lg bg-white text-black hover:bg-slate-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
