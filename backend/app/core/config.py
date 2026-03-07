from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_root: Path
    database_path: Path
    cors_origins: List[str]
    openai_api_key: str
    openai_model: str
    openai_realtime_model: str
    openai_realtime_voice: str
    relay_shared_secret: str
    admin_token: str
    enforce_apple_context: bool
    apple_allowed_bundle_ids: List[str]
    require_apple_attestation_token: bool
    apple_identity_audience: str
    apple_identity_issuer: str
    apple_identity_jwks_url: str
    apple_app_attest_mode: str
    app_attest_challenge_ttl_seconds: int
    squarespace_webhook_secret: str
    squarespace_webhook_enforce_signature: bool


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _to_bool(value: str, default: bool = False) -> bool:
    if not value:
        return default
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _to_int(value: str, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    database_path = Path(
        os.getenv("DATABASE_PATH", str(project_root / "backend" / "data" / "signals.db"))
    )

    cors_origins_raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8000,http://localhost:3000,https://noahlucas.com",
    )

    return Settings(
        project_root=project_root,
        database_path=database_path,
        cors_origins=_split_csv(cors_origins_raw),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5"),
        openai_realtime_model=os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime"),
        openai_realtime_voice=os.getenv("OPENAI_REALTIME_VOICE", "alloy"),
        relay_shared_secret=os.getenv("RELAY_SHARED_SECRET", ""),
        admin_token=os.getenv("ADMIN_TOKEN", ""),
        enforce_apple_context=_to_bool(os.getenv("ENFORCE_APPLE_CONTEXT", "")),
        apple_allowed_bundle_ids=_split_csv(os.getenv("APPLE_ALLOWED_BUNDLE_IDS", "")),
        require_apple_attestation_token=_to_bool(os.getenv("REQUIRE_APPLE_ATTESTATION_TOKEN", "")),
        apple_identity_audience=os.getenv("APPLE_IDENTITY_AUDIENCE", ""),
        apple_identity_issuer=os.getenv("APPLE_IDENTITY_ISSUER", "https://appleid.apple.com"),
        apple_identity_jwks_url=os.getenv("APPLE_IDENTITY_JWKS_URL", "https://appleid.apple.com/auth/keys"),
        apple_app_attest_mode=os.getenv("APPLE_APP_ATTEST_MODE", "basic").strip().lower() or "basic",
        app_attest_challenge_ttl_seconds=_to_int(os.getenv("APP_ATTEST_CHALLENGE_TTL_SECONDS", "300"), 300),
        squarespace_webhook_secret=os.getenv("SQUARESPACE_WEBHOOK_SECRET", ""),
        squarespace_webhook_enforce_signature=_to_bool(os.getenv("SQUARESPACE_WEBHOOK_ENFORCE_SIGNATURE", "true"), True),
    )
