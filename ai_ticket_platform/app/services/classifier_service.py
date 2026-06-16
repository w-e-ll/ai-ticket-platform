from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from ai_ticket_platform.app.ai.embeddings import get_embedding_provider
from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.utils.errors import ClassificationError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class ClassificationResult:
    """Ticket classification prediction result."""

    department: str
    confidence: float | None
    probabilities: dict[str, float] | None


class ClassifierService:
    """Service for ML-based ticket department classification."""

    fallback_departments = {
        "hr": ("salary", "vacation", "leave", "harassment", "benefits", "contract"),
        "it": ("laptop", "password", "network", "vpn", "email", "outlook", "disk"),
        "transportation": ("driver", "route", "bus", "fare", "vehicle", "passenger"),
        "finance": ("invoice", "payment", "expense", "reimbursement", "budget"),
        "legal": ("law", "contract", "compliance", "policy", "claim"),
        "security": ("breach", "access", "threat", "incident", "suspicious"),
    }

    def __init__(self, *, model_path: Path | None = None) -> None:
        """Initialize classifier service."""
        self.settings = get_settings()
        self.embedding_provider = get_embedding_provider()
        self.model_path = model_path or self.settings.classifier_model_path
        self.model = self._load_model_if_exists()

        logger.info(
            "Classifier service initialized",
            extra={
                "event": "classifier_service_initialized",
                "operation": "classifier_service_init",
                "status": "success",
                "model_path": str(self.model_path),
                "model_loaded": self.model is not None,
                "embedding_model": self.embedding_provider.model_name(),
            },
        )

    def classify(self, text: str) -> ClassificationResult:
        """Classify ticket text into a department."""
        normalized_text = self._validate_text(text)

        logger.info(
            "Ticket classification started",
            extra={
                "event": "ticket_classification_started",
                "operation": "classify_ticket",
                "status": "started",
                "text_length": len(normalized_text),
                "model_loaded": self.model is not None,
            },
        )

        try:
            if self.model is None:
                logger.warning(
                    "Classifier model missing; using keyword fallback",
                    extra={
                        "event": "classifier_model_missing",
                        "operation": "classify_ticket",
                        "status": "warning",
                    },
                )
                return self._classify_with_fallback(normalized_text)

            embedding = self.embedding_provider.embed_text(normalized_text)
            features = np.array([embedding], dtype=float)

            predicted_department = str(self.model.predict(features)[0])
            probabilities = self._predict_probabilities(features)
            confidence = (
                probabilities.get(predicted_department)
                if probabilities is not None
                else None
            )

            result = ClassificationResult(
                department=predicted_department.lower(),
                confidence=confidence,
                probabilities=probabilities,
            )

            logger.info(
                "Ticket classification completed",
                extra={
                    "event": "ticket_classification_completed",
                    "operation": "classify_ticket",
                    "status": "success",
                    "department": result.department,
                    "confidence": result.confidence,
                },
            )

            return result

        except ClassificationError:
            raise

        except Exception as exc:
            logger.error(
                "Ticket classification failed",
                extra={
                    "event": "ticket_classification_failed",
                    "operation": "classify_ticket",
                    "status": "failed",
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise ClassificationError("Failed to classify ticket") from exc

    def train(
        self,
        *,
        texts: list[str],
        departments: list[str],
        save_model: bool = True,
    ) -> float:
        """Train classifier from labeled ticket examples."""
        logger.info(
            "Classifier training started",
            extra={
                "event": "classifier_training_started",
                "operation": "train_classifier",
                "status": "started",
                "sample_count": len(texts),
                "save_model": save_model,
            },
        )

        try:
            self._validate_training_data(texts, departments)

            normalized_texts = [self._validate_text(text) for text in texts]
            normalized_departments = [
                self._normalize_department(department)
                for department in departments
            ]

            embeddings = self.embedding_provider.embed_texts(normalized_texts)
            features = np.array(embeddings, dtype=float)

            model = LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
            )

            model.fit(features, normalized_departments)

            accuracy = float(model.score(features, normalized_departments))
            self.model = model

            if save_model:
                self.save_model()

            logger.info(
                "Classifier training completed",
                extra={
                    "event": "classifier_training_completed",
                    "operation": "train_classifier",
                    "status": "success",
                    "sample_count": len(texts),
                    "accuracy": accuracy,
                    "department_count": len(set(normalized_departments)),
                },
            )

            return accuracy

        except ClassificationError:
            raise

        except Exception as exc:
            logger.error(
                "Classifier training failed",
                extra={
                    "event": "classifier_training_failed",
                    "operation": "train_classifier",
                    "status": "failed",
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise ClassificationError("Failed to train classifier") from exc

    def save_model(self) -> None:
        """Persist classifier model to disk."""
        if self.model is None:
            raise ClassificationError("cannot save empty classifier model")

        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, self.model_path)

            logger.info(
                "Classifier model saved",
                extra={
                    "event": "classifier_model_saved",
                    "operation": "save_classifier_model",
                    "status": "success",
                    "model_path": str(self.model_path),
                },
            )

        except Exception as exc:
            logger.error(
                "Classifier model save failed",
                extra={
                    "event": "classifier_model_save_failed",
                    "operation": "save_classifier_model",
                    "status": "failed",
                    "model_path": str(self.model_path),
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise ClassificationError("Failed to save classifier model") from exc

    def _load_model_if_exists(self):
        """Load classifier model if model file exists."""
        if not self.model_path.exists():
            logger.warning(
                "Classifier model file not found",
                extra={
                    "event": "classifier_model_file_not_found",
                    "operation": "load_classifier_model",
                    "status": "warning",
                    "model_path": str(self.model_path),
                },
            )
            return None

        try:
            model = joblib.load(self.model_path)

            logger.info(
                "Classifier model loaded",
                extra={
                    "event": "classifier_model_loaded",
                    "operation": "load_classifier_model",
                    "status": "success",
                    "model_path": str(self.model_path),
                },
            )

            return model

        except Exception as exc:
            logger.error(
                "Classifier model load failed",
                extra={
                    "event": "classifier_model_load_failed",
                    "operation": "load_classifier_model",
                    "status": "failed",
                    "model_path": str(self.model_path),
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise ClassificationError("Failed to load classifier model") from exc

    def _predict_probabilities(
        self,
        features: np.ndarray,
    ) -> dict[str, float] | None:
        """Predict class probabilities when model supports them."""
        if self.model is None or not hasattr(self.model, "predict_proba"):
            return None

        probabilities = self.model.predict_proba(features)[0]
        classes = self.model.classes_

        return {
            str(label).lower(): float(probability)
            for label, probability in zip(classes, probabilities, strict=True)
        }

    def _classify_with_fallback(self, text: str) -> ClassificationResult:
        """Classify ticket using keyword fallback rules."""
        lowered = text.lower()
        scores: dict[str, int] = {}

        for department, keywords in self.fallback_departments.items():
            scores[department] = sum(
                1 for keyword in keywords if keyword in lowered
            )

        best_department = max(scores, key=scores.get)
        best_score = scores[best_department]
        total_score = sum(scores.values())

        confidence = (
            best_score / total_score
            if total_score > 0
            else 0.25
        )

        if total_score == 0:
            best_department = "it"

        logger.info(
            "Keyword fallback classification completed",
            extra={
                "event": "keyword_fallback_classification_completed",
                "operation": "classify_ticket_fallback",
                "status": "success",
                "department": best_department,
                "confidence": confidence,
            },
        )

        return ClassificationResult(
            department=best_department,
            confidence=confidence,
            probabilities={
                department: (
                    score / total_score if total_score > 0 else 0.0
                )
                for department, score in scores.items()
            },
        )

    def _validate_text(self, text: str) -> str:
        """Validate and normalize classification text."""
        if not isinstance(text, str):
            raise ClassificationError("classification text must be a string")

        normalized = " ".join(text.strip().split())

        if not normalized:
            raise ClassificationError("classification text must not be empty")

        if len(normalized) > 10000:
            raise ClassificationError("classification text is too long")

        return normalized

    def _validate_training_data(
        self,
        texts: list[str],
        departments: list[str],
    ) -> None:
        """Validate training dataset."""
        if not texts:
            raise ClassificationError("training texts must not be empty")

        if not departments:
            raise ClassificationError("training departments must not be empty")

        if len(texts) != len(departments):
            raise ClassificationError(
                "training texts and departments must have the same length"
            )

        if len(texts) < 6:
            raise ClassificationError("at least 6 training samples are required")

        unique_departments = {
            self._normalize_department(department)
            for department in departments
        }

        if len(unique_departments) < 2:
            raise ClassificationError("at least 2 departments are required")

    def _normalize_department(self, department: str) -> str:
        """Normalize department value."""
        if not isinstance(department, str):
            raise ClassificationError("department must be a string")

        normalized = department.strip().lower()

        if not normalized:
            raise ClassificationError("department must not be empty")

        if len(normalized) > 100:
            raise ClassificationError("department is too long")

        return normalized
