from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Request

from app.models import LabWeeklySnapshotResponse
from app.routes.deps import require_admin

router = APIRouter()


@router.get("/lab/weekly-snapshot", response_model=LabWeeklySnapshotResponse)
def lab_weekly_snapshot(request: Request) -> LabWeeklySnapshotResponse:
    require_admin(request)
    store = request.app.state.store
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    since_iso = since.isoformat()

    project_root: Path = request.app.state.settings.project_root
    drafts_dir = project_root / "content" / "notes-drafts"
    notes_drafts_generated = 0
    if drafts_dir.exists():
        notes_drafts_generated = len(list(drafts_dir.glob("*.md")))

    decision_entries_created = store.count_decision_journal_entries_since(since_iso=since_iso)
    squarespace_events_received = store.count_squarespace_events_since(since_iso=since_iso)
    agent_runs_created = store.count_agent_runs_since(since_iso=since_iso)
    agent_runs_completed = store.count_agent_runs_since(since_iso=since_iso, status="completed")

    averages = store.averaged_signals(days=7)
    recovery = float(averages.get("recovery", 0.0))
    focus = float(averages.get("focus", 0.0))
    balance = float(averages.get("balance", 0.0))
    action = float(averages.get("action", 0.0))

    summary = (
        f"7d snapshot: {agent_runs_completed}/{agent_runs_created} agent runs completed, "
        f"{decision_entries_created} decisions logged, {notes_drafts_generated} note drafts available, "
        f"{squarespace_events_received} Squarespace events captured."
    )

    return LabWeeklySnapshotResponse(
        window_days=7,
        summary=summary,
        notes_drafts_generated=notes_drafts_generated,
        decision_entries_created=decision_entries_created,
        squarespace_events_received=squarespace_events_received,
        agent_runs_created=agent_runs_created,
        agent_runs_completed=agent_runs_completed,
        signal_recovery_avg=recovery,
        signal_focus_avg=focus,
        signal_balance_avg=balance,
        signal_action_avg=action,
        generated_at=now,
    )
