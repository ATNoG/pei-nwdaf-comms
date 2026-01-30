"""
API routes for container box management.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from ...models.schemas import ContainerBox
from ...core.state import state_manager
from ...core.logging import get_logger
from ..websocket import connection_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/boxes", tags=["boxes"])


@router.get("", response_model=List[ContainerBox])
async def get_boxes():
    return await state_manager.get_boxes()


@router.post("", response_model=ContainerBox, status_code=status.HTTP_201_CREATED)
async def create_box(box: ContainerBox):
    # Check if box with ID already exists
    existing = await state_manager.get_box(box.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Box with ID {box.id} already exists",
        )

    await state_manager.add_box(box)
    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Created box: {box.id}")
    return box


@router.get("/{box_id}", response_model=ContainerBox)
async def get_box(box_id: str):
    box = await state_manager.get_box(box_id)
    if not box:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Box with ID {box_id} not found",
        )
    return box


@router.put("/{box_id}", response_model=ContainerBox)
async def update_box(box_id: str, box: ContainerBox):
    success = await state_manager.update_box(box_id, box)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Box with ID {box_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Updated box: {box_id}")
    return box


@router.delete("/{box_id}")
async def delete_box(box_id: str):
    success = await state_manager.delete_box(box_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Box with ID {box_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Deleted box: {box_id}")
    return {"message": f"Box {box_id} deleted successfully"}
