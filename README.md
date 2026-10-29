# Legal Intelligence RAG System

A full-stack legal research application for Indian Supreme Court judgments. It combines case analytics and search with retrieval-augmented answers grounded in retrieved judgment passages.

> This project is for legal research and information only. It is not a substitute for advice from a qualified lawyer.

## Features

- Search Supreme Court judgments and view case details.
- Explore analytics, including case-year, judge, entity, and case-type distributions.
- Sign up, log in, and access protected API endpoints.
- Ask legal research questions and receive answers based on retrieved judgment passages, with sources and citations.
- Use a Next.js frontend and a FastAPI backend.

## Technology

- **Frontend:** Next.js, React, TypeScript
- **Backend:** FastAPI, Uvicorn, SQLite
- **Retrieval:** ChromaDB, Sentence Transformers
- **Answer generation:** OpenRouter API

## Requirements

- Python 3.10 or later
- Node.js and npm
- Judgment database and ChromaDB vector index (see [Data files](#data-files))
- An OpenRouter API key to use question answering

## Run locally on Windows

Open two Command Prompt windows from the project directory.

### 1. Configure the backend

Create and activate a virtual environment, then install the backend packages:

```cmd
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r backend\requirements.txt
python -m pip install chromadb sentence-transformers
```

Create a `.env` file in the project root with your own values:

```env
AUTH_SECRET_KEY=replace_with_a_long_random_secret
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
```

Keep `.env` private. Do not commit API keys or other credentials.

Start the API:

```cmd
uvicorn backend.app:app --reload
```

The backend runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Start the frontend

In the second Command Prompt window:

```cmd
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Data files

The judgment database and vector index are local generated assets and are not included in this repository. The backend expects:

- `data\legal_dataset.db`
- `vector_db\`

Provide a database containing the expected case and metadata tables and a ChromaDB index with the `legal_judgments` collection before using search, analytics, or retrieval. The embedding and reranking models are `all-MiniLM-L6-v2` and `cross-encoder/ms-marco-MiniLM-L-6-v2`; Sentence Transformers may download them the first time they are used.

## API overview

- `GET /api/health` — health check
- `POST /api/auth/signup` and `POST /api/auth/login` — account access
- `GET /api/cases` and `GET /api/cases/{case_id}` — browse judgments
- `GET /api/search?q=...` — search judgments
- `POST /api/ask` — ask a question grounded in retrieved sources
- `GET /docs` — interactive API documentation

Most application endpoints require authentication.

## Repository hygiene

Local secrets, virtual environments, caches, datasets, embeddings, and vector indexes should stay out of version control. Review `git status` before pushing to confirm that no private keys or local data are staged.
