"""FastAPI entrypoint for the review dashboard API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data import AppData, load_data
from db import DatabaseError, ensure_schema_and_seed, get_policy, update_policy
from ideas import IdeaGenerationError, generate_ideas
from services import filter_options, heatmap, topics_for_cell

state: dict[str, AppData] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_schema_and_seed()
    state["data"] = load_data()
    yield
    state.clear()


app = FastAPI(title="Customer Review Dashboard API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PolicyUpdate(BaseModel):
    content: str = Field(..., min_length=1)


def _data() -> AppData:
    return state["data"]


@app.get("/api/health")
def health():
    return {"ok": True, "rows": int(len(_data().df))}


@app.get("/api/policy")
def api_get_policy():
    try:
        return get_policy()
    except DatabaseError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.put("/api/policy")
def api_put_policy(body: PolicyUpdate):
    try:
        return update_policy(body.content)
    except DatabaseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/filters")
def api_filters(
    store_name: list[str] | None = Query(None),
    satisfaction: list[str] | None = Query(None),
    journey: list[str] | None = Query(None),
    topic: list[str] | None = Query(None),
):
    return filter_options(
        _data(),
        store_name=store_name,
        satisfaction=satisfaction,
        journey=journey,
        topic=topic,
    )


@app.get("/api/heatmap")
def api_heatmap(
    store_name: list[str] | None = Query(None),
    satisfaction: list[str] | None = Query(None),
    journey: list[str] | None = Query(None),
    topic: list[str] | None = Query(None),
):
    return heatmap(
        _data(),
        store_name=store_name,
        satisfaction=satisfaction,
        journey=journey,
        topic=topic,
    )


@app.get("/api/topics")
def api_topics(
    journey: str = Query(...),
    store_name: list[str] | None = Query(None),
    satisfaction: list[str] | None = Query(None),
    topic: list[str] | None = Query(None),
):
    return topics_for_cell(
        _data(),
        journey=journey,
        store_name=store_name,
        satisfaction=satisfaction,
        topic=topic,
    )


@app.get("/api/ideas")
def api_ideas(
    journey: str = Query(...),
    topic: str = Query(...),
    satisfaction: str = Query(...),
    store_name: list[str] | None = Query(None),
):
    try:
        return generate_ideas(
            _data(),
            journey=journey,
            topic=topic,
            satisfaction=satisfaction,
            store_name=store_name,
        )
    except IdeaGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Idea generation failed: {exc}") from exc
