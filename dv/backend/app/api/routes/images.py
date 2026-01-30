"""
API routes for image layer management.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List
import os

from ...models.schemas import ImageLayer, FileUploadResponse
from ...core.state import state_manager
from ...core.config import settings
from ...core.security import validate_file_upload, sanitize_filename, generate_safe_filename
from ...core.logging import get_logger
from ..websocket import connection_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/images", tags=["images"])

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)


@router.get("", response_model=List[ImageLayer])
async def get_images():
    return await state_manager.get_images()


@router.post("", response_model=ImageLayer, status_code=status.HTTP_201_CREATED)
async def create_image(image: ImageLayer):
    # Check if image with ID already exists
    existing = await state_manager.get_image(image.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image with ID {image.id} already exists",
        )

    await state_manager.add_image(image)
    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Created image: {image.id}")
    return image


@router.get("/{image_id}", response_model=ImageLayer)
async def get_image(image_id: str):
    image = await state_manager.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found",
        )
    return image


@router.put("/{image_id}", response_model=ImageLayer)
async def update_image(image_id: str, image: ImageLayer):
    success = await state_manager.update_image(image_id, image)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Updated image: {image_id}")
    return image


@router.delete("/{image_id}")
async def delete_image(image_id: str):
    success = await state_manager.delete_image(image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found",
        )

    await connection_manager.send_state_update(await state_manager.get_state())
    logger.info(f"Deleted image: {image_id}")
    return {"message": f"Image {image_id} deleted successfully"}


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload an image file.

    Validates file size, type, and extension before saving.
    """
    # Read content and validate the file
    content = await file.read()
    await file.seek(0)

    file_size = await validate_file_upload(file, content)

    # Generate safe filename
    safe_filename = generate_safe_filename(file.filename)
    file_path = os.path.join(settings.upload_dir, safe_filename)

    # Save the file
    try:
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Uploaded file: {safe_filename} ({file_size} bytes)")
        return FileUploadResponse(
            filename=safe_filename,
            url=f"/uploads/{safe_filename}",
            size=file_size,
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}",
        )
