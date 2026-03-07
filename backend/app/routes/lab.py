from __future__ import annotations

from fastapi import APIRouter

from app.routes.lab_daily_brief import router as brief_router
from app.routes.lab_decision_journal import router as journal_router

router = APIRouter()
router.include_router(brief_router)
router.include_router(journal_router)
