from __future__ import annotations

import hashlib
import hmac
import time
from threading import Lock
from typing import Dict

from fastapi import HTTPException, status

_NONCE_TTL_SECONDS = 900
_NONCE_CACHE: Dict[str, int] = {}
_NONCE_LOCK = Lock()


def _prune_nonce_cache(now: int) -> None:
    stale = [nonce for nonce, seen_at in _NONCE_CACHE.items() if now - seen_at > _NONCE_TTL_SECONDS]
    for nonce in stale:
        _NONCE_CACHE.pop(nonce, None)


def validate_relay_signature(
    raw_body: bytes,
    timestamp: str,
    nonce: str,
    signature: str,
    shared_secret: str,
    max_age_seconds: int = 300,
) -> None:
    if not shared_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RELAY_SHARED_SECRET is not configured.",
        )

    if not timestamp or not nonce or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing relay headers.")

    try:
        sent_at = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid timestamp.") from exc

    now = int(time.time())
    if abs(now - sent_at) > max_age_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale relay signature.")

    payload = timestamp.encode("utf-8") + b"." + nonce.encode("utf-8") + b"." + raw_body
    expected = hmac.new(shared_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature.lower()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid relay signature.")

    with _NONCE_LOCK:
        _prune_nonce_cache(now)
        if nonce in _NONCE_CACHE:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Replay nonce rejected.")
        _NONCE_CACHE[nonce] = now


def hash_identifier(raw_value: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_value.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:24]


def assert_admin_token(sent_token: str, expected_token: str) -> None:
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_TOKEN is not configured.",
        )

    if not sent_token or not hmac.compare_digest(sent_token, expected_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin token invalid.")
