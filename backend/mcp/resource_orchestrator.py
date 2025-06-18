import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Type, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os

from .sophia_mcp_server import MCPResource, SophiaMCPServer

class SophiaResourceOrchestrator:
    """Orchestrator for SOPHIA resources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mcp_server = SophiaMCPServer()
        self.initialized = False
        
    async def initialize(self):
        """Initialize the resource orchestrator"""
        if self.initialized:
            return
        
        try:
            # Initialize MCP server
            await self.mcp_server.initialize()
            
            self.initialized = True
            self.logger.info("SOPHIA Resource Orchestrator initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SOPHIA Resource Orchestrator: {e}")
            raise
    
    async def get_resource(self, resource_name: str) -> Optional[MCPResource]:
        """Get a resource by name"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.mcp_server.get_resource(resource_name)
        except ValueError:
            self.logger.warning(f"Resource '{resource_name}' not found")
            return None
    
    async def get_resource_content(self, resource_name: str, uri: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the content of a resource"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.mcp_server.get_resource_content(resource_name, uri)
        except ValueError:
            self.logger.warning(f"Resource '{resource_name}' not found")
            return None
        except Exception as e:
            self.logger.error(f"Error getting resource content: {e}")
            return None
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the provided parameters"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.mcp_server.execute_tool(tool_name, parameters)
        except ValueError as e:
            self.logger.warning(f"Error executing tool: {e}")
            return {"error": str(e)}
        except Exception as e:
            self.logger.error(f"Error executing tool: {e}")
            return {"error": f"Internal error: {str(e)}"}
    
    async def get_all_resources(self) -> List[Dict[str, Any]]:
        """Get information about all available resources"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.mcp_server.get_all_resource_schemas()
        except Exception as e:
            self.logger.error(f"Error getting resources: {e}")
            return []
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get information about all available tools"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.mcp_server.get_all_tool_schemas()
        except Exception as e:
            self.logger.error(f"Error getting tools: {e}")
            return []
    
    async def get_resource_by_type(self, resource_type: str) -> Optional[MCPResource]:
        """Get a resource by type (e.g., 'vector', 'crm', 'gong')"""
        if not self.initialized:
            await self.initialize()
        
        # Get all resources
        resources = await self.get_all_resources()
        
        # Find resource by type
        for resource in resources:
            if resource_type.lower() in resource["name"].lower() or resource_type.lower() in resource["description"].lower():
                return await self.get_resource(resource["name"])
        
        self.logger.warning(f"Resource of type '{resource_type}' not found")
        return None
    
    async def get_tool_by_function(self, function_description: str) -> Optional[Dict[str, Any]]:
        """Get a tool by function description"""
        if not self.initialized:
            await self.initialize()
        
        # Get all tools
        tools = await self.get_all_tools()
        
        # Find tool by function description
        for tool in tools:
            if function_description.lower() in tool["name"].lower() or function_description.lower() in tool["description"].lower():
                return tool
        
        self.logger.warning(f"Tool for function '{function_description}' not found")
        return None
    
    async def register_custom_resource(self, resource: MCPResource):
        """Register a custom resource with the MCP server"""
        if not self.initialized:
            await self.initialize()
        
        await self.mcp_server.register_resource(resource)
    
    async def create_dynamic_resource(self, name: str, description: str, uri: str, api_client: Any) -> MCPResource:
        """Create and register a dynamic resource"""
        if not self.initialized:
            await self.initialize()
        
        # Create resource
        resource = MCPResource(
            name=name,
            description=description,
            uri=uri,
            api_client=api_client
        )
        
        # Register resource
        await self.register_custom_resource(resource)
        
        return resource
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get information about the MCP server"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.mcp_server.get_server_info()
        except Exception as e:
            self.logger.error(f"Error getting server info: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
