from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.core.sanitizer import default_action, default_headline, derive_public_scores
from app.models import (
    EditorialMemoryItem,
    EditorialMemoryResponse,
    EditorialMemoryUpsertRequest,
    FeedMetrics,
    PublicFeedResponse,
    RefreshResponse,
    RealtimeSessionRequest,
    RealtimeSessionResponse,
)
from app.routes.deps import require_admin
from app.routes.errors import bad_gateway, service_unavailable

router = APIRouter()


@router.post("/openai/realtime-session", response_model=RealtimeSessionResponse)
def create_realtime_session(payload: RealtimeSessionRequest, request: Request) -> RealtimeSessionResponse:
    require_admin(request)
    try:
        session = request.app.state.openai_service.create_realtime_session(
            model=payload.model,
            voice=payload.voice,
            instructions=payload.instructions,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("OpenAI session error", exc) from exc
    return RealtimeSessionResponse(session=session)


@router.post("/intel/refresh", response_model=RefreshResponse)
def refresh_public_feed(request: Request) -> RefreshResponse:
    require_admin(request)

    store = request.app.state.store
    averages = store.averaged_signals(days=7)
    scores = derive_public_scores(averages)

    headline = default_headline(scores)
    action = default_action(scores)

    ai_brief = None
    try:
        ai_brief = request.app.state.openai_service.generate_public_brief(averages, scores)
    except Exception:
        ai_brief = None

    if ai_brief is not None:
        headline = ai_brief["headline"]
        action = ai_brief["action"]

    updated_at = datetime.now(timezone.utc)
    metrics = FeedMetrics(
        recovery=f"{scores['recovery']}/100",
        focus=f"{scores['focus']}/100",
        balance=f"{scores['balance']}/100",
        action=action,
    )
    feed = PublicFeedResponse(headline=headline, metrics=metrics, updated_at=updated_at)

    store.save_public_feed(
        day=updated_at.date().isoformat(),
        headline=feed.headline,
        recovery=feed.metrics.recovery,
        focus=feed.metrics.focus,
        balance=feed.metrics.balance,
        action=feed.metrics.action,
        updated_at=updated_at,
    )

    return RefreshResponse(refreshed=ai_brief is not None, feed=feed)


@router.get("/openai/editorial-memory", response_model=EditorialMemoryResponse)
def list_editorial_memory(request: Request) -> EditorialMemoryResponse:
    require_admin(request)
    rows = request.app.state.store.list_editorial_memory(limit=32)
    items = [
        EditorialMemoryItem(
            id=row["id"],
            theme=row["theme"],
            notes=row["notes"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
        for row in rows
    ]
    return EditorialMemoryResponse(items=items)


@router.post("/openai/editorial-memory", response_model=EditorialMemoryResponse)
def upsert_editorial_memory(payload: EditorialMemoryUpsertRequest, request: Request) -> EditorialMemoryResponse:
    require_admin(request)
    store = request.app.state.store
    store.upsert_editorial_memory(theme=payload.theme, notes=payload.notes)
    return list_editorial_memory(request)
