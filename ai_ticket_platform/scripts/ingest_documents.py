from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from ai_ticket_platform.app.database import AsyncSessionLocal
from ai_ticket_platform.app.services.document_service import DocumentService
from ai_ticket_platform.app.utils.logging import get_logger, setup_logging


logger = get_logger(__name__)


class LocalUploadFile:
    """Small UploadFile-compatible wrapper for local files."""

    def __init__(self, file_path: Path) -> None:
        """Open local file for document ingestion."""
        self.path = file_path
        self.filename = file_path.name
        self.content_type = self._detect_content_type(file_path)
        self.file = file_path.open("rb")

    def close(self) -> None:
        """Close opened local file."""
        self.file.close()

    def _detect_content_type(self, file_path: Path) -> str:
        """Detect basic content type from extension."""
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return "application/pdf"

        if extension == ".docx":
            return (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            )

        if extension == ".txt":
            return "text/plain"

        return "application/octet-stream"


async def ingest_document_file(
    *,
    tenant_id: UUID,
    file_path: Path,
    department: str | None,
) -> None:
    """Ingest one local document into the knowledge base."""
    logger.info(
        "Script document ingestion started",
        extra={
            "event": "script_document_ingestion_started",
            "operation": "ingest_document_file",
            "status": "started",
            "tenant_id": str(tenant_id),
            "filename": file_path.name,
            "department": department,
        },
    )

    upload_file = LocalUploadFile(file_path)

    try:
        async with AsyncSessionLocal() as db_session:
            document_service = DocumentService(db_session)

            document = await document_service.upload_and_index_document(
                tenant_id=tenant_id,
                upload_file=upload_file,  # type: ignore[arg-type]
                department=department,
            )

        logger.info(
            "Script document ingestion completed",
            extra={
                "event": "script_document_ingestion_completed",
                "operation": "ingest_document_file",
                "status": "success",
                "tenant_id": str(tenant_id),
                "document_id": str(document.id),
                "filename": document.filename,
                "chunk_count": document.chunk_count,
            },
        )

    except Exception as exc:
        logger.error(
            "Script document ingestion failed",
            extra={
                "event": "script_document_ingestion_failed",
                "operation": "ingest_document_file",
                "status": "failed",
                "tenant_id": str(tenant_id),
                "filename": file_path.name,
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )
        raise

    finally:
        upload_file.close()


async def ingest_path(
    *,
    tenant_id: UUID,
    path: Path,
    department: str | None,
) -> None:
    """Ingest one file or all supported files from directory."""
    logger.info(
        "Script ingestion path processing started",
        extra={
            "event": "script_ingestion_path_processing_started",
            "operation": "ingest_path",
            "status": "started",
            "tenant_id": str(tenant_id),
            "path": str(path),
            "department": department,
        },
    )

    if not path.exists():
        raise FileNotFoundError(f"path does not exist: {path}")

    if path.is_file():
        await ingest_document_file(
            tenant_id=tenant_id,
            file_path=path,
            department=department,
        )
        return

    supported_extensions = {".pdf", ".docx", ".txt"}

    files = sorted(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() in supported_extensions
    )

    if not files:
        logger.warning(
            "No supported documents found for ingestion",
            extra={
                "event": "script_no_supported_documents_found",
                "operation": "ingest_path",
                "status": "warning",
                "path": str(path),
            },
        )
        return

    for file_path in files:
        await ingest_document_file(
            tenant_id=tenant_id,
            file_path=file_path,
            department=department,
        )

    logger.info(
        "Script ingestion path processing completed",
        extra={
            "event": "script_ingestion_path_processing_completed",
            "operation": "ingest_path",
            "status": "success",
            "tenant_id": str(tenant_id),
            "path": str(path),
            "file_count": len(files),
        },
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest documents into AI Ticket Platform knowledge base.",
    )

    parser.add_argument(
        "--tenant-id",
        required=True,
        help="Tenant UUID.",
    )

    parser.add_argument(
        "--path",
        required=True,
        help="Document file or directory path.",
    )

    parser.add_argument(
        "--department",
        default=None,
        choices=[
            "hr",
            "it",
            "transportation",
            "finance",
            "legal",
            "security",
        ],
        help="Optional department metadata.",
    )

    return parser.parse_args()


async def main() -> None:
    """Run document ingestion script."""
    setup_logging()

    args = parse_args()

    tenant_id = UUID(args.tenant_id)
    path = Path(args.path).resolve()

    logger.info(
        "Document ingestion script started",
        extra={
            "event": "document_ingestion_script_started",
            "operation": "main",
            "status": "started",
            "tenant_id": str(tenant_id),
            "path": str(path),
            "department": args.department,
        },
    )

    await ingest_path(
        tenant_id=tenant_id,
        path=path,
        department=args.department,
    )

    logger.info(
        "Document ingestion script completed",
        extra={
            "event": "document_ingestion_script_completed",
            "operation": "main",
            "status": "success",
            "tenant_id": str(tenant_id),
            "path": str(path),
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
