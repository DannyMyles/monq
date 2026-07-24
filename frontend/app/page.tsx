"use client";

import { useState } from "react";
import UploadDropzone from "@/components/UploadDropzone";
import DocumentSummary from "@/components/DocumentSummary";
import ChatPanel, { type ChatPanelMessage } from "@/components/ChatPanel";
import {
  ApiError,
  deleteDocument,
  sendChatMessage,
  uploadDocument,
  type DocumentSummary as DocumentSummaryType,
} from "@/lib/api";

export default function Home() {
  const [document, setDocument] = useState<DocumentSummaryType | null>(null);
  const [messages, setMessages] = useState<ChatPanelMessage[]>([]);
  const [uploading, setUploading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileSelected(file: File) {
    setError(null);
    setUploading(true);
    setMessages([]);
    try {
      const doc = await uploadDocument(file);
      setDocument(doc);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  async function handleSend(question: string) {
    if (!document) return;
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setSending(true);
    try {
      const response = await sendChatMessage(document.id, question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer, sources: response.sources },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to get an answer. Please retry.");
    } finally {
      setSending(false);
    }
  }

  async function handleReset() {
    if (document) {
      try {
        await deleteDocument(document.id);
      } catch {
        // best-effort cleanup; proceed to reset the UI regardless
      }
    }
    setDocument(null);
    setMessages([]);
    setError(null);
  }

  return (
    <main className="min-h-screen bg-cream">
      <div className="mx-auto flex max-w-3xl flex-col gap-10 px-6 py-10 sm:px-10 sm:py-14">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-accent">
            <span className="h-2 w-2 rounded-full bg-accent" />
          </span>
          <span className="font-serif text-lg tracking-wide text-ink">Procurement Assistant</span>
        </div>

        <header className="text-center">
          <h1 className="text-balance font-serif text-4xl leading-tight text-ink sm:text-5xl">
            Ask your procurement{" "}
            <span className="rounded bg-accent-light px-2 py-0.5">documents</span>
            <br />
            anything.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-balance font-serif text-lg italic text-ink-muted">
            Upload a contract, RFP, invoice, or SLA — we&apos;ll classify it and ground every
            answer in what it actually says.
          </p>
        </header>

        {error && (
          <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        )}

        {!document ? (
          <UploadDropzone onFileSelected={handleFileSelected} disabled={uploading} />
        ) : (
          <DocumentSummary document={document} onReset={handleReset} />
        )}

        {document && document.status === "ready" && (
          <div className="min-h-[420px] flex-1">
            <ChatPanel messages={messages} onSend={handleSend} sending={sending} />
          </div>
        )}
      </div>
    </main>
  );
}
