from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.models import LabDailyBriefRequest, LabDailyBriefResponse
from app.routes.deps import require_admin
from app.routes.errors import bad_gateway, service_unavailable

router = APIRouter()


@router.post("/lab/daily-brief", response_model=LabDailyBriefResponse)
def generate_lab_daily_brief(payload: LabDailyBriefRequest, request: Request) -> LabDailyBriefResponse:
    require_admin(request)
    memory = request.app.state.store.list_editorial_memory(limit=24)

    try:
        result = request.app.state.openai_service.generate_lab_daily_brief(
            priorities=payload.priorities,
            risks=payload.risks,
            context=payload.context,
            memory=memory,
        )
    except RuntimeError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("OpenAI daily brief error", exc) from exc

    if not result:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI daily brief output was invalid.")

    try:
        top_actions = [str(item) for item in result["top_actions"]][:3]
        watchouts = [str(item) for item in result["watchouts"]][:3]
        return LabDailyBriefResponse(
            headline=str(result["headline"]),
            top_actions=top_actions,
            watchouts=watchouts,
            communication_draft=str(result["communication_draft"]),
            generated_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI daily brief schema validation failed: {exc}",
        ) from exc
