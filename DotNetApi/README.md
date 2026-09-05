# DotNetApi

An ASP.NET Core (.NET 10) Web API that acts as the public-facing orchestrator. It receives questions from callers, forwards them to the [PythonAgent](../PythonAgent) RAG service over HTTP, and relays back the answer and supporting source snippets.

## Stack

- ASP.NET Core Web API (controller-based)
- `IHttpClientFactory` with a named client (`PythonAgent`) for outbound calls
- OpenAPI (`/openapi/v1.json`) enabled in Development

## Project structure

```text
DotNetApi/
  Controllers/
    AgentController.cs        # POST api/agent/ask
    WeatherForecastController.cs  # default template sample, safe to delete
  Models/
    AgentModels.cs            # request/response DTOs, incl. mapping to the Python service's JSON shape
  Program.cs                   # service registration, HttpClient config, middleware pipeline
  appsettings.json             # PythonAgentSettings:BaseUrl lives here
```

## How it talks to the Python service

`Program.cs` registers a named `HttpClient` via `AddHttpClient("PythonAgent", ...)`, whose `BaseAddress` is read from configuration (`PythonAgentSettings:BaseUrl`) instead of being hardcoded. `AgentController` asks `IHttpClientFactory` for that client and POSTs to `/ask`.

Configuration is resolved in the usual ASP.NET Core order, so it can be overridden without touching code:

- `appsettings.json` (default): `http://localhost:8000` — for running both services locally outside Docker
- Environment variable (used in `docker-compose.yml`): `PythonAgentSettings__BaseUrl=http://python-agent:8000` — Docker Compose service-name DNS

## Run locally (no Docker)

Prerequisite: the [PythonAgent](../PythonAgent) service running on `http://localhost:8000` (see its README).

```bash
cd DotNetApi
dotnet run
```

The API listens on `http://localhost:5181` (see `Properties/launchSettings.json`). Swagger/OpenAPI JSON is available at `/openapi/v1.json` when `ASPNETCORE_ENVIRONMENT=Development`.

## Run with Docker

Prefer the root-level `docker compose up --build` (see the [top-level README](../README.md)) so both services come up together on the same network.

To run just this service in isolation instead:

```bash
cd DotNetApi
docker build -f DotNetApi/Dockerfile -t dotnet-api .
docker run --rm -p 8080:8080 -e ASPNETCORE_HTTP_PORTS=8080 -e PythonAgentSettings__BaseUrl=http://host.docker.internal:8000 dotnet-api
```

(`host.docker.internal` lets the container reach a PythonAgent instance running on your host machine, outside of Docker.)

## Endpoint

### POST `api/agent/ask`

Request:

```json
{ "question": "Does this candidate's experience match the BDO job description?" }
```

Success (200):

```json
{
  "answer": "...",
  "sourceSnippets": [
    { "source": "resume.txt", "snippet": "..." }
  ]
}
```

Error responses:

- `400 Bad Request` — `question` is missing/empty/whitespace
- `502 Bad Gateway` — the Python service is unreachable (connection refused, timeout) or returned a non-2xx/unreadable response

## Notes for learning

- `AgentModels.cs` deliberately keeps two sets of DTOs: the public `AskRequest`/`AskResponse`/`SourceSnippet` (camelCase JSON, our own contract) and internal `PythonAskRequest`/`PythonAskResponse`/`PythonSourceSnippet` (decorated with `[JsonPropertyName]` to match the Python service's snake_case JSON like `source_snippets`). The controller maps between them so a change in the Python service's JSON casing never leaks into our public API.
- `IHttpClientFactory` (rather than `new HttpClient()`) avoids socket exhaustion and centralizes configuration like `BaseAddress`.
