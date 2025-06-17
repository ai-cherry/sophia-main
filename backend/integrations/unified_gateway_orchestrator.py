"""
Sophia AI - Unified API Gateway Orchestrator
Intelligent routing and management across multiple API gateways
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import httpx
import redis

from ..config.secure_config import get_secure_config

class GatewayType(Enum):
    """Available gateway types"""
    KONG = "kong"
    PORTKEY = "portkey"
    OPENROUTER = "openrouter"
    DIRECT = "direct"
    CUSTOM = "custom"

class ServiceCategory(Enum):
    """Service categories for routing"""
    LLM = "llm"
    VECTOR_DB = "vector_db"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    PROPERTY_MANAGEMENT = "property_management"
    ANALYTICS = "analytics"
    COMMUNICATION = "communication"
    INFRASTRUCTURE = "infrastructure"

@dataclass
class GatewayRoute:
    """Configuration for a gateway route"""
    service_name: str
    category: ServiceCategory
    gateway_type: GatewayType
    endpoint: str
    api_key_name: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    rate_limit: int = 100  # requests per minute
    timeout: float = 30.0
    retry_count: int = 3
    priority: int = 1
    health_check_endpoint: Optional[str] = None
    cost_per_request: float = 0.0
    
@dataclass
class GatewayMetrics:
    """Metrics for gateway performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    total_cost: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_latency(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency / self.successful_requests

class UnifiedGatewayOrchestrator:
    """
    Unified API Gateway Orchestrator
    Manages routing, failover, and optimization across all API gateways
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.secure_config = get_secure_config()
        self.redis_client = redis.Redis.from_url(
            "redis://localhost:6379/0",
            decode_responses=True
        )
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        # Route registry
        self.routes: Dict[str, List[GatewayRoute]] = {}
        self.metrics: Dict[str, GatewayMetrics] = {}
        
        # Initialize routes
        self._initialize_routes()
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._metrics_aggregation_loop())
    
    def _initialize_routes(self):
        """Initialize all gateway routes"""
        
        # LLM Routes
        self._add_llm_routes()
        
        # Vector Database Routes
        self._add_vector_db_routes()
        
        # Business Intelligence Routes
        self._add_business_intelligence_routes()
        
        # Property Management Routes
        self._add_property_management_routes()
        
        # Analytics Routes
        self._add_analytics_routes()
        
        # Communication Routes
        self._add_communication_routes()
        
        self.logger.info(f"Initialized {sum(len(routes) for routes in self.routes.values())} routes across {len(self.routes)} services")
    
    def _add_llm_routes(self):
        """Add LLM service routes"""
        llm_routes = []
        
        # Portkey Gateway (Primary)
        if self.secure_config.portkey_api_key:
            llm_routes.append(GatewayRoute(
                service_name="llm",
                category=ServiceCategory.LLM,
                gateway_type=GatewayType.PORTKEY,
                endpoint="https://api.portkey.ai/v1/proxy",
                api_key_name="portkey_api_key",
                headers={"x-portkey-mode": "proxy"},
                rate_limit=1000,
                priority=1,
                cost_per_request=0.0001
            ))
        
        # OpenRouter (Secondary)
        if self.secure_config.openrouter_api_key:
            llm_routes.append(GatewayRoute(
                service_name="llm",
                category=ServiceCategory.LLM,
                gateway_type=GatewayType.OPENROUTER,
                endpoint="https://openrouter.ai/api/v1",
                api_key_name="openrouter_api_key",
                rate_limit=500,
                priority=2,
                cost_per_request=0.0002
            ))
        
        # Direct OpenAI
        if self.secure_config.openai_api_key:
            llm_routes.append(GatewayRoute(
                service_name="llm",
                category=ServiceCategory.LLM,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.openai.com/v1",
                api_key_name="openai_api_key",
                rate_limit=200,
                priority=3,
                cost_per_request=0.0003
            ))
        
        # Direct Anthropic
        if self.secure_config.anthropic_api_key:
            llm_routes.append(GatewayRoute(
                service_name="llm",
                category=ServiceCategory.LLM,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.anthropic.com/v1",
                api_key_name="anthropic_api_key",
                headers={"anthropic-version": "2023-06-01"},
                rate_limit=100,
                priority=4,
                cost_per_request=0.0004
            ))
        
        self.routes["llm"] = llm_routes
    
    def _add_vector_db_routes(self):
        """Add vector database routes"""
        vector_routes = []
        
        # Pinecone
        if self.secure_config.pinecone_api_key:
            vector_routes.append(GatewayRoute(
                service_name="pinecone",
                category=ServiceCategory.VECTOR_DB,
                gateway_type=GatewayType.DIRECT,
                endpoint=f"https://api.pinecone.io",
                api_key_name="pinecone_api_key",
                rate_limit=1000,
                priority=1
            ))
        
        # Weaviate
        if self.secure_config.weaviate_api_key:
            vector_routes.append(GatewayRoute(
                service_name="weaviate",
                category=ServiceCategory.VECTOR_DB,
                gateway_type=GatewayType.DIRECT,
                endpoint=self.secure_config.weaviate_url or "https://weaviate.io",
                api_key_name="weaviate_api_key",
                rate_limit=1000,
                priority=1
            ))
        
        self.routes["vector_db"] = vector_routes
    
    def _add_business_intelligence_routes(self):
        """Add business intelligence service routes"""
        bi_routes = []
        
        # HubSpot
        if self.secure_config.hubspot_api_key:
            bi_routes.append(GatewayRoute(
                service_name="hubspot",
                category=ServiceCategory.BUSINESS_INTELLIGENCE,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.hubapi.com",
                api_key_name="hubspot_api_key",
                rate_limit=100,
                priority=1
            ))
        
        # Gong.io
        if self.secure_config.gong_api_key:
            bi_routes.append(GatewayRoute(
                service_name="gong",
                category=ServiceCategory.BUSINESS_INTELLIGENCE,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.gong.io/v2",
                api_key_name="gong_api_key",
                headers={"Content-Type": "application/json"},
                rate_limit=50,
                priority=1
            ))
        
        # Salesforce
        if self.secure_config.salesforce_api_key:
            bi_routes.append(GatewayRoute(
                service_name="salesforce",
                category=ServiceCategory.BUSINESS_INTELLIGENCE,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.salesforce.com",
                api_key_name="salesforce_api_key",
                rate_limit=100,
                priority=1
            ))
        
        self.routes["business_intelligence"] = bi_routes
    
    def _add_property_management_routes(self):
        """Add property management service routes"""
        pm_routes = []
        
        # Yardi
        if self.secure_config.yardi_api_key:
            pm_routes.append(GatewayRoute(
                service_name="yardi",
                category=ServiceCategory.PROPERTY_MANAGEMENT,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.yardi.com/v1",
                api_key_name="yardi_api_key",
                rate_limit=50,
                priority=1
            ))
        
        # RealPage
        if self.secure_config.realpage_api_key:
            pm_routes.append(GatewayRoute(
                service_name="realpage",
                category=ServiceCategory.PROPERTY_MANAGEMENT,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.realpage.com/v1",
                api_key_name="realpage_api_key",
                rate_limit=50,
                priority=1
            ))
        
        # AppFolio
        if self.secure_config.appfolio_api_key:
            pm_routes.append(GatewayRoute(
                service_name="appfolio",
                category=ServiceCategory.PROPERTY_MANAGEMENT,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.appfolio.com/v1",
                api_key_name="appfolio_api_key",
                rate_limit=50,
                priority=1
            ))
        
        # CoStar
        if self.secure_config.costar_api_key:
            pm_routes.append(GatewayRoute(
                service_name="costar",
                category=ServiceCategory.PROPERTY_MANAGEMENT,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.costar.com/v1",
                api_key_name="costar_api_key",
                rate_limit=100,
                priority=1
            ))
        
        self.routes["property_management"] = pm_routes
    
    def _add_analytics_routes(self):
        """Add analytics service routes"""
        analytics_routes = []
        
        # Arize AI (through Kong)
        if self.secure_config.arize_api_key and self.secure_config.kong_access_token:
            analytics_routes.append(GatewayRoute(
                service_name="arize",
                category=ServiceCategory.ANALYTICS,
                gateway_type=GatewayType.KONG,
                endpoint="https://api.konghq.com/arize",
                api_key_name="kong_access_token",
                headers={"X-Arize-Api-Key": self.secure_config.arize_api_key},
                rate_limit=100,
                priority=1
            ))
        
        # Google Analytics
        if self.secure_config.google_analytics_key:
            analytics_routes.append(GatewayRoute(
                service_name="google_analytics",
                category=ServiceCategory.ANALYTICS,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://analytics.googleapis.com/v1",
                api_key_name="google_analytics_key",
                rate_limit=100,
                priority=2
            ))
        
        self.routes["analytics"] = analytics_routes
    
    def _add_communication_routes(self):
        """Add communication service routes"""
        comm_routes = []
        
        # Slack
        if self.secure_config.slack_bot_token:
            comm_routes.append(GatewayRoute(
                service_name="slack",
                category=ServiceCategory.COMMUNICATION,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://slack.com/api",
                api_key_name="slack_bot_token",
                rate_limit=50,
                priority=1
            ))
        
        # Twilio
        if self.secure_config.twilio_account_sid:
            comm_routes.append(GatewayRoute(
                service_name="twilio",
                category=ServiceCategory.COMMUNICATION,
                gateway_type=GatewayType.DIRECT,
                endpoint="https://api.twilio.com",
                api_key_name="twilio_auth_token",
                rate_limit=100,
                priority=1
            ))
        
        self.routes["communication"] = comm_routes
    
    async def route_request(
        self,
        service_name: str,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        prefer_gateway: Optional[GatewayType] = None
    ) -> Dict[str, Any]:
        """
        Route a request through the optimal gateway
        
        Args:
            service_name: Name of the service to route to
            method: HTTP method
            path: API path
            data: Request data
            headers: Additional headers
            prefer_gateway: Preferred gateway type
            
        Returns:
            Response data
        """
        # Get available routes for service
        available_routes = self._get_available_routes(service_name, prefer_gateway)
        
        if not available_routes:
            raise ValueError(f"No available routes for service: {service_name}")
        
        # Sort by priority and success rate
        sorted_routes = self._sort_routes_by_performance(available_routes)
        
        # Try routes in order
        last_error = None
        for route in sorted_routes:
            try:
                # Check rate limit
                if not await self._check_rate_limit(route):
                    continue
                
                # Make request
                response = await self._execute_request(route, method, path, data, headers)
                
                # Update metrics
                await self._update_metrics(route, success=True, latency=response.get("latency", 0))
                
                return response
                
            except Exception as e:
                last_error = e
                await self._update_metrics(route, success=False, error=str(e))
                self.logger.warning(f"Route failed for {route.service_name} via {route.gateway_type}: {str(e)}")
                continue
        
        # All routes failed
        raise Exception(f"All routes failed for {service_name}. Last error: {last_error}")
    
    def _get_available_routes(
        self,
        service_name: str,
        prefer_gateway: Optional[GatewayType] = None
    ) -> List[GatewayRoute]:
        """Get available routes for a service"""
        routes = []
        
        # Check all route categories
        for category_routes in self.routes.values():
            for route in category_routes:
                if route.service_name == service_name:
                    # Check if API key is configured
                    if route.api_key_name:
                        api_key = getattr(self.secure_config, route.api_key_name, None)
                        if not api_key:
                            continue
                    
                    # Apply gateway preference
                    if prefer_gateway and route.gateway_type != prefer_gateway:
                        continue
                    
                    routes.append(route)
        
        return routes
    
    def _sort_routes_by_performance(self, routes: List[GatewayRoute]) -> List[GatewayRoute]:
        """Sort routes by performance metrics"""
        def route_score(route: GatewayRoute) -> float:
            metrics = self.metrics.get(f"{route.service_name}:{route.gateway_type.value}", GatewayMetrics())
            
            # Calculate score based on success rate, latency, and cost
            success_weight = 0.5
            latency_weight = 0.3
            cost_weight = 0.2
            
            success_score = metrics.success_rate * success_weight
            latency_score = (1 / (1 + metrics.average_latency)) * latency_weight
            cost_score = (1 / (1 + route.cost_per_request)) * cost_weight
            
            # Apply priority boost
            priority_boost = 1 / route.priority
            
            return (success_score + latency_score + cost_score) * priority_boost
        
        return sorted(routes, key=route_score, reverse=True)
    
    async def _check_rate_limit(self, route: GatewayRoute) -> bool:
        """Check if route is within rate limit"""
        key = f"rate_limit:{route.service_name}:{route.gateway_type.value}"
        current = self.redis_client.incr(key)
        
        if current == 1:
            self.redis_client.expire(key, 60)  # Reset every minute
        
        return current <= route.rate_limit
    
    async def _execute_request(
        self,
        route: GatewayRoute,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute request through gateway"""
        start_time = datetime.now()
        
        # Build URL
        url = f"{route.endpoint}{path}"
        
        # Build headers
        request_headers = route.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Add authentication
        if route.api_key_name:
            api_key = getattr(self.secure_config, route.api_key_name)
            if route.gateway_type == GatewayType.PORTKEY:
                request_headers["x-portkey-api-key"] = api_key
            elif route.gateway_type == GatewayType.OPENROUTER:
                request_headers["Authorization"] = f"Bearer {api_key}"
            else:
                request_headers["Authorization"] = f"Bearer {api_key}"
        
        # Make request
        response = await self.http_client.request(
            method=method,
            url=url,
            json=data,
            headers=request_headers,
            timeout=route.timeout
        )
        
        response.raise_for_status()
        
        # Calculate latency
        latency = (datetime.now() - start_time).total_seconds()
        
        result = response.json() if response.content else {}
        result["_gateway_metadata"] = {
            "gateway_type": route.gateway_type.value,
            "latency": latency,
            "route": route.service_name
        }
        
        return result
    
    async def _update_metrics(
        self,
        route: GatewayRoute,
        success: bool,
        latency: float = 0,
        error: Optional[str] = None
    ):
        """Update route metrics"""
        key = f"{route.service_name}:{route.gateway_type.value}"
        
        if key not in self.metrics:
            self.metrics[key] = GatewayMetrics()
        
        metrics = self.metrics[key]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
            metrics.total_latency += latency
            metrics.total_cost += route.cost_per_request
        else:
            metrics.failed_requests += 1
            metrics.last_error = error
            metrics.last_error_time = datetime.now()
        
        # Store in Redis for persistence
        self.redis_client.hset(
            "gateway_metrics",
            key,
            json.dumps({
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "average_latency": metrics.average_latency,
                "total_cost": metrics.total_cost,
                "success_rate": metrics.success_rate
            })
        )
    
    async def _health_check_loop(self):
        """Background task to check gateway health"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                for category_routes in self.routes.values():
                    for route in category_routes:
                        if route.health_check_endpoint:
                            try:
                                response = await self.http_client.get(
                                    route.health_check_endpoint,
                                    timeout=10.0
                                )
                                health_status = response.status_code == 200
                            except:
                                health_status = False
                            
                            # Store health status
                            self.redis_client.hset(
                                "gateway_health",
                                f"{route.service_name}:{route.gateway_type.value}",
                                json.dumps({
                                    "healthy": health_status,
                                    "last_check": datetime.now().isoformat()
                                })
                            )
                
            except Exception as e:
                self.logger.error(f"Health check error: {str(e)}")
    
    async def _metrics_aggregation_loop(self):
        """Background task to aggregate and report metrics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Aggregate hourly
                
                # Aggregate metrics
                total_requests = sum(m.total_requests for m in self.metrics.values())
                total_cost = sum(m.total_cost for m in self.metrics.values())
                average_success_rate = sum(m.success_rate for m in self.metrics.values()) / len(self.metrics) if self.metrics else 0
                
                # Log summary
                self.logger.info(f"Gateway metrics - Requests: {total_requests}, Cost: ${total_cost:.2f}, Success Rate: {average_success_rate:.2%}")
                
                # Store aggregated metrics
                self.redis_client.hset(
                    "gateway_aggregated_metrics",
                    datetime.now().strftime("%Y-%m-%d-%H"),
                    json.dumps({
                        "total_requests": total_requests,
                        "total_cost": total_cost,
                        "average_success_rate": average_success_rate,
                        "gateway_breakdown": {
                            k: {
                                "requests": v.total_requests,
                                "success_rate": v.success_rate,
                                "avg_latency": v.average_latency
                            }
                            for k, v in self.metrics.items()
                        }
                    })
                )
                
            except Exception as e:
                self.logger.error(f"Metrics aggregation error: {str(e)}")
    
    def get_gateway_status(self) -> Dict[str, Any]:
        """Get current gateway status and metrics"""
        return {
            "configured_routes": {
                category: len(routes) for category, routes in self.routes.items()
            },
            "total_routes": sum(len(routes) for routes in self.routes.values()),
            "active_gateways": list(set(
                route.gateway_type.value 
                for routes in self.routes.values() 
                for route in routes
            )),
            "metrics_summary": {
                key: {
                    "success_rate": metrics.success_rate,
                    "average_latency": metrics.average_latency,
                    "total_requests": metrics.total_requests,
                    "total_cost": metrics.total_cost
                }
                for key, metrics in self.metrics.items()
            }
        }

# Global orchestrator instance
_orchestrator: Optional[UnifiedGatewayOrchestrator] = None

def get_gateway_orchestrator() -> UnifiedGatewayOrchestrator:
    """Get or create the gateway orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = UnifiedGatewayOrchestrator()
    return _orchestrator 