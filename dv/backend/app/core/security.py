"""
Security utilities for file validation and input sanitization.
"""
import os
import re
import uuid
from typing import Optional, List
from fastapi import HTTPException, UploadFile
from .config import settings


async def validate_file_upload(file: UploadFile, content: bytes = None) -> int:
    """
    Validate uploaded file for size, type, and extension.

    Args:
        file: The uploaded file to validate
        content: File content if already read

    Raises:
        HTTPException: If validation fails

    Returns:
        The file size in bytes
    """
    # Read content if not provided to get size
    if content is None:
        content = await file.read()
        await file.seek(0)

    file_size = len(content)

    # Check file size
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size / 1024 / 1024}MB"
        )

    # Check content type
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=415,
            detail=f"File type {file.content_type} is not allowed. "
            f"Allowed types: {', '.join(settings.allowed_image_types)}"
        )

    # Check file extension
    if file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in settings.allowed_image_extensions:
            raise HTTPException(
                status_code=415,
                detail=f"File extension {ext} is not allowed. "
                f"Allowed extensions: {', '.join(settings.allowed_image_extensions)}"
            )

    return file_size


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized safe filename
    """
    # Extract filename without path
    filename = os.path.basename(filename)

    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    # Ensure filename isn't empty
    if not filename:
        filename = str(uuid.uuid4())

    return filename


def validate_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF attacks.

    Args:
        url: URL to validate

    Returns:
        True if URL is safe, False otherwise
    """
    if not url:
        return False

    # Basic URL validation
    url_pattern = re.compile(
        r"^(https?:\/\/)?"  # optional scheme
        r"(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|"  # domain
        r"localhost|"  # localhost
        r"127\.0\.0\.1|"  # loopback
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # private class A
        r"172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}|"  # private class B
        r"192\.168\.\d{1,3}\.\d{1,3})"  # private class C
        r"(:\d+)?(\/[^\s]*)?$"  # optional port and path
    )

    if not url_pattern.match(url):
        return False

    # Block internal/private URLs if needed (uncomment for production)
    # blocked_patterns = ["169.254.", "metadata.", "localhost"]
    # for pattern in blocked_patterns:
    #     if pattern in url:
    #         return False

    return True


def generate_safe_filename(original_filename: str) -> str:
    """
    Generate a safe filename with UUID prefix.

    Args:
        original_filename: Original filename

    Returns:
        Safe filename with UUID prefix
    """
    ext = os.path.splitext(sanitize_filename(original_filename))[1]
    return f"{uuid.uuid4()}{ext}"
