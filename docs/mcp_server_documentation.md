# SOPHIA AI System - MCP Server Documentation

## Overview

The Model Context Protocol (MCP) server is a critical component of the SOPHIA AI System, providing a standardized way for AI models to access tools and resources. This document outlines the architecture, configuration, and usage of the MCP server in SOPHIA.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Tools](#tools)
5. [Resources](#resources)
6. [Authentication](#authentication)
7. [Rate Limiting](#rate-limiting)
8. [Monitoring](#monitoring)
9. [Development Guide](#development-guide)
10. [Troubleshooting](#troubleshooting)

## Introduction

The Model Context Protocol (MCP) is a standardized protocol for AI models to access external tools and resources. In SOPHIA, the MCP server acts as a bridge between AI models and various business systems, allowing models to:

- Execute specialized tools for data analysis
- Access structured resources from business systems
- Maintain consistent interfaces across different AI providers
- Ensure security and compliance with business rules

## Architecture

The MCP server in SOPHIA follows a modular architecture:

```
backend/mcp/
├── server.py                # Main server implementation
├── resource_orchestrator.py # Manages resource access
├── tool_orchestrator.py     # Manages tool execution
├── auth/                    # Authentication modules
├── tools/                   # Tool implementations
│   ├── gong_tools.py        # Gong.io integration tools
│   ├── vector_tools.py      # Vector database tools
│   ├── crm_tools.py         # CRM integration tools
│   └── ...
└── resources/               # Resource implementations
    ├── gong_resources.py    # Gong.io resources
    ├── crm_resources.py     # CRM resources
    └── ...
```

### Key Components

1. **Server**: The main MCP server that handles requests, authentication, and routing.
2. **Tool Orchestrator**: Manages tool registration, validation, and execution.
3. **Resource Orchestrator**: Manages resource registration, access, and caching.
4. **Tools**: Implementations of specific tools that models can use.
5. **Resources**: Implementations of specific resources that models can access.

## Configuration

The MCP server is configured using the `mcp_config.json` file at the root of the project. This file defines:

- Server configuration (host, port, etc.)
- Available tools and their configurations
- Available resources and their configurations
- Authentication settings
- Rate limiting rules
- Monitoring settings

Example configuration:

```json
{
  "server_name": "sophia-mcp-server",
  "version": "1.0.0",
  "description": "SOPHIA AI MCP Server for PayReady",
  "host": "0.0.0.0",
  "port": 8002,
  "log_level": "INFO",
  "cors_origins": ["*"],
  "auth": {
    "enabled": true,
    "jwt_secret": "${JWT_SECRET}",
    "jwt_algorithm": "HS256",
    "token_expiration": 86400
  },
  "tools": [
    {
      "name": "gong_tools",
      "module": "backend.mcp.tools.gong_tools",
      "enabled": true,
      "functions": [
        "gong_call_analysis",
        "gong_transcript_extraction"
      ]
    }
  ],
  "resources": [
    {
      "name": "crm_resources",
      "module": "backend.mcp.resources.crm_resources",
      "enabled": true,
      "resources": [
        "hubspot_contacts",
        "hubspot_companies"
      ]
    }
  ]
}
```

## Tools

Tools are functions that models can execute to perform specific tasks. Each tool has:

- A unique name
- Input schema (parameters)
- Output schema (return value)
- Implementation logic

### Tool Definition

Tools are defined in Python modules under `backend/mcp/tools/`. Each tool is a function with type hints and docstrings that define its behavior.

Example tool definition:

```python
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class GongCallAnalysisInput(BaseModel):
    call_id: str = Field(..., description="The ID of the Gong call to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform", enum=["sentiment", "topics", "questions", "next_steps"])
    
class GongCallAnalysisOutput(BaseModel):
    call_id: str
    analysis_results: Dict[str, any]
    summary: str
    
def gong_call_analysis(input_data: GongCallAnalysisInput) -> GongCallAnalysisOutput:
    """
    Analyze a Gong call recording and extract insights.
    
    This tool connects to the Gong.io API, retrieves the specified call,
    and performs the requested type of analysis on the call content.
    
    Args:
        input_data: The input parameters for the analysis
        
    Returns:
        Analysis results and summary
    """
    # Implementation logic here
    ...
    
    return GongCallAnalysisOutput(
        call_id=input_data.call_id,
        analysis_results=results,
        summary=summary
    )
```

### Tool Registration

Tools are automatically registered with the MCP server based on the configuration in `mcp_config.json`. The server scans the specified modules and registers functions that match the names in the configuration.

### Tool Usage

Models can use tools by sending a request to the MCP server with:

- The tool name
- Input parameters according to the tool's schema

Example request:

```json
{
  "tool_name": "gong_call_analysis",
  "input": {
    "call_id": "call-123456",
    "analysis_type": "sentiment"
  }
}
```

## Resources

Resources are data sources that models can access. Each resource has:

- A unique URI
- Access control rules
- Implementation logic

### Resource Definition

Resources are defined in Python modules under `backend/mcp/resources/`. Each resource is a class that implements the `Resource` interface.

Example resource definition:

```python
from typing import Dict, List, Optional
from backend.mcp.resource import Resource, ResourceRequest

class HubspotContactsResource(Resource):
    """
    Resource for accessing HubSpot contacts.
    """
    
    def __init__(self, config: Dict[str, any]):
        super().__init__(config)
        self.hubspot_client = self._create_hubspot_client()
    
    async def get(self, request: ResourceRequest) -> Dict[str, any]:
        """
        Get HubSpot contacts based on the request parameters.
        
        Args:
            request: The resource request
            
        Returns:
            Contact data
        """
        # Implementation logic here
        ...
        
        return contacts_data
```

### Resource Registration

Resources are automatically registered with the MCP server based on the configuration in `mcp_config.json`. The server scans the specified modules and registers resources that match the names in the configuration.

### Resource Usage

Models can access resources by sending a request to the MCP server with:

- The resource URI
- Optional query parameters

Example request:

```json
{
  "resource_uri": "hubspot_contacts",
  "query_params": {
    "email": "customer@example.com"
  }
}
```

## Authentication

The MCP server supports JWT-based authentication. Each request must include a valid JWT token in the `Authorization` header.

### JWT Configuration

JWT authentication is configured in the `auth` section of `mcp_config.json`:

```json
"auth": {
  "enabled": true,
  "jwt_secret": "${JWT_SECRET}",
  "jwt_algorithm": "HS256",
  "token_expiration": 86400
}
```

### Token Generation

Tokens can be generated using the `/auth/token` endpoint of the MCP server:

```bash
curl -X POST http://localhost:8002/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "model", "password": "password"}'
```

### Token Usage

Include the token in the `Authorization` header of requests:

```bash
curl http://localhost:8002/tools/gong_call_analysis \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"input": {...}}'
```

## Rate Limiting

The MCP server implements rate limiting to prevent abuse and ensure fair usage of resources.

### Rate Limit Configuration

Rate limits are configured in the `rate_limits` section of `mcp_config.json`:

```json
"rate_limits": {
  "enabled": true,
  "default_rate": 100,
  "default_period": 60,
  "per_tool_limits": {
    "web_search": {
      "rate": 10,
      "period": 60
    }
  }
}
```

### Rate Limit Headers

The server includes rate limit headers in responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed in the period
- `X-RateLimit-Remaining`: The number of requests remaining in the current period
- `X-RateLimit-Reset`: The time when the rate limit will reset (Unix timestamp)

## Monitoring

The MCP server includes monitoring capabilities to track usage, performance, and errors.

### Prometheus Metrics

The server exposes Prometheus metrics at the `/metrics` endpoint, including:

- Request counts by tool/resource
- Request durations
- Error counts
- Rate limit hits

### Logging

The server logs events to both console and file, with structured logging in JSON format. Log levels can be configured in `mcp_config.json`.

## Development Guide

### Adding a New Tool

1. Create a new Python module in `backend/mcp/tools/` or add to an existing module
2. Define the tool function with input/output schemas
3. Add comprehensive docstrings
4. Add the tool to `mcp_config.json`
5. Write tests for the tool

Example:

```python
# backend/mcp/tools/slack_tools.py

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class SlackMessageInput(BaseModel):
    channel: str = Field(..., description="The Slack channel to send the message to")
    message: str = Field(..., description="The message content")
    
class SlackMessageOutput(BaseModel):
    channel: str
    message_id: str
    timestamp: str
    
def slack_send_message(input_data: SlackMessageInput) -> SlackMessageOutput:
    """
    Send a message to a Slack channel.
    
    Args:
        input_data: The input parameters for the message
        
    Returns:
        Details of the sent message
    """
    # Implementation logic here
    ...
    
    return SlackMessageOutput(
        channel=input_data.channel,
        message_id=message_id,
        timestamp=timestamp
    )
```

Then add to `mcp_config.json`:

```json
"tools": [
  {
    "name": "slack_tools",
    "module": "backend.mcp.tools.slack_tools",
    "enabled": true,
    "functions": [
      "slack_send_message"
    ]
  }
]
```

### Adding a New Resource

1. Create a new Python module in `backend/mcp/resources/` or add to an existing module
2. Define the resource class implementing the `Resource` interface
3. Add comprehensive docstrings
4. Add the resource to `mcp_config.json`
5. Write tests for the resource

Example:

```python
# backend/mcp/resources/slack_resources.py

from typing import Dict, List, Optional
from backend.mcp.resource import Resource, ResourceRequest

class SlackChannelsResource(Resource):
    """
    Resource for accessing Slack channels.
    """
    
    def __init__(self, config: Dict[str, any]):
        super().__init__(config)
        self.slack_client = self._create_slack_client()
    
    async def get(self, request: ResourceRequest) -> Dict[str, any]:
        """
        Get Slack channels based on the request parameters.
        
        Args:
            request: The resource request
            
        Returns:
            Channel data
        """
        # Implementation logic here
        ...
        
        return channels_data
```

Then add to `mcp_config.json`:

```json
"resources": [
  {
    "name": "slack_resources",
    "module": "backend.mcp.resources.slack_resources",
    "enabled": true,
    "resources": [
      "slack_channels"
    ]
  }
]
```

## Troubleshooting

### Common Issues

#### Tool Not Found

If a tool is not found, check:

1. The tool name in the request matches the function name
2. The tool is listed in `mcp_config.json`
3. The module containing the tool is correctly specified
4. The tool function is properly defined

#### Resource Not Found

If a resource is not found, check:

1. The resource URI in the request matches the resource name
2. The resource is listed in `mcp_config.json`
3. The module containing the resource is correctly specified
4. The resource class is properly defined

#### Authentication Failures

If authentication fails, check:

1. The JWT token is included in the `Authorization` header
2. The token is valid and not expired
3. The JWT secret in the server matches the one used to generate the token

#### Rate Limit Exceeded

If rate limits are exceeded, check:

1. The rate limit configuration in `mcp_config.json`
2. The client is respecting rate limit headers
3. Consider implementing backoff and retry logic in the client

### Logs

Check the server logs for detailed error information:

```bash
docker-compose logs mcp-server
```

### Health Check

Use the health check endpoint to verify the server is running correctly:

```bash
curl http://localhost:8002/health
```

### Metrics

Check the metrics endpoint for performance and usage information:

```bash
curl http://localhost:8002/metrics
```

## Conclusion

The MCP server is a powerful component of the SOPHIA AI System, enabling AI models to interact with business systems in a standardized, secure, and efficient way. By following the guidelines in this documentation, you can extend and customize the MCP server to meet your specific needs.
