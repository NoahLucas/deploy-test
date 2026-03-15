from __future__ import annotations

import json
from calendar import month_name
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.models import (
    AutobiographerChapterGenerateRequest,
    AutobiographerChapterItem,
    AutobiographerChapterResponse,
    AutobiographerChaptersResponse,
    AutobiographerMemoryEventCreateRequest,
    AutobiographerMemoryEventItem,
    AutobiographerMemoryEventsResponse,
    AutobiographerMonthlyChapterGenerateRequest,
    AutobiographerMonthlyChapterItem,
    AutobiographerMonthlyChapterResponse,
    AutobiographerMonthlyChaptersInitializeRequest,
    AutobiographerMonthlyChaptersResponse,
    AutobiographerPublishLiveNoteRequest,
    AutobiographerPublishLiveNoteResponse,
    AutobiographerPublishYearNoteRequest,
    AutobiographerPublishYearNoteResponse,
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
    people_raw = row.get("people_json") or "[]"
    try:
        tags = json.loads(tags_raw)
    except json.JSONDecodeError:
        tags = []
    try:
        people = json.loads(people_raw)
    except json.JSONDecodeError:
        people = []
    if not isinstance(tags, list):
        tags = []
    if not isinstance(people, list):
        people = []

    return AutobiographerMemoryEventItem(
        id=row["id"],
        source=row["source"],
        title=row["title"],
        detail=row["detail"],
        tags=[str(tag) for tag in tags],
        people=[str(person) for person in people],
        place_label=(str(row.get("place_label", "")).strip() or None),
        privacy_level=str(row.get("privacy_level", "private")),
        review_state=str(row.get("review_state", "accepted")),
        source_kind=str(row.get("source_kind", "manual")),
        joy_score=float(row["joy_score"]) if row.get("joy_score") is not None else None,
        family_relevance_score=float(row["family_relevance_score"]) if row.get("family_relevance_score") is not None else None,
        importance_score=float(row["importance_score"]) if row.get("importance_score") is not None else None,
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


def _to_year_chapter_item(row: dict) -> AutobiographerChapterItem:
    return AutobiographerChapterItem(
        id=row["id"],
        year=row["year"],
        persona_label=row["persona_label"],
        style_brief=row["style_brief"],
        summary=row["summary"],
        chapter_markdown=row["chapter_markdown"],
        generated_at=_as_dt(row["generated_at"]),
        updated_at=_as_dt(row["updated_at"]),
    )


def _safe_subdir(raw: str) -> str:
    cleaned = "".join(ch for ch in raw.lower() if ch.isalnum() or ch in {"-", "_"})
    return cleaned or "notes-drafts"


def _build_live_note_markdown(year: int, chapter_rows: list[dict]) -> tuple[str, str]:
    sorted_rows = sorted(chapter_rows, key=lambda row: row["month"])
    title = f"{year} Autobiography (Live)"
    lead = (
        "A living chapter feed updated throughout the year. "
        "Each month remains live until complete, then locks as a historical snapshot."
    )

    sections: list[str] = [f"# {title}", "", lead, ""]
    for row in sorted_rows:
        month_label = _month_label(row["month"])
        status = str(row["status"]).lower()
        status_label = "Locked" if status == "locked" else "Live"
        sections.append(f"## {month_label} {year} · {status_label}")
        sections.append("")
        sections.append(str(row["chapter_markdown"]).strip())
        sections.append("")

    summary = str(sorted_rows[-1]["summary"]).strip() if sorted_rows else lead
    return summary, "\n".join(sections).strip() + "\n"


def _build_year_inputs(
    *,
    store,
    year: int,
) -> tuple[list[dict], list[dict]]:
    memory_rows = store.list_autobiographer_memory_events(limit=500, year=year)
    events = [_to_memory_item(row) for row in memory_rows]
    events.sort(key=lambda item: item.event_at)

    month_rows = store.list_autobiographer_month_chapters(year=year, limit=24)
    monthly_payload = [
        {
            "month": row["month"],
            "summary": row["summary"],
            "status": row["status"],
            "chapter_markdown": row["chapter_markdown"],
        }
        for row in month_rows
    ]
    memory_payload = [
        {
            "source": item.source,
            "source_kind": item.source_kind,
            "title": item.title,
            "detail": item.detail,
            "tags": item.tags,
            "people": item.people,
            "place_label": item.place_label,
            "privacy_level": item.privacy_level,
            "review_state": item.review_state,
            "joy_score": item.joy_score,
            "family_relevance_score": item.family_relevance_score,
            "importance_score": item.importance_score,
            "event_at": item.event_at.isoformat(),
        }
        for item in events
    ]
    return monthly_payload, memory_payload


@router.post("/lab/autobiographer/events", response_model=AutobiographerMemoryEventItem)
def create_autobiographer_event(payload: AutobiographerMemoryEventCreateRequest, request: Request) -> AutobiographerMemoryEventItem:
    require_admin(request)
    store = request.app.state.store
    event_id = store.create_autobiographer_memory_event(
        source=payload.source,
        title=payload.title,
        detail=payload.detail,
        tags_json=json.dumps(payload.tags),
        people_json=json.dumps(payload.people),
        place_label=payload.place_label or "",
        privacy_level=payload.privacy_level,
        review_state=payload.review_state,
        source_kind=payload.source_kind,
        joy_score=payload.joy_score,
        family_relevance_score=payload.family_relevance_score,
        importance_score=payload.importance_score,
        event_at=payload.event_at.astimezone(timezone.utc).isoformat(),
    )
    rows = store.list_autobiographer_memory_events(limit=500)
    event_row = next((row for row in rows if row["id"] == event_id), None)
    if event_row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist event.")
    return _to_memory_item(event_row)


@router.get("/lab/autobiographer/events", response_model=AutobiographerMemoryEventsResponse)
def list_autobiographer_events(
    request: Request,
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    month: Optional[int] = Query(default=None, ge=1, le=12),
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
            "source_kind": item.source_kind,
            "title": item.title,
            "detail": item.detail,
            "tags": item.tags,
            "people": item.people,
            "place_label": item.place_label,
            "privacy_level": item.privacy_level,
            "review_state": item.review_state,
            "joy_score": item.joy_score,
            "family_relevance_score": item.family_relevance_score,
            "importance_score": item.importance_score,
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


@router.post("/lab/autobiographer/year-chapters/generate", response_model=AutobiographerChapterResponse)
def generate_autobiographer_year_chapter(
    payload: AutobiographerChapterGenerateRequest,
    request: Request,
) -> AutobiographerChapterResponse:
    require_admin(request)
    store = request.app.state.store

    monthly_payload, memory_payload = _build_year_inputs(store=store, year=payload.year)
    if not monthly_payload and not memory_payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No autobiographer memory found for this year. Add events or generate monthly chapters first.",
        )

    try:
        generated = request.app.state.openai_service.generate_autobiographer_year_chapter(
            year=payload.year,
            persona_label=payload.persona_label,
            style_brief=payload.style_brief,
            monthly_chapters=monthly_payload,
            memory_events=memory_payload,
            include_private_context=payload.include_private_context,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("Autobiographer yearly generation error", exc) from exc

    if not generated:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Autobiographer yearly output was empty.")

    summary = str(generated.get("summary", "")).strip()
    chapter_markdown = str(generated.get("chapter_markdown", "")).strip()
    if not summary or not chapter_markdown:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Autobiographer yearly output schema invalid.")

    if not chapter_markdown.startswith("# "):
        chapter_markdown = f"# {payload.year}\n\n{chapter_markdown}"

    store.upsert_autobiographer_chapter(
        year=payload.year,
        persona_label=payload.persona_label,
        style_brief=payload.style_brief,
        summary=summary,
        chapter_markdown=chapter_markdown,
    )

    row = store.get_autobiographer_chapter_by_year(year=payload.year)
    if row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Year chapter not found after generation.")
    return AutobiographerChapterResponse(chapter=_to_year_chapter_item(row))


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


@router.get("/lab/autobiographer/year-chapters", response_model=AutobiographerChaptersResponse)
def list_autobiographer_year_chapters(
    request: Request,
    limit: int = Query(default=12, ge=1, le=50),
) -> AutobiographerChaptersResponse:
    require_admin(request)
    rows = request.app.state.store.list_autobiographer_chapters(limit=limit)
    items = [_to_year_chapter_item(row) for row in rows]
    return AutobiographerChaptersResponse(items=items)


@router.get("/lab/autobiographer/year-chapters/{year}", response_model=AutobiographerChapterResponse)
def get_autobiographer_year_chapter(
    year: int,
    request: Request,
) -> AutobiographerChapterResponse:
    require_admin(request)
    row = request.app.state.store.get_autobiographer_chapter_by_year(year=year)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Year chapter not found")
    return AutobiographerChapterResponse(chapter=_to_year_chapter_item(row))


@router.post("/lab/autobiographer/publish-live-note", response_model=AutobiographerPublishLiveNoteResponse)
def publish_autobiographer_live_note(
    payload: AutobiographerPublishLiveNoteRequest,
    request: Request,
) -> AutobiographerPublishLiveNoteResponse:
    require_admin(request)
    now = datetime.now(timezone.utc)
    if payload.year == now.year and payload.month > now.month:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="month cannot be in the future for current year")

    existing = request.app.state.store.get_autobiographer_month_chapter(year=payload.year, month=payload.month)
    should_generate = (
        existing is None
        or payload.force_regenerate
        or str(existing.get("status", "")).lower() == "live"
    )
    if should_generate:
        _ = generate_autobiographer_month_chapter(
            AutobiographerMonthlyChapterGenerateRequest(
                year=payload.year,
                month=payload.month,
                persona_label=payload.persona_label,
                style_brief=payload.style_brief,
                include_private_context=payload.include_private_context,
                force_regenerate=payload.force_regenerate,
            ),
            request,
        )

    rows = request.app.state.store.list_autobiographer_month_chapters(year=payload.year, limit=24)
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No chapters found for year.")

    summary, body_markdown = _build_live_note_markdown(payload.year, rows)
    slug = f"autobiography-{payload.year}-live"
    title = f"{payload.year} Autobiography (Live)"
    project_root: Path = request.app.state.settings.project_root
    target_dir = project_root / "content" / _safe_subdir(payload.subdir)
    target_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = target_dir / f"{slug}.md"
    json_path = target_dir / f"{slug}.json"

    draft = {
        "title": title,
        "slug": slug,
        "summary": summary,
        "body_markdown": body_markdown,
        "meta_title": f"{title} - Noah Lucas",
        "meta_description": "A continuously updated yearly autobiography note generated from monthly chapter synthesis.",
        "social_quotes": [
            "A living monthly chapter feed for the year in progress.",
            "Each month stays live while it unfolds, then locks as record.",
            "Memory, reflection, and execution context in one narrative stream.",
        ],
        "generated_at": now.isoformat(),
    }

    front_matter = [
        "---",
        f"title: {json.dumps(draft['title'])}",
        f"slug: {json.dumps(draft['slug'])}",
        f"summary: {json.dumps(draft['summary'])}",
        f"meta_title: {json.dumps(draft['meta_title'])}",
        f"meta_description: {json.dumps(draft['meta_description'])}",
        "---",
        "",
    ]
    markdown_path.write_text("\n".join(front_matter) + body_markdown, encoding="utf-8")
    json_path.write_text(json.dumps(draft, indent=2), encoding="utf-8")

    return AutobiographerPublishLiveNoteResponse(
        year=payload.year,
        month=payload.month,
        slug=slug,
        title=title,
        markdown_path=str(markdown_path),
        json_path=str(json_path),
        summary=summary,
        updated_at=now,
    )


@router.post("/lab/autobiographer/publish-year-note", response_model=AutobiographerPublishYearNoteResponse)
def publish_autobiographer_year_note(
    payload: AutobiographerPublishYearNoteRequest,
    request: Request,
) -> AutobiographerPublishYearNoteResponse:
    require_admin(request)
    chapter_row = request.app.state.store.get_autobiographer_chapter_by_year(year=payload.year)
    if chapter_row is None or payload.force_regenerate:
        _ = generate_autobiographer_year_chapter(
            AutobiographerChapterGenerateRequest(
                year=payload.year,
                persona_label=payload.persona_label,
                style_brief=payload.style_brief,
                include_private_context=payload.include_private_context,
            ),
            request,
        )
        chapter_row = request.app.state.store.get_autobiographer_chapter_by_year(year=payload.year)

    if chapter_row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Year chapter not found after generation.")

    now = datetime.now(timezone.utc)
    title = f"{payload.year} Autobiography"
    slug = f"autobiography-{payload.year}"
    body_markdown = str(chapter_row["chapter_markdown"]).strip() + "\n"
    project_root: Path = request.app.state.settings.project_root
    target_dir = project_root / "content" / _safe_subdir(payload.subdir)
    target_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = target_dir / f"{slug}.md"
    json_path = target_dir / f"{slug}.json"

    draft = {
        "title": title,
        "slug": slug,
        "summary": str(chapter_row["summary"]).strip(),
        "body_markdown": body_markdown,
        "meta_title": f"{title} - Noah Lucas",
        "meta_description": "A yearly autobiographical chapter synthesized from notes, memories, and digital exhaust.",
        "social_quotes": [
            "A yearly chapter built from the signals of a life actually lived.",
            "Work, relationships, wonder, and reflection synthesized into one narrative.",
            "A biographical record designed to help remember what mattered.",
        ],
        "generated_at": now.isoformat(),
    }

    front_matter = [
        "---",
        f"title: {json.dumps(draft['title'])}",
        f"slug: {json.dumps(draft['slug'])}",
        f"summary: {json.dumps(draft['summary'])}",
        f"meta_title: {json.dumps(draft['meta_title'])}",
        f"meta_description: {json.dumps(draft['meta_description'])}",
        "---",
        "",
    ]
    markdown_path.write_text("\n".join(front_matter) + body_markdown, encoding="utf-8")
    json_path.write_text(json.dumps(draft, indent=2), encoding="utf-8")

    return AutobiographerPublishYearNoteResponse(
        year=payload.year,
        slug=slug,
        title=title,
        markdown_path=str(markdown_path),
        json_path=str(json_path),
        summary=str(chapter_row["summary"]).strip(),
        updated_at=now,
    )
