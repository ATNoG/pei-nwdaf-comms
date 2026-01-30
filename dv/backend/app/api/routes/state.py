"""
API routes for dashboard state management.
"""
from fastapi import APIRouter, status
from datetime import datetime

from ...models.schemas import DashboardState, ViewSettings
from ...core.state import state_manager
from ...core.logging import get_logger
from ...core.config import settings
from ..websocket import connection_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["state"])


@router.get("/state", response_model=DashboardState)
async def get_dashboard_state():
    return await state_manager.get_state()


@router.post("/state", response_model=DashboardState)
async def update_dashboard_state(state: DashboardState):
    await state_manager.update_state(state)
    await connection_manager.send_state_update(state)
    logger.info("Dashboard state updated")
    return await state_manager.get_state()


@router.post("/toggle-lock")
async def toggle_lock():
    is_locked = await state_manager.toggle_lock()
    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Dashboard lock toggled: {is_locked}")
    return {"locked": is_locked}


@router.post("/set-view")
async def set_view(settings: ViewSettings):
    await state_manager.set_view(settings.zoom, settings.pan_x, settings.pan_y)
    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"View updated: zoom={settings.zoom}, pan=({settings.pan_x}, {settings.pan_y})")
    return {"zoom": settings.zoom, "pan_x": settings.pan_x, "pan_y": settings.pan_y}


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": datetime.utcnow().isoformat(),
        "connections": connection_manager.get_connection_count(),
    }
