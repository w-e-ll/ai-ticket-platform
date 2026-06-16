from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from ai_ticket_platform.app.database import AsyncSessionLocal
from ai_ticket_platform.app.models.db import (
    Document,
    DocumentChunk,
    Tenant,
    Ticket,
    TicketMessage,
    User,
)
from ai_ticket_platform.app.security import hash_password
from ai_ticket_platform.app.services.classifier_service import ClassifierService
from ai_ticket_platform.app.utils.logging import get_logger, setup_logging


logger = get_logger(__name__)


DEMO_TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")


async def seed_tenant() -> Tenant:
    """Create demo tenant."""
    logger.info(
        "Tenant seed started",
        extra={
            "event": "tenant_seed_started",
            "operation": "seed_tenant",
            "status": "started",
            "tenant_id": str(DEMO_TENANT_ID),
        },
    )

    async with AsyncSessionLocal() as db_session:
        tenant = Tenant(
            id=DEMO_TENANT_ID,
            name="Demo Enterprise",
            slug="demo-enterprise",
            is_active=True,
        )

        db_session.add(tenant)

        await db_session.commit()
        await db_session.refresh(tenant)

    logger.info(
        "Tenant seed completed",
        extra={
            "event": "tenant_seed_completed",
            "operation": "seed_tenant",
            "status": "success",
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
        },
    )

    return tenant


async def seed_users(*, tenant_id: UUID) -> list[User]:
    """Create demo users."""
    logger.info(
        "User seed started",
        extra={
            "event": "user_seed_started",
            "operation": "seed_users",
            "status": "started",
            "tenant_id": str(tenant_id),
        },
    )

    users_data = [
        {
            "email": "admin@demo.local",
            "full_name": "Demo Administrator",
            "role": "admin",
            "password": "AdminPassword123!",
        },
        {
            "email": "support@demo.local",
            "full_name": "Support Engineer",
            "role": "support",
            "password": "SupportPassword123!",
        },
        {
            "email": "employee@demo.local",
            "full_name": "Demo Employee",
            "role": "employee",
            "password": "EmployeePassword123!",
        },
    ]

    created_users: list[User] = []

    async with AsyncSessionLocal() as db_session:
        for item in users_data:
            user = User(
                tenant_id=tenant_id,
                email=item["email"],
                full_name=item["full_name"],
                role=item["role"],
                hashed_password=hash_password(item["password"]),
                is_active=True,
            )

            db_session.add(user)
            created_users.append(user)

            logger.debug(
                "Seed user prepared",
                extra={
                    "event": "seed_user_prepared",
                    "operation": "seed_users",
                    "status": "success",
                    "email": item["email"],
                    "role": item["role"],
                },
            )

        await db_session.commit()

        for user in created_users:
            await db_session.refresh(user)

    logger.info(
        "User seed completed",
        extra={
            "event": "user_seed_completed",
            "operation": "seed_users",
            "status": "success",
            "tenant_id": str(tenant_id),
            "user_count": len(created_users),
        },
    )

    return created_users


