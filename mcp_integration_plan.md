# Sophia AI MCP Integration Plan

## Overview

This plan outlines the integration of Docker MCP (Model Context Protocol) servers into the Sophia AI platform, including the addition of HubSpot and Asana integrations.

## Current vs Future Architecture

### Current Architecture Challenges
- Manual integration management for each service
- SSL certificate issues on different platforms
- Complex authentication flows (MFA, OAuth, API keys)
- Inconsistent error handling across integrations
- Difficult to add new integrations

### MCP-Enabled Architecture Benefits
- Standardized integration interface
- Container-based isolation and security
- Unified authentication management
- Consistent error handling and monitoring
- AI agents can directly access all services as tools

## Integration Roadmap

### Phase 1: Foundation (Week 1)

#### 1.1 MCP Infrastructure Setup
```yaml
# docker-compose.mcp.yml
version: '3.8'
services:
  mcp-gateway:
    image: anthropic/mcp-gateway:latest
    ports:
      - "8090:8090"
    environment:
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
    volumes:
      - ./mcp-config:/config
    
  mcp-registry:
    image: anthropic/mcp-registry:latest
    ports:
      - "8091:8091"
```

#### 1.2 Core MCP Servers

**Snowflake MCP Server**
```dockerfile
# mcp-servers/snowflake/Dockerfile
FROM mcp/base:latest
COPY snowflake-mcp-server.py /app/
RUN pip install snowflake-connector-python cryptography
CMD ["python", "/app/snowflake-mcp-server.py"]
```

**Pinecone MCP Server**
```bash
docker pull pinecone/assistant-mcp:latest
```

**Pulumi MCP Server**
```bash
docker pull pulumi/mcp-server:latest
```

### Phase 2: Business System Integration (Week 2-3)

#### 2.1 HubSpot MCP Server

Create a custom MCP server for HubSpot:

```python
# mcp-servers/hubspot/hubspot_mcp_server.py
"""
HubSpot MCP Server for Sophia AI
Provides standardized access to HubSpot CRM functionality
"""

from mcp import Server, Tool, Resource
import aiohttp
import os

class HubSpotMCPServer(Server):
    def __init__(self):
        super().__init__("hubspot-mcp")
        self.api_key = os.environ.get("HUBSPOT_API_KEY")
        self.base_url = "https://api.hubapi.com"
        
    async def setup(self):
        # Register tools
        self.register_tool(Tool(
            name="get_contacts",
            description="Retrieve HubSpot contacts",
            parameters={
                "limit": {"type": "integer", "default": 100},
                "properties": {"type": "array", "items": {"type": "string"}}
            },
            handler=self.get_contacts
        ))
        
        self.register_tool(Tool(
            name="create_deal",
            description="Create a new deal in HubSpot",
            parameters={
                "properties": {"type": "object", "required": ["dealname", "amount"]}
            },
            handler=self.create_deal
        ))
        
        self.register_tool(Tool(
            name="update_contact",
            description="Update a HubSpot contact",
            parameters={
                "contact_id": {"type": "string", "required": True},
                "properties": {"type": "object"}
            },
            handler=self.update_contact
        ))
    
    async def get_contacts(self, limit=100, properties=None):
        """Retrieve contacts from HubSpot"""
        # Implementation here
        pass
    
    async def create_deal(self, properties):
        """Create a new deal"""
        # Implementation here
        pass
    
    async def update_contact(self, contact_id, properties):
        """Update contact properties"""
        # Implementation here
        pass
```

#### 2.2 Asana MCP Server

Create a custom MCP server for Asana:

