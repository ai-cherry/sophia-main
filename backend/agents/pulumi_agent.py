"""Pulumi Agent for Sophia AI
Handles all Pulumi IaC operations with natural language support
"""

import json
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List

from backend.agents.core.agent_router import AgentCapability, AgentRegistration
from backend.agents.core.base_agent import AgentConfig, BaseAgent
from backend.core.context_manager import context_manager
from backend.integrations.pulumi_mcp_client import pulumi_mcp_client

logger = logging.getLogger(__name__)


class PulumiAgent(BaseAgent):
    """Pulumi agent with natural language support
    - Stack management
    - Resource operations
    - Context-aware commands
    - AI-Copilot error handling
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="pulumi_agent",
            agent_type="infrastructure",
            specialization="Pulumi Infrastructure as Code",
        )
        super().__init__(config)
        self.mcp_client = pulumi_mcp_client
        self._validate_environment()

    def _validate_environment(self):
        """Validate Pulumi environment"""
        try:
            # Check if Pulumi CLI is available
            result = subprocess.run(
                ["pulumi", "version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info(f"Pulumi CLI available: {result.stdout.strip()}")
            else:
                logger.warning("Pulumi CLI not found")
        except Exception as e:
            logger.error(f"Failed to validate Pulumi environment: {e}")

    async def execute(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Pulumi command based on natural language input"""
        command_lower = command.lower()
        session_id = context.get("session_id", "default")
        user_context = {
            "user_id": context.get("user_id", "unknown"),
            "role": context.get("role", "viewer"),
        }

        try:
            # Deploy stack
            if "deploy" in command_lower and "stack" in command_lower:
                return await self._deploy_stack(command, session_id, user_context)

            # List resources
            elif (
                any(keyword in command_lower for keyword in ["list", "show", "get"])
                and "resource" in command_lower
            ):
                return await self._list_resources(command, session_id, user_context)

            # Stack operations
            elif "stack" in command_lower:
                if "create" in command_lower:
                    return await self._create_stack(command, session_id)
                elif "select" in command_lower or "switch" in command_lower:
                    return await self._select_stack(command, session_id)
                elif "output" in command_lower:
                    return await self._get_stack_outputs(
                        command, session_id, user_context
                    )
                else:
                    return await self._list_stacks(session_id)

            # Preview changes
            elif "preview" in command_lower:
                return await self._preview_changes(command, session_id, user_context)

            # Refresh state
            elif "refresh" in command_lower:
                return await self._refresh_stack(command, session_id, user_context)

            # Update configuration
            elif "config" in command_lower or "set" in command_lower:
                return await self._update_config(command, session_id)

            # Generate code
            elif "generate" in command_lower or "create" in command_lower:
                return await self._generate_code(command, session_id)

            # Fix errors with AI-Copilot
            elif "fix" in command_lower or "error" in command_lower:
                return await self._fix_with_copilot(command, session_id)

            # Default: try to parse as direct Pulumi command
            else:
                return await self._execute_direct_command(command, session_id)

        except Exception as e:
            logger.error(f"Error executing Pulumi command: {e}")
            return {"status": "error", "message": str(e)}

    async def _deploy_stack(
        self, command: str, session_id: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy a Pulumi stack"""
        # Extract stack name from command
        stack_name = await self._get_stack_from_command_or_context(command, session_id)

        # Check if preview only
        preview_only = "preview" in command.lower()

        # Use MCP client for deployment
        result = await self.mcp_client.deploy_stack(
            stack=stack_name, user_context=user_context, preview_only=preview_only
        )

        # Update context with deployment info
        if result["status"] == "success":
            await context_manager.update_pulumi_context(
                session_id,
                stack=stack_name,
                last_deployment=datetime.utcnow().isoformat(),
            )

        return result

    async def _list_resources(
        self, command: str, session_id: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List resources in a stack"""
        stack_name = await self._get_stack_from_command_or_context(command, session_id)

        # Use MCP client to list resources
        result = await self.mcp_client.list_resources(
            stack=stack_name, user_context=user_context
        )

        return result

    async def _create_stack(self, command: str, session_id: str) -> Dict[str, Any]:
        """Create a new Pulumi stack"""
        # Extract stack name from command
        parts = command.split()
        stack_name = None

        for i, part in enumerate(parts):
            if part in ["stack", "called", "named"]:
                if i + 1 < len(parts):
                    stack_name = parts[i + 1]
                    break

        if not stack_name:
            return {"status": "error", "message": "Please specify a stack name"}

        try:
            # Create stack using CLI
            result = subprocess.run(
                ["pulumi", "stack", "init", stack_name], capture_output=True, text=True
            )

            if result.returncode == 0:
                # Update context
                await context_manager.update_pulumi_context(
                    session_id, stack=stack_name
                )

                return {
                    "status": "success",
                    "message": f"Stack '{stack_name}' created",
                    "stack": stack_name,
                    "output": result.stdout,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to create stack: {result.stderr}",
                }

        except Exception as e:
            return {"status": "error", "message": f"Failed to create stack: {str(e)}"}

    async def _select_stack(self, command: str, session_id: str) -> Dict[str, Any]:
        """Select/switch to a different stack"""
        # Extract stack name
        stack_name = command.split()[-1]

        try:
            # Select stack using CLI
            result = subprocess.run(
                ["pulumi", "stack", "select", stack_name],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Update context
                await context_manager.update_pulumi_context(
                    session_id, stack=stack_name
                )

                return {
                    "status": "success",
                    "message": f"Switched to stack '{stack_name}'",
                    "stack": stack_name,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to select stack: {result.stderr}",
                }

        except Exception as e:
            return {"status": "error", "message": f"Failed to select stack: {str(e)}"}

    async def _get_stack_outputs(
        self, command: str, session_id: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get stack outputs"""
        stack_name = await self._get_stack_from_command_or_context(command, session_id)

        # Use MCP client to get outputs
        result = await self.mcp_client.get_stack_outputs(
            stack=stack_name, user_context=user_context
        )

        return result

    async def _list_stacks(self, session_id: str) -> Dict[str, Any]:
        """List all stacks"""
        try:
            result = subprocess.run(
                ["pulumi", "stack", "ls", "--json"], capture_output=True, text=True
            )

            if result.returncode == 0:
                stacks = json.loads(result.stdout)

                # Get current stack from context
                session_context = await context_manager.get_full_context(session_id)
                current_stack = session_context.get("pulumi", {}).get("current_stack")

                return {
                    "status": "success",
                    "stacks": stacks,
                    "current_stack": current_stack,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to list stacks: {result.stderr}",
                }

        except Exception as e:
            return {"status": "error", "message": f"Failed to list stacks: {str(e)}"}

    async def _preview_changes(
        self, command: str, session_id: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Preview stack changes"""
        stack_name = await self._get_stack_from_command_or_context(command, session_id)

        # Use MCP client with preview_only=True
        result = await self.mcp_client.deploy_stack(
            stack=stack_name, user_context=user_context, preview_only=True
        )

        return result

    async def _refresh_stack(
        self, command: str, session_id: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refresh stack state"""
        stack_name = await self._get_stack_from_command_or_context(command, session_id)

        # Use MCP client to refresh
        result = await self.mcp_client.refresh_stack(
            stack=stack_name, user_context=user_context
        )

        return result

    async def _update_config(self, command: str, session_id: str) -> Dict[str, Any]:
        """Update stack configuration"""
        # Parse config command
        # Example: "set aws:region to us-west-2"
        if "set" in command and "to" in command:
            parts = command.split("to")
            if len(parts) == 2:
                config_key = parts[0].replace("set", "").strip()
                config_value = parts[1].strip()

                try:
                    # Set config using CLI
                    result = subprocess.run(
                        ["pulumi", "config", "set", config_key, config_value],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        return {
                            "status": "success",
                            "message": f"Configuration updated: {config_key} = {config_value}",
                            "key": config_key,
                            "value": config_value,
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to update config: {result.stderr}",
                        }

                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to update config: {str(e)}",
                    }

        return {
            "status": "error",
            "message": "Invalid config command format. Use: 'set [key] to [value]'",
        }

    async def _generate_code(self, command: str, session_id: str) -> Dict[str, Any]:
        """Generate Pulumi code based on description"""
        # Extract what to generate
        description = command.replace("generate", "").replace("create", "").strip()

        # Basic code generation examples
        code_templates = {
            "s3 bucket": """import pulumi
import pulumi_aws as aws

# Create an S3 bucket
bucket = aws.s3.Bucket("my-bucket",
    acl="private",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True
    )
)

pulumi.export("bucket_name", bucket.id)""",
            "ec2 instance": """import pulumi
import pulumi_aws as aws

# Create an EC2 instance
instance = aws.ec2.Instance("my-instance",
    instance_type="t3.micro",
    ami="ami-0c55b159cbfafe1f0",  # Update with your AMI
    tags={
        "Name": "My Instance"
    }
)

pulumi.export("instance_id", instance.id)
pulumi.export("public_ip", instance.public_ip)""",
            "kubernetes deployment": """import pulumi
import pulumi_kubernetes as k8s

# Create a Kubernetes deployment
deployment = k8s.apps.v1.Deployment("my-deployment",
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=3,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={"app": "my-app"}
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={"app": "my-app"}
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[k8s.core.v1.ContainerArgs(
                    name="my-container",
                    image="nginx:latest",
                    ports=[k8s.core.v1.ContainerPortArgs(
                        container_port=80
                    )]
                )]
            )
        )
    )
)

