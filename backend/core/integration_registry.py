"""
Sophia AI - Integration Registry
Registry for all integrations with the Sophia AI platform
"""

import os
import json
import logging
import asyncio
import importlib
from typing import Dict, List, Any, Optional, Type, Callable
import inspect

from .integration_config import Integration, ServiceConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationRegistry:
    """
    Registry for all integrations with the Sophia AI platform
    """
    
    def __init__(self):
        self.integrations = {}
        self.instances = {}
        self.metadata = {}
        self.initialized = False
    
    def register(self, service_name: str, integration_class: Type[Integration], metadata: Dict[str, Any] = None):
        """Register an integration"""
        self.integrations[service_name] = integration_class
        if metadata:
            self.metadata[service_name] = metadata
        logger.info(f"Registered integration for {service_name}")
    
    def get_integration_class(self, service_name: str) -> Optional[Type[Integration]]:
        """Get an integration class"""
        return self.integrations.get(service_name)
    
    def get_integration(self, service_name: str) -> Optional[Integration]:
        """Get an integration instance"""
        if service_name in self.instances:
            return self.instances[service_name]
        
        integration_class = self.get_integration_class(service_name)
        if not integration_class:
            logger.error(f"Integration not found for {service_name}")
            return None
        
        try:
            instance = integration_class()
            self.instances[service_name] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create instance of {service_name} integration: {e}")
            return None
    
    def get_metadata(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an integration"""
        return self.metadata.get(service_name)
    
    def list_integrations(self) -> List[str]:
        """List all registered integrations"""
        return list(self.integrations.keys())
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all integrations"""
        results = {}
        for service_name in self.integrations:
            integration = self.get_integration(service_name)
            if integration:
                results[service_name] = await integration.initialize()
            else:
                results[service_name] = False
        
        return results
    
    def discover_integrations(self, package_path: str = "backend.integrations") -> List[str]:
        """Discover integrations in a package"""
        discovered = []
        try:
            package = importlib.import_module(package_path)
            package_dir = os.path.dirname(package.__file__)
            
            # Find all Python files in the package
            for filename in os.listdir(package_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = filename[:-3]
                    full_module_name = f"{package_path}.{module_name}"
                    
                    try:
                        module = importlib.import_module(full_module_name)
                        
                        # Find all classes that inherit from Integration
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, Integration) and obj != Integration:
                                # Extract service name from class name
                                service_name = name.replace("Integration", "").lower()
                                
                                # Register integration
                                self.register(service_name, obj)
                                discovered.append(service_name)
                    except Exception as e:
                        logger.error(f"Failed to load module {full_module_name}: {e}")
            
            logger.info(f"Discovered {len(discovered)} integrations in {package_path}")
        except Exception as e:
            logger.error(f"Failed to discover integrations in {package_path}: {e}")
        
        return discovered
    
    def load_registry_file(self, file_path: str = None) -> bool:
        """Load registry from a file"""
        if file_path is None:
            file_path = os.environ.get(
                "INTEGRATION_REGISTRY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/integration_registry.json"
            )
        
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    registry_data = json.load(f)
                
                # Load metadata
                for service_name, metadata in registry_data.items():
                    self.metadata[service_name] = metadata
                
                logger.info(f"Loaded integration registry from {file_path}")
                return True
            else:
                logger.warning(f"Integration registry file not found at {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to load integration registry from {file_path}: {e}")
            return False
    
    def save_registry_file(self, file_path: str = None) -> bool:
        """Save registry to a file"""
        if file_path is None:
            file_path = os.environ.get(
                "INTEGRATION_REGISTRY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/integration_registry.json"
            )
        
        try:
            # Prepare registry data
            registry_data = {}
            for service_name in self.integrations:
                registry_data[service_name] = self.metadata.get(service_name, {})
            
            # Save to file
            with open(file_path, "w") as f:
                json.dump(registry_data, f, indent=2)
            
            logger.info(f"Saved integration registry to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save integration registry to {file_path}: {e}")
            return False


# Global registry instance
registry = IntegrationRegistry()


def register_integration(service_name: str, metadata: Dict[str, Any] = None):
    """Decorator to register an integration"""
    def decorator(cls):
        registry.register(service_name, cls, metadata)
        return cls
    return decorator


def get_integration(service_name: str) -> Optional[Integration]:
    """Get an integration instance"""
    return registry.get_integration(service_name)


async def get_client(service_name: str) -> Optional[Any]:
    """Get a client for a service"""
    integration = get_integration(service_name)
    if not integration:
        return None
    
    await integration.initialize()
    return integration.client


def list_integrations() -> List[str]:
    """List all registered integrations"""
    return registry.list_integrations()


async def initialize_all_integrations() -> Dict[str, bool]:
    """Initialize all integrations"""
    return await registry.initialize_all()


def discover_integrations(package_path: str = "backend.integrations") -> List[str]:
    """Discover integrations in a package"""
    return registry.discover_integrations(package_path)

