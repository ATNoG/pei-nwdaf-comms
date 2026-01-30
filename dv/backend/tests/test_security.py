"""
Tests for security features.
"""
import pytest
from io import BytesIO


def test_file_upload_size_limit(client):
    """Test that large files are rejected."""
    # Create a file larger than the limit (5MB)
    large_content = b"x" * (6 * 1024 * 1024)  # 6MB
    files = {"file": ("large.jpg", BytesIO(large_content), "image/jpeg")}

    response = client.post("/api/images/upload", files=files)
    # Should return 413 (Payload Too Large) or 422 (Validation Error)
    assert response.status_code in [413, 422]


def test_file_upload_invalid_type(client):
    """Test that non-image files are rejected."""
    # Create a small non-image file
    file_content = b"not an image"
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

    response = client.post("/api/images/upload", files=files)
    assert response.status_code == 415


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.options("/api/boxes")
    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
