"""Datadog MCP server using FastMCP OpenAPI integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

# Import patches to apply them
from . import patches  # noqa: F401

if TYPE_CHECKING:
    from fastmcp.server.openapi import FastMCPOpenAPI

from datadog_mcp.auth import DatadogClient
from datadog_mcp.config import AppConfig


class DatadogMCPServer:
    """MCP server for Datadog integration using FastMCP OpenAPI."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize the server with configuration."""
        self.config = config
        self.datadog_client = DatadogClient(config.datadog)
        self.mcp_server: FastMCPOpenAPI | None = None

    def _get_bundled_spec_path(self) -> Path:
        """Get the path to the bundled OpenAPI specification."""
        return Path(__file__).parent / "specs" / "datadog-v2.yaml"

    def _load_openapi_spec(self) -> dict[str, Any]:
        """Load the OpenAPI specification from file or use bundled version."""
        import logging

        logger = logging.getLogger("datadog_mcp")

        # Use custom path if provided, otherwise use bundled spec
        if self.config.datadog.openapi_spec_path:
            spec_path = Path(self.config.datadog.openapi_spec_path)
            logger.info(f"Using custom OpenAPI spec: {spec_path}")
        else:
            spec_path = self._get_bundled_spec_path()
            logger.info("Using bundled OpenAPI spec")

        try:
            with open(spec_path, encoding="utf-8") as f:
                if spec_path.suffix in [".yaml", ".yml"]:
                    import yaml
                    spec: dict[str, Any] = yaml.safe_load(f)
                else:
                    spec = json.load(f)
                return spec
        except FileNotFoundError as e:
            msg = f"OpenAPI spec file not found: {spec_path}"
            raise FileNotFoundError(msg) from e
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            msg = f"Invalid specification in file {spec_path}: {e}"
            raise ValueError(msg) from e

    async def _create_authenticated_client(self) -> httpx.AsyncClient:
        """Create an authenticated HTTP client for Datadog API calls."""
        headers = self.datadog_client.get_auth_headers()

        return httpx.AsyncClient(
            base_url=self.config.datadog.base_url,
            headers=headers,
            timeout=self.config.datadog.timeout,
        )

    def _get_route_filters(self) -> list[RouteMap]:
        """Get route filtering rules for safe observability-focused tools.

        Security Model:
        1. DENY ALL destructive operations (POST, PUT, PATCH, DELETE)
        2. ALLOW ONLY specific read-only GET endpoints
        3. DEFAULT DENY everything else

        This whitelist approach ensures only safe, read-only operations
        are exposed through the MCP interface.
        """
        # Define safe read-only endpoints for observability workflows
        safe_endpoints = [
            # Metrics and time-series data
            r"^/api/v2/metrics.*",  # Query metrics data
            r"^/api/v2/query/.*",  # Time-series queries
            # Dashboards and visualizations
            r"^/api/v2/dashboards.*",  # Dashboard configurations
            r"^/api/v2/notebooks.*",  # Notebook data
            # Monitoring and alerts
            r"^/api/v2/monitors.*",  # Monitor configurations
            r"^/api/v2/downtime.*",  # Scheduled downtimes
            r"^/api/v2/synthetics.*",  # Synthetic tests
            # Logs and events
            r"^/api/v2/logs/events/search$",  # Search logs
            r"^/api/v2/logs/events$",  # List log events
            r"^/api/v2/logs/config.*",  # Log pipeline configs
            # APM and traces
            r"^/api/v2/apm/.*",  # APM data
            r"^/api/v2/traces/.*",  # Trace data
            r"^/api/v2/spans/.*",  # Span data
            # Infrastructure
            r"^/api/v2/hosts.*",  # Host information
            r"^/api/v2/tags.*",  # Tag management (read)
            r"^/api/v2/usage.*",  # Usage statistics
            # Service management
            r"^/api/v2/services.*",  # Service catalog
            r"^/api/v2/slos.*",  # Service level objectives
            r"^/api/v2/incidents.*",  # Incident management
            # Security and compliance
            r"^/api/v2/security_monitoring.*",  # Security signals
            r"^/api/v2/cloud_workload_security.*",  # CWS data
            # Teams and organization (read-only)
            r"^/api/v2/users.*",  # User information
            r"^/api/v2/roles.*",  # Role information
            r"^/api/v2/teams.*",  # Team structure
            # API metadata
            r"^/api/v2/api_keys$",  # List API keys (no create/delete)
            r"^/api/v2/application_keys$",  # List app keys (no create/delete)
        ]

        filters = [
            # SECURITY: Block ALL destructive operations first
            RouteMap(
                methods=["POST", "PUT", "PATCH", "DELETE"], mcp_type=MCPType.EXCLUDE
            ),
        ]

        # Add whitelisted read-only endpoints
        filters.extend(
            RouteMap(
                pattern=pattern,
                methods=["GET"],
                mcp_type=MCPType.TOOL,
            )
            for pattern in safe_endpoints
        )

        # SECURITY: Default deny everything else
        filters.append(RouteMap(pattern=r".*", mcp_type=MCPType.EXCLUDE))

        return filters

    async def initialize(self) -> None:
        """Initialize the FastMCP server with Datadog OpenAPI spec."""
        import logging

        logger = logging.getLogger("datadog_mcp")

        # Load OpenAPI specification
        openapi_spec = self._load_openapi_spec()

        # Create authenticated client
        auth_client = await self._create_authenticated_client()

        # Create FastMCP server from OpenAPI specification
        if self.config.mcp.enable_security_filtering:
            # Use security filtering (default, recommended)
            route_maps = self._get_route_filters()
            logger.info(
                "Security filtering ENABLED - only safe read-only endpoints exposed"
            )
        else:
            # WARNING: No security filtering - exposes ALL Datadog API endpoints
            route_maps = None
            logger.warning(
                "Security filtering DISABLED - ALL Datadog API endpoints exposed including destructive operations!"
            )

        self.mcp_server = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=auth_client,
            route_maps=route_maps,
        )

    def run(self) -> None:
        """Run the MCP server with the configured transport."""
        if not self.mcp_server:
            msg = "Server not initialized. Call initialize() first."
            raise RuntimeError(msg)

        transport = self.config.mcp.transport

        if transport == "stdio":
            self.mcp_server.run("stdio")
        elif transport == "http":
            self.mcp_server.run("streamable-http", port=self.config.mcp.port)
        elif transport == "sse":
            self.mcp_server.run("sse", port=self.config.mcp.port)
        else:
            msg = f"Unsupported transport: {transport}"
            raise ValueError(msg)

    async def start(self) -> None:
        """Initialize and run the server."""
        await self.initialize()
        # Note: run() is synchronous and will block
        self.run()