"""Workflow orchestration layer for n8n integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class N8nWorkflow:
    name: str
    id: str


class N8nWorkflowOrchestrator:
    """Simple orchestrator to execute n8n workflows via REST API."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.registry: Dict[str, N8nWorkflow] = {}
        self._client = httpx.AsyncClient(timeout=30)

    async def close(self) -> None:
        await self._client.aclose()

    def register_workflow(self, name: str, workflow_id: str) -> None:
        self.registry[name] = N8nWorkflow(name=name, id=workflow_id)
        logger.debug("Registered workflow %s -> %s", name, workflow_id)

    async def execute_workflow(
        self,
        name: str,
        inputs: Dict[str, Any],
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a registered workflow with retries."""
        if name not in self.registry:
            raise ValueError(f"Workflow {name} not registered")

        payload = {"input": inputs}
        if agent_context:
            payload["context"] = agent_context

        url = f"{self.base_url}/webhook/{self.registry[name].id}"
        headers = {"X-N8N-API-KEY": self.api_key}

        for attempt in range(3):
            try:
                resp = await self._client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                logger.info("Workflow %s executed", name)
                return data
            except Exception as exc:
                wait_time = 2 ** attempt
                logger.warning("Workflow %s failed: %s - retrying in %ss", name, exc, wait_time)
                await asyncio.sleep(wait_time)
        raise RuntimeError(f"Workflow {name} execution failed after retries")


def create_default_orchestrator() -> N8nWorkflowOrchestrator:
    import os

    orchestrator = N8nWorkflowOrchestrator(
        base_url=os.getenv("N8N_BASE_URL", "http://localhost:5678"),
        api_key=os.getenv("N8N_API_KEY", ""),
    )
    return orchestrator
