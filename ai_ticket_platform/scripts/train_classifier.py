from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from ai_ticket_platform.app.services.classifier_service import (
    ClassifierService,
)
from ai_ticket_platform.app.utils.errors import ClassificationError
from ai_ticket_platform.app.utils.logging import (
    get_logger,
    setup_logging,
)


logger = get_logger(__name__)


REQUIRED_COLUMNS = {
    "text",
    "department",
}


def load_training_dataset(
    csv_path: Path,
) -> tuple[list[str], list[str]]:
    """Load labeled ticket dataset from CSV."""
    logger.info(
        "Training dataset loading started",
        extra={
            "event": "training_dataset_loading_started",
            "operation": "load_training_dataset",
            "status": "started",
            "csv_path": str(csv_path),
        },
    )

    if not csv_path.exists():
        raise FileNotFoundError(f"dataset file does not exist: {csv_path}")

    if not csv_path.is_file():
        raise ClassificationError("dataset path must be a file")

    texts: list[str] = []
    departments: list[str] = []

    try:
        with csv_path.open(
            mode="r",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise ClassificationError(
                    "dataset CSV does not contain headers"
                )

            normalized_headers = {
                header.strip().lower()
                for header in reader.fieldnames
                if header
            }

            missing_columns = REQUIRED_COLUMNS - normalized_headers

            if missing_columns:
                raise ClassificationError(
                    "dataset CSV is missing required columns",
                    details={
                        "missing_columns": sorted(missing_columns),
                    },
                )

            for row_index, row in enumerate(reader, start=1):
                text = (row.get("text") or "").strip()
                department = (row.get("department") or "").strip().lower()

                if not text:
                    logger.warning(
                        "Skipping empty training text row",
                        extra={
                            "event": "training_dataset_row_skipped",
                            "operation": "load_training_dataset",
                            "status": "warning",
                            "row_index": row_index,
                        },
                    )
                    continue

                if not department:
                    logger.warning(
                        "Skipping empty department row",
                        extra={
                            "event": "training_dataset_row_skipped",
                            "operation": "load_training_dataset",
                            "status": "warning",
                            "row_index": row_index,
                        },
                    )
                    continue

                texts.append(text)
                departments.append(department)

        if not texts:
            raise ClassificationError(
                "training dataset does not contain valid rows"
            )

        logger.info(
            "Training dataset loading completed",
            extra={
                "event": "training_dataset_loading_completed",
                "operation": "load_training_dataset",
                "status": "success",
                "csv_path": str(csv_path),
                "sample_count": len(texts),
                "department_count": len(set(departments)),
            },
        )

        return texts, departments

    except ClassificationError:
        raise

    except Exception as exc:
        logger.error(
            "Training dataset loading failed",
            extra={
                "event": "training_dataset_loading_failed",
                "operation": "load_training_dataset",
                "status": "failed",
                "csv_path": str(csv_path),
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )

        raise ClassificationError(
            "Failed to load training dataset"
        ) from exc


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Train AI Ticket Platform classifier.",
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to training CSV dataset.",
    )

    parser.add_argument(
        "--save-model",
        action="store_true",
        default=False,
        help="Persist trained model to disk.",
    )

    return parser.parse_args()


async def main() -> None:
    """Run classifier training script."""
    setup_logging()

    args = parse_args()

    dataset_path = Path(args.dataset).resolve()

    logger.info(
        "Classifier training script started",
        extra={
            "event": "classifier_training_script_started",
            "operation": "train_classifier_main",
            "status": "started",
            "dataset_path": str(dataset_path),
            "save_model": args.save_model,
        },
    )

    texts, departments = load_training_dataset(dataset_path)

    classifier_service = ClassifierService()

    accuracy = classifier_service.train(
        texts=texts,
        departments=departments,
        save_model=args.save_model,
    )

    logger.info(
        "Classifier training script completed",
        extra={
            "event": "classifier_training_script_completed",
            "operation": "train_classifier_main",
            "status": "success",
            "dataset_path": str(dataset_path),
            "accuracy": accuracy,
            "sample_count": len(texts),
        },
    )

    print()
    print("Classifier training completed successfully.")
    print()
    print(f"Dataset: {dataset_path}")
    print(f"Samples: {len(texts)}")
    print(f"Departments: {len(set(departments))}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Model Saved: {args.save_model}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
