"use client";

import { useRef, useState } from "react";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export default function UploadDropzone({ onFileSelected, disabled }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(file: File | undefined) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a PDF file.");
      return;
    }
    onFileSelected(file);
  }

  return (
    <div
      data-testid="upload-dropzone"
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (disabled) return;
        handleFile(e.dataTransfer.files[0]);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`group flex flex-col items-center justify-center gap-4 rounded-4xl border-2 border-dashed p-14 text-center transition-colors ${
        disabled
          ? "cursor-not-allowed border-ink/10 bg-ink/[0.02] text-ink-muted"
          : "cursor-pointer border-ink/15 bg-cream-card hover:border-accent/60 hover:bg-accent-light/10"
      } ${isDragging ? "border-accent bg-accent-light/20" : ""}`}
    >
      <div
        className={`flex h-14 w-14 items-center justify-center rounded-full transition-colors ${
          disabled ? "bg-ink/5 text-ink-muted" : "bg-accent-light/50 text-accent-dark group-hover:bg-accent-light"
        }`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          className="h-6 w-6"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 16.5V4.5m0 0-4 4m4-4 4 4M4 16.5v2.25A2.25 2.25 0 0 0 6.25 21h11.5A2.25 2.25 0 0 0 20 18.75V16.5"
          />
        </svg>
      </div>
      <div>
        <p className="font-serif text-xl text-ink">
          {disabled ? "Processing…" : "Drag & drop a PDF here"}
        </p>
        <p className="mt-1 text-sm text-ink-muted">
          {disabled ? "This can take a few seconds" : "or click to browse — contracts, RFPs, invoices, SLAs, and more"}
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        disabled={disabled}
        onChange={(e) => handleFile(e.target.files?.[0])}
        aria-label="Upload PDF"
      />
    </div>
  );
}
