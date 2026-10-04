"""Rating-based satisfaction labels (not NLP sentiment)."""

from __future__ import annotations

import logging

import pandas as pd

from config import (
    COL_REVIEW,
    COL_SATISFACTION,
    COL_STARS,
    COL_STORE_NAME,
    NEGATIVE_LABEL,
    POSITIVE_LABEL,
    SATISFACTION_THRESHOLD,
)

logger = logging.getLogger(__name__)


def stars_to_satisfaction(stars: object) -> str:
    """Map star rating to satisfaction: <4 negative, >=4 positive."""
    value = float(stars)
    if value < SATISFACTION_THRESHOLD:
        return NEGATIVE_LABEL
    return POSITIVE_LABEL


def apply_satisfaction_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Add rating-based satisfaction; keep store_name, stars, review."""
    labeled = pd.DataFrame(
        {
            COL_STORE_NAME: df[COL_STORE_NAME],
            COL_STARS: df[COL_STARS],
            COL_REVIEW: df[COL_REVIEW],
            COL_SATISFACTION: df[COL_STARS].map(stars_to_satisfaction),
        }
    ).reset_index(drop=True)
    logger.info(
        "Applied rating-based satisfaction labels to %s rows "
        "(threshold=%s; not NLP sentiment)",
        len(labeled),
        SATISFACTION_THRESHOLD,
    )
    return labeled
