"""COSTAR methodology agent."""

from __future__ import annotations

from typing import Any, Dict

from .core.base_agent import BaseAgent


class COSTARAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="costar")

    async def analyze(self, context: str, objective: str) -> Dict[str, Any]:
        prompt = (
            f"Context: {context}\nObjective: {objective}\n"
            "Provide a structured response following the COSTAR method."
        )
        response = await self.llm.chat([{"role": "user", "content": prompt}])
        return response
