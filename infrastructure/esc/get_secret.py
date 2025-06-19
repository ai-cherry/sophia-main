#!/usr/bin/env python3
"""
Sophia AI - Get Secret from Pulumi ESC
This script retrieves a secret from Pulumi ESC for use in GitHub Actions workflows.
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

try:
    from backend.core.pulumi_esc import ESCClient
except ImportError:
    # Fallback implementation if the module is not available
    class ESCClient:
        """Fallback implementation of ESCClient"""
        
        def __init__(self, organization: str, project: str, stack: str):
            self.organization = organization
            self.project = project
            self.stack = stack
            self.initialized = False
        
        async def initialize(self) -> bool:
            """Initialize the client"""
            import subprocess
            import json
            
            try:
                # Check if pulumi is installed
                subprocess.run(["pulumi", "--version"], check=True, capture_output=True)
                
                # Login to Pulumi
                if "PULUMI_ACCESS_TOKEN" in os.environ:
                    subprocess.run(["pulumi", "login"], check=True, capture_output=True)
                
                self.initialized = True
                return True
            except Exception as e:
                logger.error(f"Failed to initialize ESC client: {e}")
                return False
        
        async def get_secret(self, key: str) -> Optional[str]:
            """Get a secret from Pulumi ESC"""
            import subprocess
            import json
            
            if not self.initialized:
                await self.initialize()
            
            try:
                # Format the key for Pulumi ESC
                esc_key = f"{self.organization}/{self.project}/{self.stack}#{key}"
                
                # Get the secret using pulumi CLI
                result = subprocess.run(
                    ["pulumi", "stack", "output", "--show-secrets", key, "--json"],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=os.path.join(project_root, "infrastructure")
                )
                
                # Parse the result
                if result.stdout.strip():
                    return json.loads(result.stdout.strip())
                else:
                    return None
            except Exception as e:
                logger.error(f"Failed to get secret {key}: {e}")
                return None
        
        async def get_configuration(self, key: str) -> Optional[str]:
            """Get a configuration value from Pulumi ESC"""
            import subprocess
            import json
            
            if not self.initialized:
                await self.initialize()
            
            try:
                # Format the key for Pulumi ESC
                esc_key = f"{self.organization}/{self.project}/{self.stack}:{key}"
                
                # Get the configuration using pulumi CLI
                result = subprocess.run(
                    ["pulumi", "config", "get", key, "--json"],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=os.path.join(project_root, "infrastructure")
                )
                
                # Parse the result
                if result.stdout.strip():
                    return json.loads(result.stdout.strip())
                else:
                    return None
            except Exception as e:
                logger.error(f"Failed to get configuration {key}: {e}")
                return None


async def get_secret(
    service_name: str,
    key: str,
    organization: str = "ai-cherry",
    project: str = "sophia",
    environment: str = "production"
) -> Optional[str]:
    """Get a secret from Pulumi ESC"""
    try:
        # Initialize ESC client
        esc_client = ESCClient(
            organization=organization,
            project=project,
            stack=environment
        )
        
        # Get the secret
        secret_key = f"{service_name}_{key}"
        secret_value = await esc_client.get_secret(secret_key)
        
        return secret_value
    except Exception as e:
        logger.error(f"Failed to get secret {service_name}_{key}: {e}")
        return None


async def get_config(
    service_name: str,
    key: str,
    organization: str = "ai-cherry",
    project: str = "sophia",
    environment: str = "production"
) -> Optional[str]:
    """Get a configuration value from Pulumi ESC"""
    try:
        # Initialize ESC client
        esc_client = ESCClient(
            organization=organization,
            project=project,
            stack=environment
        )
        
        # Get the configuration
        config_key = f"{service_name}_{key}"
        config_value = await esc_client.get_configuration(config_key)
        
        return config_value
    except Exception as e:
        logger.error(f"Failed to get configuration {service_name}_{key}: {e}")
        return None


async def get_service_secrets(
    service_name: str,
    organization: str = "ai-cherry",
    project: str = "sophia",
    environment: str = "production"
) -> Dict[str, str]:
    """Get all secrets for a service from Pulumi ESC"""
    try:
        # Initialize ESC client
        esc_client = ESCClient(
            organization=organization,
            project=project,
            stack=environment
        )
        
        # Get the service registry
        registry_path = os.path.join(project_root, "infrastructure", "integration_registry.json")
        if os.path.exists(registry_path):
            with open(registry_path, "r") as f:
                registry = json.load(f)
        else:
            logger.error(f"Service registry not found at {registry_path}")
            return {}
        
        # Get the service configuration
        if service_name not in registry:
            logger.error(f"Service {service_name} not found in registry")
            return {}
        
        service_config = registry[service_name]
        secret_keys = service_config.get("secret_keys", [])
        
        # Get all secrets for the service
        secrets = {}
        for key in secret_keys:
            secret_key = f"{service_name}_{key}"
            secret_value = await esc_client.get_secret(secret_key)
            if secret_value:
                secrets[key] = secret_value
        
        return secrets
    except Exception as e:
        logger.error(f"Failed to get secrets for service {service_name}: {e}")
        return {}


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Get a secret from Pulumi ESC")
    parser.add_argument("--service", "-s", required=True, help="Service name")
    parser.add_argument("--key", "-k", help="Secret key (if not provided, all secrets for the service will be returned)")
    parser.add_argument("--organization", "-o", default="ai-cherry", help="Pulumi organization")
    parser.add_argument("--project", "-p", default="sophia", help="Pulumi project")
    parser.add_argument("--environment", "-e", default="production", help="Environment (stack)")
    parser.add_argument("--config", "-c", action="store_true", help="Get configuration instead of secret")
    parser.add_argument("--output", help="Output file (JSON)")
    parser.add_argument("--github-output", action="store_true", help="Output in GitHub Actions format")
    args = parser.parse_args()
    
    try:
        if args.key:
            # Get a specific secret or configuration
            if args.config:
                value = await get_config(
                    args.service,
                    args.key,
                    args.organization,
                    args.project,
                    args.environment
                )
            else:
                value = await get_secret(
                    args.service,
                    args.key,
                    args.organization,
                    args.project,
                    args.environment
                )
            
            if value is None:
                logger.error(f"Secret or configuration not found: {args.service}_{args.key}")
                return 1
            
            # Output the value
            if args.github_output:
                # GitHub Actions format
                with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                    f.write(f"{args.service}_{args.key}={value}\n")
            elif args.output:
                # Output to file
                with open(args.output, "w") as f:
                    json.dump({"value": value}, f)
            else:
                # Output to stdout
                print(value)
        else:
            # Get all secrets for the service
            secrets = await get_service_secrets(
                args.service,
                args.organization,
                args.project,
                args.environment
            )
            
            if not secrets:
                logger.error(f"No secrets found for service: {args.service}")
                return 1
            
            # Output the secrets
            if args.github_output:
                # GitHub Actions format
                with open(os.environ.get("GITHUB_OUTPUT", ""), "a") as f:
                    for key, value in secrets.items():
                        f.write(f"{args.service}_{key}={value}\n")
            elif args.output:
                # Output to file
                with open(args.output, "w") as f:
                    json.dump(secrets, f)
            else:
                # Output to stdout
                print(json.dumps(secrets, indent=2))
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))

