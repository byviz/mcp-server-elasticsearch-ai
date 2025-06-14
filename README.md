# Datadog MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to interact with Datadog's observability platform through natural language.

## Features

- **Metrics**: Query time-series data, list metrics, get metadata
- **Logs**: Search and filter log events  
- **APM**: Access trace data, service maps, dependencies
- **Infrastructure**: Host information, container data, process metrics
- **Dashboards**: List and read dashboard configurations
- **Monitors**: Alert rules and status information
- **Incidents**: Incident tracking and management
- **Service Catalog**: Service definitions and relationships
- **SLOs**: Service level objectives and compliance data
- **Usage**: Account usage statistics

## Installation

### From Source

```bash
git clone https://github.com/brukhabtu/datadog-mcp.git
cd datadog-mcp
pip install -e .
```

### Using Docker

```bash
docker pull ghcr.io/brukhabtu/datadog-mcp:latest
```

## Configuration

### Required Environment Variables

```bash
DATADOG_API_KEY="your-datadog-api-key"
DATADOG_APP_KEY="your-datadog-application-key"
```

### Optional Environment Variables

```bash
DATADOG_BASE_URL="https://api.datadoghq.com"  # Default US site
DATADOG_TIMEOUT=30                             # Request timeout in seconds
MCP_TRANSPORT=stdio                            # Transport method (stdio/websocket)
MCP_PORT=8000                                  # Port for WebSocket transport
MCP_LOG_LEVEL=INFO                             # Logging level
MCP_ENABLE_SECURITY_FILTERING=true             # Enable read-only filtering
```

### Regional Endpoints

For different Datadog regions:
- US: `https://api.datadoghq.com` (default)
- EU: `https://api.datadoghq.eu`
- US3: `https://api.us3.datadoghq.com`
- US5: `https://api.us5.datadoghq.com`
- AP1: `https://api.ap1.datadoghq.com`

## Usage

### Command Line

```bash
# Run with default stdio transport
datadog-mcp

# Run with WebSocket transport
datadog-mcp --transport websocket --port 8000

# Run with debug logging
datadog-mcp --log-level DEBUG
```

### Docker

```bash
# Run with environment file
docker run --env-file .env ghcr.io/brukhabtu/datadog-mcp:latest

# Run with individual environment variables
docker run -e DATADOG_API_KEY=your-key \
           -e DATADOG_APP_KEY=your-app-key \
           ghcr.io/brukhabtu/datadog-mcp:latest
```

### Claude Desktop Integration

Add to your Claude Desktop configuration file:

#### macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
#### Windows: `%APPDATA%\Claude\claude_desktop_config.json`
#### Linux: `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "datadog": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env", "DATADOG_API_KEY",
        "--env", "DATADOG_APP_KEY",
        "ghcr.io/brukhabtu/datadog-mcp:latest"
      ],
      "env": {
        "DATADOG_API_KEY": "your-datadog-api-key",
        "DATADOG_APP_KEY": "your-datadog-application-key"
      }
    }
  }
}
```

Or use the native installation:

```json
{
  "mcpServers": {
    "datadog": {
      "command": "datadog-mcp",
      "args": ["--transport", "stdio"],
      "env": {
        "DATADOG_API_KEY": "your-datadog-api-key",
        "DATADOG_APP_KEY": "your-datadog-application-key"
      }
    }
  }
}
```

## OpenAPI Specification

The server requires the Datadog v2 API OpenAPI specification to be placed at:
`src/datadog_mcp/specs/datadog-v2.yaml`

You can obtain this specification from:
- [Datadog's API documentation](https://docs.datadoghq.com/api/)
- [Datadog's GitHub repositories](https://github.com/DataDog)
- Community-maintained specifications

## Security

By default, the server runs with security filtering enabled (`MCP_ENABLE_SECURITY_FILTERING=true`), which restricts operations to read-only access. This includes:

### Allowed Operations
- GET requests to query metrics, logs, traces, etc.
- Reading dashboards, monitors, and configurations
- Searching and filtering data
- Viewing usage statistics

### Blocked Operations
- All POST, PUT, PATCH, DELETE operations
- User and API key management
- Organization settings modifications
- Any destructive actions

To disable security filtering (not recommended for production):
```bash
MCP_ENABLE_SECURITY_FILTERING=false
```

## Example Interactions

Once configured, you can interact with Datadog through natural language:

- "Show me the error rate for my web service over the last hour"
- "List all active monitors that are alerting"
- "Get the CPU usage metrics for production hosts"
- "Show me recent incidents in the platform team"
- "What's our log volume usage this month?"
- "Find traces with high latency in the payment service"
- "Show me the service dependencies for the API gateway"

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/brukhabtu/datadog-mcp.git
cd datadog-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Running Tests

```bash
pytest tests/
```

### Building Docker Image

```bash
docker build -t datadog-mcp:local .
```

## Architecture

The server follows the same architectural patterns as the [Jira MCP](https://github.com/brukhabtu/jira-mcp) implementation:

- **FastMCP 2.0**: Leverages automatic tool generation from OpenAPI specifications
- **Security-First**: Default read-only access with configurable filtering
- **Environment Configuration**: All settings via environment variables
- **Docker-First**: Containerized deployment for consistency
- **Transport Flexibility**: Supports both stdio and WebSocket transports

## Troubleshooting

### Authentication Errors
- Ensure both `DATADOG_API_KEY` and `DATADOG_APP_KEY` are set correctly
- Verify your keys have the necessary permissions in Datadog
- Check you're using the correct regional endpoint

### Connection Issues
- Verify your network can reach the Datadog API
- Check if you need to configure proxy settings
- Ensure the timeout is sufficient for your queries

### Missing Tools
- Verify the OpenAPI specification is present in `src/datadog_mcp/specs/`
- Check the server logs for any specification loading errors
- Ensure the specification version matches your Datadog API version

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License - see LICENSE file for details

## Credits

Based on the [Jira MCP](https://github.com/brukhabtu/jira-mcp) implementation pattern.