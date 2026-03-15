from __future__ import annotations

from typing import Dict

# Endpoint-level kill switches for experimentation and safe rollouts.
MANAGED_ENDPOINTS: Dict[str, str] = {
    "/api/v1/squarespace/webhooks": "squarespace",
    "/api/v1/admin/squarespace/events": "squarespace",
    "/api/v1/apple/ingest": "apple",
    "/api/v1/apple/identity/verify": "apple",
    "/api/v1/apple/app-attest/challenge": "apple",
    "/api/v1/apple/app-attest/verify": "apple",
    "/api/v1/openai/realtime-session": "openai",
    "/api/v1/openai/editorial-memory": "openai",
    "/api/v1/openai/notes/ideate": "openai",
    "/api/v1/openai/notes/draft": "openai",
    "/api/v1/openai/notes/save": "openai",
    "/api/v1/openai/notes/pipeline": "openai",
    "/api/v1/openai/site-memory-chat": "openai",
    "/api/v1/openai/provenance/export": "openai",
    "/api/v1/lab/daily-brief": "openai",
    "/api/v1/lab/decision-journal": "openai",
    "/api/v1/lab/weekly-snapshot": "openai",
    "/api/v1/lab/autobiographer/chapters/generate": "openai",
    "/api/v1/lab/autobiographer/chapters/initialize-year": "openai",
    "/api/v1/lab/autobiographer/publish-live-note": "openai",
    "/api/v1/lab/autobiographer/year-chapters/generate": "openai",
    "/api/v1/lab/autobiographer/publish-year-note": "openai",
    "/api/v1/agents/chief/dispatch": "openai",
    "/api/v1/agents/runs": "openai",
}

ADMIN_BYPASS_PREFIXES = {
    "/api/v1/admin",
}
