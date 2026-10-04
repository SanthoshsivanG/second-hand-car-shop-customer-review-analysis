"""Orchestrate preprocessing stages in folder order.

Flow:
    raw_data → cleaning → labeling → journey_classification
    → validation → processed_data → (optional) topic_modeling
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from cleaning.clean_reviews import MissingRawColumnsError, clean_reviews_stage
from config import PipelineConfig
from journey_classification.classify import (
    JourneyClassificationError,
    apply_journey_classification,
)
from labeling.satisfaction import apply_satisfaction_labels
from topic_modeling.bertopic_topics import TopicModelingError, run_topic_modeling
from validation.validate import (
    OutputFormatError,
    PipelineMetrics,
    validate_processed_stage,
)

logger = logging.getLogger(__name__)

__all__ = [
    "MissingRawColumnsError",
    "JourneyClassificationError",
    "TopicModelingError",
    "OutputFormatError",
    "PipelineMetrics",
    "run_pipeline",
]


def load_raw_reviews(input_csv: Path) -> pd.DataFrame:
    """Load the raw reviews CSV from raw_data (or configured path)."""
    if not input_csv.exists():
        raise FileNotFoundError(
            f"Raw CSV not found: {input_csv}. "
            "Place reviews.csv under data_preprocessing/raw_data/ "
            "or pass --input / set REVIEW_RAW_CSV."
        )
    logger.info("Loading raw reviews from %s", input_csv)
    return pd.read_csv(input_csv)


def save_processed_reviews(df: pd.DataFrame, output_csv: Path) -> None:
    """Write the validated dataset to processed_data (or configured path)."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info("Wrote processed reviews to %s (%s rows)", output_csv, len(df))


def run_pipeline(config: PipelineConfig) -> PipelineMetrics:
    """Execute stages in order through journey classification."""
    raw = load_raw_reviews(config.input_csv)
    input_row_count = len(raw)

    # 1) cleaning/
    cleaned, empty_removed = clean_reviews_stage(raw)

    # 2) labeling/
    labeled = apply_satisfaction_labels(cleaned)

    # 3) journey_classification/
    with_journey = apply_journey_classification(labeled)

    # 4) validation/
    metrics = validate_processed_stage(
        with_journey,
        input_row_count=input_row_count,
        empty_review_removed_count=empty_removed,
    )

    # 5) processed_data/
    save_processed_reviews(with_journey, config.output_csv)

    # 6) topic_modeling/ (optional — BERTopic + Gemini naming)
    if config.run_topics:
        logger.info("Running topic modeling (BERTopic per journey)...")
        run_topic_modeling(with_journey)

    return metrics
