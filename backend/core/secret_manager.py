import os
import json
import asyncio
from typing import Dict, List, Any, Optional
import logging
import keyring

try:
    from pulumi import automation as auto
except ImportError:
    # Mock for development environments without Pulumi
    class auto:
        class LocalWorkspace:
            def __init__(self, project_settings=None):
                pass
            
            async def get_environment_variables(self, env_name):
                return {}
        
        class ProjectSettings:
            def __init__(self, name=None, runtime=None):
                self.name = name
                self.runtime = runtime

class SophiaSecretManager:
    """Unified secret management for all SOPHIA integrations"""
    
    def __init__(self, env: str = "local"):
        self.env = env
        self.logger = logging.getLogger(__name__)
        self._secrets_cache = {}
        
    async def get_secret(self, key: str, service: Optional[str] = None) -> str:
        """Get secret with fallback hierarchy"""
        cache_key = f"{service}:{key}" if service else key
        
        # Check cache first
        if cache_key in self._secrets_cache:
            return self._secrets_cache[cache_key]
            
        # Try environment-specific methods
        if self.env == "local":
            secret = await self._get_local_secret(key, service)
        elif self.env in ["staging", "production"]:
            secret = await self._get_pulumi_esc_secret(key, service)
        else:
            raise ValueError(f"Unknown environment: {self.env}")
            
        # Cache and return
        if secret:
            self._secrets_cache[cache_key] = secret
            return secret
        else:
            raise ValueError(f"Secret not found: {cache_key}")
    
    async def _get_local_secret(self, key: str, service: Optional[str] = None) -> Optional[str]:
        """Get secret from local environment"""
        env_key = f"{service.upper()}_{key.upper()}" if service else key.upper()
        
        # Try environment variable first
        secret = os.getenv(env_key)
        if secret:
            return secret
            
        # Try system keyring as fallback
        try:
            if service:
                secret = keyring.get_password(f"sophia-{service}", key)
                return secret
        except Exception as e:
            self.logger.warning(f"Keyring access failed: {e}")
            
        return None
    
    async def _get_pulumi_esc_secret(self, key: str, service: Optional[str] = None) -> Optional[str]:
        """Get secret from Pulumi ESC"""
        try:
            # Create workspace
            workspace = auto.LocalWorkspace(
                project_settings=auto.ProjectSettings(
                    name="sophia",
                    runtime="python"
                )
            )
            
            # Get environment variables
            env_name = f"payready/sophia-{self.env}"
            env_vars = await workspace.get_environment_variables(env_name)
            
            # Construct key path
            if service:
                secret_path = f"api_keys.{service}.{key}"
            else:
                secret_path = f"api_keys.{key}"
                
            return env_vars.get(secret_path)
            
        except Exception as e:
            self.logger.error(f"Pulumi ESC access failed: {e}")
            return None

# Singleton instance for global use
secret_manager = SophiaSecretManager(env=os.getenv("SOPHIA_ENV", "local"))
