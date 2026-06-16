from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

from ai_ticket_platform.app.utils.errors import AppError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class RetrievalEvaluationResult:
    """Retrieval quality evaluation result."""

    query: str
    expected_document_ids: list[str]
    retrieved_document_ids: list[str]
    precision_at_k: float
    recall_at_k: float
    hit_rate: float


@dataclass(frozen=True)
class ClassificationEvaluationResult:
    """Classification quality evaluation result."""

    text: str
    expected_department: str
    predicted_department: str
    confidence: float | None
    is_correct: bool


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregated evaluation metrics."""

    metric_name: str
    sample_count: int
    metrics: dict[str, float]


class EvaluationError(AppError):
    """Raised when AI evaluation fails."""

    default_error_code = "evaluation_error"


def evaluate_retrieval_result(
    *,
    query: str,
    expected_document_ids: list[str],
    retrieved_document_ids: list[str],
    top_k: int,
) -> RetrievalEvaluationResult:
    """Evaluate one retrieval result."""
    logger.info(
        "Retrieval evaluation started",
        extra={
            "event": "retrieval_evaluation_started",
            "operation": "evaluate_retrieval_result",
            "status": "started",
            "top_k": top_k,
        },
    )

    try:
        _validate_query(query)
        _validate_top_k(top_k)

        expected = set(_normalize_ids(expected_document_ids))
        retrieved = _normalize_ids(retrieved_document_ids)[:top_k]
        retrieved_set = set(retrieved)

        if not expected:
            raise EvaluationError("expected_document_ids must not be empty")

        true_positives = len(expected.intersection(retrieved_set))

        precision_at_k = true_positives / max(len(retrieved), 1)
        recall_at_k = true_positives / len(expected)
        hit_rate = 1.0 if true_positives > 0 else 0.0

        result = RetrievalEvaluationResult(
            query=query.strip(),
            expected_document_ids=list(expected),
            retrieved_document_ids=retrieved,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            hit_rate=hit_rate,
        )

        logger.info(
            "Retrieval evaluation completed",
            extra={
                "event": "retrieval_evaluation_completed",
                "operation": "evaluate_retrieval_result",
                "status": "success",
                "top_k": top_k,
                "score": precision_at_k,
                "precision_at_k": precision_at_k,
                "recall_at_k": recall_at_k,
                "hit_rate": hit_rate,
            },
        )

        return result

    except EvaluationError:
        raise

    except Exception as exc:
        logger.error(
            "Retrieval evaluation failed",
            extra={
                "event": "retrieval_evaluation_failed",
                "operation": "evaluate_retrieval_result",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        raise EvaluationError("Failed to evaluate retrieval result") from exc


def summarize_retrieval_evaluations(
    results: list[RetrievalEvaluationResult],
) -> EvaluationSummary:
    """Summarize retrieval evaluation results."""
    logger.info(
        "Retrieval evaluation summary started",
        extra={
            "event": "retrieval_evaluation_summary_started",
            "operation": "summarize_retrieval_evaluations",
            "status": "started",
            "sample_count": len(results),
        },
    )

    if not results:
        raise EvaluationError("retrieval evaluation results must not be empty")

    summary = EvaluationSummary(
        metric_name="retrieval",
        sample_count=len(results),
        metrics={
            "precision_at_k": mean(item.precision_at_k for item in results),
            "recall_at_k": mean(item.recall_at_k for item in results),
            "hit_rate": mean(item.hit_rate for item in results),
        },
    )

    logger.info(
        "Retrieval evaluation summary completed",
        extra={
            "event": "retrieval_evaluation_summary_completed",
            "operation": "summarize_retrieval_evaluations",
            "status": "success",
            "sample_count": summary.sample_count,
            **summary.metrics,
        },
    )

    return summary


def evaluate_classification_result(
    *,
    text: str,
    expected_department: str,
    predicted_department: str,
    confidence: float | None = None,
) -> ClassificationEvaluationResult:
    """Evaluate one classification prediction."""
    logger.info(
        "Classification evaluation started",
        extra={
            "event": "classification_evaluation_started",
            "operation": "evaluate_classification_result",
            "status": "started",
            "expected_department": expected_department,
            "predicted_department": predicted_department,
        },
    )

    try:
        _validate_query(text)

        expected = _normalize_department(expected_department)
        predicted = _normalize_department(predicted_department)

        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise EvaluationError("confidence must be between 0 and 1")

        is_correct = expected == predicted

        result = ClassificationEvaluationResult(
            text=text.strip(),
            expected_department=expected,
            predicted_department=predicted,
            confidence=confidence,
            is_correct=is_correct,
        )

        logger.info(
            "Classification evaluation completed",
            extra={
                "event": "classification_evaluation_completed",
                "operation": "evaluate_classification_result",
                "status": "success",
                "expected_department": expected,
                "predicted_department": predicted,
                "confidence": confidence,
                "is_correct": is_correct,
            },
        )

        return result

    except EvaluationError:
        raise

    except Exception as exc:
        logger.error(
            "Classification evaluation failed",
            extra={
                "event": "classification_evaluation_failed",
                "operation": "evaluate_classification_result",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        raise EvaluationError("Failed to evaluate classification result") from exc


def summarize_classification_evaluations(
    results: list[ClassificationEvaluationResult],
) -> EvaluationSummary:
    """Summarize classification evaluation results."""
    logger.info(
        "Classification evaluation summary started",
        extra={
            "event": "classification_evaluation_summary_started",
            "operation": "summarize_classification_evaluations",
            "status": "started",
            "sample_count": len(results),
        },
    )

    if not results:
        raise EvaluationError("classification evaluation results must not be empty")

    correct_count = sum(1 for item in results if item.is_correct)
    accuracy = correct_count / len(results)

    confidence_values = [
        item.confidence for item in results if item.confidence is not None
    ]

    metrics: dict[str, float] = {
        "accuracy": accuracy,
        "correct_count": float(correct_count),
    }

    if confidence_values:
        metrics["average_confidence"] = mean(confidence_values)

    summary = EvaluationSummary(
        metric_name="classification",
        sample_count=len(results),
        metrics=metrics,
    )

    logger.info(
        "Classification evaluation summary completed",
        extra={
            "event": "classification_evaluation_summary_completed",
            "operation": "summarize_classification_evaluations",
            "status": "success",
            "sample_count": summary.sample_count,
            **summary.metrics,
        },
    )

    return summary


def evaluate_answer_grounding(
    *,
    answer: str,
    contexts: list[str],
) -> float:
    """Estimate whether answer is grounded in retrieved context."""
    logger.info(
        "Answer grounding evaluation started",
        extra={
            "event": "answer_grounding_evaluation_started",
            "operation": "evaluate_answer_grounding",
            "status": "started",
            "context_count": len(contexts),
        },
    )

    try:
        _validate_query(answer)

        normalized_contexts = [
            context.strip().lower()
            for context in contexts
            if isinstance(context, str) and context.strip()
        ]

        if not normalized_contexts:
            raise EvaluationError("contexts must not be empty")

        answer_terms = {
            token
            for token in answer.lower().split()
            if len(token) >= 4
        }

        context_text = " ".join(normalized_contexts)

        if not answer_terms:
            raise EvaluationError("answer does not contain enough terms to evaluate")

        matched_terms = {
            token for token in answer_terms if token in context_text
        }

        score = len(matched_terms) / len(answer_terms)

        logger.info(
            "Answer grounding evaluation completed",
            extra={
                "event": "answer_grounding_evaluation_completed",
                "operation": "evaluate_answer_grounding",
                "status": "success",
                "score": score,
                "context_count": len(normalized_contexts),
            },
        )

        return score

    except EvaluationError:
        raise

    except Exception as exc:
        logger.error(
            "Answer grounding evaluation failed",
            extra={
                "event": "answer_grounding_evaluation_failed",
                "operation": "evaluate_answer_grounding",
                "status": "failed",
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        raise EvaluationError("Failed to evaluate answer grounding") from exc


def _validate_query(value: str) -> None:
    """Validate non-empty text value."""
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError("text value must not be empty")


def _validate_top_k(top_k: int) -> None:
    """Validate top-k value."""
    if top_k < 1:
        raise EvaluationError("top_k must be greater than zero")

    if top_k > 100:
        raise EvaluationError("top_k must not exceed 100")


def _normalize_ids(values: list[str]) -> list[str]:
    """Normalize identifier list."""
    if not values:
        return []

    normalized: list[str] = []

    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue

        normalized.append(value.strip())

    return normalized


def _normalize_department(value: str) -> str:
    """Normalize department name."""
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError("department must not be empty")

    return value.strip().lower()
