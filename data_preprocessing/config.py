"""Path and pipeline configuration for data preprocessing.

Paths are resolved relative to this package directory (or overridden via CLI /
environment variables). Absolute local filesystem paths are never required.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT: Path = Path(__file__).resolve().parent

DEFAULT_RAW_DIR: Path = PACKAGE_ROOT / "raw_data"
DEFAULT_PROCESSED_DIR: Path = PACKAGE_ROOT / "processed_data"
DEFAULT_INPUT_FILENAME: str = "reviews.csv"
DEFAULT_OUTPUT_FILENAME: str = "reviews_processed.csv"

# Raw / processed column names
COL_STORE_NAME: str = "store_name"
COL_STARS: str = "stars"
COL_REVIEW: str = "review"
COL_SATISFACTION: str = "satisfaction"

REQUIRED_RAW_COLUMNS: tuple[str, ...] = (
    COL_STORE_NAME,
    COL_STARS,
    COL_REVIEW,
)

REQUIRED_OUTPUT_COLUMNS: tuple[str, ...] = (
    COL_STORE_NAME,
    COL_STARS,
    COL_REVIEW,
    COL_SATISFACTION,
)

POSITIVE_LABEL: str = "positive"
NEGATIVE_LABEL: str = "negative"
SATISFACTION_THRESHOLD: int = 4

# Journey classification (multi-label)
JOURNEY_CLASSES: tuple[str, ...] = (
    "pre_visit",
    "sales",
    "contract",
    "after_sales",
)
JOURNEY_DIR: Path = PACKAGE_ROOT / "journey_classification"
JOURNEY_MODEL_DIR: Path = JOURNEY_DIR / "model"
JOURNEY_MODEL_WEIGHTS: Path = JOURNEY_MODEL_DIR / "best_bilstm_model.pt"
JOURNEY_MODEL_CONFIG: Path = JOURNEY_MODEL_DIR / "model_config.json"
JOURNEY_MERGE_CSV: Path = JOURNEY_DIR / "reviews_with_journey_preds.csv"
JOURNEY_LABELS_CSV: Path = (
    JOURNEY_DIR / "reviews_manual_label_sample_800_labeled_fixed.csv"
)
JOURNEY_PRED_COLUMNS: tuple[str, ...] = tuple(
    col
    for name in JOURNEY_CLASSES
    for col in (f"{name}_prob", f"{name}_pred")
)

# Topic modeling (BERTopic per journey × satisfaction)
TOPIC_DIR: Path = PACKAGE_ROOT / "topic_modeling"
TOPIC_OUTPUT_DIR: Path = TOPIC_DIR / "output"
TOPIC_OUTPUT_JSON: Path = TOPIC_OUTPUT_DIR / "topics_by_journey.json"
DEFAULT_TOPIC_EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
DEFAULT_GEMINI_MODEL: str = "gemini-2.0-flash"
DEFAULT_TOPIC_MAX_PER_JOURNEY: int = 10  # at least 10 topics per journey×satisfaction
DEFAULT_TOPIC_SAMPLES_PER_TOPIC: int = 5


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for a single pipeline run."""

    input_csv: Path
    output_csv: Path
    run_topics: bool = False

    @classmethod
    def from_sources(
        cls,
        input_csv: str | Path | None = None,
        output_csv: str | Path | None = None,
        run_topics: bool = False,
    ) -> PipelineConfig:
        """Build config from CLI args, then env vars, then package defaults.

        Environment variables:
            REVIEW_RAW_CSV: path to the raw reviews CSV
            REVIEW_PROCESSED_CSV: path for the processed output CSV
        """
        resolved_input = Path(
            input_csv
            or os.environ.get("REVIEW_RAW_CSV")
            or (DEFAULT_RAW_DIR / DEFAULT_INPUT_FILENAME)
        )
        resolved_output = Path(
            output_csv
            or os.environ.get("REVIEW_PROCESSED_CSV")
            or (DEFAULT_PROCESSED_DIR / DEFAULT_OUTPUT_FILENAME)
        )
        if not resolved_input.is_absolute():
            resolved_input = (Path.cwd() / resolved_input).resolve()
        else:
            resolved_input = resolved_input.resolve()
        if not resolved_output.is_absolute():
            resolved_output = (Path.cwd() / resolved_output).resolve()
        else:
            resolved_output = resolved_output.resolve()
        return cls(
            input_csv=resolved_input,
            output_csv=resolved_output,
            run_topics=run_topics,
        )
