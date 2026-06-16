from __future__ import annotations

import time
from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ai_ticket_platform.app.config import Settings, get_settings
from ai_ticket_platform.app.utils.errors import (
    AppError,
    error_response_from_exception,
    log_exception,
)
from ai_ticket_platform.app.utils.logging import (
    get_logger,
    setup_logging,
)


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown lifecycle operations."""
    startup_started_at = time.perf_counter()

    settings = get_settings()

    app_logger = setup_logging(
        log_dir=settings.log_dir,
        level=settings.log_level,
    )

    app_logger.info(
        "Application startup started",
        extra={
            "event": "application_startup_started",
            "operation": "startup",
            "status": "started",
        },
    )

    try:
        app.state.settings = settings

        duration_ms = int((time.perf_counter() - startup_started_at) * 1000)

        app_logger.info(
            "Application startup completed successfully",
            extra={
                "event": "application_startup_completed",
                "operation": "startup",
                "status": "success",
                "duration_ms": duration_ms,
                "environment": settings.app_env,
            },
        )

        yield

    except Exception as exc:
        log_exception(exc, context={"operation": "startup"})

        app_logger.error(
            "Application startup failed",
            extra={
                "event": "application_startup_failed",
                "operation": "startup",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        raise

    finally:
        app_logger.info(
            "Application shutdown started",
            extra={
                "event": "application_shutdown_started",
                "operation": "shutdown",
                "status": "started",
            },
        )

        app_logger.info(
            "Application shutdown completed",
            extra={
                "event": "application_shutdown_completed",
                "operation": "shutdown",
                "status": "success",
            },
        )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings: Settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Enterprise AI Ticket Intelligence Platform with "
            "RAG, semantic search, and ML-based routing."
        ),
        debug=settings.debug,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    register_request_logging_middleware(app)
    register_routes(app, settings)

    logger.info(
        "FastAPI application instance created",
        extra={
            "event": "application_created",
            "operation": "create_app",
            "status": "success",
            "app_name": settings.app_name,
            "environment": settings.app_env,
        },
    )

    return app


def register_routes(app: FastAPI, settings: Settings) -> None:
    """Register API routes."""
    try:
        from ai_ticket_platform.app.api.admin import router as admin_router
        from ai_ticket_platform.app.api.chat import router as chat_router
        from ai_ticket_platform.app.api.documents import (
            router as documents_router,
        )
        from ai_ticket_platform.app.api.health import (
            router as health_router,
        )
        from ai_ticket_platform.app.api.tickets import (
            router as tickets_router,
        )

        app.include_router(
            health_router,
            prefix=settings.api_v1_prefix,
            tags=["Health"],
        )
        app.include_router(
            documents_router,
            prefix=settings.api_v1_prefix,
            tags=["Documents"],
        )
        app.include_router(
            tickets_router,
            prefix=settings.api_v1_prefix,
            tags=["Tickets"],
        )
        app.include_router(
            chat_router,
            prefix=settings.api_v1_prefix,
            tags=["Chat"],
        )
        app.include_router(
            admin_router,
            prefix=settings.api_v1_prefix,
            tags=["Admin"],
        )

        logger.info(
            "API routes registered",
            extra={
                "event": "api_routes_registered",
                "operation": "register_routes",
                "status": "success",
                "api_prefix": settings.api_v1_prefix,
                "routers": [
                    "health",
                    "documents",
                    "tickets",
                    "chat",
                    "admin",
                ],
            },
        )

    except Exception as exc:
        logger.error(
            "API route registration failed",
            extra={
                "event": "api_routes_registration_failed",
                "operation": "register_routes",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )
        raise


def register_exception_handlers(app: FastAPI) -> None:
    """Register API exception handlers."""

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)

        log_exception(
            exc,
            context={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )

        payload, status_code = error_response_from_exception(exc)

        return JSONResponse(
            status_code=status_code,
            content=payload,
            headers={"X-Request-ID": request_id or ""},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)

        log_exception(
            exc,
            context={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )

        payload, status_code = error_response_from_exception(exc)

        return JSONResponse(
            status_code=status_code,
            content=payload,
            headers={"X-Request-ID": request_id or ""},
        )


def register_request_logging_middleware(app: FastAPI) -> None:
    """Register request logging middleware."""

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next,
    ):
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid4()),
        )

        request.state.request_id = request_id

        started_at = time.perf_counter()

        logger.info(
            "HTTP request started",
            extra={
                "event": "http_request_started",
                "operation": "http_request",
                "status": "started",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        try:
            response = await call_next(request)

            duration_ms = int(
                (time.perf_counter() - started_at) * 1000
            )

            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http_request_completed",
                    "operation": "http_request",
                    "status": "success",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            duration_ms = int(
                (time.perf_counter() - started_at) * 1000
            )

            logger.error(
                "HTTP request failed",
                extra={
                    "event": "http_request_failed",
                    "operation": "http_request",
                    "status": "failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise


app = create_app()


if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "ai_ticket_platform.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
