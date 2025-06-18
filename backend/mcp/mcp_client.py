"""
MCP Client for Sophia AI
Provides unified interface for agents to interact with MCP servers
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import backoff

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with MCP servers through the gateway"""
    
    def __init__(self, gateway_url: str = "http://localhost:8090", auth_token: Optional[str] = None):
        self.gateway_url = gateway_url
        self.auth_token = auth_token
        self.session = None
        self._servers = {}
        self._tools = {}
        
    async def connect(self):
        """Connect to MCP gateway and discover available servers"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        self.session = aiohttp.ClientSession(headers=headers)
        
        # Discover available servers
        await self._discover_servers()
        
    async def close(self):
        """Close the client connection"""
        if self.session:
            await self.session.close()
            
    async def _discover_servers(self):
        """Discover available MCP servers and their tools"""
        try:
            async with self.session.get(f"{self.gateway_url}/servers") as response:
                if response.status == 200:
                    servers = await response.json()
                    for server in servers:
                        server_name = server["name"]
                        self._servers[server_name] = server
                        
                        # Get tools for each server
                        await self._discover_tools(server_name)
                        
                    logger.info(f"Discovered {len(self._servers)} MCP servers")
                else:
                    logger.error(f"Failed to discover servers: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error discovering servers: {e}")
            
    async def _discover_tools(self, server_name: str):
        """Discover tools available on a specific server"""
        try:
            async with self.session.get(f"{self.gateway_url}/servers/{server_name}/tools") as response:
                if response.status == 200:
                    tools = await response.json()
                    for tool in tools.get("tools", []):
                        tool_key = f"{server_name}.{tool['name']}"
                        self._tools[tool_key] = {
                            "server": server_name,
                            "tool": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["parameters"]
                        }
                    logger.info(f"Discovered {len(tools.get('tools', []))} tools for {server_name}")
                    
        except Exception as e:
            logger.error(f"Error discovering tools for {server_name}: {e}")
            
    def list_servers(self) -> List[str]:
        """List available MCP servers"""
        return list(self._servers.keys())
        
    def list_tools(self, server: Optional[str] = None) -> List[str]:
        """List available tools, optionally filtered by server"""
        if server:
            return [key for key in self._tools.keys() if key.startswith(f"{server}.")]
        return list(self._tools.keys())
        
    def get_tool_info(self, tool_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        return self._tools.get(tool_key)
        
    @backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=3)
    async def call_tool(self, server: str, tool: str, **parameters) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        tool_key = f"{server}.{tool}"
        if tool_key not in self._tools:
            return {
                "error": f"Tool {tool_key} not found",
                "available_tools": self.list_tools(server)
            }
            
        # Validate parameters
        tool_info = self._tools[tool_key]
        required_params = {
            k for k, v in tool_info["parameters"].items() 
            if isinstance(v, dict) and v.get("required", False)
        }
        
        missing_params = required_params - set(parameters.keys())
        if missing_params:
            return {
                "error": f"Missing required parameters: {missing_params}",
                "tool_info": tool_info
            }
            
        # Make the tool call
        payload = {
            "server": server,
            "tool": tool,
            "parameters": parameters
        }
        
        try:
            async with self.session.post(
                f"{self.gateway_url}/tool-call",
                json=payload
            ) as response:
                result = await response.json()
                
                # Add metadata
                result["_metadata"] = {
                    "server": server,
                    "tool": tool,
                    "timestamp": datetime.now().isoformat(),
                    "status_code": response.status
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_key}: {e}")
            return {
                "error": str(e),
                "tool": tool_key
            }
            
    async def batch_call(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple tool calls in parallel"""
        tasks = []
        for call in calls:
            task = self.call_tool(
                call["server"],
                call["tool"],
                **call.get("parameters", {})
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "call": calls[i]
                })
            else:
                processed_results.append(result)
                
        return processed_results
        
    async def execute_workflow(self, workflow: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a sequence of tool calls with dependencies"""
        results = []
        context = {}
        
        for step in workflow:
            # Resolve parameters from context
            parameters = step.get("parameters", {})
            resolved_params = {}
            
            for key, value in parameters.items():
                if isinstance(value, str) and value.startswith("$"):
                    # Reference to previous result
                    ref_path = value[1:].split(".")
                    ref_value = context
                    for part in ref_path:
                        if part.isdigit():
                            ref_value = ref_value[int(part)]
                        else:
                            ref_value = ref_value.get(part, value)
                    resolved_params[key] = ref_value
                else:
                    resolved_params[key] = value
                    
            # Execute the step
            result = await self.call_tool(
                step["server"],
                step["tool"],
                **resolved_params
            )
            
            results.append(result)
            
            # Store result in context
            if "store_as" in step:
                context[step["store_as"]] = result
                
            # Check for stop conditions
            if not result.get("success", True) and step.get("stop_on_error", False):
                break
                
        return results


class MCPToolWrapper:
    """Wrapper to make MCP tools compatible with LangChain/CrewAI"""
    
    def __init__(self, client: MCPClient, server: str, tool: str):
        self.client = client
        self.server = server
        self.tool = tool
        self.tool_info = client.get_tool_info(f"{server}.{tool}")
        
    @property
    def name(self) -> str:
        return f"{self.server}_{self.tool}"
        
    @property
    def description(self) -> str:
        return self.tool_info.get("description", "")
        
    async def __call__(self, **kwargs) -> Any:
        """Execute the tool"""
        result = await self.client.call_tool(self.server, self.tool, **kwargs)
        
        # Extract the actual result or return error
        if result.get("success"):
            return result.get("result", result)
        else:
            raise Exception(result.get("error", "Tool execution failed"))
            
    def as_langchain_tool(self):
        """Convert to LangChain tool format"""
        from langchain.tools import Tool
        
        def sync_wrapper(**kwargs):
            """Synchronous wrapper for LangChain compatibility"""
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self(**kwargs))
            
        return Tool(
            name=self.name,
            description=self.description,
            func=sync_wrapper
        ) 