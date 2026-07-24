# Procurement Document Assistant

Upload a procurement PDF (contract, RFP, invoice, SLA, ...), have it classified into a standard
procurement type, and chat with it using retrieval-augmented generation grounded in the
document's own text.

See [`DESIGN.md`](DESIGN.md) for architecture, API contract, data model, chunking strategy, and
RAG approach. See [`TOOLS_AND_AI.md`](TOOLS_AND_AI.md) for tools used and AI-assistance
disclosure.

## Screenshots

### 1. Upload a PDF

![Upload screen](docs/screenshots/1-upload.png)

### 2. Automatic classification

![Classification result](docs/screenshots/2-classification.png)

### 3. Chat, grounded in the document (with expandable sources)

![Grounded chat with sources](docs/screenshots/3-chat.png)

## Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, MySQL (PyMySQL driver), Google Gemini API
  (`gemini-embedding-001` for embeddings, `gemini-flash-lite-latest` for classification/chat).
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS.
- **Tests**: pytest (backend), Jest + React Testing Library (frontend).

## Prerequisites

- Python 3.10+
- Node.js 18+
- A running MySQL (or MariaDB) server
- A Google Gemini API key (free tier available at [aistudio.google.com](https://aistudio.google.com) — no billing required to get started)

## 1. Database Setup

Create a database and user (adjust credentials as you like — they must match `DATABASE_URL` in
your `.env`):

```sql
CREATE DATABASE monq CHARACTER SET utf8mb4;
CREATE USER 'monq_user'@'localhost' IDENTIFIED BY 'monq_password';
GRANT ALL PRIVILEGES ON monq.* TO 'monq_user'@'localhost';
FLUSH PRIVILEGES;
```

Tables are created automatically on backend startup (`Base.metadata.create_all`) — no separate
migration step is needed for this assessment's scope.

## 2. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set DATABASE_URL to match the DB you created above, and set GEMINI_API_KEY

uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).

To get a `GEMINI_API_KEY`: sign in at [aistudio.google.com](https://aistudio.google.com) →
**Get API key** → **Create API key**. The free tier needs no payment method, though note some
newer models (e.g. `gemini-2.0-flash`) can return `429 RESOURCE_EXHAUSTED` with a `0` free-tier
limit on some accounts/regions — if that happens, call `client.models.list()` (or check
[ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models)) for which
models currently have free quota on your account, and set `GEMINI_CHAT_MODEL` accordingly;
`gemini-flash-lite-latest` and `gemini-embedding-001` were confirmed working on the free tier as
of this writing.

### Backend environment variables (`backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://monq_user:monq_password@localhost:3306/monq` | SQLAlchemy connection string |
| `GEMINI_API_KEY` | — (required) | Used for both embeddings and chat/classification |
| `GEMINI_CHAT_MODEL` | `gemini-flash-lite-latest` | Classification + chat model |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model |
| `CHUNK_TOKEN_BUDGET` | `500` | Max tokens per chunk |
| `CHUNK_TOKEN_OVERLAP` | `75` | Overlap tokens between consecutive chunks |
| `RAG_TOP_K` | `5` | Number of chunks retrieved per chat question |
| `MAX_UPLOAD_MB` | `20` | Upload size limit |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed frontend origins |

### Running backend tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

Tests use an in-memory SQLite database and mock all Gemini calls — no network access or real
API key is required to run the suite.

## 3. Frontend Setup

```bash
cd frontend
npm install

cp .env.local.example .env.local
# defaults to http://localhost:8000 for the backend — adjust if different

npm run dev
```

The app is now at `http://localhost:3000`.

### Running frontend tests

```bash
cd frontend
npm test
```

## 4. Using the App

1. Open `http://localhost:3000`.
2. Drag & drop (or click to browse) a PDF. The backend extracts text, chunks it, embeds the
   chunks, and classifies the document — the UI shows a status badge and the classification
   once ready.
3. Ask questions about the document in the chat panel. Each answer shows the source chunks
   (with page numbers) it was grounded in, expandable under "Sources."
4. Click "Upload a different document" to clear the current document and start over.

## Assumptions & Out-of-Scope (see DESIGN.md for details)

- Single "current document" flow — no multi-document library or multi-user auth.
- Upload processing (extract → chunk → embed → classify) runs synchronously; a background job
  queue would be the natural next step for large documents or concurrent uploads.
- No database migrations tool (Alembic) — schema is created via `create_all`, appropriate for
  this assessment's scope but not for an evolving production schema.
- Retrieval is a full O(n) cosine-similarity scan per chat question rather than an ANN index —
  appropriate at single-document scale (see DESIGN.md §3 for the upgrade path).
