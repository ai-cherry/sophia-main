#!/usr/bin/env python3
"""
Sophia AI - Integration Management CLI
Command-line interface for managing integrations with the Sophia AI platform
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from typing import Dict, List, Any, Optional
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Import integration modules
from backend.core.integration_registry import registry, discover_integrations
from backend.core.integration_config import config_manager


class IntegrationManager:
    """
    Manager for integrations with the Sophia AI platform
    """
    
    def __init__(self):
        self.registry = registry
        self.config_manager = config_manager
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the integration manager"""
        if self.initialized:
            return True
        
        try:
            # Initialize config manager
            await self.config_manager.initialize()
            
            # Load registry file
            self.registry.load_registry_file()
            
            # Discover integrations
            discover_integrations()
            
            self.initialized = True
            logger.info("Integration manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize integration manager: {e}")
            return False
    
    async def list_integrations(self) -> List[Dict[str, Any]]:
        """List all integrations"""
        if not self.initialized:
            await self.initialize()
        
        result = []
        for service_name in self.registry.list_integrations():
            metadata = self.registry.get_metadata(service_name) or {}
            
            # Get service configuration
            service_config = await self.config_manager.get_service_config(service_name)
            if service_config:
                config_keys = list(service_config.config.keys())
                secret_keys = list(service_config.secrets.keys())
            else:
                config_keys = []
                secret_keys = []
            
            result.append({
                "service_name": service_name,
                "type": metadata.get("type", "unknown"),
                "description": metadata.get("description", ""),
                "config_keys": config_keys,
                "secret_keys": secret_keys,
                "rotation_schedule": metadata.get("rotation_schedule", "90d"),
                "owner": metadata.get("owner", ""),
                "dependencies": metadata.get("dependencies", [])
            })
        
        return result
    
    async def get_integration_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of an integration"""
        if not self.initialized:
            await self.initialize()
        
        # Get integration
        integration = self.registry.get_integration(service_name)
        if not integration:
            return {
                "service_name": service_name,
                "status": "not_found",
                "error": f"Integration not found for {service_name}"
            }
        
        # Get metadata
        metadata = self.registry.get_metadata(service_name) or {}
        
        # Get service configuration
        service_config = await self.config_manager.get_service_config(service_name)
        if not service_config:
            return {
                "service_name": service_name,
                "status": "not_configured",
                "error": f"Configuration not found for {service_name}",
                "metadata": metadata
            }
        
        # Check if all required configuration is present
        config_keys = service_config.config.keys()
        secret_keys = service_config.secrets.keys()
        
        # Check if all required configuration is present
        required_config_keys = metadata.get("config_keys", [])
        required_secret_keys = metadata.get("secret_keys", [])
        
        missing_config = [key for key in required_config_keys if key not in config_keys]
        missing_secrets = [key for key in required_secret_keys if key not in secret_keys]
        
        if missing_config or missing_secrets:
            return {
                "service_name": service_name,
                "status": "incomplete_configuration",
                "error": f"Missing configuration for {service_name}",
                "missing_config": missing_config,
                "missing_secrets": missing_secrets,
                "metadata": metadata,
                "config_keys": list(config_keys),
                "secret_keys": list(secret_keys)
            }
        
        # Try to initialize the integration
        try:
            await integration.initialize()
            
            return {
                "service_name": service_name,
                "status": "ok" if integration.initialized else "initialization_failed",
                "error": None if integration.initialized else "Failed to initialize integration",
                "metadata": metadata,
                "config_keys": list(config_keys),
                "secret_keys": list(secret_keys)
            }
        except Exception as e:
            return {
                "service_name": service_name,
                "status": "initialization_failed",
                "error": str(e),
                "metadata": metadata,
                "config_keys": list(config_keys),
                "secret_keys": list(secret_keys)
            }
    
    async def get_all_integration_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all integrations"""
        if not self.initialized:
            await self.initialize()
        
        result = {}
        for service_name in self.registry.list_integrations():
            result[service_name] = await self.get_integration_status(service_name)
        
        return result
    
    async def test_integration(self, service_name: str) -> Dict[str, Any]:
        """Test an integration"""
        if not self.initialized:
            await self.initialize()
        
        # Get integration
        integration = self.registry.get_integration(service_name)
        if not integration:
            return {
                "service_name": service_name,
                "status": "not_found",
                "error": f"Integration not found for {service_name}"
            }
        
        # Try to initialize the integration
        try:
            await integration.initialize()
            
            if not integration.initialized:
                return {
                    "service_name": service_name,
                    "status": "initialization_failed",
                    "error": "Failed to initialize integration"
                }
            
            # Try to get client
            client = integration.client
            if not client:
                return {
                    "service_name": service_name,
                    "status": "client_creation_failed",
                    "error": "Failed to create client"
                }
            
            # Try to perform a simple operation
            # This is service-specific and would need to be implemented for each service
            # For now, we'll just return success
            return {
                "service_name": service_name,
                "status": "ok",
                "error": None
            }
        except Exception as e:
            return {
                "service_name": service_name,
                "status": "test_failed",
                "error": str(e)
            }
    
    async def update_integration_metadata(self, service_name: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for an integration"""
        if not self.initialized:
            await self.initialize()
        
        # Check if integration exists
        if service_name not in self.registry.list_integrations():
            logger.error(f"Integration not found for {service_name}")
            return False
        
        # Update metadata
        self.registry.metadata[service_name] = metadata
        
        # Save registry file
        return self.registry.save_registry_file()
    
    async def register_integration(self, service_name: str, metadata: Dict[str, Any]) -> bool:
        """Register a new integration"""
        if not self.initialized:
            await self.initialize()
        
        # Check if integration already exists
        if service_name in self.registry.list_integrations():
            logger.error(f"Integration already exists for {service_name}")
            return False
        
        # Register integration
        self.registry.metadata[service_name] = metadata
        
        # Save registry file
        return self.registry.save_registry_file()


def format_status(status: Dict[str, Any]) -> str:
    """Format status for display"""
    result = []
    result.append(f"Service: {status['service_name']}")
    result.append(f"Status: {status['status']}")
    
    if status.get("error"):
        result.append(f"Error: {status['error']}")
    
    if "metadata" in status:
        metadata = status["metadata"]
        result.append("Metadata:")
        for key, value in metadata.items():
            result.append(f"  {key}: {value}")
    
    if "config_keys" in status:
        result.append("Config Keys:")
        for key in status["config_keys"]:
            result.append(f"  {key}")
    
    if "secret_keys" in status:
        result.append("Secret Keys:")
        for key in status["secret_keys"]:
            result.append(f"  {key}")
    
    if "missing_config" in status and status["missing_config"]:
        result.append("Missing Config:")
        for key in status["missing_config"]:
            result.append(f"  {key}")
    
    if "missing_secrets" in status and status["missing_secrets"]:
        result.append("Missing Secrets:")
        for key in status["missing_secrets"]:
            result.append(f"  {key}")
    
    return "\n".join(result)


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Manage integrations with the Sophia AI platform")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all integrations")
    list_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get status of integrations")
    status_parser.add_argument("--service", help="Service name (default: all)")
    status_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test an integration")
    test_parser.add_argument("--service", required=True, help="Service name")
    test_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update integration metadata")
    update_parser.add_argument("--service", required=True, help="Service name")
    update_parser.add_argument("--metadata", required=True, help="Metadata file (JSON)")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register a new integration")
    register_parser.add_argument("--service", required=True, help="Service name")
    register_parser.add_argument("--metadata", required=True, help="Metadata file (JSON)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create integration manager
    manager = IntegrationManager()
    
    try:
        if args.command == "list":
            # List integrations
            integrations = await manager.list_integrations()
            
            if args.format == "json":
                print(json.dumps(integrations, indent=2))
            else:
                for integration in integrations:
                    print(f"Service: {integration['service_name']}")
                    print(f"Type: {integration['type']}")
                    print(f"Description: {integration['description']}")
                    print(f"Config Keys: {', '.join(integration['config_keys'])}")
                    print(f"Secret Keys: {', '.join(integration['secret_keys'])}")
                    print(f"Rotation Schedule: {integration['rotation_schedule']}")
                    print(f"Owner: {integration['owner']}")
                    print(f"Dependencies: {', '.join(integration['dependencies'])}")
                    print()
        
        elif args.command == "status":
            # Get status
            if args.service:
                status = await manager.get_integration_status(args.service)
                
                if args.format == "json":
                    print(json.dumps(status, indent=2))
                else:
                    print(format_status(status))
            else:
                status = await manager.get_all_integration_status()
                
                if args.format == "json":
                    print(json.dumps(status, indent=2))
                else:
                    for service_name, service_status in status.items():
                        print(format_status(service_status))
                        print()
        
        elif args.command == "test":
            # Test integration
            result = await manager.test_integration(args.service)
            
            if args.format == "json":
                print(json.dumps(result, indent=2))
            else:
                print(f"Service: {result['service_name']}")
                print(f"Status: {result['status']}")
                if result.get("error"):
                    print(f"Error: {result['error']}")
        
        elif args.command == "update":
            # Update integration metadata
            with open(args.metadata, "r") as f:
                metadata = json.load(f)
            
            success = await manager.update_integration_metadata(args.service, metadata)
            
            if success:
                print(f"Updated metadata for {args.service}")
            else:
                print(f"Failed to update metadata for {args.service}")
                return 1
        
        elif args.command == "register":
            # Register integration
            with open(args.metadata, "r") as f:
                metadata = json.load(f)
            
            success = await manager.register_integration(args.service, metadata)
            
            if success:
                print(f"Registered integration {args.service}")
            else:
                print(f"Failed to register integration {args.service}")
                return 1
        
        else:
            parser.print_help()
            return 1
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))

