"""RAG pipeline: load docs, chunk, embed, retrieve, and query the LLM."""

import logging
import os
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("rag")

DATA_DIR = Path(__file__).parent / "data"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 3
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

PROMPT = ChatPromptTemplate.from_template(
    """You are an assistant answering questions using only the provided context.
If the answer isn't contained in the context, say you don't know.

Context:
{context}

Question: {question}

Answer:"""
)


class RagService:
    def __init__(self):
        self._vector_store = None
        self._llm = None
        self._mock_mode = False

    def initialize(self):
        """Load documents, chunk, and build the in-memory vector store. Call once at startup."""
        self._mock_mode = os.getenv("MOCK_LLM", "false").lower() == "true"

        documents = []
        for file_path in sorted(DATA_DIR.glob("*.txt")):
            loader = TextLoader(str(file_path), encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = file_path.name
            documents.extend(docs)

        if not documents:
            raise RuntimeError(f"No .txt files found in {DATA_DIR}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self._vector_store = FAISS.from_documents(chunks, embeddings)

        if self._mock_mode:
            self._llm = FakeListChatModel(
                responses=["[MOCK ANSWER] This is a placeholder response generated without calling an LLM."]
            )
            logger.info("MOCK_LLM enabled — using FakeListChatModel instead of a real LLM.")
        else:
            self._llm = self._build_llm()

        logger.info("Loaded %d documents into %d chunks", len(documents), len(chunks))

    def _build_llm(self):
        """Construct the real chat model based on LLM_PROVIDER.

        Both Anthropic and OpenRouter are supported: Anthropic via its own
        SDK-backed langchain integration, OpenRouter via langchain-openai's
        ChatOpenAI pointed at OpenRouter's OpenAI-compatible endpoint (this
        same pattern also works for Groq or any other OpenAI-compatible
        provider — just change base_url).
        """
        provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key, "
                    "set LLM_PROVIDER to a different provider, or set MOCK_LLM=true."
                )
            from langchain_anthropic import ChatAnthropic

            model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
            logger.info("Using Anthropic model %s", model_name)
            return ChatAnthropic(model=model_name, temperature=0)

        if provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key, "
                    "or set MOCK_LLM=true to run without an LLM."
                )
            from langchain_openai import ChatOpenAI

            model_name = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
            logger.info("Using OpenRouter model %s", model_name)
            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0,
                # Free-tier models sometimes queue behind an overloaded upstream
                # backend for minutes before erroring. Fail fast instead so the
                # caller (and its own HTTP timeout) doesn't sit blocked for ages.
                timeout=45,
                max_retries=1,
            )

        raise RuntimeError(
            f"Unknown LLM_PROVIDER '{provider}'. Use 'anthropic', 'openrouter', or set MOCK_LLM=true."
        )

    def ask(self, question: str) -> dict:
        if self._vector_store is None or self._llm is None:
            raise RuntimeError("RagService not initialized. Call initialize() first.")

        retrieved_docs = self._vector_store.similarity_search(question, k=TOP_K)
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)

        chain = PROMPT | self._llm
        response = chain.invoke({"context": context, "question": question})

        return {
            "answer": response.content,
            "source_snippets": [
                {"source": doc.metadata.get("source", "unknown"), "snippet": doc.page_content}
                for doc in retrieved_docs
            ],
        }


rag_service = RagService()
