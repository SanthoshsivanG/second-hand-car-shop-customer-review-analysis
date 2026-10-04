"""Filter / heatmap / topic aggregation helpers."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from config import JOURNEYS, JOURNEY_LABELS, PRED_COL, SENTIMENTS
from data import AppData, TopicInfo


def _as_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        for part in str(v).split(","):
            part = part.strip()
            if part and part not in out:
                out.append(part)
    return out


def _review_hits_keywords(series: pd.Series, keywords: Iterable[str]) -> pd.Series:
    keys = [k for k in keywords if k]
    if not keys:
        return pd.Series(True, index=series.index)
    mask = pd.Series(False, index=series.index)
    for k in keys:
        mask = mask | series.str.contains(k, regex=False, na=False)
    return mask


def topic_matches_for_names(data: AppData, topic_names: list[str]) -> list[TopicInfo]:
    matched: list[TopicInfo] = []
    seen: set[tuple[str, int]] = set()
    for name in topic_names:
        for info in data.topics_by_name.get(name, []):
            key = (info.journey, info.topic_id)
            if key not in seen:
                seen.add(key)
                matched.append(info)
    return matched


def apply_filters(
    data: AppData,
    *,
    store_name: list[str] | None = None,
    satisfaction: list[str] | None = None,
    journey: list[str] | None = None,
    topic: list[str] | None = None,
    skip: set[str] | None = None,
) -> pd.DataFrame:
    """Filter reviews. `skip` omits dimensions (for linked filter option lists)."""
    skip = skip or set()
    df = data.df
    stores = _as_list(store_name)
    sats = _as_list(satisfaction)
    journeys = _as_list(journey)
    topics = _as_list(topic)

    if "store_name" not in skip and stores:
        df = df[df["store_name"].isin(stores)]
    if "satisfaction" not in skip and sats:
        df = df[df["satisfaction"].isin(sats)]

    active_journeys = [j for j in journeys if j in JOURNEYS] if journeys else list(JOURNEYS)
    if "journey" not in skip and journeys:
        mask = pd.Series(False, index=df.index)
        for j in active_journeys:
            mask = mask | (df[PRED_COL[j]] == 1)
        df = df[mask]

    if "topic" not in skip and topics:
        infos = topic_matches_for_names(data, topics)
        if not infos:
            return df.iloc[0:0]
        topic_mask = pd.Series(False, index=df.index)
        for info in infos:
            col = PRED_COL[info.journey]
            journey_hit = df[col] == 1
            if info.distinctive:
                kw_hit = _review_hits_keywords(df["_review_lc"], info.distinctive)
                topic_mask = topic_mask | (journey_hit & kw_hit)
            else:
                topic_mask = topic_mask | journey_hit
        df = df[topic_mask]

    return df


def _topic_has_hits(df: pd.DataFrame, journey: str, info: TopicInfo) -> bool:
    if df.empty or journey not in PRED_COL:
        return False
    hits = df[df[PRED_COL[journey]] == 1]
    if hits.empty:
        return False
    if info.distinctive:
        return bool(_review_hits_keywords(hits["_review_lc"], info.distinctive).any())
    return True


def filter_options(
    data: AppData,
    *,
    store_name: list[str] | None = None,
    satisfaction: list[str] | None = None,
    journey: list[str] | None = None,
    topic: list[str] | None = None,
) -> dict:
    stores_df = apply_filters(
        data,
        store_name=store_name,
        satisfaction=satisfaction,
        journey=journey,
        topic=topic,
        skip={"store_name"},
    )
    sat_df = apply_filters(
        data,
        store_name=store_name,
        satisfaction=satisfaction,
        journey=journey,
        topic=topic,
        skip={"satisfaction"},
    )
    journey_df = apply_filters(
        data,
        store_name=store_name,
        satisfaction=satisfaction,
        journey=journey,
        topic=topic,
        skip={"journey"},
    )
    # Topic options ignore currently selected topics so the list stays complete
    # for the active store/sentiment/journey scope.
    topic_df = apply_filters(
        data,
        store_name=store_name,
        satisfaction=satisfaction,
        journey=journey,
        topic=None,
        skip={"topic"},
    )

    available_journeys = [
        j for j in JOURNEYS if not journey_df.empty and (journey_df[PRED_COL[j]] == 1).any()
    ]

    selected_journeys = [j for j in _as_list(journey) if j in JOURNEYS]
    journey_scope = selected_journeys or available_journeys

    selected_sats = {
        s for s in _as_list(satisfaction) if s in SENTIMENTS
    }

    topic_names: list[str] = []
    for j in journey_scope:
        if j not in available_journeys:
            continue
        for info in data.topics_by_journey.get(j, []):
            if (
                info.satisfaction
                and selected_sats
                and info.satisfaction not in selected_sats
            ):
                continue
            if info.name in topic_names:
                continue
            if _topic_has_hits(topic_df, j, info):
                topic_names.append(info.name)

    return {
        "store_name": sorted(stores_df["store_name"].dropna().unique().tolist()),
        "satisfaction": [s for s in SENTIMENTS if s in set(sat_df["satisfaction"].tolist())],
        "journey": [
            {"id": j, "label": JOURNEY_LABELS[j]}
            for j in JOURNEYS
            if j in available_journeys
        ],
        "topic": topic_names,
    }


def heatmap(
    data: AppData,
    *,
    store_name: list[str] | None = None,
    satisfaction: list[str] | None = None,
    journey: list[str] | None = None,
    topic: list[str] | None = None,
) -> dict:
    df = apply_filters(
        data, store_name=store_name, satisfaction=satisfaction, journey=journey, topic=topic
    )
    selected_journeys = [j for j in _as_list(journey) if j in JOURNEYS] or list(JOURNEYS)
    selected_sats = [s for s in _as_list(satisfaction) if s in SENTIMENTS] or list(SENTIMENTS)

    cells = []
    for j in JOURNEYS:
        for sat in SENTIMENTS:
            if j not in selected_journeys or sat not in selected_sats:
                count = 0
            else:
                subset = df[(df[PRED_COL[j]] == 1) & (df["satisfaction"] == sat)]
                count = int(len(subset))
            cells.append(
                {
                    "journey": j,
                    "journey_label": JOURNEY_LABELS[j],
                    "satisfaction": sat,
                    "count": count,
                }
            )
    return {"cells": cells, "journeys": list(JOURNEYS), "sentiments": list(SENTIMENTS)}


def topics_for_cell(
    data: AppData,
    *,
    journey: str,
    satisfaction: list[str] | None = None,
    store_name: list[str] | None = None,
    topic: list[str] | None = None,
) -> dict:
    if journey not in JOURNEYS:
        return {"topics": []}

    df = apply_filters(
        data,
        store_name=store_name,
        satisfaction=satisfaction,
        journey=[journey],
        topic=topic,
    )
    df = df[df[PRED_COL[journey]] == 1]

    selected_topics = set(_as_list(topic))
    selected_sats = {s for s in _as_list(satisfaction) if s in SENTIMENTS}
    result = []
    for info in data.topics_by_journey.get(journey, []):
        if (
            info.satisfaction
            and selected_sats
            and info.satisfaction not in selected_sats
        ):
            continue
        if selected_topics and info.name not in selected_topics:
            continue
        if df.empty:
            size = 0
            avg_rating = 0.0
        elif info.distinctive:
            hit_mask = _review_hits_keywords(df["_review_lc"], info.distinctive)
            matched = df[hit_mask]
            size = int(len(matched))
            avg_rating = float(matched["stars"].mean()) if size else 0.0
        else:
            matched = df
            size = int(len(matched))
            avg_rating = float(matched["stars"].mean()) if size else 0.0
        if size <= 0:
            continue
        result.append(
            {
                "topic_id": info.topic_id,
                "name": info.name,
                "journey": journey,
                "satisfaction": info.satisfaction,
                "size": size,
                "avg_rating": round(avg_rating, 3),
                "document_count": info.document_count,
                "keywords": info.distinctive or info.keywords[:5],
            }
        )
    result.sort(key=lambda x: x["size"], reverse=True)
    return {"topics": result, "journey": journey, "journey_label": JOURNEY_LABELS[journey]}
