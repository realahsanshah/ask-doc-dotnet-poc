# Python Agent Service

A FastAPI service that answers questions using RAG over a small local knowledge base. Designed to be called by a .NET orchestrator over HTTP.

## Stack

- FastAPI + Uvicorn
- LangChain for the RAG pipeline
- Anthropic (Claude) **or** any OpenAI-compatible provider (e.g. OpenRouter) for the LLM — see [Choosing an LLM provider](#choosing-an-llm-provider)
- Local HuggingFace sentence-transformer embeddings (no LLM API key required for retrieval itself)
- FAISS as an in-memory vector store

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env — see "Choosing an LLM provider" below
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Run with Docker

```bash
copy .env.example .env
# edit .env — see "Choosing an LLM provider" below (or set MOCK_LLM=true)

docker compose up --build
```

Or without compose:

```bash
docker build -t python-agent .
docker run --rm -p 8000:8000 --env-file .env python-agent
```

Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)

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

## Choosing an LLM provider

Set `LLM_PROVIDER` in `.env` to pick which real LLM answers questions. Retrieval (embeddings + FAISS) is local either way and doesn't need any of these keys.

- `LLM_PROVIDER=anthropic` (default) — requires `ANTHROPIC_API_KEY`. Model is read from `ANTHROPIC_MODEL`.
- `LLM_PROVIDER=openrouter` — a free-tier-friendly alternative. Get a key at [openrouter.ai/keys](https://openrouter.ai/keys), set `OPENROUTER_API_KEY`, and pick a model (many are tagged `:free`, e.g. the `OPENROUTER_MODEL` default in `.env.example`) via [openrouter.ai/models](https://openrouter.ai/models). Under the hood this uses `langchain-openai`'s `ChatOpenAI` pointed at OpenRouter's OpenAI-compatible endpoint — the same approach works for Groq or any other OpenAI-compatible provider by changing the `base_url` in `rag.py`.

## Mock LLM mode

Set `MOCK_LLM=true` in `.env` to run the service without any LLM API key at all. Retrieval (embeddings + FAISS) still runs for real; the LLM call is replaced with a fixed placeholder response, so you can verify the pipeline end-to-end for free. This takes priority over `LLM_PROVIDER`.
