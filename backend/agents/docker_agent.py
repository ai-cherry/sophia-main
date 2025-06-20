"""Docker Agent for Sophia AI
Handles all Docker operations with natural language support
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import docker

from backend.agents.core.agent_router import AgentCapability, AgentRegistration
from backend.agents.core.base_agent import AgentConfig, BaseAgent
from backend.agents.core.orchestrator import AgentCapability as OrchCapability
from backend.core.context_manager import context_manager

logger = logging.getLogger(__name__)


class DockerAgent(BaseAgent):
    """Docker agent with natural language support
    - Container management
    - Image operations
    - Context-aware commands
    - Dev container support
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="docker_agent",
            agent_type="infrastructure",
            specialization="Docker Operations",
        )
        super().__init__(config)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    async def execute(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Docker command based on natural language input"""
        if not self.client:
            return {"status": "error", "message": "Docker client not initialized"}

        command_lower = command.lower()
        session_id = context.get("session_id", "default")

        try:
            # List containers
            if (
                any(keyword in command_lower for keyword in ["list", "show", "get"])
                and "container" in command_lower
            ):
                return await self._list_containers(session_id)

            # Run command in container
            elif "run" in command_lower and "in" in command_lower:
                return await self._run_in_container(command, session_id)

            # Build image
            elif "build" in command_lower and (
                "image" in command_lower or "docker" in command_lower
            ):
                return await self._build_image(command, session_id)

            # Stop container
            elif "stop" in command_lower and "container" in command_lower:
                return await self._stop_container(command, session_id)

            # Start container
            elif "start" in command_lower and "container" in command_lower:
                return await self._start_container(command, session_id)

            # Switch context
            elif "switch" in command_lower or "use" in command_lower:
                return await self._switch_context(command, session_id)

            # Deploy with docker-compose
            elif "deploy" in command_lower or "compose" in command_lower:
                return await self._docker_compose_operation(command, session_id)

            # Dev container operations
            elif "dev" in command_lower and "container" in command_lower:
                return await self._dev_container_operation(command, session_id)

            # Default: try to parse as direct Docker command
            else:
                return await self._execute_direct_command(command, session_id)

        except Exception as e:
            logger.error(f"Error executing Docker command: {e}")
            return {"status": "error", "message": str(e)}

    async def _list_containers(self, session_id: str) -> Dict[str, Any]:
        """List all containers"""
        try:
            containers = self.client.containers.list(all=True)
            container_info = []

            for container in containers:
                info = {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": (
                        container.image.tags[0] if container.image.tags else "unknown"
                    ),
                    "created": container.attrs["Created"],
                }
                container_info.append(info)

            return {
                "status": "success",
                "containers": container_info,
                "count": len(container_info),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list containers: {str(e)}",
            }

    async def _run_in_container(self, command: str, session_id: str) -> Dict[str, Any]:
        """Run command in a container"""
        # Parse command to extract container name and command to run
        parts = command.split("in")
        if len(parts) < 2:
            return {
                "status": "error",
                "message": "Invalid command format. Use: 'run [command] in [container]'",
            }

        cmd_to_run = parts[0].replace("run", "").strip()
        container_name = parts[1].strip()

        # Check context for current container
        session_context = await context_manager.get_full_context(session_id)
        docker_context = session_context.get("docker", {})

        # Use context container if not specified
        if not container_name or container_name == "current":
            container_name = docker_context.get("current_container")
            if not container_name:
                return {
                    "status": "error",
                    "message": "No current container in context. Please specify container name.",
                }

        try:
            container = self.client.containers.get(container_name)
            result = container.exec_run(cmd_to_run)

            # Update context
            await context_manager.update_docker_context(
                session_id, container=container_name, last_command=cmd_to_run
            )

            return {
                "status": "success",
                "container": container_name,
                "command": cmd_to_run,
                "output": result.output.decode("utf-8") if result.output else "",
                "exit_code": result.exit_code,
            }

        except docker.errors.NotFound:
            return {
                "status": "error",
                "message": f"Container '{container_name}' not found",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to execute command: {str(e)}",
            }

    async def _build_image(self, command: str, session_id: str) -> Dict[str, Any]:
        """Build Docker image"""
        # Extract image name from command
        image_name = "my-app"  # Default
        if "as" in command:
            parts = command.split("as")
            image_name = parts[1].strip()
        elif "-t" in command:
            parts = command.split("-t")
            image_name = parts[1].strip().split()[0]

        # Get build context (default to current directory)
        build_path = "."

        try:
            # Start build
            image, build_logs = self.client.images.build(
                path=build_path, tag=image_name, rm=True
            )

            # Collect build logs
            logs = []
            for log in build_logs:
                if "stream" in log:
                    logs.append(log["stream"].strip())

            # Update context
            await context_manager.update_docker_context(
                session_id, image=image_name, last_build=datetime.utcnow().isoformat()
            )

            return {
                "status": "success",
                "image": image_name,
                "id": image.short_id,
                "logs": logs[-10:],  # Last 10 log lines
            }

        except Exception as e:
            return {"status": "error", "message": f"Failed to build image: {str(e)}"}

    async def _stop_container(self, command: str, session_id: str) -> Dict[str, Any]:
        """Stop a container"""
        # Extract container name
        container_name = command.replace("stop", "").replace("container", "").strip()

        # Check context if not specified
        if not container_name:
            session_context = await context_manager.get_full_context(session_id)
            container_name = session_context.get("docker", {}).get("current_container")
            if not container_name:
                return {
                    "status": "error",
                    "message": "No container specified and no current container in context",
                }

        try:
            container = self.client.containers.get(container_name)
            container.stop()

            return {
                "status": "success",
                "message": f"Container '{container_name}' stopped",
                "container": container_name,
            }

        except docker.errors.NotFound:
            return {
                "status": "error",
                "message": f"Container '{container_name}' not found",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to stop container: {str(e)}"}

    async def _start_container(self, command: str, session_id: str) -> Dict[str, Any]:
        """Start a container"""
        # Extract container name
        container_name = command.replace("start", "").replace("container", "").strip()

        # Check context if not specified
        if not container_name:
            session_context = await context_manager.get_full_context(session_id)
            container_name = session_context.get("docker", {}).get("current_container")
            if not container_name:
                return {
                    "status": "error",
                    "message": "No container specified and no current container in context",
                }

        try:
            container = self.client.containers.get(container_name)
            container.start()

            # Update context
            await context_manager.update_docker_context(
                session_id, container=container_name
            )

            return {
                "status": "success",
                "message": f"Container '{container_name}' started",
                "container": container_name,
            }

        except docker.errors.NotFound:
            return {
                "status": "error",
                "message": f"Container '{container_name}' not found",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to start container: {str(e)}",
            }

    async def _switch_context(self, command: str, session_id: str) -> Dict[str, Any]:
        """Switch Docker context"""
        # Extract target from command
        target = command.replace("switch to", "").replace("use", "").strip()

        if "container" in target:
            container_name = target.replace("container", "").strip()

            # Verify container exists
            try:
                container = self.client.containers.get(container_name)

                # Update context
                await context_manager.update_docker_context(
                    session_id, container=container_name
                )

                return {
                    "status": "success",
                    "message": f"Switched to container '{container_name}'",
                    "container": container_name,
                    "status": container.status,
                }

            except docker.errors.NotFound:
                return {
                    "status": "error",
                    "message": f"Container '{container_name}' not found",
                }

        return {"status": "error", "message": "Unknown context switch target"}

    async def _docker_compose_operation(
        self, command: str, session_id: str
    ) -> Dict[str, Any]:
        """Handle docker-compose operations"""
        # This is a simplified implementation
        # In production, you'd use docker-compose Python API

        if "up" in command or "deploy" in command:
            operation = "up -d"
        elif "down" in command:
            operation = "down"
        else:
            operation = "ps"

        return {
            "status": "success",
            "message": f"Docker Compose operation '{operation}' would be executed",
            "note": "Full docker-compose integration pending",
        }

    async def _dev_container_operation(
        self, command: str, session_id: str
    ) -> Dict[str, Any]:
        """Handle dev container operations"""
        import os

        # Check for devcontainer.json
        devcontainer_path = ".devcontainer/devcontainer.json"

        if not os.path.exists(devcontainer_path):
            return {
                "status": "error",
                "message": "No devcontainer.json found in .devcontainer/",
            }

        # Read devcontainer config
        with open(devcontainer_path, "r") as f:
            devcontainer_config = json.load(f)

        if "open" in command or "start" in command:
            # Start dev container
            image = devcontainer_config.get(
                "image", "mcr.microsoft.com/vscode/devcontainers/base"
            )
            name = devcontainer_config.get("name", "dev-container")

            try:
                # Check if container already exists
                try:
                    container = self.client.containers.get(name)
                    container.start()
                    action = "started"
                except docker.errors.NotFound:
                    # Create new container
                    container = self.client.containers.run(
                        image,
                        name=name,
                        detach=True,
                        volumes={os.getcwd(): {"bind": "/workspace", "mode": "rw"}},
                        environment=devcontainer_config.get("containerEnv", {}),
                    )
                    action = "created"

                # Update context
                await context_manager.update_docker_context(
                    session_id, container=name, dev_container=True
                )

                return {
                    "status": "success",
                    "message": f"Dev container '{name}' {action}",
                    "container": name,
                    "config": devcontainer_config,
                }

            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to start dev container: {str(e)}",
                }

        return {"status": "error", "message": "Unknown dev container operation"}

    async def _execute_direct_command(
        self, command: str, session_id: str
    ) -> Dict[str, Any]:
        """Execute direct Docker command"""
        # This is a fallback for commands not matched by other handlers
        return {
            "status": "info",
            "message": f"Direct Docker command execution not implemented for: {command}",
            "suggestion": "Try using more specific commands like 'list containers', 'run X in Y', etc.",
        }

    async def process_task(self, task) -> Dict[str, Any]:
        """Process task - required by BaseAgent"""
        # Delegate to execute method
        return await self.execute(
            task.task_data.get("command", ""), task.task_data.get("context", {})
        )

    async def get_capabilities(self) -> List[OrchCapability]:
        """Get list of capabilities"""
        return [
            OrchCapability(
                name="list_containers",
                description="List all Docker containers",
                input_types=["text"],
                output_types=["json"],
                estimated_duration=5.0,
            ),
            OrchCapability(
                name="run_command",
                description="Run command in Docker container",
                input_types=["text", "command"],
                output_types=["json", "output"],
                estimated_duration=30.0,
            ),
            OrchCapability(
                name="build_image",
                description="Build Docker image",
                input_types=["text", "dockerfile"],
                output_types=["json", "image"],
                estimated_duration=120.0,
            ),
            OrchCapability(
                name="container_management",
                description="Start/stop Docker containers",
                input_types=["text", "container_name"],
                output_types=["json", "status"],
                estimated_duration=10.0,
            ),
        ]


# Create and register the Docker agent
docker_agent = DockerAgent()

# Registration for the agent router
docker_registration = AgentRegistration(
    name="docker_agent",
    capabilities=[AgentCapability.DOCKER],
    handler=docker_agent.execute,
    description="Handles Docker container and image operations",
    context_requirements=["session_id"],
)
