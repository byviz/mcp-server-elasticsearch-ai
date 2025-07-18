"""Main entry point for the Elasticsearch MCP server."""

import argparse
import asyncio
import os
import sys

from elasticsearch_mcp.config import AppConfig
from elasticsearch_mcp.server import ElasticsearchMCPServer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Elasticsearch MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport method (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind for HTTP/SSE transport (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind for HTTP/SSE transport (default: 8000)"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Set environment variables based on command line arguments
    os.environ["MCP_TRANSPORT"] = args.transport
    if args.transport in ["http", "sse"]:
        os.environ["MCP_HOST"] = args.host
        os.environ["MCP_PORT"] = str(args.port)

    try:
        # Load configuration
        config = AppConfig.from_env()

        # Create server
        server = ElasticsearchMCPServer(config)

        # Initialize server async components (separate asyncio.run)
        asyncio.run(server.initialize())

        # Run the MCP server (this will block and is synchronous)
        server.run()

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
