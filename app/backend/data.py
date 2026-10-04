"""Load reviews CSV and topics JSON once at startup."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import pandas as pd

from config import JOURNEYS, PRED_COL, REVIEWS_CSV, STOPWORDS, TOPICS_JSON

_WORD_RE = re.compile(r"[a-z0-9']+")
_VALID_SAT = frozenset({"positive", "negative"})


def distinctive_keywords(keywords: list[str], name: str = "") -> list[str]:
    """Keep non-stopword tokens from keywords + topic name."""
    tokens: list[str] = []
    for raw in list(keywords) + name.lower().split():
        for tok in _WORD_RE.findall(raw.lower()):
            if tok not in STOPWORDS and tok not in tokens:
                tokens.append(tok)
    return tokens


@dataclass
class TopicInfo:
    topic_id: int
    name: str
    keywords: list[str]
    distinctive: list[str]
    document_count: int
    journey: str
    satisfaction: str | None = None  # positive | negative | None (legacy JSON)


@dataclass
class AppData:
    df: pd.DataFrame
    topics_by_journey: dict[str, list[TopicInfo]] = field(default_factory=dict)
    topics_by_name: dict[str, list[TopicInfo]] = field(default_factory=dict)


def _iter_topic_records(payload: dict) -> list[dict]:
    """Support new journey×satisfaction JSON and legacy flat topics list."""
    by_sat = payload.get("by_satisfaction")
    if isinstance(by_sat, dict):
        records: list[dict] = []
        for sat, block in by_sat.items():
            sat_norm = str(sat).lower()
            for t in (block or {}).get("topics", []):
                row = dict(t)
                row.setdefault("satisfaction", sat_norm)
                records.append(row)
        return records
    return list(payload.get("topics") or [])


def load_data() -> AppData:
    df = pd.read_csv(REVIEWS_CSV)
    for col in PRED_COL.values():
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["review"] = df["review"].fillna("").astype(str)
    df["store_name"] = df["store_name"].fillna("").astype(str)
    df["satisfaction"] = df["satisfaction"].fillna("").astype(str)
    df["_review_lc"] = df["review"].str.lower()

    with open(TOPICS_JSON, encoding="utf-8") as f:
        raw = json.load(f)

    topics_by_journey: dict[str, list[TopicInfo]] = {j: [] for j in JOURNEYS}
    topics_by_name: dict[str, list[TopicInfo]] = {}

    for journey, payload in raw.get("journeys", {}).items():
        if journey not in JOURNEYS:
            continue
        for t in _iter_topic_records(payload):
            sat_raw = t.get("satisfaction")
            sat = str(sat_raw).lower() if sat_raw else None
            if sat is not None and sat not in _VALID_SAT:
                sat = None
            info = TopicInfo(
                topic_id=int(t["topic_id"]),
                name=str(t["name"]),
                keywords=list(t.get("keywords") or []),
                distinctive=distinctive_keywords(
                    list(t.get("keywords") or []), str(t["name"])
                ),
                document_count=int(t.get("document_count") or 0),
                journey=journey,
                satisfaction=sat,
            )
            topics_by_journey[journey].append(info)
            topics_by_name.setdefault(info.name, []).append(info)

    return AppData(df=df, topics_by_journey=topics_by_journey, topics_by_name=topics_by_name)
