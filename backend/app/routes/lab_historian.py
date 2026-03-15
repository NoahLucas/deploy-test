from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.models import (
    AutobiographerMemoryEventItem,
    HistorianExtractMemoriesRequest,
    HistorianExtractMemoriesResponse,
    HistorianInterviewGenerateRequest,
    HistorianInterviewGenerateResponse,
    HistorianInterviewQuestionItem,
    HistorianInterviewSessionCreateRequest,
    HistorianInterviewSessionDetailResponse,
    HistorianInterviewSessionItem,
    HistorianInterviewSessionsResponse,
    HistorianInterviewTurnCreateRequest,
    HistorianInterviewTurnItem,
    HistorianMemoryLeadItem,
)
from app.routes.deps import require_admin
from app.routes.errors import bad_gateway, service_unavailable
from app.routes.lab_autobiographer import _as_dt, _to_memory_item

router = APIRouter()


def _to_session_item(row: dict) -> HistorianInterviewSessionItem:
    return HistorianInterviewSessionItem(
        id=row["id"],
        title=row["title"],
        objective=row["objective"],
        start_year=row.get("start_year"),
        end_year=row.get("end_year"),
        created_at=_as_dt(row["created_at"]),
        updated_at=_as_dt(row["updated_at"]),
    )


def _to_turn_item(row: dict) -> HistorianInterviewTurnItem:
    return HistorianInterviewTurnItem(
        id=row["id"],
        session_id=row["session_id"],
        speaker=row["speaker"],
        content=row["content"],
        created_at=_as_dt(row["created_at"]),
    )


