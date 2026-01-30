"""
Tests for box API endpoints.
"""
import pytest


def test_get_boxes(client, sample_box):
    """Test getting all boxes."""
    response = client.get("/api/boxes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_box(client, sample_box):
    """Test creating a new box."""
    response = client.post("/api/boxes", json=sample_box)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == sample_box["id"]
    assert data["name"] == sample_box["name"]


def test_create_duplicate_box(client, sample_box):
    """Test that creating a box with duplicate ID fails."""
    # Create first box
    client.post("/api/boxes", json=sample_box)

    # Try to create duplicate
    response = client.post("/api/boxes", json=sample_box)
    assert response.status_code == 400


def test_get_box(client, sample_box):
    """Test getting a specific box."""
    # Create a box first
    client.post("/api/boxes", json=sample_box)

    # Get the box
    response = client.get(f"/api/boxes/{sample_box['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_box["id"]


def test_get_box_not_found(client):
    """Test getting a non-existent box."""
    response = client.get("/api/boxes/non-existent")
    assert response.status_code == 404


def test_update_box(client, sample_box):
    """Test updating a box."""
    # Create a box first
    client.post("/api/boxes", json=sample_box)

    # Update the box
    updated_box = sample_box.copy()
    updated_box["name"] = "Updated Box"
    response = client.put(f"/api/boxes/{sample_box['id']}", json=updated_box)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Box"


def test_update_box_not_found(client):
    """Test updating a non-existent box."""
    response = client.put("/api/boxes/non-existent", json={"id": "non-existent"})
    assert response.status_code == 404


def test_delete_box(client, sample_box):
    """Test deleting a box."""
    # Create a box first
    client.post("/api/boxes", json=sample_box)

    # Delete the box
    response = client.delete(f"/api/boxes/{sample_box['id']}")
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data["message"].lower()


def test_delete_box_not_found(client):
    """Test deleting a non-existent box."""
    response = client.delete("/api/boxes/non-existent")
    assert response.status_code == 404


def test_box_validation():
    """Test box data validation."""
    from app.models.schemas import ContainerBox

    # Valid box
    valid_box = ContainerBox(
        id="test",
        name="Test",
        x=0,
        y=0,
    )
    assert valid_box.name == "Test"

    # Invalid coordinates should raise error
    with pytest.raises(Exception):
        ContainerBox(id="test", name="Test", x=-1, y=0)
