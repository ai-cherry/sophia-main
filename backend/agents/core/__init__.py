"""Core Agent System Initialization
Registers all agents and initializes core components
"""

import asyncio
import logging

from backend.agents.admin_agent import AdminAgent
from backend.agents.brain_agent import BrainAgent
from backend.agents.codebase_awareness_agent import CodebaseAwarenessAgent
from backend.agents.core.agent_router import CentralizedAgentRouter, agent_router

# Import all agents
from backend.agents.docker_agent import DockerAgent, docker_agent, docker_registration
from backend.agents.hubspot_agent import HubSpotAgent
from backend.agents.huggingface_agent import HuggingFaceAgent
from backend.agents.iac_manager_agent import IaCManagerAgent
from backend.agents.intercom_agent import IntercomAgent
from backend.agents.knowledge_agent import KnowledgeAgent
from backend.agents.pulumi_agent import PulumiAgent, pulumi_agent, pulumi_registration
from backend.core.context_manager import context_manager
from backend.integrations.huggingface_integration import huggingface_integration
from backend.integrations.portkey_client import portkey_client
from backend.mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)


async def initialize_agent_system():
    """Initialize the complete agent system
    - Register all agents
    - Initialize context manager
    - Set up integrations
    """
    try:
        # Initialize context manager
        await context_manager.initialize()
        logger.info("Context manager initialized")

        # Set context manager in router
        agent_router.context_manager = context_manager

        # Register all agents
        agent_router.register_agent(docker_registration)
        agent_router.register_agent(pulumi_registration)

        # Log registered agents
        registered = agent_router.get_registered_agents()
        logger.info(f"Registered {len(registered)} agents:")
        for name, info in registered.items():
            logger.info(f"  - {name}: {info['description']}")

        # 3. Initialize Agents
        docker_agent = DockerAgent(AgentConfig(name="docker_agent", version="1.0"))
        pulumi_agent = PulumiAgent(AgentConfig(name="pulumi_agent", version="1.0"))
        knowledge_agent = KnowledgeAgent(
            AgentConfig(name="knowledge_agent", version="1.0"), mcp_client=mcp_client
        )
        huggingface_agent = HuggingFaceAgent(
            AgentConfig(name="huggingface_agent", version="1.0"),
            hf_integration=huggingface_integration,
        )
        brain_agent = BrainAgent(
            AgentConfig(name="brain_agent", version="1.0"),
            portkey_client=portkey_client,
        )
        codebase_awareness_agent = CodebaseAwarenessAgent(
            AgentConfig(name="codebase_awareness_agent", version="1.0"),
            mcp_client=mcp_client,
        )
        admin_agent = AdminAgent(
            AgentConfig(name="admin_agent", version="1.0"), mcp_client=mcp_client
        )
        hubspot_agent = HubSpotAgent(AgentConfig(name="hubspot_agent", version="1.0"))
        intercom_agent = IntercomAgent(
            AgentConfig(name="intercom_agent", version="1.0")
        )
        iac_manager_agent = IaCManagerAgent(
            AgentConfig(name="iac_manager_agent", version="1.0"),
            portkey_client=portkey_client,
        )

        # 4. Register Agents with the Router
        agent_router.register_agent(docker_agent, "docker_agent")
        agent_router.register_agent(pulumi_agent, "pulumi_agent")
        agent_router.register_agent(knowledge_agent, "knowledge_agent")
        agent_router.register_agent(huggingface_agent, "huggingface_agent")
        agent_router.register_agent(brain_agent, "brain_agent")
        agent_router.register_agent(
            codebase_awareness_agent, "codebase_awareness_agent"
        )
        agent_router.register_agent(admin_agent, "admin_agent")
        agent_router.register_agent(hubspot_agent, "hubspot_agent")
        agent_router.register_agent(intercom_agent, "intercom_agent")
        agent_router.register_agent(iac_manager_agent, "iac_manager_agent")

        # Optional: Set a default agent
        agent_router.set_default_agent("brain_agent")

        logger.info("Agent system initialization complete")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize agent system: {e}")
        return False


async def shutdown_agent_system():
    """Gracefully shutdown the agent system"""
    try:
        # Shutdown context manager
        await context_manager.shutdown()

        # Close any open connections in agents
        # (agents should implement cleanup if needed)

        logger.info("Agent system shutdown complete")

    except Exception as e:
        logger.error(f"Error during agent system shutdown: {e}")


# Export key components
__all__ = [
    "agent_router",
    "context_manager",
    "initialize_agent_system",
    "shutdown_agent_system",
    "docker_agent",
    "pulumi_agent",
    "docker_registration",
    "pulumi_registration",
    "DockerAgent",
    "PulumiAgent",
    "KnowledgeAgent",
    "CentralizedAgentRouter",
    "MCPClient",
    "HuggingFaceAgent",
    "BrainAgent",
    "huggingface_integration",
    "portkey_client",
    "AdminAgent",
    "HubSpotAgent",
    "IntercomAgent",
    "IaCManagerAgent",
]
