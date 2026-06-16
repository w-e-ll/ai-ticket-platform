from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.app.database import get_db_session
from ai_ticket_platform.app.models.schemas import (
    TicketCreate,
    TicketMessageCreate,
    TicketMessageRead,
    TicketRead,
    TicketUpdate,
)
from ai_ticket_platform.app.services.ticket_service import TicketService
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    payload: TicketCreate,
    db_session: AsyncSession = Depends(get_db_session),
) -> TicketRead:
    """Create support ticket."""
    logger.info(
        "Ticket API creation request received",
        extra={
            "event": "ticket_api_creation_request_received",
            "operation": "api_create_ticket",
            "status": "started",
            "tenant_id": str(payload.tenant_id),
            "created_by_user_id": str(payload.created_by_user_id)
            if payload.created_by_user_id
            else None,
            "priority": payload.priority,
            "department": payload.department,
        },
    )

    ticket_service = TicketService(db_session)

    ticket, _ = await ticket_service.create_ticket(
        tenant_id=payload.tenant_id,
        title=payload.title,
        description=payload.description,
        created_by_user_id=payload.created_by_user_id,
        department=payload.department,
        priority=payload.priority,
    )

    logger.info(
        "Ticket API creation request completed",
        extra={
            "event": "ticket_api_creation_request_completed",
            "operation": "api_create_ticket",
            "status": "success",
            "tenant_id": str(payload.tenant_id),
            "ticket_id": str(ticket.id),
            "department": ticket.department,
            "priority": ticket.priority,
        },
    )

    return TicketRead.model_validate(ticket)


@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
    status_code=status.HTTP_200_OK,
)
async def get_ticket(
    ticket_id: UUID,
    tenant_id: UUID = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
) -> TicketRead:
    """Return ticket details."""
    logger.info(
        "Ticket API retrieval request received",
        extra={
            "event": "ticket_api_retrieval_request_received",
            "operation": "api_get_ticket",
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
        "Ticket API retrieval request completed",
        extra={
            "event": "ticket_api_retrieval_request_completed",
            "operation": "api_get_ticket",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket.id),
            "department": ticket.department,
            "ticket_status": ticket.status,
        },
    )

    return TicketRead.model_validate(ticket)


@router.get(
    "",
    response_model=list[TicketRead],
    status_code=status.HTTP_200_OK,
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
        "Ticket API listing request received",
        extra={
            "event": "ticket_api_listing_request_received",
            "operation": "api_list_tickets",
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
        "Ticket API listing request completed",
        extra={
            "event": "ticket_api_listing_request_completed",
            "operation": "api_list_tickets",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_count": len(tickets),
        },
    )

    return [
        TicketRead.model_validate(ticket)
        for ticket in tickets
    ]


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketRead,
    status_code=status.HTTP_200_OK,
)
async def update_ticket_status(
    ticket_id: UUID,
    status_value: str = Query(..., alias="status"),
    tenant_id: UUID = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
) -> TicketRead:
    """Update ticket status."""
    logger.info(
        "Ticket status update request received",
        extra={
            "event": "ticket_status_update_request_received",
            "operation": "api_update_ticket_status",
            "status": "started",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket_id),
            "new_ticket_status": status_value,
        },
    )

    ticket_service = TicketService(db_session)

    ticket = await ticket_service.update_ticket_status(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        status=status_value,
    )

    logger.info(
        "Ticket status update request completed",
        extra={
            "event": "ticket_status_update_request_completed",
            "operation": "api_update_ticket_status",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket.id),
            "ticket_status": ticket.status,
        },
    )

    return TicketRead.model_validate(ticket)


@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_ticket_message(
    ticket_id: UUID,
    payload: TicketMessageCreate,
    tenant_id: UUID = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
) -> TicketMessageRead:
    """Add message to support ticket."""
    logger.info(
        "Ticket message creation request received",
        extra={
            "event": "ticket_message_creation_request_received",
            "operation": "api_add_ticket_message",
            "status": "started",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket_id),
            "sender_type": payload.sender_type,
        },
    )

    ticket_service = TicketService(db_session)

    message = await ticket_service.add_ticket_message(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        sender_type=payload.sender_type,
        content=payload.content,
    )

    logger.info(
        "Ticket message creation request completed",
        extra={
            "event": "ticket_message_creation_request_completed",
            "operation": "api_add_ticket_message",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket_id),
            "message_id": str(message.id),
        },
    )

    return TicketMessageRead.model_validate(message)


@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
    status_code=status.HTTP_200_OK,
)
async def update_ticket(
    ticket_id: UUID,
    payload: TicketUpdate,
    tenant_id: UUID = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
) -> TicketRead:
    """Update mutable ticket fields."""
    logger.info(
        "Ticket update request received",
        extra={
            "event": "ticket_update_request_received",
            "operation": "api_update_ticket",
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

    if payload.title is not None:
        ticket.title = payload.title

    if payload.description is not None:
        ticket.description = payload.description

    if payload.department is not None:
        ticket.department = payload.department

    if payload.priority is not None:
        ticket.priority = payload.priority

    if payload.status is not None:
        ticket.status = payload.status

    await db_session.commit()
    await db_session.refresh(ticket)

    logger.info(
        "Ticket update request completed",
        extra={
            "event": "ticket_update_request_completed",
            "operation": "api_update_ticket",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_id": str(ticket.id),
            "department": ticket.department,
            "ticket_status": ticket.status,
        },
    )

    return TicketRead.model_validate(ticket)
