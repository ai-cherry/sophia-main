"""
Base MCP Server Implementation for Sophia AI
Provides common functionality for all MCP servers
"""

import asyncio
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Tool:
    """Represents an MCP tool"""
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.id = f"{name}-{uuid.uuid4().hex[:8]}"

class Resource:
    """Represents an MCP resource"""
    def __init__(self, name: str, description: str, uri: str, content_type: str = "application/json"):
        self.name = name
        self.description = description
        self.uri = uri
        self.content_type = content_type

class MCPServer(ABC):
    """Base class for MCP servers with HTTP support"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.is_running = False
        self.http_app = FastAPI(title=f"{name} MCP Server")
        
        @self.http_app.post("/mcp")
        async def handle_mcp_request(request: Request):
            payload = await request.json()
            response = await self.handle_request(payload)
            return JSONResponse(content=response)
            
        @self.http_app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
    def register_tool(self, tool: Tool):
        """Register a tool with the server"""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
        
    def register_resource(self, resource: Resource):
        """Register a resource with the server"""
        self.resources[resource.name] = resource
        self.logger.info(f"Registered resource: {resource.name}")
        
    @abstractmethod
    async def setup(self):
        """Setup the server - must be implemented by subclasses"""
        pass
        
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call request"""
        if tool_name not in self.tools:
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tools.keys())
            }
            
        tool = self.tools[tool_name]
        try:
            # Validate parameters
            required_params = {k for k, v in tool.parameters.items() if v.get("required", False)}
            provided_params = set(parameters.keys())
            missing_params = required_params - provided_params
            
            if missing_params:
                return {
                    "error": f"Missing required parameters: {missing_params}",
                    "parameters": tool.parameters
                }
            
            # Execute the tool
            result = await tool.handler(**parameters)
            
            return {
                "success": True,
                "result": result,
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": str(e),
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_resource_request(self, resource_name: str) -> Dict[str, Any]:
        """Handle a resource request"""
        if resource_name not in self.resources:
            return {
                "error": f"Resource '{resource_name}' not found",
                "available_resources": list(self.resources.keys())
            }
            
        resource = self.resources[resource_name]
        return {
            "success": True,
            "resource": {
                "name": resource.name,
                "description": resource.description,
                "uri": resource.uri,
                "content_type": resource.content_type
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        request_type = request.get("type")
        
        if request_type == "list_tools":
            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                    for tool in self.tools.values()
                ]
            }
            
        elif request_type == "list_resources":
            return {
                "resources": [
                    {
                        "name": resource.name,
                        "description": resource.description,
                        "uri": resource.uri
                    }
                    for resource in self.resources.values()
                ]
            }
            
        elif request_type == "tool_call":
            tool_name = request.get("tool")
            parameters = request.get("parameters", {})
            return await self.handle_tool_call(tool_name, parameters)
            
        elif request_type == "resource_request":
            resource_name = request.get("resource")
            return await self.handle_resource_request(resource_name)
            
        else:
            return {"error": f"Unknown request type: {request_type}"}
    
    async def start(self):
        """Start the MCP server's HTTP interface"""
        import uvicorn
        self.logger.info(f"Starting {self.name} HTTP server")
        await self.setup()
        
        config = uvicorn.Config(self.http_app, host="0.0.0.0", port=8080, log_level="info")
        server = uvicorn.Server(config)
        
        # We run the server directly, not in a separate process
        await server.serve()

    async def start_stdin_mode(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the MCP server"""
        self.logger.info(f"Starting {self.name} on {host}:{port}")
        
        # Setup the server
        await self.setup()
        
        # Create server using stdin/stdout for MCP protocol
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        writer = asyncio.StreamWriter(
            transport=sys.stdout,
            protocol=None,
            reader=None,
            loop=asyncio.get_event_loop()
        )
        
        self.is_running = True
        
        # Main server loop
        while self.is_running:
            try:
                # Read request from stdin
                line = await reader.readline()
                if not line:
                    break
                    
                # Parse JSON request
                request = json.loads(line.decode())
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response to stdout
                response_json = json.dumps(response) + "\n"
                writer.write(response_json.encode())
                await writer.drain()
                
            except json.JSONDecodeError as e:
                error_response = {"error": f"Invalid JSON: {e}"}
                writer.write((json.dumps(error_response) + "\n").encode())
                await writer.drain()
            except Exception as e:
                self.logger.error(f"Server error: {e}")
                error_response = {"error": f"Server error: {e}"}
                writer.write((json.dumps(error_response) + "\n").encode())
                await writer.drain()
    
    async def stop(self):
        """Stop the MCP server"""
        self.logger.info(f"Stopping {self.name}")
        self.is_running = False 