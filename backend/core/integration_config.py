"""
Sophia AI - Integration Configuration Module
Centralized configuration management for all integrations
"""

import os
import json
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, Callable
from dataclasses import dataclass, field
import aiohttp
import importlib
from functools import lru_cache

from .pulumi_esc import ESCClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variables for generic types
T = TypeVar('T')
ConfigType = TypeVar('ConfigType')
ClientType = TypeVar('ClientType')

@dataclass
class ServiceConfig:
    """Service configuration container"""
    service_name: str
    config: Dict[str, Any] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationError(Exception):
    """Exception raised for configuration errors"""
    pass


class IntegrationRegistry:
    """Registry of all integrations"""
    
    def __init__(self):
        self.integrations = {}
        self.clients = {}
        self.initialized = False
    
    def register(self, service_name: str, integration_class: Any):
        """Register an integration"""
        self.integrations[service_name] = integration_class
        logger.info(f"Registered integration for {service_name}")
    
    def get_integration(self, service_name: str) -> Optional[Any]:
        """Get an integration class"""
        return self.integrations.get(service_name)
    
    def get_client(self, service_name: str) -> Optional[Any]:
        """Get a client instance"""
        return self.clients.get(service_name)
    
    def set_client(self, service_name: str, client: Any):
        """Set a client instance"""
        self.clients[service_name] = client
    
    def list_integrations(self) -> List[str]:
        """List all registered integrations"""
        return list(self.integrations.keys())


# Global registry instance
registry = IntegrationRegistry()


class IntegrationConfig:
    """
    Centralized configuration manager for all integrations
    """
    
    def __init__(self):
        self.configs = {}
        self.secrets = {}
        self.esc_client = None
        self.initialized = False
        self.environment = os.environ.get("SOPHIA_ENVIRONMENT", "production")
        self.config_cache = {}
        self.secret_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_refresh = {}
    
    async def initialize(self) -> bool:
        """Initialize the configuration manager"""
        if self.initialized:
            return True
        
        try:
            # Initialize Pulumi ESC client
            self.esc_client = ESCClient(
                organization=os.environ.get("PULUMI_ORGANIZATION", "ai-cherry"),
                project=os.environ.get("PULUMI_PROJECT", "sophia"),
                stack=self.environment
            )
            
            # Load service registry
            await self._load_service_registry()
            
            self.initialized = True
            logger.info("Integration configuration manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize integration configuration manager: {e}")
            return False
    
    async def _load_service_registry(self) -> None:
        """Load service registry from Pulumi ESC or local file"""
        try:
            # Try to load from Pulumi ESC first
            if self.esc_client:
                registry = await self.esc_client.get_configuration("service_registry")
                if registry:
                    self.configs = registry
                    logger.info(f"Loaded service registry from Pulumi ESC with {len(self.configs)} services")
                    return
            
            # Fall back to local file
            registry_path = os.environ.get(
                "SERVICE_REGISTRY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/service_registry.json"
            )
            
            if os.path.exists(registry_path):
                with open(registry_path, "r") as f:
                    self.configs = json.load(f)
                logger.info(f"Loaded service registry from local file with {len(self.configs)} services")
            else:
                logger.error(f"Service registry not found at {registry_path}")
                self.configs = {}
        except Exception as e:
            logger.error(f"Failed to load service registry: {e}")
            self.configs = {}
    
    async def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service"""
        if not self.initialized:
            await self.initialize()
        
        if service_name not in self.configs:
            logger.error(f"Unknown service: {service_name}")
            return None
        
        try:
            # Check if we need to refresh the cache
            if service_name not in self.last_refresh or \
               (time.time() - self.last_refresh[service_name]) > self.cache_ttl:
                
                # Get service configuration
                config = {}
                secrets = {}
                
                # Get configuration values
                for key in self.configs[service_name].get("config_keys", []):
                    config_key = f"{service_name}_{key}"
                    if self.esc_client:
                        value = await self.esc_client.get_configuration(config_key)
                        if value is not None:
                            config[key] = value
                    else:
                        # Fall back to environment variables
                        env_key = f"{service_name.upper()}_{key.upper()}"
                        if env_key in os.environ:
                            config[key] = os.environ[env_key]
                
                # Get secret values
                for key in self.configs[service_name].get("secret_keys", []):
                    secret_key = f"{service_name}_{key}"
                    if self.esc_client:
                        value = await self.esc_client.get_secret(secret_key)
                        if value is not None:
                            secrets[key] = value
                    else:
                        # Fall back to environment variables
                        env_key = f"{service_name.upper()}_{key.upper()}"
                        if env_key in os.environ:
                            secrets[key] = os.environ[env_key]
                
                # Cache the results
                self.config_cache[service_name] = config
                self.secret_cache[service_name] = secrets
                self.last_refresh[service_name] = time.time()
            
            # Return service configuration
            return ServiceConfig(
                service_name=service_name,
                config=self.config_cache[service_name],
                secrets=self.secret_cache[service_name],
                metadata=self.configs[service_name]
            )
        except Exception as e:
            logger.error(f"Failed to get configuration for {service_name}: {e}")
            return None
    
    async def get_config_value(self, service_name: str, key: str) -> Optional[Any]:
        """Get a specific configuration value"""
        service_config = await self.get_service_config(service_name)
        if not service_config:
            return None
        
        return service_config.config.get(key)
    
    async def get_secret_value(self, service_name: str, key: str) -> Optional[str]:
        """Get a specific secret value"""
        service_config = await self.get_service_config(service_name)
        if not service_config:
            return None
        
        return service_config.secrets.get(key)
    
    async def get_connection_string(self, service_name: str) -> Optional[str]:
        """Get connection string for a service"""
        service_config = await self.get_service_config(service_name)
        if not service_config:
            return None
        
        try:
            if service_name == "snowflake":
                return f"snowflake://{service_config.secrets['user']}:{service_config.secrets['password']}@{service_config.config['account']}/{service_config.config['database']}/{service_config.config['schema']}?warehouse={service_config.config['warehouse']}&role={service_config.config['role']}"
            elif service_name == "postgres":
                return f"postgresql://{service_config.secrets['user']}:{service_config.secrets['password']}@{service_config.config['host']}:{service_config.config['port']}/{service_config.config['database']}"
            else:
                return None
        except KeyError as e:
            logger.error(f"Missing configuration for connection string: {e}")
            return None
    
    async def list_services(self) -> List[str]:
        """List all registered services"""
        if not self.initialized:
            await self.initialize()
        
        return list(self.configs.keys())
    
    async def get_service_metadata(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific service"""
        if not self.initialized:
            await self.initialize()
        
        if service_name not in self.configs:
            logger.error(f"Unknown service: {service_name}")
            return None
        
        return self.configs[service_name]


