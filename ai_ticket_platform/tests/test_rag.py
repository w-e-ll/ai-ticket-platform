from __future__ import annotations

from uuid import uuid4

import pytest

from ai_ticket_platform.app.ai.vector_store import (
    InMemoryVectorStore,
    build_vector_document,
)
from ai_ticket_platform.app.services.rag_service import RAGService
from ai_ticket_platform.app.utils.errors import RetrievalError


def test_vector_store_returns_similar_contexts() -> None:
    """Search vector store by cosine similarity."""
    vector_store = InMemoryVectorStore()

    first_document = build_vector_document(
        content="VPN access issues should be reported to IT service desk.",
        embedding=[1.0, 0.0, 0.0],
        tenant_id="tenant-1",
        document_id="doc-1",
        chunk_id="chunk-1",
        department="it",
    )

    second_document = build_vector_document(
        content="Vacation leave requests should be handled by HR.",
        embedding=[0.0, 1.0, 0.0],
        tenant_id="tenant-1",
        document_id="doc-2",
        chunk_id="chunk-2",
        department="hr",
    )

    vector_store.add_documents([first_document, second_document])

    results = vector_store.search(
        query_embedding=[1.0, 0.0, 0.0],
        top_k=1,
        filters={
            "tenant_id": "tenant-1",
        },
    )

    assert len(results) == 1
    assert results[0].id == "chunk-1"
    assert results[0].score == pytest.approx(1.0)


def test_vector_store_filters_by_department() -> None:
    """Filter vector search by metadata."""
    vector_store = InMemoryVectorStore()

    vector_store.add_documents(
        [
            build_vector_document(
                content="Laptop disk issue belongs to IT.",
                embedding=[1.0, 0.0],
                tenant_id="tenant-1",
                document_id="doc-1",
                chunk_id="chunk-1",
                department="it",
            ),
            build_vector_document(
                content="Bus route issue belongs to transportation.",
                embedding=[1.0, 0.0],
                tenant_id="tenant-1",
                document_id="doc-2",
                chunk_id="chunk-2",
                department="transportation",
            ),
        ]
    )

    results = vector_store.search(
        query_embedding=[1.0, 0.0],
        top_k=5,
        filters={
            "tenant_id": "tenant-1",
            "department": "transportation",
        },
    )

    assert len(results) == 1
    assert results[0].metadata["department"] == "transportation"


def test_vector_store_rejects_dimension_mismatch() -> None:
    """Reject cosine similarity with different vector dimensions."""
    vector_store = InMemoryVectorStore()

    vector_store.add_documents(
        [
            build_vector_document(
                content="IT support context.",
                embedding=[1.0, 0.0],
                tenant_id="tenant-1",
                document_id="doc-1",
                chunk_id="chunk-1",
                department="it",
            )
        ]
    )

    with pytest.raises(Exception):
        vector_store.search(
            query_embedding=[1.0, 0.0, 0.0],
            top_k=1,
        )


def test_rag_build_context_text() -> None:
    """Build prompt context text from retrieved contexts."""
    rag_service = RAGService()

    contexts = [
        rag_service._result_to_context(
            result=build_vector_document(
                content="Employees should contact IT for laptop issues.",
                embedding=[1.0, 0.0],
                tenant_id="tenant-1",
                document_id="doc-1",
                chunk_id="chunk-1",
                department="it",
                metadata={
                    "filename": "it_policy.txt",
                },
            )  # type: ignore[arg-type]
        )
    ]
