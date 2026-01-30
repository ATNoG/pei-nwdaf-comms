"""
Application configuration with environment variable support.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Settings
    title: str = "Docker Visual Monitor API"
    version: str = "1.0.0"
    debug: bool = False

    # CORS Settings - parse from comma-separated string
    cors_origins_str: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    cors_allow_credentials: bool = True
    cors_allow_methods_str: str = "GET,POST,PUT,DELETE,OPTIONS"

    @property
    def cors_allow_methods(self) -> List[str]:
        """Parse CORS methods from comma-separated string."""
        return [method.strip() for method in self.cors_allow_methods_str.split(",") if method.strip()]

    cors_allow_headers: List[str] = ["*"]

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    # File Upload Settings
    upload_dir: str = "uploads"
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    allowed_image_extensions: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    allowed_image_types: List[str] = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    # State Persistence
    state_file: str = "data/dashboard_state.json"

    # Monitoring Settings
    status_check_timeout: float = 5.0
    status_cache_ttl: int = 10  # seconds

    # WebSocket Settings
    ws_ping_interval: int = 20
    ws_ping_timeout: int = 20

    # Security Settings
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds


settings = Settings()
