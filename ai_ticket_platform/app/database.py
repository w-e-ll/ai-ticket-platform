from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.utils.errors import DatabaseError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for FastAPI dependencies."""
    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception as exc:
            await session.rollback()

            logger.error(
                "Database session failed",
                extra={
                    "event": "database_session_failed",
                    "operation": "database_session",
                    "status": "failed",
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise DatabaseError(
                "Database operation failed",
                details={"exception_type": type(exc).__name__},
            ) from exc

        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Check database connectivity."""
    try:
        async with engine.connect() as connection:
            await connection.exec_driver_sql("SELECT 1")

        logger.info(
            "Database connection check completed",
            extra={
                "event": "database_connection_check_completed",
                "operation": "database_connection_check",
                "status": "success",
            },
        )

        return True

    except Exception as exc:
        logger.error(
            "Database connection check failed",
            extra={
                "event": "database_connection_check_failed",
                "operation": "database_connection_check",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        return False


async def close_database_connection() -> None:
    """Dispose database engine."""
    await engine.dispose()

    logger.info(
        "Database connection pool disposed",
        extra={
            "event": "database_connection_pool_disposed",
            "operation": "database_shutdown",
            "status": "success",
        },
    )
