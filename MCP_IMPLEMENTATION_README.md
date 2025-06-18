# Sophia AI MCP Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing and deploying the Model Context Protocol (MCP) infrastructure for Sophia AI. The MCP architecture enables AI agents to interact with various services through a standardized interface.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Crew AI       │     │  Cursor IDE     │     │  API Clients    │
│   Agents        │     │  Integration    │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                         │
         └───────────────────────┴─────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     MCP Gateway         │
                    │   (localhost:8090)      │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
│ Snowflake MCP  │     │ Pinecone MCP    │     │ HubSpot MCP     │
│   Server        │     │   Server        │     │   Server        │
└────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- `.env` file with required credentials

### 2. Setup

```bash
# Clone the repository
cd sophia-main-4

# Copy environment template
cp env.example .env

# Edit .env with your credentials
nano .env

# Make startup script executable
chmod +x scripts/start_mcp_servers.sh

# Start MCP infrastructure
./scripts/start_mcp_servers.sh
```

### 3. Verify Installation

```bash
# Check if services are running
docker-compose -f docker-compose.mcp.yml ps

# Test MCP gateway
curl http://localhost:8090/health

# View logs
docker-compose -f docker-compose.mcp.yml logs -f
```

## MCP Servers

### Snowflake MCP Server

**Purpose**: Data warehouse operations with MFA support

**Tools**:
- `execute_query`: Execute SQL queries
- `list_tables`: List available tables
- `describe_table`: Get table schema
- `create_table`: Create new tables
- `upload_dataframe`: Upload data

**Configuration**:
```env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_AUTH_METHOD=keypair  # or password, oauth
SNOWFLAKE_PRIVATE_KEY_PATH=/keys/snowflake_rsa_key.p8
```

### Pinecone MCP Server

**Purpose**: Vector database operations

**Tools**:
- `semantic_search`: Search vectors
- `upsert_vectors`: Insert/update vectors
- `delete_vectors`: Remove vectors
- `describe_index`: Get index info

### HubSpot MCP Server

**Purpose**: CRM operations

**Tools**:
- `get_contacts`: Retrieve contacts
- `create_deal`: Create new deals
- `update_contact`: Update contact info
- `search_companies`: Search companies

### Asana MCP Server

**Purpose**: Project management

**Tools**:
- `create_task`: Create tasks
- `get_project_tasks`: List tasks
- `update_task_status`: Update status
- `assign_task`: Assign to users

## Using MCP with AI Agents

### Basic Usage

```python
from backend.mcp.mcp_client import MCPClient

# Initialize client
client = MCPClient("http://localhost:8090")
await client.connect()

# Call a tool
result = await client.call_tool(
    server="snowflake",
    tool="execute_query",
    query="SELECT COUNT(*) FROM customers"
)
```

### With Crew AI

```python
from backend.agents.core.mcp_crew_orchestrator import MCPCrewOrchestrator

# Initialize orchestrator
orchestrator = MCPCrewOrchestrator()
await orchestrator.initialize()

# Run revenue analysis
result = await orchestrator.execute_revenue_analysis("last_month")
```

### Workflow Example

```python
# Define a multi-step workflow
workflow = [
    {
        "server": "gong",
        "tool": "get_calls",
        "parameters": {"from_date": "2024-01-01"},
        "store_as": "calls"
    },
    {
        "server": "snowflake",
        "tool": "execute_query",
        "parameters": {
            "query": "INSERT INTO call_analysis VALUES ($calls.0.id, $calls.0.duration)"
        }
    },
    {
        "server": "hubspot",
        "tool": "update_contact",
        "parameters": {
            "contact_id": "$calls.0.contact_id",
            "properties": {"last_call_date": "$calls.0.date"}
        }
    }
]

results = await client.execute_workflow(workflow)
```

## Monitoring

### Dashboard

```bash
# Start monitoring dashboard
python3 scripts/mcp_dashboard.py

# Access at http://localhost:8501
```

### Metrics

- Server health status
- Request rates
- Response times
- Tool usage statistics
- Error rates

### Logs

```bash
# All servers
docker-compose -f docker-compose.mcp.yml logs

# Specific server
docker-compose -f docker-compose.mcp.yml logs snowflake-mcp

# Follow logs
docker-compose -f docker-compose.mcp.yml logs -f
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   ```bash
   # Set environment variables
   export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
   export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE
   ```

2. **Snowflake MFA Issues**
   ```bash
   # Generate key pair
   python3 scripts/generate_snowflake_keypair.py
   
   # Update .env
   SNOWFLAKE_AUTH_METHOD=keypair
   ```

3. **Container Not Starting**
   ```bash
   # Check logs
   docker-compose -f docker-compose.mcp.yml logs [service-name]
   
   # Rebuild
   docker-compose -f docker-compose.mcp.yml build --no-cache [service-name]
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual tools
client = MCPClient()
await client.connect()
print(client.list_tools())
```

## Security

### Best Practices

1. **Never commit secrets**
   - Use `.env` files
   - Add to `.gitignore`

2. **Use authentication**
   - Set `MCP_AUTH_TOKEN` in `.env`
   - Pass token to clients

3. **Network isolation**
   - Use Docker networks
   - Limit exposed ports

4. **Audit logging**
   - All operations logged
   - Review regularly

## Extending MCP

### Adding New Tools

1. Edit server implementation:
```python
self.register_tool(Tool(
    name="new_tool",
    description="Description",
    parameters={
        "param1": {"type": "string", "required": True}
    },
    handler=self.new_tool_handler
))
```

2. Implement handler:
```python
async def new_tool_handler(self, param1: str) -> Dict[str, Any]:
    # Implementation
    return {"success": True, "result": data}
```

3. Rebuild server:
```bash
docker-compose -f docker-compose.mcp.yml build [server-name]
docker-compose -f docker-compose.mcp.yml up -d [server-name]
```

### Creating New MCP Servers

1. Create server directory:
```bash
mkdir mcp-servers/myservice
```

2. Add files:
- `Dockerfile`
- `myservice_mcp_server.py`
- `requirements.txt`

3. Update `docker-compose.mcp.yml`

4. Deploy:
```bash
docker-compose -f docker-compose.mcp.yml up -d
```

## Production Deployment

### Lambda Labs

1. **Setup**:
```bash
# SSH to Lambda Labs
ssh user@lambda-instance

# Clone repo
git clone https://github.com/payready/sophia-ai

# Configure
cp env.production .env
```

2. **Deploy**:
```bash
# Use production compose file
docker-compose -f docker-compose.mcp.prod.yml up -d

# Enable auto-restart
docker-compose -f docker-compose.mcp.prod.yml up -d --restart unless-stopped
```

### Scaling

```yaml
# docker-compose.mcp.prod.yml
services:
  snowflake-mcp:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Monitoring

- Prometheus metrics endpoint
- Grafana dashboards
- Alert configuration

## Support

### Resources

- Documentation: `/docs/mcp_*.md`
- Examples: `/examples/mcp/`
- Tests: `/tests/mcp/`

### Getting Help

1. Check logs first
2. Review troubleshooting section
3. Search existing issues
4. Create detailed bug report

## Next Steps

1. **Deploy Snowflake MCP** - Start with data operations
2. **Add Pinecone MCP** - Enable vector search
3. **Integrate HubSpot/Asana** - Business operations
4. **Update AI Agents** - Use MCP tools
5. **Monitor Performance** - Optimize as needed

Remember: Start simple, add complexity gradually. The MCP architecture is designed to grow with your needs. 