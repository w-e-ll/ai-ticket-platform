from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.app.database import get_db_session
from ai_ticket_platform.app.models.schemas import (
    DocumentRead,
)
from ai_ticket_platform.app.services.document_service import (
    DocumentService,
)
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    tenant_id: UUID,
    file: UploadFile = File(...),
    department: str | None = Query(default=None),
    db_session: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    """Upload and index knowledge-base document."""
    logger.info(
        "Document upload request received",
        extra={
            "event": "document_upload_request_received",
            "operation": "upload_document",
            "status": "started",
            "tenant_id": str(tenant_id),
            "filename": file.filename,
            "content_type": file.content_type,
            "department": department,
        },
    )

    document_service = DocumentService(db_session)

    document = await document_service.upload_and_index_document(
        tenant_id=tenant_id,
        upload_file=file,
        department=department,
    )

    logger.info(
        "Document upload request completed",
        extra={
            "event": "document_upload_request_completed",
            "operation": "upload_document",
            "status": "success",
            "tenant_id": str(tenant_id),
            "document_id": str(document.id),
            "filename": document.filename,
            "chunk_count": document.chunk_count,
        },
    )

    return DocumentRead.model_validate(document)


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    status_code=status.HTTP_200_OK,
)
async def get_document(
    document_id: UUID,
    tenant_id: UUID = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    """Return document metadata."""
    logger.info(
        "Document retrieval request received",
        extra={
            "event": "document_retrieval_request_received",
            "operation": "get_document",
            "status": "started",
            "tenant_id": str(tenant_id),
            "document_id": str(document_id),
        },
    )

    document_service = DocumentService(db_session)

    document = await document_service.get_document(
        tenant_id=tenant_id,
        document_id=document_id,
    )

    logger.info(
        "Document retrieval request completed",
        extra={
            "event": "document_retrieval_request_completed",
            "operation": "get_document",
            "status": "success",
            "tenant_id": str(tenant_id),
            "document_id": str(document.id),
            "filename": document.filename,
        },
    )

    return DocumentRead.model_validate(document)


@router.get(
    "",
    response_model=list[DocumentRead],
    status_code=status.HTTP_200_OK,
)
async def list_documents(
    tenant_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[DocumentRead]:
    """List tenant knowledge-base documents."""
    logger.info(
        "Document listing request received",
        extra={
            "event": "document_listing_request_received",
            "operation": "list_documents",
            "status": "started",
            "tenant_id": str(tenant_id),
            "limit": limit,
            "offset": offset,
        },
    )

    document_service = DocumentService(db_session)

    documents = await document_service.list_documents(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )

    logger.info(
        "Document listing request completed",
        extra={
            "event": "document_listing_request_completed",
            "operation": "list_documents",
            "status": "success",
            "tenant_id": str(tenant_id),
            "document_count": len(documents),
        },
    )

    return [
        DocumentRead.model_validate(document)
        for document in documents
    ]
