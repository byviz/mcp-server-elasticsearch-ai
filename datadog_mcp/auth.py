"""Datadog authentication and HTTP client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from datadog_mcp.config import DatadogConfig
else:
    from datadog_mcp.config import DatadogConfig


class DatadogClient:
    """Authenticated HTTP client for Datadog API."""

    def __init__(self, config: DatadogConfig) -> None:
        """Initialize the Datadog client with configuration."""
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.app_key = config.app_key
        self.timeout = config.timeout

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for Datadog API."""
        return {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
            "Content-Type": "application/json",
            "User-Agent": "datadog-mcp/1.0.0",
        }

    async def get(self, path: str) -> Any:
        """Make an authenticated GET request to Datadog API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, json: Any = None) -> Any:
        """Make an authenticated POST request to Datadog API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()

    async def put(self, path: str, json: Any = None) -> Any:
        """Make an authenticated PUT request to Datadog API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()

    async def delete(self, path: str) -> None:
        """Make an authenticated DELETE request to Datadog API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()