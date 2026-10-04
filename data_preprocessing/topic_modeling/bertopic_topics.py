"""BERTopic per journey × satisfaction + Gemini topic naming."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    COL_REVIEW,
    COL_SATISFACTION,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_TOPIC_EMBEDDING_MODEL,
    DEFAULT_TOPIC_MAX_PER_JOURNEY,
    DEFAULT_TOPIC_SAMPLES_PER_TOPIC,
    JOURNEY_CLASSES,
    PACKAGE_ROOT,
    TOPIC_OUTPUT_JSON,
)

logger = logging.getLogger(__name__)

MIN_DOCS_FOR_TOPICS = 40
SATISFACTION_VALUES: tuple[str, ...] = ("positive", "negative")


class TopicModelingError(RuntimeError):
    """Raised when topic modeling cannot run."""


def load_dotenv_file() -> None:
    """Load data_preprocessing/.env if present."""
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise TopicModelingError(
            "python-dotenv is required. Install: pip install -r requirements-topics.txt"
        ) from exc
    env_path = PACKAGE_ROOT / ".env"
    load_dotenv(env_path)
    if not env_path.exists():
        logger.warning(
            "No .env at %s — copy .env.example and set GEMINI_API_KEY.", env_path
        )


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _require_gemini_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        raise TopicModelingError(
            "GEMINI_API_KEY missing. Copy .env.example to .env and set your key."
        )
    return key


def _truncate(text: str, max_chars: int = 400) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def name_topic_with_gemini(
    *,
    journey: str,
    satisfaction: str,
    keywords: list[str],
    sample_reviews: list[str],
    api_key: str,
    model_name: str,
) -> str:
    """Ask Gemini for a short category name matched to review polarity."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    samples_block = "\n".join(
        f"{i + 1}. {_truncate(s)}" for i, s in enumerate(sample_reviews)
    )
    if satisfaction == "positive":
        polarity_rule = (
            "These are POSITIVE reviews. The title MUST sound positive "
            "(praise, strengths, what went well). "
            "Do NOT use complaint, issue, delay, pressure, or problem wording."
        )
        examples = (
            "Helpful no-pressure sales help, Smooth online booking, "
            "Clear financing guidance"
        )
    else:
        polarity_rule = (
            "These are NEGATIVE reviews. The title MUST sound negative "
            "(complaints, friction, failures). "
            "Do NOT use praise words like excellent, smooth, or great."
        )
        examples = (
            "Sales pressure complaints, Financing paperwork delays, "
            "Service wait frustration"
        )

    prompt = f"""You name customer-review topics for a used-car dealership analysis.

Journey stage: {journey}
Review sentiment: {satisfaction}
{polarity_rule}

BERTopic keywords: {', '.join(keywords[:12]) if keywords else '(none)'}

Sample reviews:
{samples_block}

Return ONLY a short simple category name (2 to 5 words).
No quotes, no punctuation at the end, no explanation.
Examples: {examples}
"""
    response = model.generate_content(prompt)
    name = (response.text or "").strip().splitlines()[0].strip().strip("\"'")
    name = re.sub(r"\s+", " ", name)
    if not name:
        name = " ".join(keywords[:3]) if keywords else f"{journey} {satisfaction} topic"
    return name[:80]


