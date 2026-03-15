from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.models import (
    MemorySourceProvenanceItem,
    ProvenanceExportRequest,
    ProvenanceExportResponse,
    SiteMemoryChatRequest,
    SiteMemoryChatResponse,
)
from app.routes.deps import require_admin
from app.routes.errors import bad_gateway, service_unavailable

router = APIRouter()


@router.post("/openai/site-memory-chat", response_model=SiteMemoryChatResponse)
def site_memory_chat(payload: SiteMemoryChatRequest, request: Request) -> SiteMemoryChatResponse:
    require_admin(request)
    store = request.app.state.store
    year = payload.year
    memory_events = store.list_autobiographer_memory_events(limit=200, year=year)
    year_chapters = store.list_autobiographer_chapters(limit=20)
    revisions = store.list_autobiographer_revisions(year=year or datetime.now(timezone.utc).year, limit=30) if year else []

    try:
        generated = request.app.state.openai_service.generate_site_memory_chat(
            message=payload.message,
            year=year,
            memory_events=memory_events,
            year_chapters=year_chapters,
            revisions=revisions,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("Site memory chat error", exc) from exc

    answer_markdown = str((generated or {}).get("answer_markdown", "")).strip()
    sources_raw = (generated or {}).get("sources", [])
    sources = [
        MemorySourceProvenanceItem(
            kind=str(item.get("kind", "")).strip(),
            label=str(item.get("label", "")).strip(),
            detail=str(item.get("detail", "")).strip(),
            ref=str(item.get("ref", "")).strip(),
        )
        for item in sources_raw
        if isinstance(item, dict) and str(item.get("label", "")).strip()
    ]
    return SiteMemoryChatResponse(
        answer_markdown=answer_markdown or "I don't have enough grounded memory evidence yet to answer that well.",
        sources=sources,
        generated_at=datetime.now(timezone.utc),
    )


@router.post("/openai/provenance/export", response_model=ProvenanceExportResponse)
def export_provenance(payload: ProvenanceExportRequest, request: Request) -> ProvenanceExportResponse:
    require_admin(request)
    exported = request.app.state.provenance_export_service.export_year_package(
        year=payload.year,
        include_private_context=payload.include_private_context,
    )
    return ProvenanceExportResponse(**exported)
