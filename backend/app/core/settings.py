"""
Application settings using Pydantic BaseSettings.

Follows 12-factor app principles - all configuration via environment variables
with sensible defaults for local development.
"""

from enum import Enum

from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment modes."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    Uses .env file support via python-dotenv integration.
    """

    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/db"
    """
    Database connection URL for async SQLAlchemy.
    Format: postgresql+asyncpg://user:password@host:port/database
    Override via DATABASE_URL environment variable.
    """

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    """
    Allowed CORS origins for frontend applications.
    Defaults to common local development ports (3000 for Create React App, 5173 for Vite).
    Override via CORS_ORIGINS environment variable (comma-separated list).
    """

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    """
    Application environment mode.
    Options: Environment.DEVELOPMENT, Environment.PRODUCTION
    Controls logging format (colorful console vs JSON).
    Override via ENVIRONMENT environment variable.
    """

    # Logging
    log_level: str = "INFO"
    """
    Application logging level.
    Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Override via LOG_LEVEL environment variable.
    """

    # API Configuration
    api_v1_prefix: str = "/api/v1"
    """
    API version 1 route prefix.
    All v1 endpoints will be mounted under this prefix.
    Override via API_V1_PREFIX environment variable.
    """

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    """
    Secret key for JWT tokens and other cryptographic operations.
    MUST be changed in production to a secure random value.
    Override via SECRET_KEY environment variable.
    """

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def database_url_sync(self) -> str:
        """
        Synchronous database URL for Alembic migrations.
        Converts asyncpg driver to psycopg for sync operations.
        """
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")


# Singleton instance - loaded once at module import
settings = Settings()
"""
Global settings instance following singleton pattern.
Import and use throughout the application:
    from core.settings import settings
"""
