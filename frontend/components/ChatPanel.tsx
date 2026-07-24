"use client";

import { useState } from "react";
import type { SourceOut } from "@/lib/api";

export interface ChatPanelMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceOut[];
}

interface ChatPanelProps {
  messages: ChatPanelMessage[];
  onSend: (question: string) => void;
  disabled?: boolean;
  sending?: boolean;
}

export default function ChatPanel({ messages, onSend, disabled, sending }: ChatPanelProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || disabled || sending) return;
    onSend(trimmed);
    setQuestion("");
  }

  return (
    <div className="flex h-full flex-col gap-4 rounded-4xl border border-ink/10 bg-cream-card p-6 shadow-sm">
      <div className="flex-1 space-y-3 overflow-y-auto">
        {messages.length === 0 && (
          <p className="font-serif text-base italic text-ink-muted">
            Ask a question about this document to get started.
          </p>
        )}
        {messages.map((message, i) => (
          <div
            key={i}
            className={`rounded-2xl px-4 py-2.5 text-sm ${
              message.role === "user"
                ? "ml-auto max-w-[80%] bg-ink text-cream-card"
                : "mr-auto max-w-[80%] border border-ink/10 bg-white text-ink"
            }`}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
            {message.sources && message.sources.length > 0 && (
              <details className="mt-2 text-xs text-ink-muted">
                <summary className="cursor-pointer select-none font-medium text-accent-dark">
                  Sources ({message.sources.length})
                </summary>
                <ul className="mt-1.5 space-y-1.5">
                  {message.sources.map((source) => (
                    <li key={source.chunk_index} className="rounded-xl bg-cream/70 p-2">
                      chunk {source.chunk_index}
                      {source.page_number !== null ? `, page ${source.page_number}` : ""} —{" "}
                      {source.snippet}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
        {sending && <p className="font-serif text-sm italic text-ink-muted">Thinking…</p>}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={disabled || sending}
          placeholder="Ask a question about this document…"
          className="flex-1 rounded-full border border-ink/15 bg-white px-4 py-2.5 text-sm text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none disabled:bg-ink/5"
          aria-label="Question"
        />
        <button
          type="submit"
          disabled={disabled || sending || !question.trim()}
          className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-cream-card transition-colors hover:bg-ink-light disabled:bg-ink/20 disabled:text-ink-muted"
        >
          Send
        </button>
      </form>
    </div>
  );
}