```python
# mcp-servers/asana/asana_mcp_server.py
"""
Asana MCP Server for Sophia AI
Provides project management and task tracking capabilities
"""

from mcp import Server, Tool, Resource
import asana
import os

class AsanaMCPServer(Server):
    def __init__(self):
        super().__init__("asana-mcp")
        self.access_token = os.environ.get("ASANA_ACCESS_TOKEN")
        self.client = asana.Client.access_token(self.access_token)
        
    async def setup(self):
        # Register tools
        self.register_tool(Tool(
            name="create_task",
            description="Create a new task in Asana",
            parameters={
                "name": {"type": "string", "required": True},
                "project_gid": {"type": "string", "required": True},
                "assignee": {"type": "string"},
                "due_date": {"type": "string"},
                "notes": {"type": "string"}
            },
            handler=self.create_task
        ))
        
        self.register_tool(Tool(
            name="get_project_tasks",
            description="Get all tasks in a project",
            parameters={
                "project_gid": {"type": "string", "required": True},
                "completed": {"type": "boolean", "default": False}
            },
            handler=self.get_project_tasks
        ))
        
        self.register_tool(Tool(
            name="update_task_status",
            description="Update task completion status",
            parameters={
                "task_gid": {"type": "string", "required": True},
                "completed": {"type": "boolean", "required": True}
            },
            handler=self.update_task_status
        ))
    
    async def create_task(self, name, project_gid, assignee=None, due_date=None, notes=None):
        """Create a new Asana task"""
        # Implementation here
        pass
    
    async def get_project_tasks(self, project_gid, completed=False):
        """Retrieve tasks from a project"""
        # Implementation here
        pass
    
    async def update_task_status(self, task_gid, completed):
        """Update task completion status"""
        # Implementation here
        pass
```

#### 2.3 Gong.io MCP Server

```python
# mcp-servers/gong/gong_mcp_server.py
"""
Gong.io MCP Server for Sophia AI
Provides call recording analysis and insights
"""

from mcp import Server, Tool
import base64
import aiohttp

class GongMCPServer(Server):
    def __init__(self):
        super().__init__("gong-mcp")
        self.api_key = os.environ.get("GONG_API_KEY")
        self.api_secret = os.environ.get("GONG_API_SECRET")
        
    async def setup(self):
        self.register_tool(Tool(
            name="get_calls",
            description="Retrieve call recordings and metadata",
            parameters={
                "from_date": {"type": "string", "format": "date"},
                "to_date": {"type": "string", "format": "date"},
                "limit": {"type": "integer", "default": 100}
            },
            handler=self.get_calls
        ))
        
        self.register_tool(Tool(
            name="get_call_transcript",
            description="Get transcript for a specific call",
            parameters={
                "call_id": {"type": "string", "required": True}
            },
            handler=self.get_call_transcript
        ))
```

### Phase 3: Unified Configuration (Week 4)

#### 3.1 Complete MCP Configuration

```json
{
  "servers": [
    {
      "name": "snowflake",
      "type": "docker",
      "image": "sophia/snowflake-mcp:latest",
      "env": {
        "SNOWFLAKE_ACCOUNT": "${SNOWFLAKE_ACCOUNT}",
        "SNOWFLAKE_USER": "${SNOWFLAKE_USER}",
        "SNOWFLAKE_PRIVATE_KEY_PATH": "/keys/snowflake_rsa_key.p8"
      },
      "volumes": {
        "./keys": "/keys:ro"
      }
    },
    {
      "name": "hubspot",
      "type": "docker",
      "image": "sophia/hubspot-mcp:latest",
      "env": {
        "HUBSPOT_API_KEY": "${HUBSPOT_API_KEY}"
      }
    },
    {
      "name": "asana",
      "type": "docker",
      "image": "sophia/asana-mcp:latest",
      "env": {
        "ASANA_ACCESS_TOKEN": "${ASANA_ACCESS_TOKEN}"
      }
    },
    {
      "name": "gong",
      "type": "docker",
      "image": "sophia/gong-mcp:latest",
      "env": {
        "GONG_API_KEY": "${GONG_API_KEY}",
        "GONG_API_SECRET": "${GONG_API_SECRET}"
      }
    },
    {
      "name": "pinecone",
      "type": "docker",
      "image": "pinecone/assistant-mcp:latest",
      "env": {
        "PINECONE_API_KEY": "${PINECONE_API_KEY}"
      }
    },
    {
      "name": "pulumi",
      "type": "docker",
      "image": "pulumi/mcp-server:latest",
      "env": {
        "PULUMI_ACCESS_TOKEN": "${PULUMI_ACCESS_TOKEN}"
      },
      "volumes": {
        "./infrastructure": "/workspace:rw"
      }
    }
  ]
}
```

