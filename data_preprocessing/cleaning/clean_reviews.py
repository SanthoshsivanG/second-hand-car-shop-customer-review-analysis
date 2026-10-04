"""Clean review text; keep store_name, stars, review."""

from __future__ import annotations

import logging
import re

import pandas as pd

from config import COL_REVIEW, REQUIRED_RAW_COLUMNS

logger = logging.getLogger(__name__)

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
_UNWANTED_CHARS_PATTERN = re.compile(r"[^a-zA-Z0-9\s.,!?;:'\"()\-/%&]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


class MissingRawColumnsError(ValueError):
    """Raised when raw input is missing columns required for cleaning."""


def validate_raw_columns(df: pd.DataFrame) -> None:
    """Fail early if columns needed for cleaning/labeling are absent."""
    missing = [col for col in REQUIRED_RAW_COLUMNS if col not in df.columns]
    if missing:
        raise MissingRawColumnsError(
            "Raw CSV is missing required columns: "
            f"{missing}. Present columns: {list(df.columns)}. "
            f"Expected exactly these required columns: {list(REQUIRED_RAW_COLUMNS)}"
        )


def clean_review_text(text: object) -> str | None:
    """Clean a single review string. Returns None if empty after cleaning."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    if not isinstance(text, str):
        text = str(text)

    cleaned = text.strip()
    if not cleaned:
        return None

    cleaned = _EMOJI_PATTERN.sub(" ", cleaned)
    cleaned = _UNWANTED_CHARS_PATTERN.sub(" ", cleaned)
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned or None


def clean_reviews_stage(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Run the cleaning stage.

    Returns:
        Cleaned DataFrame and count of rows removed for empty reviews.
    """
    validate_raw_columns(df)
    working = df.loc[:, list(REQUIRED_RAW_COLUMNS)].copy()
    input_count = len(working)

    working[COL_REVIEW] = working[COL_REVIEW].map(clean_review_text)
    empty_mask = working[COL_REVIEW].isna()
    empty_removed = int(empty_mask.sum())
    working = working.loc[~empty_mask].copy().reset_index(drop=True)

    logger.info(
        "Removed %s rows with empty/null/whitespace-only reviews "
        "(from %s rows entering cleaning)",
        empty_removed,
        input_count,
    )
    if working.empty:
        logger.warning("No rows remain after review cleaning.")
    return working, empty_removed
