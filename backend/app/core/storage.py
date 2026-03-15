from __future__ import annotations

import ast
import base64
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional


class SignalStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ingested_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    signal_key TEXT NOT NULL,
                    value REAL NOT NULL,
                    collected_at TEXT NOT NULL,
                    inserted_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ingested_day_key
                ON ingested_signals(day, signal_key)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS public_feed (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    day TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    recovery TEXT NOT NULL,
                    focus TEXT NOT NULL,
                    balance TEXT NOT NULL,
                    action TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS editorial_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme TEXT NOT NULL UNIQUE,
                    notes TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    context TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    chosen_option TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    follow_up_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_attest_challenges (
                    challenge TEXT PRIMARY KEY,
                    device_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS apple_device_trust (
                    device_hash TEXT PRIMARY KEY,
                    key_id TEXT NOT NULL,
                    bundle_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    verified_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS endpoint_toggles (
                    path TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS squarespace_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    website_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission TEXT NOT NULL,
                    context TEXT NOT NULL,
                    status TEXT NOT NULL,
                    planner_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    output TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES agent_runs(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autobiographer_memory_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    people_json TEXT NOT NULL DEFAULT '[]',
                    place_label TEXT,
                    privacy_level TEXT NOT NULL DEFAULT 'private',
                    review_state TEXT NOT NULL DEFAULT 'accepted',
                    source_kind TEXT NOT NULL DEFAULT 'manual',
                    joy_score REAL,
                    family_relevance_score REAL,
                    importance_score REAL,
                    source_metadata_json TEXT NOT NULL DEFAULT '{}',
                    event_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_autobio_events_event_at
                ON autobiographer_memory_events(event_at DESC)
                """
            )
            for statement in (
                "ALTER TABLE autobiographer_memory_events ADD COLUMN people_json TEXT NOT NULL DEFAULT '[]'",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN place_label TEXT",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN privacy_level TEXT NOT NULL DEFAULT 'private'",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN review_state TEXT NOT NULL DEFAULT 'accepted'",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN source_kind TEXT NOT NULL DEFAULT 'manual'",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN joy_score REAL",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN family_relevance_score REAL",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN importance_score REAL",
                "ALTER TABLE autobiographer_memory_events ADD COLUMN source_metadata_json TEXT NOT NULL DEFAULT '{}'",
            ):
                try:
                    conn.execute(statement)
                except sqlite3.OperationalError:
                    pass
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autobiographer_chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL UNIQUE,
                    persona_label TEXT NOT NULL,
                    style_brief TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    chapter_markdown TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autobiographer_monthly_chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    persona_label TEXT NOT NULL,
                    style_brief TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    chapter_markdown TEXT NOT NULL,
                    status TEXT NOT NULL,
                    locked_at TEXT,
                    generated_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(year, month)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_autobio_monthly_year_month
                ON autobiographer_monthly_chapters(year, month)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autobiographer_memory_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    source TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    uri TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES autobiographer_memory_events(id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_autobio_artifacts_event_id
                ON autobiographer_memory_artifacts(event_id, captured_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autobiographer_scene_clusters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    place_label TEXT,
                    people_json TEXT NOT NULL,
                    themes_json TEXT NOT NULL,
                    event_ids_json TEXT NOT NULL,
                    start_at TEXT NOT NULL,
                    end_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_autobio_scene_year
                ON autobiographer_scene_clusters(year, start_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autobiographer_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    title TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    body_markdown TEXT NOT NULL,
                    source_job_id INTEGER,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_autobio_revision_year
                ON autobiographer_revisions(year, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autobiographer_revision_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    error_text TEXT,
                    revision_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_autobio_revision_job_year
                ON autobiographer_revision_jobs(year, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS historian_interview_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    start_year INTEGER,
                    end_year INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS historian_interview_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    speaker TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES historian_interview_sessions(id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_historian_turns_session
                ON historian_interview_turns(session_id, created_at ASC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_webauthn_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    credential_id TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    public_key_b64 TEXT NOT NULL DEFAULT '',
                    sign_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT
                )
                """
            )
            for statement in (
                "ALTER TABLE admin_webauthn_credentials ADD COLUMN public_key_b64 TEXT NOT NULL DEFAULT ''",
                "ALTER TABLE admin_webauthn_credentials ADD COLUMN sign_count INTEGER NOT NULL DEFAULT 0",
            ):
                try:
                    conn.execute(statement)
                except sqlite3.OperationalError:
                    pass
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_auth_challenges (
                    challenge_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    challenge_b64 TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_auth_sessions (
                    session_id TEXT PRIMARY KEY,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    revoked_at TEXT
                )
                """
            )

    def insert_sanitized_signals(
        self,
        day: str,
        source_hash: str,
        collected_at: str,
        signals: Dict[str, float],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        rows: List[tuple] = [
            (day, source_hash, key, value, collected_at, now)
            for key, value in signals.items()
        ]

        with self._lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO ingested_signals(day, source_hash, signal_key, value, collected_at, inserted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def averaged_signals(self, days: int = 7) -> Dict[str, float]:
        since = (date.today() - timedelta(days=max(days - 1, 0))).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT signal_key, AVG(value) AS avg_value
                FROM ingested_signals
                WHERE day >= ?
                GROUP BY signal_key
                """,
                (since,),
            ).fetchall()
        return {str(row["signal_key"]): float(row["avg_value"]) for row in rows}

    def save_public_feed(
        self,
        day: str,
        headline: str,
        recovery: str,
        focus: str,
        balance: str,
        action: str,
        updated_at: datetime,
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO public_feed (id, day, headline, recovery, focus, balance, action, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    day = excluded.day,
                    headline = excluded.headline,
                    recovery = excluded.recovery,
                    focus = excluded.focus,
                    balance = excluded.balance,
                    action = excluded.action,
                    updated_at = excluded.updated_at
                """,
                (
                    day,
                    headline,
                    recovery,
                    focus,
                    balance,
                    action,
                    updated_at.isoformat(),
                ),
            )

    def get_public_feed(self) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM public_feed WHERE id = 1").fetchone()

        if row is None:
            return None

        return {
            "headline": str(row["headline"]),
            "recovery": str(row["recovery"]),
            "focus": str(row["focus"]),
            "balance": str(row["balance"]),
            "action": str(row["action"]),
            "updated_at": str(row["updated_at"]),
        }

    def upsert_editorial_memory(self, theme: str, notes: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO editorial_memory(theme, notes, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(theme) DO UPDATE SET
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (theme.strip(), notes.strip(), now),
            )

    def list_editorial_memory(self, limit: int = 24) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, theme, notes, updated_at
                FROM editorial_memory
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

        output: List[Dict[str, str]] = []
        for row in rows:
            output.append(
                {
                    "id": int(row["id"]),
                    "theme": str(row["theme"]),
                    "notes": str(row["notes"]),
                    "updated_at": str(row["updated_at"]),
                }
            )
        return output

    def create_decision_journal_entry(
        self,
        *,
        title: str,
        context: str,
        options_json: str,
        chosen_option: str,
        rationale: str,
        follow_up_date: Optional[str],
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO decision_journal(
                    title, context, options_json, chosen_option, rationale, follow_up_date, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, context, options_json, chosen_option, rationale, follow_up_date, now, now),
            )
            return int(cursor.lastrowid)

    def list_decision_journal_entries(self, limit: int = 50) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, context, options_json, chosen_option, rationale, follow_up_date, created_at, updated_at
                FROM decision_journal
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "title": str(row["title"]),
                "context": str(row["context"]),
                "options_json": str(row["options_json"]),
                "chosen_option": str(row["chosen_option"]),
                "rationale": str(row["rationale"]),
                "follow_up_date": str(row["follow_up_date"]) if row["follow_up_date"] is not None else "",
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def get_decision_journal_entry(self, entry_id: int) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, title, context, options_json, chosen_option, rationale, follow_up_date, created_at, updated_at
                FROM decision_journal
                WHERE id = ?
                """,
                (entry_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "title": str(row["title"]),
            "context": str(row["context"]),
            "options_json": str(row["options_json"]),
            "chosen_option": str(row["chosen_option"]),
            "rationale": str(row["rationale"]),
            "follow_up_date": str(row["follow_up_date"]) if row["follow_up_date"] is not None else "",
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def create_app_attest_challenge(self, *, challenge: str, device_hash: str, expires_at: datetime) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO app_attest_challenges(challenge, device_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (challenge, device_hash, expires_at.isoformat(), now),
            )

    def consume_app_attest_challenge(self, *, challenge: str, device_hash: str) -> bool:
        now = datetime.now(timezone.utc)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT challenge, device_hash, expires_at, used_at
                FROM app_attest_challenges
                WHERE challenge = ?
                """,
                (challenge,),
            ).fetchone()
            if row is None:
                return False
            if str(row["device_hash"]) != device_hash:
                return False
            if row["used_at"] is not None:
                return False
            try:
                expires_at = datetime.fromisoformat(str(row["expires_at"]))
            except Exception:
                return False
            if now > expires_at:
                return False

            conn.execute(
                """
                UPDATE app_attest_challenges
                SET used_at = ?
                WHERE challenge = ?
                """,
                (now.isoformat(), challenge),
            )
            return True

    def upsert_apple_device_trust(self, *, device_hash: str, key_id: str, bundle_id: str, mode: str) -> None:
        verified_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO apple_device_trust(device_hash, key_id, bundle_id, mode, verified_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(device_hash) DO UPDATE SET
                    key_id = excluded.key_id,
                    bundle_id = excluded.bundle_id,
                    mode = excluded.mode,
                    verified_at = excluded.verified_at
                """,
                (device_hash, key_id, bundle_id, mode, verified_at),
            )

    def set_endpoint_toggle(self, *, path: str, platform: str, enabled: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO endpoint_toggles(path, platform, enabled, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    platform = excluded.platform,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (path, platform, 1 if enabled else 0, now),
            )

    def list_endpoint_toggles(self) -> Dict[str, Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT path, platform, enabled, updated_at
                FROM endpoint_toggles
                """
            ).fetchall()
        output: Dict[str, Dict[str, str]] = {}
        for row in rows:
            output[str(row["path"])] = {
                "platform": str(row["platform"]),
                "enabled": "true" if int(row["enabled"]) == 1 else "false",
                "updated_at": str(row["updated_at"]),
            }
        return output

    def insert_squarespace_event(
        self,
        *,
        event_id: str,
        event_type: str,
        website_id: str,
        created_at: str,
        payload_json: str,
    ) -> None:
        received_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO squarespace_events(
                    event_id, event_type, website_id, created_at, received_at, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, event_type, website_id, created_at, received_at, payload_json),
            )

    def list_squarespace_events(self, limit: int = 50) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_id, event_type, website_id, created_at, received_at
                FROM squarespace_events
                ORDER BY received_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "event_id": str(row["event_id"]),
                "event_type": str(row["event_type"]),
                "website_id": str(row["website_id"]),
                "created_at": str(row["created_at"]),
                "received_at": str(row["received_at"]),
            }
            for row in rows
        ]

    def create_agent_run(
        self,
        *,
        mission: str,
        context: str,
        status: str,
        planner_summary: str,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO agent_runs(mission, context, status, planner_summary, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (mission, context, status, planner_summary, now, now),
            )
            return int(cursor.lastrowid)

    def add_agent_task(
        self,
        *,
        run_id: int,
        role: str,
        objective: str,
        status: str,
        priority: int,
        output: str = "",
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO agent_tasks(run_id, role, objective, status, priority, output, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, role, objective, status, priority, output, now, now),
            )
            return int(cursor.lastrowid)

    def update_agent_task(self, *, task_id: int, status: str, output: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE agent_tasks
                SET status = ?, output = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, output, now, task_id),
            )

    def update_agent_run_status(self, *, run_id: int, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE agent_runs
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, run_id),
            )

    def list_agent_runs(self, limit: int = 50) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, mission, context, status, planner_summary, created_at, updated_at
                FROM agent_runs
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "mission": str(row["mission"]),
                "context": str(row["context"]),
                "status": str(row["status"]),
                "planner_summary": str(row["planner_summary"]),
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def get_agent_run(self, run_id: int) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, mission, context, status, planner_summary, created_at, updated_at
                FROM agent_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "mission": str(row["mission"]),
            "context": str(row["context"]),
            "status": str(row["status"]),
            "planner_summary": str(row["planner_summary"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def list_agent_tasks(self, *, run_id: int) -> List[Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, run_id, role, objective, status, priority, output, created_at, updated_at
                FROM agent_tasks
                WHERE run_id = ?
                ORDER BY priority DESC, id ASC
                """,
                (run_id,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "run_id": int(row["run_id"]),
                "role": str(row["role"]),
                "objective": str(row["objective"]),
                "status": str(row["status"]),
                "priority": int(row["priority"]),
                "output": str(row["output"]) if row["output"] is not None else "",
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def count_decision_journal_entries_since(self, *, since_iso: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count_value
                FROM decision_journal
                WHERE created_at >= ?
                """,
                (since_iso,),
            ).fetchone()
        return int(row["count_value"]) if row else 0

    def count_squarespace_events_since(self, *, since_iso: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count_value
                FROM squarespace_events
                WHERE received_at >= ?
                """,
                (since_iso,),
            ).fetchone()
        return int(row["count_value"]) if row else 0

    def count_agent_runs_since(self, *, since_iso: str, status: Optional[str] = None) -> int:
        with self._connect() as conn:
            if status:
                row = conn.execute(
                    """
                    SELECT COUNT(*) AS count_value
                    FROM agent_runs
                    WHERE created_at >= ? AND status = ?
                    """,
                    (since_iso, status),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT COUNT(*) AS count_value
                    FROM agent_runs
                    WHERE created_at >= ?
                    """,
                    (since_iso,),
                ).fetchone()
        return int(row["count_value"]) if row else 0

    def create_autobiographer_memory_event(
        self,
        *,
        source: str,
        title: str,
        detail: str,
        tags_json: str,
        people_json: str = "[]",
        place_label: str = "",
        privacy_level: str = "private",
        review_state: str = "accepted",
        source_kind: str = "manual",
        joy_score: Optional[float] = None,
        family_relevance_score: Optional[float] = None,
        importance_score: Optional[float] = None,
        source_metadata_json: str = "{}",
        event_at: str,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO autobiographer_memory_events(
                    source, title, detail, tags_json, people_json, place_label,
                    privacy_level, review_state, source_kind, joy_score,
                    family_relevance_score, importance_score, source_metadata_json, event_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    title,
                    detail,
                    tags_json,
                    people_json,
                    place_label,
                    privacy_level,
                    review_state,
                    source_kind,
                    joy_score,
                    family_relevance_score,
                    importance_score,
                    source_metadata_json,
                    event_at,
                    created_at,
                ),
            )
            return int(cursor.lastrowid)

    def update_autobiographer_memory_review_state(self, *, event_ids: List[int], review_state: str) -> int:
        if not event_ids:
            return 0
        now = datetime.now(timezone.utc).isoformat()
        placeholders = ", ".join("?" for _ in event_ids)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"""
                UPDATE autobiographer_memory_events
                SET review_state = ?, source_metadata_json = source_metadata_json, created_at = created_at
                WHERE id IN ({placeholders})
                """,
                [review_state] + event_ids,
            )
            conn.execute("SELECT ?", (now,))
            return int(cursor.rowcount or 0)

    def update_autobiographer_memory_privacy_level(self, *, event_ids: List[int], privacy_level: str) -> int:
        if not event_ids:
            return 0
        placeholders = ", ".join("?" for _ in event_ids)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"""
                UPDATE autobiographer_memory_events
                SET privacy_level = ?, source_metadata_json = source_metadata_json, created_at = created_at
                WHERE id IN ({placeholders})
                """,
                [privacy_level] + event_ids,
            )
            return int(cursor.rowcount or 0)

    def list_autobiographer_memory_events(
        self,
        *,
        limit: int = 120,
        year: Optional[int] = None,
        review_state: Optional[str] = None,
        privacy_level: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            where_clauses: List[str] = []
            params: List[object] = []
            if year is not None:
                start = f"{year:04d}-01-01T00:00:00"
                end = f"{year + 1:04d}-01-01T00:00:00"
                where_clauses.append("event_at >= ? AND event_at < ?")
                params.extend([start, end])
            if review_state:
                where_clauses.append("review_state = ?")
                params.append(review_state)
            if privacy_level:
                where_clauses.append("privacy_level = ?")
                params.append(privacy_level)
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            params.append(safe_limit)
            rows = conn.execute(
                f"""
                SELECT id, source, title, detail, tags_json, people_json, place_label, privacy_level,
                       review_state, source_kind, joy_score, family_relevance_score, importance_score,
                       source_metadata_json, event_at, created_at
                FROM autobiographer_memory_events
                {where_sql}
                ORDER BY event_at DESC, id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "source": str(row["source"]),
                "title": str(row["title"]),
                "detail": str(row["detail"]),
                "tags_json": str(row["tags_json"]),
                "people_json": str(row["people_json"]),
                "place_label": str(row["place_label"]) if row["place_label"] is not None else "",
                "privacy_level": str(row["privacy_level"]),
                "review_state": str(row["review_state"]),
                "source_kind": str(row["source_kind"]),
                "joy_score": float(row["joy_score"]) if row["joy_score"] is not None else None,
                "family_relevance_score": float(row["family_relevance_score"]) if row["family_relevance_score"] is not None else None,
                "importance_score": float(row["importance_score"]) if row["importance_score"] is not None else None,
                "source_metadata_json": str(row["source_metadata_json"]),
                "event_at": str(row["event_at"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def create_autobiographer_memory_artifact(
        self,
        *,
        event_id: Optional[int],
        source: str,
        artifact_type: str,
        uri: str,
        captured_at: str,
        metadata_json: str,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO autobiographer_memory_artifacts(
                    event_id, source, artifact_type, uri, captured_at, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, source, artifact_type, uri, captured_at, metadata_json, created_at),
            )
            return int(cursor.lastrowid)

    def replace_autobiographer_scene_clusters(self, *, year: int, scenes: List[Dict[str, str]]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM autobiographer_scene_clusters WHERE year = ?", (year,))
            for scene in scenes:
                conn.execute(
                    """
                    INSERT INTO autobiographer_scene_clusters(
                        year, title, summary, place_label, people_json, themes_json, event_ids_json,
                        start_at, end_at, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        year,
                        scene["title"],
                        scene["summary"],
                        scene.get("place_label", ""),
                        scene["people_json"],
                        scene["themes_json"],
                        scene["event_ids_json"],
                        scene["start_at"],
                        scene["end_at"],
                        now,
                        now,
                    ),
                )

    def list_autobiographer_scene_clusters(self, *, year: int, limit: int = 120) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 300))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, year, title, summary, place_label, people_json, themes_json, event_ids_json,
                       start_at, end_at, created_at, updated_at
                FROM autobiographer_scene_clusters
                WHERE year = ?
                ORDER BY start_at DESC, id DESC
                LIMIT ?
                """,
                (year, safe_limit),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "year": int(row["year"]),
                "title": str(row["title"]),
                "summary": str(row["summary"]),
                "place_label": str(row["place_label"]) if row["place_label"] is not None else "",
                "people_json": str(row["people_json"]),
                "themes_json": str(row["themes_json"]),
                "event_ids_json": str(row["event_ids_json"]),
                "start_at": str(row["start_at"]),
                "end_at": str(row["end_at"]),
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def create_autobiographer_revision_job(
        self,
        *,
        year: int,
        mode: str,
        status: str,
        summary: str,
        input_json: str,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO autobiographer_revision_jobs(
                    year, mode, status, summary, input_json, output_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (year, mode, status, summary, input_json, "{}", now, now),
            )
            return int(cursor.lastrowid)

    def complete_autobiographer_revision_job(
        self,
        *,
        job_id: int,
        status: str,
        summary: str,
        output_json: str,
        revision_id: Optional[int] = None,
        error_text: str = "",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE autobiographer_revision_jobs
                SET status = ?, summary = ?, output_json = ?, revision_id = ?, error_text = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, summary, output_json, revision_id, error_text or None, now, now, job_id),
            )

    def list_autobiographer_revision_jobs(self, *, limit: int = 50) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, year, mode, status, summary, error_text, revision_id, created_at, updated_at, completed_at
                FROM autobiographer_revision_jobs
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "year": int(row["year"]),
                "mode": str(row["mode"]),
                "status": str(row["status"]),
                "summary": str(row["summary"]),
                "error_text": str(row["error_text"]) if row["error_text"] is not None else "",
                "revision_id": int(row["revision_id"]) if row["revision_id"] is not None else None,
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
                "completed_at": str(row["completed_at"]) if row["completed_at"] is not None else "",
            }
            for row in rows
        ]

    def get_autobiographer_revision_job(self, *, job_id: int) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, year, mode, status, summary, error_text, revision_id, created_at, updated_at, completed_at
                FROM autobiographer_revision_jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "year": int(row["year"]),
            "mode": str(row["mode"]),
            "status": str(row["status"]),
            "summary": str(row["summary"]),
            "error_text": str(row["error_text"]) if row["error_text"] is not None else "",
            "revision_id": int(row["revision_id"]) if row["revision_id"] is not None else None,
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "completed_at": str(row["completed_at"]) if row["completed_at"] is not None else "",
        }

    def create_autobiographer_revision(
        self,
        *,
        year: int,
        mode: str,
        title: str,
        slug: str,
        summary: str,
        body_markdown: str,
        source_job_id: Optional[int],
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO autobiographer_revisions(
                    year, mode, title, slug, summary, body_markdown, source_job_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (year, mode, title, slug, summary, body_markdown, source_job_id, created_at),
            )
            return int(cursor.lastrowid)

    def list_autobiographer_revisions(self, *, year: int, limit: int = 30) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, year, mode, title, slug, summary, body_markdown, source_job_id, created_at
                FROM autobiographer_revisions
                WHERE year = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (year, safe_limit),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "year": int(row["year"]),
                "mode": str(row["mode"]),
                "title": str(row["title"]),
                "slug": str(row["slug"]),
                "summary": str(row["summary"]),
                "body_markdown": str(row["body_markdown"]),
                "source_job_id": int(row["source_job_id"]) if row["source_job_id"] is not None else None,
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def get_autobiographer_revision(self, *, revision_id: int) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, year, mode, title, slug, summary, body_markdown, source_job_id, created_at
                FROM autobiographer_revisions
                WHERE id = ?
                """,
                (revision_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "year": int(row["year"]),
            "mode": str(row["mode"]),
            "title": str(row["title"]),
            "slug": str(row["slug"]),
            "summary": str(row["summary"]),
            "body_markdown": str(row["body_markdown"]),
            "source_job_id": int(row["source_job_id"]) if row["source_job_id"] is not None else None,
            "created_at": str(row["created_at"]),
        }

    def create_historian_interview_session(
        self,
        *,
        title: str,
        objective: str,
        start_year: Optional[int],
        end_year: Optional[int],
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO historian_interview_sessions(title, objective, start_year, end_year, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (title, objective, start_year, end_year, now, now),
            )
            return int(cursor.lastrowid)

    def list_historian_interview_sessions(self, *, limit: int = 30) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, objective, start_year, end_year, created_at, updated_at
                FROM historian_interview_sessions
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "title": str(row["title"]),
                "objective": str(row["objective"]),
                "start_year": int(row["start_year"]) if row["start_year"] is not None else None,
                "end_year": int(row["end_year"]) if row["end_year"] is not None else None,
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def get_historian_interview_session(self, *, session_id: int) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, title, objective, start_year, end_year, created_at, updated_at
                FROM historian_interview_sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "title": str(row["title"]),
            "objective": str(row["objective"]),
            "start_year": int(row["start_year"]) if row["start_year"] is not None else None,
            "end_year": int(row["end_year"]) if row["end_year"] is not None else None,
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def add_historian_interview_turn(self, *, session_id: int, speaker: str, content: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO historian_interview_turns(session_id, speaker, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, speaker, content, now),
            )
            conn.execute(
                """
                UPDATE historian_interview_sessions
                SET updated_at = ?
                WHERE id = ?
                """,
                (now, session_id),
            )
            return int(cursor.lastrowid)

    def list_historian_interview_turns(self, *, session_id: int, limit: int = 200) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, session_id, speaker, content, created_at
                FROM historian_interview_turns
                WHERE session_id = ?
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                (session_id, safe_limit),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "session_id": int(row["session_id"]),
                "speaker": str(row["speaker"]),
                "content": str(row["content"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def upsert_autobiographer_chapter(
        self,
        *,
        year: int,
        persona_label: str,
        style_brief: str,
        summary: str,
        chapter_markdown: str,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO autobiographer_chapters(
                    year, persona_label, style_brief, summary, chapter_markdown, generated_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(year) DO UPDATE SET
                    persona_label = excluded.persona_label,
                    style_brief = excluded.style_brief,
                    summary = excluded.summary,
                    chapter_markdown = excluded.chapter_markdown,
                    updated_at = excluded.updated_at
                """,
                (year, persona_label, style_brief, summary, chapter_markdown, now, now),
            )
            row = conn.execute(
                """
                SELECT id
                FROM autobiographer_chapters
                WHERE year = ?
                """,
                (year,),
            ).fetchone()
            return int(row["id"]) if row else 0

    def get_autobiographer_chapter_by_year(self, *, year: int) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, year, persona_label, style_brief, summary, chapter_markdown, generated_at, updated_at
                FROM autobiographer_chapters
                WHERE year = ?
                """,
                (year,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "year": int(row["year"]),
            "persona_label": str(row["persona_label"]),
            "style_brief": str(row["style_brief"]),
            "summary": str(row["summary"]),
            "chapter_markdown": str(row["chapter_markdown"]),
            "generated_at": str(row["generated_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def list_autobiographer_chapters(self, *, limit: int = 20) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, year, persona_label, style_brief, summary, chapter_markdown, generated_at, updated_at
                FROM autobiographer_chapters
                ORDER BY year DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "year": int(row["year"]),
                "persona_label": str(row["persona_label"]),
                "style_brief": str(row["style_brief"]),
                "summary": str(row["summary"]),
                "chapter_markdown": str(row["chapter_markdown"]),
                "generated_at": str(row["generated_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def upsert_autobiographer_month_chapter(
        self,
        *,
        year: int,
        month: int,
        persona_label: str,
        style_brief: str,
        summary: str,
        chapter_markdown: str,
        status: str,
        locked_at: Optional[str],
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO autobiographer_monthly_chapters(
                    year, month, persona_label, style_brief, summary, chapter_markdown,
                    status, locked_at, generated_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(year, month) DO UPDATE SET
                    persona_label = excluded.persona_label,
                    style_brief = excluded.style_brief,
                    summary = excluded.summary,
                    chapter_markdown = excluded.chapter_markdown,
                    status = excluded.status,
                    locked_at = excluded.locked_at,
                    updated_at = excluded.updated_at
                """,
                (
                    year,
                    month,
                    persona_label,
                    style_brief,
                    summary,
                    chapter_markdown,
                    status,
                    locked_at,
                    now,
                    now,
                ),
            )
            row = conn.execute(
                """
                SELECT id
                FROM autobiographer_monthly_chapters
                WHERE year = ? AND month = ?
                """,
                (year, month),
            ).fetchone()
            return int(row["id"]) if row else 0

    def get_autobiographer_month_chapter(self, *, year: int, month: int) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, year, month, persona_label, style_brief, summary, chapter_markdown,
                       status, locked_at, generated_at, updated_at
                FROM autobiographer_monthly_chapters
                WHERE year = ? AND month = ?
                """,
                (year, month),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "year": int(row["year"]),
            "month": int(row["month"]),
            "persona_label": str(row["persona_label"]),
            "style_brief": str(row["style_brief"]),
            "summary": str(row["summary"]),
            "chapter_markdown": str(row["chapter_markdown"]),
            "status": str(row["status"]),
            "locked_at": str(row["locked_at"]) if row["locked_at"] is not None else "",
            "generated_at": str(row["generated_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def list_autobiographer_month_chapters(self, *, year: Optional[int] = None, limit: int = 240) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            if year is None:
                rows = conn.execute(
                    """
                    SELECT id, year, month, persona_label, style_brief, summary, chapter_markdown,
                           status, locked_at, generated_at, updated_at
                    FROM autobiographer_monthly_chapters
                    ORDER BY year DESC, month DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, year, month, persona_label, style_brief, summary, chapter_markdown,
                           status, locked_at, generated_at, updated_at
                    FROM autobiographer_monthly_chapters
                    WHERE year = ?
                    ORDER BY month ASC
                    LIMIT ?
                    """,
                    (year, safe_limit),
                ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "year": int(row["year"]),
                "month": int(row["month"]),
                "persona_label": str(row["persona_label"]),
                "style_brief": str(row["style_brief"]),
                "summary": str(row["summary"]),
                "chapter_markdown": str(row["chapter_markdown"]),
                "status": str(row["status"]),
                "locked_at": str(row["locked_at"]) if row["locked_at"] is not None else "",
                "generated_at": str(row["generated_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def save_admin_webauthn_credential(
        self,
        *,
        credential_id: str,
        label: str,
        public_key_b64: str,
        sign_count: int,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO admin_webauthn_credentials(
                    credential_id, label, public_key_b64, sign_count, created_at, last_used_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(credential_id) DO UPDATE SET
                    label = excluded.label,
                    public_key_b64 = excluded.public_key_b64,
                    sign_count = excluded.sign_count
                """,
                (credential_id, label, public_key_b64, int(sign_count), now, now),
            )

    @staticmethod
    def _normalize_admin_credential_id_value(value: str) -> str:
        raw = str(value).strip()
        if not raw:
            return raw
        if (raw.startswith("b'") and raw.endswith("'")) or (raw.startswith('b"') and raw.endswith('"')):
            try:
                parsed = ast.literal_eval(raw)
            except Exception:
                return raw
            if isinstance(parsed, (bytes, bytearray)):
                return base64.urlsafe_b64encode(bytes(parsed)).decode("ascii").rstrip("=")
        return raw

    def normalize_admin_webauthn_credential_ids(self) -> int:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT credential_id
                FROM admin_webauthn_credentials
                """
            ).fetchall()
            updates: list[tuple[str, str]] = []
            for row in rows:
                current = str(row["credential_id"])
                normalized = self._normalize_admin_credential_id_value(current)
                if normalized and normalized != current:
                    updates.append((normalized, current))

            for normalized, current in updates:
                conn.execute(
                    """
                    UPDATE admin_webauthn_credentials
                    SET credential_id = ?
                    WHERE credential_id = ?
                    """,
                    (normalized, current),
                )

        return len(updates)

    def list_admin_webauthn_credentials(self) -> List[Dict[str, str]]:
        self.normalize_admin_webauthn_credential_ids()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT credential_id, label, public_key_b64, sign_count, created_at, last_used_at
                FROM admin_webauthn_credentials
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            {
                "credential_id": self._normalize_admin_credential_id_value(str(row["credential_id"])),
                "label": str(row["label"]),
                "public_key_b64": str(row["public_key_b64"]),
                "sign_count": int(row["sign_count"]),
                "created_at": str(row["created_at"]),
                "last_used_at": str(row["last_used_at"]) if row["last_used_at"] is not None else "",
            }
            for row in rows
        ]

    def get_admin_webauthn_credential(self, *, credential_id: str) -> Optional[Dict[str, str | int]]:
        self.normalize_admin_webauthn_credential_ids()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT credential_id, label, public_key_b64, sign_count, created_at, last_used_at
                FROM admin_webauthn_credentials
                WHERE credential_id = ?
                """,
                (credential_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "credential_id": self._normalize_admin_credential_id_value(str(row["credential_id"])),
            "label": str(row["label"]),
            "public_key_b64": str(row["public_key_b64"]),
            "sign_count": int(row["sign_count"]),
            "created_at": str(row["created_at"]),
            "last_used_at": str(row["last_used_at"]) if row["last_used_at"] is not None else "",
        }

    def has_admin_webauthn_credential(self, *, credential_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM admin_webauthn_credentials
                WHERE credential_id = ?
                """,
                (credential_id,),
            ).fetchone()
        return row is not None

    def mark_admin_webauthn_credential_used(self, *, credential_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE admin_webauthn_credentials
                SET last_used_at = ?
                WHERE credential_id = ?
                """,
                (now, credential_id),
            )

    def update_admin_webauthn_sign_count(self, *, credential_id: str, sign_count: int) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE admin_webauthn_credentials
                SET sign_count = ?
                WHERE credential_id = ?
                """,
                (int(sign_count), credential_id),
            )

    def create_admin_auth_challenge(
        self,
        *,
        challenge_id: str,
        kind: str,
        challenge_b64: str,
        expires_at: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO admin_auth_challenges(challenge_id, kind, challenge_b64, expires_at, used_at, created_at)
                VALUES (?, ?, ?, ?, NULL, ?)
                """,
                (challenge_id, kind, challenge_b64, expires_at, now),
            )

    def consume_admin_auth_challenge(self, *, challenge_id: str, kind: str) -> Optional[Dict[str, str]]:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT challenge_id, kind, challenge_b64, expires_at, used_at
                FROM admin_auth_challenges
                WHERE challenge_id = ? AND kind = ?
                """,
                (challenge_id, kind),
            ).fetchone()
            if row is None:
                return None
            if row["used_at"] is not None:
                return None
            try:
                expires_at = datetime.fromisoformat(str(row["expires_at"]))
            except Exception:
                return None
            if expires_at < now:
                return None
            conn.execute(
                """
                UPDATE admin_auth_challenges
                SET used_at = ?
                WHERE challenge_id = ? AND kind = ?
                """,
                (now_iso, challenge_id, kind),
            )
        return {
            "challenge_id": str(row["challenge_id"]),
            "kind": str(row["kind"]),
            "challenge_b64": str(row["challenge_b64"]),
            "expires_at": str(row["expires_at"]),
        }

    def create_admin_auth_session(self, *, session_id: str, expires_at: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO admin_auth_sessions(session_id, expires_at, created_at, last_seen_at, revoked_at)
                VALUES (?, ?, ?, ?, NULL)
                """,
                (session_id, expires_at, now, now),
            )

    def get_admin_auth_session(self, *, session_id: str) -> Optional[Dict[str, str]]:
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT session_id, expires_at, created_at, last_seen_at, revoked_at
                FROM admin_auth_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        if row["revoked_at"] is not None:
            return None
        try:
            expires_at = datetime.fromisoformat(str(row["expires_at"]))
        except Exception:
            return None
        if expires_at < now:
            return None
        return {
            "session_id": str(row["session_id"]),
            "expires_at": str(row["expires_at"]),
            "created_at": str(row["created_at"]),
            "last_seen_at": str(row["last_seen_at"]),
        }

    def touch_admin_auth_session(self, *, session_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE admin_auth_sessions
                SET last_seen_at = ?
                WHERE session_id = ? AND revoked_at IS NULL
                """,
                (now, session_id),
            )

    def revoke_admin_auth_session(self, *, session_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE admin_auth_sessions
                SET revoked_at = ?
                WHERE session_id = ?
                """,
                (now, session_id),
            )
