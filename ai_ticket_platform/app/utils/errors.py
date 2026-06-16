from __future__ import annotations

from http import HTTPStatus
from typing import Any

from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


class AppError(Exception):
    """Base application exception with API-safe metadata."""

    default_status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code: str = "application_error"

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if not message or not message.strip():
            logger.error("Application error initialized with empty message")
            raise ValueError("exception message must not be empty")

        self.message = message.strip()
        self.error_code = error_code or self.default_error_code
        self.status_code = status_code or self.default_status_code
        self.details = details or {}

        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


class ConfigurationError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "configuration_error"


class StartupValidationError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "startup_validation_error"


class RequestValidationError(AppError):
    default_status_code = HTTPStatus.BAD_REQUEST
    default_error_code = "request_validation_error"


class AuthenticationError(AppError):
    default_status_code = HTTPStatus.UNAUTHORIZED
    default_error_code = "authentication_error"


class AuthorizationError(AppError):
    default_status_code = HTTPStatus.FORBIDDEN
    default_error_code = "authorization_error"


class ResourceNotFoundError(AppError):
    default_status_code = HTTPStatus.NOT_FOUND
    default_error_code = "resource_not_found"


class ConflictError(AppError):
    default_status_code = HTTPStatus.CONFLICT
    default_error_code = "conflict_error"


class FileStorageError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "file_storage_error"


class DocumentParsingError(AppError):
    default_status_code = HTTPStatus.BAD_REQUEST
    default_error_code = "document_parsing_error"


class DocumentValidationError(AppError):
    default_status_code = HTTPStatus.BAD_REQUEST
    default_error_code = "document_validation_error"


class ChunkingError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "chunking_error"


class EmbeddingError(AppError):
    default_status_code = HTTPStatus.BAD_GATEWAY
    default_error_code = "embedding_error"


class VectorStoreError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "vector_store_error"


class RetrievalError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "retrieval_error"


class LLMServiceError(AppError):
    default_status_code = HTTPStatus.BAD_GATEWAY
    default_error_code = "llm_service_error"


class ClassificationError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "classification_error"


class TicketRoutingError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "ticket_routing_error"


class TicketCreationError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "ticket_creation_error"


class AnalyticsError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "analytics_error"


class DatabaseError(AppError):
    default_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_error_code = "database_error"


class ExternalServiceError(AppError):
    default_status_code = HTTPStatus.BAD_GATEWAY
    default_error_code = "external_service_error"


class RateLimitError(AppError):
    default_status_code = HTTPStatus.TOO_MANY_REQUESTS
    default_error_code = "rate_limit_error"


class TimeoutError(AppError):
    default_status_code = HTTPStatus.GATEWAY_TIMEOUT
    default_error_code = "timeout_error"


def log_exception(
    exc: Exception,
    *,
    context: dict[str, Any] | None = None,
) -> None:
    context = context or {}

    if isinstance(exc, AppError):
        logger.error(
            "Application error occurred",
            extra={
                "event": "application_error",
                "operation": "exception_handling",
                "status": "failed",
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                **context,
            },
            exc_info=True,
        )
        return

    logger.error(
        "Unexpected exception occurred",
        extra={
            "event": "unexpected_exception",
            "operation": "exception_handling",
            "status": "failed",
            "exception_type": type(exc).__name__,
            **context,
        },
        exc_info=True,
    )


def error_response_from_exception(exc: Exception) -> tuple[dict[str, Any], int]:
    if isinstance(exc, AppError):
        return exc.to_dict(), int(exc.status_code)

    return (
        {
            "error": {
                "code": "internal_server_error",
                "message": "Unexpected internal error",
                "details": {},
            }
        },
        int(HTTPStatus.INTERNAL_SERVER_ERROR),
    )
