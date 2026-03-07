from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.core.security import hash_identifier
from app.models import (
    AppAttestChallengeRequest,
    AppAttestChallengeResponse,
    AppAttestVerifyRequest,
    AppAttestVerifyResponse,
)
from app.routes.deps import apple_hash_secret
from app.routes.errors import bad_gateway

router = APIRouter()


@router.post("/apple/app-attest/challenge", response_model=AppAttestChallengeResponse)
def issue_app_attest_challenge(payload: AppAttestChallengeRequest, request: Request) -> AppAttestChallengeResponse:
    device_hash = hash_identifier(payload.device_id, apple_hash_secret(request))
    challenge, expires_at = request.app.state.apple_app_attest_service.issue_challenge()
    request.app.state.store.create_app_attest_challenge(
        challenge=challenge,
        device_hash=device_hash,
        expires_at=expires_at,
    )
    return AppAttestChallengeResponse(challenge=challenge, expires_at=expires_at)


@router.post("/apple/app-attest/verify", response_model=AppAttestVerifyResponse)
def verify_app_attest(payload: AppAttestVerifyRequest, request: Request) -> AppAttestVerifyResponse:
    device_hash = hash_identifier(payload.device_id, apple_hash_secret(request))

    consumed = request.app.state.store.consume_app_attest_challenge(
        challenge=payload.challenge,
        device_hash=device_hash,
    )
    if not consumed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Challenge invalid or expired.")

    try:
        request.app.state.apple_app_attest_service.verify_attestation_payload(payload.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("App Attest verification error", exc) from exc

    mode = request.app.state.settings.apple_app_attest_mode
    request.app.state.store.upsert_apple_device_trust(
        device_hash=device_hash,
        key_id=payload.key_id,
        bundle_id=payload.bundle_id,
        mode=mode,
    )

    return AppAttestVerifyResponse(
        accepted=True,
        mode=mode,
        device_hash=device_hash,
        key_id=payload.key_id,
        verified_at=datetime.now(timezone.utc),
    )
