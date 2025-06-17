"""
Sophia AI - Base Agent Class
Foundation for all specialized agents in the Pay Ready ecosystem

This module provides the base agent class that all specialized agents inherit from,
ensuring consistent communication protocols and integration patterns.
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os
import redis
import openai
from .orchestrator import AgentStatus, AgentCapability, Task, TaskStatus

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    agent_id: str
    agent_type: str
    specialization: str
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = 6379
    openai_api_key: str = None
    performance_target: float = 0.90
    max_concurrent_tasks: int = 5

class BaseAgent(ABC):
    """Base class for all Sophia AI agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = config.agent_id
        self.agent_type = config.agent_type
        self.specialization = config.specialization
        self.status = AgentStatus.INACTIVE
        self.current_tasks: Dict[str, Task] = {}
        self.performance_metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_duration': 0.0,
            'success_rate': 1.0
        }
        
        # Redis connection for communication
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            decode_responses=True
        )
        
        # OpenAI client if needed
        if config.openai_api_key:
            openai.api_key = config.openai_api_key
        
        self.is_running = False
        
    @abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        pass
    
    @abstractmethod
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Process assigned task and return result"""
        pass
    
    async def start(self):
        """Start the agent and register with orchestrator"""
        try:
            self.is_running = True
            self.status = AgentStatus.ACTIVE
            
            # Register with orchestrator
            await self._register_with_orchestrator()
            
            # Start task processing loop
            asyncio.create_task(self._task_processing_loop())
            
            # Start health reporting
            asyncio.create_task(self._health_reporting_loop())
            
            logger.info(f"Agent {self.agent_id} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {str(e)}")
            self.status = AgentStatus.ERROR
            raise
    
    async def stop(self):
        """Stop the agent gracefully"""
        self.is_running = False
        self.status = AgentStatus.INACTIVE
        
        # Complete any remaining tasks
        for task_id, task in self.current_tasks.items():
            await self._complete_task(task_id, {"error": "Agent shutting down"}, False)
        
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def _register_with_orchestrator(self):
        """Register agent with the orchestrator"""
        try:
            capabilities = await self.get_capabilities()
            
            registration_data = {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'capabilities': [
                    {
                        'name': cap.name,
                        'description': cap.description,
                        'input_types': cap.input_types,
                        'output_types': cap.output_types,
                        'estimated_duration': cap.estimated_duration
                    } for cap in capabilities
                ],
                'endpoint': f"redis://agent:{self.agent_id}",
                'status': self.status.value,
                'performance_score': self.performance_metrics['success_rate'],
                'last_seen': datetime.now().isoformat(),
                'current_load': len(self.current_tasks) / self.config.max_concurrent_tasks,
                'specialization': self.specialization
            }
            
            await self.redis_client.publish(
                'sophia:agents:registration',
                json.dumps(registration_data)
            )
            
            logger.info(f"Registered agent {self.agent_id} with orchestrator")
            
        except Exception as e:
            logger.error(f"Failed to register agent {self.agent_id}: {str(e)}")
            raise
    
    async def _task_processing_loop(self):
        """Main task processing loop"""
        pubsub = self.redis_client.pubsub()
        channel = f"sophia:agent:{self.agent_id}:tasks"
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if not self.is_running:
                    break
                    
                if message['type'] == 'message':
                    try:
                        task_data = json.loads(message['data'])
                        if task_data['type'] == 'task_assignment':
                            await self._handle_task_assignment(task_data['task'])
                    except Exception as e:
                        logger.error(f"Error processing task message: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Task processing loop error: {str(e)}")
        finally:
            await pubsub.unsubscribe(channel)
    
    async def _handle_task_assignment(self, task_data: Dict[str, Any]):
        """Handle new task assignment"""
        try:
            # Check if we can accept more tasks
            if len(self.current_tasks) >= self.config.max_concurrent_tasks:
                logger.warning(f"Agent {self.agent_id} at capacity, rejecting task")
                return
            
            # Create task object
            task = Task(
                task_id=task_data['task_id'],
                task_type=task_data['task_type'],
                agent_id=task_data['agent_id'],
                task_data=task_data['task_data'],
                status=TaskStatus(task_data['status']),
                created_at=datetime.fromisoformat(task_data['created_at']),
                started_at=datetime.fromisoformat(task_data['started_at']) if task_data['started_at'] else None,
                completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data['completed_at'] else None,
                result=task_data['result'],
                error_message=task_data['error_message'],
                priority=task_data['priority']
            )
            
            # Add to current tasks
            self.current_tasks[task.task_id] = task
            
            # Update status to busy if needed
            if len(self.current_tasks) > 0:
                self.status = AgentStatus.BUSY
            
            # Process task asynchronously
            asyncio.create_task(self._execute_task(task))
            
            logger.info(f"Agent {self.agent_id} accepted task {task.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle task assignment: {str(e)}")
    
    async def _execute_task(self, task: Task):
        """Execute task and handle result"""
        start_time = datetime.now()
        
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = start_time
            
            # Process the task
            result = await self.process_task(task)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update performance metrics
            self._update_performance_metrics(duration, True)
            
            # Complete task successfully
            await self._complete_task(task.task_id, result, True)
            
            logger.info(f"Agent {self.agent_id} completed task {task.task_id} in {duration:.2f}s")
            
        except Exception as e:
            # Calculate duration for failed task
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update performance metrics
            self._update_performance_metrics(duration, False)
            
            # Complete task with error
            error_result = {"error": str(e), "duration": duration}
            await self._complete_task(task.task_id, error_result, False)
            
            logger.error(f"Agent {self.agent_id} failed task {task.task_id}: {str(e)}")
    
    async def _complete_task(self, task_id: str, result: Dict[str, Any], success: bool):
        """Complete task and notify orchestrator"""
        try:
            if task_id not in self.current_tasks:
                logger.warning(f"Task {task_id} not found in current tasks")
                return
            
            task = self.current_tasks[task_id]
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = result
            
            # Publish result
            result_message = {
                'type': 'task_result',
                'task_id': task_id,
                'agent_id': self.agent_id,
                'result': result,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.redis_client.publish(
                'sophia:agents:results',
                json.dumps(result_message)
            )
            
            # Remove from current tasks
            del self.current_tasks[task_id]
            
            # Update status if no more tasks
            if len(self.current_tasks) == 0:
                self.status = AgentStatus.ACTIVE
            
            logger.info(f"Agent {self.agent_id} completed task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {str(e)}")
    
    def _update_performance_metrics(self, duration: float, success: bool):
        """Update agent performance metrics"""
        if success:
            self.performance_metrics['tasks_completed'] += 1
        else:
            self.performance_metrics['tasks_failed'] += 1
        
        # Update average duration
        total_tasks = self.performance_metrics['tasks_completed'] + self.performance_metrics['tasks_failed']
        current_avg = self.performance_metrics['average_duration']
        self.performance_metrics['average_duration'] = (
            (current_avg * (total_tasks - 1) + duration) / total_tasks
        )
        
        # Update success rate
        self.performance_metrics['success_rate'] = (
            self.performance_metrics['tasks_completed'] / total_tasks
        )
    
    async def _health_reporting_loop(self):
        """Report health status to orchestrator"""
        while self.is_running:
            try:
                health_data = {
                    'agent_id': self.agent_id,
                    'status': self.status.value,
                    'current_load': len(self.current_tasks) / self.config.max_concurrent_tasks,
                    'performance_metrics': self.performance_metrics,
                    'last_seen': datetime.now().isoformat()
                }
                
                await self.redis_client.publish(
                    'sophia:agents:health',
                    json.dumps(health_data)
                )
                
                await asyncio.sleep(30)  # Report every 30 seconds
                
            except Exception as e:
                logger.error(f"Health reporting error: {str(e)}")
                await asyncio.sleep(30)
    
    async def send_message_to_agent(self, target_agent_id: str, message: Dict[str, Any]):
        """Send message to another agent"""
        try:
            message_data = {
                'from_agent': self.agent_id,
                'to_agent': target_agent_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            channel = f"sophia:agent:{target_agent_id}:messages"
            await self.redis_client.publish(channel, json.dumps(message_data))
            
            logger.info(f"Sent message from {self.agent_id} to {target_agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to {target_agent_id}: {str(e)}")
    
    async def get_business_context(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get business context from context manager"""
        try:
            cache_key = f"sophia:context:business:{entity_type}:{entity_id}"
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get business context: {str(e)}")
            return None
    
    async def store_business_context(self, entity_type: str, entity_id: str, context: Dict[str, Any]):
        """Store business context"""
        try:
            cache_key = f"sophia:context:business:{entity_type}:{entity_id}"
            await self.redis_client.setex(cache_key, 1800, json.dumps(context))  # 30 min TTL
            logger.info(f"Stored business context for {entity_type}:{entity_id}")
        except Exception as e:
            logger.error(f"Failed to store business context: {str(e)}")

