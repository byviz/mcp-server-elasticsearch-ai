"""Elasticsearch MCP server using FastMCP OpenAPI integration."""

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

from elasticsearch_mcp.auth import ElasticsearchClient
from elasticsearch_mcp.config import AppConfig
from elasticsearch_mcp.optimized_tools import OptimizedAPMTools


class OptimizedElasticsearchClient:
    """Wrapper client that intercepts optimized endpoints."""

    def __init__(self, original_client: httpx.AsyncClient, optimized_tools: OptimizedAPMTools):
        self.original_client = original_client
        self.optimized_tools = optimized_tools
        self.base_url = original_client.base_url
        self.headers = original_client.headers

    def _create_response(self, status_code: int, json_data: dict, url: str) -> httpx.Response:
        """Create a valid httpx.Response object with proper request instance."""
        import json as json_lib

        # Create a mock request
        request = httpx.Request(
            method="GET",
            url=url,
            headers=self.headers
        )

        # Create response with proper content
        content = json_lib.dumps(json_data).encode('utf-8')

        response = httpx.Response(
            status_code=status_code,
            content=content,
            headers={"content-type": "application/json"},
            request=request
        )

        return response

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Intercept requests to optimized endpoints."""
        # Check if this is an optimized endpoint
        if method == "GET":
            if url.endswith("/_apm/trace/analyze") or "/_apm/trace/analyze?" in url:
                try:
                    # Debug: Print the URL and kwargs being processed
                    print(f"DEBUG: Processing URL: {url}")
                    print(f"DEBUG: kwargs: {kwargs}")

                    # Parse query parameters from URL
                    from urllib.parse import parse_qs, urlparse
                    parsed_url = urlparse(url)
                    query_params = parse_qs(parsed_url.query)

                    # Debug: Print parsed parameters
                    print(f"DEBUG: Parsed query params: {query_params}")

                    # Extract parameters from URL query params or kwargs (FastMCP sends params in kwargs)
                    trace_id = None
                    include_errors = True
                    include_metrics = True

                    # Try to get from URL query params first
                    if query_params.get("trace_id"):
                        trace_id = query_params.get("trace_id", [None])[0]
                        include_errors = query_params.get("include_errors", ["true"])[0].lower() == "true"
                        include_metrics = query_params.get("include_metrics", ["true"])[0].lower() == "true"

                    # If not found in URL, try kwargs (FastMCP way)
                    if not trace_id and 'params' in kwargs:
                        params = kwargs['params']
                        trace_id = params.get("trace_id")
                        include_errors = params.get("include_errors", True)
                        include_metrics = params.get("include_metrics", True)

                    # If still not found, try direct kwargs
                    if not trace_id:
                        trace_id = kwargs.get("trace_id")
                        include_errors = kwargs.get("include_errors", True)
                        include_metrics = kwargs.get("include_metrics", True)

                    print(f"DEBUG: Extracted trace_id: {trace_id}")
                    print(f"DEBUG: Extracted include_errors: {include_errors}")
                    print(f"DEBUG: Extracted include_metrics: {include_metrics}")

                    if not trace_id:
                        return self._create_response(400, {"error": "trace_id parameter is required"}, url)

                    result = await self.optimized_tools.analyze_trace_performance(
                        trace_id=trace_id,
                        include_errors=include_errors,
                        include_metrics=include_metrics
                    )
                    return self._create_response(200, result, url)
                except Exception as e:
                    print(f"DEBUG: Exception in analyze_trace_performance: {e}")
                    return self._create_response(500, {"error": str(e)}, url)

            elif url.endswith("/_apm/errors/patterns") or "/_apm/errors/patterns?" in url:
                try:
                    # Parse query parameters from URL
                    from urllib.parse import parse_qs, urlparse
                    parsed_url = urlparse(url)
                    query_params = parse_qs(parsed_url.query)

                    # Extract parameters from URL query params or kwargs (FastMCP sends params in kwargs)
                    time_range = "now-24h"
                    service_name = None
                    error_type = None
                    min_frequency = 1

                    # Try to get from URL query params first
                    if query_params.get("time_range"):
                        time_range = query_params.get("time_range", ["now-24h"])[0]
                        service_name = query_params.get("service_name", [None])[0]
                        error_type = query_params.get("error_type", [None])[0]
                        min_frequency = int(query_params.get("min_frequency", ["1"])[0])

                    # If not found in URL, try kwargs (FastMCP way)
                    if 'params' in kwargs:
                        params = kwargs['params']
                        time_range = params.get("time_range", time_range)
                        service_name = params.get("service_name", service_name)
                        error_type = params.get("error_type", error_type)
                        min_frequency = params.get("min_frequency", min_frequency)

                    # If still not found, try direct kwargs
                    time_range = kwargs.get("time_range", time_range)
                    service_name = kwargs.get("service_name", service_name)
                    error_type = kwargs.get("error_type", error_type)
                    min_frequency = kwargs.get("min_frequency", min_frequency)

                    result = await self.optimized_tools.find_error_patterns(
                        time_range=time_range,
                        service_name=service_name,
                        error_type=error_type,
                        min_frequency=min_frequency
                    )
                    return self._create_response(200, result, url)
                except Exception as e:
                    return self._create_response(500, {"error": str(e)}, url)

            elif url.endswith("/_apm/business/correlate") or "/_apm/business/correlate?" in url:
                try:
                    # Debug: Print the URL and kwargs being processed
                    print(f"DEBUG: Processing correlate URL: {url}")
                    print(f"DEBUG: correlate kwargs: {kwargs}")

                    # Parse query parameters from URL
                    from urllib.parse import parse_qs, urlparse
                    parsed_url = urlparse(url)
                    query_params = parse_qs(parsed_url.query)

                    # Debug: Print parsed parameters
                    print(f"DEBUG: Parsed correlate query params: {query_params}")

                    # Extract parameters from URL query params or kwargs (FastMCP sends params in kwargs)
                    correlation_id = None
                    time_window = "30m"
                    include_user_journey = False

                    # Try to get from URL query params first
                    if query_params.get("correlation_id"):
                        correlation_id = query_params.get("correlation_id", [None])[0]
                        time_window = query_params.get("time_window", ["30m"])[0]
                        include_user_journey = query_params.get("include_user_journey", ["false"])[0].lower() == "true"

                    # If not found in URL, try kwargs (FastMCP way)
                    if not correlation_id and 'params' in kwargs:
                        params = kwargs['params']
                        correlation_id = params.get("correlation_id")
                        time_window = params.get("time_window", time_window)
                        include_user_journey = params.get("include_user_journey", include_user_journey)

                    # If still not found, try direct kwargs
                    if not correlation_id:
                        correlation_id = kwargs.get("correlation_id")
                        time_window = kwargs.get("time_window", time_window)
                        include_user_journey = kwargs.get("include_user_journey", include_user_journey)

                    print(f"DEBUG: Extracted correlation_id: {correlation_id}")
                    print(f"DEBUG: Extracted time_window: {time_window}")
                    print(f"DEBUG: Extracted include_user_journey: {include_user_journey}")

                    if not correlation_id:
                        return self._create_response(400, {"error": "correlation_id parameter is required"}, url)

                    result = await self.optimized_tools.correlate_business_events(
                        correlation_id=correlation_id,
                        time_window=time_window,
                        include_user_journey=include_user_journey
                    )
                    return self._create_response(200, result, url)
                except Exception as e:
                    print(f"DEBUG: Exception in correlate_business_events: {e}")
                    return self._create_response(500, {"error": str(e)}, url)

        # For all other requests, use the original client
        return await self.original_client.request(method, url, **kwargs)

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request wrapper."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request wrapper."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT request wrapper."""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """PATCH request wrapper."""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE request wrapper."""
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs) -> httpx.Response:
        """HEAD request wrapper."""
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs) -> httpx.Response:
        """OPTIONS request wrapper."""
        return await self.request("OPTIONS", url, **kwargs)

    async def aclose(self) -> None:
        """Close the underlying client."""
        await self.original_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.original_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return await self.original_client.__aexit__(exc_type, exc_val, exc_tb)


class ElasticsearchMCPServer:
    """MCP server for Elasticsearch integration using FastMCP OpenAPI."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize the server with configuration."""
        self.config = config
        self.elasticsearch_client = ElasticsearchClient(config.elasticsearch)
        self.optimized_tools: OptimizedAPMTools | None = None
        self.mcp_server: FastMCPOpenAPI | None = None

    def _get_bundled_spec_path(self) -> Path:
        """Get the path to the bundled OpenAPI specification."""
        return Path(__file__).parent / "specs" / "elasticsearch-byviz.yaml"

    def _load_openapi_spec(self) -> dict[str, Any]:
        """Load the OpenAPI specification from file or use bundled version."""
        import logging

        logger = logging.getLogger("elasticsearch_mcp")

        # Use custom path if provided, otherwise use bundled spec
        if self.config.elasticsearch.openapi_spec_path:
            spec_path = Path(self.config.elasticsearch.openapi_spec_path)
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

    async def _create_authenticated_client(self) -> OptimizedElasticsearchClient:
        """Create an authenticated HTTP client for Elasticsearch API calls with optimized tool support."""
        headers = self.elasticsearch_client.get_auth_headers()
        client_config = self.elasticsearch_client.get_client_config()

        original_client = httpx.AsyncClient(
            base_url=self.config.elasticsearch.base_url,
            headers=headers,
            **client_config,
        )

        # Wrap the client with our optimized interceptor
        return OptimizedElasticsearchClient(original_client, self.optimized_tools)

    # APM Endpoint Handlers
    async def analyzeTracePerformance(self, trace_id: str, include_errors: bool = True, include_metrics: bool = True) -> dict:
        """Handle trace performance analysis endpoint."""
        print(f"DEBUG: analyzeTracePerformance called with trace_id={trace_id}, include_errors={include_errors}, include_metrics={include_metrics}")

        if not trace_id:
            raise ValueError("trace_id parameter is required")

        result = await self.optimized_tools.analyze_trace_performance(
            trace_id=trace_id,
            include_errors=include_errors,
            include_metrics=include_metrics
        )
        return result

    async def findErrorPatterns(self, time_range: str = "now-24h", service_name: str = None, error_type: str = None, min_frequency: int = 1) -> dict:
        """Handle error pattern analysis endpoint."""
        print(f"DEBUG: findErrorPatterns called with time_range={time_range}, service_name={service_name}, error_type={error_type}, min_frequency={min_frequency}")

        result = await self.optimized_tools.find_error_patterns(
            time_range=time_range,
            service_name=service_name,
            error_type=error_type,
            min_frequency=min_frequency
        )
        return result

    async def correlateBusinessEvents(self, correlation_id: str, time_window: str = "30m", include_user_journey: bool = False) -> dict:
        """Handle business event correlation endpoint."""
        print(f"DEBUG: correlateBusinessEvents called with correlation_id={correlation_id}, time_window={time_window}, include_user_journey={include_user_journey}")

        if not correlation_id:
            raise ValueError("correlation_id parameter is required")

        result = await self.optimized_tools.correlate_business_events(
            correlation_id=correlation_id,
            time_window=time_window,
            include_user_journey=include_user_journey
        )
        return result

    def _get_route_filters(self) -> list[RouteMap]:
        """Get route filtering rules for safe search-focused tools.

        Security Model:
        1. DENY ALL destructive operations (POST, PUT, PATCH, DELETE) except for safe search operations
        2. ALLOW ONLY specific read-only GET endpoints and safe search POST endpoints
        3. DEFAULT DENY everything else

        This whitelist approach ensures only safe, read-only operations
        are exposed through the MCP interface.
        """
        # Define safe read-only endpoints for search and analytics workflows
        safe_endpoints = [
            # Search and query operations
            r"^/_search$",  # Search documents
            r"^/.*/_search$",  # Search specific indices
            r"^/_msearch$",  # Multi-search
            r"^/.*/_msearch$",  # Multi-search specific indices
            r"^/_count$",  # Count documents
            r"^/.*/_count$",  # Count documents in specific indices
            r"^/_explain/.*$",  # Explain queries
            r"^/.*/_explain/.*$",  # Explain queries for specific indices
            r"^/_field_caps$",  # Field capabilities
            r"^/.*/_field_caps$",  # Field capabilities for specific indices
            r"^/_validate/query$",  # Validate queries
            r"^/.*/_validate/query$",  # Validate queries for specific indices
            r"^/_render/template$",  # Render search templates
            r"^/.*/_render/template$",  # Render search templates for specific indices

            # APM (Application Performance Monitoring) endpoints
            r"^/logs-apm\..*/_search$",  # APM error logs search
            r"^/traces-apm.*/_search$",  # APM traces search
            r"^/metrics-apm\..*/_search$",  # APM metrics search

            # Metrics and monitoring endpoints
            r"^/metricbeat-.*/_search$",  # System metrics search
            r"^/logs-.*/_search$",  # Log data search
            r"^/filebeat-.*/_search$",  # Filebeat logs search
            r"^/auditbeat-.*/_search$",  # Audit logs search
            r"^/packetbeat-.*/_search$",  # Network packet logs search
            r"^/winlogbeat-.*/_search$",  # Windows logs search
            r"^/heartbeat-.*/_search$",  # Uptime monitoring search
            r"^/functionbeat-.*/_search$",  # Serverless logs search
            r"^/journalbeat-.*/_search$",  # Systemd journal search

            # Watcher and alerting (read-only)
            r"^/\.watcher-history.*/_search$",  # Watcher history search
            r"^/\.watches$",  # Watcher configurations
            r"^/\.watches/.*$",  # Specific watcher configurations

            # Machine learning (read-only)
            r"^/\.ml-.*/_search$",  # ML indices search
            r"^/_ml/.*$",  # ML API endpoints (read-only)

            # Security (read-only)
            r"^/\.security.*/_search$",  # Security indices search
            r"^/_security/.*$",  # Security API endpoints (read-only)

            # Cluster and node information
            r"^/$",  # Cluster info
            r"^/_cluster/health$",  # Cluster health
            r"^/_cluster/state$",  # Cluster state
            r"^/_cluster/stats$",  # Cluster statistics
            r"^/_cluster/settings$",  # Cluster settings
            r"^/_cluster/pending_tasks$",  # Pending tasks
            r"^/_cluster/allocation/explain$",  # Allocation explanation
            r"^/_nodes$",  # Node information
            r"^/_nodes/.*$",  # Specific node information
            r"^/_cat/.*$",  # Cat API (all read-only)

            # Index management (read-only)
            r"^/.*$",  # Index information
            r"^/.*/_mapping$",  # Index mappings
            r"^/.*/_settings$",  # Index settings
            r"^/.*/_stats$",  # Index statistics
            r"^/.*/_recovery$",  # Index recovery
            r"^/.*/_segments$",  # Index segments
            r"^/.*/_shard_stores$",  # Shard stores
            r"^/.*/_upgrade$",  # Index upgrade info

            # Templates and aliases (read-only)
            r"^/_template$",  # Index templates
            r"^/_template/.*$",  # Specific index templates
            r"^/_index_template$",  # Index templates (new format)
            r"^/_index_template/.*$",  # Specific index templates (new format)
            r"^/_component_template$",  # Component templates
            r"^/_component_template/.*$",  # Specific component templates
            r"^/_alias$",  # Aliases
            r"^/_alias/.*$",  # Specific aliases
            r"^/.*/_alias$",  # Index aliases
            r"^/.*/_alias/.*$",  # Specific index aliases

            # Monitoring and observability
            r"^/_monitoring/.*$",  # Monitoring data
            r"^/_xpack$",  # X-Pack info
            r"^/_license$",  # License info
            r"^/_features$",  # Features
            r"^/_cluster/stats$",  # Cluster statistics
            r"^/_nodes/stats$",  # Node statistics
            r"^/_nodes/hot_threads$",  # Hot threads for performance troubleshooting

            # Optimized APM Analysis Tools (GET endpoints)
            r"^/_apm/trace/analyze$",  # Trace performance analysis
            r"^/_apm/errors/patterns$",  # Error pattern analysis
            r"^/_apm/business/correlate$",  # Business event correlation

            # Ingest pipelines (read-only)
            r"^/_ingest/pipeline$",  # List pipelines
            r"^/_ingest/pipeline/.*$",  # Get specific pipeline
            r"^/_ingest/processor/grok$",  # Grok processor patterns

            # Scripts (read-only)
            r"^/_scripts$",  # List scripts
            r"^/_scripts/.*$",  # Get specific script

            # Snapshot and repository info (read-only)
            r"^/_snapshot$",  # Repository info
            r"^/_snapshot/.*$",  # Snapshot info
        ]

        # Safe POST endpoints for search operations
        safe_post_endpoints = [
            r"^/_search$",  # Search with POST body
            r"^/.*/_search$",  # Search specific indices with POST body
            r"^/_msearch$",  # Multi-search with POST body
            r"^/.*/_msearch$",  # Multi-search specific indices with POST body
            r"^/_count$",  # Count with POST body
            r"^/.*/_count$",  # Count specific indices with POST body
            r"^/_explain/.*$",  # Explain with POST body
            r"^/.*/_explain/.*$",  # Explain for specific indices with POST body
            r"^/_field_caps$",  # Field capabilities with POST body
            r"^/.*/_field_caps$",  # Field capabilities for specific indices with POST body
            r"^/_validate/query$",  # Validate queries with POST body
            r"^/.*/_validate/query$",  # Validate queries for specific indices with POST body
            r"^/_render/template$",  # Render search templates with POST body
            r"^/.*/_render/template$",  # Render search templates for specific indices with POST body
            r"^/_mget$",  # Multi-get with POST body
            r"^/.*/_mget$",  # Multi-get from specific indices with POST body
            r"^/.*/_mtermvectors$",  # Multi term vectors with POST body
            r"^/_sql$",  # SQL queries with POST body
            r"^/_sql/translate$",  # SQL translate with POST body
            r"^/_eql/search$",  # EQL search with POST body
            r"^/.*/_eql/search$",  # EQL search for specific indices with POST body
            r"^/_ingest/pipeline/_simulate$",  # Simulate ingest pipeline
            r"^/_ingest/pipeline/.*/_simulate$",  # Simulate specific ingest pipeline

            # APM POST endpoints for advanced search and analysis
            r"^/logs-apm\..*/_search$",  # APM error logs analysis with POST body
            r"^/traces-apm.*/_search$",  # APM traces analysis with POST body
            r"^/metrics-apm\..*/_search$",  # APM metrics analysis with POST body

            # Metrics and monitoring POST endpoints
            r"^/metricbeat-.*/_search$",  # System metrics analysis with POST body
            r"^/logs-.*/_search$",  # Log analysis with POST body
            r"^/filebeat-.*/_search$",  # Filebeat logs analysis with POST body
        ]

        filters = [
            # SECURITY: Block ALL destructive operations first
            RouteMap(
                methods=["POST", "PUT", "PATCH", "DELETE"],
                mcp_type=MCPType.EXCLUDE
            ),
        ]

        # Add whitelisted read-only GET endpoints
        filters.extend(
            RouteMap(
                pattern=pattern,
                methods=["GET"],
                mcp_type=MCPType.TOOL,
            )
            for pattern in safe_endpoints
        )

        # Add whitelisted safe POST endpoints for search operations
        filters.extend(
            RouteMap(
                pattern=pattern,
                methods=["POST"],
                mcp_type=MCPType.TOOL,
            )
            for pattern in safe_post_endpoints
        )

        # SECURITY: Default deny everything else
        filters.append(RouteMap(pattern=r".*", mcp_type=MCPType.EXCLUDE))

        return filters

    def _log_configuration_status(self) -> None:
        """Log the current configuration status."""
        import logging

        logger = logging.getLogger("elasticsearch_mcp")

        # Log Elasticsearch configuration
        logger.info(f"Elasticsearch URL: {self.config.elasticsearch.base_url}")
        logger.info(f"Security filtering: {'ENABLED' if self.config.mcp.enable_security_filtering else 'DISABLED'}")
        logger.info(f"Transport: {self.config.mcp.transport}")
        if self.config.mcp.transport in ["http", "sse"]:
            logger.info(f"Port: {self.config.mcp.port}")



    async def initialize(self) -> None:
        """Initialize the FastMCP server with Elasticsearch OpenAPI spec."""
        import logging

        logger = logging.getLogger("elasticsearch_mcp")

        # Log configuration status
        self._log_configuration_status()

        # Initialize optimized tools
        self.optimized_tools = OptimizedAPMTools(self.elasticsearch_client)
        logger.info("Optimized APM tools initialized successfully")

        # Load OpenAPI specification
        openapi_spec = self._load_openapi_spec()

        # Create authenticated client with optimized tool support
        auth_client = await self._create_authenticated_client()

        # Create FastMCP server from OpenAPI specification
        if self.config.mcp.enable_security_filtering:
            # Use security filtering (default, recommended)
            route_maps = self._get_route_filters()
            logger.info(
                "Security filtering ENABLED - only safe read-only endpoints exposed"
            )
        else:
            # WARNING: No security filtering - exposes ALL Elasticsearch API endpoints
            route_maps = None
            logger.warning(
                "Security filtering DISABLED - ALL Elasticsearch API endpoints exposed including destructive operations!"
            )

        self.mcp_server = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=auth_client,
            route_maps=route_maps,
        )

        logger.info("Optimized APM tools integrated successfully with MCP server")

    def run(self) -> None:
        """Run the MCP server with the configured transport."""
        if not self.mcp_server:
            msg = "Server not initialized. Call initialize() first."
            raise RuntimeError(msg)

        transport = self.config.mcp.transport

        if transport == "stdio":
            self.mcp_server.run("stdio")
        elif transport == "http":
            self.mcp_server.run("streamable-http", host="0.0.0.0", port=self.config.mcp.port)
        elif transport == "sse":
            self.mcp_server.run("sse", host="0.0.0.0", port=self.config.mcp.port)
        else:
            msg = f"Unsupported transport: {transport}"
            raise ValueError(msg)

    async def start(self) -> None:
        """Initialize and run the server."""
        await self.initialize()
        # Note: run() is synchronous and will block
        self.run()
