# Design Document — AI-Powered Procurement Document Assistant

## 1. High-Level Architecture

```
                     ┌─────────────────────┐
                     │   Next.js Frontend   │
                     │  (upload + chat UI)  │
                     └──────────┬───────────┘
                                │ REST (fetch, JSON / multipart)
                                ▼
                     ┌─────────────────────┐
                     │   FastAPI Backend    │
                     │  routers/documents   │
                     │  routers/chat        │
                     └──────────┬───────────┘
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
     services/pdf_extract  services/chunking  services/classification
             │                  │                  │
             └────────┬─────────┴─────────┬────────┘
                      ▼                   ▼
             services/llm_client     services/retrieval
                      │                   │
                      ▼                   ▼
             Gemini API (embeddings,   MySQL (documents, chunks,
             chat completions)         chat_messages)
```

The flow for a single "current document" session:

1. **Upload** — user drops a PDF in the Next.js UI → `POST /api/documents/upload`.
2. **Extract & chunk** — backend extracts text per page (`pypdf`), splits it into
   paragraph-aware, token-budgeted chunks with overlap.
3. **Vectorize** — all chunks for the document are embedded in a single batched Gemini
   embeddings call and stored (as JSON arrays) alongside the chunk text in MySQL.
4. **Classify** — a single Gemini chat call classifies the document into one of 9 standard
   procurement types.
5. **Chat (RAG)** — user asks a question → question is embedded → cosine similarity ranks
   all stored chunk embeddings for that document → top-k chunks are passed to a Gemini chat
   call with a grounding system prompt → grounded answer + cited chunks returned.

Both upload processing and classification run **synchronously** in the request/response
cycle. This is a deliberate scope decision: the brief allows a single-document flow with no
production-grade infra requirement, and assessment-sized PDFs process in a few seconds. A
production system handling large documents or concurrent uploads would move extraction/
embedding/classification to a background job queue (e.g. Celery/RQ) with the API returning
immediately with `status=processing` and the frontend polling `GET /{id}`. The status field
already models this (`uploaded → processing → ready | failed`) precisely so that upgrade path
doesn't require a data-model change.

**Why Python/FastAPI over Node.js/NestJS for the backend**: this service is dominated by
text/NLP-adjacent work — PDF extraction, token-aware chunking, embedding calls, cosine-similarity
ranking — and Python's ecosystem for that (`pypdf`, `tiktoken`, `numpy`) is more mature and
ergonomic than the Node.js equivalents, and it's where the LLM/RAG tooling ecosystem is most
mature and best-documented right now. FastAPI gives the same things NestJS is valued for — typed
request/response models, dependency injection (`Depends`), automatic OpenAPI docs — with less
structural boilerplate for a single-service scope like this one; NestJS's heavier module/DI
conventions pay off more at multi-team, multi-service scale than they would here. This was a
fit-for-purpose call, not a gap — I write comfortably in NestJS as well, and would reach for it
without hesitation on a more service-heavy, multi-team backend.

## 2. API Contract

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| POST | `/api/documents/upload` | `multipart/form-data`, field `file` | 201 `DocumentSummary` | 400 non-PDF, 422 empty file, 413 over size limit. A downstream processing error (extraction/embedding/classification) still returns **201** with `status="failed"` and `error_message` set — the document resource was created, so its id/status stay visible to the client rather than being lost behind a bare error response. Only request-validation failures (bad file, empty file, too large) are actual 4xx errors. |
| GET | `/api/documents/{id}` | — | 200 `DocumentSummary` | 404 unknown id |
| GET | `/api/documents/{id}/chunks` | — | 200 `ChunkOut[]` | Debug/transparency endpoint — no embeddings in the payload |
| POST | `/api/documents/{id}/chat` | `{"question": string}` | 200 `{"answer": string, "sources": SourceOut[]}` | 404 unknown id, 409 if not yet `ready`, 422 empty question |
| GET | `/api/documents/{id}/messages` | — | 200 `ChatMessageOut[]` | Chat history, for UI reload |
| DELETE | `/api/documents/{id}` | — | 204 | Clears the "current document" slot for a new upload |

```ts
DocumentSummary = {
  id: string; original_filename: string;
  status: "uploaded" | "processing" | "ready" | "failed";
  page_count: number; chunk_count: number;
  classification: string | null; classification_reasoning: string | null;
  error_message: string | null; created_at: string;
}
SourceOut = { chunk_index: number; page_number: number | null; snippet: string; score: number }
```

## 3. Data Model (MySQL via SQLAlchemy)

**documents** — `id` (CHAR(36) PK), `original_filename`, `stored_path`, `page_count`,
`status`, `classification`, `classification_reasoning`, `error_message`, `created_at`,
`updated_at`.

**chunks** — `id` (PK), `document_id` (FK), `chunk_index`, `text` (TEXT), `token_count`,
`page_number`, `embedding` (JSON — 3072-length float array from `gemini-embedding-001`),
`created_at`.

**chat_messages** — `id` (PK), `document_id` (FK), `role` (`user`/`assistant`), `content`,
`created_at`. Backs both the reloadable chat history endpoint and the last-N-turns context
window included in RAG prompts for follow-up questions.

