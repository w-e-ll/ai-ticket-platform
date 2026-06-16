from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.app.models.db import Ticket, TicketMessage, TicketStatus
from ai_ticket_platform.app.services.classifier_service import (
    ClassificationResult,
    ClassifierService,
)
from ai_ticket_platform.app.services.llm_service import LLMService
from ai_ticket_platform.app.utils.errors import (
    ResourceNotFoundError,
    TicketCreationError,
    TicketRoutingError,
)
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


class TicketService:
    """Service for ticket creation, routing, and updates."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize ticket service dependencies."""
        self.db_session = db_session
        self.classifier_service = ClassifierService()
        self.llm_service = LLMService()

        logger.info(
            "Ticket service initialized",
            extra={
                "event": "ticket_service_initialized",
                "operation": "ticket_service_init",
                "status": "success",
            },
        )

    async def create_ticket(
        self,
        *,
        tenant_id: UUID,
        title: str,
        description: str,
        created_by_user_id: UUID | None = None,
        department: str | None = None,
        priority: str = "medium",
    ) -> tuple[Ticket, ClassificationResult]:
        """Create ticket and classify department when needed."""
        normalized_title = self._validate_text(title, field_name="title", max_length=500)
        normalized_description = self._validate_text(
            description,
            field_name="description",
            max_length=10000,
        )
        normalized_priority = self._normalize_priority(priority)

        logger.info(
            "Ticket creation started",
            extra={
                "event": "ticket_creation_started",
                "operation": "create_ticket",
                "status": "started",
                "tenant_id": str(tenant_id),
                "created_by_user_id": str(created_by_user_id)
                if created_by_user_id
                else None,
                "priority": normalized_priority,
                "department": department,
            },
        )

        try:
            ticket_text = f"{normalized_title}\n\n{normalized_description}"

            if department:
                classification = ClassificationResult(
                    department=self._normalize_department(department),
                    confidence=1.0,
                    probabilities=None,
                )
            else:
                classification = self.route_ticket(ticket_text)

            ai_summary = await self._safe_summarize_ticket(ticket_text)

            ticket = Ticket(
                tenant_id=tenant_id,
                created_by_user_id=created_by_user_id,
                title=normalized_title,
                description=normalized_description,
                department=classification.department,
                priority=normalized_priority,
                status=TicketStatus.OPEN.value,
                classification_confidence=classification.confidence,
                ai_summary=ai_summary,
                metadata_json={
                    "classification_probabilities": classification.probabilities,
                    "classification_source": "ml_classifier"
                    if not department
                    else "manual",
                },
            )

            self.db_session.add(ticket)
            await self.db_session.flush()

            initial_message = TicketMessage(
                ticket_id=ticket.id,
                sender_type="user",
                content=normalized_description,
            )

            self.db_session.add(initial_message)

            await self.db_session.commit()
            await self.db_session.refresh(ticket)

            logger.info(
                "Ticket creation completed",
                extra={
                    "event": "ticket_creation_completed",
                    "operation": "create_ticket",
                    "status": "success",
                    "tenant_id": str(tenant_id),
                    "ticket_id": str(ticket.id),
                    "department": ticket.department,
                    "priority": ticket.priority,
                    "confidence": ticket.classification_confidence,
                },
            )

            return ticket, classification

        except Exception as exc:
            await self.db_session.rollback()

            logger.error(
                "Ticket creation failed",
                extra={
                    "event": "ticket_creation_failed",
                    "operation": "create_ticket",
                    "status": "failed",
                    "tenant_id": str(tenant_id),
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise TicketCreationError("Failed to create ticket") from exc

    def route_ticket(self, ticket_text: str) -> ClassificationResult:
        """Classify ticket and return routing result."""
        normalized_text = self._validate_text(
            ticket_text,
            field_name="ticket_text",
            max_length=10000,
        )

        logger.info(
            "Ticket routing started",
            extra={
                "event": "ticket_routing_started",
                "operation": "route_ticket",
                "status": "started",
                "text_length": len(normalized_text),
            },
        )

        try:
            classification = self.classifier_service.classify(normalized_text)

            logger.info(
                "Ticket routing completed",
                extra={
                    "event": "ticket_routing_completed",
                    "operation": "route_ticket",
                    "status": "success",
                    "department": classification.department,
                    "confidence": classification.confidence,
                },
            )

            return classification

        except Exception as exc:
            logger.error(
                "Ticket routing failed",
                extra={
                    "event": "ticket_routing_failed",
                    "operation": "route_ticket",
                    "status": "failed",
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise TicketRoutingError("Failed to route ticket") from exc

    async def get_ticket(
        self,
        *,
        tenant_id: UUID,
        ticket_id: UUID,
    ) -> Ticket:
        """Return ticket by tenant and ticket id."""
        logger.info(
            "Ticket retrieval started",
            extra={
                "event": "ticket_retrieval_started",
                "operation": "get_ticket",
                "status": "started",
                "tenant_id": str(tenant_id),
                "ticket_id": str(ticket_id),
            },
        )

        result = await self.db_session.execute(
            select(Ticket).where(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
            )
        )

        ticket = result.scalar_one_or_none()

        if ticket is None:
            logger.warning(
                "Ticket not found",
                extra={
                    "event": "ticket_not_found",
                    "operation": "get_ticket",
                    "status": "warning",
                    "tenant_id": str(tenant_id),
                    "ticket_id": str(ticket_id),
                },
            )

            raise ResourceNotFoundError(
                "Ticket not found",
                details={
                    "tenant_id": str(tenant_id),
                    "ticket_id": str(ticket_id),
                },
            )

        logger.info(
            "Ticket retrieval completed",
            extra={
                "event": "ticket_retrieval_completed",
                "operation": "get_ticket",
                "status": "success",
                "tenant_id": str(tenant_id),
                "ticket_id": str(ticket.id),
                "department": ticket.department,
                "status": ticket.status,
            },
        )

        return ticket

    async def list_tickets(
        self,
        *,
        tenant_id: UUID,
        department: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Ticket]:
        """List tickets for tenant with optional filters."""
        self._validate_pagination(limit=limit, offset=offset)

        normalized_department = (
            self._normalize_department(department) if department else None
        )
        normalized_status = self._normalize_status(status) if status else None

        logger.info(
            "Ticket listing started",
            extra={
                "event": "ticket_listing_started",
                "operation": "list_tickets",
                "status": "started",
                "tenant_id": str(tenant_id),
                "department": normalized_department,
                "ticket_status": normalized_status,
                "limit": limit,
                "offset": offset,
            },
        )

        query = select(Ticket).where(Ticket.tenant_id == tenant_id)

        if normalized_department:
            query = query.where(Ticket.department == normalized_department)

        if normalized_status:
            query = query.where(Ticket.status == normalized_status)

        query = query.order_by(Ticket.created_at.desc()).limit(limit).offset(offset)

        result = await self.db_session.execute(query)
        tickets = list(result.scalars().all())

        logger.info(
            "Ticket listing completed",
            extra={
                "event": "ticket_listing_completed",
                "operation": "list_tickets",
                "status": "success",
                "tenant_id": str(tenant_id),
                "ticket_count": len(tickets),
                "department": normalized_department,
                "ticket_status": normalized_status,
            },
        )

        return tickets

    async def update_ticket_status(
        self,
        *,
        tenant_id: UUID,
        ticket_id: UUID,
        status: str,
    ) -> Ticket:
        """Update ticket lifecycle status."""
        normalized_status = self._normalize_status(status)

        logger.info(
            "Ticket status update started",
            extra={
                "event": "ticket_status_update_started",
                "operation": "update_ticket_status",
                "status": "started",
                "tenant_id": str(tenant_id),
                "ticket_id": str(ticket_id),
                "new_ticket_status": normalized_status,
            },
        )

        try:
            ticket = await self.get_ticket(
                tenant_id=tenant_id,
                ticket_id=ticket_id,
            )

            old_status = ticket.status
            ticket.status = normalized_status

            await self.db_session.commit()
            await self.db_session.refresh(ticket)

            logger.info(
                "Ticket status update completed",
                extra={
                    "event": "ticket_status_update_completed",
                    "operation": "update_ticket_status",
                    "status": "success",
                    "tenant_id": str(tenant_id),
                    "ticket_id": str(ticket.id),
                    "old_ticket_status": old_status,
                    "new_ticket_status": normalized_status,
                },
            )

            return ticket

        except Exception as exc:
            await self.db_session.rollback()

            logger.error(
                "Ticket status update failed",
                extra={
                    "event": "ticket_status_update_failed",
                    "operation": "update_ticket_status",
                    "status": "failed",
                    "tenant_id": str(tenant_id),
                    "ticket_id": str(ticket_id),
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise TicketCreationError("Failed to update ticket status") from exc

    async def add_ticket_message(
        self,
        *,
        tenant_id: UUID,
        ticket_id: UUID,
        sender_type: str,
        content: str,
    ) -> TicketMessage:
        """Add message to existing ticket."""
        normalized_sender_type = self._validate_text(
            sender_type,
            field_name="sender_type",
            max_length=50,
        ).lower()
        normalized_content = self._validate_text(
            content,
            field_name="content",
            max_length=10000,
        )

        logger.info(
            "Ticket message creation started",
            extra={
                "event": "ticket_message_creation_started",
                "operation": "add_ticket_message",
                "status": "started",
                "tenant_id": str(tenant_id),
                "ticket_id": str(ticket_id),
                "sender_type": normalized_sender_type,
            },
        )

        try:
            ticket = await self.get_ticket(
                tenant_id=tenant_id,
                ticket_id=ticket_id,
            )

            message = TicketMessage(
                ticket_id=ticket.id,
                sender_type=normalized_sender_type,
                content=normalized_content,
            )

            self.db_session.add(message)
            await self.db_session.commit()
            await self.db_session.refresh(message)

            logger.info(
                "Ticket message creation completed",
                extra={
                    "event": "ticket_message_creation_completed",
                    "operation": "add_ticket_message",
                    "status": "success",
                    "tenant_id": str(tenant_id),
                    "ticket_id": str(ticket.id),
                    "message_id": str(message.id),
                    "sender_type": normalized_sender_type,
                },
            )

            return message

        except Exception as exc:
            await self.db_session.rollback()

            logger.error(
                "Ticket message creation failed",
                extra={
                    "event": "ticket_message_creation_failed",
                    "operation": "add_ticket_message",
                    "status": "failed",
                    "tenant_id": str(tenant_id),
                    "ticket_id": str(ticket_id),
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise TicketCreationError("Failed to add ticket message") from exc

    async def _safe_summarize_ticket(self, ticket_text: str) -> str | None:
        """Try to summarize ticket without blocking ticket creation."""
        try:
            summary = await self.llm_service.summarize_ticket(
                ticket_content=ticket_text,
            )

            logger.info(
                "Ticket AI summary generated",
                extra={
                    "event": "ticket_ai_summary_generated",
                    "operation": "safe_summarize_ticket",
                    "status": "success",
                    "summary_length": len(summary),
                },
            )

            return summary

        except Exception as exc:
            logger.warning(
                "Ticket AI summary skipped",
                extra={
                    "event": "ticket_ai_summary_skipped",
                    "operation": "safe_summarize_ticket",
                    "status": "warning",
                    "exception_type": type(exc).__name__,
                },
            )

            return None

    def _validate_text(
        self,
        value: str,
        *,
        field_name: str,
        max_length: int,
    ) -> str:
        """Validate and normalize text field."""
        if not isinstance(value, str):
            raise TicketCreationError(f"{field_name} must be a string")

        normalized = " ".join(value.strip().split())

        if not normalized:
            raise TicketCreationError(f"{field_name} must not be empty")

        if len(normalized) > max_length:
            raise TicketCreationError(
                f"{field_name} exceeds max length",
                details={
                    "field_name": field_name,
                    "max_length": max_length,
                    "actual_length": len(normalized),
                },
            )

        return normalized

    def _normalize_department(self, value: str) -> str:
        """Normalize department value."""
        normalized = self._validate_text(
            value,
            field_name="department",
            max_length=100,
        ).lower()

        allowed = {
            "hr",
            "it",
            "transportation",
            "finance",
            "legal",
            "security",
        }

        if normalized not in allowed:
            raise TicketRoutingError(
                "Unsupported department",
                details={
                    "department": normalized,
                    "allowed_departments": sorted(allowed),
                },
            )

        return normalized

    def _normalize_priority(self, value: str) -> str:
        """Normalize priority value."""
        normalized = self._validate_text(
            value,
            field_name="priority",
            max_length=50,
        ).lower()

        allowed = {"low", "medium", "high", "critical"}

        if normalized not in allowed:
            raise TicketCreationError(
                "Unsupported priority",
                details={
                    "priority": normalized,
                    "allowed_priorities": sorted(allowed),
                },
            )

        return normalized

    def _normalize_status(self, value: str) -> str:
        """Normalize ticket status."""
        normalized = self._validate_text(
            value,
            field_name="status",
            max_length=50,
        ).lower()

        allowed = {"open", "in_progress", "resolved", "closed"}

        if normalized not in allowed:
            raise TicketCreationError(
                "Unsupported ticket status",
                details={
                    "status": normalized,
                    "allowed_statuses": sorted(allowed),
                },
            )

        return normalized

    def _validate_pagination(self, *, limit: int, offset: int) -> None:
        """Validate pagination parameters."""
        if limit < 1 or limit > 200:
            raise TicketCreationError("limit must be between 1 and 200")

        if offset < 0:
            raise TicketCreationError("offset must not be negative")
