from __future__ import annotations

import hashlib
import hmac

from fastapi import HTTPException, status

from app.core.config import Settings


def validate_squarespace_signature(
    *,
    raw_body: bytes,
    signature: str,
    timestamp: str,
    settings: Settings,
) -> None:
    if not settings.squarespace_webhook_enforce_signature:
        return

    secret = settings.squarespace_webhook_secret
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SQUARESPACE_WEBHOOK_SECRET is not configured.",
        )

    if not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Squarespace signature header.")

    # Support both payload styles:
    # 1) HMAC(secret, raw_body)
    # 2) HMAC(secret, timestamp + '.' + raw_body)
    raw_digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    with_ts_material = (timestamp.encode("utf-8") + b"." + raw_body) if timestamp else raw_body
    ts_digest = hmac.new(secret.encode("utf-8"), with_ts_material, hashlib.sha256).hexdigest()

    clean_signature = signature.strip().lower().replace("sha256=", "")
    if not (hmac.compare_digest(clean_signature, raw_digest) or hmac.compare_digest(clean_signature, ts_digest)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Squarespace webhook signature.")
