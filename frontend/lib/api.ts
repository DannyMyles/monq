const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface DocumentSummary {
  id: string;
  original_filename: string;
  status: "uploaded" | "processing" | "ready" | "failed";
  page_count: number;
  chunk_count: number;
  classification: string | null;
  classification_reasoning: string | null;
  error_message: string | null;
  created_at: string;
}

export interface SourceOut {
  chunk_index: number;
  page_number: number | null;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceOut[];
}

export interface ChatMessageOut {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON; fall back to statusText
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function uploadDocument(file: File): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<DocumentSummary>(response);
}

export async function getDocument(documentId: string): Promise<DocumentSummary> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`);
  return handleResponse<DocumentSummary>(response);
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
    method: "DELETE",
  });
  return handleResponse<void>(response);
}

export async function sendChatMessage(
  documentId: string,
  question: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handleResponse<ChatResponse>(response);
}
