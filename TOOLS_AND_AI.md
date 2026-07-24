# Tools & AI-Use Summary

## Tools

| Tool | Purpose |
|---|---|
| Claude Code (VS Code extension) | Primary development environment |
| Python 3.10, FastAPI, SQLAlchemy, PyMySQL | Backend framework, ORM, MySQL driver |
| pypdf | PDF text extraction |
| tiktoken | Token counting for chunking |
| Google Gen AI Python SDK (`google-genai`) — `gemini-embedding-001`, `gemini-flash-lite-latest` | Embeddings, classification, chat |
| numpy | Cosine similarity computation for retrieval |
| pytest, httpx (FastAPI `TestClient`) | Backend testing |
| reportlab | Generates a synthetic sample PDF used as a test fixture |
| Next.js 14 (App Router), TypeScript, Tailwind CSS | Frontend framework and styling |
| Jest, React Testing Library, `@testing-library/user-event` | Frontend testing |

## AI Tool Use

**Claude Code (Anthropic, Claude Sonnet 5)** was used as the primary pair-programmer for this
entire assessment, under direct human direction at every step:

- **Requirements clarification**: before writing any code, Claude Code asked clarifying
  questions (LLM/embedding provider choice, API key availability) and produced a written
  implementation plan (architecture, data model, chunking/RAG approach, API contract, build
  order) that was reviewed and approved before implementation began.
- **Backend**: all FastAPI routes, SQLAlchemy models, PDF extraction, chunking algorithm, LLM
  client wrapper (`services/llm_client.py`), classification logic, and cosine-similarity
  retrieval/RAG prompting were drafted by Claude Code.
- **Frontend**: all React components (upload dropzone, document summary, chat panel), the
  typed API client, and page wiring were drafted by Claude Code.
- **Tests**: the full backend pytest suite (chunking edge cases, classification fallback
  behavior, retrieval ranking, upload/chat endpoint behavior) and the frontend Jest/RTL suite
  were drafted by Claude Code alongside the corresponding implementation, not bolted on after.
- **Documentation**: this file, `README.md`, and `DESIGN.md` were drafted by Claude Code based
  on the actual implementation and decisions made during the session.

### Validation performed

- Full backend suite executed and passing (27/27), with all LLM calls mocked at the
  `services/llm_client` boundary so tests run offline and deterministically.
- Full frontend suite executed and passing (10/10).
- `tsc --noEmit` and `next lint` run clean on the frontend.
- End-to-end manual verification against a real local MariaDB instance (schema creation via
  `create_all`, actual `INSERT`/`SELECT` round-trips inspected directly in the database) and a
  real, headless-browser-driven pass through the Next.js UI (upload → error surfaced → status
  badge rendered, zero browser console errors).
- One real bug was caught by this manual browser pass and fixed as a direct result: the upload
  endpoint originally raised a bare HTTP 500 (with no document `id`) when downstream processing
  (extract/embed/classify) failed, so the frontend had no way to show the "failed" status badge
  it was built to render — it just displayed a transient error banner and reset to the upload
  screen. Fixed so the endpoint always returns 201 with the document's `id`/`status`/
  `error_message`, since the document resource genuinely was created even if processing failed.
  Confirmed visually afterward via a headless-browser screenshot showing the corrected badge.

### Mid-project provider switch: OpenAI → Gemini

The app originally shipped against OpenAI (`text-embedding-3-small` + `gpt-4o-mini`), per the
initial provider decision. During live testing, the candidate's OpenAI account repeatedly hit
`insufficient_quota` (no billing configured on the API platform, separate from a paid ChatGPT
consumer subscription — a common point of confusion since they're distinct products/billing
systems under the same company). Rather than block on that, we switched to Google's Gemini API,
which offers a genuinely free tier requiring no payment method. This was a contained change
specifically because all LLM calls were already isolated behind one module boundary
(`services/llm_client.py`, formerly `openai_client.py`): only that file, its two call sites
(`classification.py`, `routers/chat.py`/`routers/documents.py`), config/env vars, and test
mocks needed to change — `chunking.py`, `retrieval.py`'s ranking logic, and all router/schema
code were untouched.

Two things were verified directly against the real Gemini API before finalizing model choices,
using the candidate's actual key:
- `gemini-2.0-flash` (the obvious default choice) returned `429 RESOURCE_EXHAUSTED` with a `0`
  free-tier limit on this account — confirmed by listing models via `client.models.list()` and
  trial-calling several candidates. `gemini-flash-lite-latest` worked (verified with a real JSON
  classification call), so that's what's configured as the default `GEMINI_CHAT_MODEL`.
- Similarly, `text-embedding-004` (Gemini's older embedding model name) 404'd for this key;
  `gemini-embedding-001` worked (verified with both single and batched embedding calls, 3072-dim
  vectors returned). This is now the default `GEMINI_EMBEDDING_MODEL`.

Both models are confirmed working end-to-end with a real key as of this writing; a fresh
account/region could still see different free-tier availability, which is why the README calls
out how to re-check current model availability if this recurs.

**A genuine live pass was completed** (not just mocked tests): uploaded a real PDF through the
running API against real MySQL, got back `status: "ready"`, `classification: "Contract"` with a
sensible one-sentence justification; asked "How many days does the client have to pay an invoice,
and what happens if they are late?" and got back a correct, chunk-cited answer ("...within thirty
(30) days... interest at 1.5% per month... [chunk 0]"); asked an intentionally out-of-scope
question ("What is the CEO's favorite color?") and got the exact designed refusal, "I can't find
that in this document." — confirming the RAG grounding prompt works as intended against a real
model, not just the mocked test suite.

Everything in this repository was reviewed by the candidate before submission; no code was
copied in from an external source unmodified.
