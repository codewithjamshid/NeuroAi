"""Aggregates module routers under /api/v1 (mounted in app.main)."""

from fastapi import APIRouter

from app.modules.health.router import router as health_router

router = APIRouter()
router.include_router(health_router)
