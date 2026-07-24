"use client";

import type { DocumentSummary as DocumentSummaryType } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  uploaded: "bg-ink/5 text-ink-muted",
  processing: "bg-accent-light/60 text-accent-dark",
  ready: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-700",
};

interface DocumentSummaryProps {
  document: DocumentSummaryType;
  onReset: () => void;
}

export default function DocumentSummary({ document, onReset }: DocumentSummaryProps) {
  return (
    <div className="flex flex-col gap-4 rounded-4xl border border-ink/10 bg-cream-card p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-serif text-lg text-ink">{document.original_filename}</p>
          <p className="mt-0.5 text-xs text-ink-muted">
            {document.page_count} page{document.page_count === 1 ? "" : "s"} ·{" "}
            {document.chunk_count} chunk{document.chunk_count === 1 ? "" : "s"}
          </p>
        </div>
        <button
          onClick={onReset}
          className="whitespace-nowrap rounded-full border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink transition-colors hover:bg-ink hover:text-cream-card"
        >
          Upload a different document
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
            STATUS_STYLES[document.status] ?? STATUS_STYLES.uploaded
          }`}
        >
          {document.status}
        </span>
        {document.classification && (
          <span className="rounded-full bg-ink px-2.5 py-1 text-xs font-medium text-cream-card">
            {document.classification}
          </span>
        )}
      </div>

      {document.classification_reasoning && (
        <p className="font-serif text-sm italic leading-relaxed text-ink-light">
          {document.classification_reasoning}
        </p>
      )}

      {document.status === "failed" && document.error_message && (
        <p className="rounded-2xl bg-red-50 px-3 py-2 text-xs text-red-700">
          {document.error_message}
        </p>
      )}
    </div>
  );
}
