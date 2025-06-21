"""Pulumi ESC client wrapper used by infrastructure scripts.

This module exposes :class:`PulumiESCManager`, a thin asynchronous wrapper around
the official ``pulumi_esc`` Python package.  The previous implementation was a
minimal placeholder used to satisfy imports.  It has been replaced with a fully
functional client that authenticates using ``PULUMI_ACCESS_TOKEN`` and provides
methods for retrieving, setting and rotating secrets.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import pulumi_esc

logger = logging.getLogger(__name__)


class PulumiESCManager:
    """Simple asynchronous client for Pulumi ESC."""

    def __init__(
        self,
        organization: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> None:
        self.access_token = os.getenv("PULUMI_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("PULUMI_ACCESS_TOKEN environment variable is required")

        self.organization = organization or os.getenv("PULUMI_ORG", "ai-cherry")
        env_name = environment or os.getenv("PULUMI_ENVIRONMENT", "sophia-ai-production")
        self.environment = f"{self.organization}/default/{env_name}"

        self._client: Optional[pulumi_esc.Client] = None
        self.initialized = False

    async def initialize(self) -> None:
        """Create the underlying ``pulumi_esc`` client if needed."""
        if self.initialized:
            return

        self._client = pulumi_esc.Client(access_token=self.access_token)
        self.initialized = True
        logger.info("Pulumi ESC client initialized for %s", self.environment)

    async def get_secret(self, key: str) -> Optional[str]:
        """Return the value of ``key`` from the current ESC environment."""
        await self.initialize()
        if not self._client:
            return None

        try:
            return await self._client.get_secret(self.environment, key)
        except Exception as exc:  # pragma: no cover - network/ESC failures
            logger.error("Failed to get secret %s: %s", key, exc)
            return None

    async def set_secret(self, key: str, value: str) -> bool:
        """Store ``value`` in the current ESC environment under ``key``."""
        await self.initialize()
        if not self._client:
            return False

        try:
            await self._client.set_secret(self.environment, key, value)
            return True
        except Exception as exc:  # pragma: no cover - network/ESC failures
            logger.error("Failed to set secret %s: %s", key, exc)
            return False

    async def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate ``key`` to ``new_value`` using the ESC API."""
        await self.initialize()
        if not self._client:
            return False

        try:
            await self._client.rotate_secret(self.environment, key, new_value)
            return True
        except Exception as exc:  # pragma: no cover - network/ESC failures
            logger.error("Failed to rotate secret %s: %s", key, exc)
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check against the ESC API."""
        await self.initialize()
        if not self._client:
            return {"status": "uninitialized"}

        try:
            await self._client.get_environment(self.environment)
            return {"status": "healthy", "initialized": True}
        except Exception as exc:  # pragma: no cover - network/ESC failures
            return {
                "status": "unhealthy",
                "error": str(exc),
                "initialized": True,
            }

