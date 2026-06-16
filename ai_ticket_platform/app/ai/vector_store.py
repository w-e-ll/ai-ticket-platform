from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.utils.errors import VectorStoreError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class VectorDocument:
    """Document chunk stored in vector search."""

    id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class VectorSearchResult:
    """Vector search result with similarity score."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any]


class InMemoryVectorStore:
    """Simple local vector store for development and testing."""

    def __init__(self) -> None:
        """Initialize empty in-memory vector store."""
        self._documents: dict[str, VectorDocument] = {}

        logger.info(
            "In-memory vector store initialized",
            extra={
                "event": "vector_store_initialized",
                "operation": "vector_store_init",
                "status": "success",
                "provider": "in_memory",
            },
        )

    def add_documents(self, documents: list[VectorDocument]) -> int:
        """Add embedded documents to vector store."""
        logger.info(
            "Vector document insertion started",
            extra={
                "event": "vector_document_insertion_started",
                "operation": "add_documents",
                "status": "started",
                "document_count": len(documents),
                "provider": "in_memory",
            },
        )

        try:
            self._validate_documents(documents)

            for document in documents:
                self._documents[document.id] = document

                logger.debug(
                    "Vector document stored",
                    extra={
                        "event": "vector_document_stored",
                        "operation": "add_documents",
                        "status": "success",
                        "document_id": document.id,
                        "provider": "in_memory",
                    },
                )

            logger.info(
                "Vector document insertion completed",
                extra={
                    "event": "vector_document_insertion_completed",
                    "operation": "add_documents",
                    "status": "success",
                    "document_count": len(documents),
                    "total_documents": len(self._documents),
                    "provider": "in_memory",
                },
            )

            return len(documents)

        except VectorStoreError:
            raise

        except Exception as exc:
            logger.error(
                "Vector document insertion failed",
                extra={
                    "event": "vector_document_insertion_failed",
                    "operation": "add_documents",
                    "status": "failed",
                    "provider": "in_memory",
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise VectorStoreError("Failed to add documents to vector store") from exc

    def search(
        self,
        *,
        query_embedding: list[float],
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search similar documents by cosine similarity."""
        settings = get_settings()
        effective_top_k = top_k or settings.top_k_results

        logger.info(
            "Vector search started",
            extra={
                "event": "vector_search_started",
                "operation": "vector_search",
                "status": "started",
                "top_k": effective_top_k,
                "provider": "in_memory",
            },
        )

        try:
            self._validate_embedding(query_embedding)
            self._validate_top_k(effective_top_k)

            results: list[VectorSearchResult] = []

            for document in self._documents.values():
                if filters and not self._matches_filters(document.metadata, filters):
                    continue

                score = cosine_similarity(query_embedding, document.embedding)

                results.append(
                    VectorSearchResult(
                        id=document.id,
                        content=document.content,
                        score=score,
                        metadata=document.metadata,
                    )
                )

            results.sort(key=lambda item: item.score, reverse=True)

            limited_results = results[:effective_top_k]

            logger.info(
                "Vector search completed",
                extra={
                    "event": "vector_search_completed",
                    "operation": "vector_search",
                    "status": "success",
                    "top_k": effective_top_k,
                    "result_count": len(limited_results),
                    "provider": "in_memory",
                },
            )

            return limited_results

        except VectorStoreError:
            raise

        except Exception as exc:
            logger.error(
                "Vector search failed",
                extra={
                    "event": "vector_search_failed",
                    "operation": "vector_search",
                    "status": "failed",
                    "provider": "in_memory",
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise VectorStoreError("Vector search failed") from exc

    def count(self) -> int:
        """Return number of stored vector documents."""
        total = len(self._documents)

        logger.debug(
            "Vector document count calculated",
            extra={
                "event": "vector_document_count_calculated",
                "operation": "vector_store_count",
                "status": "success",
                "document_count": total,
                "provider": "in_memory",
            },
        )

        return total

    def clear(self) -> None:
        """Clear all stored vector documents."""
        total_before = len(self._documents)
        self._documents.clear()

        logger.info(
            "Vector store cleared",
            extra={
                "event": "vector_store_cleared",
                "operation": "vector_store_clear",
                "status": "success",
                "document_count": total_before,
                "provider": "in_memory",
            },
        )

    def _validate_documents(self, documents: list[VectorDocument]) -> None:
        """Validate documents before insertion."""
        if not documents:
            raise VectorStoreError("documents must not be empty")

        expected_dimension: int | None = None

        for index, document in enumerate(documents):
            if not document.id:
                raise VectorStoreError(
                    "document id must not be empty",
                    details={"index": index},
                )

            if not document.content.strip():
                raise VectorStoreError(
                    "document content must not be empty",
                    details={"index": index, "document_id": document.id},
                )

            self._validate_embedding(document.embedding)

            current_dimension = len(document.embedding)

            if expected_dimension is None:
                expected_dimension = current_dimension

            if current_dimension != expected_dimension:
                raise VectorStoreError(
                    "all document embeddings must have the same dimension",
                    details={
                        "index": index,
                        "expected_dimension": expected_dimension,
                        "actual_dimension": current_dimension,
                    },
                )

    def _validate_embedding(self, embedding: list[float]) -> None:
        """Validate embedding vector."""
        if not embedding:
            raise VectorStoreError("embedding must not be empty")

        for index, value in enumerate(embedding):
            if not isinstance(value, int | float):
                raise VectorStoreError(
                    "embedding values must be numeric",
                    details={"index": index},
                )

            if math.isnan(float(value)) or math.isinf(float(value)):
                raise VectorStoreError(
                    "embedding values must be finite",
                    details={"index": index},
                )

    def _validate_top_k(self, top_k: int) -> None:
        """Validate top-k search value."""
        if top_k < 1:
            raise VectorStoreError("top_k must be greater than zero")

        if top_k > 100:
            raise VectorStoreError("top_k must not exceed 100")

    def _matches_filters(
        self,
        metadata: dict[str, Any],
        filters: dict[str, Any],
    ) -> bool:
        """Check whether document metadata satisfies filters."""
        for key, expected_value in filters.items():
            if metadata.get(key) != expected_value:
                return False

        return True


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(left) != len(right):
        logger.error(
            "Cosine similarity dimension mismatch",
            extra={
                "event": "cosine_similarity_dimension_mismatch",
                "operation": "cosine_similarity",
                "status": "failed",
                "left_dimension": len(left),
                "right_dimension": len(right),
            },
        )
        raise VectorStoreError(
            "vectors must have the same dimension",
            details={
                "left_dimension": len(left),
                "right_dimension": len(right),
            },
        )

    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        raise VectorStoreError("vectors must not have zero norm")

    return dot_product / (left_norm * right_norm)


def build_vector_document(
    *,
    content: str,
    embedding: list[float],
    document_id: UUID | str | None = None,
    chunk_id: UUID | str | None = None,
    tenant_id: UUID | str | None = None,
    department: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> VectorDocument:
    """Build validated vector document from chunk data."""
    if not content or not content.strip():
        raise VectorStoreError("content must not be empty")

    vector_id = str(chunk_id or uuid4())

    document_metadata: dict[str, Any] = {
        **(metadata or {}),
        "document_id": str(document_id) if document_id else None,
        "chunk_id": str(chunk_id) if chunk_id else vector_id,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "department": department,
    }

    logger.debug(
        "Vector document built",
        extra={
            "event": "vector_document_built",
            "operation": "build_vector_document",
            "status": "success",
            "document_id": str(document_id) if document_id else None,
            "chunk_id": str(chunk_id) if chunk_id else vector_id,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "department": department,
        },
    )

    return VectorDocument(
        id=vector_id,
        content=content.strip(),
        embedding=embedding,
        metadata=document_metadata,
    )


_vector_store: InMemoryVectorStore | None = None


def get_vector_store() -> InMemoryVectorStore:
    """Return singleton vector store instance."""
    global _vector_store

    if _vector_store is None:
        logger.info(
            "Vector store singleton creation started",
            extra={
                "event": "vector_store_singleton_creation_started",
                "operation": "get_vector_store",
                "status": "started",
                "provider": "in_memory",
            },
        )

        _vector_store = InMemoryVectorStore()

    return _vector_store
