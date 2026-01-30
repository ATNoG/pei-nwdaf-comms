"""
Tests for line API endpoints.
"""
import pytest


def test_get_lines(client, sample_line, sample_box):
    """Test getting all lines."""
    # Create source and target boxes first
    box1 = sample_box.copy()
    box1["id"] = "test-box-1"
    box2 = sample_box.copy()
    box2["id"] = "test-box-2"
    client.post("/api/boxes", json=box1)
    client.post("/api/boxes", json=box2)

    response = client.get("/api/lines")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_line(client, sample_line, sample_box):
    """Test creating a new line."""
    # Create source and target boxes first
    box1 = sample_box.copy()
    box1["id"] = "test-box-1"
    box2 = sample_box.copy()
    box2["id"] = "test-box-2"
    client.post("/api/boxes", json=box1)
    client.post("/api/boxes", json=box2)

    response = client.post("/api/lines", json=sample_line)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == sample_line["id"]


def test_create_duplicate_line(client, sample_line, sample_box):
    """Test that creating a line with duplicate ID fails."""
    # Create boxes first
    box1 = sample_box.copy()
    box1["id"] = "test-box-1"
    box2 = sample_box.copy()
    box2["id"] = "test-box-2"
    client.post("/api/boxes", json=box1)
    client.post("/api/boxes", json=box2)

    # Create first line
    client.post("/api/lines", json=sample_line)

    # Try to create duplicate
    response = client.post("/api/lines", json=sample_line)
    assert response.status_code == 400


def test_get_line(client, sample_line, sample_box):
    """Test getting a specific line."""
    # Create boxes and line
    box1 = sample_box.copy()
    box1["id"] = "test-box-1"
    box2 = sample_box.copy()
    box2["id"] = "test-box-2"
    client.post("/api/boxes", json=box1)
    client.post("/api/boxes", json=box2)
    client.post("/api/lines", json=sample_line)

    response = client.get(f"/api/lines/{sample_line['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_line["id"]


def test_get_line_not_found(client):
    """Test getting a non-existent line."""
    response = client.get("/api/lines/non-existent")
    assert response.status_code == 404


def test_delete_line(client, sample_line, sample_box):
    """Test deleting a line."""
    # Create boxes and line
    box1 = sample_box.copy()
    box1["id"] = "test-box-1"
    box2 = sample_box.copy()
    box2["id"] = "test-box-2"
    client.post("/api/boxes", json=box1)
    client.post("/api/boxes", json=box2)
    client.post("/api/lines", json=sample_line)

    response = client.delete(f"/api/lines/{sample_line['id']}")
    assert response.status_code == 200


def test_delete_line_not_found(client):
    """Test deleting a non-existent line."""
    response = client.delete("/api/lines/non-existent")
    assert response.status_code == 404


def test_line_validation():
    """Test line data validation."""
    from app.models.schemas import ConnectionLine

    # Valid line
    valid_line = ConnectionLine(
        id="test",
        source_box_id="box1",
        target_box_id="box2",
    )
    assert valid_line.id == "test"

    # Invalid color should raise error
    with pytest.raises(Exception):
        ConnectionLine(
            id="test",
            source_box_id="box1",
            target_box_id="box2",
            color="invalid"
        )
