from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status

from app.models import (
    NoteIdea,
    NotesDraftRequest,
    NotesDraftResponse,
    NotesIdeationRequest,
    NotesIdeationResponse,
    NotesPipelineRequest,
    NotesPipelineResponse,
    NotesSaveRequest,
    NotesSaveResponse,
)
from app.routes.deps import require_admin
from app.routes.errors import bad_gateway, service_unavailable

router = APIRouter()


def _safe_subdir(raw: str) -> str:
    cleaned = "".join(ch for ch in raw.lower() if ch.isalnum() or ch in {"-", "_"})
    return cleaned or "notes-drafts"


def write_draft_to_disk(request: Request, payload: NotesSaveRequest) -> NotesSaveResponse:
    draft = payload.draft
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = "".join(ch for ch in draft.slug.lower() if ch.isalnum() or ch == "-").strip("-")
    if not slug:
        slug = f"note-{now}"

    project_root: Path = request.app.state.settings.project_root
    target_dir = project_root / "content" / _safe_subdir(payload.subdir)
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"{now}-{slug}"
    markdown_path = target_dir / f"{base_name}.md"
    json_path = target_dir / f"{base_name}.json"

    front_matter = [
        "---",
        f"title: {json.dumps(draft.title)}",
        f"slug: {json.dumps(draft.slug)}",
        f"summary: {json.dumps(draft.summary)}",
        f"meta_title: {json.dumps(draft.meta_title)}",
        f"meta_description: {json.dumps(draft.meta_description)}",
        "---",
        "",
    ]
    markdown_path.write_text("\n".join(front_matter) + draft.body_markdown.strip() + "\n", encoding="utf-8")
    json_path.write_text(draft.model_dump_json(indent=2), encoding="utf-8")

    return NotesSaveResponse(markdown_path=str(markdown_path), json_path=str(json_path))


def _generate_ideas(request: Request, payload: NotesIdeationRequest) -> list[NoteIdea]:
    store = request.app.state.store
    memory = store.list_editorial_memory(limit=24)
    try:
        generated = request.app.state.openai_service.generate_notes_ideas(
            context=payload.context,
            count=payload.count,
            memory=memory,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("OpenAI ideation error", exc) from exc

    if not generated or not isinstance(generated.get("ideas"), list):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI ideation output was invalid.")

    ideas: list[NoteIdea] = []
    for raw_idea in generated["ideas"]:
        try:
            ideas.append(NoteIdea.model_validate(raw_idea))
        except Exception:
            continue
    if not ideas:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No valid ideas returned.")
    return ideas


def _generate_draft(request: Request, *, brief: str, target_words: int) -> NotesDraftResponse:
    store = request.app.state.store
    memory = store.list_editorial_memory(limit=24)
    try:
        generated = request.app.state.openai_service.generate_note_draft(
            brief=brief,
            target_words=target_words,
            memory=memory,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("OpenAI draft error", exc) from exc

    if not generated:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI draft output was invalid.")
    try:
        return NotesDraftResponse.model_validate(generated)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI draft schema validation failed: {exc}",
        ) from exc


@router.post("/openai/notes/ideate", response_model=NotesIdeationResponse)
def ideate_notes(payload: NotesIdeationRequest, request: Request) -> NotesIdeationResponse:
    require_admin(request)
    return NotesIdeationResponse(ideas=_generate_ideas(request, payload)[: payload.count])


@router.post("/openai/notes/draft", response_model=NotesDraftResponse)
def draft_note(payload: NotesDraftRequest, request: Request) -> NotesDraftResponse:
    require_admin(request)
    return _generate_draft(request, brief=payload.brief, target_words=payload.target_words)


@router.post("/openai/notes/save", response_model=NotesSaveResponse)
def save_note_draft(payload: NotesSaveRequest, request: Request) -> NotesSaveResponse:
    require_admin(request)
    return write_draft_to_disk(request, payload)


@router.post("/openai/notes/pipeline", response_model=NotesPipelineResponse)
def run_notes_pipeline(payload: NotesPipelineRequest, request: Request) -> NotesPipelineResponse:
    require_admin(request)

    ideas = _generate_ideas(
        request,
        NotesIdeationRequest(context=payload.context, count=payload.count),
    )
    index = min(payload.draft_idea_index, len(ideas) - 1)
    selected = ideas[index]
    selected_brief = (
        f"Title: {selected.title}\n"
        f"Thesis: {selected.thesis}\n"
        f"Why now: {selected.why_now}\n"
        f"Format: {selected.format}\n"
        "Outline:\n- " + "\n- ".join(selected.outline)
    )

    draft = _generate_draft(request, brief=selected_brief, target_words=payload.target_words)
    saved = None
    if payload.save_to_disk:
        saved = write_draft_to_disk(request, NotesSaveRequest(draft=draft, subdir=payload.subdir))

    return NotesPipelineResponse(
        ideas=ideas[: payload.count],
        selected_brief=selected_brief,
        draft=draft,
        saved=saved,
    )
