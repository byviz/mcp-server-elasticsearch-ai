"""Unit tests for Datadog authentication."""

import pytest

from datadog_mcp.auth import DatadogClient
from datadog_mcp.config import DatadogConfig


class TestDatadogClient:
    """Tests for DatadogClient authentication."""

    @pytest.fixture
    def datadog_config(self) -> DatadogConfig:
        """Create a test Datadog configuration."""
        return DatadogConfig(
            base_url="https://api.datadoghq.com",
            api_key="test-api-key",
            app_key="test-app-key",
            timeout=30,
        )

    def test_client_initialization(self, datadog_config: DatadogConfig) -> None:
        """Test DatadogClient initialization."""
        client = DatadogClient(datadog_config)
        
        assert client.base_url == "https://api.datadoghq.com"
        assert client.api_key == "test-api-key"
        assert client.app_key == "test-app-key"
        assert client.timeout == 30

    def test_get_auth_headers(self, datadog_config: DatadogConfig) -> None:
        """Test authentication header generation."""
        client = DatadogClient(datadog_config)
        headers = client.get_auth_headers()
        
        assert headers["DD-API-KEY"] == "test-api-key"
        assert headers["DD-APPLICATION-KEY"] == "test-app-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "datadog-mcp/1.0.0"

    def test_headers_not_exposed_in_repr(self, datadog_config: DatadogConfig) -> None:
        """Test that sensitive data is not exposed in string representation."""
        client = DatadogClient(datadog_config)
        client_str = str(client)
        
        # Ensure API keys are not in string representation
        assert "test-api-key" not in client_str
        assert "test-app-key" not in client_str