@router.post("/lab/historian/sessions", response_model=HistorianInterviewSessionItem)
def create_historian_session(
    payload: HistorianInterviewSessionCreateRequest,
    request: Request,
) -> HistorianInterviewSessionItem:
    require_admin(request)
    store = request.app.state.store
    session_id = store.create_historian_interview_session(
        title=payload.title,
        objective=payload.objective,
        start_year=payload.start_year,
        end_year=payload.end_year,
    )
    row = store.get_historian_interview_session(session_id=session_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create historian session.")
    return _to_session_item(row)


@router.get("/lab/historian/sessions", response_model=HistorianInterviewSessionsResponse)
def list_historian_sessions(request: Request) -> HistorianInterviewSessionsResponse:
    require_admin(request)
    rows = request.app.state.store.list_historian_interview_sessions(limit=50)
    return HistorianInterviewSessionsResponse(items=[_to_session_item(row) for row in rows])


@router.get("/lab/historian/sessions/{session_id}", response_model=HistorianInterviewSessionDetailResponse)
def get_historian_session(session_id: int, request: Request) -> HistorianInterviewSessionDetailResponse:
    require_admin(request)
    store = request.app.state.store
    session = store.get_historian_interview_session(session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historian session not found.")
    turns = store.list_historian_interview_turns(session_id=session_id, limit=300)
    return HistorianInterviewSessionDetailResponse(
        session=_to_session_item(session),
        turns=[_to_turn_item(turn) for turn in turns],
    )


@router.post("/lab/historian/sessions/{session_id}/turns", response_model=HistorianInterviewTurnItem)
def add_historian_turn(
    session_id: int,
    payload: HistorianInterviewTurnCreateRequest,
    request: Request,
) -> HistorianInterviewTurnItem:
    require_admin(request)
    store = request.app.state.store
    session = store.get_historian_interview_session(session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historian session not found.")
    turn_id = store.add_historian_interview_turn(
        session_id=session_id,
        speaker=payload.speaker.strip().lower(),
        content=payload.content.strip(),
    )
    turn = next(
        (row for row in store.list_historian_interview_turns(session_id=session_id, limit=300) if row["id"] == turn_id),
        None,
    )
    if turn is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Historian turn not found after save.")
    return _to_turn_item(turn)


@router.post("/lab/historian/sessions/{session_id}/generate", response_model=HistorianInterviewGenerateResponse)
def generate_historian_turn(
    session_id: int,
    payload: HistorianInterviewGenerateRequest,
    request: Request,
) -> HistorianInterviewGenerateResponse:
    require_admin(request)
    store = request.app.state.store
    session = store.get_historian_interview_session(session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historian session not found.")

    turns = store.list_historian_interview_turns(session_id=session_id, limit=120)
    memory_events = store.list_autobiographer_memory_events(limit=250)
    year_chapters = store.list_autobiographer_chapters(limit=20)

    try:
        generated = request.app.state.openai_service.generate_historian_interview_turn(
            session=session,
            turns=turns,
            memory_events=memory_events,
            year_chapters=year_chapters,
            max_questions=payload.max_questions,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("Historian generation error", exc) from exc

    if not generated:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Historian output was empty.")

    opening = str(generated.get("opening", "")).strip()
    questions_raw = generated.get("questions", [])
    missing_periods_raw = generated.get("missing_periods", [])
    leads_raw = generated.get("memory_leads", [])
    if not opening or not isinstance(questions_raw, list):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Historian output schema invalid.")

    assistant_turn_id = store.add_historian_interview_turn(
        session_id=session_id,
        speaker="assistant",
        content=opening + ("\n\n" + "\n".join(f"- {str(item.get('question', '')).strip()}" for item in questions_raw if isinstance(item, dict)) if questions_raw else ""),
    )
    assistant_turn = next(
        (row for row in store.list_historian_interview_turns(session_id=session_id, limit=300) if row["id"] == assistant_turn_id),
        None,
    )
    if assistant_turn is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Generated historian turn not found after save.")

    questions = [
        HistorianInterviewQuestionItem(
            question=str(item.get("question", "")).strip(),
            why_this_matters=str(item.get("why_this_matters", "")).strip(),
            target_years=[int(year) for year in item.get("target_years", []) if isinstance(year, int)],
            follow_if_answered=str(item.get("follow_if_answered", "")).strip() or None,
        )
        for item in questions_raw
        if isinstance(item, dict) and str(item.get("question", "")).strip()
    ]
    missing_periods = [str(item).strip() for item in missing_periods_raw if str(item).strip()]
    memory_leads = [
        HistorianMemoryLeadItem(
            title=str(item.get("title", "")).strip(),
            detail=str(item.get("detail", "")).strip(),
            year=int(item["year"]) if isinstance(item.get("year"), int) else None,
            tags=[str(tag) for tag in item.get("tags", []) if str(tag).strip()],
            people=[str(person) for person in item.get("people", []) if str(person).strip()],
            place_label=str(item.get("place_label", "")).strip() or None,
            confidence=str(item.get("confidence", "low")).strip() or "low",
        )
        for item in leads_raw
        if isinstance(item, dict) and str(item.get("title", "")).strip() and str(item.get("detail", "")).strip()
    ]

    return HistorianInterviewGenerateResponse(
        session=_to_session_item(store.get_historian_interview_session(session_id=session_id) or session),
        assistant_turn=_to_turn_item(assistant_turn),
        questions=questions,
        missing_periods=missing_periods,
        memory_leads=memory_leads,
    )


@router.post("/lab/historian/sessions/{session_id}/extract-memories", response_model=HistorianExtractMemoriesResponse)
def extract_historian_memories(
    session_id: int,
    payload: HistorianExtractMemoriesRequest,
    request: Request,
) -> HistorianExtractMemoriesResponse:
    require_admin(request)
    store = request.app.state.store
    session = store.get_historian_interview_session(session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historian session not found.")

    turns = store.list_historian_interview_turns(session_id=session_id, limit=500)
    selected = [turn for turn in turns if turn["id"] in set(payload.turn_ids) and turn["speaker"] == "user"]
    created_items: list[AutobiographerMemoryEventItem] = []
    for turn in selected:
        content = str(turn["content"]).strip()
        if not content:
            continue
        title = content.split("\n", 1)[0].strip()[:120] or f"Historian interview memory {turn['id']}"
        event_id = store.create_autobiographer_memory_event(
            source="historian-interview",
            title=title,
            detail=content,
            tags_json=json.dumps(["historian-backfill", "interview"]),
            people_json="[]",
            place_label="",
            privacy_level="private",
            review_state="candidate",
            source_kind="historian_interview",
            source_metadata_json=json.dumps({"session_id": session_id, "turn_id": turn["id"]}),
            event_at=_as_dt(turn["created_at"]).astimezone(timezone.utc).isoformat(),
        )
        row = next((item for item in store.list_autobiographer_memory_events(limit=20) if item["id"] == event_id), None)
        if row is not None:
            created_items.append(_to_memory_item(row))

    return HistorianExtractMemoriesResponse(created_events=created_items)
