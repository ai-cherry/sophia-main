"""Linear Secret Management for Pulumi ESC
Manages Linear API credentials and configuration
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from infrastructure.pulumi_esc import PulumiESCManager

logger = logging.getLogger(__name__)


class LinearSecretManager:
    """Manages Linear secrets in Pulumi ESC"""

    def __init__(self):
        self.environment_name = "linear"
        self.esc = PulumiESCManager()

    async def setup_linear_secrets(self) -> bool:
        """Setup Linear secrets in Pulumi ESC"""
        try:
            # Check for required environment variables
            required_vars = ["LINEAR_API_TOKEN", "LINEAR_WORKSPACE_ID"]

            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.warning(f"Missing Linear environment variables: {missing_vars}")
                logger.info("Please set the following environment variables:")
                for var in missing_vars:
                    logger.info(f"  export {var}=your_value_here")
                return False

            # Store Linear credentials in Pulumi ESC
            secrets = {
                "api_token": os.getenv("LINEAR_API_TOKEN"),
                "workspace_id": os.getenv("LINEAR_WORKSPACE_ID"),
                "mcp_server_url": "https://mcp.linear.app/sse",
                "api_base_url": "https://api.linear.app/graphql",
            }

            # Optional OAuth credentials
            if os.getenv("LINEAR_OAUTH_CLIENT_ID"):
                secrets["oauth_client_id"] = os.getenv("LINEAR_OAUTH_CLIENT_ID")

            if os.getenv("LINEAR_OAUTH_CLIENT_SECRET"):
                secrets["oauth_client_secret"] = os.getenv("LINEAR_OAUTH_CLIENT_SECRET")

            # Store each secret
            for key, value in secrets.items():
                if value:
                    await self.esc.set_secret(f"linear.{key}", value)
                    logger.info(f"Stored Linear secret: {key}")

            logger.info("Linear secrets setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Linear secrets: {e}")
            return False

    async def get_linear_config(self) -> Optional[Dict[str, Any]]:
        """Get Linear configuration from Pulumi ESC"""
        try:
            config = await self.esc.get_configuration("linear")

            if not config:
                logger.warning("Linear configuration not found in Pulumi ESC")
                return None

            # Validate required fields
            required_fields = ["api_token", "workspace_id"]
            missing_fields = [field for field in required_fields if field not in config]

            if missing_fields:
                logger.error(f"Missing required Linear config fields: {missing_fields}")
                return None

            logger.info("Retrieved Linear configuration from Pulumi ESC")
            return config

        except Exception as e:
            logger.error(f"Failed to get Linear configuration: {e}")
            return None

    async def update_linear_secret(self, key: str, value: str) -> bool:
        """Update a specific Linear secret"""
        try:
            await self.esc.set_secret(f"linear.{key}", value)
            logger.info(f"Updated Linear secret: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Linear secret {key}: {e}")
            return False

    async def rotate_linear_token(self, new_token: str) -> bool:
        """Rotate Linear API token"""
        try:
            # Update token in Pulumi ESC
            success = await self.update_linear_secret("api_token", new_token)

            if success:
                logger.info("Linear API token rotated successfully")
                return True
            else:
                logger.error("Failed to rotate Linear API token")
                return False

        except Exception as e:
            logger.error(f"Error rotating Linear API token: {e}")
            return False

    async def validate_linear_config(self) -> Dict[str, Any]:
        """Validate Linear configuration"""
        try:
            config = await self.get_linear_config()

            if not config:
                return {
                    "valid": False,
                    "error": "Configuration not found",
                    "missing_fields": ["api_token", "workspace_id"],
                }

            # Check required fields
            required_fields = ["api_token", "workspace_id"]
            missing_fields = [field for field in required_fields if field not in config]

            if missing_fields:
                return {
                    "valid": False,
                    "error": "Missing required fields",
                    "missing_fields": missing_fields,
                }

            # Check token format (basic validation)
            api_token = config.get("api_token", "")
            if not api_token.startswith("lin_api_"):
                return {
                    "valid": False,
                    "error": "Invalid API token format",
                    "details": "Linear API tokens should start with 'lin_api_'",
                }

            return {
                "valid": True,
                "workspace_id": config.get("workspace_id"),
                "mcp_server_url": config.get("mcp_server_url"),
                "api_base_url": config.get("api_base_url"),
                "has_oauth": bool(config.get("oauth_client_id")),
            }

        except Exception as e:
            logger.error(f"Error validating Linear configuration: {e}")
            return {"valid": False, "error": str(e)}

    async def get_environment_variables(self) -> Dict[str, str]:
        """Get Linear environment variables for local development"""
        try:
            config = await self.get_linear_config()

            if not config:
                return {}

            env_vars = {
                "LINEAR_API_TOKEN": config.get("api_token", ""),
                "LINEAR_WORKSPACE_ID": config.get("workspace_id", ""),
                "LINEAR_MCP_SERVER_URL": config.get(
                    "mcp_server_url", "https://mcp.linear.app/sse"
                ),
                "LINEAR_API_BASE_URL": config.get(
                    "api_base_url", "https://api.linear.app/graphql"
                ),
            }

            # Add OAuth variables if available
            if config.get("oauth_client_id"):
                env_vars["LINEAR_OAUTH_CLIENT_ID"] = config["oauth_client_id"]

            if config.get("oauth_client_secret"):
                env_vars["LINEAR_OAUTH_CLIENT_SECRET"] = config["oauth_client_secret"]

            return env_vars

        except Exception as e:
            logger.error(f"Error getting Linear environment variables: {e}")
            return {}


# Global Linear secret manager instance
linear_secret_manager = LinearSecretManager()


# Convenience functions
async def setup_linear_secrets() -> bool:
    """Setup Linear secrets in Pulumi ESC"""
    return await linear_secret_manager.setup_linear_secrets()


async def get_linear_config() -> Optional[Dict[str, Any]]:
    """Get Linear configuration from Pulumi ESC"""
    return await linear_secret_manager.get_linear_config()


async def validate_linear_config() -> Dict[str, Any]:
    """Validate Linear configuration"""
    return await linear_secret_manager.validate_linear_config()


async def rotate_linear_token(new_token: str) -> bool:
    """Rotate Linear API token"""
    return await linear_secret_manager.rotate_linear_token(new_token)


async def main():
    """Main entry point for Linear secret management"""
    print("Setting up Linear secrets...")

    success = await setup_linear_secrets()
    if success:
        print("✅ Linear secrets setup completed")

        # Validate configuration
        validation = await validate_linear_config()
        if validation["valid"]:
            print("✅ Linear configuration is valid")
            print(f"   Workspace ID: {validation['workspace_id']}")
            print(f"   MCP Server: {validation['mcp_server_url']}")
            print(f"   Has OAuth: {validation['has_oauth']}")
        else:
            print(f"❌ Linear configuration validation failed: {validation['error']}")
    else:
        print("❌ Failed to setup Linear secrets")


if __name__ == "__main__":
    asyncio.run(main())
