"""Unit test fixtures for Elasticsearch MCP."""

import pytest

from elasticsearch_mcp.config import ElasticsearchConfig, MCPConfig


@pytest.fixture
def sample_elasticsearch_config() -> ElasticsearchConfig:
    """Create a sample ElasticsearchConfig for testing."""
    return ElasticsearchConfig(
        base_url="http://localhost:9200",
        username="test-user",
        password="test-password",
        timeout=30,
        verify_certs=True,
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