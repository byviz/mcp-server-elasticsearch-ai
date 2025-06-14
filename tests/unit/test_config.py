"""Unit tests for configuration models and loading."""

import os

import pytest

from datadog_mcp.config import AppConfig, DatadogConfig, MCPConfig


class TestDatadogConfig:
    """Tests for DatadogConfig model."""

    def test_model_creation_and_defaults(self) -> None:
        """Test DatadogConfig model creation and default values."""
        config = DatadogConfig(
            base_url="https://api.datadoghq.com",
            api_key="test-api-key",
            app_key="test-app-key"
        )
        assert config.base_url == "https://api.datadoghq.com"
        assert config.api_key == "test-api-key"
        assert config.app_key == "test-app-key"
        assert config.timeout == 30  # default value
        assert config.site == "datadoghq.com"  # default value

    def test_validation_rejects_empty_values(self) -> None:
        """Test that DatadogConfig properly validates required fields."""
        # Empty base_url
        with pytest.raises(ValueError, match="Field cannot be empty"):
            DatadogConfig(base_url="", api_key="test-api-key", app_key="test-app-key")

        # Whitespace-only base_url
        with pytest.raises(ValueError, match="Field cannot be empty"):
            DatadogConfig(base_url="   ", api_key="test-api-key", app_key="test-app-key")

        # Empty api_key
        with pytest.raises(ValueError, match="Field cannot be empty"):
            DatadogConfig(
                base_url="https://api.datadoghq.com", api_key="", app_key="test-app-key"
            )

        # Empty app_key
        with pytest.raises(ValueError, match="Field cannot be empty"):
            DatadogConfig(
                base_url="https://api.datadoghq.com",
                api_key="test-api-key",
                app_key="",
            )

    def test_strips_whitespace(self) -> None:
        """Test that DatadogConfig strips whitespace from string fields."""
        config = DatadogConfig(
            base_url="  https://api.datadoghq.com  ",
            api_key="  test-api-key  ",
            app_key="  test-app-key  ",
        )
        assert config.base_url == "https://api.datadoghq.com"
        assert config.api_key == "test-api-key"
        assert config.app_key == "test-app-key"


class TestMCPConfig:
    """Tests for MCPConfig model."""

    def test_defaults(self) -> None:
        """Test MCPConfig default values."""
        config = MCPConfig()
        assert config.transport == "stdio"
        assert config.port == 8000
        assert config.log_level == "INFO"
        assert config.enable_security_filtering is True


class TestAppConfig:
    """Tests for AppConfig model and environment loading."""

    def test_from_env_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful configuration loading from environment."""
        monkeypatch.setenv("DATADOG_API_KEY", "test-api-key")
        monkeypatch.setenv("DATADOG_APP_KEY", "test-app-key")
        monkeypatch.setenv("DATADOG_BASE_URL", "https://api.datadoghq.eu")
        monkeypatch.setenv("MCP_TRANSPORT", "http")
        monkeypatch.setenv("MCP_PORT", "9000")

        config = AppConfig.from_env()

        assert config.datadog.api_key == "test-api-key"
        assert config.datadog.app_key == "test-app-key"
        assert config.datadog.base_url == "https://api.datadoghq.eu"
        assert config.mcp.transport == "http"
        assert config.mcp.port == 9000

    def test_from_env_missing_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing required environment variables raise errors."""
        # Missing DATADOG_API_KEY
        monkeypatch.delenv("DATADOG_API_KEY", raising=False)
        monkeypatch.setenv("DATADOG_APP_KEY", "test-app-key")
        
        with pytest.raises(ValueError, match="DATADOG_API_KEY environment variable is required"):
            AppConfig.from_env()

        # Missing DATADOG_APP_KEY
        monkeypatch.setenv("DATADOG_API_KEY", "test-api-key")
        monkeypatch.delenv("DATADOG_APP_KEY", raising=False)
        
        with pytest.raises(ValueError, match="DATADOG_APP_KEY environment variable is required"):
            AppConfig.from_env()

    def test_from_env_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default values when optional environment variables are not set."""
        monkeypatch.setenv("DATADOG_API_KEY", "test-api-key")
        monkeypatch.setenv("DATADOG_APP_KEY", "test-app-key")

        config = AppConfig.from_env()

        # Check defaults
        assert config.datadog.base_url == "https://api.datadoghq.com"
        assert config.datadog.timeout == 30
        assert config.datadog.site == "datadoghq.com"
        assert config.mcp.transport == "stdio"
        assert config.mcp.port == 8000
        assert config.mcp.log_level == "INFO"
        assert config.mcp.enable_security_filtering is True

    def test_security_filtering_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test parsing of MCP_ENABLE_SECURITY_FILTERING values."""
        monkeypatch.setenv("DATADOG_API_KEY", "test-api-key")
        monkeypatch.setenv("DATADOG_APP_KEY", "test-app-key")

        # Test true values
        for value in ["true", "True", "TRUE", "1", "yes", "YES"]:
            monkeypatch.setenv("MCP_ENABLE_SECURITY_FILTERING", value)
            config = AppConfig.from_env()
            assert config.mcp.enable_security_filtering is True

        # Test false values
        for value in ["false", "False", "FALSE", "0", "no", "NO"]:
            monkeypatch.setenv("MCP_ENABLE_SECURITY_FILTERING", value)
            config = AppConfig.from_env()
            assert config.mcp.enable_security_filtering is False