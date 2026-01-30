"""
Pytest configuration and fixtures.
"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_box():
    """Create a sample container box for testing."""
    return {
        "id": "test-box-1",
        "name": "Test Box",
        "x": 100,
        "y": 200,
        "status_url": "https://httpbin.org/status/200",
        "parameters": {},
        "expanded": False,
        "visible_on_map": [],
        "width": 200,
        "height": 100,
    }


@pytest.fixture
def sample_line():
    """Create a sample connection line for testing."""
    return {
        "id": "test-line-1",
        "source_box_id": "test-box-1",
        "target_box_id": "test-box-2",
        "color": "#000000",
        "polling_interval": 2,
        "change_on_response": False,
        "red_on_failure": False,
    }


@pytest.fixture
def sample_image():
    """Create a sample image layer for testing."""
    return {
        "id": "test-image-1",
        "name": "Test Image",
        "layer_type": "background",
        "url": "https://example.com/image.jpg",
        "x": 0,
        "y": 0,
        "width": 800,
        "height": 600,
    }
