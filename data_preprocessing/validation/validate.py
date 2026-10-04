"""Final validation of processed dataset format and summary metrics."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from config import (
    COL_REVIEW,
    COL_SATISFACTION,
    COL_STARS,
    COL_STORE_NAME,
    JOURNEY_CLASSES,
    JOURNEY_PRED_COLUMNS,
    NEGATIVE_LABEL,
    POSITIVE_LABEL,
    REQUIRED_OUTPUT_COLUMNS,
)

logger = logging.getLogger(__name__)

ALLOWED_SATISFACTION: frozenset[str] = frozenset(
    {POSITIVE_LABEL, NEGATIVE_LABEL}
)


class OutputFormatError(ValueError):
    """Raised when the processed dataset fails final format checks."""


@dataclass(frozen=True)
class PipelineMetrics:
    input_row_count: int
    empty_review_removed_count: int
    final_row_count: int
    positive_count: int
    negative_count: int
    unique_store_count: int

    def log(self) -> None:
        logger.info("Pipeline validation metrics")
        logger.info("  input_row_count: %s", self.input_row_count)
        logger.info(
            "  rows_removed_empty_review: %s", self.empty_review_removed_count
        )
        logger.info("  final_row_count: %s", self.final_row_count)
        logger.info("  positive_count: %s", self.positive_count)
        logger.info("  negative_count: %s", self.negative_count)
        logger.info("  unique_store_count: %s", self.unique_store_count)


def validate_output_format(df: pd.DataFrame) -> None:
    """Check required processed schema and value constraints."""
    missing = [c for c in REQUIRED_OUTPUT_COLUMNS if c not in df.columns]
    if missing:
        raise OutputFormatError(
            "Processed data missing required columns: "
            f"{missing}. Present: {list(df.columns)}. "
            f"Expected: {list(REQUIRED_OUTPUT_COLUMNS)}"
        )

    if df[COL_STARS].isna().any():
        raise OutputFormatError("Processed data has null values in 'stars'.")
    try:
        pd.to_numeric(df[COL_STARS], errors="raise")
    except (TypeError, ValueError) as exc:
        raise OutputFormatError(
            "Processed data 'stars' must be numeric."
        ) from exc

    reviews = df[COL_REVIEW]
    if reviews.isna().any() or (reviews.astype(str).str.strip() == "").any():
        raise OutputFormatError(
            "Processed data has empty or null values in 'review'."
        )

    invalid_labels = set(df[COL_SATISFACTION].unique()) - ALLOWED_SATISFACTION
    if invalid_labels:
        raise OutputFormatError(
            "Processed data has invalid satisfaction labels: "
            f"{sorted(invalid_labels)}. Allowed: {sorted(ALLOWED_SATISFACTION)}"
        )

    missing_journey = [c for c in JOURNEY_PRED_COLUMNS if c not in df.columns]
    if missing_journey:
        raise OutputFormatError(
            "Processed data missing journey columns: "
            f"{missing_journey}. Expected: {list(JOURNEY_PRED_COLUMNS)}"
        )
    for name in JOURNEY_CLASSES:
        pred_col = f"{name}_pred"
        prob_col = f"{name}_prob"
        pred_vals = set(df[pred_col].dropna().unique().tolist())
        if not pred_vals.issubset({0, 1, 0.0, 1.0}):
            raise OutputFormatError(
                f"Journey column '{pred_col}' must be 0/1. Found: {sorted(pred_vals)}"
            )
        if df[prob_col].isna().any():
            raise OutputFormatError(f"Journey column '{prob_col}' has nulls.")
        if ((df[prob_col] < 0) | (df[prob_col] > 1)).any():
            raise OutputFormatError(
                f"Journey column '{prob_col}' must be in [0, 1]."
            )


def compute_metrics(
    *,
    input_row_count: int,
    empty_review_removed_count: int,
    processed: pd.DataFrame,
) -> PipelineMetrics:
    """Compute summary metrics for the validated frame."""
    return PipelineMetrics(
        input_row_count=input_row_count,
        empty_review_removed_count=empty_review_removed_count,
        final_row_count=len(processed),
        positive_count=int(
            (processed[COL_SATISFACTION] == POSITIVE_LABEL).sum()
        ),
        negative_count=int(
            (processed[COL_SATISFACTION] == NEGATIVE_LABEL).sum()
        ),
        unique_store_count=int(processed[COL_STORE_NAME].nunique()),
    )


def validate_processed_stage(
    df: pd.DataFrame,
    *,
    input_row_count: int,
    empty_review_removed_count: int,
) -> PipelineMetrics:
    """Final stage: validate format, then return metrics."""
    validate_output_format(df)
    metrics = compute_metrics(
        input_row_count=input_row_count,
        empty_review_removed_count=empty_review_removed_count,
        processed=df,
    )
    metrics.log()
    for name in JOURNEY_CLASSES:
        logger.info(
            "  journey_%s_positive: %s",
            name,
            int(df[f"{name}_pred"].sum()),
        )
    logger.info("Final output format validation passed.")
    return metrics
