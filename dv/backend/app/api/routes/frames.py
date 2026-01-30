"""
API routes for frame management.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import string
import random

from ...models.schemas import Frame
from ...core.state import state_manager
from ...core.logging import get_logger
from ..websocket import connection_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/frames", tags=["frames"])


def generate_frame_id() -> str:
    """Generate a unique frame ID."""
    return "frame_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


@router.get("", response_model=List[Frame])
async def get_frames():
    return await state_manager.get_frames()


@router.post("", response_model=Frame, status_code=status.HTTP_201_CREATED)
async def create_frame(frame: Frame):
    # Check if frame with ID already exists
    existing = await state_manager.get_frame(frame.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Frame with ID {frame.id} already exists",
        )

    await state_manager.add_frame(frame)
    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Created frame: {frame.id}")
    return frame


@router.get("/{frame_id}", response_model=Frame)
async def get_frame(frame_id: str):
    frame = await state_manager.get_frame(frame_id)
    if not frame:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Frame with ID {frame_id} not found",
        )
    return frame


@router.put("/{frame_id}", response_model=Frame)
async def update_frame(frame_id: str, frame: Frame):
    success = await state_manager.update_frame(frame_id, frame)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Frame with ID {frame_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Updated frame: {frame_id}")
    return frame


@router.delete("/{frame_id}")
async def delete_frame(frame_id: str):
    success = await state_manager.delete_frame(frame_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Frame with ID {frame_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Deleted frame: {frame_id}")
    return {"message": f"Frame {frame_id} deleted successfully"}
