"""
Sophia AI - Model Context Protocol (MCP) Server
Production-ready MCP server for business intelligence integration
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
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

# Database and AI service imports
import psycopg2
import redis
import pinecone
import weaviate
from openai import OpenAI

@dataclass
class SophiaMCPConfig:
    """Configuration for Sophia AI MCP Server"""
    
    # Server Configuration
    server_name: str = "sophia-payready-mcp"
    server_version: str = "1.0.0"
    server_description: str = "Sophia AI Pay Ready Business Intelligence MCP Server"
    
    # Database Configuration
    database_url: str = os.getenv("POSTGRES_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    
    # Vector Database Configuration
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-west-2")
    pinecone_index: str = os.getenv("PINECONE_INDEX", "sophia-payready")

    weaviate_url: str = os.getenv("WEAVIATE_URL", "")
    weaviate_api_key: str = os.getenv("WEAVIATE_API_KEY", "")
    weaviate_class: str = os.getenv("WEAVIATE_CLASS", "SophiaPayReady")
    
    # AI Service Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # Business Intelligence Configuration
    business_units: List[str] = None
    departments: List[str] = None
    metric_types: List[str] = None
    
    def __post_init__(self):
        if self.business_units is None:
            self.business_units = ["pay_ready_core", "pay_ready_plus", "enterprise"]
        
        if self.departments is None:
            self.departments = ["sales", "marketing", "finance", "hr", "operations", "strategy"]
        
        if self.metric_types is None:
            self.metric_types = ["revenue", "growth", "efficiency", "satisfaction", "retention"]

class SophiaPayReadyMCPServer:
    """
    Sophia AI Pay Ready MCP Server
    Provides business intelligence context and tools to AI models
    """
    
    def __init__(self, config: SophiaMCPConfig):
        self.config = config
        self.server = Server(config.server_name)
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self.db_connection = None
        self.redis_client = None
        self.pinecone_index = None
        self.weaviate_client = None
        self.openai_client = None
        
        # Setup server handlers
        self.setup_server_handlers()
        
        # Initialize connections
        asyncio.create_task(self.initialize_connections())
    
    async def initialize_connections(self):
        """Initialize all external service connections"""
        try:
            # Database connection
            self.db_connection = psycopg2.connect(self.config.database_url)
            self.logger.info("PostgreSQL connection established")
            
            # Redis connection
            self.redis_client = redis.from_url(self.config.redis_url, decode_responses=True)
            self.logger.info("Redis connection established")
            
            # Pinecone connection
            pinecone.init(
                api_key=self.config.pinecone_api_key,
                environment=self.config.pinecone_environment
            )
            self.pinecone_index = pinecone.Index(self.config.pinecone_index)
            self.logger.info("Pinecone connection established")
            
            # Weaviate connection
            auth_config = weaviate.AuthApiKey(api_key=self.config.weaviate_api_key)
            self.weaviate_client = weaviate.Client(
                url=self.config.weaviate_url,
                auth_client_secret=auth_config
            )
            self.logger.info("Weaviate connection established")
            
            # OpenAI connection
            if self.config.openai_api_key:
                self.openai_client = OpenAI(api_key=self.config.openai_api_key)
                self.logger.info("OpenAI connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connections: {str(e)}")
            raise
    
    def setup_server_handlers(self):
        """Setup MCP server request handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            """List available business intelligence resources"""
            resources = [
                Resource(
                    uri="sophia://business-metrics",
                    name="Business Metrics",
                    description="Real-time business performance metrics and KPIs",
                    mimeType="application/json"
                ),
                Resource(
                    uri="sophia://financial-data",
                    name="Financial Data",
                    description="Revenue, expenses, and financial performance data",
                    mimeType="application/json"
                ),
                Resource(
                    uri="sophia://customer-analytics",
                    name="Customer Analytics",
                    description="Customer acquisition, retention, and satisfaction metrics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="sophia://operational-metrics",
                    name="Operational Metrics",
                    description="System performance and operational efficiency data",
                    mimeType="application/json"
                ),
                Resource(
                    uri="sophia://strategic-insights",
                    name="Strategic Insights",
                    description="AI-generated strategic recommendations and market analysis",
                    mimeType="application/json"
                ),
                Resource(
                    uri="sophia://knowledge-base",
                    name="Knowledge Base",
                    description="Searchable business intelligence knowledge base",
                    mimeType="application/json"
                )
            ]
            
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Read specific business intelligence resource"""
            
            if uri == "sophia://business-metrics":
                data = await self.get_business_metrics()
            elif uri == "sophia://financial-data":
                data = await self.get_financial_data()
            elif uri == "sophia://customer-analytics":
                data = await self.get_customer_analytics()
            elif uri == "sophia://operational-metrics":
                data = await self.get_operational_metrics()
            elif uri == "sophia://strategic-insights":
                data = await self.get_strategic_insights()
            elif uri == "sophia://knowledge-base":
                data = await self.get_knowledge_base_summary()
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
            
            content = TextContent(
                type="text",
                text=json.dumps(data, indent=2, default=str)
            )
            
            return ReadResourceResult(contents=[content])
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available business intelligence tools"""
            tools = [
                Tool(
                    name="query_business_data",
                    description="Query business data using natural language",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query for business data"
                            },
                            "department": {
                                "type": "string",
                                "enum": self.config.departments,
                                "description": "Filter by department"
                            },
                            "business_unit": {
                                "type": "string",
                                "enum": self.config.business_units,
                                "description": "Filter by business unit"
                            },
                            "metric_type": {
                                "type": "string",
                                "enum": self.config.metric_types,
                                "description": "Filter by metric type"
                            },
                            "time_range": {
                                "type": "string",
                                "enum": ["today", "week", "month", "quarter", "year"],
                                "description": "Time range for data"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="semantic_search",
                    description="Perform semantic search across business intelligence data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            },
                            "filters": {
                                "type": "object",
                                "description": "Additional filters for search"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="generate_insights",
                    description="Generate AI-powered business insights",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "context": {
                                "type": "string",
                                "description": "Business context for insight generation"
                            },
                            "focus_area": {
                                "type": "string",
                                "enum": ["revenue", "growth", "efficiency", "strategy", "operations"],
                                "description": "Focus area for insights"
                            },
                            "time_horizon": {
                                "type": "string",
                                "enum": ["short_term", "medium_term", "long_term"],
                                "description": "Time horizon for insights"
                            }
                        },
                        "required": ["context"]
                    }
                ),
                Tool(
                    name="update_business_data",
                    description="Update business data and metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data_type": {
                                "type": "string",
                                "enum": ["metric", "kpi", "goal", "target"],
                                "description": "Type of data to update"
                            },
                            "data": {
                                "type": "object",
                                "description": "Data to update"
                            },
                            "source": {
                                "type": "string",
                                "description": "Source of the data update"
                            }
                        },
                        "required": ["data_type", "data"]
                    }
                ),
                Tool(
                    name="health_check",
                    description="Check health status of all connected services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "detailed": {
                                "type": "boolean",
                                "description": "Include detailed health information",
                                "default": False
                            }
                        }
                    }
                )
            ]
            
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool execution requests"""
            
            try:
                if name == "query_business_data":
                    result = await self.query_business_data(**arguments)
                elif name == "semantic_search":
                    result = await self.semantic_search(**arguments)
                elif name == "generate_insights":
                    result = await self.generate_insights(**arguments)
                elif name == "update_business_data":
                    result = await self.update_business_data(**arguments)
                elif name == "health_check":
                    result = await self.health_check(**arguments)
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
    
    async def get_business_metrics(self) -> Dict[str, Any]:
        """Get current business metrics and KPIs"""
        try:
            # Check Redis cache first
            cached_metrics = self.redis_client.get("business_metrics")
            if cached_metrics:
                return json.loads(cached_metrics)
            
            # Query database for metrics
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        metric_name,
                        metric_value,
                        metric_type,
                        department,
                        business_unit,
                        created_at
                    FROM business_metrics 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    ORDER BY created_at DESC
                """)
                
                metrics = []
                for row in cursor.fetchall():
                    metrics.append({
                        "name": row[0],
                        "value": row[1],
                        "type": row[2],
                        "department": row[3],
                        "business_unit": row[4],
                        "timestamp": row[5]
                    })
            
            # Cache results
            self.redis_client.setex(
                "business_metrics", 
                300,  # 5 minutes
                json.dumps(metrics, default=str)
            )
            
            return {"metrics": metrics, "last_updated": datetime.now()}
            
        except Exception as e:
            self.logger.error(f"Failed to get business metrics: {str(e)}")
            return {"error": str(e)}
    
    async def get_financial_data(self) -> Dict[str, Any]:
        """Get financial performance data"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        revenue_total,
                        revenue_recurring,
                        expenses_total,
                        profit_margin,
                        customer_acquisition_cost,
                        lifetime_value,
                        period_start,
                        period_end
                    FROM financial_summary 
                    WHERE period_end >= NOW() - INTERVAL '90 days'
                    ORDER BY period_end DESC
                """)
                
                financial_data = []
                for row in cursor.fetchall():
                    financial_data.append({
                        "revenue_total": row[0],
                        "revenue_recurring": row[1],
                        "expenses_total": row[2],
                        "profit_margin": row[3],
                        "customer_acquisition_cost": row[4],
                        "lifetime_value": row[5],
                        "period_start": row[6],
                        "period_end": row[7]
                    })
            
            return {"financial_data": financial_data, "last_updated": datetime.now()}
            
        except Exception as e:
            self.logger.error(f"Failed to get financial data: {str(e)}")
            return {"error": str(e)}
    
    async def get_customer_analytics(self) -> Dict[str, Any]:
        """Get customer analytics and insights"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        total_customers,
                        new_customers,
                        churned_customers,
                        retention_rate,
                        satisfaction_score,
                        nps_score,
                        period_date
                    FROM customer_analytics 
                    WHERE period_date >= NOW() - INTERVAL '30 days'
                    ORDER BY period_date DESC
                """)
                
                customer_data = []
                for row in cursor.fetchall():
                    customer_data.append({
                        "total_customers": row[0],
                        "new_customers": row[1],
                        "churned_customers": row[2],
                        "retention_rate": row[3],
                        "satisfaction_score": row[4],
                        "nps_score": row[5],
                        "period_date": row[6]
                    })
            
            return {"customer_analytics": customer_data, "last_updated": datetime.now()}
            
        except Exception as e:
            self.logger.error(f"Failed to get customer analytics: {str(e)}")
            return {"error": str(e)}
    
    async def get_operational_metrics(self) -> Dict[str, Any]:
        """Get operational performance metrics"""
        try:
            # Get system metrics from Redis
            system_metrics = {
                "database_connections": self.redis_client.get("db_connections") or "0",
                "api_response_time": self.redis_client.get("api_response_time") or "0",
                "error_rate": self.redis_client.get("error_rate") or "0",
                "uptime": self.redis_client.get("uptime") or "0"
            }
            
            # Get operational KPIs from database
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        process_efficiency,
                        automation_rate,
                        quality_score,
                        team_productivity,
                        system_availability,
                        created_at
                    FROM operational_metrics 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                operational_kpis = {}
                if row:
                    operational_kpis = {
                        "process_efficiency": row[0],
                        "automation_rate": row[1],
                        "quality_score": row[2],
                        "team_productivity": row[3],
                        "system_availability": row[4],
                        "last_updated": row[5]
                    }
            
            return {
                "system_metrics": system_metrics,
                "operational_kpis": operational_kpis,
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get operational metrics: {str(e)}")
            return {"error": str(e)}
    
    async def get_strategic_insights(self) -> Dict[str, Any]:
        """Get AI-generated strategic insights"""
        try:
            # Get recent insights from cache
            cached_insights = self.redis_client.get("strategic_insights")
            if cached_insights:
                return json.loads(cached_insights)
            
            # Generate new insights using AI
            if self.openai_client:
                # Get recent business data for context
                business_metrics = await self.get_business_metrics()
                financial_data = await self.get_financial_data()
                
                context = f"""
                Recent Business Metrics: {json.dumps(business_metrics, default=str)}
                Recent Financial Data: {json.dumps(financial_data, default=str)}
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are Sophia AI, a business intelligence assistant for Pay Ready. Generate strategic insights based on the provided business data."
                        },
                        {
                            "role": "user",
                            "content": f"Based on this business data, provide strategic insights and recommendations: {context}"
                        }
                    ],
                    max_tokens=1000
                )
                
                insights = {
                    "ai_insights": response.choices[0].message.content,
                    "generated_at": datetime.now(),
                    "model_used": "gpt-4"
                }
                
                # Cache insights for 1 hour
                self.redis_client.setex(
                    "strategic_insights",
                    3600,
                    json.dumps(insights, default=str)
                )
                
                return insights
            else:
                return {"error": "OpenAI client not configured"}
                
        except Exception as e:
            self.logger.error(f"Failed to get strategic insights: {str(e)}")
            return {"error": str(e)}
    
    async def get_knowledge_base_summary(self) -> Dict[str, Any]:
        """Get knowledge base summary and statistics"""
        try:
            # Get Pinecone index stats
            pinecone_stats = self.pinecone_index.describe_index_stats()
            
            # Get Weaviate class info
            weaviate_schema = self.weaviate_client.schema.get(self.config.weaviate_class)
            
            # Get recent documents count
            weaviate_count = self.weaviate_client.query.aggregate(self.config.weaviate_class).with_meta_count().do()
            
            return {
                "pinecone_stats": pinecone_stats,
                "weaviate_schema": weaviate_schema,
                "weaviate_document_count": weaviate_count,
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get knowledge base summary: {str(e)}")
            return {"error": str(e)}
    
    async def query_business_data(self, query: str, **filters) -> Dict[str, Any]:
        """Query business data using natural language"""
        try:
            # Use semantic search to find relevant data
            search_results = await self.semantic_search(query, limit=5, filters=filters)
            
            # Generate SQL query based on natural language (simplified)
            # In production, this would use more sophisticated NL-to-SQL
            sql_conditions = []
            params = []
            
            if filters.get("department"):
                sql_conditions.append("department = %s")
                params.append(filters["department"])
            
            if filters.get("business_unit"):
                sql_conditions.append("business_unit = %s")
                params.append(filters["business_unit"])
            
            if filters.get("time_range"):
                time_mapping = {
                    "today": "created_at >= CURRENT_DATE",
                    "week": "created_at >= NOW() - INTERVAL '7 days'",
                    "month": "created_at >= NOW() - INTERVAL '30 days'",
                    "quarter": "created_at >= NOW() - INTERVAL '90 days'",
                    "year": "created_at >= NOW() - INTERVAL '365 days'"
                }
                if filters["time_range"] in time_mapping:
                    sql_conditions.append(time_mapping[filters["time_range"]])
            
            where_clause = " AND ".join(sql_conditions) if sql_conditions else "1=1"
            
            with self.db_connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT * FROM business_metrics 
                    WHERE {where_clause}
                    ORDER BY created_at DESC 
                    LIMIT 50
                """, params)
                
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                data = []
                for row in results:
                    data.append(dict(zip(columns, row)))
            
            return {
                "query": query,
                "filters": filters,
                "semantic_results": search_results,
                "database_results": data,
                "result_count": len(data)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to query business data: {str(e)}")
            return {"error": str(e)}
    
    async def semantic_search(self, query: str, limit: int = 10, filters: Dict = None) -> Dict[str, Any]:
        """Perform semantic search across business intelligence data"""
        try:
            # Get query embedding
            if self.openai_client:
                embedding_response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=query
                )
                query_vector = embedding_response.data[0].embedding
            else:
                # Fallback to dummy vector
                query_vector = [0.0] * 1536
            
            # Search Pinecone
            pinecone_results = self.pinecone_index.query(
                vector=query_vector,
                top_k=limit,
                include_metadata=True,
                filter=filters or {}
            )
            
            # Search Weaviate
            weaviate_query = (
                self.weaviate_client.query
                .get(self.config.weaviate_class, ["content", "title", "category"])
                .with_hybrid(query=query)
                .with_limit(limit)
            )
            
            if filters:
                # Convert filters to Weaviate format
                where_conditions = []
                for key, value in filters.items():
                    where_conditions.append({
                        "path": [key],
                        "operator": "Equal",
                        "valueString": str(value)
                    })
                
                if where_conditions:
                    weaviate_query = weaviate_query.with_where({
                        "operator": "And",
                        "operands": where_conditions
                    })
            
            weaviate_results = weaviate_query.do()
            
            return {
                "query": query,
                "pinecone_results": pinecone_results,
                "weaviate_results": weaviate_results,
                "total_results": len(pinecone_results.get("matches", [])) + len(weaviate_results.get("data", {}).get("Get", {}).get(self.config.weaviate_class, []))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to perform semantic search: {str(e)}")
            return {"error": str(e)}
    
    async def generate_insights(self, context: str, focus_area: str = None, time_horizon: str = "medium_term") -> Dict[str, Any]:
        """Generate AI-powered business insights"""
        try:
            if not self.openai_client:
                return {"error": "OpenAI client not configured"}
            
            # Get relevant business data for context
            business_data = await self.get_business_metrics()
            financial_data = await self.get_financial_data()
            
            system_prompt = f"""
            You are Sophia AI, an expert business intelligence assistant for Pay Ready.
            Focus Area: {focus_area or 'general business strategy'}
            Time Horizon: {time_horizon}
            
            Provide actionable insights and recommendations based on the business context and data.
            """
            
            user_prompt = f"""
            Business Context: {context}
            
            Current Business Metrics: {json.dumps(business_data, default=str)}
            Financial Data: {json.dumps(financial_data, default=str)}
            
            Generate strategic insights and specific recommendations.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            insights = {
                "context": context,
                "focus_area": focus_area,
                "time_horizon": time_horizon,
                "insights": response.choices[0].message.content,
                "generated_at": datetime.now(),
                "model_used": "gpt-4"
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate insights: {str(e)}")
            return {"error": str(e)}
    
    async def update_business_data(self, data_type: str, data: Dict[str, Any], source: str = "mcp_server") -> Dict[str, Any]:
        """Update business data and metrics"""
        try:
            with self.db_connection.cursor() as cursor:
                if data_type == "metric":
                    cursor.execute("""
                        INSERT INTO business_metrics 
                        (metric_name, metric_value, metric_type, department, business_unit, source, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data.get("name"),
                        data.get("value"),
                        data.get("type"),
                        data.get("department"),
                        data.get("business_unit"),
                        source,
                        datetime.now()
                    ))
                elif data_type == "kpi":
                    cursor.execute("""
                        INSERT INTO kpi_tracking 
                        (kpi_name, current_value, target_value, department, period_start, period_end, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data.get("name"),
                        data.get("current_value"),
                        data.get("target_value"),
                        data.get("department"),
                        data.get("period_start"),
                        data.get("period_end"),
                        datetime.now()
                    ))
                
                self.db_connection.commit()
            
            # Clear relevant caches
            self.redis_client.delete("business_metrics")
            
            return {
                "status": "success",
                "data_type": data_type,
                "updated_at": datetime.now(),
                "source": source
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update business data: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self, detailed: bool = False) -> Dict[str, Any]:
        """Check health status of all connected services"""
        health_status = {
            "server": {"status": "healthy", "timestamp": datetime.now()},
            "database": {"status": "unknown"},
            "redis": {"status": "unknown"},
            "pinecone": {"status": "unknown"},
            "weaviate": {"status": "unknown"},
            "openai": {"status": "unknown"}
        }
        
        # Test database connection
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_status["database"]["status"] = "healthy"
        except Exception as e:
            health_status["database"]["status"] = "unhealthy"
            health_status["database"]["error"] = str(e)
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            health_status["redis"]["status"] = "healthy"
        except Exception as e:
            health_status["redis"]["status"] = "unhealthy"
            health_status["redis"]["error"] = str(e)
        
        # Test Pinecone connection
        try:
            stats = self.pinecone_index.describe_index_stats()
            health_status["pinecone"]["status"] = "healthy"
            if detailed:
                health_status["pinecone"]["stats"] = stats
        except Exception as e:
            health_status["pinecone"]["status"] = "unhealthy"
            health_status["pinecone"]["error"] = str(e)
        
        # Test Weaviate connection
        try:
            meta = self.weaviate_client.get_meta()
            health_status["weaviate"]["status"] = "healthy"
            if detailed:
                health_status["weaviate"]["meta"] = meta
        except Exception as e:
            health_status["weaviate"]["status"] = "unhealthy"
            health_status["weaviate"]["error"] = str(e)
        
        # Test OpenAI connection
        try:
            if self.openai_client:
                # Simple test call
                response = self.openai_client.models.list()
                health_status["openai"]["status"] = "healthy"
                if detailed:
                    health_status["openai"]["models_count"] = len(response.data)
            else:
                health_status["openai"]["status"] = "not_configured"
        except Exception as e:
            health_status["openai"]["status"] = "unhealthy"
            health_status["openai"]["error"] = str(e)
        
        return health_status

async def main():
    """Main function to run the Sophia AI MCP Server"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration
    config = SophiaMCPConfig()
    
    # Create and initialize server
    mcp_server = SophiaPayReadyMCPServer(config)
    
    # Run server
    async with mcp_server.server.stdio_server() as (read_stream, write_stream):
        await mcp_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=config.server_name,
                server_version=config.server_version,
                capabilities=mcp_server.server.get_capabilities()
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

