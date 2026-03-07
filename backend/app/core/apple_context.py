from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import Settings


def validate_apple_client_context(
    *,
    bundle_id: str,
    app_version: str,
    ios_version: str,
    attestation_token: str,
    settings: Settings,
) -> None:
    """
    Lightweight guardrails for Apple relay metadata.
    Cryptographic App Attest verification is a later phase.
    """
    if not settings.enforce_apple_context:
        return

    if not bundle_id or not app_version or not ios_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required Apple client context fields.",
        )

    if settings.apple_allowed_bundle_ids and bundle_id not in settings.apple_allowed_bundle_ids:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bundle ID not allowlisted.",
        )

    if settings.require_apple_attestation_token and not attestation_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Attestation token required by server policy.",
        )
