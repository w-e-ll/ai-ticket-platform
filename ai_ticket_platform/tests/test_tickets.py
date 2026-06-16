from __future__ import annotations

from uuid import uuid4

import pytest

from ai_ticket_platform.app.models.db import TicketStatus
from ai_ticket_platform.app.services.ticket_service import TicketService
from ai_ticket_platform.app.utils.errors import TicketCreationError, TicketRoutingError


def test_ticket_service_validates_title() -> None:
    """Reject empty ticket title."""
    service = TicketService.__new__(TicketService)

    with pytest.raises(TicketCreationError):
        service._validate_text(
            "   ",
            field_name="title",
            max_length=500,
        )


def test_ticket_service_validates_description_length() -> None:
    """Reject overlong ticket description."""
    service = TicketService.__new__(TicketService)

    with pytest.raises(TicketCreationError):
        service._validate_text(
            "x" * 10001,
            field_name="description",
            max_length=10000,
        )


def test_ticket_service_normalizes_priority() -> None:
    """Normalize supported priority value."""
    service = TicketService.__new__(TicketService)

    result = service._normalize_priority(" HIGH ")

    assert result == "high"


def test_ticket_service_rejects_invalid_priority() -> None:
    """Reject unsupported priority value."""
    service = TicketService.__new__(TicketService)

    with pytest.raises(TicketCreationError):
        service._normalize_priority("urgent")


def test_ticket_service_normalizes_status() -> None:
    """Normalize supported ticket status."""
    service = TicketService.__new__(TicketService)

    result = service._normalize_status(" In_Progress ")

    assert result == TicketStatus.IN_PROGRESS.value


def test_ticket_service_rejects_invalid_status() -> None:
    """Reject unsupported ticket status."""
    service = TicketService.__new__(TicketService)

    with pytest.raises(TicketCreationError):
        service._normalize_status("waiting")


def test_ticket_service_normalizes_department() -> None:
    """Normalize supported department."""
    service = TicketService.__new__(TicketService)

    result = service._normalize_department(" IT ")

    assert result == "it"


def test_ticket_service_rejects_invalid_department() -> None:
    """Reject unsupported department."""
    service = TicketService.__new__(TicketService)

    with pytest.raises(TicketRoutingError):
        service._normalize_department("sales")


def test_ticket_service_validates_pagination() -> None:
    """Accept valid pagination parameters."""
    service = TicketService.__new__(TicketService)

    service._validate_pagination(limit=50, offset=0)


def test_ticket_service_rejects_invalid_limit() -> None:
    """Reject invalid pagination limit."""
    service = TicketService.__new__(TicketService)

    with pytest.raises(TicketCreationError):
        service._validate_pagination(limit=0, offset=0)

    with pytest.raises(TicketCreationError):
        service._validate_pagination(limit=201, offset=0)


def test_ticket_service_rejects_invalid_offset() -> None:
    """Reject invalid pagination offset."""
    service = TicketService.__new__(TicketService)

    with pytest.raises(TicketCreationError):
        service._validate_pagination(limit=50, offset=-1)


@pytest.mark.asyncio
async def test_ticket_service_create_ticket_with_manual_department(monkeypatch) -> None:
    """Create ticket using manual department without classifier dependency."""

    class FakeSession:
        """Minimal async DB session test double."""

        def add(self, item) -> None:
            """Accept added ORM object."""
            if getattr(item, "id", None) is None:
                item.id = uuid4()

        async def flush(self) -> None:
            """Simulate flush."""

        async def commit(self) -> None:
            """Simulate commit."""

        async def refresh(self, item) -> None:
            """Simulate refresh."""

        async def rollback(self) -> None:
            """Simulate rollback."""

    async def fake_summary(self, ticket_text: str) -> str:
        """Return deterministic summary."""
        return "Test summary"

    monkeypatch.setattr(
        TicketService,
        "_safe_summarize_ticket",
        fake_summary,
    )

    service = TicketService.__new__(TicketService)
    service.db_session = FakeSession()

    ticket, classification = await service.create_ticket(
        tenant_id=uuid4(),
        title="VPN issue",
        description="VPN does not connect.",
        department="it",
        priority="medium",
    )

    assert ticket.title == "VPN issue"
    assert ticket.department == "it"
    assert ticket.status == TicketStatus.OPEN.value
    assert classification.department == "it"
    assert classification.confidence == 1.0