async def seed_tickets(
    *,
    tenant_id: UUID,
    created_by_user_id: UUID,
) -> list[Ticket]:
    """Create demo tickets."""
    logger.info(
        "Ticket seed started",
        extra={
            "event": "ticket_seed_started",
            "operation": "seed_tickets",
            "status": "started",
            "tenant_id": str(tenant_id),
        },
    )

    classifier_service = ClassifierService()

    tickets_data = [
        {
            "title": "VPN access not working",
            "description": (
                "I cannot connect to company VPN after password reset."
            ),
            "priority": "high",
        },
        {
            "title": "Salary payment delay",
            "description": (
                "My salary has not arrived this month."
            ),
            "priority": "critical",
        },
        {
            "title": "Suspicious login detected",
            "description": (
                "I received multiple MFA prompts during the night."
            ),
            "priority": "high",
        },
    ]

    created_tickets: list[Ticket] = []

    async with AsyncSessionLocal() as db_session:
        for item in tickets_data:
            classification = classifier_service.classify(
                f"{item['title']}\n\n{item['description']}"
            )

            ticket = Ticket(
                tenant_id=tenant_id,
                created_by_user_id=created_by_user_id,
                title=item["title"],
                description=item["description"],
                department=classification.department,
                priority=item["priority"],
                status="open",
                classification_confidence=classification.confidence,
                ai_summary=f"AI summary for: {item['title']}",
                metadata_json={
                    "seeded": True,
                    "classification_probabilities": (
                        classification.probabilities
                    ),
                },
            )

            db_session.add(ticket)
            await db_session.flush()

            initial_message = TicketMessage(
                ticket_id=ticket.id,
                sender_type="user",
                content=item["description"],
            )

            db_session.add(initial_message)

            created_tickets.append(ticket)

            logger.debug(
                "Seed ticket prepared",
                extra={
                    "event": "seed_ticket_prepared",
                    "operation": "seed_tickets",
                    "status": "success",
                    "ticket_title": ticket.title,
                    "department": ticket.department,
                    "priority": ticket.priority,
                },
            )

        await db_session.commit()

        for ticket in created_tickets:
            await db_session.refresh(ticket)

    logger.info(
        "Ticket seed completed",
        extra={
            "event": "ticket_seed_completed",
            "operation": "seed_tickets",
            "status": "success",
            "tenant_id": str(tenant_id),
            "ticket_count": len(created_tickets),
        },
    )

    return created_tickets


async def seed_documents(*, tenant_id: UUID) -> list[Document]:
    """Create demo documents and chunks."""
    logger.info(
        "Document seed started",
        extra={
            "event": "document_seed_started",
            "operation": "seed_documents",
            "status": "started",
            "tenant_id": str(tenant_id),
        },
    )

    documents_data = [
        {
            "filename": "vpn_policy.txt",
            "department": "it",
            "content": (
                "Employees must reset VPN passwords every 90 days."
            ),
        },
        {
            "filename": "salary_policy.txt",
            "department": "finance",
            "content": (
                "Salary payments are processed on the last working day."
            ),
        },
    ]

    created_documents: list[Document] = []

    async with AsyncSessionLocal() as db_session:
        for item in documents_data:
            document = Document(
                tenant_id=tenant_id,
                filename=item["filename"],
                file_path=f"/seed/{item['filename']}",
                content_type="text/plain",
                file_size_bytes=len(item["content"]),
                department=item["department"],
                is_processed=True,
                chunk_count=1,
                metadata_json={
                    "seeded": True,
                },
            )

            db_session.add(document)
            await db_session.flush()

            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                content=item["content"],
                vector_id=str(uuid4()),
                embedding_model="seed-model",
                metadata_json={
                    "seeded": True,
                },
            )

            db_session.add(chunk)

            created_documents.append(document)

            logger.debug(
                "Seed document prepared",
                extra={
                    "event": "seed_document_prepared",
                    "operation": "seed_documents",
                    "status": "success",
                    "filename": document.filename,
                    "department": document.department,
                },
            )

        await db_session.commit()

        for document in created_documents:
            await db_session.refresh(document)

    logger.info(
        "Document seed completed",
        extra={
            "event": "document_seed_completed",
            "operation": "seed_documents",
            "status": "success",
            "tenant_id": str(tenant_id),
            "document_count": len(created_documents),
        },
    )

    return created_documents


async def main() -> None:
    """Run full demo data seeding."""
    setup_logging()

    logger.info(
        "Database seed script started",
        extra={
            "event": "database_seed_script_started",
            "operation": "seed_main",
            "status": "started",
        },
    )

    tenant = await seed_tenant()

    users = await seed_users(
        tenant_id=tenant.id,
    )

    await seed_tickets(
        tenant_id=tenant.id,
        created_by_user_id=users[0].id,
    )

    await seed_documents(
        tenant_id=tenant.id,
    )

    logger.info(
        "Database seed script completed",
        extra={
            "event": "database_seed_script_completed",
            "operation": "seed_main",
            "status": "success",
            "tenant_id": str(tenant.id),
        },
    )

    print()
    print("Demo environment successfully seeded.")
    print()
    print(f"Tenant ID: {tenant.id}")
    print()
    print("Users:")
    print("- admin@demo.local / AdminPassword123!")
    print("- support@demo.local / SupportPassword123!")
    print("- employee@demo.local / EmployeePassword123!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
