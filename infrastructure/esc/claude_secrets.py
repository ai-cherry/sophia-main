"""Claude Secret Management for Sophia AI
Manages Claude/Anthropic API credentials through Pulumi ESC
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from infrastructure.pulumi_esc import PulumiESCManager

logger = logging.getLogger(__name__)


class ClaudeSecretManager:
    """Manages Claude/Anthropic API secrets through Pulumi ESC
    """

    def __init__(self):
        self.service_name = "claude"
        self.esc = PulumiESCManager()
        self.required_fields = ["api_key", "model", "max_tokens", "organization_id"]

        # Get Anthropic API key from environment variable for security
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

    async def setup_claude_secrets(self) -> bool:
        """Setup Claude secrets in Pulumi ESC"""
        # Validate API key is provided
        if not self.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY environment variable is required")
            return False

        try:
            logger.info("Setting up Claude secrets in Pulumi ESC...")

            # Claude configuration
            claude_config = {
                "api_key": self.anthropic_api_key,
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "organization_id": "sophia-ai",
                "api_base_url": "https://api.anthropic.com/v1",
                "anthropic_version": "2023-06-01",
                "rate_limits": {"requests_per_minute": 50, "tokens_per_minute": 40000},
                "features": {
                    "code_generation": True,
                    "code_analysis": True,
                    "code_refactoring": True,
                    "documentation_generation": True,
                    "test_generation": True,
                },
            }

            # Set each configuration value
            for key, value in claude_config.items():
                config_key = f"claude_{key}"
                success = await self.esc.set_configuration(config_key, value)
                if success:
                    logger.info(f"Set Claude configuration: {key}")
                else:
                    logger.error(f"Failed to set Claude configuration: {key}")
                    return False

            # Set the API key as a secret
            secret_success = await self.esc.set_secret(
                "claude_api_key", self.anthropic_api_key
            )
            if secret_success:
                logger.info("Claude API key stored as secret in Pulumi ESC")
            else:
                logger.error("Failed to store Claude API key as secret")
                return False

            logger.info("Claude secrets setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to setup Claude secrets: {e}")
            return False

    async def validate_claude_config(self) -> Dict[str, Any]:
        """Validate Claude configuration in Pulumi ESC"""
        try:
            logger.info("Validating Claude configuration...")

            validation_result = {
                "valid": True,
                "missing_fields": [],
                "config_found": {},
                "errors": [],
            }

            # Check each required field
            for field in self.required_fields:
                config_key = f"claude_{field}"
                try:
                    value = await self.esc.get_configuration(config_key)
                    if value is not None:
                        validation_result["config_found"][field] = "✓"
                        logger.info(f"Claude {field}: Found")
                    else:
                        validation_result["missing_fields"].append(field)
                        validation_result["config_found"][field] = "✗"
                        validation_result["valid"] = False
                        logger.warning(f"Claude {field}: Missing")
                except Exception as e:
                    validation_result["errors"].append(f"Error checking {field}: {e}")
                    validation_result["config_found"][field] = "Error"
                    validation_result["valid"] = False

            # Check API key secret
            try:
                api_key = await self.esc.get_secret("claude_api_key")
                if api_key:
                    validation_result["config_found"]["api_key_secret"] = "✓"
                    logger.info("Claude API key secret: Found")
                else:
                    validation_result["missing_fields"].append("api_key_secret")
                    validation_result["config_found"]["api_key_secret"] = "✗"
                    validation_result["valid"] = False
                    logger.warning("Claude API key secret: Missing")
            except Exception as e:
                validation_result["errors"].append(
                    f"Error checking API key secret: {e}"
                )
                validation_result["config_found"]["api_key_secret"] = "Error"
                validation_result["valid"] = False

            if not validation_result["valid"]:
                validation_result["error"] = "Configuration incomplete"

            return validation_result

        except Exception as e:
            logger.error(f"Failed to validate Claude configuration: {e}")
            return {
                "valid": False,
                "error": str(e),
                "missing_fields": self.required_fields,
                "config_found": {},
                "errors": [str(e)],
            }

    async def get_environment_variables(self) -> Dict[str, str]:
        """Get Claude environment variables from Pulumi ESC"""
        try:
            env_vars = {}

            # Get configuration values
            config_mappings = {
                "ANTHROPIC_API_KEY": "claude_api_key",
                "CLAUDE_MODEL": "claude_model",
                "CLAUDE_MAX_TOKENS": "claude_max_tokens",
                "CLAUDE_ORGANIZATION_ID": "claude_organization_id",
                "CLAUDE_API_BASE_URL": "claude_api_base_url",
                "ANTHROPIC_VERSION": "claude_anthropic_version",
            }

            for env_var, config_key in config_mappings.items():
                try:
                    if env_var == "ANTHROPIC_API_KEY":
                        # Get from secrets
                        value = await self.esc.get_secret("claude_api_key")
                    else:
                        # Get from configuration
                        value = await self.esc.get_configuration(config_key)

                    if value is not None:
                        env_vars[env_var] = str(value)
                        logger.info(f"Retrieved {env_var}")
                    else:
                        logger.warning(f"Could not retrieve {env_var}")

                except Exception as e:
                    logger.error(f"Error retrieving {env_var}: {e}")

            return env_vars

        except Exception as e:
            logger.error(f"Failed to get Claude environment variables: {e}")
            return {}

    async def rotate_api_key(self, new_api_key: str) -> bool:
        """Rotate Claude API key"""
        try:
            logger.info("Rotating Claude API key...")

            # Update the API key secret
            success = await self.esc.set_secret("claude_api_key", new_api_key)
            if success:
                # Update the configuration as well
                config_success = await self.esc.set_configuration(
                    "claude_api_key", new_api_key
                )
                if config_success:
                    logger.info("Claude API key rotated successfully")
                    return True
                else:
                    logger.error("Failed to update Claude API key in configuration")
                    return False
            else:
                logger.error("Failed to update Claude API key secret")
                return False

        except Exception as e:
            logger.error(f"Failed to rotate Claude API key: {e}")
            return False

    async def get_claude_config(self) -> Optional[Dict[str, Any]]:
        """Get complete Claude configuration"""
        try:
            config = {}

            # Get all Claude configuration values
            config_keys = [
                "api_key",
                "model",
                "max_tokens",
                "organization_id",
                "api_base_url",
                "anthropic_version",
                "rate_limits",
                "features",
            ]

            for key in config_keys:
                config_key = f"claude_{key}"
                try:
                    if key == "api_key":
                        # Get from secrets
                        value = await self.esc.get_secret("claude_api_key")
                    else:
                        # Get from configuration
                        value = await self.esc.get_configuration(config_key)

                    if value is not None:
                        config[key] = value

                except Exception as e:
                    logger.warning(f"Could not retrieve Claude {key}: {e}")

            return config if config else None

        except Exception as e:
            logger.error(f"Failed to get Claude configuration: {e}")
            return None

    async def test_claude_connection(self) -> Dict[str, Any]:
        """Test Claude API connection"""
        try:
            # Get configuration
            config = await self.get_claude_config()
            if not config:
                return {
                    "success": False,
                    "error": "Configuration not found",
                    "timestamp": datetime.now().isoformat(),
                }

            # Import Claude integration for testing
            from backend.integrations.claude_integration import claude_integration

            # Initialize and test
            success = await claude_integration.initialize()
            if success:
                # Test with a simple message
                test_response = await claude_integration.send_message("Hello, Claude!")
                if test_response:
                    return {
                        "success": True,
                        "model": test_response.model,
                        "tokens_used": test_response.tokens_used,
                        "response_length": len(test_response.content),
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to get response from Claude",
                        "timestamp": datetime.now().isoformat(),
                    }
            else:
                return {
                    "success": False,
                    "error": "Failed to initialize Claude integration",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to test Claude connection: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def generate_claude_env_file(self, output_path: str = ".env.claude") -> bool:
        """Generate .env file for Claude configuration"""
        try:
            env_vars = await self.get_environment_variables()

            if not env_vars:
                logger.error("No Claude environment variables found")
                return False

            # Generate .env file content
            env_content = "# Claude/Anthropic API Configuration\n"
            env_content += f"# Generated on {datetime.now().isoformat()}\n\n"

            for key, value in env_vars.items():
                env_content += f"{key}={value}\n"

            # Write to file
            with open(output_path, "w") as f:
                f.write(env_content)

            logger.info(f"Claude environment file generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate Claude env file: {e}")
            return False


# Global Claude secret manager instance
claude_secret_manager = ClaudeSecretManager()


async def main():
    """Main function for running Claude secret management operations"""
    print("🔐 Claude Secret Management for Sophia AI")
    print("=" * 50)

    # Setup secrets
    print("\n1. Setting up Claude secrets in Pulumi ESC...")
    setup_success = await claude_secret_manager.setup_claude_secrets()
    if setup_success:
        print("   ✅ Claude secrets setup completed")
    else:
        print("   ❌ Claude secrets setup failed")
        return

    # Validate configuration
    print("\n2. Validating Claude configuration...")
    validation = await claude_secret_manager.validate_claude_config()
    print(f"   📋 Configuration valid: {validation['valid']}")
    if not validation["valid"]:
        print(f"   ⚠️  Missing fields: {validation['missing_fields']}")
        if validation["errors"]:
            print(f"   ❌ Errors: {validation['errors']}")

    # Get environment variables
    print("\n3. Generating environment variables...")
    env_vars = await claude_secret_manager.get_environment_variables()
    print(f"   🌍 Generated {len(env_vars)} environment variables")
    for key in env_vars.keys():
        print(f"      • {key}")

    # Generate .env file
    print("\n4. Generating .env file...")
    env_file_success = await claude_secret_manager.generate_claude_env_file()
    if env_file_success:
        print("   ✅ .env.claude file generated")
    else:
        print("   ❌ Failed to generate .env file")

    # Test connection
    print("\n5. Testing Claude API connection...")
    test_result = await claude_secret_manager.test_claude_connection()
    if test_result["success"]:
        print("   ✅ Claude API connection successful")
        print(f"      • Model: {test_result.get('model', 'N/A')}")
        print(f"      • Tokens used: {test_result.get('tokens_used', 'N/A')}")
    else:
        print(
            f"   ❌ Claude API connection failed: {test_result.get('error', 'Unknown error')}"
        )

    print("\n" + "=" * 50)
    print("✅ Claude Secret Management Complete")
    print("\n📋 Next Steps:")
    print("1. Configure MCP server with Claude integration")
    print("2. Test Claude as Code functionality")
    print("3. Deploy to production environment")


if __name__ == "__main__":
    asyncio.run(main())
