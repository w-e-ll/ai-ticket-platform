from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Celery

from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.database import AsyncSessionLocal
from ai_ticket_platform.app.services.classifier_service import ClassifierService
from ai_ticket_platform.app.services.document_service import DocumentService
from ai_ticket_platform.app.services.ticket_service import TicketService
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

settings = get_settings()

celery_app = Celery(
    "ai_ticket_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@celery_app.task(name="ai_ticket_platform.health_check")
def health_check_task() -> dict[str, str]:
    """Run worker health check."""
    logger.info(
        "Worker health check started",
        extra={
            "event": "worker_health_check_started",
            "operation": "health_check_task",
            "status": "started",
        },
    )

    logger.info(
        "Worker health check completed",
        extra={
            "event": "worker_health_check_completed",
            "operation": "health_check_task",
            "status": "success",
        },
    )

    return {"status": "ok"}


@celery_app.task(name="ai_ticket_platform.classify_ticket")
def classify_ticket_task(text: str) -> dict[str, object]:
    """Classify ticket text in background."""
    logger.info(
        "Background ticket classification started",
        extra={
            "event": "background_ticket_classification_started",
            "operation": "classify_ticket_task",
            "status": "started",
            "text_length": len(text or ""),
        },
    )

    classifier = ClassifierService()
    result = classifier.classify(text)

    logger.info(
        "Background ticket classification completed",
        extra={
            "event": "background_ticket_classification_completed",
            "operation": "classify_ticket_task",
            "status": "success",
            "department": result.department,
            "confidence": result.confidence,
        },
    )

    return {
        "department": result.department,
        "confidence": result.confidence,
        "probabilities": result.probabilities,
    }


@celery_app.task(name="ai_ticket_platform.summarize_ticket")
def summarize_ticket_task(
    *,
    tenant_id: str,
    ticket_id: str,
) -> dict[str, str | None]:
    """Generate and persist AI ticket summary in background."""
    return asyncio.run(
        _summarize_ticket_async(
            tenant_id=UUID(tenant_id),
            ticket_id=UUID(ticket_id),
        )
    )


async def _summarize_ticket_async(
    *,
    tenant_id: UUID,
    ticket_id: UUID,
) -> dict[str, str | None]:
    """Async implementation for ticket summarization task."""
    logger.info(
        "Background ticket summarization started",
        extra={
            "event": "background_ticket_summarization_started",
            "operation": "summarize_ticket_task",
            "status": "started",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket_id),
        },
    )

    async with AsyncSessionLocal() as db_session:
        ticket_service = TicketService(db_session)
        ticket = await ticket_service.get_ticket(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
        )

        ticket_text = f"{ticket.title}\n\n{ticket.description}"
        summary = await ticket_service.llm_service.summarize_ticket(
            ticket_content=ticket_text,
        )

        ticket.ai_summary = summary

        await db_session.commit()
        await db_session.refresh(ticket)

    logger.info(
        "Background ticket summarization completed",
        extra={
            "event": "background_ticket_summarization_completed",
            "operation": "summarize_ticket_task",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket_id),
            "summary_length": len(summary),
        },
    )

    return {
        "ticket_id": str(ticket_id),
        "summary": summary,
    }


@celery_app.task(name="ai_ticket_platform.reindex_document")
def reindex_document_task(
    *,
    tenant_id: str,
    document_id: str,
) -> dict[str, str]:
    """Placeholder for document reindexing background task."""
    return asyncio.run(
        _reindex_document_async(
            tenant_id=UUID(tenant_id),
            document_id=UUID(document_id),
        )
    )


async def _reindex_document_async(
    *,
    tenant_id: UUID,
    document_id: UUID,
) -> dict[str, str]:
    """Async implementation for document reindexing task."""
    logger.info(
        "Background document reindex started",
        extra={
            "event": "background_document_reindex_started",
            "operation": "reindex_document_task",
            "status": "started",
            "tenant_id": str(tenant_id),
            "document_id": str(document_id),
        },
    )

    async with AsyncSessionLocal() as db_session:
        document_service = DocumentService(db_session)
        document = await document_service.get_document(
            tenant_id=tenant_id,
            document_id=document_id,
        )

    logger.info(
        "Background document reindex completed",
        extra={
            "event": "background_document_reindex_completed",
            "operation": "reindex_document_task",
            "status": "success",
            "tenant_id": str(tenant_id),
            "document_id": str(document.id),
        },
    )

    return {
        "document_id": str(document_id),
        "status": "reindex_placeholder_completed",
    }
