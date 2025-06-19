"""
Sophia AI - Pulumi ESC Client
Client for interacting with Pulumi ESC API
"""

import os
import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Union
import aiohttp
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ESCClient:
    """
    Client for interacting with Pulumi ESC API
    """
    
    def __init__(self, organization: str = None, project: str = None, stack: str = None):
        self.organization = organization or os.environ.get("PULUMI_ORGANIZATION", "ai-cherry")
        self.project = project or os.environ.get("PULUMI_PROJECT", "sophia")
        self.stack = stack or os.environ.get("PULUMI_STACK", "production")
        self.environment = f"sophia-{self.stack}"
        self.api_url = "https://api.pulumi.com"
        self.access_token = os.environ.get("PULUMI_ACCESS_TOKEN")
        self.session = None
        self.config_cache = {}
        self.secret_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_refresh = {}
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"token {self.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.pulumi+8"
                }
            )
    
    async def close(self) -> None:
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Pulumi API"""
        await self._ensure_session()
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_text = await response.text()
                
                if response.status >= 400:
                    logger.error(f"Pulumi API error: {response.status} - {response_text}")
                    raise ValueError(f"Pulumi API error: {response.status} - {response_text}")
                
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return {"text": response_text}
                
        except aiohttp.ClientError as e:
            logger.error(f"Pulumi API request error: {e}")
            raise
    
    async def get_environments(self) -> List[Dict[str, Any]]:
        """Get all environments for the organization"""
        response = await self._make_request(
            "GET", 
            f"/api/environments/{self.organization}"
        )
        return response.get("environments", [])
    
    async def get_environment(self, environment_name: str = None) -> Optional[Dict[str, Any]]:
        """Get environment details"""
        env_name = environment_name or self.environment
        try:
            response = await self._make_request(
                "GET", 
                f"/api/environments/{self.organization}/{env_name}"
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get environment {env_name}: {e}")
            return None
    
    async def get_secret_groups(self, environment_name: str = None) -> List[Dict[str, Any]]:
        """Get all secret groups for an environment"""
        env_name = environment_name or self.environment
        try:
            response = await self._make_request(
                "GET", 
                f"/api/environments/{self.organization}/{env_name}/secret-groups"
            )
            return response.get("secretGroups", [])
        except Exception as e:
            logger.error(f"Failed to get secret groups for {env_name}: {e}")
            return []
    
    async def get_secrets(self, environment_name: str = None) -> List[Dict[str, Any]]:
        """Get all secrets for an environment"""
        env_name = environment_name or self.environment
        try:
            response = await self._make_request(
                "GET", 
                f"/api/environments/{self.organization}/{env_name}/secrets"
            )
            return response.get("secrets", [])
        except Exception as e:
            logger.error(f"Failed to get secrets for {env_name}: {e}")
            return []
    
    async def get_secret(self, secret_name: str, environment_name: str = None) -> Optional[str]:
        """Get a secret value"""
        env_name = environment_name or self.environment
        
        # Check if we need to refresh the cache
        cache_key = f"{env_name}:{secret_name}"
        if cache_key not in self.last_refresh or \
           (time.time() - self.last_refresh[cache_key]) > self.cache_ttl:
            
            try:
                # In a real implementation, this would call the Pulumi API to get the secret value
                # For this example, we'll fall back to environment variables
                env_key = secret_name.upper().replace("-", "_")
                value = os.environ.get(env_key)
                
                # Cache the result
                self.secret_cache[cache_key] = value
                self.last_refresh[cache_key] = time.time()
            except Exception as e:
                logger.error(f"Failed to get secret {secret_name} from {env_name}: {e}")
                return None
        
        return self.secret_cache.get(cache_key)
    
    async def get_configuration(self, config_name: str, environment_name: str = None) -> Optional[Any]:
        """Get a configuration value"""
        env_name = environment_name or self.environment
        
        # Check if we need to refresh the cache
        cache_key = f"{env_name}:{config_name}"
        if cache_key not in self.last_refresh or \
           (time.time() - self.last_refresh[cache_key]) > self.cache_ttl:
            
            try:
                # In a real implementation, this would call the Pulumi API to get the configuration value
                # For this example, we'll fall back to environment variables
                env_key = config_name.upper().replace("-", "_")
                value = os.environ.get(env_key)
                
                # Cache the result
                self.config_cache[cache_key] = value
                self.last_refresh[cache_key] = time.time()
            except Exception as e:
                logger.error(f"Failed to get configuration {config_name} from {env_name}: {e}")
                return None
        
        return self.config_cache.get(cache_key)
    
    async def set_secret(self, secret_name: str, value: str, secret_group: str, environment_name: str = None) -> bool:
        """Set a secret value"""
        env_name = environment_name or self.environment
        try:
            # In a real implementation, this would call the Pulumi API to set the secret value
            # For this example, we'll just log the action
            logger.info(f"Setting secret {secret_name} in group {secret_group} for environment {env_name}")
            
            # Update the cache
            cache_key = f"{env_name}:{secret_name}"
            self.secret_cache[cache_key] = value
            self.last_refresh[cache_key] = time.time()
            
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {secret_name} in {env_name}: {e}")
            return False
    
    async def set_configuration(self, config_name: str, value: Any, environment_name: str = None) -> bool:
        """Set a configuration value"""
        env_name = environment_name or self.environment
        try:
            # In a real implementation, this would call the Pulumi API to set the configuration value
            # For this example, we'll just log the action
            logger.info(f"Setting configuration {config_name} for environment {env_name}")
            
            # Update the cache
            cache_key = f"{env_name}:{config_name}"
            self.config_cache[cache_key] = value
            self.last_refresh[cache_key] = time.time()
            
            return True
        except Exception as e:
            logger.error(f"Failed to set configuration {config_name} in {env_name}: {e}")
            return False

