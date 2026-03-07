from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx
try:
    import jwt  # type: ignore
except ImportError:  # pragma: no cover - optional until dependencies are installed
    jwt = None

from app.core.config import Settings


class AppleIdentityService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.Client(timeout=httpx.Timeout(10.0, connect=5.0))
        self._jwks_cache: Dict[str, Any] = {}
        self._jwks_cached_at: datetime | None = None

    def verify_identity_token(self, *, identity_token: str, nonce: str | None = None) -> Dict[str, Any]:
        if jwt is None:
            raise RuntimeError("PyJWT is not installed. Install backend requirements first.")
        if not self.settings.apple_identity_audience:
            raise RuntimeError("APPLE_IDENTITY_AUDIENCE is not configured.")

        header = jwt.get_unverified_header(identity_token)
        kid = header.get("kid")
        alg = header.get("alg")
        if not kid or alg != "RS256":
            raise RuntimeError("Invalid Apple identity token header.")

        jwk = self._lookup_jwk(str(kid))
        key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)

        claims = jwt.decode(
            identity_token,
            key=key,
            algorithms=["RS256"],
            audience=self.settings.apple_identity_audience,
            issuer=self.settings.apple_identity_issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )

        if nonce:
            token_nonce = claims.get("nonce")
            if token_nonce != nonce:
                raise RuntimeError("Apple identity nonce mismatch.")

        return claims

    def _lookup_jwk(self, kid: str) -> str:
        now = datetime.now(timezone.utc)
        if not self._jwks_cache or not self._jwks_cached_at or (now - self._jwks_cached_at) > timedelta(hours=6):
            self._refresh_jwks()

        jwk = self._jwks_cache.get(kid)
        if not isinstance(jwk, str):
            self._refresh_jwks()
            jwk = self._jwks_cache.get(kid)

        if not isinstance(jwk, str):
            raise RuntimeError("Apple JWKS key id not found.")
        return jwk

    def _refresh_jwks(self) -> None:
        response = self._client.get(self.settings.apple_identity_jwks_url)
        response.raise_for_status()
        payload = response.json()
        keys = payload.get("keys", [])
        if not isinstance(keys, list):
            raise RuntimeError("Apple JWKS payload malformed.")

        mapped: Dict[str, str] = {}
        for key in keys:
            if not isinstance(key, dict):
                continue
            kid = key.get("kid")
            if not isinstance(kid, str):
                continue
            mapped[kid] = json.dumps(key)

        if not mapped:
            raise RuntimeError("Apple JWKS keys unavailable.")

        self._jwks_cache = mapped
        self._jwks_cached_at = datetime.now(timezone.utc)