class Integration(Generic[ConfigType, ClientType]):
    """Base class for all integrations"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.config_manager = IntegrationConfig()
        self.client = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the integration"""
        if self.initialized:
            return True
        
        try:
            # Initialize config manager
            if not self.config_manager.initialized:
                await self.config_manager.initialize()
            
            # Get service configuration
            service_config = await self.config_manager.get_service_config(self.service_name)
            if not service_config:
                logger.error(f"Failed to get configuration for {self.service_name}")
                return False
            
            # Initialize client
            self.client = await self._create_client(service_config)
            if not self.client:
                logger.error(f"Failed to create client for {self.service_name}")
                return False
            
            # Register client in registry
            registry.set_client(self.service_name, self.client)
            
            self.initialized = True
            logger.info(f"Initialized {self.service_name} integration")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.service_name} integration: {e}")
            return False
    
    async def _create_client(self, config: ServiceConfig) -> Optional[ClientType]:
        """Create a client for the integration"""
        raise NotImplementedError("Subclasses must implement _create_client")
    
    async def get_client(self) -> Optional[ClientType]:
        """Get the client for the integration"""
        if not self.initialized:
            await self.initialize()
        
        return self.client


class SnowflakeIntegration(Integration[ServiceConfig, Any]):
    """Snowflake integration"""
    
    def __init__(self):
        super().__init__("snowflake")
    
    async def _create_client(self, config: ServiceConfig) -> Optional[Any]:
        """Create a Snowflake client"""
        try:
            # Import snowflake connector
            import snowflake.connector
            
            # Create connection
            conn = snowflake.connector.connect(
                user=config.secrets.get("user"),
                password=config.secrets.get("password"),
                account=config.config.get("account"),
                warehouse=config.config.get("warehouse"),
                database=config.config.get("database"),
                schema=config.config.get("schema"),
                role=config.config.get("role")
            )
            
            return conn
        except ImportError:
            logger.error("Snowflake connector not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create Snowflake client: {e}")
            return None


