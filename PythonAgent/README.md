# Python Agent Service

A FastAPI service that answers questions using RAG over a small local knowledge base. Designed to be called by a .NET orchestrator over HTTP.

## Stack
- FastAPI + Uvicorn
- LangChain for the RAG pipeline
- Anthropic (Claude) for the LLM
- Local HuggingFace sentence-transformer embeddings (no OpenAI key required)
- FAISS as an in-memory vector store

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env and set ANTHROPIC_API_KEY
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

Swagger docs: http://localhost:8000/docs

## Run with Docker

```bash
copy .env.example .env
# edit .env and set ANTHROPIC_API_KEY (or set MOCK_LLM=true)

docker compose up --build
```

Or without compose:
```bash
docker build -t python-agent .
docker run --rm -p 8000:8000 --env-file .env python-agent
```

Swagger docs: http://localhost:8000/docs

> To run this service together with the .NET orchestrator on one shared network, use the **root-level** `docker-compose.yml` instead (`docker compose up --build` from the repo root) — see the [top-level README](../README.md). This service's own `docker-compose.yml` is for running it standalone.

## Endpoints

### GET /health
Returns `{ "status": "ok" }`.

### POST /ask
Request:
```json
{ "question": "Does this candidate's experience match the BDO job description?" }
```

Response:
```json
{
  "answer": "...",
  "source_snippets": [
    { "source": "resume.txt", "snippet": "..." }
  ]
}
```

## Data
Add or edit `.txt` files under `data/` — they're loaded, chunked, and embedded once at startup.

## Mock LLM mode
Set `MOCK_LLM=true` in `.env` to run the service without an Anthropic API key. Retrieval (embeddings + FAISS) still runs for real; the LLM call is replaced with a fixed placeholder response, so you can verify the pipeline end-to-end for free.
