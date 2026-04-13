# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup & Running

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL + pgvector
docker compose up -d

# Run server (with hot reload)
uvicorn app.main:app --reload --port 8000
```

API docs at http://localhost:8000/docs. Health check at http://localhost:8000/health.

**Required env vars** (in `.env`):
- `ANTHROPIC_API_KEY` — required for LLM responses
- `DATABASE_URL` — defaults to local PostgreSQL

Optional: `UPLOAD_DIR`, `CHUNK_SIZE` (default 800), `CHUNK_OVERLAP` (default 100), `RETRIEVAL_TOP_K` (default 5).

## Architecture

This is an async-first RAG (Retrieval-Augmented Generation) system where Claude can iteratively retrieve document chunks to answer questions.

**Data flow:**
1. **Ingest:** Upload → parse (PDF/DOCX/TXT) → chunk with overlap → embed (sentence-transformers) → store in pgvector
2. **Query:** Question → embed → cosine similarity search → top-K chunks → Claude
3. **Agentic loop:** Claude may call the `search_documents` tool up to 3 times to fetch additional context before producing its final answer

**Layer structure:**
- `app/api/` — FastAPI routers (`documents.py`, `qa.py`)
- `app/services/document_processor.py` — file parsing and smart chunking (preserves paragraph/sentence boundaries)
- `app/services/embedding_service.py` — singleton SentenceTransformer (`all-MiniLM-L6-v2`, 384-dim), runs in thread pool to avoid blocking the event loop
- `app/services/retrieval_service.py` — pgvector cosine-distance search with optional document_id filtering
- `app/services/llm_service.py` — Claude API with `thinking={"type": "adaptive"}`, accumulates and deduplicates retrieved chunks across tool-call rounds
- `app/models.py` — `Document` (metadata) and `DocumentChunk` (text + vector), with cascade delete
- `app/config.py` — pydantic-settings, all config from environment
- `app/database.py` — async SQLAlchemy session factory, initializes pgvector extension on startup

**Key non-obvious behaviors:**
- Embedding uses `asyncio.get_event_loop().run_in_executor(None, ...)` to stay non-blocking
- Sources are deduplicated by `(document_id, chunk_index)` and truncated to 200-char previews
- PDFs preserve page numbers; DOCX/TXT chunks have `page_number=None`
- Deleting a document cascades to all its chunks (`cascade="all, delete-orphan"`)
- The agentic loop hard-caps at 3 search tool calls per question
