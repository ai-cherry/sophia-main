import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Type, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os

from crewai import Crew, Agent, Task, Process
from crewai.agent import CrewAgentConfig
from langchain.tools import BaseTool

from ...core.secret_manager import secret_manager
from ...mcp.resource_orchestrator import SophiaResourceOrchestrator
from .persistent_memory import PersistentMemory

@dataclass
class SophiaAgentConfig:
    """Configuration for a SOPHIA agent"""
    name: str
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = True
    max_iterations: int = 15
    memory: Optional[PersistentMemory] = None
    tools: List[Any] = field(default_factory=list)
    llm_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SophiaTaskConfig:
    """Configuration for a SOPHIA task"""
    description: str
    expected_output: str
    agent_name: str
    context: Optional[str] = None
    async_execution: bool = True
    tools: List[Any] = field(default_factory=list)

class CrewOrchestrator:
    """Orchestrator for CrewAI agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.resource_orchestrator = SophiaResourceOrchestrator()
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.crews: Dict[str, Crew] = {}
        self.initialized = False
        
    async def initialize(self):
        """Initialize the CrewAI orchestrator"""
        if self.initialized:
            return
        
        try:
            # Initialize resource orchestrator
            await self.resource_orchestrator.initialize()
            
            # Initialize OpenAI API key for CrewAI
            api_key = await secret_manager.get_secret("api_key", "openai")
            os.environ["OPENAI_API_KEY"] = api_key
            
            self.initialized = True
            self.logger.info("CrewAI orchestrator initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize CrewAI orchestrator: {e}")
            raise
    
    async def create_agent(self, config: SophiaAgentConfig) -> Agent:
        """Create a CrewAI agent"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get MCP tools if needed
            mcp_tools = []
            if config.tools:
                for tool_name in config.tools:
                    tool = await self.resource_orchestrator.get_tool_by_function(tool_name)
                    if tool:
                        mcp_tools.append(self._convert_mcp_tool_to_langchain(tool))
            
            # Set up LLM config
            llm_config = {
                "model": "gpt-4-turbo",
                "temperature": 0.7,
                **config.llm_config
            }
            
            # Create agent config
            agent_config = CrewAgentConfig(
                verbose=config.verbose,
                allow_delegation=config.allow_delegation,
                max_iterations=config.max_iterations,
                memory=config.memory.get_memory() if config.memory else None,
                tools=mcp_tools
            )
            
            # Create agent
            agent = Agent(
                name=config.name,
                role=config.role,
                goal=config.goal,
                backstory=config.backstory,
                verbose=config.verbose,
                allow_delegation=config.allow_delegation,
                max_iterations=config.max_iterations,
                memory=config.memory.get_memory() if config.memory else None,
                tools=mcp_tools,
                llm_config=llm_config,
                config=agent_config
            )
            
            # Store agent
            self.agents[config.name] = agent
            
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}")
            raise
    
    async def create_task(self, config: SophiaTaskConfig) -> Task:
        """Create a CrewAI task"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get agent
            if config.agent_name not in self.agents:
                raise ValueError(f"Agent '{config.agent_name}' not found")
            
            agent = self.agents[config.agent_name]
            
            # Get MCP tools if needed
            mcp_tools = []
            if config.tools:
                for tool_name in config.tools:
                    tool = await self.resource_orchestrator.get_tool_by_function(tool_name)
                    if tool:
                        mcp_tools.append(self._convert_mcp_tool_to_langchain(tool))
            
            # Create task
            task = Task(
                description=config.description,
                expected_output=config.expected_output,
                agent=agent,
                context=config.context,
                async_execution=config.async_execution,
                tools=mcp_tools
            )
            
            # Generate task ID
            task_id = str(uuid.uuid4())
            
            # Store task
            self.tasks[task_id] = task
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise
    
    async def create_crew(self, name: str, agents: List[str], tasks: List[str], process: Process = Process.sequential, verbose: bool = True) -> Crew:
        """Create a CrewAI crew"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get agents
            crew_agents = []
            for agent_name in agents:
                if agent_name not in self.agents:
                    raise ValueError(f"Agent '{agent_name}' not found")
                crew_agents.append(self.agents[agent_name])
            
            # Get tasks
            crew_tasks = []
            for task_id in tasks:
                if task_id not in self.tasks:
                    raise ValueError(f"Task '{task_id}' not found")
                crew_tasks.append(self.tasks[task_id])
            
            # Create crew
            crew = Crew(
                agents=crew_agents,
                tasks=crew_tasks,
                verbose=verbose,
                process=process
            )
            
            # Store crew
            self.crews[name] = crew
            
            return crew
            
        except Exception as e:
            self.logger.error(f"Failed to create crew: {e}")
            raise
    
    async def run_crew(self, name: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run a CrewAI crew"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get crew
            if name not in self.crews:
                raise ValueError(f"Crew '{name}' not found")
            
            crew = self.crews[name]
            
            # Run crew
            start_time = datetime.now()
            
            if inputs:
                result = crew.kickoff(inputs=inputs)
            else:
                result = crew.kickoff()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Format result
            return {
                "crew_name": name,
                "result": result,
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to run crew: {e}")
            raise
    
    async def run_task(self, task_id: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Run a single CrewAI task"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get task
            if task_id not in self.tasks:
                raise ValueError(f"Task '{task_id}' not found")
            
            task = self.tasks[task_id]
            
            # Run task
            start_time = datetime.now()
            
            if context:
                result = task.execute(context=context)
            else:
                result = task.execute()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Format result
            return {
                "task_id": task_id,
                "result": result,
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to run task: {e}")
            raise
    
    async def create_hierarchical_crew(self, name: str, manager_config: SophiaAgentConfig, worker_configs: List[SophiaAgentConfig], manager_task_config: SophiaTaskConfig, worker_task_configs: List[SophiaTaskConfig]) -> Dict[str, Any]:
        """Create a hierarchical crew with a manager and workers"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create manager agent
            manager_agent = await self.create_agent(manager_config)
            
            # Create worker agents
            worker_agents = []
            for worker_config in worker_configs:
                worker_agent = await self.create_agent(worker_config)
                worker_agents.append(worker_agent)
            
            # Create worker tasks
            worker_tasks = []
            worker_task_ids = []
            for worker_task_config in worker_task_configs:
                worker_task = await self.create_task(worker_task_config)
                worker_tasks.append(worker_task)
                
                # Find task ID
                for task_id, task in self.tasks.items():
                    if task == worker_task:
                        worker_task_ids.append(task_id)
                        break
            
            # Create manager task
            manager_task = await self.create_task(manager_task_config)
            
            # Find manager task ID
            manager_task_id = None
            for task_id, task in self.tasks.items():
                if task == manager_task:
                    manager_task_id = task_id
                    break
            
            # Create crew
            all_agents = [manager_config.name] + [worker_config.name for worker_config in worker_configs]
            all_tasks = [manager_task_id] + worker_task_ids
            
            crew = await self.create_crew(
                name=name,
                agents=all_agents,
                tasks=all_tasks,
                process=Process.hierarchical,
                verbose=True
            )
            
            return {
                "crew_name": name,
                "manager": {
                    "name": manager_config.name,
                    "task_id": manager_task_id
                },
                "workers": [
                    {
                        "name": worker_configs[i].name,
                        "task_id": worker_task_ids[i]
                    }
                    for i in range(len(worker_configs))
                ],
                "status": "created"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create hierarchical crew: {e}")
            raise
    
    def _convert_mcp_tool_to_langchain(self, mcp_tool: Dict[str, Any]) -> BaseTool:
        """Convert an MCP tool to a LangChain tool"""
        # Create a LangChain tool that wraps the MCP tool
        tool_name = mcp_tool["name"]
        tool_description = mcp_tool["description"]
        
        async def _tool_func(*args, **kwargs):
            # Execute MCP tool
            result = await self.resource_orchestrator.execute_tool(tool_name, kwargs)
            return json.dumps(result)
        
        # Create LangChain tool
        from langchain.tools import StructuredTool
        
        # Prepare arguments schema
        args_schema = {}
        for param_name, param_schema in mcp_tool["parameters"].items():
            args_schema[param_name] = (str, param_schema.get("description", ""))
        
        # Create tool
        tool = StructuredTool.from_function(
            func=_tool_func,
            name=tool_name,
            description=tool_description,
            args_schema=args_schema
        )
        
        return tool
