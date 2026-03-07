from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.core.squarespace_security import validate_squarespace_signature
from app.models import SquarespaceEventItem, SquarespaceEventsResponse, SquarespaceWebhookIngestResponse
from app.routes.deps import require_admin

router = APIRouter()


@router.post("/squarespace/webhooks", response_model=SquarespaceWebhookIngestResponse)
async def ingest_squarespace_webhook(request: Request) -> SquarespaceWebhookIngestResponse:
    settings = request.app.state.settings
    raw_body = await request.body()

    signature = request.headers.get("x-squarespace-signature", "")
    timestamp = request.headers.get("x-squarespace-timestamp", "")
    validate_squarespace_signature(
        raw_body=raw_body,
        signature=signature,
        timestamp=timestamp,
        settings=settings,
    )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid Squarespace JSON payload.") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid Squarespace payload shape.")

    event_id = str(payload.get("id") or payload.get("eventId") or "").strip()
    event_type = str(payload.get("type") or payload.get("eventType") or "unknown").strip() or "unknown"
    website_id = str(payload.get("websiteId") or payload.get("website_id") or "unknown").strip() or "unknown"
    created_at = str(payload.get("createdAt") or payload.get("created_at") or datetime.now(timezone.utc).isoformat())

    if not event_id:
        # Deterministic fallback for providers that omit id.
        event_id = f"evt-{abs(hash(raw_body))}"

    request.app.state.store.insert_squarespace_event(
        event_id=event_id,
        event_type=event_type,
        website_id=website_id,
        created_at=created_at,
        payload_json=json.dumps(payload),
    )

    return SquarespaceWebhookIngestResponse(accepted=True, event_type=event_type, event_id=event_id)


@router.get("/admin/squarespace/events", response_model=SquarespaceEventsResponse)
def list_squarespace_events(request: Request) -> SquarespaceEventsResponse:
    require_admin(request)
    rows = request.app.state.store.list_squarespace_events(limit=80)
    items = [
        SquarespaceEventItem(
            id=row["id"],
            event_id=row["event_id"],
            event_type=row["event_type"],
            website_id=row["website_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            received_at=datetime.fromisoformat(row["received_at"]),
        )
        for row in rows
    ]
    return SquarespaceEventsResponse(items=items)
