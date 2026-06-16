from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.utils.errors import EmbeddingError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


class EmbeddingProvider(ABC):
    """Base interface for embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Embed one text value."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text values."""

    @abstractmethod
    def model_name(self) -> str:
        """Return embedding model name."""


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, *, model: str | None = None) -> None:
        """Initialize OpenAI embeddings client."""
        settings = get_settings()

        self._model = model or settings.openai_embedding_model
        self._client = OpenAI(api_key=settings.openai_api_key)

        logger.info(
            "OpenAI embedding provider initialized",
            extra={
                "event": "embedding_provider_initialized",
                "operation": "embedding_init",
                "status": "success",
                "provider": "openai",
                "model": self._model,
            },
        )

    def embed_text(self, text: str) -> list[float]:
        """Embed one text value."""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text values."""
        normalized_texts = self._validate_texts(texts)

        logger.info(
            "OpenAI embedding generation started",
            extra={
                "event": "embedding_generation_started",
                "operation": "embed_texts",
                "status": "started",
                "provider": "openai",
                "model": self._model,
                "text_count": len(normalized_texts),
            },
        )

        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=normalized_texts,
            )

            vectors = [item.embedding for item in response.data]

            logger.info(
                "OpenAI embedding generation completed",
                extra={
                    "event": "embedding_generation_completed",
                    "operation": "embed_texts",
                    "status": "success",
                    "provider": "openai",
                    "model": self._model,
                    "text_count": len(normalized_texts),
                    "embedding_count": len(vectors),
                },
            )

            return vectors

        except Exception as exc:
            logger.error(
                "OpenAI embedding generation failed",
                extra={
                    "event": "embedding_generation_failed",
                    "operation": "embed_texts",
                    "status": "failed",
                    "provider": "openai",
                    "model": self._model,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise EmbeddingError("OpenAI embedding generation failed") from exc

    def model_name(self) -> str:
        """Return embedding model name."""
        return self._model

    def _validate_texts(self, texts: list[str]) -> list[str]:
        """Validate and normalize embedding input texts."""
        if not texts:
            raise EmbeddingError("texts must not be empty")

        normalized_texts: list[str] = []

        for index, text in enumerate(texts):
            if not isinstance(text, str):
                raise EmbeddingError(
                    "embedding input must be a string",
                    details={"index": index},
                )

            normalized = text.strip()

            if not normalized:
                raise EmbeddingError(
                    "embedding input must not be empty",
                    details={"index": index},
                )

            normalized_texts.append(normalized)

        return normalized_texts


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers embedding provider."""

    def __init__(self, *, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        """Initialize local embedding model."""
        self._model_name = model

        logger.info(
            "SentenceTransformer embedding provider initialization started",
            extra={
                "event": "embedding_provider_initialization_started",
                "operation": "embedding_init",
                "status": "started",
                "provider": "sentence_transformers",
                "model": self._model_name,
            },
        )

        try:
            self._model = SentenceTransformer(self._model_name)

            logger.info(
                "SentenceTransformer embedding provider initialized",
                extra={
                    "event": "embedding_provider_initialized",
                    "operation": "embedding_init",
                    "status": "success",
                    "provider": "sentence_transformers",
                    "model": self._model_name,
                },
            )

        except Exception as exc:
            logger.error(
                "SentenceTransformer embedding provider initialization failed",
                extra={
                    "event": "embedding_provider_initialization_failed",
                    "operation": "embedding_init",
                    "status": "failed",
                    "provider": "sentence_transformers",
                    "model": self._model_name,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise EmbeddingError("SentenceTransformer initialization failed") from exc

    def embed_text(self, text: str) -> list[float]:
        """Embed one text value."""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text values."""
        normalized_texts = self._validate_texts(texts)

        logger.info(
            "SentenceTransformer embedding generation started",
            extra={
                "event": "embedding_generation_started",
                "operation": "embed_texts",
                "status": "started",
                "provider": "sentence_transformers",
                "model": self._model_name,
                "text_count": len(normalized_texts),
            },
        )

        try:
            vectors = self._model.encode(
                normalized_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            result = [vector.astype(float).tolist() for vector in vectors]

            logger.info(
                "SentenceTransformer embedding generation completed",
                extra={
                    "event": "embedding_generation_completed",
                    "operation": "embed_texts",
                    "status": "success",
                    "provider": "sentence_transformers",
                    "model": self._model_name,
                    "text_count": len(normalized_texts),
                    "embedding_count": len(result),
                    "embedding_dimension": len(result[0]) if result else 0,
                },
            )

            return result

        except Exception as exc:
            logger.error(
                "SentenceTransformer embedding generation failed",
                extra={
                    "event": "embedding_generation_failed",
                    "operation": "embed_texts",
                    "status": "failed",
                    "provider": "sentence_transformers",
                    "model": self._model_name,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise EmbeddingError("SentenceTransformer embedding generation failed") from exc

    def model_name(self) -> str:
        """Return embedding model name."""
        return self._model_name

    def _validate_texts(self, texts: list[str]) -> list[str]:
        """Validate and normalize embedding input texts."""
        if not texts:
            raise EmbeddingError("texts must not be empty")

        normalized_texts: list[str] = []

        for index, text in enumerate(texts):
            if not isinstance(text, str):
                raise EmbeddingError(
                    "embedding input must be a string",
                    details={"index": index},
                )

            normalized = text.strip()

            if not normalized:
                raise EmbeddingError(
                    "embedding input must not be empty",
                    details={"index": index},
                )

            normalized_texts.append(normalized)

        return normalized_texts


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """Create and cache configured embedding provider."""
    settings = get_settings()

    logger.info(
        "Embedding provider selection started",
        extra={
            "event": "embedding_provider_selection_started",
            "operation": "get_embedding_provider",
            "status": "started",
        },
    )

    if getattr(settings, "embedding_provider", "openai") == "sentence_transformers":
        provider = SentenceTransformerEmbeddingProvider()

    else:
        provider = OpenAIEmbeddingProvider()

    logger.info(
        "Embedding provider selected",
        extra={
            "event": "embedding_provider_selected",
            "operation": "get_embedding_provider",
            "status": "success",
            "provider": type(provider).__name__,
            "model": provider.model_name(),
        },
    )

    return provider
