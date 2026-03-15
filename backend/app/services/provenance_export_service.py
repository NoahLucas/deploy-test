from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.storage import SignalStore


class ProvenanceExportService:
    def __init__(self, settings: Settings, store: SignalStore) -> None:
        self.settings = settings
        self.store = store

    def export_year_package(self, *, year: int, include_private_context: bool) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        root = Path(self.settings.google_drive_sync_dir).expanduser().resolve() / "autobiographer" / str(year)
        root.mkdir(parents=True, exist_ok=True)

        events = self.store.list_autobiographer_memory_events(limit=1000, year=year)
        scenes = self.store.list_autobiographer_scene_clusters(year=year, limit=300)
        chapters = []
        year_chapter = self.store.get_autobiographer_chapter_by_year(year=year)
        if year_chapter is not None:
            chapters.append(year_chapter)
        monthly = self.store.list_autobiographer_month_chapters(year=year, limit=24)
        revisions = self.store.list_autobiographer_revisions(year=year, limit=100)

        package = {
            "year": year,
            "include_private_context": include_private_context,
            "exported_at": now.isoformat(),
            "counts": {
                "events": len(events),
                "scenes": len(scenes),
                "chapters": len(chapters) + len(monthly),
                "revisions": len(revisions),
            },
            "events": events,
            "scenes": scenes,
            "year_chapter": year_chapter,
            "monthly_chapters": monthly,
            "revisions": revisions,
        }

        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(package, indent=2), encoding="utf-8")

        if year_chapter is not None:
            (root / f"chapter-{year}.md").write_text(str(year_chapter["chapter_markdown"]).strip() + "\n", encoding="utf-8")

        for revision in revisions:
            slug = str(revision["slug"]).strip() or f"revision-{revision['id']}"
            (root / f"{slug}.md").write_text(str(revision["body_markdown"]).strip() + "\n", encoding="utf-8")

        return {
            "year": year,
            "export_root": str(root),
            "manifest_path": str(manifest_path),
            "events_exported": len(events),
            "chapters_exported": len(chapters) + len(monthly),
            "revisions_exported": len(revisions),
            "scenes_exported": len(scenes),
            "exported_at": now,
        }
