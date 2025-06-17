"""
Sophia AI - Property Management MCP Server
Integrates with Yardi, RealPage, AppFolio, and other property management systems
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import os
import sys

# MCP Protocol imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import (
        Resource, Tool, TextContent, ImageContent, EmbeddedResource,
        CallToolRequest, CallToolResult, ListResourcesRequest, ListResourcesResult,
        ListToolsRequest, ListToolsResult, ReadResourceRequest, ReadResourceResult
    )
except ImportError:
    print("MCP library not found. Install with: pip install mcp")
    sys.exit(1)

import httpx
import redis
from ..config.secure_config import get_secure_config

@dataclass
class PropertyManagementConfig:
    """Configuration for Property Management MCP Server"""
    
    # Server Configuration
    server_name: str = "property-management-mcp"
    server_version: str = "1.0.0"
    server_description: str = "Property Management Integration MCP Server for Apartment Industry"
    
    # Property Management Systems
    yardi_api_key: Optional[str] = None
    yardi_api_secret: Optional[str] = None
    yardi_base_url: str = "https://api.yardi.com/v1"
    
    realpage_api_key: Optional[str] = None
    realpage_base_url: str = "https://api.realpage.com/v1"
    
    appfolio_api_key: Optional[str] = None
    appfolio_base_url: str = "https://api.appfolio.com/v1"
    
    entrata_api_key: Optional[str] = None
    entrata_base_url: str = "https://api.entrata.com/v1"
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    def __post_init__(self):
        # Load from secure config
        secure_config = get_secure_config()
        self.yardi_api_key = secure_config.yardi_api_key
        self.yardi_api_secret = secure_config.yardi_api_secret
        self.realpage_api_key = secure_config.realpage_api_key
        self.appfolio_api_key = secure_config.appfolio_api_key
        self.entrata_api_key = secure_config.entrata_api_key

class PropertyManagementMCPServer:
    """
    Property Management MCP Server
    Provides unified access to apartment industry property management systems
    """
    
    def __init__(self, config: PropertyManagementConfig):
        self.config = config
        self.server = Server(config.server_name)
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self.redis_client = None
        self.http_client = None
        
        # API availability tracking
        self.available_systems = {}
        
        # Setup server handlers
        self.setup_server_handlers()
        
        # Initialize connections
        asyncio.create_task(self.initialize_connections())
    
    async def initialize_connections(self):
        """Initialize all service connections"""
        try:
            # Redis connection
            self.redis_client = redis.from_url(self.config.redis_url, decode_responses=True)
            self.logger.info("Redis connection established")
            
            # HTTP client
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Check available systems
            self.available_systems = {
                'yardi': bool(self.config.yardi_api_key),
                'realpage': bool(self.config.realpage_api_key),
                'appfolio': bool(self.config.appfolio_api_key),
                'entrata': bool(self.config.entrata_api_key)
            }
            
            self.logger.info(f"Available property management systems: {[k for k, v in self.available_systems.items() if v]}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connections: {str(e)}")
            raise
    
    def setup_server_handlers(self):
        """Setup MCP server request handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            """List available property management resources"""
            resources = [
                Resource(
                    uri="property://units",
                    name="Property Units",
                    description="Apartment units across all properties",
                    mimeType="application/json"
                ),
                Resource(
                    uri="property://residents",
                    name="Resident Information",
                    description="Current and prospective resident data",
                    mimeType="application/json"
                ),
                Resource(
                    uri="property://leases",
                    name="Lease Agreements",
                    description="Active and historical lease information",
                    mimeType="application/json"
                ),
                Resource(
                    uri="property://maintenance",
                    name="Maintenance Requests",
                    description="Work orders and maintenance history",
                    mimeType="application/json"
                ),
                Resource(
                    uri="property://financials",
                    name="Property Financials",
                    description="Rent rolls, payments, and financial data",
                    mimeType="application/json"
                ),
                Resource(
                    uri="property://occupancy",
                    name="Occupancy Analytics",
                    description="Occupancy rates and availability",
                    mimeType="application/json"
                ),
                Resource(
                    uri="property://market-data",
                    name="Market Intelligence",
                    description="Market comparisons and pricing analytics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="property://compliance",
                    name="Compliance Data",
                    description="Fair housing and regulatory compliance",
                    mimeType="application/json"
                )
            ]
            
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Read specific property management resource"""
            
            if uri == "property://units":
                data = await self.get_units_summary()
            elif uri == "property://residents":
                data = await self.get_residents_summary()
            elif uri == "property://leases":
                data = await self.get_leases_summary()
            elif uri == "property://maintenance":
                data = await self.get_maintenance_summary()
            elif uri == "property://financials":
                data = await self.get_financial_summary()
            elif uri == "property://occupancy":
                data = await self.get_occupancy_analytics()
            elif uri == "property://market-data":
                data = await self.get_market_intelligence()
            elif uri == "property://compliance":
                data = await self.get_compliance_status()
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
            
            content = TextContent(
                type="text",
                text=json.dumps(data, indent=2, default=str)
            )
            
            return ReadResourceResult(contents=[content])
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available property management tools"""
            tools = [
                Tool(
                    name="search_units",
                    description="Search for apartment units",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "property_id": {
                                "type": "string",
                                "description": "Filter by property ID"
                            },
                            "bedrooms": {
                                "type": "integer",
                                "description": "Number of bedrooms"
                            },
                            "max_rent": {
                                "type": "number",
                                "description": "Maximum rent amount"
                            },
                            "available_only": {
                                "type": "boolean",
                                "description": "Show only available units",
                                "default": False
                            },
                            "system": {
                                "type": "string",
                                "enum": ["yardi", "realpage", "appfolio", "entrata", "all"],
                                "description": "Property management system to query",
                                "default": "all"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_resident_info",
                    description="Get resident information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "resident_id": {
                                "type": "string",
                                "description": "Resident ID"
                            },
                            "email": {
                                "type": "string",
                                "description": "Resident email"
                            },
                            "unit_number": {
                                "type": "string",
                                "description": "Unit number"
                            }
                        }
                    }
                ),
                Tool(
                    name="create_maintenance_request",
                    description="Create a maintenance work order",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "unit_id": {
                                "type": "string",
                                "description": "Unit ID"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["plumbing", "electrical", "hvac", "appliance", "other"],
                                "description": "Maintenance category"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["emergency", "high", "medium", "low"],
                                "description": "Priority level"
                            },
                            "description": {
                                "type": "string",
                                "description": "Issue description"
                            }
                        },
                        "required": ["unit_id", "category", "priority", "description"]
                    }
                ),
                Tool(
                    name="get_rent_roll",
                    description="Get rent roll for properties",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "property_id": {
                                "type": "string",
                                "description": "Property ID"
                            },
                            "month": {
                                "type": "string",
                                "description": "Month (YYYY-MM)"
                            },
                            "include_details": {
                                "type": "boolean",
                                "description": "Include detailed breakdown",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="analyze_market_pricing",
                    description="Analyze market pricing and comparisons",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "property_id": {
                                "type": "string",
                                "description": "Property to analyze"
                            },
                            "radius_miles": {
                                "type": "number",
                                "description": "Search radius for comparables",
                                "default": 3
                            },
                            "unit_type": {
                                "type": "string",
                                "description": "Unit type to compare"
                            }
                        },
                        "required": ["property_id"]
                    }
                ),
                Tool(
                    name="sync_property_data",
                    description="Sync data across property management systems",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_system": {
                                "type": "string",
                                "enum": ["yardi", "realpage", "appfolio", "entrata"],
                                "description": "Source system"
                            },
                            "target_system": {
                                "type": "string",
                                "enum": ["yardi", "realpage", "appfolio", "entrata", "sophia"],
                                "description": "Target system"
                            },
                            "data_type": {
                                "type": "string",
                                "enum": ["units", "residents", "leases", "financials"],
                                "description": "Type of data to sync"
                            }
                        },
                        "required": ["source_system", "target_system", "data_type"]
                    }
                )
            ]
            
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool execution requests"""
            
            try:
                if name == "search_units":
                    result = await self.search_units(**arguments)
                elif name == "get_resident_info":
                    result = await self.get_resident_info(**arguments)
                elif name == "create_maintenance_request":
                    result = await self.create_maintenance_request(**arguments)
                elif name == "get_rent_roll":
                    result = await self.get_rent_roll(**arguments)
                elif name == "analyze_market_pricing":
                    result = await self.analyze_market_pricing(**arguments)
                elif name == "sync_property_data":
                    result = await self.sync_property_data(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                content = TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )
                
                return CallToolResult(content=[content])
                
            except Exception as e:
                self.logger.error(f"Tool execution failed: {str(e)}")
                error_content = TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )
                return CallToolResult(content=[error_content], isError=True)
    
    async def search_units(self, property_id: str = None, bedrooms: int = None, 
                          max_rent: float = None, available_only: bool = False,
                          system: str = "all") -> Dict[str, Any]:
        """Search for apartment units across property management systems"""
        units = []
        
        # Query each available system
        if system == "all":
            systems_to_query = [k for k, v in self.available_systems.items() if v]
        else:
            systems_to_query = [system] if self.available_systems.get(system) else []
        
        for sys in systems_to_query:
            try:
                if sys == "yardi":
                    sys_units = await self._search_yardi_units(property_id, bedrooms, max_rent, available_only)
                elif sys == "realpage":
                    sys_units = await self._search_realpage_units(property_id, bedrooms, max_rent, available_only)
                elif sys == "appfolio":
                    sys_units = await self._search_appfolio_units(property_id, bedrooms, max_rent, available_only)
                elif sys == "entrata":
                    sys_units = await self._search_entrata_units(property_id, bedrooms, max_rent, available_only)
                
                units.extend(sys_units)
            except Exception as e:
                self.logger.error(f"Error searching {sys} units: {str(e)}")
        
        # Cache results
        cache_key = f"unit_search:{property_id}:{bedrooms}:{max_rent}:{available_only}"
        self.redis_client.setex(cache_key, 300, json.dumps(units))
        
        return {
            "total_units": len(units),
            "units": units[:100],  # Limit to 100 results
            "systems_queried": systems_to_query,
            "cached": False
        }
    
    async def _search_yardi_units(self, property_id: str = None, bedrooms: int = None,
                                 max_rent: float = None, available_only: bool = False) -> List[Dict]:
        """Search units in Yardi system"""
        if not self.config.yardi_api_key:
            return []
        
        # Mock implementation - replace with actual Yardi API call
        mock_units = [
            {
                "unit_id": "YARDI-001",
                "property_id": "PROP-100",
                "unit_number": "101",
                "bedrooms": 2,
                "bathrooms": 2,
                "sq_ft": 1100,
                "rent": 2500,
                "available": True,
                "available_date": "2024-02-01",
                "system": "yardi"
            }
        ]
        
        return mock_units
    
    async def get_market_intelligence(self) -> Dict[str, Any]:
        """Get market intelligence data"""
        try:
            # Aggregate market data from various sources
            market_data = {
                "average_rents": {
                    "studio": 1800,
                    "1br": 2400,
                    "2br": 3200,
                    "3br": 4500
                },
                "occupancy_rates": {
                    "market_average": 0.945,
                    "submarket_average": 0.952,
                    "competitive_set": 0.948
                },
                "market_trends": {
                    "rent_growth_yoy": 0.042,
                    "occupancy_change": 0.008,
                    "new_supply": 2500,
                    "absorption": 2300
                },
                "competitive_properties": 15,
                "last_updated": datetime.now()
            }
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Failed to get market intelligence: {str(e)}")
            return {"error": str(e)}
    
    async def sync_property_data(self, source_system: str, target_system: str, 
                                data_type: str) -> Dict[str, Any]:
        """Sync data between property management systems"""
        try:
            # Track sync operation
            sync_id = f"sync_{datetime.now().timestamp()}"
            
            # Mock sync operation - replace with actual implementation
            result = {
                "sync_id": sync_id,
                "source": source_system,
                "target": target_system,
                "data_type": data_type,
                "status": "completed",
                "records_synced": 150,
                "errors": 0,
                "duration_seconds": 12.5,
                "timestamp": datetime.now()
            }
            
            # Log sync operation
            self.redis_client.hset(
                "sync_operations",
                sync_id,
                json.dumps(result, default=str)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sync operation failed: {str(e)}")
            return {
                "sync_id": sync_id,
                "status": "failed",
                "error": str(e)
            }

# Additional helper methods would include:
# - get_units_summary()
# - get_residents_summary()
# - get_leases_summary()
# - get_maintenance_summary()
# - get_financial_summary()
# - get_occupancy_analytics()
# - get_compliance_status()
# - API-specific implementations for RealPage, AppFolio, Entrata

async def main():
    """Main entry point for Property Management MCP Server"""
    config = PropertyManagementConfig()
    server = PropertyManagementMCPServer(config)
    
    # Start server
    async with StdioServerParameters() as params:
        await server.server.run(
            params,
            InitializationOptions(
                server_name=config.server_name,
                server_version=config.server_version
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 