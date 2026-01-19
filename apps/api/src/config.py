"""
Configuration settings for the Code Weaver Pro API
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App Configuration
    app_name: str = "Code Weaver Pro API"
    debug: bool = True
    environment: str = "development"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Supabase Configuration (optional for local development)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None

    # LLM Configuration (for future phases)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # WebSocket Configuration
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()


def get_settings() -> Settings:
    """Dependency injection for settings"""
    return settings
