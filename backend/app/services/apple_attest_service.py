from __future__ import annotations

import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.core.config import Settings


class AppleAppAttestService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def issue_challenge(self) -> tuple[str, datetime]:
        challenge = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.settings.app_attest_challenge_ttl_seconds)
        return challenge, expires_at

    def verify_attestation_payload(self, payload: Dict[str, Any]) -> None:
        mode = self.settings.apple_app_attest_mode
        if mode == "off":
            return

        attestation_b64 = str(payload.get("attestation_object_b64", ""))
        client_hash_b64 = str(payload.get("client_data_hash_b64", ""))
        key_id = str(payload.get("key_id", ""))

        # Baseline structural validation for pre-production integration.
        attestation = self._decode_b64(attestation_b64, min_len=64, label="attestation_object_b64")
        client_hash = self._decode_b64(client_hash_b64, min_len=16, label="client_data_hash_b64")

        if len(key_id.strip()) < 6:
            raise RuntimeError("Invalid App Attest key_id.")

        if mode == "strict":
            # Full Apple attestation chain validation is required for strict mode.
            # Keep explicit failure behavior until the full cryptographic verifier is enabled.
            raise RuntimeError(
                "APPLE_APP_ATTEST_MODE=strict requires full cryptographic attestation verification implementation."
            )

        if len(attestation) < 128:
            raise RuntimeError("App Attest attestation object too small for basic mode.")
        if len(client_hash) < 16:
            raise RuntimeError("App Attest client data hash too small.")

    @staticmethod
    def _decode_b64(value: str, *, min_len: int, label: str) -> bytes:
        try:
            raw = base64.b64decode(value, validate=True)
        except Exception as exc:
            raise RuntimeError(f"Invalid base64 for {label}.") from exc
        if len(raw) < min_len:
            raise RuntimeError(f"Decoded {label} is too short.")
        return raw
