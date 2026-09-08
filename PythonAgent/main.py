"""FastAPI app exposing /ask and /health endpoints for the RAG agent."""

import asyncio
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import rag_service

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RAG service...")
    rag_service.initialize()
    logger.info("RAG service ready.")
    yield


app = FastAPI(title="Ask Doc Python Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = ""


class SourceSnippet(BaseModel):
    source: str
    snippet: str


class AskResponse(BaseModel):
    answer: str
    source_snippets: list[SourceSnippet]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    logger.info("Received question: %s", question)

    try:
        # rag_service.ask() is synchronous (blocking FAISS search + LLM call).
        # Running it directly here would block FastAPI's single event loop for
        # the whole request, freezing every other in-flight request (including
        # /health) until it finishes. asyncio.to_thread offloads it to a worker
        # thread so the event loop stays free to handle concurrent requests.
        result = await asyncio.to_thread(rag_service.ask, question)
    except Exception:
        logger.exception("Failed to answer question")
        raise HTTPException(status_code=500, detail="Failed to generate an answer.")

    logger.info("Answered question with %d source snippets", len(result["source_snippets"]))
    return result
