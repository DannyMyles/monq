# Tools & AI-Use Summary

## Tools

| Tool | Purpose |
|---|---|
| Python 3.10, FastAPI, SQLAlchemy, PyMySQL | Backend framework, ORM, MySQL driver |
| pypdf | PDF text extraction |
| tiktoken | Token counting for chunking |
| Google Gen AI Python SDK (`google-genai`) — `gemini-embedding-001`, `gemini-flash-lite-latest` | Embeddings, classification, chat |
| numpy | Cosine similarity computation for retrieval |
| pytest, httpx (FastAPI `TestClient`) | Backend testing |
| reportlab | Generates a synthetic sample PDF used as a test fixture |
| Next.js 14 (App Router), TypeScript, Tailwind CSS | Frontend framework and styling |
| Jest, React Testing Library, `@testing-library/user-event` | Frontend testing |
| Claude (Anthropic) | Used to speed up development |

## AI Tool Use

I used Claude to speed up development.

I reviewed the code before submission and tested the app end to end myself — real MySQL
instance, real Gemini API key, my own PDFs — confirming upload, classification, and chat all
work correctly and that answers stay grounded in the source document.
