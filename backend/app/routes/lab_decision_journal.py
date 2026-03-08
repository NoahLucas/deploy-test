from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status

from app.models import DecisionJournalEntry, DecisionJournalEntryCreateRequest, DecisionJournalListResponse
from app.routes.deps import require_admin

router = APIRouter()


@router.post("/lab/decision-journal", response_model=DecisionJournalEntry)
def create_decision_journal_entry(payload: DecisionJournalEntryCreateRequest, request: Request) -> DecisionJournalEntry:
    require_admin(request)
    store = request.app.state.store
    row_id = store.create_decision_journal_entry(
        title=payload.title,
        context=payload.context,
        options_json=json.dumps(payload.options),
        chosen_option=payload.chosen_option,
        rationale=payload.rationale,
        follow_up_date=payload.follow_up_date,
    )
    row = store.get_decision_journal_entry(row_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist decision entry.")

    return DecisionJournalEntry(
        id=row_id,
        title=row["title"],
        context=row["context"],
        options=[str(opt) for opt in json.loads(row["options_json"])],
        chosen_option=row["chosen_option"],
        rationale=row["rationale"],
        follow_up_date=row["follow_up_date"] or None,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


@router.get("/lab/decision-journal", response_model=DecisionJournalListResponse)
def list_decision_journal_entries(request: Request) -> DecisionJournalListResponse:
    require_admin(request)
    rows = request.app.state.store.list_decision_journal_entries(limit=60)
    items = [
        DecisionJournalEntry(
            id=row["id"],
            title=row["title"],
            context=row["context"],
            options=[str(opt) for opt in json.loads(row["options_json"])],
            chosen_option=row["chosen_option"],
            rationale=row["rationale"],
            follow_up_date=row["follow_up_date"] or None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
        for row in rows
    ]
    return DecisionJournalListResponse(items=items)
