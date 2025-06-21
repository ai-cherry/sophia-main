"""Pulumi MCP Server Client for Sophia AI
Infrastructure automation via Model Context Protocol
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class PulumiMCPConfig:
    """Configuration for Pulumi MCP Server"""

    base_url: str = "http://pulumi-mcp-server:9001"
    api_token: str = ""
    organization: str = "sophia-ai"
    project: str = "sophia"
    allowed_stacks: List[str] = None
    rbac_enabled: bool = True
    audit_log_path: str = "logs/pulumi-mcp-audit.log"


class PulumiMCPClient:
    """Client for Pulumi MCP Server
    - Infrastructure queries and management
    - RBAC enforcement
    - Audit logging
    - Safe operations only (no destroy without explicit approval)
    """

    def __init__(self, config_path: str = "config/pulumi-mcp.json"):
        self.config = self._load_config(config_path)
        if not self.config.api_token:
            raise ValueError("PULUMI_ACCESS_TOKEN environment variable is required")
        self.session = None
        self.audit_logger = self._setup_audit_logger()

    def _load_config(self, config_path: str) -> PulumiMCPConfig:
        """Load configuration from file or environment"""
        config_data = {
            "base_url": os.getenv("PULUMI_MCP_URL", "http://pulumi-mcp-server:9001"),
            "api_token": os.getenv("PULUMI_ACCESS_TOKEN"),
            "organization": os.getenv("PULUMI_ORG", "sophia-ai"),
            "project": os.getenv("PULUMI_PROJECT", "sophia"),
            "allowed_stacks": ["dev", "staging", "prod"],
            "rbac_enabled": True,
        }

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                file_config = json.load(f)
                config_data.update(file_config)

        return PulumiMCPConfig(**config_data)

    def _setup_audit_logger(self) -> logging.Logger:
        """Setup separate audit logger for infrastructure operations"""
        audit_logger = logging.getLogger("pulumi-mcp-audit")

        try:
            # Ensure logs directory exists
            log_dir = os.path.dirname(self.config.audit_log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            handler = logging.FileHandler(self.config.audit_log_path)
            formatter = logging.Formatter("%(asctime)s - %(message)s")
            handler.setFormatter(formatter)
            audit_logger.addHandler(handler)
            audit_logger.setLevel(logging.INFO)
        except Exception as e:
            # Fallback to console logging if file logging fails
            logger.warning(
                f"Failed to setup file logging for audit: {e}, using console"
            )
            handler = logging.StreamHandler()
            formatter = logging.Formatter("AUDIT: %(asctime)s - %(message)s")
            handler.setFormatter(formatter)
            audit_logger.addHandler(handler)
            audit_logger.setLevel(logging.INFO)

        return audit_logger

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def list_resources(
        self, stack: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List resources in a stack
        Safe read-only operation
        """
        # RBAC check
        if not self._check_permission(user_context, "read", stack):
            return {
                "status": "error",
                "message": f"Permission denied: Cannot read stack {stack}",
            }

        # Audit log
        self._audit_log(user_context, "list_resources", {"stack": stack})

        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json",
            }

            async with self.session.get(
                f"{self.config.base_url}/api/stacks/{self.config.organization}/{self.config.project}/{stack}/resources",
                headers=headers,
            ) as response:
                if response.status == 200:
                    resources = await response.json()
                    return {"status": "success", "resources": resources, "stack": stack}
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"Failed to list resources: {error_text}",
                    }

        except Exception as e:
            logger.error(f"Error listing resources: {e}")
            return {"status": "error", "message": str(e)}

    async def deploy_stack(
        self,
        stack: str,
        user_context: Dict[str, Any],
        preview_only: bool = True,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Deploy or preview a stack deployment
        Requires explicit approval for actual deployment
        """
        # RBAC check
        permission_needed = "preview" if preview_only else "deploy"
        if not self._check_permission(user_context, permission_needed, stack):
            return {
                "status": "error",
                "message": f"Permission denied: Cannot {permission_needed} stack {stack}",
            }

        # Audit log
        self._audit_log(
            user_context,
            f"deploy_stack_{permission_needed}",
            {"stack": stack, "preview_only": preview_only, "parameters": parameters},
        )

        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json",
            }

            request_data = {
                "preview": preview_only,
                "parameters": parameters or {},
                "user": user_context.get("user_id", "unknown"),
            }

            endpoint = "preview" if preview_only else "up"

            async with self.session.post(
                f"{self.config.base_url}/api/stacks/{self.config.organization}/{self.config.project}/{stack}/{endpoint}",
                json=request_data,
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "success",
                        "result": result,
                        "stack": stack,
                        "preview_only": preview_only,
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"Deployment failed: {error_text}",
                    }

        except Exception as e:
            logger.error(f"Error deploying stack: {e}")
            return {"status": "error", "message": str(e)}

    async def get_stack_outputs(
        self, stack: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get stack outputs
        Safe read-only operation
        """
        # RBAC check
        if not self._check_permission(user_context, "read", stack):
            return {
                "status": "error",
                "message": f"Permission denied: Cannot read stack {stack}",
            }

        # Audit log
        self._audit_log(user_context, "get_stack_outputs", {"stack": stack})

        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json",
            }

            async with self.session.get(
                f"{self.config.base_url}/api/stacks/{self.config.organization}/{self.config.project}/{stack}/outputs",
                headers=headers,
            ) as response:
                if response.status == 200:
                    outputs = await response.json()
                    return {"status": "success", "outputs": outputs, "stack": stack}
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"Failed to get outputs: {error_text}",
                    }

        except Exception as e:
            logger.error(f"Error getting stack outputs: {e}")
            return {"status": "error", "message": str(e)}

    async def refresh_stack(
        self, stack: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refresh stack state
        Updates state to match actual cloud resources
        """
        # RBAC check
        if not self._check_permission(user_context, "refresh", stack):
            return {
                "status": "error",
                "message": f"Permission denied: Cannot refresh stack {stack}",
            }

        # Audit log
        self._audit_log(user_context, "refresh_stack", {"stack": stack})

        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{self.config.base_url}/api/stacks/{self.config.organization}/{self.config.project}/{stack}/refresh",
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"status": "success", "result": result, "stack": stack}
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"Refresh failed: {error_text}",
                    }

        except Exception as e:
            logger.error(f"Error refreshing stack: {e}")
            return {"status": "error", "message": str(e)}

    def _check_permission(
        self, user_context: Dict[str, Any], action: str, stack: str
    ) -> bool:
        """Check if user has permission for action on stack
        Implement RBAC logic here
        """
        if not self.config.rbac_enabled:
            return True

        # Check if stack is allowed
        if stack not in self.config.allowed_stacks:
            return False

        # Get user role from context
        user_role = user_context.get("role", "viewer")

        # Define permission matrix
        permissions = {
            "admin": ["read", "preview", "deploy", "refresh", "destroy"],
            "developer": ["read", "preview", "deploy", "refresh"],
            "viewer": ["read"],
        }

        allowed_actions = permissions.get(user_role, [])
        return action in allowed_actions

    def _audit_log(
        self, user_context: Dict[str, Any], action: str, details: Dict[str, Any]
    ):
        """Log infrastructure operations for audit trail"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_context.get("user_id", "unknown"),
            "role": user_context.get("role", "unknown"),
            "action": action,
            "details": details,
        }
        self.audit_logger.info(json.dumps(audit_entry))

    async def get_copilot_suggestions(
        self, error_message: str, stack_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI-Copilot suggestions for errors
        Uses Pulumi's AI-Copilot feature
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json",
            }

            request_data = {
                "error": error_message,
                "context": stack_context,
                "copilot": True,
            }

            async with self.session.post(
                f"{self.config.base_url}/api/copilot/suggestions",
                json=request_data,
                headers=headers,
            ) as response:
                if response.status == 200:
                    suggestions = await response.json()
                    return {"status": "success", "suggestions": suggestions}
                else:
                    return {
                        "status": "error",
                        "message": "Failed to get copilot suggestions",
                    }

        except Exception as e:
            logger.error(f"Error getting copilot suggestions: {e}")
            return {"status": "error", "message": str(e)}


# Global Pulumi MCP client instance
pulumi_mcp_client = PulumiMCPClient()
