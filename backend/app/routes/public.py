from __future__ import annotations

import base64
import json
import re
import secrets
from html import unescape
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree

import httpx
from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from webauthn import verify_authentication_response, verify_registration_response
from webauthn.helpers import base64url_to_bytes

from app.core.security import assert_admin_token
from app.core.sanitizer import default_action, default_headline, derive_public_scores
from app.models import (
    FeedMetrics,
    PublicFeedResponse,
    PublicNoteDetailResponse,
    PublicNotesResponse,
    PublicNoteSummary,
    SquarespaceNotesResponse,
    SquarespaceNoteSummary,
)

router = APIRouter()
SQUARESPACE_NOTES_RSS_URL = "https://noahlucas.com/notes?format=rss"
SQUARESPACE_NOTES_CACHE_TTL_SECONDS = 90
_SQUARESPACE_NOTES_CACHE: dict[str, object] = {"fetched_at": None, "payload": None}
_ADMIN_AUTH_COOKIE_NAME = "nl_admin_session"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _draft_files(project_root: Path, limit: int = 24) -> list[Path]:
    notes_dir = project_root / "content" / "notes-drafts"
    if not notes_dir.exists():
        return []
    files = sorted(notes_dir.glob("*.json"), reverse=True)
    return files[: max(1, min(limit, 100))]


