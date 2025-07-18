"""Elasticsearch authentication and HTTP client."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from elasticsearch_mcp.config import ElasticsearchConfig
else:
    from elasticsearch_mcp.config import ElasticsearchConfig


class ElasticsearchClient:
    """Authenticated HTTP client for Elasticsearch API."""

    def __init__(self, config: ElasticsearchConfig) -> None:
        """Initialize the Elasticsearch client with configuration."""
        self.base_url = config.base_url
        self.username = config.username
        self.password = config.password
        self.api_key = config.api_key
        self.cloud_id = config.cloud_id
        self.timeout = config.timeout
        self.verify_certs = config.verify_certs
        self.ca_certs = config.ca_certs
        self.client_cert = config.client_cert
        self.client_key = config.client_key

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for Elasticsearch API."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "elasticsearch-mcp/1.0.0",
        }

        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        elif self.username and self.password:
            credentials = base64.b64encode(
                f"{self.username}:{self.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"

        return headers

    def get_client_config(self) -> dict[str, Any]:
        """Get HTTP client configuration."""
        config = {
            "timeout": self.timeout,
            "verify": self.verify_certs,
        }

        if self.ca_certs:
            config["verify"] = self.ca_certs

        if self.client_cert and self.client_key:
            config["cert"] = (self.client_cert, self.client_key)

        return config

    async def get(self, path: str) -> Any:
        """Make an authenticated GET request to Elasticsearch API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()
        client_config = self.get_client_config()

        async with httpx.AsyncClient(**client_config) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, json: Any = None) -> Any:
        """Make an authenticated POST request to Elasticsearch API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()
        client_config = self.get_client_config()

        async with httpx.AsyncClient(**client_config) as client:
            response = await client.post(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()

    async def put(self, path: str, json: Any = None) -> Any:
        """Make an authenticated PUT request to Elasticsearch API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()
        client_config = self.get_client_config()

        async with httpx.AsyncClient(**client_config) as client:
            response = await client.put(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()

    async def delete(self, path: str) -> None:
        """Make an authenticated DELETE request to Elasticsearch API."""
        url = f"{self.base_url}{path}"
        headers = self.get_auth_headers()
        client_config = self.get_client_config()

        async with httpx.AsyncClient(**client_config) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
