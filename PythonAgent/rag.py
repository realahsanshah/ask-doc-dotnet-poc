"""RAG pipeline: load docs, chunk, embed, retrieve, and query the LLM."""

import logging
import os
from pathlib import Path

from langchain_anthropic import ChatAnthropic
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

        if not self._mock_mode and not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key, "
                "or set MOCK_LLM=true to run without an LLM."
            )

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
            logger.info("MOCK_LLM enabled — using FakeListChatModel instead of Anthropic.")
        else:
            model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
            self._llm = ChatAnthropic(model=model_name, temperature=0)

        logger.info("Loaded %d documents into %d chunks", len(documents), len(chunks))

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