pulumi.export("deployment_name", deployment.metadata.name)""",
        }

        # Find matching template
        generated_code = None
        for key, template in code_templates.items():
            if key in description.lower():
                generated_code = template
                break

        if generated_code:
            return {
                "status": "success",
                "message": f"Generated Pulumi code for {description}",
                "code": generated_code,
                "language": "python",
            }
        else:
            return {
                "status": "info",
                "message": f"Code generation for '{description}' not implemented yet",
                "suggestion": "Try: 's3 bucket', 'ec2 instance', or 'kubernetes deployment'",
            }

    async def _fix_with_copilot(self, command: str, session_id: str) -> Dict[str, Any]:
        """Use AI-Copilot to fix errors"""
        # Extract error message from command or get from context
        session_context = await context_manager.get_full_context(session_id)
        pulumi_context = session_context.get("pulumi", {})

        # Get last error if available
        last_error = pulumi_context.get("last_error", "No recent error found")

        if "error:" in command.lower():
            # Extract error from command
            error_message = command.split("error:")[-1].strip()
        else:
            error_message = last_error

        # Use MCP client to get copilot suggestions
        result = await self.mcp_client.get_copilot_suggestions(
            error_message=error_message, stack_context=pulumi_context
        )

        return result

    async def _execute_direct_command(
        self, command: str, session_id: str
    ) -> Dict[str, Any]:
        """Execute direct Pulumi command"""
        # Map common commands
        command_map = {
            "up": ["pulumi", "up", "--yes"],
            "destroy": ["pulumi", "destroy", "--yes"],
            "preview": ["pulumi", "preview"],
            "refresh": ["pulumi", "refresh", "--yes"],
        }

        # Check if it's a known command
        for key, cmd in command_map.items():
            if key in command.lower():
                try:
                    # Add --copilot flag for better error messages
                    cmd_with_copilot = cmd + ["--copilot"]

                    result = subprocess.run(
                        cmd_with_copilot, capture_output=True, text=True
                    )

                    if result.returncode == 0:
                        return {
                            "status": "success",
                            "message": "Command executed successfully",
                            "output": result.stdout,
                        }
                    else:
                        # Store error in context for copilot
                        await context_manager.update_pulumi_context(
                            session_id, last_error=result.stderr
                        )

                        return {
                            "status": "error",
                            "message": "Command failed",
                            "error": result.stderr,
                            "suggestion": "Use 'fix error' to get AI-Copilot suggestions",
                        }

                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to execute command: {str(e)}",
                    }

        return {
            "status": "info",
            "message": f"Direct command execution not implemented for: {command}",
            "suggestion": "Try specific commands like 'deploy stack', 'list resources', etc.",
        }

    async def _get_stack_from_command_or_context(
        self, command: str, session_id: str
    ) -> str:
        """Get stack name from command or context"""
        # Try to extract from command
        words = command.split()
        for i, word in enumerate(words):
            if word == "stack" and i + 1 < len(words):
                return words[i + 1]

        # Get from context
        session_context = await context_manager.get_full_context(session_id)
        stack = session_context.get("pulumi", {}).get("current_stack")

        if not stack:
            # Default to dev stack
            stack = "dev"

        return stack

    async def process_task(self, task) -> Dict[str, Any]:
        """Process task - required by BaseAgent"""
        # Delegate to execute method
        return await self.execute(
            task.task_data.get("command", ""), task.task_data.get("context", {})
        )

    async def get_capabilities(self) -> List[str]:
        """Get list of capabilities"""
        return [
            "deploy stack",
            "preview changes",
            "list resources",
            "create/select stack",
            "get stack outputs",
            "update configuration",
            "generate code",
            "fix errors with AI-Copilot",
            "refresh state",
        ]


# Create and register the Pulumi agent
pulumi_agent = PulumiAgent()

# Registration for the agent router
pulumi_registration = AgentRegistration(
    name="pulumi_agent",
    capabilities=[AgentCapability.PULUMI],
    handler=pulumi_agent.execute,
    description="Handles Pulumi infrastructure as code operations",
    context_requirements=["session_id", "user_id", "role"],
)
