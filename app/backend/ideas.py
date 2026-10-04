"""Generate keep/improve ideas from longest matching review samples."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd

from config import JOURNEY_LABELS, PRED_COL
from data import AppData
from db import DatabaseError, get_policy, save_generated_ideas
from services import _review_hits_keywords, apply_filters, topic_matches_for_names

SAMPLE_N = 5


class IdeaGenerationError(RuntimeError):
    pass


def _load_dotenv_files() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = Path(__file__).resolve().parent
    candidates = [here.parent / ".env"]
    # Local repo layout only (not present inside the Docker /app image)
    if len(here.parents) > 1:
        candidates.append(here.parents[1] / "data_preprocessing" / ".env")
    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=False)


def _gemini_key() -> str:
    _load_dotenv_files()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        raise IdeaGenerationError(
            "GEMINI_API_KEY missing. Set it in app/.env or data_preprocessing/.env"
        )
    return key


def load_policy_text() -> tuple[str, str | None]:
    """Return (policy_content, updated_at iso) from Postgres."""
    try:
        row = get_policy()
    except DatabaseError as exc:
        raise IdeaGenerationError(str(exc)) from exc
    return row["content"], row.get("updated_at")


def _matching_reviews(
    data: AppData,
    *,
    journey: str,
    topic_name: str,
    satisfaction: list[str] | None,
    store_name: list[str] | None,
) -> pd.DataFrame:
    df = apply_filters(
        data,
        store_name=store_name,
        satisfaction=satisfaction,
        journey=[journey],
        topic=[topic_name],
    )
    df = df[df[PRED_COL[journey]] == 1]
    infos = [
        info
        for info in topic_matches_for_names(data, [topic_name])
        if info.journey == journey
    ]
    if infos and infos[0].distinctive:
        df = df[_review_hits_keywords(df["_review_lc"], infos[0].distinctive)]
    return df


def select_longest_comments(df: pd.DataFrame, n: int = SAMPLE_N) -> list[dict]:
    if df.empty:
        return []
    work = df.copy()
    work["_len"] = work["review"].astype(str).str.len()
    top = work.sort_values("_len", ascending=False).head(n)
    out = []
    for _, row in top.iterrows():
        text = str(row["review"]).strip()
        out.append(
            {
                "store_name": str(row.get("store_name", "")),
                "stars": float(row["stars"]) if pd.notna(row["stars"]) else None,
                "review": text,
                "char_len": int(len(text)),
            }
        )
    return out


def _call_gemini(
    *,
    policy: str,
    mode: str,
    journey: str,
    topic: str,
    satisfaction: str,
    comments: list[dict],
) -> list[str]:
    import google.generativeai as genai

    api_key = _gemini_key()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    goal = (
        "Generate improvement ideas (what to fix)."
        if mode == "improve"
        else "Generate points to keep (strengths to protect and repeat)."
    )
    samples = "\n\n".join(
        f"Comment {i + 1} (stars={c.get('stars')}, chars={c['char_len']}):\n{c['review']}"
        for i, c in enumerate(comments)
    )
    prompt = f"""Follow this policy strictly:

{policy}

---
Task: {goal}
Journey stage: {JOURNEY_LABELS.get(journey, journey)}
Topic category: {topic}
Sentiment: {satisfaction}

Sample customer comments (longest texts for this topic):
{samples}

Return ONLY a markdown bullet list (use "- " bullets). No title, no intro.
"""
    response = model.generate_content(prompt)
    text = (response.text or "").strip()
    if not text:
        raise IdeaGenerationError("Gemini returned an empty response.")

    bullets: list[str] = []
    for line in text.splitlines():
        cleaned = re.sub(r"^\s*([-*\d+\.]+\s*)", "", line).strip()
        if cleaned:
            bullets.append(cleaned)
    if not bullets:
        bullets = [text]
    return bullets


def generate_ideas(
    data: AppData,
    *,
    journey: str,
    topic: str,
    satisfaction: str,
    store_name: list[str] | None = None,
) -> dict:
    sat = satisfaction.strip().lower()
    if sat not in {"positive", "negative"}:
        raise IdeaGenerationError("satisfaction must be 'positive' or 'negative'.")
    if journey not in PRED_COL:
        raise IdeaGenerationError(f"Unknown journey: {journey}")

    mode = "keep" if sat == "positive" else "improve"
    policy, policy_updated_at = load_policy_text()
    matched = _matching_reviews(
        data,
        journey=journey,
        topic_name=topic,
        satisfaction=[sat],
        store_name=store_name,
    )
    comments = select_longest_comments(matched, SAMPLE_N)
    if not comments:
        raise IdeaGenerationError(
            "No matching comments found for this topic under current filters."
        )

    ideas = _call_gemini(
        policy=policy,
        mode=mode,
        journey=journey,
        topic=topic,
        satisfaction=sat,
        comments=comments,
    )

    idea_id: int | None = None
    try:
        idea_id = save_generated_ideas(
            journey=journey,
            topic=topic,
            satisfaction=sat,
            mode=mode,
            store_names=store_name,
            ideas=ideas,
            comments=comments,
            policy_updated_at=policy_updated_at,
        )
    except DatabaseError:
        # Generation still succeeds even if persistence fails.
        idea_id = None

    return {
        "id": idea_id,
        "mode": mode,
        "journey": journey,
        "journey_label": JOURNEY_LABELS.get(journey, journey),
        "topic": topic,
        "satisfaction": sat,
        "comments": comments,
        "ideas": ideas,
    }
