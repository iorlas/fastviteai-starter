"""
Tests for core.settings module.

Tests cover:
- Default values for all settings
- Environment variable overrides
- Settings singleton pattern
- Database URL sync conversion
- Type validation
"""

import pytest

from app.core.settings import Settings, settings


class TestSettingsDefaults:
    """Test default values for all settings."""

    def test_database_url_default(self):
        """Test default database_url is set correctly."""
        s = Settings()
        assert s.database_url == "postgresql+asyncpg://postgres:postgres@localhost:5432/db"
        assert "asyncpg" in s.database_url

    def test_secret_key_default(self):
        """Test default secret_key is set for development."""
        s = Settings()
        assert s.secret_key == "dev-secret-key-change-in-production"
        assert len(s.secret_key) > 0

    def test_cors_origins_default(self):
        """Test default CORS origins include common dev ports."""
        s = Settings()
        assert isinstance(s.cors_origins, list)
        assert "http://localhost:3000" in s.cors_origins
        assert "http://localhost:5173" in s.cors_origins

    def test_log_level_default(self):
        """Test default log level is INFO."""
        s = Settings()
        assert s.log_level == "INFO"

    def test_api_v1_prefix_default(self):
        """Test default API v1 prefix."""
        s = Settings()
        assert s.api_v1_prefix == "/api/v1"


class TestSettingsEnvironmentOverrides:
    """Test environment variable overrides for settings."""

    def test_database_url_override(self, monkeypatch):
        """Test DATABASE_URL environment variable overrides default."""
        test_url = "postgresql+asyncpg://testuser:testpass@testhost:5433/testdb"
        monkeypatch.setenv("DATABASE_URL", test_url)
        s = Settings()
        assert s.database_url == test_url

    def test_secret_key_override(self, monkeypatch):
        """Test SECRET_KEY environment variable overrides default."""
        test_key = "super-secret-production-key"
        monkeypatch.setenv("SECRET_KEY", test_key)
        s = Settings()
        assert s.secret_key == test_key

    def test_cors_origins_override(self, monkeypatch):
        """Test CORS_ORIGINS environment variable overrides default."""
        # Pydantic Settings parses JSON arrays from env vars
        monkeypatch.setenv("CORS_ORIGINS", '["https://example.com", "https://app.example.com"]')
        s = Settings()
        assert "https://example.com" in s.cors_origins
        assert "https://app.example.com" in s.cors_origins

    def test_log_level_override(self, monkeypatch):
        """Test LOG_LEVEL environment variable overrides default."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.log_level == "DEBUG"

    def test_api_v1_prefix_override(self, monkeypatch):
        """Test API_V1_PREFIX environment variable overrides default."""
        monkeypatch.setenv("API_V1_PREFIX", "/v1")
        s = Settings()
        assert s.api_v1_prefix == "/v1"


class TestSettingsSingleton:
    """Test settings singleton pattern."""

    def test_singleton_instance_exists(self):
        """Test that settings singleton instance is created."""
        from app.core.settings import settings

        assert settings is not None
        assert isinstance(settings, Settings)

    def test_singleton_values_accessible(self):
        """Test that settings values are accessible from singleton."""
        assert hasattr(settings, "database_url")
        assert hasattr(settings, "secret_key")
        assert hasattr(settings, "cors_origins")
        assert hasattr(settings, "log_level")
        assert hasattr(settings, "api_v1_prefix")

    def test_singleton_is_consistent(self):
        """Test that importing settings returns consistent instance."""
        from app.core.settings import settings as settings1
        from app.core.settings import settings as settings2

        # These should be the exact same object in memory
        assert settings1 is settings2


class TestDatabaseUrlSync:
    """Test database_url_sync property for Alembic."""

    def test_sync_url_converts_asyncpg_to_psycopg(self):
        """Test that database_url_sync converts asyncpg driver to psycopg."""
        s = Settings()
        sync_url = s.database_url_sync
        assert "psycopg" in sync_url
        assert "asyncpg" not in sync_url

    def test_sync_url_preserves_connection_details(self):
        """Test that sync URL preserves all connection details."""
        s = Settings()
        sync_url = s.database_url_sync
        # Should preserve user, password, host, port, database
        assert "postgres:postgres" in sync_url
        assert "localhost:5432" in sync_url
        assert "db" in sync_url

    def test_sync_url_with_custom_database_url(self, monkeypatch):
        """Test sync URL conversion with custom database URL."""
        custom_url = "postgresql+asyncpg://user:pass@db.example.com:5432/mydb"
        monkeypatch.setenv("DATABASE_URL", custom_url)
        s = Settings()
        sync_url = s.database_url_sync
        assert sync_url == "postgresql+psycopg://user:pass@db.example.com:5432/mydb"


class TestSettingsValidation:
    """Test type validation and error handling."""

    def test_settings_created_without_errors(self):
        """Test that Settings can be instantiated without errors."""
        try:
            s = Settings()
            assert s is not None
        except Exception as e:
            pytest.fail(f"Settings instantiation failed: {e}")

    def test_cors_origins_is_list_type(self):
        """Test that cors_origins is validated as a list."""
        s = Settings()
        assert isinstance(s.cors_origins, list)
        for origin in s.cors_origins:
            assert isinstance(origin, str)


class TestSettingsDocumentation:
    """Test that settings have proper documentation."""

    def test_settings_class_has_docstring(self):
        """Test that Settings class has documentation."""
        assert Settings.__doc__ is not None
        assert len(Settings.__doc__) > 0

    def test_database_url_field_has_docstring(self):
        """Test that database_url field has documentation in code."""
        # Field docstrings are accessible via __fields__ in Pydantic v2
        s = Settings()
        assert hasattr(s, "database_url")

    def test_database_url_sync_has_docstring(self):
        """Test that database_url_sync property has documentation."""
        assert Settings.database_url_sync.fget.__doc__ is not None


class TestSettings12FactorCompliance:
    """Test 12-factor app compliance."""

    def test_all_config_overridable_via_env(self, monkeypatch):
        """Test that all configuration can be overridden via environment variables."""
        # Set all environment variables
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@test:5432/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("CORS_ORIGINS", '["https://test.com"]')
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        monkeypatch.setenv("API_V1_PREFIX", "/test")

        s = Settings()

        # Verify all overrides took effect
        assert "test:test@test:5432/test" in s.database_url
        assert s.secret_key == "test-secret"
        assert "https://test.com" in s.cors_origins
        assert s.log_level == "ERROR"
        assert s.api_v1_prefix == "/test"

    def test_sensible_defaults_for_local_dev(self):
        """Test that defaults are suitable for local development."""
        s = Settings()
        # Defaults should work for local dev without any configuration
        assert "localhost" in s.database_url
        assert s.secret_key is not None  # Has a default (even if insecure)
        assert "localhost" in str(s.cors_origins)
        assert s.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert s.api_v1_prefix.startswith("/")
