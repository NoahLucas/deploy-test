from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status

from app.core.endpoint_registry import MANAGED_ENDPOINTS
from app.models import (
    AppleConnectRequest,
    AppleConnectResponse,
    EndpointToggleItem,
    EndpointToggleListResponse,
    EndpointToggleUpdateRequest,
    OpenAIConnectRequest,
    OpenAIConnectResponse,
)
from app.routes.deps import require_admin
from app.routes.errors import bad_gateway

router = APIRouter()


@router.get("/admin/endpoints", response_model=EndpointToggleListResponse)
def list_managed_endpoints(request: Request) -> EndpointToggleListResponse:
    require_admin(request)
    store = request.app.state.store
    current = store.list_endpoint_toggles()
    items: list[EndpointToggleItem] = []

    for path, platform in MANAGED_ENDPOINTS.items():
        state = current.get(path)
        enabled = True
        updated_at = None
        if state:
            enabled = state["enabled"] == "true"
            try:
                updated_at = datetime.fromisoformat(state["updated_at"])
            except Exception:
                updated_at = None
        items.append(EndpointToggleItem(path=path, platform=platform, enabled=enabled, updated_at=updated_at))

    items.sort(key=lambda item: (item.platform, item.path))
    return EndpointToggleListResponse(items=items)


@router.post("/admin/endpoints/toggle", response_model=EndpointToggleListResponse)
def toggle_endpoint(payload: EndpointToggleUpdateRequest, request: Request) -> EndpointToggleListResponse:
    require_admin(request)
    path = payload.path.strip()
    platform = MANAGED_ENDPOINTS.get(path)
    if not platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint is not toggle-managed.")

    request.app.state.store.set_endpoint_toggle(path=path, platform=platform, enabled=payload.enabled)
    return list_managed_endpoints(request)


@router.post("/admin/openai/connect", response_model=OpenAIConnectResponse)
def connect_openai(payload: OpenAIConnectRequest, request: Request) -> OpenAIConnectResponse:
    require_admin(request)
    service = request.app.state.openai_service
    try:
        service.configure_runtime(api_key=payload.api_key, model=payload.model)
        test = service.test_connectivity()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("OpenAI connect failed", exc) from exc

    return OpenAIConnectResponse(
        connected=True,
        model=str(test.get("model", service.active_model)),
        account_hint=str(test.get("account_hint", "unknown")),
    )


@router.post("/admin/apple/connect", response_model=AppleConnectResponse)
def connect_apple(payload: AppleConnectRequest, request: Request) -> AppleConnectResponse:
    require_admin(request)
    try:
        claims = request.app.state.apple_identity_service.verify_identity_token(
            identity_token=payload.identity_token,
            nonce=payload.nonce,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except Exception as exc:
        raise bad_gateway("Apple connect failed", exc) from exc

    try:
        expires_at = datetime.fromtimestamp(int(claims["exp"]))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Apple token exp parse failed: {exc}") from exc

    return AppleConnectResponse(
        connected=True,
        subject=str(claims.get("sub", "")),
        audience=str(claims.get("aud", "")),
        expires_at=expires_at,
    )
