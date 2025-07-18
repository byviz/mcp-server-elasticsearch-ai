"""Unit tests for Elasticsearch authentication."""

import pytest

from elasticsearch_mcp.auth import ElasticsearchClient
from elasticsearch_mcp.config import ElasticsearchConfig


class TestElasticsearchClient:
    """Tests for ElasticsearchClient authentication."""

    @pytest.fixture
    def elasticsearch_config(self) -> ElasticsearchConfig:
        """Create a test Elasticsearch configuration."""
        return ElasticsearchConfig(
            base_url="http://localhost:9200",
            username="test-user",
            password="test-password",
            timeout=30,
        )

    def test_client_initialization(self, elasticsearch_config: ElasticsearchConfig) -> None:
        """Test ElasticsearchClient initialization."""
        client = ElasticsearchClient(elasticsearch_config)
        
        assert client.base_url == "http://localhost:9200"
        assert client.username == "test-user"
        assert client.password == "test-password"
        assert client.timeout == 30

    def test_get_auth_headers_basic_auth(self, elasticsearch_config: ElasticsearchConfig) -> None:
        """Test authentication header generation for basic auth."""
        client = ElasticsearchClient(elasticsearch_config)
        headers = client.get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "elasticsearch-mcp/1.0.0"

    def test_get_auth_headers_api_key(self) -> None:
        """Test authentication header generation for API key."""
        config = ElasticsearchConfig(
            base_url="http://localhost:9200",
            api_key="test-api-key",
        )
        client = ElasticsearchClient(config)
        headers = client.get_auth_headers()
        
        assert headers["Authorization"] == "ApiKey test-api-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "elasticsearch-mcp/1.0.0"

    def test_get_auth_headers_no_auth(self) -> None:
        """Test authentication header generation without authentication."""
        config = ElasticsearchConfig(base_url="http://localhost:9200")
        client = ElasticsearchClient(config)
        headers = client.get_auth_headers()
        
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "elasticsearch-mcp/1.0.0"

    def test_get_client_config_default(self, elasticsearch_config: ElasticsearchConfig) -> None:
        """Test HTTP client configuration with defaults."""
        client = ElasticsearchClient(elasticsearch_config)
        config = client.get_client_config()
        
        assert config["timeout"] == 30
        assert config["verify"] is True

    def test_get_client_config_with_certs(self) -> None:
        """Test HTTP client configuration with certificates."""
        config = ElasticsearchConfig(
            base_url="https://localhost:9200",
            ca_certs="/path/to/ca.crt",
            client_cert="/path/to/client.crt",
            client_key="/path/to/client.key",
            verify_certs=False,
        )
        client = ElasticsearchClient(config)
        client_config = client.get_client_config()
        
        assert client_config["verify"] == "/path/to/ca.crt"
        assert client_config["cert"] == ("/path/to/client.crt", "/path/to/client.key")

    def test_headers_not_exposed_in_repr(self, elasticsearch_config: ElasticsearchConfig) -> None:
        """Test that sensitive data is not exposed in string representation."""
        client = ElasticsearchClient(elasticsearch_config)
        client_str = str(client)
        
        # Ensure credentials are not in string representation
        assert "test-user" not in client_str
        assert "test-password" not in client_str