def _fit_bertopic(
    docs: list[str],
    *,
    embedding_model_name: str,
    max_topics: int,
) -> tuple[Any, list[int]]:
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer

    embedder = SentenceTransformer(embedding_model_name)
    # Smaller clusters so we can reach >= max_topics themes
    min_topic_size = max(8, min(20, len(docs) // max(60, max_topics * 8)))
    topic_model = BERTopic(
        embedding_model=embedder,
        min_topic_size=min_topic_size,
        top_n_words=10,
        verbose=False,
        calculate_probabilities=False,
    )
    topics, _ = topic_model.fit_transform(docs)

    unique_non_outlier = sorted({t for t in topics if t != -1})
    if len(unique_non_outlier) < max_topics and min_topic_size > 5:
        retry_size = max(5, min_topic_size // 2)
        logger.info(
            "Only %s topics with min_topic_size=%s; retrying with %s",
            len(unique_non_outlier),
            min_topic_size,
            retry_size,
        )
        topic_model = BERTopic(
            embedding_model=embedder,
            min_topic_size=retry_size,
            top_n_words=10,
            verbose=False,
            calculate_probabilities=False,
        )
        topics, _ = topic_model.fit_transform(docs)
        unique_non_outlier = sorted({t for t in topics if t != -1})

    if len(unique_non_outlier) > max_topics:
        topic_model = topic_model.reduce_topics(docs, nr_topics=max_topics)
        topics = topic_model.topics_

    return topic_model, list(topics)


def _topic_keywords(topic_model: Any, topic_id: int) -> list[str]:
    words = topic_model.get_topic(topic_id)
    if not words:
        return []
    return [w for w, _ in words[:10]]


def build_topics_for_slice(
    docs: list[str],
    *,
    journey: str,
    satisfaction: str,
    embedding_model_name: str,
    max_topics: int,
    samples_per_topic: int,
    api_key: str,
    gemini_model: str,
) -> dict[str, Any]:
    """Run BERTopic + Gemini naming for one journey × satisfaction corpus."""
    if len(docs) < MIN_DOCS_FOR_TOPICS:
        logger.warning(
            "Slice %s/%s has only %s docs (< %s); skipping BERTopic.",
            journey,
            satisfaction,
            len(docs),
            MIN_DOCS_FOR_TOPICS,
        )
        return {
            "document_count": len(docs),
            "topics": [],
            "skipped": True,
            "reason": f"fewer than {MIN_DOCS_FOR_TOPICS} documents",
        }

    logger.info(
        "Fitting BERTopic for journey=%s satisfaction=%s docs=%s embedding=%s",
        journey,
        satisfaction,
        len(docs),
        embedding_model_name,
    )
    topic_model, topics = _fit_bertopic(
        docs,
        embedding_model_name=embedding_model_name,
        max_topics=max_topics,
    )

    counts: dict[int, int] = {}
    for t in topics:
        if t == -1:
            continue
        counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:max_topics]

    topic_payloads: list[dict[str, Any]] = []
    for topic_id, count in ranked:
        indices = [i for i, t in enumerate(topics) if t == topic_id]
        sample_idx = indices[:samples_per_topic]
        samples = [docs[i] for i in sample_idx]
        keywords = _topic_keywords(topic_model, topic_id)
        try:
            name = name_topic_with_gemini(
                journey=journey,
                satisfaction=satisfaction,
                keywords=keywords,
                sample_reviews=samples,
                api_key=api_key,
                model_name=gemini_model,
            )
        except Exception as exc:  # noqa: BLE001 - keep pipeline resilient
            logger.exception(
                "Gemini naming failed for %s/%s topic %s: %s",
                journey,
                satisfaction,
                topic_id,
                exc,
            )
            name = " / ".join(keywords[:3]) if keywords else f"{journey}_{satisfaction}_{topic_id}"

        topic_payloads.append(
            {
                "topic_id": int(topic_id),
                "name": name,
                "satisfaction": satisfaction,
                "keywords": keywords,
                "document_count": int(count),
                "sample_reviews": samples,
            }
        )
        logger.info(
            "Journey %s/%s topic %s -> '%s' (n=%s)",
            journey,
            satisfaction,
            topic_id,
            name,
            count,
        )

    return {
        "document_count": len(docs),
        "topics": topic_payloads,
        "skipped": False,
    }


def run_topic_modeling(
    df: pd.DataFrame,
    *,
    output_json: Path | None = None,
) -> dict[str, Any]:
    """Run BERTopic for all journey × satisfaction slices and write JSON."""
    load_dotenv_file()
    api_key = _require_gemini_key()

    embedding_model = os.environ.get(
        "TOPIC_EMBEDDING_MODEL", DEFAULT_TOPIC_EMBEDDING_MODEL
    )
    gemini_model = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    max_topics = _env_int("TOPIC_MAX_PER_JOURNEY", DEFAULT_TOPIC_MAX_PER_JOURNEY)
    samples_per_topic = _env_int(
        "TOPIC_SAMPLES_PER_TOPIC", DEFAULT_TOPIC_SAMPLES_PER_TOPIC
    )
    # At least 10 topics per journey×satisfaction slice (cap at 15 for cost)
    max_topics = max(10, min(15, max_topics))
    samples_per_topic = max(1, min(5, samples_per_topic))

    missing_pred = [f"{j}_pred" for j in JOURNEY_CLASSES if f"{j}_pred" not in df.columns]
    if missing_pred:
        raise TopicModelingError(
            f"DataFrame missing journey prediction columns: {missing_pred}"
        )
    if COL_REVIEW not in df.columns:
        raise TopicModelingError(f"DataFrame missing '{COL_REVIEW}' column.")
    if COL_SATISFACTION not in df.columns:
        raise TopicModelingError(f"DataFrame missing '{COL_SATISFACTION}' column.")

    journeys_out: dict[str, Any] = {}
    for journey in JOURNEY_CLASSES:
        pred_col = f"{journey}_pred"
        journey_mask = df[pred_col].astype(int) == 1
        by_sat: dict[str, Any] = {}
        flat_topics: list[dict[str, Any]] = []
        total_docs = 0

        for satisfaction in SATISFACTION_VALUES:
            sat_mask = (
                journey_mask
                & (df[COL_SATISFACTION].astype(str).str.lower() == satisfaction)
            )
            docs = (
                df.loc[sat_mask, COL_REVIEW]
                .astype(str)
                .map(lambda x: x.strip())
                .replace("", pd.NA)
                .dropna()
                .tolist()
            )
            slice_payload = build_topics_for_slice(
                docs,
                journey=journey,
                satisfaction=satisfaction,
                embedding_model_name=embedding_model,
                max_topics=max_topics,
                samples_per_topic=samples_per_topic,
                api_key=api_key,
                gemini_model=gemini_model,
            )
            by_sat[satisfaction] = slice_payload
            total_docs += int(slice_payload.get("document_count") or 0)
            for topic in slice_payload.get("topics", []):
                flat_topics.append(topic)

        journeys_out[journey] = {
            "document_count": total_docs,
            "by_satisfaction": by_sat,
            # Flat list kept for simpler consumers (each topic has satisfaction)
            "topics": flat_topics,
        }

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": embedding_model,
        "gemini_model": gemini_model,
        "max_topics_per_journey_satisfaction": max_topics,
        "samples_per_topic_for_naming": samples_per_topic,
        "grouping": "journey_x_satisfaction",
        "journeys": journeys_out,
    }

    out_path = output_json or TOPIC_OUTPUT_JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    logger.info("Wrote topic JSON to %s", out_path)
    return payload
