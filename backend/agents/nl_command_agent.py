"""Natural language command processing agent."""

from __future__ import annotations

from typing import Any, Dict, List

from .core.base_agent import BaseAgent
from ..integrations.workflow_orchestrator import N8nWorkflowOrchestrator


class NLCommandAgent(BaseAgent):
    """Agent that parses and executes natural language commands."""

    def __init__(self, orchestrator: N8nWorkflowOrchestrator) -> None:
        super().__init__(name="nl_command")
        self.orchestrator = orchestrator

    async def handle(self, command: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "Parse user command and output JSON instructions"},
            {"role": "user", "content": command},
        ]
        plan = await self.llm.chat(messages)
        workflow_name = plan.get("workflow", "")
        inputs = plan.get("inputs", {})
        if workflow_name:
            result = await self.orchestrator.execute_workflow(workflow_name, inputs)
            return {"result": result}
        return {"plan": plan}
