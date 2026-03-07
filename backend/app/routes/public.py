from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status

from app.core.sanitizer import default_action, default_headline, derive_public_scores
from app.models import (
    FeedMetrics,
    PublicFeedResponse,
    PublicNoteDetailResponse,
    PublicNotesResponse,
    PublicNoteSummary,
)

router = APIRouter()


def _draft_files(project_root: Path, limit: int = 24) -> list[Path]:
    notes_dir = project_root / "content" / "notes-drafts"
    if not notes_dir.exists():
        return []
    files = sorted(notes_dir.glob("*.json"), reverse=True)
    return files[: max(1, min(limit, 100))]


def _read_draft(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/feed", response_model=PublicFeedResponse)
def get_public_feed(request: Request) -> PublicFeedResponse:
    store = request.app.state.store
    cached = store.get_public_feed()

    if cached:
        updated_at = datetime.fromisoformat(cached["updated_at"])
        return PublicFeedResponse(
            headline=cached["headline"],
            metrics=FeedMetrics(
                recovery=cached["recovery"],
                focus=cached["focus"],
                balance=cached["balance"],
                action=cached["action"],
            ),
            updated_at=updated_at,
        )

    averages = store.averaged_signals(days=7)
    scores = derive_public_scores(averages)

    return PublicFeedResponse(
        headline=default_headline(scores),
        metrics=FeedMetrics(
            recovery=f"{scores['recovery']}/100",
            focus=f"{scores['focus']}/100",
            balance=f"{scores['balance']}/100",
            action=default_action(scores),
        ),
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/notes-drafts", response_model=PublicNotesResponse)
def get_public_note_drafts(request: Request) -> PublicNotesResponse:
    project_root: Path = request.app.state.settings.project_root
    items: list[PublicNoteSummary] = []
    for file_path in _draft_files(project_root, limit=24):
        try:
            raw = _read_draft(file_path)
            items.append(
                PublicNoteSummary(
                    title=str(raw["title"]),
                    slug=str(raw["slug"]),
                    summary=str(raw["summary"]),
                    generated_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                )
            )
        except Exception:
            continue

    return PublicNotesResponse(items=items)


@router.get("/notes-drafts/{slug}", response_model=PublicNoteDetailResponse)
def get_public_note_draft_detail(slug: str, request: Request) -> PublicNoteDetailResponse:
    project_root: Path = request.app.state.settings.project_root
    slug = slug.strip().lower()
    if not slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    for file_path in _draft_files(project_root, limit=100):
        try:
            raw = _read_draft(file_path)
        except Exception:
            continue
        if str(raw.get("slug", "")).strip().lower() != slug:
            continue
        try:
            return PublicNoteDetailResponse(
                title=str(raw["title"]),
                slug=str(raw["slug"]),
                summary=str(raw["summary"]),
                body_markdown=str(raw["body_markdown"]),
                meta_title=str(raw["meta_title"]),
                meta_description=str(raw["meta_description"]),
                social_quotes=[str(q) for q in raw.get("social_quotes", [])][:3],
                generated_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
            )
        except Exception:
            break

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
