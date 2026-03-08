from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.endpoint_registry import ADMIN_BYPASS_PREFIXES, MANAGED_ENDPOINTS
from app.core.storage import SignalStore
from app.routes import admin, agents, apple, ingest, lab, openai, public, squarespace
from app.services.apple_attest_service import AppleAppAttestService
from app.services.apple_identity_service import AppleIdentityService
from app.services.agent_executor_service import AgentExecutorService
from app.services.chief_of_staff_service import ChiefOfStaffService
from app.services.openai_service import OpenAIService

settings = get_settings()
store = SignalStore(settings.database_path)
openai_service = OpenAIService(settings)
apple_identity_service = AppleIdentityService(settings)
apple_app_attest_service = AppleAppAttestService(settings)
chief_service = ChiefOfStaffService()
agent_executor_service = AgentExecutorService()

app = FastAPI(
    title="Noah Lucas Signal Stack",
    version="1.0.0",
    description="Privacy-first website backend with OpenAI and Apple signal ingestion.",
)

app.state.settings = settings
app.state.store = store
app.state.openai_service = openai_service
app.state.apple_identity_service = apple_identity_service
app.state.apple_app_attest_service = apple_app_attest_service
app.state.chief_service = chief_service
app.state.agent_executor_service = agent_executor_service

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Content-Type",
        "X-Admin-Token",
        "X-Relay-Timestamp",
        "X-Relay-Nonce",
        "X-Relay-Signature",
        "X-Apple-Bundle-Id",
        "X-Apple-App-Version",
        "X-Apple-IOS-Version",
        "X-Apple-Attestation-Token",
    ],
)


@app.middleware("http")
async def endpoint_toggle_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in MANAGED_ENDPOINTS and not any(path.startswith(prefix) for prefix in ADMIN_BYPASS_PREFIXES):
        toggles = request.app.state.store.list_endpoint_toggles()
        state = toggles.get(path)
        if state and state.get("enabled") == "false":
            return JSONResponse(
                status_code=423,
                content={"detail": f"Endpoint is disabled by integration toggle: {path}"},
            )
    return await call_next(request)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": str(settings.database_path),
    }


app.include_router(public.router, prefix="/api/v1/public", tags=["public"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(apple.router, prefix="/api/v1", tags=["apple"])
app.include_router(openai.router, prefix="/api/v1", tags=["openai"])
app.include_router(lab.router, prefix="/api/v1", tags=["lab"])
app.include_router(squarespace.router, prefix="/api/v1", tags=["squarespace"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])

def resolve_site_dir() -> Path | None:
    """Find the frontend site directory across local/dev and Render monorepo layouts."""
    candidates = [
        settings.project_root / "site",
        settings.project_root.parent / "site",
        Path(__file__).resolve().parents[3] / "site",
        Path(__file__).resolve().parents[2] / "site",
    ]
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


site_dir = resolve_site_dir()
if site_dir is not None:
    app.mount("/", StaticFiles(directory=str(site_dir), html=True), name="site")