#### 3.2 AI Agent Integration

Update Crew AI agents to use MCP tools:

```python
# backend/agents/enhanced_crew_orchestrator.py
from crewai import Agent, Task, Crew
from mcp import MCPClient

class EnhancedCrewOrchestrator:
    def __init__(self):
        self.mcp_client = MCPClient()
        self.mcp_client.connect("localhost:8090")
        
    def create_sales_analyst_agent(self):
        return Agent(
            role="Sales Analyst",
            goal="Analyze sales data and provide insights",
            tools=[
                self.mcp_client.get_tool("gong", "get_calls"),
                self.mcp_client.get_tool("gong", "get_call_transcript"),
                self.mcp_client.get_tool("hubspot", "get_contacts"),
                self.mcp_client.get_tool("snowflake", "execute_query"),
                self.mcp_client.get_tool("pinecone", "semantic_search")
            ]
        )
    
    def create_project_manager_agent(self):
        return Agent(
            role="Project Manager",
            goal="Manage tasks and coordinate team activities",
            tools=[
                self.mcp_client.get_tool("asana", "create_task"),
                self.mcp_client.get_tool("asana", "get_project_tasks"),
                self.mcp_client.get_tool("asana", "update_task_status"),
                self.mcp_client.get_tool("slack", "send_message")
            ]
        )
```

### Phase 4: Monitoring and Optimization (Week 5)

#### 4.1 MCP Monitoring Dashboard

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
```

#### 4.2 Performance Metrics

Track key metrics:
- MCP server response times
- Tool execution success rates
- Container resource usage
- API rate limit status
- Error rates by integration

## Implementation Benefits

### For Pay Ready Business

1. **Sales Intelligence**
   - Unified view of customer interactions (Gong + HubSpot)
   - Automated task creation from call insights (Gong → Asana)
   - Real-time revenue impact analysis (HubSpot + Snowflake)

2. **Project Management**
   - Automatic task creation from customer requests
   - Integration between CRM activities and project tasks
   - AI-driven priority assignment

3. **Team Collaboration**
   - Slack notifications for important CRM events
   - Asana task updates in team channels
   - Call summary distribution

### Technical Benefits

1. **Simplified Development**
   - Standard interface for all integrations
   - Easier to add new services
   - Consistent error handling

2. **Enhanced Security**
   - Container isolation
   - Centralized secret management
   - Audit logging for all operations

3. **Improved Reliability**
   - Service health monitoring
   - Automatic container restarts
   - Rate limit management

## Cost Analysis

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Docker Infrastructure | $50-100 | Lambda Labs servers |
| Additional Monitoring | $20-40 | Prometheus/Grafana |
| Development Time | 160 hours | One-time investment |
| Maintenance Reduction | -40 hours/month | Ongoing savings |

**ROI**: Break-even in 4 months, then 40 hours/month saved

## Rollout Plan

### Week 1: Foundation
- Set up MCP infrastructure
- Deploy Snowflake and Pinecone MCP servers
- Test with existing agents

### Week 2-3: Business Systems
- Deploy HubSpot MCP server
- Deploy Asana MCP server
- Update Gong integration to MCP

### Week 4: Integration
- Update all Crew AI agents
- Implement unified authentication
- Set up monitoring

### Week 5: Optimization
- Performance tuning
- Documentation
- Team training

## Success Metrics

1. **Technical Metrics**
   - 99.9% uptime for MCP servers
   - <100ms average response time
   - Zero authentication failures

2. **Business Metrics**
   - 50% reduction in integration maintenance time
   - 30% faster new feature deployment
   - 100% of agents using MCP tools

## Conclusion

Implementing Docker MCP integration will transform Sophia AI into a more robust, scalable, and maintainable platform. The addition of HubSpot and Asana through MCP servers will provide Pay Ready with comprehensive business automation capabilities while maintaining security and performance standards. 