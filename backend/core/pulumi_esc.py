"""Sophia AI - Enhanced Pulumi ESC Client (LEGACY)

🔐 IMPORTANT: This file is now LEGACY - Use backend/core/auto_esc_config.py instead!

The permanent GitHub Organization Secrets → Pulumi ESC solution provides automatic configuration.
This file is kept for backward compatibility and advanced ESC operations only.

For new code, use:
from backend.core.auto_esc_config import config

Client for interacting with Pulumi ESC API with improved error handling and security
"""

import asyncio
import logging
import os
import time
from functools import wraps
from typing import Any, Dict, List, Optional

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🚨 LEGACY WARNING
logger.warning(
    "pulumi_esc.py is LEGACY. Use backend/core/auto_esc_config.py for automatic secret loading from Pulumi ESC."
)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}"
                    )
                    await asyncio.sleep(delay * (2**attempt))  # Exponential backoff
            return None

        return wrapper

    return decorator


class ESCClient:
    """Enhanced client for interacting with Pulumi ESC API"""

    def __init__(
        self, organization: str = None, project: str = None, stack: str = None
    ):
        self.organization = organization or os.environ.get(
            "PULUMI_ORGANIZATION", "ai-cherry"
        )
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
        self._lock = asyncio.Lock()
        self.initialized = False

        if not self.access_token:
            raise ValueError("PULUMI_ACCESS_TOKEN environment variable is required")

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created with proper error handling"""
        if self.session is None or self.session.closed:
            if not self.access_token:
                raise ValueError("Pulumi access token is required")

            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"token {self.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.pulumi+8",
                },
                timeout=timeout,
            )

    async def close(self) -> None:
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    @retry_on_failure(max_retries=3)
    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retry logic and error handling"""
        await self._ensure_session()

        url = f"{self.api_url}{endpoint}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.warning(f"Resource not found: {endpoint}")
                    return None
                elif response.status == 401:
                    logger.error("Unauthorized: Check Pulumi access token")
                    raise ValueError("Invalid Pulumi access token")
                elif response.status == 403:
                    logger.error("Forbidden: Insufficient permissions")
                    raise ValueError("Insufficient Pulumi permissions")
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status} for {endpoint}: {error_text}")
                    response.raise_for_status()
        except aiohttp.ClientError as e:
            logger.error(f"Client error for {endpoint}: {e}")
            raise
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error for {endpoint}: {e}")
            raise

    @retry_on_failure(max_retries=2)
    async def get_environment(self) -> Optional[Dict[str, Any]]:
        """Get Pulumi ESC environment details"""
        endpoint = f"/api/environments/{self.organization}/{self.environment}"
        return await self._make_request("GET", endpoint)

    @retry_on_failure(max_retries=2)
    async def get_configuration(self, key: str) -> Optional[Any]:
        """Get configuration value from Pulumi ESC"""
        # Check cache first
        cache_key = f"config_{key}"
        if cache_key in self.config_cache:
            cached_time = self.last_refresh.get(cache_key, 0)
            if time.time() - cached_time < self.cache_ttl:
                return self.config_cache[cache_key]

        try:
            endpoint = (
                f"/api/environments/{self.organization}/{self.environment}/values"
            )
            response = await self._make_request("GET", endpoint)

            if response and "values" in response:
                values = response["values"]

                # Navigate nested structure to find the key
                value = self._get_nested_value(values, key)

                # Cache the result
                self.config_cache[cache_key] = value
                self.last_refresh[cache_key] = time.time()

                return value

        except Exception as e:
            logger.error(f"Failed to get configuration for {key}: {e}")

        return None

    @retry_on_failure(max_retries=2)
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret value from Pulumi ESC"""
        # Check cache first
        cache_key = f"secret_{key}"
        if cache_key in self.secret_cache:
            cached_time = self.last_refresh.get(cache_key, 0)
            if time.time() - cached_time < self.cache_ttl:
                return self.secret_cache[cache_key]

        try:
            endpoint = (
                f"/api/environments/{self.organization}/{self.environment}/values"
            )
            response = await self._make_request("GET", endpoint)

            if response and "values" in response:
                values = response["values"]

                # Navigate nested structure to find the secret
                secret = self._get_nested_value(values, key)

                if secret is not None:
                    # Cache the result (be careful with secret caching)
                    self.secret_cache[cache_key] = secret
                    self.last_refresh[cache_key] = time.time()

                return secret

        except Exception as e:
            logger.error(f"Failed to get secret for {key}: {e}")

        return None

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[Any]:
        """Get value from nested dictionary structure"""
        # Try direct key access first
        if key in data:
            return data[key]

        # Try with service prefix patterns
        parts = key.split("_", 1)
        if len(parts) == 2:
            service, field = parts

            # Check if there's a service section
            if service in data and isinstance(data[service], dict):
                if field in data[service]:
                    return data[service][field]

            # Check for secrets section
            if "secrets" in data and isinstance(data["secrets"], dict):
                if key in data["secrets"]:
                    return data["secrets"][key]
                if service in data["secrets"] and isinstance(
                    data["secrets"][service], dict
                ):
                    if field in data["secrets"][service]:
                        return data["secrets"][service][field]

            # Check for config section
            if "config" in data and isinstance(data["config"], dict):
                if key in data["config"]:
                    return data["config"][key]
                if service in data["config"] and isinstance(
                    data["config"][service], dict
                ):
                    if field in data["config"][service]:
                        return data["config"][service][field]

        return None

    async def set_configuration(self, key: str, value: Any) -> bool:
        """Set configuration value in Pulumi ESC"""
        try:
            endpoint = (
                f"/api/environments/{self.organization}/{self.environment}/values"
            )

            # Get current values
            current = await self._make_request("GET", endpoint)
            if not current:
                current = {"values": {}}

            # Update the value
            values = current.get("values", {})
            self._set_nested_value(values, key, value)

            # Update the environment
            payload = {"values": values}
            response = await self._make_request("PUT", endpoint, json=payload)

            if response:
                # Clear cache for this key
                cache_key = f"config_{key}"
                if cache_key in self.config_cache:
                    del self.config_cache[cache_key]
                if cache_key in self.last_refresh:
                    del self.last_refresh[cache_key]

                logger.info(f"Successfully set configuration for {key}")
                return True

        except Exception as e:
            logger.error(f"Failed to set configuration for {key}: {e}")

        return False

    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret value in Pulumi ESC"""
        try:
            endpoint = (
                f"/api/environments/{self.organization}/{self.environment}/values"
            )

            # Get current values
            current = await self._make_request("GET", endpoint)
            if not current:
                current = {"values": {}}

            # Update the secret
            values = current.get("values", {})
            if "secrets" not in values:
                values["secrets"] = {}

            self._set_nested_value(values["secrets"], key, {"secret": value})

            # Update the environment
            payload = {"values": values}
            response = await self._make_request("PUT", endpoint, json=payload)

            if response:
                # Clear cache for this key
                cache_key = f"secret_{key}"
                if cache_key in self.secret_cache:
                    del self.secret_cache[cache_key]
                if cache_key in self.last_refresh:
                    del self.last_refresh[cache_key]

                logger.info(f"Successfully set secret for {key}")
                return True

        except Exception as e:
            logger.error(f"Failed to set secret for {key}: {e}")

        return False

    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set value in nested dictionary structure"""
        parts = key.split("_", 1)
        if len(parts) == 2:
            service, field = parts
            if service not in data:
                data[service] = {}
            data[service][field] = value
        else:
            data[key] = value

    async def list_environments(self) -> List[str]:
        """List all Pulumi ESC environments for the organization"""
        try:
            endpoint = f"/api/environments/{self.organization}"
            response = await self._make_request("GET", endpoint)

            if response and "environments" in response:
                return [env["name"] for env in response["environments"]]

        except Exception as e:
            logger.error(f"Failed to list environments: {e}")

        return []

    async def validate_connection(self) -> bool:
        """Validate connection to Pulumi ESC"""
        try:
            environments = await self.list_environments()
            if self.environment in environments:
                logger.info(
                    f"Successfully validated connection to Pulumi ESC environment: {self.environment}"
                )
                return True
            else:
                logger.warning(
                    f"Environment {self.environment} not found in organization {self.organization}"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to validate Pulumi ESC connection: {e}")
            return False

    async def clear_cache(self) -> None:
        """Clear all cached values"""
        async with self._lock:
            self.config_cache.clear()
            self.secret_cache.clear()
            self.last_refresh.clear()
        logger.info("Cleared Pulumi ESC cache")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "config_cache_size": len(self.config_cache),
            "secret_cache_size": len(self.secret_cache),
            "cache_ttl": self.cache_ttl,
            "last_refresh_count": len(self.last_refresh),
        }


# Global Pulumi ESC client instance
pulumi_esc_client = ESCClient()
