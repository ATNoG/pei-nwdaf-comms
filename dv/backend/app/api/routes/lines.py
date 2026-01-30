"""
API routes for connection line management.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from ...models.schemas import ConnectionLine
from ...core.state import state_manager
from ...core.logging import get_logger
from ..websocket import connection_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/lines", tags=["lines"])


@router.get("", response_model=List[ConnectionLine])
async def get_lines():
    return await state_manager.get_lines()


@router.post("", response_model=ConnectionLine, status_code=status.HTTP_201_CREATED)
async def create_line(line: ConnectionLine):
    # Check if line with ID already exists
    existing = await state_manager.get_line(line.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Line with ID {line.id} already exists",
        )

    await state_manager.add_line(line)
    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Created line: {line.id}")
    return line


@router.get("/{line_id}", response_model=ConnectionLine)
async def get_line(line_id: str):
    line = await state_manager.get_line(line_id)
    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Line with ID {line_id} not found",
        )
    return line


@router.put("/{line_id}", response_model=ConnectionLine)
async def update_line(line_id: str, line: ConnectionLine):
    success = await state_manager.update_line(line_id, line)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Line with ID {line_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Updated line: {line_id}")
    return line


@router.delete("/{line_id}")
async def delete_line(line_id: str):
    success = await state_manager.delete_line(line_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Line with ID {line_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Deleted line: {line_id}")
    return {"message": f"Line {line_id} deleted successfully"}
