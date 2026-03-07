from __future__ import annotations

from fastapi import Request

from app.core.security import assert_admin_token


def require_admin(request: Request) -> None:
    settings = request.app.state.settings
    assert_admin_token(request.headers.get("x-admin-token", ""), settings.admin_token)


def apple_hash_secret(request: Request) -> str:
    settings = request.app.state.settings
    return settings.relay_shared_secret or settings.admin_token or "public-fallback"
