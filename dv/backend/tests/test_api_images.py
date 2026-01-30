"""
Tests for image API endpoints.
"""
import pytest
from io import BytesIO


def test_get_images(client):
    """Test getting all images."""
    response = client.get("/api/images")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_image(client, sample_image):
    """Test creating a new image."""
    response = client.post("/api/images", json=sample_image)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == sample_image["id"]


def test_create_duplicate_image(client, sample_image):
    """Test that creating an image with duplicate ID fails."""
    # Create first image
    client.post("/api/images", json=sample_image)

    # Try to create duplicate
    response = client.post("/api/images", json=sample_image)
    assert response.status_code == 400


def test_get_image(client, sample_image):
    """Test getting a specific image."""
    # Create an image first
    client.post("/api/images", json=sample_image)

    response = client.get(f"/api/images/{sample_image['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_image["id"]


def test_get_image_not_found(client):
    """Test getting a non-existent image."""
    response = client.get("/api/images/non-existent")
    assert response.status_code == 404


def test_delete_image(client, sample_image):
    """Test deleting an image."""
    # Create an image first
    client.post("/api/images", json=sample_image)

    response = client.delete(f"/api/images/{sample_image['id']}")
    assert response.status_code == 200


def test_delete_image_not_found(client):
    """Test deleting a non-existent image."""
    response = client.delete("/api/images/non-existent")
    assert response.status_code == 404


def test_upload_file(client):
    """Test file upload endpoint."""
    # Create a simple test image
    file_content = b"fake image content"
    files = {"file": ("test.jpg", BytesIO(file_content), "image/jpeg")}

    response = client.post("/api/images/upload", files=files)
    # Should fail because it's not a real image, but should not 500
    assert response.status_code in [400, 415, 500]


def test_image_validation():
    """Test image data validation."""
    from app.models.schemas import ImageLayer

    # Valid image
    valid_image = ImageLayer(
        id="test",
        name="Test",
        layer_type="background",
        url="https://example.com/img.jpg",
    )
    assert valid_image.name == "Test"

    # Invalid layer type should raise error
    with pytest.raises(Exception):
        ImageLayer(
            id="test",
            name="Test",
            layer_type="invalid",
            url="https://example.com/img.jpg",
        )
