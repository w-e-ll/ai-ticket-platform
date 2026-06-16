from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ai_ticket_platform.app.ai.embeddings import get_embedding_provider
from ai_ticket_platform.app.ai.vector_store import (
    VectorSearchResult,
    get_vector_store,
)
from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.services.llm_service import LLMService
from ai_ticket_platform.app.utils.errors import RetrievalError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class RAGContext:
    """Retrieved context used for grounded answer generation."""

    content: str
    score: float
    document_id: str | None
    chunk_id: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RAGAnswer:
    """Final RAG answer with retrieved context."""

    answer: str
    contexts: list[RAGContext]


class RAGService:
    """Service for retrieval-augmented question answering."""

    def __init__(self) -> None:
        """Initialize RAG dependencies."""
        self.settings = get_settings()
        self.embedding_provider = get_embedding_provider()
        self.vector_store = get_vector_store()
        self.llm_service = LLMService()

        logger.info(
            "RAG service initialized",
            extra={
                "event": "rag_service_initialized",
                "operation": "rag_service_init",
                "status": "success",
                "embedding_model": self.embedding_provider.model_name(),
            },
        )

    async def answer_question(
        self,
        *,
        tenant_id: UUID,
        question: str,
        top_k: int | None = None,
        department: str | None = None,
    ) -> RAGAnswer:
        """Answer user question using retrieved knowledge-base context."""
        normalized_question = self._validate_question(question)
        effective_top_k = top_k or self.settings.top_k_results

        logger.info(
            "RAG answer generation started",
            extra={
                "event": "rag_answer_generation_started",
                "operation": "answer_question",
                "status": "started",
                "tenant_id": str(tenant_id),
                "top_k": effective_top_k,
                "department": department,
            },
        )

        try:
            contexts = self.retrieve_contexts(
                tenant_id=tenant_id,
                query=normalized_question,
                top_k=effective_top_k,
                department=department,
            )

            if not contexts:
                logger.warning(
                    "RAG answer generation has no retrieved context",
                    extra={
                        "event": "rag_no_context_found",
                        "operation": "answer_question",
                        "status": "warning",
                        "tenant_id": str(tenant_id),
                        "top_k": effective_top_k,
                        "department": department,
                    },
                )

                return RAGAnswer(
                    answer=(
                        "I could not find sufficient information in the "
                        "knowledge base."
                    ),
                    contexts=[],
                )

            context_text = self.build_context_text(contexts)

            answer = await self.llm_service.generate_rag_answer(
                question=normalized_question,
                context=context_text,
            )

            rag_answer = RAGAnswer(
                answer=answer,
                contexts=contexts,
            )

            logger.info(
                "RAG answer generation completed",
                extra={
                    "event": "rag_answer_generation_completed",
                    "operation": "answer_question",
                    "status": "success",
                    "tenant_id": str(tenant_id),
                    "top_k": effective_top_k,
                    "context_count": len(contexts),
                    "answer_length": len(answer),
                },
            )

            return rag_answer

        except RetrievalError:
            raise

        except Exception as exc:
            logger.error(
                "RAG answer generation failed",
                extra={
                    "event": "rag_answer_generation_failed",
                    "operation": "answer_question",
                    "status": "failed",
                    "tenant_id": str(tenant_id),
                    "top_k": effective_top_k,
                    "department": department,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise RetrievalError("Failed to generate RAG answer") from exc

    def retrieve_contexts(
        self,
        *,
        tenant_id: UUID,
        query: str,
        top_k: int | None = None,
        department: str | None = None,
    ) -> list[RAGContext]:
        """Retrieve relevant document chunks from vector store."""
        normalized_query = self._validate_question(query)
        effective_top_k = top_k or self.settings.top_k_results

        logger.info(
            "RAG context retrieval started",
            extra={
                "event": "rag_context_retrieval_started",
                "operation": "retrieve_contexts",
                "status": "started",
                "tenant_id": str(tenant_id),
                "top_k": effective_top_k,
                "department": department,
            },
        )

        try:
            query_embedding = self.embedding_provider.embed_text(normalized_query)

            filters: dict[str, Any] = {
                "tenant_id": str(tenant_id),
            }

            if department:
                filters["department"] = department.strip().lower()

            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=effective_top_k,
                filters=filters,
            )

            contexts = [
                self._result_to_context(result)
                for result in search_results
            ]

            logger.info(
                "RAG context retrieval completed",
                extra={
                    "event": "rag_context_retrieval_completed",
                    "operation": "retrieve_contexts",
                    "status": "success",
                    "tenant_id": str(tenant_id),
                    "top_k": effective_top_k,
                    "department": department,
                    "context_count": len(contexts),
                },
            )

            return contexts

        except Exception as exc:
            logger.error(
                "RAG context retrieval failed",
                extra={
                    "event": "rag_context_retrieval_failed",
                    "operation": "retrieve_contexts",
                    "status": "failed",
                    "tenant_id": str(tenant_id),
                    "top_k": effective_top_k,
                    "department": department,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise RetrievalError("Failed to retrieve RAG contexts") from exc

    def build_context_text(self, contexts: list[RAGContext]) -> str:
        """Build compact prompt context from retrieved chunks."""
        logger.info(
            "RAG context text build started",
            extra={
                "event": "rag_context_text_build_started",
                "operation": "build_context_text",
                "status": "started",
                "context_count": len(contexts),
            },
        )

        if not contexts:
            raise RetrievalError("contexts must not be empty")

        context_blocks: list[str] = []

        for index, context in enumerate(contexts, start=1):
            filename = context.metadata.get("filename", "unknown document")
            department = context.metadata.get("department", "unknown department")

            context_blocks.append(
                "\n".join(
                    [
                        f"[Context {index}]",
                        f"Document: {filename}",
                        f"Department: {department}",
                        f"Score: {context.score:.4f}",
                        "Content:",
                        context.content,
                    ]
                )
            )

        context_text = "\n\n".join(context_blocks)

        logger.info(
            "RAG context text build completed",
            extra={
                "event": "rag_context_text_build_completed",
                "operation": "build_context_text",
                "status": "success",
                "context_count": len(contexts),
                "context_length": len(context_text),
            },
        )

        return context_text

    def _result_to_context(self, result: VectorSearchResult) -> RAGContext:
        """Convert vector search result to RAG context."""
        metadata = result.metadata or {}

        return RAGContext(
            content=result.content,
            score=result.score,
            document_id=metadata.get("document_id"),
            chunk_id=metadata.get("chunk_id"),
            metadata=metadata,
        )

    def _validate_question(self, question: str) -> str:
        """Validate and normalize user question."""
        if not isinstance(question, str):
            raise RetrievalError("question must be a string")

        normalized = " ".join(question.strip().split())

        if not normalized:
            raise RetrievalError("question must not be empty")

        if len(normalized) > 10000:
            raise RetrievalError("question is too long")

        logger.debug(
            "RAG question validation completed",
            extra={
                "event": "rag_question_validation_completed",
                "operation": "validate_question",
                "status": "success",
                "question_length": len(normalized),
            },
        )

        return normalized
