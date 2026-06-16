from __future__ import annotations

from dataclasses import dataclass

from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.utils.errors import ChunkingError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class TextChunk:
    """Text chunk with position metadata."""

    content: str
    chunk_index: int
    start_char: int
    end_char: int


class TextChunker:
    """Splits long text into overlapping chunks."""

    def __init__(
        self,
        *,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        """Initialize chunker configuration."""
        settings = get_settings()

        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        self._validate_settings()

        logger.info(
            "Text chunker initialized",
            extra={
                "event": "text_chunker_initialized",
                "operation": "chunking_init",
                "status": "success",
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            },
        )

    def _validate_settings(self) -> None:
        """Validate chunking settings."""
        if self.chunk_size <= 0:
            raise ChunkingError("chunk_size must be greater than zero")

        if self.chunk_overlap < 0:
            raise ChunkingError("chunk_overlap must not be negative")

        if self.chunk_overlap >= self.chunk_size:
            raise ChunkingError("chunk_overlap must be smaller than chunk_size")

    def split(self, text: str) -> list[TextChunk]:
        """Split text into normalized overlapping chunks."""
        logger.info(
            "Text chunking started",
            extra={
                "event": "text_chunking_started",
                "operation": "split_text",
                "status": "started",
                "text_length": len(text or ""),
            },
        )

        try:
            normalized_text = self._normalize_text(text)

            if not normalized_text:
                logger.warning(
                    "Text chunking skipped: empty text",
                    extra={
                        "event": "text_chunking_skipped",
                        "operation": "split_text",
                        "status": "warning",
                    },
                )
                return []

            chunks: list[TextChunk] = []
            start = 0
            chunk_index = 0
            text_length = len(normalized_text)

            while start < text_length:
                end = min(start + self.chunk_size, text_length)
                raw_chunk = normalized_text[start:end].strip()

                if raw_chunk:
                    chunks.append(
                        TextChunk(
                            content=raw_chunk,
                            chunk_index=chunk_index,
                            start_char=start,
                            end_char=end,
                        )
                    )

                    logger.debug(
                        "Text chunk created",
                        extra={
                            "event": "text_chunk_created",
                            "operation": "split_text",
                            "status": "success",
                            "chunk_index": chunk_index,
                            "start_char": start,
                            "end_char": end,
                        },
                    )

                    chunk_index += 1

                if end >= text_length:
                    break

                start = end - self.chunk_overlap

            logger.info(
                "Text chunking completed",
                extra={
                    "event": "text_chunking_completed",
                    "operation": "split_text",
                    "status": "success",
                    "chunk_count": len(chunks),
                    "text_length": text_length,
                },
            )

            return chunks

        except ChunkingError:
            raise

        except Exception as exc:
            logger.error(
                "Text chunking failed",
                extra={
                    "event": "text_chunking_failed",
                    "operation": "split_text",
                    "status": "failed",
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise ChunkingError("Failed to split text into chunks") from exc

    def _normalize_text(self, text: str) -> str:
        """Normalize raw text before chunking."""
        if text is None:
            raise ChunkingError("text must not be None")

        normalized = "\n".join(
            line.strip()
            for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            if line.strip()
        )

        logger.debug(
            "Text normalized for chunking",
            extra={
                "event": "text_normalized",
                "operation": "normalize_text",
                "status": "success",
                "text_length": len(normalized),
            },
        )

        return normalized


def chunk_text(
    text: str,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[TextChunk]:
    """Convenience function for splitting text into chunks."""
    chunker = TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return chunker.split(text)
