"""
Sophia AI - Core Agent Architecture Framework
AI Assistant Orchestrator for Pay Ready

This module implements the foundational agent architecture that enables
Sophia to coordinate multiple specialized agents for business intelligence
and automation tasks.
"""

import asyncio
import json
import logging
import redis
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    ACTIVE = "active"
    BUSY = "busy"
    INACTIVE = "inactive"
    ERROR = "error"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentCapability:
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    estimated_duration: float  # seconds

@dataclass
class AgentInfo:
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]
    endpoint: str
    status: AgentStatus
    performance_score: float
    last_seen: datetime
    current_load: float
    specialization: str

@dataclass
class Task:
    task_id: str
    task_type: str
    agent_id: Optional[str]
    task_data: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    priority: int = 1  # 1=low, 5=high

class AgentMessageBus:
    """Redis-based message bus for agent communication"""
    
    def __init__(self, redis_host: str = "150.230.47.71", redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.channels = {
            'agent_coordination': 'sophia:agents:coordination',
            'task_delegation': 'sophia:agents:tasks',
            'results_sharing': 'sophia:agents:results',
            'slack_interface': 'sophia:slack:messages',
            'crm_updates': 'sophia:crm:updates',
            'call_analysis': 'sophia:gong:analysis',
            'health_checks': 'sophia:agents:health'
        }
        self.subscribers = {}
        
    async def publish_task(self, agent_id: str, task: Task):
        """Publish task to specific agent"""
        try:
            channel = f"sophia:agent:{agent_id}:tasks"
            message = {
                'type': 'task_assignment',
                'task': asdict(task),
                'timestamp': datetime.now().isoformat()
            }
            await self.redis_client.publish(channel, json.dumps(message))
            logger.info(f"Published task {task.task_id} to agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to publish task to agent {agent_id}: {str(e)}")
            raise
    
    async def publish_result(self, task_id: str, agent_id: str, result: Dict[str, Any]):
        """Publish task result to results channel"""
        try:
            message = {
                'type': 'task_result',
                'task_id': task_id,
                'agent_id': agent_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            await self.redis_client.publish(self.channels['results_sharing'], json.dumps(message))
            logger.info(f"Published result for task {task_id} from agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to publish result for task {task_id}: {str(e)}")
            raise
    
    async def subscribe_to_channel(self, channel: str, callback: Callable):
        """Subscribe to a specific channel with callback"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Error processing message from {channel}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {str(e)}")
            raise

class AgentRegistry:
    """Central registry for agent discovery and management"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.agents: Dict[str, AgentInfo] = {}
        self.capabilities_index: Dict[str, List[str]] = {}
        
    async def register_agent(self, agent_info: AgentInfo):
        """Register new agent with capabilities"""
        try:
            self.agents[agent_info.agent_id] = agent_info
            
            # Update capabilities index
            for capability in agent_info.capabilities:
                if capability.name not in self.capabilities_index:
                    self.capabilities_index[capability.name] = []
                if agent_info.agent_id not in self.capabilities_index[capability.name]:
                    self.capabilities_index[capability.name].append(agent_info.agent_id)
            
            # Store in Redis for persistence
            agent_data = asdict(agent_info)
            agent_data['last_seen'] = agent_info.last_seen.isoformat()
            await self.redis_client.hset(
                "sophia:agents:registry", 
                agent_info.agent_id, 
                json.dumps(agent_data)
            )
            
            logger.info(f"Registered agent {agent_info.agent_id} with {len(agent_info.capabilities)} capabilities")
        except Exception as e:
            logger.error(f"Failed to register agent {agent_info.agent_id}: {str(e)}")
            raise
    
    async def find_agent_for_task(self, task_type: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Find best agent for specific task"""
        try:
            # Get agents with required capability
            candidates = self.capabilities_index.get(task_type, [])
            
            if not candidates:
                logger.warning(f"No agents found for task type: {task_type}")
                return None
            
            # Filter active agents with low load
            available_agents = []
            for agent_id in candidates:
                agent = self.agents.get(agent_id)
                if (agent and 
                    agent.status == AgentStatus.ACTIVE and 
                    agent.current_load < 0.8):  # Less than 80% load
                    available_agents.append(agent)
            
            if not available_agents:
                logger.warning(f"No available agents for task type: {task_type}")
                return None
            
            # Sort by performance score and load
            best_agent = max(available_agents, 
                           key=lambda a: a.performance_score * (1 - a.current_load))
            
            logger.info(f"Selected agent {best_agent.agent_id} for task {task_type}")
            return best_agent.agent_id
            
        except Exception as e:
            logger.error(f"Failed to find agent for task {task_type}: {str(e)}")
            return None
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, load: float = None):
        """Update agent status and load"""
        try:
            if agent_id in self.agents:
                self.agents[agent_id].status = status
                self.agents[agent_id].last_seen = datetime.now()
                if load is not None:
                    self.agents[agent_id].current_load = load
                
                # Update in Redis
                agent_data = asdict(self.agents[agent_id])
                agent_data['last_seen'] = self.agents[agent_id].last_seen.isoformat()
                await self.redis_client.hset(
                    "sophia:agents:registry", 
                    agent_id, 
                    json.dumps(agent_data)
                )
                
                logger.info(f"Updated agent {agent_id} status to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} status: {str(e)}")
            raise
    
    async def get_all_agents(self) -> List[AgentInfo]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    async def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have specific capability"""
        return self.capabilities_index.get(capability, [])

class ContextManager:
    """Manages shared context and memory across agents"""
    
    def __init__(self, redis_client: redis.Redis, postgres_connection: str):
        self.redis_client = redis_client
        self.postgres_connection = postgres_connection
        
    async def store_conversation_context(self, user_id: str, conversation_id: str, context: Dict[str, Any]):
        """Store conversation context for continuity"""
        try:
            key = f"sophia:context:conversation:{user_id}:{conversation_id}"
            await self.redis_client.setex(key, 3600, json.dumps(context))  # 1 hour TTL
            logger.info(f"Stored conversation context for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to store conversation context: {str(e)}")
            raise
    
    async def get_conversation_context(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation context"""
        try:
            key = f"sophia:context:conversation:{user_id}:{conversation_id}"
            context_data = await self.redis_client.get(key)
            if context_data:
                return json.loads(context_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get conversation context: {str(e)}")
            return None
    
    async def store_business_context(self, entity_type: str, entity_id: str, context: Dict[str, Any]):
        """Store business context (CRM data, call insights, etc.)"""
        try:
            with psycopg2.connect(self.postgres_connection) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        INSERT INTO business_context (entity_type, entity_id, context_data, last_updated)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (entity_type, entity_id) 
                        DO UPDATE SET context_data = %s, last_updated = %s
                    """, (entity_type, entity_id, json.dumps(context), datetime.now(),
                          json.dumps(context), datetime.now()))
                    conn.commit()
            
            # Also cache in Redis for fast access
            cache_key = f"sophia:context:business:{entity_type}:{entity_id}"
            await self.redis_client.setex(cache_key, 1800, json.dumps(context))  # 30 min TTL
            
            logger.info(f"Stored business context for {entity_type}:{entity_id}")
        except Exception as e:
            logger.error(f"Failed to store business context: {str(e)}")
            raise
    
    async def get_business_context(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve business context with Redis cache fallback"""
        try:
            # Try Redis cache first
            cache_key = f"sophia:context:business:{entity_type}:{entity_id}"
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            # Fallback to PostgreSQL
            with psycopg2.connect(self.postgres_connection) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT context_data FROM business_context 
                        WHERE entity_type = %s AND entity_id = %s
                    """, (entity_type, entity_id))
                    result = cur.fetchone()
                    
                    if result:
                        context = result['context_data']
                        # Update cache
                        await self.redis_client.setex(cache_key, 1800, json.dumps(context))
                        return context
            
            return None
        except Exception as e:
            logger.error(f"Failed to get business context: {str(e)}")
            return None
    
    async def update_learning_context(self, interaction_id: str, outcome: Dict[str, Any], feedback: Dict[str, Any]):
        """Update learning context based on outcomes and feedback"""
        try:
            learning_data = {
                'interaction_id': interaction_id,
                'outcome': outcome,
                'feedback': feedback,
                'timestamp': datetime.now().isoformat()
            }
            
            with psycopg2.connect(self.postgres_connection) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO interaction_history 
                        (interaction_id, user_id, channel, query_text, intent, 
                         response_text, user_feedback, outcome_success, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        interaction_id,
                        outcome.get('user_id'),
                        outcome.get('channel'),
                        outcome.get('query_text'),
                        outcome.get('intent'),
                        outcome.get('response_text'),
                        feedback.get('rating'),
                        feedback.get('success', True),
                        datetime.now()
                    ))
                    conn.commit()
            
            logger.info(f"Updated learning context for interaction {interaction_id}")
        except Exception as e:
            logger.error(f"Failed to update learning context: {str(e)}")
            raise

class TaskRouter:
    """Routes tasks to appropriate agents and manages task lifecycle"""
    
    def __init__(self, agent_registry: AgentRegistry, message_bus: AgentMessageBus, 
                 context_manager: ContextManager):
        self.agent_registry = agent_registry
        self.message_bus = message_bus
        self.context_manager = context_manager
        self.active_tasks: Dict[str, Task] = {}
        
    async def submit_task(self, task_type: str, task_data: Dict[str, Any], 
                         priority: int = 1, context: Dict[str, Any] = None) -> str:
        """Submit new task for processing"""
        try:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                task_type=task_type,
                agent_id=None,
                task_data=task_data,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                started_at=None,
                completed_at=None,
                result=None,
                error_message=None,
                priority=priority
            )
            
            # Find appropriate agent
            agent_id = await self.agent_registry.find_agent_for_task(task_type, context)
            if not agent_id:
                task.status = TaskStatus.FAILED
                task.error_message = f"No available agent for task type: {task_type}"
                logger.error(f"Failed to find agent for task {task_id}")
                return task_id
            
            # Assign task to agent
            task.agent_id = agent_id
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            self.active_tasks[task_id] = task
            
            # Send task to agent
            await self.message_bus.publish_task(agent_id, task)
            
            # Update agent status
            await self.agent_registry.update_agent_status(agent_id, AgentStatus.BUSY)
            
            logger.info(f"Submitted task {task_id} to agent {agent_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task: {str(e)}")
            raise
    
    async def complete_task(self, task_id: str, result: Dict[str, Any], success: bool = True):
        """Mark task as completed with result"""
        try:
            if task_id not in self.active_tasks:
                logger.warning(f"Task {task_id} not found in active tasks")
                return
            
            task = self.active_tasks[task_id]
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = result
            
            # Update agent status back to active
            if task.agent_id:
                await self.agent_registry.update_agent_status(task.agent_id, AgentStatus.ACTIVE)
            
            # Publish result
            await self.message_bus.publish_result(task_id, task.agent_id, result)
            
            # Remove from active tasks
            del self.active_tasks[task_id]
            
            logger.info(f"Completed task {task_id} with success: {success}")
            
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {str(e)}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get current task status"""
        return self.active_tasks.get(task_id)
    
    async def get_active_tasks(self) -> List[Task]:
        """Get all active tasks"""
        return list(self.active_tasks.values())

class SophiaOrchestrator:
    """Main orchestrator class that coordinates all agents and systems"""
    
    def __init__(self, redis_host: str = "150.230.47.71", postgres_connection: str = None):
        self.redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)
        self.message_bus = AgentMessageBus(redis_host)
        self.agent_registry = AgentRegistry(self.redis_client)
        self.context_manager = ContextManager(self.redis_client, postgres_connection)
        self.task_router = TaskRouter(self.agent_registry, self.message_bus, self.context_manager)
        self.is_running = False
        
    async def start(self):
        """Start the orchestrator and all subsystems"""
        try:
            self.is_running = True
            logger.info("Starting Sophia AI Orchestrator...")
            
            # Start health check monitoring
            asyncio.create_task(self._health_check_loop())
            
            # Start result processing
            asyncio.create_task(self._process_results())
            
            logger.info("Sophia AI Orchestrator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start orchestrator: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the orchestrator gracefully"""
        self.is_running = False
        logger.info("Sophia AI Orchestrator stopped")
    
    async def submit_task(self, task_type: str, task_data: Dict[str, Any], 
                         priority: int = 1, context: Dict[str, Any] = None) -> str:
        """Submit task to the orchestrator"""
        return await self.task_router.submit_task(task_type, task_data, priority, context)
    
    async def register_agent(self, agent_info: AgentInfo):
        """Register new agent with the orchestrator"""
        await self.agent_registry.register_agent(agent_info)
    
    async def _health_check_loop(self):
        """Periodic health check for all agents"""
        while self.is_running:
            try:
                agents = await self.agent_registry.get_all_agents()
                for agent in agents:
                    # Check if agent hasn't been seen for more than 5 minutes
                    if datetime.now() - agent.last_seen > timedelta(minutes=5):
                        await self.agent_registry.update_agent_status(
                            agent.agent_id, AgentStatus.INACTIVE
                        )
                        logger.warning(f"Agent {agent.agent_id} marked as inactive")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _process_results(self):
        """Process task results from agents"""
        async def result_callback(message):
            try:
                if message['type'] == 'task_result':
                    task_id = message['task_id']
                    result = message['result']
                    await self.task_router.complete_task(task_id, result, True)
            except Exception as e:
                logger.error(f"Error processing result: {str(e)}")
        
        await self.message_bus.subscribe_to_channel(
            self.message_bus.channels['results_sharing'], 
            result_callback
        )

# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Initialize orchestrator
        postgres_conn = "postgresql://sophia_admin:password@150.230.47.71:5432/sophia_payready"
        orchestrator = SophiaOrchestrator(postgres_connection=postgres_conn)
        
        # Start orchestrator
        await orchestrator.start()
        
        # Example agent registration
        call_analysis_capabilities = [
            AgentCapability(
                name="call_analysis",
                description="Analyze sales calls for insights and sentiment",
                input_types=["call_recording", "call_transcript"],
                output_types=["call_insights", "sentiment_analysis"],
                estimated_duration=120.0
            )
        ]
        
        call_agent = AgentInfo(
            agent_id="call_analysis_agent",
            agent_type="analysis",
            capabilities=call_analysis_capabilities,
            endpoint="http://localhost:8001/call-analysis",
            status=AgentStatus.ACTIVE,
            performance_score=0.95,
            last_seen=datetime.now(),
            current_load=0.2,
            specialization="sales_call_analysis"
        )
        
        await orchestrator.register_agent(call_agent)
        
        # Example task submission
        task_id = await orchestrator.submit_task(
            "call_analysis",
            {
                "call_id": "call_123",
                "gong_call_id": "gong_456",
                "transcript": "Sample call transcript..."
            },
            priority=3
        )
        
        print(f"Submitted task: {task_id}")
        
        # Keep running
        await asyncio.sleep(10)
        await orchestrator.stop()
    
    asyncio.run(main())

