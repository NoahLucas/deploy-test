from __future__ import annotations

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
        event_at: str,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO autobiographer_memory_events(source, title, detail, tags_json, event_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source, title, detail, tags_json, event_at, created_at),
            )
            return int(cursor.lastrowid)

    def list_autobiographer_memory_events(
        self,
        *,
        limit: int = 120,
        year: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            if year is None:
                rows = conn.execute(
                    """
                    SELECT id, source, title, detail, tags_json, event_at, created_at
                    FROM autobiographer_memory_events
                    ORDER BY event_at DESC, id DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
            else:
                start = f"{year:04d}-01-01T00:00:00"
                end = f"{year + 1:04d}-01-01T00:00:00"
                rows = conn.execute(
                    """
                    SELECT id, source, title, detail, tags_json, event_at, created_at
                    FROM autobiographer_memory_events
                    WHERE event_at >= ? AND event_at < ?
                    ORDER BY event_at DESC, id DESC
                    LIMIT ?
                    """,
                    (start, end, safe_limit),
                ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "source": str(row["source"]),
                "title": str(row["title"]),
                "detail": str(row["detail"]),
                "tags_json": str(row["tags_json"]),
                "event_at": str(row["event_at"]),
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