class PineconeIntegration(Integration[ServiceConfig, Any]):
    """Pinecone integration"""
    
    def __init__(self):
        super().__init__("pinecone")
    
    async def _create_client(self, config: ServiceConfig) -> Optional[Any]:
        """Create a Pinecone client"""
        try:
            # Import pinecone
            import pinecone
            
            # Initialize pinecone
            pinecone.init(
                api_key=config.secrets.get("api_key"),
                environment=config.config.get("environment")
            )
            
            return pinecone
        except ImportError:
            logger.error("Pinecone not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create Pinecone client: {e}")
            return None


class OpenAIIntegration(Integration[ServiceConfig, Any]):
    """OpenAI integration"""
    
    def __init__(self):
        super().__init__("openai")
    
    async def _create_client(self, config: ServiceConfig) -> Optional[Any]:
        """Create an OpenAI client"""
        try:
            # Import openai
            import openai
            
            # Set API key
            openai.api_key = config.secrets.get("api_key")
            
            return openai
        except ImportError:
            logger.error("OpenAI not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            return None


class AnthropicIntegration(Integration[ServiceConfig, Any]):
    """Anthropic integration"""
    
    def __init__(self):
        super().__init__("anthropic")
    
    async def _create_client(self, config: ServiceConfig) -> Optional[Any]:
        """Create an Anthropic client"""
        try:
            # Import anthropic
            import anthropic
            
            # Create client
            client = anthropic.Anthropic(api_key=config.secrets.get("api_key"))
            
            return client
        except ImportError:
            logger.error("Anthropic not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create Anthropic client: {e}")
            return None


class EstuaryIntegration(Integration[ServiceConfig, Any]):
    """Estuary integration"""
    
    def __init__(self):
        super().__init__("estuary")
    
    async def _create_client(self, config: ServiceConfig) -> Optional[Any]:
        """Create an Estuary client"""
        try:
            # Import custom Estuary client
            from ..integrations.estuary_flow_integration_updated import EstuaryFlowClient
            
            # Create client
            client = EstuaryFlowClient()
            await client.setup()
            
            return client
        except ImportError:
            logger.error("Estuary client not found")
            return None
        except Exception as e:
            logger.error(f"Failed to create Estuary client: {e}")
            return None


class AirbyteIntegration(Integration[ServiceConfig, Any]):
    """Airbyte integration"""
    
    def __init__(self):
        super().__init__("airbyte")
    
    async def _create_client(self, config: ServiceConfig) -> Optional[Any]:
        """Create an Airbyte client"""
        try:
            # Import custom Airbyte client
            from ..integrations.airbyte_cloud_integration import AirbyteCloudClient
            
            # Create client
            client = AirbyteCloudClient()
            await client.setup()
            
            return client
        except ImportError:
            logger.error("Airbyte client not found")
            return None
        except Exception as e:
            logger.error(f"Failed to create Airbyte client: {e}")
            return None


# Register integrations
registry.register("snowflake", SnowflakeIntegration)
registry.register("pinecone", PineconeIntegration)
registry.register("openai", OpenAIIntegration)
registry.register("anthropic", AnthropicIntegration)
registry.register("estuary", EstuaryIntegration)
registry.register("airbyte", AirbyteIntegration)


# Singleton instance of the configuration manager
config_manager = IntegrationConfig()


@lru_cache(maxsize=32)
def get_integration(service_name: str) -> Optional[Integration]:
    """Get an integration instance"""
    integration_class = registry.get_integration(service_name)
    if not integration_class:
        logger.error(f"Integration not found for {service_name}")
        return None
    
    return integration_class()


async def get_client(service_name: str) -> Optional[Any]:
    """Get a client for a service"""
    # Check if client is already initialized
    client = registry.get_client(service_name)
    if client:
        return client
    
    # Initialize integration and get client
    integration = get_integration(service_name)
    if not integration:
        return None
    
    await integration.initialize()
    return integration.client


async def get_config(service_name: str) -> Optional[ServiceConfig]:
    """Get configuration for a service"""
    return await config_manager.get_service_config(service_name)


async def get_secret(service_name: str, key: str) -> Optional[str]:
    """Get a secret value"""
    return await config_manager.get_secret_value(service_name, key)


async def get_connection_string(service_name: str) -> Optional[str]:
    """Get connection string for a service"""
    return await config_manager.get_connection_string(service_name)


async def list_services() -> List[str]:
    """List all registered services"""
    return await config_manager.list_services()


async def list_integrations() -> List[str]:
    """List all registered integrations"""
    return registry.list_integrations()

