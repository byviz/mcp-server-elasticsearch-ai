"""Unit tests for Elasticsearch MCP configuration."""

import os
from unittest.mock import patch

import pytest

from elasticsearch_mcp.config import AppConfig, ElasticsearchConfig, MCPConfig


class TestElasticsearchConfig:
    """Tests for ElasticsearchConfig model."""

    def test_valid_config(self) -> None:
        """Test valid ElasticsearchConfig creation."""
        config = ElasticsearchConfig(
            base_url="http://localhost:9200",
            username="test-user",
            password="test-password",
        )
        assert config.base_url == "http://localhost:9200"
        assert config.username == "test-user"
        assert config.password == "test-password"
        assert config.timeout == 30
        assert config.verify_certs is True

    def test_empty_base_url(self) -> None:
        """Test ElasticsearchConfig with empty base_url."""
        with pytest.raises(ValueError, match="Base URL cannot be empty"):
            ElasticsearchConfig(base_url="")

    def test_has_auth_with_username_password(self) -> None:
        """Test has_auth with username and password."""
        config = ElasticsearchConfig(
            base_url="http://localhost:9200",
            username="test-user",
            password="test-password",
        )
        assert config.has_auth() is True

    def test_has_auth_with_api_key(self) -> None:
        """Test has_auth with API key."""
        config = ElasticsearchConfig(
            base_url="http://localhost:9200",
            api_key="test-api-key",
        )
        assert config.has_auth() is True

    def test_has_auth_with_cloud_id(self) -> None:
        """Test has_auth with cloud ID."""
        config = ElasticsearchConfig(
            base_url="http://localhost:9200",
            cloud_id="test-cloud-id",
        )
        assert config.has_auth() is True

    def test_has_auth_without_credentials(self) -> None:
        """Test has_auth without any credentials."""
        config = ElasticsearchConfig(base_url="http://localhost:9200")
        assert config.has_auth() is False


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
    """Tests for AppConfig model."""

    def test_from_env_minimal(self) -> None:
        """Test AppConfig.from_env with minimal configuration."""
        env_vars = {
            "ELASTICSEARCH_URL": "http://localhost:9200",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()
            
        assert config.elasticsearch.base_url == "http://localhost:9200"
        assert config.elasticsearch.username is None
        assert config.elasticsearch.password is None
        assert config.elasticsearch.api_key is None
        assert config.mcp.transport == "stdio"
        assert config.mcp.enable_security_filtering is True

    def test_from_env_full_config(self) -> None:
        """Test AppConfig.from_env with full configuration."""
        env_vars = {
            "ELASTICSEARCH_URL": "https://elasticsearch.example.com:9200",
            "ELASTICSEARCH_USERNAME": "elastic",
            "ELASTICSEARCH_PASSWORD": "changeme",
            "ELASTICSEARCH_API_KEY": "test-api-key",
            "ELASTICSEARCH_CLOUD_ID": "test-cloud-id",
            "ELASTICSEARCH_TIMEOUT": "60",
            "ELASTICSEARCH_VERIFY_CERTS": "false",
            "MCP_TRANSPORT": "http",
            "MCP_PORT": "9000",
            "MCP_LOG_LEVEL": "DEBUG",
            "MCP_ENABLE_SECURITY_FILTERING": "false",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()
            
        assert config.elasticsearch.base_url == "https://elasticsearch.example.com:9200"
        assert config.elasticsearch.username == "elastic"
        assert config.elasticsearch.password == "changeme"
        assert config.elasticsearch.api_key == "test-api-key"
        assert config.elasticsearch.cloud_id == "test-cloud-id"
        assert config.elasticsearch.timeout == 60
        assert config.elasticsearch.verify_certs is False
        assert config.mcp.transport == "http"
        assert config.mcp.port == 9000
        assert config.mcp.log_level == "DEBUG"
        assert config.mcp.enable_security_filtering is False