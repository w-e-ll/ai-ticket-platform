from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """API health response."""

    status: str = Field(min_length=2, max_length=50)
    app_name: str = Field(min_length=2, max_length=255)
    environment: str = Field(min_length=2, max_length=50)
    timestamp: str = Field(min_length=10)


class TenantCreate(BaseModel):
    """Payload for creating a tenant."""

    name: str = Field(min_length=2, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Normalize tenant name."""
        normalized = value.strip()

        if not normalized:
            logger.error("Tenant name validation failed: empty value")
            raise ValueError("tenant name must not be empty")

        logger.debug("Tenant name normalized", extra={"operation": "tenant_validation"})

        return normalized


class TenantRead(BaseModel):
    """Tenant read model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    """Payload for creating a user."""

    tenant_id: UUID
    email: str = Field(min_length=5, max_length=255)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    role: str = Field(default="user", min_length=2, max_length=50)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate and normalize email."""
        normalized = value.strip().lower()

        if "@" not in normalized:
            logger.error("User email validation failed", extra={"operation": "user_validation"})
            raise ValueError("email must contain @")

        return normalized

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        """Normalize full name."""
        normalized = " ".join(value.strip().split())

        if not normalized:
            raise ValueError("full name must not be empty")

        return normalized


class UserRead(BaseModel):
    """User read model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TicketCreate(BaseModel):
    """Payload for creating a ticket."""

    tenant_id: UUID
    created_by_user_id: UUID | None = None
    title: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=3, max_length=10000)
    department: str | None = Field(default=None, max_length=100)
    priority: str = Field(default="medium", min_length=2, max_length=50)

    @field_validator("title", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """Normalize ticket text fields."""
        normalized = " ".join(value.strip().split())

        if not normalized:
            logger.error("Ticket text validation failed", extra={"operation": "ticket_validation"})
            raise ValueError("ticket text must not be empty")

        return normalized

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        """Validate ticket priority."""
        normalized = value.strip().lower()
        allowed = {"low", "medium", "high", "critical"}

        if normalized not in allowed:
            logger.error(
                "Ticket priority validation failed",
                extra={
                    "operation": "ticket_validation",
                    "priority": normalized,
                },
            )
            raise ValueError(f"priority must be one of: {sorted(allowed)}")

        return normalized


class TicketRead(BaseModel):
    """Ticket read model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_by_user_id: UUID | None
    title: str
    description: str
    department: str
    priority: str
    status: str
    classification_confidence: float | None
    ai_summary: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class TicketUpdate(BaseModel):
    """Payload for updating a ticket."""

    title: str | None = Field(default=None, min_length=3, max_length=500)
    description: str | None = Field(default=None, min_length=3, max_length=10000)
    department: str | None = Field(default=None, max_length=100)
    priority: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=50)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        """Validate ticket status."""
        if value is None:
            return value

        normalized = value.strip().lower()
        allowed = {"open", "in_progress", "resolved", "closed"}

        if normalized not in allowed:
            logger.error(
                "Ticket status validation failed",
                extra={
                    "operation": "ticket_validation",
                    "status": normalized,
                },
            )
            raise ValueError(f"status must be one of: {sorted(allowed)}")

        return normalized


class TicketMessageCreate(BaseModel):
    """Payload for creating a ticket message."""

    ticket_id: UUID
    sender_type: str = Field(min_length=2, max_length=50)
    content: str = Field(min_length=1, max_length=10000)


class TicketMessageRead(BaseModel):
    """Ticket message read model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    sender_type: str
    content: str
    created_at: datetime


class DocumentRead(BaseModel):
    """Document read model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    filename: str
    file_path: str
    content_type: str
    file_size_bytes: int
    chunk_count: int
    is_processed: bool
    created_at: datetime


class DocumentChunkRead(BaseModel):
    """Document chunk read model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    embedding_model: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime


class ChatRequest(BaseModel):
    """Payload for RAG chat request."""

    tenant_id: UUID
    message: str = Field(min_length=1, max_length=10000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        """Normalize chat message."""
        normalized = " ".join(value.strip().split())

        if not normalized:
            logger.error("Chat message validation failed", extra={"operation": "chat_validation"})
            raise ValueError("message must not be empty")

        return normalized


class RetrievedContext(BaseModel):
    """Retrieved RAG context item."""

    document_id: UUID | None = None
    chunk_id: UUID | None = None
    content: str = Field(min_length=1)
    score: float | None = Field(default=None, ge=0.0)
    metadata: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """RAG chat response."""

    answer: str = Field(min_length=1)
    contexts: list[RetrievedContext] = Field(default_factory=list)


class ClassificationRequest(BaseModel):
    """Payload for ticket classification."""

    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """Normalize classification text."""
        normalized = " ".join(value.strip().split())

        if not normalized:
            logger.error(
                "Classification text validation failed",
                extra={"operation": "classification_validation"},
            )
            raise ValueError("classification text must not be empty")

        return normalized


class ClassificationResponse(BaseModel):
    """Ticket classification result."""

    department: str = Field(min_length=2, max_length=100)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    probabilities: dict[str, float] | None = None


class TicketSubmissionRequest(BaseModel):
    """Payload for AI-assisted ticket submission."""

    tenant_id: UUID
    created_by_user_id: UUID | None = None
    title: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=3, max_length=10000)


class TicketSubmissionResponse(BaseModel):
    """Response after ticket submission."""

    ticket: TicketRead
    classification: ClassificationResponse


class ErrorDetail(BaseModel):
    """API error detail."""

    code: str = Field(min_length=2, max_length=100)
    message: str = Field(min_length=1, max_length=1000)
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """API error response."""

    error: ErrorDetail
