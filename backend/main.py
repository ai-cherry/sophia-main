"""
Pay Ready AI Agent Orchestrator - Main Entry Point
Centralized orchestration for all Pay Ready specialized AI agents
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn

from backend.agents.specialized.pay_ready_agents import (
    PayReadyAgentOrchestrator,
    AgentPriority,
    AgentTask
)
from backend.integrations.enhanced_natural_language_processor import (
    EnhancedNaturalLanguageProcessor
)
from backend.analytics.real_time_business_intelligence import (
    RealTimeBusinessIntelligence
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
agent_orchestrator = None
nlp_processor = None
business_intelligence = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global agent_orchestrator, nlp_processor, business_intelligence
    
    # Initialize configuration
    config = {
        'database_url': os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/payready'),
        'redis_host': os.getenv('REDIS_HOST', 'localhost'),
        'redis_port': int(os.getenv('REDIS_PORT', 6379)),
        'kong_config': {
            'access_token': os.getenv('KONG_ACCESS_TOKEN'),
            'base_url': os.getenv('KONG_BASE_URL', 'https://api.konghq.com')
        },
        'nlp_config': {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'model_name': os.getenv('NLP_MODEL', 'gpt-4')
        },
        'knowledge_config': {
            'pinecone_api_key': os.getenv('PINECONE_API_KEY'),
            'pinecone_environment': os.getenv('PINECONE_ENVIRONMENT'),
            'weaviate_url': os.getenv('WEAVIATE_URL')
        }
    }
    
    # Initialize components
    logger.info("Initializing Pay Ready AI Agent System...")
    
    try:
        # Initialize agent orchestrator
        agent_orchestrator = PayReadyAgentOrchestrator(config)
        
        # Initialize NLP processor
        nlp_processor = EnhancedNaturalLanguageProcessor(config)
        
        # Initialize business intelligence
        business_intelligence = RealTimeBusinessIntelligence(config)
        
        # Start agent processing
        asyncio.create_task(agent_orchestrator.start_processing())
        
        logger.info("Pay Ready AI Agent System initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize Pay Ready AI Agent System: {e}")
        raise
    finally:
        logger.info("Shutting down Pay Ready AI Agent System...")

# Create FastAPI app
app = FastAPI(
    title="Pay Ready AI Agent System",
    description="Centralized AI agent orchestration for Pay Ready B2B operations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class AgentTaskRequest(BaseModel):
    agent_type: str
    task_type: str
    data: Dict[str, Any]
    priority: str = "medium"
    context: Optional[Dict[str, Any]] = None

class MetricsRequest(BaseModel):
    time_period: str = "30_days"
    metric_types: Optional[List[str]] = None

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pay Ready AI Agent System",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check agent orchestrator status
        agent_status = await agent_orchestrator.get_agent_status()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {
                "agent_orchestrator": "operational",
                "nlp_processor": "operational",
                "business_intelligence": "operational"
            },
            "agent_summary": {
                "total_agents": len(agent_status),
                "active_agents": len([a for a in agent_status.values() if a.get('status') == 'active'])
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="System health check failed")

@app.post("/chat")
async def process_chat(request: ChatRequest):
    """Process natural language chat request"""
    try:
        response = await nlp_processor.process_request(
            query=request.message,
            context=request.context
        )
        
        return {
            "success": True,
            "response": response.to_dict()
        }
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/agents/task")
async def submit_agent_task(request: AgentTaskRequest):
    """Submit a task to a specific agent"""
    try:
        # Map priority string to enum
        priority_map = {
            "critical": AgentPriority.CRITICAL,
            "high": AgentPriority.HIGH,
            "medium": AgentPriority.MEDIUM,
            "low": AgentPriority.LOW
        }
        priority = priority_map.get(request.priority.lower(), AgentPriority.MEDIUM)
        
        task_id = await agent_orchestrator.submit_task(
            agent_type=request.agent_type,
            task_type=request.task_type,
            data=request.data,
            priority=priority,
            context=request.context
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task submitted to {request.agent_type} agent"
        }
    except Exception as e:
        logger.error(f"Agent task submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task submission failed: {str(e)}")

@app.get("/agents/task/{task_id}")
async def get_task_result(task_id: str):
    """Get the result of a completed task"""
    try:
        result = await agent_orchestrator.get_task_result(task_id)
        
        if result is None:
            return {
                "success": False,
                "message": "Task not found or still processing"
            }
        
        return {
            "success": True,
            "result": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Task result retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task result retrieval failed: {str(e)}")

@app.get("/agents/status")
async def get_agent_status(agent_type: Optional[str] = None):
    """Get status of agents"""
    try:
        status = await agent_orchestrator.get_agent_status(agent_type)
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Agent status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent status retrieval failed: {str(e)}")

@app.post("/metrics/dashboard")
async def get_business_dashboard(request: MetricsRequest):
    """Get comprehensive business dashboard"""
    try:
        dashboard = await business_intelligence.get_business_dashboard(
            time_period=request.time_period
        )
        
        return {
            "success": True,
            "dashboard": dashboard
        }
    except Exception as e:
        logger.error(f"Dashboard retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")

@app.get("/metrics/executive-report")
async def get_executive_report(time_period: str = "30_days"):
    """Get executive summary report"""
    try:
        report = await business_intelligence.generate_executive_report(time_period)
        
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(f"Executive report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Executive report generation failed: {str(e)}")

@app.get("/nlp/performance")
async def get_nlp_performance():
    """Get NLP processor performance metrics"""
    try:
        metrics = nlp_processor.get_performance_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"NLP performance retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"NLP performance retrieval failed: {str(e)}")

# Background task endpoints
@app.post("/agents/start-health-monitoring")
async def start_client_health_monitoring(background_tasks: BackgroundTasks):
    """Start continuous client health monitoring"""
    try:
        task_id = await agent_orchestrator.submit_task(
            agent_type="client_health",
            task_type="analyze_client_health",
            data={},
            priority=AgentPriority.HIGH
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Client health monitoring started"
        }
    except Exception as e:
        logger.error(f"Health monitoring start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health monitoring start failed: {str(e)}")

@app.post("/agents/analyze-sales-performance")
async def analyze_sales_performance():
    """Trigger sales performance analysis"""
    try:
        task_id = await agent_orchestrator.submit_task(
            agent_type="sales_intelligence",
            task_type="analyze_sales_performance",
            data={},
            priority=AgentPriority.HIGH
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Sales performance analysis started"
        }
    except Exception as e:
        logger.error(f"Sales analysis start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sales analysis start failed: {str(e)}")

@app.post("/agents/market-research")
async def conduct_market_research(research_type: str = "industry_trends"):
    """Conduct market research analysis"""
    try:
        task_id = await agent_orchestrator.submit_task(
            agent_type="market_research",
            task_type=research_type,
            data={},
            priority=AgentPriority.MEDIUM
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Market research ({research_type}) started"
        }
    except Exception as e:
        logger.error(f"Market research start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Market research start failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

