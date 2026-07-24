import { render, screen, fireEvent } from "@testing-library/react";
import DocumentSummary from "@/components/DocumentSummary";
import type { DocumentSummary as DocumentSummaryType } from "@/lib/api";

const baseDocument: DocumentSummaryType = {
  id: "doc-1",
  original_filename: "agreement.pdf",
  status: "ready",
  page_count: 3,
  chunk_count: 12,
  classification: "SLA",
  classification_reasoning: "Mentions uptime guarantees and service credits.",
  error_message: null,
  created_at: new Date().toISOString(),
};

describe("DocumentSummary", () => {
  it("renders filename, status, and classification", () => {
    render(<DocumentSummary document={baseDocument} onReset={jest.fn()} />);

    expect(screen.getByText("agreement.pdf")).toBeInTheDocument();
    expect(screen.getByText("ready")).toBeInTheDocument();
    expect(screen.getByText("SLA")).toBeInTheDocument();
    expect(screen.getByText(/3 pages/)).toBeInTheDocument();
  });

  it("shows the error message when the document failed", () => {
    render(
      <DocumentSummary
        document={{ ...baseDocument, status: "failed", error_message: "Extraction failed" }}
        onReset={jest.fn()}
      />
    );
    expect(screen.getByText("Extraction failed")).toBeInTheDocument();
  });

  it("calls onReset when the reset button is clicked", () => {
    const onReset = jest.fn();
    render(<DocumentSummary document={baseDocument} onReset={onReset} />);

    fireEvent.click(screen.getByText("Upload a different document"));

    expect(onReset).toHaveBeenCalled();
  });
});
