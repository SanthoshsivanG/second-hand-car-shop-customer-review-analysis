"""Runtime paths and shared constants."""

from __future__ import annotations

import os
from pathlib import Path


def _default_data_paths() -> tuple[Path, Path]:
    """Resolve local repo defaults; Docker uses /data mounts (or env overrides)."""
    parents = Path(__file__).resolve().parents
    # Local: <repo>/app/backend/config.py -> parents[2] is repo root.
    # Container: /app/config.py has no parents[2].
    if len(parents) > 2:
        root = parents[2]
        return (
            root / "data_preprocessing" / "processed_data" / "reviews_processed.csv",
            root
            / "data_preprocessing"
            / "topic_modeling"
            / "output"
            / "topics_by_journey.json",
        )
    return (
        Path("/data/processed/reviews_processed.csv"),
        Path("/data/topics/topics_by_journey.json"),
    )


_DEFAULT_CSV, _DEFAULT_TOPICS = _default_data_paths()

REVIEWS_CSV = Path(os.getenv("REVIEWS_CSV", str(_DEFAULT_CSV)))
TOPICS_JSON = Path(os.getenv("TOPICS_JSON", str(_DEFAULT_TOPICS)))

JOURNEYS = ("pre_visit", "sales", "contract", "after_sales")
JOURNEY_LABELS = {
    "pre_visit": "Pre-visit",
    "sales": "Sales",
    "contract": "Contract",
    "after_sales": "After-sales",
}
SENTIMENTS = ("positive", "negative")
PRED_COL = {j: f"{j}_pred" for j in JOURNEYS}

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "her",
        "his",
        "i",
        "in",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "she",
        "so",
        "that",
        "the",
        "their",
        "them",
        "they",
        "this",
        "to",
        "was",
        "we",
        "were",
        "with",
        "you",
        "your",
        "very",
        "car",  # too common in this corpus to be distinctive
    }
)
