from __future__ import annotations

import json
from calendar import month_name
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.models import (
    AutobiographerMemoryEventCreateRequest,
    AutobiographerMemoryEventItem,
    AutobiographerMemoryEventsResponse,
    AutobiographerMonthlyChapterGenerateRequest,
    AutobiographerMonthlyChapterItem,
    AutobiographerMonthlyChapterResponse,
    AutobiographerMonthlyChaptersInitializeRequest,
    AutobiographerMonthlyChaptersResponse,
)
from app.routes.deps import require_admin
from app.routes.errors import bad_gateway, service_unavailable

router = APIRouter()


def _month_label(month: int) -> str:
    return month_name[month]


def _as_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _is_month_closed(*, year: int, month: int, now: datetime) -> bool:
    return (year, month) < (now.year, now.month)


def _to_memory_item(row: dict) -> AutobiographerMemoryEventItem:
    tags_raw = row.get("tags_json") or "[]"
    try:
        tags = json.loads(tags_raw)
    except json.JSONDecodeError:
        tags = []
    if not isinstance(tags, list):
        tags = []

    return AutobiographerMemoryEventItem(
        id=row["id"],
        source=row["source"],
        title=row["title"],
        detail=row["detail"],
        tags=[str(tag) for tag in tags],
        event_at=_as_dt(row["event_at"]),
        created_at=_as_dt(row["created_at"]),
    )


def _to_month_chapter_item(row: dict) -> AutobiographerMonthlyChapterItem:
    locked_at = row.get("locked_at") or None
    return AutobiographerMonthlyChapterItem(
        id=row["id"],
        year=row["year"],
        month=row["month"],
        month_label=_month_label(row["month"]),
        persona_label=row["persona_label"],
        style_brief=row["style_brief"],
        summary=row["summary"],
        chapter_markdown=row["chapter_markdown"],
        status=row["status"],
        locked_at=_as_dt(locked_at) if locked_at else None,
        generated_at=_as_dt(row["generated_at"]),
        updated_at=_as_dt(row["updated_at"]),
    )


@router.post("/lab/autobiographer/events", response_model=AutobiographerMemoryEventItem)
def create_autobiographer_event(payload: AutobiographerMemoryEventCreateRequest, request: Request) -> AutobiographerMemoryEventItem:
    require_admin(request)
    store = request.app.state.store
    event_id = store.create_autobiographer_memory_event(
        source=payload.source,
        title=payload.title,
        detail=payload.detail,
        tags_json=json.dumps(payload.tags),
        event_at=payload.event_at.astimezone(timezone.utc).isoformat(),
    )
    rows = store.list_autobiographer_memory_events(limit=1)
    event_row = next((row for row in rows if row["id"] == event_id), None)
    if event_row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist event.")
    return _to_memory_item(event_row)


@router.get("/lab/autobiographer/events", response_model=AutobiographerMemoryEventsResponse)
def list_autobiographer_events(
    request: Request,
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    limit: int = Query(default=120, ge=1, le=500),
) -> AutobiographerMemoryEventsResponse:
    require_admin(request)
    rows = request.app.state.store.list_autobiographer_memory_events(limit=limit, year=year)
    items = [_to_memory_item(row) for row in rows]
    if month is not None:
        items = [item for item in items if item.event_at.month == month and (year is None or item.event_at.year == year)]
    return AutobiographerMemoryEventsResponse(items=items)


@router.post("/lab/autobiographer/chapters/initialize-year", response_model=AutobiographerMonthlyChaptersResponse)
def initialize_autobiographer_year(
    payload: AutobiographerMonthlyChaptersInitializeRequest,
    request: Request,
) -> AutobiographerMonthlyChaptersResponse:
    require_admin(request)
    store = request.app.state.store
    now = datetime.now(timezone.utc)

    for month in range(1, 13):
        existing = store.get_autobiographer_month_chapter(year=payload.year, month=month)
        if existing is not None:
            continue

        is_closed = _is_month_closed(year=payload.year, month=month, now=now)
        status_value = "locked" if is_closed else "live"
        locked_at = now.isoformat() if is_closed else ""
        label = _month_label(month)
        summary = f"{label} {payload.year} initialized and ready for monthly autobiographer updates."
        chapter = (
            f"# {label} {payload.year}\n\n"
            "This chapter shell is initialized. Add memory events and run monthly generation to build a living narrative."
        )

        store.upsert_autobiographer_month_chapter(
            year=payload.year,
            month=month,
            persona_label=payload.persona_label,
            style_brief=payload.style_brief,
            summary=summary,
            chapter_markdown=chapter,
            status=status_value,
            locked_at=locked_at,
        )

    rows = store.list_autobiographer_month_chapters(year=payload.year, limit=24)
    items = [_to_month_chapter_item(row) for row in rows]
    return AutobiographerMonthlyChaptersResponse(year=payload.year, items=items)


