from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.app.database import get_db_session
from ai_ticket_platform.app.models.schemas import (
    ClassificationResponse,
    TicketRead,
    TicketSubmissionRequest,
    TicketSubmissionResponse,
)
from ai_ticket_platform.app.services.classifier_service import (
    ClassificationResult,
    ClassifierService,
)
from ai_ticket_platform.app.services.ticket_service import TicketService
from ai_ticket_platform.app.utils.errors import RequestValidationError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post(
    "/tickets",
    response_model=TicketSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    payload: TicketSubmissionRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> TicketSubmissionResponse:
    """Create and classify support ticket."""
    logger.info(
        "Admin ticket creation request received",
        extra={
            "event": "admin_ticket_creation_requested",
            "operation": "admin_create_ticket",
            "status": "started",
            "tenant_id": str(payload.tenant_id),
            "created_by_user_id": str(payload.created_by_user_id)
            if payload.created_by_user_id
            else None,
        },
    )

    ticket_service = TicketService(db_session)

    ticket, classification = await ticket_service.create_ticket(
        tenant_id=payload.tenant_id,
        title=payload.title,
        description=payload.description,
        created_by_user_id=payload.created_by_user_id,
    )

    logger.info(
        "Admin ticket creation completed",
        extra={
            "event": "admin_ticket_creation_completed",
            "operation": "admin_create_ticket",
            "status": "success",
            "tenant_id": str(payload.tenant_id),
            "ticket_id": str(ticket.id),
            "department": classification.department,
            "confidence": classification.confidence,
        },
    )

    return TicketSubmissionResponse(
        ticket=TicketRead.model_validate(ticket),
        classification=ClassificationResponse(
            department=classification.department,
            confidence=classification.confidence,
            probabilities=classification.probabilities,
        ),
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketRead,
)
async def get_ticket(
    ticket_id: UUID,
    tenant_id: UUID = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
) -> TicketRead:
    """Return ticket details."""
    logger.info(
        "Admin ticket retrieval request received",
        extra={
            "event": "admin_ticket_retrieval_requested",
            "operation": "admin_get_ticket",
            "status": "started",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket_id),
        },
    )

    ticket_service = TicketService(db_session)

    ticket = await ticket_service.get_ticket(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
    )

    logger.info(
        "Admin ticket retrieval completed",
        extra={
            "event": "admin_ticket_retrieval_completed",
            "operation": "admin_get_ticket",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket.id),
        },
    )

    return TicketRead.model_validate(ticket)


@router.get(
    "/tickets",
    response_model=list[TicketRead],
)
async def list_tickets(
    tenant_id: UUID = Query(...),
    department: str | None = Query(default=None),
    ticket_status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[TicketRead]:
    """List tenant tickets."""
    logger.info(
        "Admin ticket listing request received",
        extra={
            "event": "admin_ticket_listing_requested",
            "operation": "admin_list_tickets",
            "status": "started",
            "tenant_id": str(tenant_id),
            "department": department,
            "ticket_status": ticket_status,
            "limit": limit,
            "offset": offset,
        },
    )

    ticket_service = TicketService(db_session)

    tickets = await ticket_service.list_tickets(
        tenant_id=tenant_id,
        department=department,
        status=ticket_status,
        limit=limit,
        offset=offset,
    )

    logger.info(
        "Admin ticket listing completed",
        extra={
            "event": "admin_ticket_listing_completed",
            "operation": "admin_list_tickets",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_count": len(tickets),
        },
    )

    return [
        TicketRead.model_validate(ticket)
        for ticket in tickets
    ]


@router.post(
    "/classify",
    response_model=ClassificationResponse,
)
async def classify_ticket_text(
    *,
    text: str,
) -> ClassificationResponse:
    """Classify raw ticket text."""
    normalized_text = " ".join(text.strip().split())

    if not normalized_text:
        raise RequestValidationError("text must not be empty")

    logger.info(
        "Admin ticket classification request received",
        extra={
            "event": "admin_ticket_classification_requested",
            "operation": "admin_classify_ticket",
            "status": "started",
            "text_length": len(normalized_text),
        },
    )

    classifier_service = ClassifierService()

    classification: ClassificationResult = classifier_service.classify(
        normalized_text,
    )

    logger.info(
        "Admin ticket classification completed",
        extra={
            "event": "admin_ticket_classification_completed",
            "operation": "admin_classify_ticket",
            "status": "success",
            "department": classification.department,
            "confidence": classification.confidence,
        },
    )

    return ClassificationResponse(
        department=classification.department,
        confidence=classification.confidence,
        probabilities=classification.probabilities,
    )
