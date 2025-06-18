import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Type, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os

from ..core.secret_manager import secret_manager

@dataclass
class MCPTool:
    """Base class for MCP tools"""
    name: str
    description: str
    parameters: Dict[str, Dict[str, Any]]
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        raise NotImplementedError("Subclasses must implement execute")

@dataclass
class MCPResource:
    """Base class for MCP resources"""
    name: str
    description: str
    uri: str
    api_client: Any = None
    
    async def get_content(self) -> Dict[str, Any]:
        """Get the resource content"""
        raise NotImplementedError("Subclasses must implement get_content")

class SophiaMCPServer:
    """MCP server for SOPHIA AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.initialized = False
        
    async def initialize(self):
        """Initialize the MCP server"""
        if self.initialized:
            return
        
        try:
            # Load tools
            await self._load_tools()
            
            # Load resources
            await self._load_resources()
            
            self.initialized = True
            self.logger.info("SOPHIA MCP server initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SOPHIA MCP server: {e}")
            raise
    
    async def _load_tools(self):
        """Load all available tools"""
        # Import tool modules
        from .tools.gong_tools import GongCallAnalysisTool, GongTranscriptExtractionTool
        from .tools.vector_tools import VectorSearchTool, VectorStoreTool
        from .tools.crm_tools import CrmSyncTool, CrmQueryTool
        
        # Initialize tools
        tools = [
            GongCallAnalysisTool(),
            GongTranscriptExtractionTool(),
            VectorSearchTool(),
            VectorStoreTool(),
            CrmSyncTool(),
            CrmQueryTool()
        ]
        
        # Register tools
        for tool in tools:
            await self.register_tool(tool)
    
    async def _load_resources(self):
        """Load all available resources"""
        # Import resource modules
        from ..integrations.gong.enhanced_gong_integration import GongClient
        from ..integrations.estuary_flow_integration import EstuaryFlowClient
        
        # Initialize resources
        gong_client = GongClient()
        await gong_client.setup()
        
        estuary_client = EstuaryFlowClient()
        await estuary_client.setup()
        
        # Create resources
        gong_resource = MCPResource(
            name="gong",
            description="Gong.io call recording and analysis platform",
            uri="gong://api",
            api_client=gong_client
        )
        
        estuary_resource = MCPResource(
            name="estuary",
            description="Estuary Flow real-time data streaming platform",
            uri="estuary://api",
            api_client=estuary_client
        )
        
        # Register resources
        await self.register_resource(gong_resource)
        await self.register_resource(estuary_resource)
        
        # Initialize vector database resources
        try:
            vector_db = os.environ.get("VECTOR_DB", "pinecone")
            
            if vector_db == "pinecone":
                import pinecone
                
                api_key = await secret_manager.get_secret("api_key", "pinecone")
                environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east1-gcp")
                
                pinecone.init(api_key=api_key, environment=environment)
                
                pinecone_resource = MCPResource(
                    name="pinecone",
                    description="Pinecone vector database",
                    uri="pinecone://api",
                    api_client=pinecone
                )
                
                await self.register_resource(pinecone_resource)
                
            elif vector_db == "weaviate":
                import weaviate
                
                api_key = await secret_manager.get_secret("api_key", "weaviate")
                url = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
                
                weaviate_client = weaviate.Client(
                    url=url,
                    auth_client_secret=weaviate.AuthApiKey(api_key=api_key)
                )
                
                weaviate_resource = MCPResource(
                    name="weaviate",
                    description="Weaviate vector database",
                    uri="weaviate://api",
                    api_client=weaviate_client
                )
                
                await self.register_resource(weaviate_resource)
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize vector database resource: {e}")
    
    async def register_tool(self, tool: MCPTool):
        """Register a tool with the MCP server"""
        if tool.name in self.tools:
            self.logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    async def register_resource(self, resource: MCPResource):
        """Register a resource with the MCP server"""
        if resource.name in self.resources:
            self.logger.warning(f"Resource '{resource.name}' already registered, overwriting")
        
        self.resources[resource.name] = resource
        self.logger.info(f"Registered resource: {resource.name}")
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the provided parameters"""
        if not self.initialized:
            await self.initialize()
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        
        # Validate parameters
        self._validate_parameters(tool, parameters)
        
        # Execute tool
        self.logger.info(f"Executing tool: {tool_name}")
        result = await tool.execute(parameters)
        
        return result
    
    async def get_resource(self, resource_name: str) -> MCPResource:
        """Get a resource by name"""
        if not self.initialized:
            await self.initialize()
        
        if resource_name not in self.resources:
            raise ValueError(f"Resource '{resource_name}' not found")
        
        return self.resources[resource_name]
    
    async def get_resource_content(self, resource_name: str, uri: Optional[str] = None) -> Dict[str, Any]:
        """Get the content of a resource"""
        if not self.initialized:
            await self.initialize()
        
        if resource_name not in self.resources:
            raise ValueError(f"Resource '{resource_name}' not found")
        
        resource = self.resources[resource_name]
        
        # Override URI if provided
        if uri:
            resource.uri = uri
        
        return await resource.get_content()
    
    def _validate_parameters(self, tool: MCPTool, parameters: Dict[str, Any]):
        """Validate parameters against tool schema"""
        for param_name, param_schema in tool.parameters.items():
            # Check required parameters
            if param_schema.get("required", False) and param_name not in parameters:
                raise ValueError(f"Required parameter '{param_name}' not provided")
            
            # Skip validation if parameter not provided
            if param_name not in parameters:
                continue
            
            param_value = parameters[param_name]
            
            # Validate type
            param_type = param_schema.get("type")
            if param_type == "string" and not isinstance(param_value, str):
                raise ValueError(f"Parameter '{param_name}' must be a string")
            elif param_type == "integer" and not isinstance(param_value, int):
                raise ValueError(f"Parameter '{param_name}' must be an integer")
            elif param_type == "number" and not isinstance(param_value, (int, float)):
                raise ValueError(f"Parameter '{param_name}' must be a number")
            elif param_type == "boolean" and not isinstance(param_value, bool):
                raise ValueError(f"Parameter '{param_name}' must be a boolean")
            elif param_type == "array" and not isinstance(param_value, list):
                raise ValueError(f"Parameter '{param_name}' must be an array")
            elif param_type == "object" and not isinstance(param_value, dict):
                raise ValueError(f"Parameter '{param_name}' must be an object")
            
            # Validate enum
            if "enum" in param_schema and param_value not in param_schema["enum"]:
                raise ValueError(f"Parameter '{param_name}' must be one of: {param_schema['enum']}")
    
    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the schema for a tool"""
        if not self.initialized:
            await self.initialize()
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
    
    async def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools"""
        if not self.initialized:
            await self.initialize()
        
        schemas = []
        for tool_name in self.tools:
            schema = await self.get_tool_schema(tool_name)
            schemas.append(schema)
        
        return schemas
    
    async def get_resource_schema(self, resource_name: str) -> Dict[str, Any]:
        """Get the schema for a resource"""
        if not self.initialized:
            await self.initialize()
        
        if resource_name not in self.resources:
            raise ValueError(f"Resource '{resource_name}' not found")
        
        resource = self.resources[resource_name]
        
        return {
            "name": resource.name,
            "description": resource.description,
            "uri": resource.uri
        }
    
    async def get_all_resource_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all resources"""
        if not self.initialized:
            await self.initialize()
        
        schemas = []
        for resource_name in self.resources:
            schema = await self.get_resource_schema(resource_name)
            schemas.append(schema)
        
        return schemas
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get information about the MCP server"""
        if not self.initialized:
            await self.initialize()
        
        return {
            "name": "SOPHIA MCP Server",
            "version": "1.0.0",
            "description": "Model Context Protocol server for SOPHIA AI",
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "timestamp": datetime.now().isoformat()
        }
