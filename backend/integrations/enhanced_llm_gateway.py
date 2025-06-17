"""Enhanced LLM gateway using Portkey and OpenRouter."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class EnhancedLLMGateway:
    """Route LLM requests with intelligent model selection."""

    def __init__(self, portkey_api_key: str, openrouter_api_key: str | None = None) -> None:
        self.portkey_key = portkey_api_key
        self.openrouter_key = openrouter_api_key
        self.client = httpx.AsyncClient(timeout=60)
        self.base_url = "https://api.portkey.ai/v1"

    async def close(self) -> None:
        await self.client.aclose()

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"x-portkey-api-key": self.portkey_key}
        resp = await self.client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def chat(self, messages: List[Dict[str, str]], task: str = "reasoning") -> Dict[str, Any]:
        model_map = {
            "structured_output": ["claude-3-opus", "claude-3-sonnet"],
            "reasoning": ["gpt-4o", "gemini-1.5-pro"],
            "cost_efficient": ["llama-3-70b", "mixtral-8x7b"],
            "code_generation": ["deepseek-coder", "claude-3-opus"],
            "vision": ["gpt-4-vision", "claude-3-opus"],
        }
        models = model_map.get(task, ["gpt-4o"])
        for model in models:
            payload = {"messages": messages, "model": model}
            try:
                result = await self._post(payload)
                logger.info("Model %s succeeded", model)
                return result
            except Exception as exc:
                logger.warning("Model %s failed: %s", model, exc)
                continue
        raise RuntimeError("All models failed")
