"""Configuration management for AI Red Blue Platform."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "AI Red Blue Platform"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Database
    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    database_pool_size: int = Field(default=5, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, validation_alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: Optional[str] = Field(default=None, validation_alias="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, validation_alias="REDIS_CACHE_TTL")

    # Security
    secret_key: str = Field(default="change-in-production", validation_alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, validation_alias="JWT_EXPIRATION_HOURS")
    encryption_key: Optional[str] = Field(default=None, validation_alias="ENCRYPTION_KEY")

    # AI Providers
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    azure_endpoint: Optional[str] = Field(default=None, validation_alias="AZURE_ENDPOINT")
    azure_api_key: Optional[str] = Field(default=None, validation_alias="AZURE_API_KEY")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # External Tools
    external_tools_path: Optional[Path] = Field(
        default=None, validation_alias="EXTERNAL_TOOLS_PATH"
    )
    tools_timeout: int = Field(default=300, validation_alias="TOOLS_TIMEOUT")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        validation_alias_generator = lambda x: x.upper()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production", "testing"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got: {v}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def database_config(self) -> dict[str, Any]:
        """Get database configuration dictionary."""
        return {
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
        }

    @property
    def cache_config(self) -> dict[str, Any]:
        """Get cache configuration dictionary."""
        return {
            "redis_url": self.redis_url,
            "ttl": self.redis_cache_ttl,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
