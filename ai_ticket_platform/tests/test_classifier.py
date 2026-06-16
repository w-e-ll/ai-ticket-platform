from __future__ import annotations

import pytest

from ai_ticket_platform.app.services.classifier_service import (
    ClassificationResult,
    ClassifierService,
)
from ai_ticket_platform.app.utils.errors import ClassificationError


def test_classifier_fallback_routes_it_ticket() -> None:
    """Classify IT issue when ML model is unavailable."""
    classifier = ClassifierService()
    classifier.model = None

    result = classifier.classify(
        "My laptop cannot connect to VPN and Outlook email is not working."
    )

    assert isinstance(result, ClassificationResult)
    assert result.department == "it"
    assert result.confidence is not None
    assert 0.0 <= result.confidence <= 1.0


def test_classifier_fallback_routes_hr_ticket() -> None:
    """Classify HR issue when ML model is unavailable."""
    classifier = ClassifierService()
    classifier.model = None

    result = classifier.classify(
        "I need help with vacation leave and salary benefits."
    )

    assert result.department == "hr"
    assert result.confidence is not None
    assert 0.0 <= result.confidence <= 1.0


def test_classifier_fallback_routes_transportation_ticket() -> None:
    """Classify transportation issue when ML model is unavailable."""
    classifier = ClassifierService()
    classifier.model = None

    result = classifier.classify(
        "The bus driver was rude and the route was delayed."
    )

    assert result.department == "transportation"
    assert result.confidence is not None
    assert 0.0 <= result.confidence <= 1.0


def test_classifier_rejects_empty_text() -> None:
    """Reject empty classification input."""
    classifier = ClassifierService()
    classifier.model = None

    with pytest.raises(ClassificationError):
        classifier.classify("   ")


def test_classifier_rejects_non_string_text() -> None:
    """Reject non-string classification input."""
    classifier = ClassifierService()
    classifier.model = None

    with pytest.raises(ClassificationError):
        classifier.classify(None)  # type: ignore[arg-type]


def test_classifier_rejects_too_long_text() -> None:
    """Reject overlong classification input."""
    classifier = ClassifierService()
    classifier.model = None

    with pytest.raises(ClassificationError):
        classifier.classify("x" * 10001)


def test_training_validation_requires_samples() -> None:
    """Reject empty training dataset."""
    classifier = ClassifierService()

    with pytest.raises(ClassificationError):
        classifier.train(texts=[], departments=[])


def test_training_validation_requires_matching_lengths() -> None:
    """Reject training data with mismatched lengths."""
    classifier = ClassifierService()

    with pytest.raises(ClassificationError):
        classifier.train(
            texts=["VPN issue", "Salary issue"],
            departments=["it"],
        )


def test_training_validation_requires_two_departments() -> None:
    """Reject single-class training dataset."""
    classifier = ClassifierService()

    with pytest.raises(ClassificationError):
        classifier.train(
            texts=[
                "VPN issue one",
                "VPN issue two",
                "VPN issue three",
                "VPN issue four",
                "VPN issue five",
                "VPN issue six",
            ],
            departments=[
                "it",
                "it",
                "it",
                "it",
                "it",
                "it",
            ],
        )