@router.post("/lab/autobiographer/chapters/generate", response_model=AutobiographerMonthlyChapterResponse)
def generate_autobiographer_month_chapter(
    payload: AutobiographerMonthlyChapterGenerateRequest,
    request: Request,
) -> AutobiographerMonthlyChapterResponse:
    require_admin(request)
    store = request.app.state.store
    now = datetime.now(timezone.utc)

    existing = store.get_autobiographer_month_chapter(year=payload.year, month=payload.month)
    if existing and existing.get("status") == "locked" and not payload.force_regenerate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chapter is locked because the month is complete. Set force_regenerate=true to override.",
        )

    rows = store.list_autobiographer_memory_events(limit=500, year=payload.year)
    events = [_to_memory_item(row) for row in rows]
    month_events = [item for item in events if item.event_at.month == payload.month]
    month_events.sort(key=lambda item: item.event_at)

    memory_payload = [
        {
            "source": item.source,
            "title": item.title,
            "detail": item.detail,
            "tags": item.tags,
            "event_at": item.event_at.isoformat(),
        }
        for item in month_events
    ]

    try:
        generated = request.app.state.openai_service.generate_autobiographer_month_chapter(
            year=payload.year,
            month=payload.month,
            month_label=_month_label(payload.month),
            persona_label=payload.persona_label,
            style_brief=payload.style_brief,
            memory_events=memory_payload,
            include_private_context=payload.include_private_context,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("Autobiographer generation error", exc) from exc

    if not generated:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Autobiographer output was empty.")

    summary = str(generated.get("summary", "")).strip()
    chapter_markdown = str(generated.get("chapter_markdown", "")).strip()
    if not summary or not chapter_markdown:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Autobiographer output schema invalid.")

    is_closed = _is_month_closed(year=payload.year, month=payload.month, now=now)
    status_value = "locked" if is_closed else "live"
    locked_at = now.isoformat() if is_closed else ""

    store.upsert_autobiographer_month_chapter(
        year=payload.year,
        month=payload.month,
        persona_label=payload.persona_label,
        style_brief=payload.style_brief,
        summary=summary,
        chapter_markdown=chapter_markdown,
        status=status_value,
        locked_at=locked_at,
    )

    row = store.get_autobiographer_month_chapter(year=payload.year, month=payload.month)
    if row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Chapter not found after generation.")
    return AutobiographerMonthlyChapterResponse(chapter=_to_month_chapter_item(row))


@router.get("/lab/autobiographer/chapters", response_model=AutobiographerMonthlyChaptersResponse)
def list_autobiographer_month_chapters(
    request: Request,
    year: int = Query(default_factory=lambda: datetime.now(timezone.utc).year, ge=2000, le=2100),
) -> AutobiographerMonthlyChaptersResponse:
    require_admin(request)
    rows = request.app.state.store.list_autobiographer_month_chapters(year=year, limit=24)
    items = [_to_month_chapter_item(row) for row in rows]
    return AutobiographerMonthlyChaptersResponse(year=year, items=items)


@router.get("/lab/autobiographer/chapters/{year}/{month}", response_model=AutobiographerMonthlyChapterResponse)
def get_autobiographer_month_chapter(
    year: int,
    month: int,
    request: Request,
) -> AutobiographerMonthlyChapterResponse:
    require_admin(request)
    if month < 1 or month > 12:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="month must be 1..12")
    row = request.app.state.store.get_autobiographer_month_chapter(year=year, month=month)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return AutobiographerMonthlyChapterResponse(chapter=_to_month_chapter_item(row))
