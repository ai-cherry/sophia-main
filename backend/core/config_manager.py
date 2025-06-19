"""
Sophia AI - Configuration Manager
Centralized configuration management for all integrations
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
import aiohttp
import pulumi_esc
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Service configuration container"""
    service_name: str
    config: Dict[str, Any]
    secrets: Dict[str, str]
    metadata: Dict[str, Any]


class ConfigManager:
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
            self.esc_client = pulumi_esc.ESCClient(
                organization=os.environ.get("PULUMI_ORGANIZATION", "ai-cherry"),
                project=os.environ.get("PULUMI_PROJECT", "sophia"),
                stack=self.environment
            )
            
            # Load service registry
            await self._load_service_registry()
            
            self.initialized = True
            logger.info("Configuration manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize configuration manager: {e}")
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
                # Create default registry
                self.configs = {
                    "snowflake": {
                        "type": "database",
                        "config_keys": ["account", "warehouse", "database", "schema", "role"],
                        "secret_keys": ["user", "password"],
                        "rotation_schedule": "30d"
                    },
                    "gong": {
                        "type": "api",
                        "config_keys": ["base_url"],
                        "secret_keys": ["api_key", "api_secret", "client_secret"],
                        "rotation_schedule": "60d"
                    },
                    "vercel": {
                        "type": "api",
                        "config_keys": ["team_id", "project_id", "org_id"],
                        "secret_keys": ["token"],
                        "rotation_schedule": "90d"
                    },
                    "estuary": {
                        "type": "api",
                        "config_keys": ["api_url"],
                        "secret_keys": ["api_key"],
                        "rotation_schedule": "60d"
                    },
                    "lambda_labs": {
                        "type": "infrastructure",
                        "config_keys": [],
                        "secret_keys": ["api_key", "jupyter_password", "ssh_public_key", "ssh_private_key"],
                        "rotation_schedule": "90d"
                    },
                    "airbyte": {
                        "type": "api",
                        "config_keys": [],
                        "secret_keys": ["api_key", "password"],
                        "rotation_schedule": "60d"
                    },
                    "pinecone": {
                        "type": "api",
                        "config_keys": ["environment"],
                        "secret_keys": ["api_key"],
                        "rotation_schedule": "90d"
                    },
                    "weaviate": {
                        "type": "api",
                        "config_keys": ["url"],
                        "secret_keys": ["api_key"],
                        "rotation_schedule": "90d"
                    },
                    "openai": {
                        "type": "api",
                        "config_keys": [],
                        "secret_keys": ["api_key"],
                        "rotation_schedule": "30d"
                    },
                    "anthropic": {
                        "type": "api",
                        "config_keys": [],
                        "secret_keys": ["api_key"],
                        "rotation_schedule": "30d"
                    }
                }
                logger.info(f"Created default service registry with {len(self.configs)} services")
        except Exception as e:
            logger.error(f"Failed to load service registry: {e}")
            # Create empty registry
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
    
    async def get_api_client(self, service_name: str) -> Optional[Any]:
        """Get API client for a service"""
        service_config = await self.get_service_config(service_name)
        if not service_config:
            return None
        
        try:
            if service_name == "pinecone":
                import pinecone
                pinecone.init(
                    api_key=service_config.secrets["api_key"],
                    environment=service_config.config["environment"]
                )
                return pinecone
            elif service_name == "openai":
                import openai
                openai.api_key = service_config.secrets["api_key"]
                return openai
            elif service_name == "anthropic":
                import anthropic
                client = anthropic.Anthropic(api_key=service_config.secrets["api_key"])
                return client
            else:
                return None
        except ImportError as e:
            logger.error(f"Failed to import module for {service_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create API client for {service_name}: {e}")
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


# Create singleton instance
config_manager = ConfigManager()

async def get_config(service_name: str) -> Optional[ServiceConfig]:
    """Get configuration for a service"""
    return await config_manager.get_service_config(service_name)

async def get_secret(service_name: str, key: str) -> Optional[str]:
    """Get a secret value"""
    return await config_manager.get_secret_value(service_name, key)

async def get_connection_string(service_name: str) -> Optional[str]:
    """Get connection string for a service"""
    return await config_manager.get_connection_string(service_name)

async def get_api_client(service_name: str) -> Optional[Any]:
    """Get API client for a service"""
    return await config_manager.get_api_client(service_name)

