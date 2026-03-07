from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from app.core.apple_context import validate_apple_client_context
from app.core.sanitizer import sanitize_signals
from app.core.security import hash_identifier, validate_relay_signature
from app.models import AppleSignalIngestRequest, IngestResponse

router = APIRouter()


def _parse_ingest_payload(raw_body: bytes) -> AppleSignalIngestRequest:
    try:
        return AppleSignalIngestRequest.model_validate_json(raw_body)
    except AttributeError:
        return AppleSignalIngestRequest.parse_raw(raw_body)


@router.post("/apple/ingest", response_model=IngestResponse)
async def ingest_apple_signals(request: Request) -> IngestResponse:
    settings = request.app.state.settings
    raw_body = await request.body()

    validate_relay_signature(
        raw_body=raw_body,
        timestamp=request.headers.get("x-relay-timestamp", ""),
        nonce=request.headers.get("x-relay-nonce", ""),
        signature=request.headers.get("x-relay-signature", ""),
        shared_secret=settings.relay_shared_secret,
    )

    try:
        payload = _parse_ingest_payload(raw_body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid JSON payload for apple ingest.",
        ) from exc

    # Accept either payload fields or headers so existing relay clients remain compatible.
    bundle_id = payload.bundle_id or request.headers.get("x-apple-bundle-id", "")
    app_version = payload.app_version or request.headers.get("x-apple-app-version", "")
    ios_version = payload.ios_version or request.headers.get("x-apple-ios-version", "")

    validate_apple_client_context(
        bundle_id=bundle_id,
        app_version=app_version,
        ios_version=ios_version,
        attestation_token=payload.attestation_token or request.headers.get("x-apple-attestation-token", ""),
        settings=settings,
    )

    sanitized = sanitize_signals(payload.signals)
    if not sanitized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No allowed signal keys in payload.",
        )

    source_hash = hash_identifier(payload.device_id, settings.relay_shared_secret)
    request.app.state.store.insert_sanitized_signals(
        day=payload.collected_at.date().isoformat(),
        source_hash=source_hash,
        collected_at=payload.collected_at.isoformat(),
        signals=sanitized,
    )

    return IngestResponse(
        accepted=len(sanitized),
        dropped=max(len(payload.signals) - len(sanitized), 0),
        message="Signals accepted and sanitized.",
    )
