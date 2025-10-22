"""
Configuration management for ElyterraX Backend
Loads environment variables and provides configuration settings
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Environment
    env: str = "development"

    # API Configuration
    api_title: str = "ElyterraX API"
    api_version: str = "1.0.0-phase1"

    # Database Configuration
    database_url: str = "postgresql+psycopg://admin:admin@localhost:5432/realestate_dev"
    postgres_user: str = "admin"
    postgres_password: str = "admin"
    postgres_db: str = "realestate_dev"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173,https://app.elyterrax.com"

    # Security & JWT Configuration
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Using lru_cache ensures settings are only loaded once
    """
    return Settings()


# Global settings instance
settings = get_settings()
