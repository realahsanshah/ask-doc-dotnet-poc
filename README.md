# Ask Doc

A small two-service proof-of-concept for asking natural-language questions over a local set of documents (resume, job description, notes), using retrieval-augmented generation (RAG).

```text
Caller  --HTTP-->  DotNetApi (ASP.NET Core)  --HTTP-->  PythonAgent (FastAPI + LangChain RAG)
                     api/agent/ask                        /ask
```

- **[DotNetApi](DotNetApi/)** — public-facing ASP.NET Core Web API. Validates requests and orchestrates the call to the Python service. See [DotNetApi/README.md](DotNetApi/README.md).
- **[PythonAgent](PythonAgent/)** — FastAPI service that does the actual RAG work: chunks the `.txt` files in `PythonAgent/data/`, embeds them locally, retrieves the most relevant chunks for a question, and asks Claude (Anthropic) to answer using only that context. See [PythonAgent/README.md](PythonAgent/README.md).

Why two services instead of one? It's a deliberate learning setup for practicing cross-service HTTP calls, `IHttpClientFactory`, error translation (502 handling), and Docker Compose multi-service networking.

## Quick start (Docker Compose — recommended)

This brings up both services together, wired to talk to each other automatically.

```bash
# 1. One-time: give the Python service its config
cp PythonAgent/.env.example PythonAgent/.env
# edit PythonAgent/.env — set MOCK_LLM=true to skip needing a real API key,
# or set ANTHROPIC_API_KEY to a real key to get real answers.

# 2. Bring both services up
docker compose up --build
```

Then:

```bash
curl -X POST http://localhost:8080/api/agent/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Does this candidate's experience match the job description?\"}"
```

- DotNetApi (call this one): `http://localhost:8080`
- PythonAgent (internal, but also exposed for debugging): `http://localhost:8000/docs`

## Run without Docker

Each service can also run directly on your machine — see the per-service READMEs for details:

1. Start PythonAgent first: [PythonAgent/README.md](PythonAgent/README.md) (`uvicorn main:app --reload --port 8000`)
2. Then start DotNetApi: [DotNetApi/README.md](DotNetApi/README.md) (`dotnet run`), which defaults to calling `http://localhost:8000`.

## How the two services find each other

DotNetApi never hardcodes the Python service's address — it reads `PythonAgentSettings:BaseUrl` from configuration (see [DotNetApi/README.md](DotNetApi/README.md#how-it-talks-to-the-python-service) for the full precedence table):

- Locally: `http://localhost:8000` (from `appsettings.json`)
- In `docker-compose.yml`: `http://python-agent:8000` (the compose service name, resolved via Docker's internal DNS)

## Secrets

Nothing is committed. `PythonAgent/.env` (created from `PythonAgent/.env.example`) holds `ANTHROPIC_API_KEY` and is gitignored — see the root [.gitignore](.gitignore).
