"""
State management for the dashboard.
"""
import json
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from cachetools import TTLCache

from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import (
    ContainerBox,
    ConnectionLine,
    ImageLayer,
    Frame,
    DashboardState,
)

logger = get_logger(__name__)


class StateManager:
    """
    Async state manager with caching and persistence.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._state: DashboardState = DashboardState()
        self._status_cache: TTLCache = TTLCache(
            maxsize=1000, ttl=settings.status_cache_ttl
        )
        self._ensure_data_dir()
        # Load state synchronously during init
        self._load_state_sync()

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        data_dir = Path(settings.state_file).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    def _load_state_sync(self) -> None:
        """Load state from file synchronously."""
        try:
            if os.path.exists(settings.state_file):
                with open(settings.state_file, "r") as f:
                    data = json.load(f)
                    self._state = DashboardState(**data)
                logger.info(f"Loaded state from {settings.state_file}")
            else:
                logger.info("No existing state file found, starting with empty state")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self._state = DashboardState()

    async def _save_state(self) -> None:
        """Save state to file asynchronously."""
        try:
            # Create backup before saving
            if os.path.exists(settings.state_file):
                backup_path = f"{settings.state_file}.backup"
                os.replace(settings.state_file, backup_path)

            # Write to a temp file first, then atomic rename
            # Use mode='json' to convert HttpUrl and other special types to strings
            temp_path = f"{settings.state_file}.tmp"
            with open(temp_path, "w") as f:
                json.dump(self._state.model_dump(mode='json'), f, indent=2)
            os.replace(temp_path, settings.state_file)
            logger.debug(f"Saved state to {settings.state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    # Box operations
    async def get_boxes(self) -> List[ContainerBox]:
        """Get all boxes."""
        async with self._lock:
            return self._state.boxes.copy()

    async def get_box(self, box_id: str) -> Optional[ContainerBox]:
        """Get a specific box by ID."""
        async with self._lock:
            for box in self._state.boxes:
                if box.id == box_id:
                    return box
            return None

    async def add_box(self, box: ContainerBox) -> None:
        """Add a new box."""
        async with self._lock:
            self._state.boxes.append(box)
            await self._save_state()

    async def update_box(self, box_id: str, box: ContainerBox) -> bool:
        """Update an existing box."""
        async with self._lock:
            for i, existing_box in enumerate(self._state.boxes):
                if existing_box.id == box_id:
                    self._state.boxes[i] = box
                    await self._save_state()
                    return True
            return False

    async def delete_box(self, box_id: str) -> bool:
        """Delete a box and its connected lines."""
        async with self._lock:
            for i, box in enumerate(self._state.boxes):
                if box.id == box_id:
                    self._state.boxes.pop(i)
                    # Remove connected lines
                    self._state.lines = [
                        line
                        for line in self._state.lines
                        if line.source_box_id != box_id and line.target_box_id != box_id
                    ]
                    await self._save_state()
                    return True
            return False

    # Line operations
    async def get_lines(self) -> List[ConnectionLine]:
        """Get all lines."""
        async with self._lock:
            return self._state.lines.copy()

    async def get_line(self, line_id: str) -> Optional[ConnectionLine]:
        """Get a specific line by ID."""
        async with self._lock:
            for line in self._state.lines:
                if line.id == line_id:
                    return line
            return None

    async def add_line(self, line: ConnectionLine) -> None:
        """Add a new line."""
        async with self._lock:
            self._state.lines.append(line)
            await self._save_state()

    async def update_line(self, line_id: str, line: ConnectionLine) -> bool:
        """Update an existing line."""
        async with self._lock:
            for i, existing_line in enumerate(self._state.lines):
                if existing_line.id == line_id:
                    self._state.lines[i] = line
                    await self._save_state()
                    return True
            return False

    async def delete_line(self, line_id: str) -> bool:
        """Delete a line."""
        async with self._lock:
            for i, line in enumerate(self._state.lines):
                if line.id == line_id:
                    self._state.lines.pop(i)
                    await self._save_state()
                    return True
            return False

    # Image operations
    async def get_images(self) -> List[ImageLayer]:
        """Get all images."""
        async with self._lock:
            return self._state.images.copy()

    async def get_image(self, image_id: str) -> Optional[ImageLayer]:
        """Get a specific image by ID."""
        async with self._lock:
            for image in self._state.images:
                if image.id == image_id:
                    return image
            return None

    async def add_image(self, image: ImageLayer) -> None:
        """Add a new image."""
        async with self._lock:
            self._state.images.append(image)
            await self._save_state()

    async def update_image(self, image_id: str, image: ImageLayer) -> bool:
        """Update an existing image."""
        async with self._lock:
            for i, existing_image in enumerate(self._state.images):
                if existing_image.id == image_id:
                    self._state.images[i] = image
                    await self._save_state()
                    return True
            return False

    async def delete_image(self, image_id: str) -> bool:
        """Delete an image."""
        async with self._lock:
            for i, image in enumerate(self._state.images):
                if image.id == image_id:
                    self._state.images.pop(i)
                    await self._save_state()
                    return True
            return False

    # Frame operations
    async def get_frames(self) -> List[Frame]:
        """Get all frames."""
        async with self._lock:
            return self._state.frames.copy()

    async def get_frame(self, frame_id: str) -> Optional[Frame]:
        """Get a specific frame by ID."""
        async with self._lock:
            for frame in self._state.frames:
                if frame.id == frame_id:
                    return frame
            return None

    async def add_frame(self, frame: Frame) -> None:
        """Add a new frame."""
        async with self._lock:
            self._state.frames.append(frame)
            await self._save_state()

    async def update_frame(self, frame_id: str, frame: Frame) -> bool:
        """Update an existing frame."""
        async with self._lock:
            for i, existing_frame in enumerate(self._state.frames):
                if existing_frame.id == frame_id:
                    self._state.frames[i] = frame
                    await self._save_state()
                    return True
            return False

    async def delete_frame(self, frame_id: str) -> bool:
        """Delete a frame."""
        async with self._lock:
            for i, frame in enumerate(self._state.frames):
                if frame.id == frame_id:
                    self._state.frames.pop(i)
                    await self._save_state()
                    return True
            return False

    # View operations
    async def set_view(self, zoom: float, pan_x: float, pan_y: float) -> None:
        """Set view properties."""
        async with self._lock:
            self._state.zoom = zoom
            self._state.pan_x = pan_x
            self._state.pan_y = pan_y
            await self._save_state()

    async def toggle_lock(self) -> bool:
        """Toggle lock state."""
        async with self._lock:
            self._state.locked = not self._state.locked
            await self._save_state()
            return self._state.locked

    # Status cache operations
    def get_status(self, box_id: str) -> Optional[Dict]:
        """Get cached status for a box."""
        return self._status_cache.get(box_id)

    def set_status(self, box_id: str, status: Dict) -> None:
        """Set cached status for a box."""
        self._status_cache[box_id] = status

    # Full state operations
    async def get_state(self) -> DashboardState:
        """Get the full dashboard state with status data."""
        async with self._lock:
            state = self._state.model_copy()
            # Add status data to each box
            for box in state.boxes:
                status = self._status_cache.get(box.id)
                if status:
                    box.statusData = status
            return state

    async def update_state(self, state: DashboardState) -> None:
        """Update the full dashboard state."""
        async with self._lock:
            self._state = state
            await self._save_state()


# Global state manager instance
state_manager = StateManager()
