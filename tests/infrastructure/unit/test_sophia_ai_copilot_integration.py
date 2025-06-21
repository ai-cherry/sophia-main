"""Unit tests for the Sophia AI Copilot integration."""

import os
import sys

# Add project root to path to allow imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)

from infrastructure.sophia_ai_copilot_integration import SophiaAICopilot


class TestSophiaAICopilotIntegration:
    """Tests for basic Copilot initialization and logic."""

    def test_initialization(self):
        copilot = SophiaAICopilot()
        assert copilot.context["monthly_budget_usd"] == 1000
        assert copilot.budget == 1000

    def test_analysis_and_suggestions(self):
        copilot = SophiaAICopilot()
        analysis = copilot.analyze_resources()
        assert isinstance(analysis, list)
        suggestions = copilot.generate_optimization_suggestions(analysis)
        assert any("GPU" in s for s in suggestions)
        assert any("$" in s for s in suggestions)

    def test_scaling_trigger(self):
        copilot = SophiaAICopilot()
        assert copilot.trigger_scaling_via_pulumi("scale up") is True
        assert copilot.optimize_lambda_labs_gpu_utilization() is True
