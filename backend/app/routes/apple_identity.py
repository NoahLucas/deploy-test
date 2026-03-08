from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.core.security import hash_identifier
from app.models import AppleIdentityVerifyRequest, AppleIdentityVerifyResponse
from app.routes.deps import apple_hash_secret
from app.routes.errors import bad_gateway

router = APIRouter()


@router.post("/apple/identity/verify", response_model=AppleIdentityVerifyResponse)
def verify_apple_identity(payload: AppleIdentityVerifyRequest, request: Request) -> AppleIdentityVerifyResponse:
    try:
        claims = request.app.state.apple_identity_service.verify_identity_token(
            identity_token=payload.identity_token,
            nonce=payload.nonce,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("Apple identity verification error", exc) from exc

    sub = str(claims.get("sub", ""))
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Apple identity token missing subject.")

    expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc)
    email_verified_raw = claims.get("email_verified")
    email_verified = None
    if isinstance(email_verified_raw, bool):
        email_verified = email_verified_raw
    elif isinstance(email_verified_raw, str):
        email_verified = email_verified_raw.lower() in {"true", "1"}

    return AppleIdentityVerifyResponse(
        valid=True,
        subject=hash_identifier(sub, apple_hash_secret(request)),
        email=claims.get("email"),
        email_verified=email_verified,
        audience=str(claims.get("aud", "")),
        issuer=str(claims.get("iss", "")),
        expires_at=expires_at,
    )
