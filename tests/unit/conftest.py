"""Shared fixtures for unit tests."""

import pytest

from datadog_mcp.config import AppConfig, DatadogConfig, MCPConfig


@pytest.fixture
def sample_datadog_config() -> DatadogConfig:
    """Create a sample DatadogConfig for testing."""
    return DatadogConfig(
        base_url="https://api.datadoghq.com",
        api_key="test-api-key",
        app_key="test-app-key",
        timeout=30,
        site="datadoghq.com",
    )


@pytest.fixture
def sample_mcp_config() -> MCPConfig:
    """Create a sample MCPConfig for testing."""
    return MCPConfig(
        transport="stdio",
        port=8000,
        log_level="INFO",
        enable_security_filtering=True,
    )


@pytest.fixture
def sample_app_config(
    sample_datadog_config: DatadogConfig, sample_mcp_config: MCPConfig
) -> AppConfig:
    """Create a sample AppConfig for testing."""
    return AppConfig(datadog=sample_datadog_config, mcp=sample_mcp_config)