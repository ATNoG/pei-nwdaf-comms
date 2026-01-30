"""
Main FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .core.security import validate_url
from .api.routes import boxes, lines, images, frames, state, monitoring
from .api.websocket import connection_manager
from .models.schemas import DashboardState

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(f"Starting {settings.title} v{settings.version}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"State file: {settings.state_file}")

    # Wire dependencies for connection-aware polling
    from .services.monitoring import monitoring_service
    from .core.state import state_manager
    connection_manager.set_dependencies(state_manager, monitoring_service)

    yield
    # Shutdown
    await monitoring_service.stop_polling()
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.title,
    version=settings.version,
    debug=settings.debug,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS with proper origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Mount static files for uploads
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Include routers
app.include_router(boxes.router)
app.include_router(lines.router)
app.include_router(images.router)
app.include_router(frames.router)
app.include_router(state.router)
app.include_router(monitoring.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.title,
        "version": settings.version,
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.

    Clients connect to this endpoint to receive instant updates
    when the dashboard state changes.
    """
    await connection_manager.connect(websocket)
    try:
        # Send current state to new client
        from .core.state import state_manager
        from .api.websocket import serialize_state
        await websocket.send_json({
            "type": "state_update",
            "data": serialize_state(await state_manager.get_state())
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back for now (can be used for client-to-server communication)
            logger.debug(f"Received WebSocket message: {data[:100]}")

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


def main():
    """Run the application directly (for development)."""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    main()
