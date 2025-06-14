"""Configuration models for Datadog MCP server."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    pass


class DatadogConfig(BaseModel):
    """Configuration for Datadog connection."""

    base_url: str
    api_key: str
    app_key: str
    timeout: int = 30
    site: str = "datadoghq.com"
    openapi_spec_path: str | None = None

    @field_validator("base_url", "api_key", "app_key")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "Field cannot be empty"
            raise ValueError(msg)
        return v.strip()


class MCPConfig(BaseModel):
    """Configuration for MCP server."""

    transport: str = "stdio"
    port: int = 8000
    log_level: str = "INFO"
    enable_security_filtering: bool = True


class AppConfig(BaseModel):
    """Main application configuration."""

    datadog: DatadogConfig
    mcp: MCPConfig

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load configuration from environment variables."""
        # Required environment variables
        api_key = os.getenv("DATADOG_API_KEY")
        app_key = os.getenv("DATADOG_APP_KEY")

        if not api_key:
            msg = "DATADOG_API_KEY environment variable is required"
            raise ValueError(msg)
        if not app_key:
            msg = "DATADOG_APP_KEY environment variable is required"
            raise ValueError(msg)

        # Optional environment variables with defaults
        base_url = os.getenv("DATADOG_BASE_URL", "https://api.datadoghq.com")
        timeout = int(os.getenv("DATADOG_TIMEOUT", "30"))
        site = os.getenv("DATADOG_SITE", "datadoghq.com")
        openapi_spec_path = os.getenv("DATADOG_OPENAPI_SPEC_PATH")
        transport = os.getenv("MCP_TRANSPORT", "stdio")
        port = int(os.getenv("MCP_PORT", "8000"))
        log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
        enable_security_filtering = os.getenv(
            "MCP_ENABLE_SECURITY_FILTERING", "true"
        ).lower() in ("true", "1", "yes")

        datadog_config = DatadogConfig(
            base_url=base_url,
            api_key=api_key,
            app_key=app_key,
            timeout=timeout,
            site=site,
            openapi_spec_path=openapi_spec_path,
        )

        mcp_config = MCPConfig(
            transport=transport,
            port=port,
            log_level=log_level,
            enable_security_filtering=enable_security_filtering,
        )

        return cls(datadog=datadog_config, mcp=mcp_config)