class AgentHealthMonitor:
    """Monitor agent health and performance"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.agent_health: Dict[str, Dict[str, Any]] = {}
    
    async def start_monitoring(self):
        """Start health monitoring"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('sophia:agents:health')
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    health_data = json.loads(message['data'])
                    agent_id = health_data['agent_id']
                    self.agent_health[agent_id] = health_data
                    
                    # Check for performance issues
                    await self._check_agent_performance(agent_id, health_data)
                    
                except Exception as e:
                    logger.error(f"Error processing health data: {str(e)}")
    
    async def _check_agent_performance(self, agent_id: str, health_data: Dict[str, Any]):
        """Check agent performance and alert if needed"""
        try:
            metrics = health_data.get('performance_metrics', {})
            success_rate = metrics.get('success_rate', 1.0)
            current_load = health_data.get('current_load', 0.0)
            
            # Alert if success rate drops below 80%
            if success_rate < 0.8:
                logger.warning(f"Agent {agent_id} success rate low: {success_rate:.2%}")
            
            # Alert if load is consistently high
            if current_load > 0.9:
                logger.warning(f"Agent {agent_id} high load: {current_load:.2%}")
                
        except Exception as e:
            logger.error(f"Error checking agent performance: {str(e)}")
    
    def get_agent_health(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get health data for specific agent"""
        return self.agent_health.get(agent_id)
    
    def get_all_agent_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health data for all agents"""
        return self.agent_health.copy()

# Utility functions for agent development
async def create_agent_response(success: bool, data: Any = None, error: str = None, 
                               metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create standardized agent response"""
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'data': data,
        'error': error,
        'metadata': metadata or {}
    }
    return response

async def validate_task_data(task: Task, required_fields: List[str]) -> bool:
    """Validate that task data contains required fields"""
    try:
        for field in required_fields:
            if field not in task.task_data:
                logger.error(f"Missing required field: {field}")
                return False
        return True
    except Exception as e:
        logger.error(f"Task validation error: {str(e)}")
        return False

# Example specialized agent implementation
class ExampleSpecializedAgent(BaseAgent):
    """Example implementation of a specialized agent"""
    
    async def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="example_processing",
                description="Example task processing capability",
                input_types=["text", "json"],
                output_types=["processed_text", "analysis"],
                estimated_duration=30.0
            )
        ]
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Process example task"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['input_text']):
                raise ValueError("Missing required field: input_text")
            
            input_text = task.task_data['input_text']
            
            # Simulate processing
            await asyncio.sleep(1)
            
            # Create result
            result = {
                'processed_text': input_text.upper(),
                'word_count': len(input_text.split()),
                'processing_time': 1.0
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))

if __name__ == "__main__":
    async def main():
        # Example usage
        config = AgentConfig(
            agent_id="example_agent",
            agent_type="processing",
            specialization="text_processing"
        )
        
        agent = ExampleSpecializedAgent(config)
        await agent.start()
        
        # Keep running
        await asyncio.sleep(60)
        await agent.stop()
    
    asyncio.run(main())

