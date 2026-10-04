"""PostgreSQL helpers for idea_policy and generated_ideas."""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SEED_POLICY = Path(__file__).resolve().parent / "postgres" / "seed_policy.md"
INIT_SQL = Path(__file__).resolve().parent / "postgres" / "init.sql"


class DatabaseError(RuntimeError):
    pass


def database_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://review:review@localhost:5432/review_dashboard",
    ).strip()
    if not url:
        raise DatabaseError("DATABASE_URL is empty.")
    return url


@contextmanager
def connect() -> Iterator[Any]:
    try:
        import psycopg2
    except ImportError as exc:
        raise DatabaseError("psycopg2 is not installed.") from exc

    conn = psycopg2.connect(database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema_and_seed(*, retries: int = 20, delay_s: float = 1.0) -> None:
    """Create tables if missing and seed default policy when empty."""
    init_sql = INIT_SQL.read_text(encoding="utf-8")
    seed = SEED_POLICY.read_text(encoding="utf-8").strip()
    last_err: Exception | None = None

    for _ in range(retries):
        try:
            with connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(init_sql)
                    cur.execute("SELECT content FROM idea_policy WHERE id = 1")
                    row = cur.fetchone()
                    if row is None:
                        cur.execute(
                            "INSERT INTO idea_policy (id, content) VALUES (1, %s)",
                            (seed,),
                        )
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(delay_s)

    raise DatabaseError(f"Could not initialize Postgres: {last_err}")


def get_policy() -> dict:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content, updated_at FROM idea_policy WHERE id = 1"
            )
            row = cur.fetchone()
            if row is None:
                raise DatabaseError("idea_policy row missing. Restart backend to seed.")
            content, updated_at = row
            return {
                "content": content,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }


def update_policy(content: str) -> dict:
    text = (content or "").strip()
    if not text:
        raise DatabaseError("Policy content cannot be empty.")
    now = datetime.now(timezone.utc)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO idea_policy (id, content, updated_at)
                VALUES (1, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content,
                    updated_at = EXCLUDED.updated_at
                RETURNING content, updated_at
                """,
                (text, now),
            )
            content_out, updated_at = cur.fetchone()
            return {
                "content": content_out,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }


def save_generated_ideas(
    *,
    journey: str,
    topic: str,
    satisfaction: str,
    mode: str,
    store_names: list[str] | None,
    ideas: list[str],
    comments: list[dict],
    policy_updated_at: str | None,
) -> int:
    policy_ts = None
    if policy_updated_at:
        policy_ts = datetime.fromisoformat(policy_updated_at)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO generated_ideas (
                    journey, topic, satisfaction, mode,
                    store_names, ideas, comments, policy_version
                )
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                RETURNING id
                """,
                (
                    journey,
                    topic,
                    satisfaction,
                    mode,
                    json.dumps(store_names or []),
                    json.dumps(ideas),
                    json.dumps(comments),
                    policy_ts,
                ),
            )
            return int(cur.fetchone()[0])
