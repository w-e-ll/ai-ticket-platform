from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request

from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> dict[str, Any]:
    """Return application health status."""
    settings = request.app.state.settings

    logger.info(
        "Health check requested",
        extra={
            "event": "health_check_requested",
            "operation": "health_check",
            "status": "success",
            "request_id": getattr(request.state, "request_id", None),
        },
    )

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check(request: Request) -> dict[str, Any]:
    """Return readiness status."""
    settings = request.app.state.settings

    logger.info(
        "Readiness check requested",
        extra={
            "event": "readiness_check_requested",
            "operation": "readiness_check",
            "status": "success",
            "request_id": getattr(request.state, "request_id", None),
        },
    )

    return {
        "status": "ready",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
