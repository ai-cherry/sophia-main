"""Integration tests for the Sophia automation API."""

import os
import shutil
import sys
import uuid

import pytest

# Add project root to import path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)

from infrastructure.sophia_automation_api import create_stack


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_stack_preview(test_env_manager):
    """Ensure a stack can be created in preview mode without deploying resources."""
    stack_name = f"preview-{uuid.uuid4().hex[:8]}"

    def program():
        # empty Pulumi program for preview
        pass

    if shutil.which("pulumi") is None:
        pytest.skip("Pulumi CLI not installed")

    os.environ.setdefault("PULUMI_ACCESS_TOKEN", "test-token")

    result = await create_stack(stack_name, program, preview=True)

    assert hasattr(result, "change_summary")

    test_env_manager.cleanup_test_stack(stack_name)