def _read_draft(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rss_text(parent: ElementTree.Element, tag: str) -> str:
    value = parent.findtext(tag)
    return (value or "").strip()


def _clean_rss_html(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_rfc2822_utc(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value.strip(), "%a, %d %b %Y %H:%M:%S %z")
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _is_secure_request(request: Request) -> bool:
    proto = request.headers.get("x-forwarded-proto", "").strip().lower()
    if proto:
        return proto == "https"
    return request.url.scheme == "https"


def _expected_rp_id(request: Request) -> str:
    configured = request.app.state.settings.webauthn_rp_id
    return configured or (request.url.hostname or "")


def _expected_origin(request: Request) -> str:
    configured = request.app.state.settings.webauthn_origin
    if configured:
        return configured
    return f"{'https' if _is_secure_request(request) else 'http'}://{request.url.hostname or ''}"


@router.get("/feed", response_model=PublicFeedResponse)
def get_public_feed(request: Request) -> PublicFeedResponse:
    store = request.app.state.store
    cached = store.get_public_feed()

    if cached:
        updated_at = datetime.fromisoformat(cached["updated_at"])
        return PublicFeedResponse(
            headline=cached["headline"],
            metrics=FeedMetrics(
                recovery=cached["recovery"],
                focus=cached["focus"],
                balance=cached["balance"],
                action=cached["action"],
            ),
            updated_at=updated_at,
        )

    averages = store.averaged_signals(days=7)
    scores = derive_public_scores(averages)

    return PublicFeedResponse(
        headline=default_headline(scores),
        metrics=FeedMetrics(
            recovery=f"{scores['recovery']}/100",
            focus=f"{scores['focus']}/100",
            balance=f"{scores['balance']}/100",
            action=default_action(scores),
        ),
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/notes-drafts", response_model=PublicNotesResponse)
def get_public_note_drafts(request: Request) -> PublicNotesResponse:
    project_root: Path = request.app.state.settings.project_root
    items: list[PublicNoteSummary] = []
    for file_path in _draft_files(project_root, limit=24):
        try:
            raw = _read_draft(file_path)
            items.append(
                PublicNoteSummary(
                    title=str(raw["title"]),
                    slug=str(raw["slug"]),
                    summary=str(raw["summary"]),
                    generated_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                )
            )
        except Exception:
            continue

    return PublicNotesResponse(items=items)


@router.get("/notes-drafts/{slug}", response_model=PublicNoteDetailResponse)
def get_public_note_draft_detail(slug: str, request: Request) -> PublicNoteDetailResponse:
    project_root: Path = request.app.state.settings.project_root
    slug = slug.strip().lower()
    if not slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    for file_path in _draft_files(project_root, limit=100):
        try:
            raw = _read_draft(file_path)
        except Exception:
            continue
        if str(raw.get("slug", "")).strip().lower() != slug:
            continue
        try:
            return PublicNoteDetailResponse(
                title=str(raw["title"]),
                slug=str(raw["slug"]),
                summary=str(raw["summary"]),
                body_markdown=str(raw["body_markdown"]),
                meta_title=str(raw["meta_title"]),
                meta_description=str(raw["meta_description"]),
                social_quotes=[str(q) for q in raw.get("social_quotes", [])][:3],
                generated_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
            )
        except Exception:
            break

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")


@router.get("/squarespace-notes", response_model=SquarespaceNotesResponse)
def get_squarespace_notes() -> SquarespaceNotesResponse:
    now = datetime.now(timezone.utc)
    cached_at = _SQUARESPACE_NOTES_CACHE.get("fetched_at")
    cached_payload = _SQUARESPACE_NOTES_CACHE.get("payload")
    if isinstance(cached_at, datetime) and isinstance(cached_payload, SquarespaceNotesResponse):
        age_seconds = (now - cached_at).total_seconds()
        if age_seconds < SQUARESPACE_NOTES_CACHE_TTL_SECONDS:
            return cached_payload

    try:
        response = httpx.get(SQUARESPACE_NOTES_RSS_URL, timeout=12.0)
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch Squarespace notes feed: {exc}",
        ) from exc

    try:
        root = ElementTree.fromstring(response.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invalid Squarespace RSS response: {exc}",
        ) from exc

    items: list[SquarespaceNoteSummary] = []
    for node in root.findall("./channel/item"):
        title = _rss_text(node, "title")
        url = _rss_text(node, "link")
        summary = _clean_rss_html(_rss_text(node, "description"))
        if not summary:
            summary = _clean_rss_html(_rss_text(node, "content:encoded"))
        published = _parse_rfc2822_utc(_rss_text(node, "pubDate"))
        if not title or not url:
            continue
        items.append(
            SquarespaceNoteSummary(
                title=title,
                url=url,
                summary=summary[:320],
                published_at=published,
            )
        )
        if len(items) >= 12:
            break

    payload = SquarespaceNotesResponse(
        source=SQUARESPACE_NOTES_RSS_URL,
        updated_at=now,
        items=items,
    )
    _SQUARESPACE_NOTES_CACHE["fetched_at"] = now
    _SQUARESPACE_NOTES_CACHE["payload"] = payload
    return payload


@router.get("/admin-auth/session")
def get_admin_auth_session(
    request: Request,
    admin_session: str | None = Cookie(default=None, alias=_ADMIN_AUTH_COOKIE_NAME),
) -> dict[str, object]:
    if not admin_session:
        return {"authorized": False}
    session = request.app.state.store.get_admin_auth_session(session_id=admin_session)
    if not session:
        return {"authorized": False}
    request.app.state.store.touch_admin_auth_session(session_id=admin_session)
    return {"authorized": True, "expires_at": session["expires_at"]}


@router.post("/admin-auth/logout")
def logout_admin_auth(
    request: Request,
    response: Response,
    admin_session: str | None = Cookie(default=None, alias=_ADMIN_AUTH_COOKIE_NAME),
) -> dict[str, bool]:
    if admin_session:
        request.app.state.store.revoke_admin_auth_session(session_id=admin_session)
    response.delete_cookie(_ADMIN_AUTH_COOKIE_NAME, path="/")
    return {"logged_out": True}


@router.post("/admin-auth/webauthn/register/challenge")
def start_admin_register_challenge(request: Request) -> dict[str, object]:
    assert_admin_token(request.headers.get("x-admin-token", ""), request.app.state.settings.admin_token)
    challenge_id = secrets.token_urlsafe(24)
    challenge = _b64url_encode(secrets.token_bytes(32))
    user_id = _b64url_encode(secrets.token_bytes(16))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    request.app.state.store.create_admin_auth_challenge(
        challenge_id=challenge_id,
        kind="register",
        challenge_b64=challenge,
        expires_at=expires_at.isoformat(),
    )
    return {
        "challenge_id": challenge_id,
        "challenge": challenge,
        "rp": {"id": _expected_rp_id(request), "name": request.app.state.settings.webauthn_rp_name},
        "user": {"id": user_id, "name": "owner@noahlucas.com", "displayName": "Noah Lucas"},
        "timeout": 60000,
    }


@router.post("/admin-auth/webauthn/register/complete")
def complete_admin_register_challenge(request: Request, payload: dict[str, object]) -> dict[str, object]:
    assert_admin_token(request.headers.get("x-admin-token", ""), request.app.state.settings.admin_token)
    challenge_id = str(payload.get("challenge_id", "")).strip()
    credential = payload.get("credential")
    label = str(payload.get("label", "Owner device")).strip() or "Owner device"
    if not challenge_id or not isinstance(credential, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing challenge_id or credential.")
    challenge = request.app.state.store.consume_admin_auth_challenge(challenge_id=challenge_id, kind="register")
    if not challenge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Registration challenge invalid or expired.")

    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge["challenge_b64"]),
            expected_rp_id=_expected_rp_id(request),
            expected_origin=_expected_origin(request),
            require_user_verification=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Registration verification failed: {exc}") from exc

    request.app.state.store.save_admin_webauthn_credential(
        credential_id=str(verification.credential_id),
        label=label,
        public_key_b64=_b64url_encode(verification.credential_public_key),
        sign_count=int(verification.sign_count),
    )
    return {"registered": True, "credential_count": len(request.app.state.store.list_admin_webauthn_credentials())}


@router.post("/admin-auth/webauthn/challenge")
def start_admin_auth_challenge(request: Request) -> dict[str, object]:
    credentials = request.app.state.store.list_admin_webauthn_credentials()
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="No owner credential enrolled. Complete owner enrollment first.",
        )
    challenge_id = secrets.token_urlsafe(24)
    challenge = _b64url_encode(secrets.token_bytes(32))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    request.app.state.store.create_admin_auth_challenge(
        challenge_id=challenge_id,
        kind="auth",
        challenge_b64=challenge,
        expires_at=expires_at.isoformat(),
    )
    return {
        "challenge_id": challenge_id,
        "challenge": challenge,
        "rp_id": _expected_rp_id(request),
        "timeout": 60000,
        "allow_credentials": [item["credential_id"] for item in credentials],
    }


@router.post("/admin-auth/webauthn/verify")
def verify_admin_auth_challenge(request: Request, response: Response, payload: dict[str, object]) -> dict[str, object]:
    challenge_id = str(payload.get("challenge_id", "")).strip()
    credential = payload.get("credential")
    credential_id = str((credential or {}).get("id", "")).strip() if isinstance(credential, dict) else ""
    if not challenge_id or not credential_id or not isinstance(credential, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing challenge_id or credential.")

    challenge = request.app.state.store.consume_admin_auth_challenge(challenge_id=challenge_id, kind="auth")
    if not challenge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth challenge invalid or expired.")
    stored = request.app.state.store.get_admin_webauthn_credential(credential_id=credential_id)
    if not stored:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Credential is not enrolled for owner access.")

    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge["challenge_b64"]),
            expected_rp_id=_expected_rp_id(request),
            expected_origin=_expected_origin(request),
            credential_public_key=base64url_to_bytes(str(stored["public_key_b64"])),
            credential_current_sign_count=int(stored["sign_count"]),
            require_user_verification=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication verification failed: {exc}") from exc

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=8)
    session_id = secrets.token_urlsafe(32)
    request.app.state.store.create_admin_auth_session(session_id=session_id, expires_at=expires_at.isoformat())
    request.app.state.store.mark_admin_webauthn_credential_used(credential_id=credential_id)
    request.app.state.store.update_admin_webauthn_sign_count(
        credential_id=credential_id,
        sign_count=int(verification.new_sign_count),
    )
    response.set_cookie(
        key=_ADMIN_AUTH_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=_is_secure_request(request),
        samesite="lax",
        max_age=int(timedelta(hours=8).total_seconds()),
        path="/",
    )
    return {"authorized": True, "expires_at": expires_at.isoformat()}
