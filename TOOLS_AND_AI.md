# Tools & AI-Use Summary

## Tools

| Tool | Purpose |
|---|---|
| VS Code | IDE |
| Python 3.10, FastAPI, SQLAlchemy, PyMySQL | Backend framework, ORM, MySQL driver |
| pypdf | PDF text extraction |
| tiktoken | Token counting for chunking |
| Google Gen AI Python SDK (`google-genai`) — `gemini-embedding-001`, `gemini-flash-lite-latest` | Embeddings, classification, chat |
| numpy | Cosine similarity computation for retrieval |
| pytest, httpx (FastAPI `TestClient`) | Backend testing |
| reportlab | Generates a synthetic sample PDF used as a test fixture |
| Next.js 14 (App Router), TypeScript, Tailwind CSS | Frontend framework and styling |
| Jest, React Testing Library, `@testing-library/user-event` | Frontend testing |
| Claude (Anthropic) | AI coding assistant |

## AI Tool Use

An AI coding assistant helped implement the backend (routes, models, chunking, classification,
RAG retrieval), frontend (components, API client), and the pytest/Jest test suites, based on
architecture and design decisions I made. I reviewed all the code and validated it myself: the
full test suite passes (27 backend, 10 frontend), and I ran the app end to end against a real
MySQL instance and a real Gemini key with my own PDFs to confirm classification and chat answers
were correct and grounded in the document.
