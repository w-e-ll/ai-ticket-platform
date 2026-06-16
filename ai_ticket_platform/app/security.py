from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.utils.errors import AuthenticationError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

settings = get_settings()

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    logger.debug(
        "Password verification started",
        extra={
            "event": "password_verification_started",
            "operation": "verify_password",
            "status": "started",
        },
    )

    try:
        result = password_context.verify(plain_password, hashed_password)

        logger.info(
            "Password verification completed",
            extra={
                "event": "password_verification_completed",
                "operation": "verify_password",
                "status": "success",
            },
        )

        return result

    except Exception as exc:
        logger.error(
            "Password verification failed",
            extra={
                "event": "password_verification_failed",
                "operation": "verify_password",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        raise AuthenticationError("Password verification failed") from exc


def hash_password(password: str) -> str:
    """Hash user password."""
    if not password or len(password) < 8:
        logger.error(
            "Password hashing validation failed",
            extra={
                "event": "password_hashing_validation_failed",
                "operation": "hash_password",
                "status": "failed",
            },
        )
        raise AuthenticationError("Password must be at least 8 characters long")

    logger.debug(
        "Password hashing started",
        extra={
            "event": "password_hashing_started",
            "operation": "hash_password",
            "status": "started",
        },
    )

    hashed_password = password_context.hash(password)

    logger.info(
        "Password hashing completed",
        extra={
            "event": "password_hashing_completed",
            "operation": "hash_password",
            "status": "success",
        },
    )

    return hashed_password


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create signed JWT access token."""
    if not subject or not subject.strip():
        logger.error(
            "Access token creation failed: empty subject",
            extra={
                "event": "access_token_creation_failed",
                "operation": "create_access_token",
                "status": "failed",
            },
        )
        raise AuthenticationError("Token subject must not be empty")

    now = datetime.now(timezone.utc)

    expire_at = now + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }

    if extra_claims:
        payload.update(extra_claims)

    try:
        token = jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.algorithm,
        )

        logger.info(
            "Access token created",
            extra={
                "event": "access_token_created",
                "operation": "create_access_token",
                "status": "success",
                "expires_at": expire_at.isoformat(),
            },
        )

        return token

    except Exception as exc:
        logger.error(
            "Access token creation failed",
            extra={
                "event": "access_token_creation_failed",
                "operation": "create_access_token",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        raise AuthenticationError("Access token creation failed") from exc


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT access token."""
    if not token or not token.strip():
        logger.error(
            "Access token decoding failed: empty token",
            extra={
                "event": "access_token_decoding_failed",
                "operation": "decode_access_token",
                "status": "failed",
            },
        )
        raise AuthenticationError("Access token must not be empty")

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        logger.info(
            "Access token decoded",
            extra={
                "event": "access_token_decoded",
                "operation": "decode_access_token",
                "status": "success",
            },
        )

        return payload

    except JWTError as exc:
        logger.warning(
            "Invalid access token",
            extra={
                "event": "access_token_invalid",
                "operation": "decode_access_token",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
        )

        raise AuthenticationError("Invalid or expired access token") from exc


def get_token_subject(token: str) -> str:
    """Extract subject from JWT access token."""
    payload = decode_access_token(token)
    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.strip():
        logger.error(
            "Token subject extraction failed",
            extra={
                "event": "token_subject_extraction_failed",
                "operation": "get_token_subject",
                "status": "failed",
            },
        )
        raise AuthenticationError("Token subject is missing")

    logger.debug(
        "Token subject extracted",
        extra={
            "event": "token_subject_extracted",
            "operation": "get_token_subject",
            "status": "success",
        },
    )

    return subject
