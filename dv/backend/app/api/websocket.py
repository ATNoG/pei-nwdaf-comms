"""
WebSocket connection manager for real-time updates.
"""
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, Any
from ..core.logging import get_logger

logger = get_logger(__name__)


def serialize_state(state: Any) -> dict:
    """
    Convert Pydantic models to JSON-serializable dict.

    This handles HttpUrl and other special types by using mode='json'.
    """
    if hasattr(state, 'model_dump'):
        return state.model_dump(mode='json')
    return state


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._state_manager = None
        self._monitoring_service = None

    def set_dependencies(self, state_manager, monitoring_service):
        """Inject dependencies for polling control."""
        self._state_manager = state_manager
        self._monitoring_service = monitoring_service

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

        # Start polling on first connection
        if len(self.active_connections) == 1 and self._monitoring_service:
            await self._monitoring_service.start_polling(
                self._state_manager, self
            )

        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

            # Stop polling when no connections
            if len(self.active_connections) == 0 and self._monitoring_service:
                asyncio.create_task(self._monitoring_service.stop_polling())

            logger.info(
                f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
            )

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message dictionary to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_state_update(self, state: Any) -> None:
        """
        Broadcast a state update to all connected clients.

        Args:
            state: The dashboard state (Pydantic model or dict) to broadcast
        """
        serialized = serialize_state(state)
        await self.broadcast({"type": "state_update", "data": serialized})

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
connection_manager = ConnectionManager()
