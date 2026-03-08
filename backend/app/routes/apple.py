from __future__ import annotations

from fastapi import APIRouter

from app.routes.apple_attest import router as attest_router
from app.routes.apple_identity import router as identity_router

router = APIRouter()
router.include_router(identity_router)
router.include_router(attest_router)