**Why embeddings live in a MySQL JSON column instead of a dedicated vector DB**: the brief
explicitly permits "in-memory" vector storage and a single-document scope. Cosine similarity
is computed in Python (`numpy`) over all of a document's chunks at query time — a full O(n)
scan. For a single document with a few dozen to a few hundred chunks this is fast (single-digit
milliseconds) and keeps the whole stack to "just MySQL," which was a hard requirement here.
The explicit tradeoff: no ANN index (ivfflat/HNSW), so this would not scale to
many-thousands-of-chunks-per-query or true multi-document corpus search. If that were needed,
the natural upgrade is pgvector (keeps SQL, adds ANN indexing) or a managed vector DB
(Pinecone/Weaviate) — the `retrieval.py` interface (`rank_chunks(query_embedding, chunks,
top_k)`) is already isolated behind a small module boundary specifically so that swap wouldn't
touch the rest of the app.

## 4. Chunking Strategy

1. Extract text **per page** with `pypdf`.
2. Split each page's text into **paragraphs** on blank lines; collapse internal whitespace.
3. Greedily pack paragraphs into a chunk until adding the next one would exceed a
   **500-token budget** (`tiktoken` `cl100k_base`), then close the chunk and start the next.
4. Seed each new chunk with the **last 75 tokens** (~15%) of the previous chunk before adding
   new paragraphs — overlap.
5. **Fallback**: if a single paragraph itself exceeds the token budget (e.g. a long unbroken
   clause), it's split on sentence boundaries and packed the same way; if even a single
   sentence exceeds the budget (pathological run-on text), it's hard-split by raw token count.

**Why paragraph-aware over fixed-character chunking**: procurement documents are structured —
clauses, line items, definitions — and a paragraph is usually the smallest self-contained
semantic unit. Cutting mid-sentence (as naive fixed-length chunking does) frequently splits a
clause's subject from its condition (e.g. "the penalty is 5%" / "per day of delay" ending up in
different chunks), which directly hurts retrieval precision. Packing whole paragraphs up to a
token budget keeps chunks semantically coherent while still bounding embedding/context cost.

**Why overlap**: even with paragraph-aware packing, a chunk boundary can still fall between two
paragraphs that are logically related (e.g. an SLA metric defined in one paragraph, its remedy
in the next). A 15% trailing-token overlap means a fact spanning that boundary still appears
whole in at least one chunk, at a modest (~15%) storage/embedding cost.

## 5. Classification

A single Gemini chat completion (`gemini-flash-lite-latest`, JSON response mode, temperature 0)
is given the first ~8,000 characters of extracted text (a document's opening — title, parties,
purpose — is almost always sufficient to identify its type, and capping input keeps the call
cheap) and a system prompt enumerating the 9 supported types: **Contract, RFP / RFQ, Quote /
Proposal, Invoice, SLA, Amendment, NDA, Purchase Order, Other**. The model returns
`{"type": ..., "reasoning": ...}`; any unrecognized or unparsable response is defaulted to
`Other` rather than surfaced as an error, since misclassification into an existing category
would be worse than an honest "couldn't confidently classify."

An LLM (rather than keyword/regex rules) was chosen because procurement documents vary widely
in phrasing across vendors and industries — an NDA might be titled "Confidentiality Agreement,"
a Purchase Order might just be labeled "PO #4471" — and a zero-shot classifier generalizes to
that variation far better than a maintained keyword list, at the cost of one cheap LLM call per
upload.

## 6. RAG Approach

1. Embed the user's question (`gemini-embedding-001`, 1 call).
2. Load all of the current document's chunk embeddings and rank them by cosine similarity
   against the question embedding (`services/retrieval.rank_chunks`); take the **top 5**
   (`RAG_TOP_K`, configurable).
3. Build the prompt: a system message instructs the model to answer **only** from the labeled
   context blocks (`[chunk N, page P]`), to cite the chunks it uses inline (`[chunk N]`), and —
   critically — to respond with a fixed, literal "I can't find that in this document." sentence
   if the context is insufficient, rather than let it improvise a hedge that could still smuggle
   in outside knowledge.
4. The last 3 turns of conversation (`CHAT_HISTORY_TURNS`) are included as prior messages so
   follow-up questions ("and what about the renewal clause?") resolve correctly.
5. One chat completion call returns the answer; the API response also returns the ranked
   `sources` (chunk index, page, snippet, similarity score) so the frontend can show citations
   the user can verify against the source text.

**Grounding tradeoff, stated explicitly**: rather than a hard numeric similarity cutoff (e.g.
"only include chunks scoring > 0.75"), grounding is enforced primarily through the system
prompt plus a fixed refusal string. A hard cutoff is brittle — the right threshold varies by
document and embedding model, and a too-strict cutoff can starve the model of a
borderline-relevant chunk it actually needed. Always sending the top-k (even if all scores are
mediocre) and relying on prompting to say "not found" when the content genuinely isn't there
was the more robust choice for a small, single-document corpus; it's called out here as a place
a numeric threshold could be layered in later if false-positive "confident but wrong" answers
became a problem in practice.

## 7. Testing

Backend tests run against an in-memory SQLite database (a deliberate test-only substitution for
MySQL — SQLAlchemy abstracts the dialect and the JSON column type works identically on both;
this keeps the suite fast and dependency-free while MySQL remains the actual dev/prod target)
and mock all Gemini calls through the `services/llm_client` module boundary, so the suite
never makes a network call. See `README.md` for how to run both suites.
