"""Configuration models for Elasticsearch MCP server."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    pass


class ElasticsearchConfig(BaseModel):
    """Configuration for Elasticsearch connection."""

    base_url: str
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    cloud_id: str | None = None
    timeout: int = 30
    verify_certs: bool = True
    ca_certs: str | None = None
    client_cert: str | None = None
    client_key: str | None = None
    openapi_spec_path: str | None = None

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "Base URL cannot be empty"
            raise ValueError(msg)
        return v.strip()

    def has_auth(self) -> bool:
        """Check if authentication is configured."""
        return bool(
            self.api_key or
            (self.username and self.password) or
            self.cloud_id
        )


class MCPConfig(BaseModel):
    """Configuration for MCP server."""

    transport: str = "stdio"
    port: int = 8000
    log_level: str = "INFO"
    enable_security_filtering: bool = True


class AppConfig(BaseModel):
    """Main application configuration."""

    elasticsearch: ElasticsearchConfig
    mcp: MCPConfig

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load configuration from environment variables."""
        # Elasticsearch connection settings
        base_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        username = os.getenv("ELASTICSEARCH_USERNAME")
        password = os.getenv("ELASTICSEARCH_PASSWORD")
        api_key = os.getenv("ELASTICSEARCH_API_KEY")
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        timeout = int(os.getenv("ELASTICSEARCH_TIMEOUT", "30"))
        verify_certs = os.getenv("ELASTICSEARCH_VERIFY_CERTS", "true").lower() in ("true", "1", "yes")
        ca_certs = os.getenv("ELASTICSEARCH_CA_CERTS")
        client_cert = os.getenv("ELASTICSEARCH_CLIENT_CERT")
        client_key = os.getenv("ELASTICSEARCH_CLIENT_KEY")
        openapi_spec_path = os.getenv("ELASTICSEARCH_OPENAPI_SPEC_PATH")

        # MCP server settings
        transport = os.getenv("MCP_TRANSPORT", "stdio")
        port = int(os.getenv("MCP_PORT", "8000"))
        log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
        enable_security_filtering = os.getenv(
            "MCP_ENABLE_SECURITY_FILTERING", "true"
        ).lower() in ("true", "1", "yes")

        elasticsearch_config = ElasticsearchConfig(
            base_url=base_url,
            username=username,
            password=password,
            api_key=api_key,
            cloud_id=cloud_id,
            timeout=timeout,
            verify_certs=verify_certs,
            ca_certs=ca_certs,
            client_cert=client_cert,
            client_key=client_key,
            openapi_spec_path=openapi_spec_path,
        )

        mcp_config = MCPConfig(
            transport=transport,
            port=port,
            log_level=log_level,
            enable_security_filtering=enable_security_filtering,
        )

        return cls(
            elasticsearch=elasticsearch_config,
            mcp=mcp_config,
        )
