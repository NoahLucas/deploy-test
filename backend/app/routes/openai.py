from __future__ import annotations

from fastapi import APIRouter

from app.routes.openai_intel import router as intel_router
from app.routes.openai_memory import router as memory_router
from app.routes.openai_notes import router as notes_router

router = APIRouter()
router.include_router(intel_router)
router.include_router(notes_router)
router.include_router(memory_router)
