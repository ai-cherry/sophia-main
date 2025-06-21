"""Automation utilities for managing Sophia AI infrastructure with Pulumi.

This module provides high-level functions for programmatic stack creation,
scaling, and cost optimisation. It integrates with the Pulumi ESC environment
configuration via :class:`~infrastructure.pulumi_esc.PulumiESCManager`.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from pulumi import automation as auto

from .pulumi_esc import PulumiESCManager

logger = logging.getLogger(__name__)


async def create_stack(
    stack_name: str,
    program: Callable[[], None],
    *,
    config: Optional[Dict[str, Any]] = None,
    preview: bool = False,
) -> auto.UpResult | auto.PreviewResult:
    """Create or select a Pulumi stack and optionally deploy it.

    The stack will automatically be configured with values fetched from Pulumi
    ESC if available. Additional configuration can be supplied via ``config``.

    Args:
        stack_name: Name of the stack to create or select.
        program: Pulumi program to run.
        config: Additional configuration values.
        preview: If ``True`` run ``preview`` instead of ``up``.

    Returns:
        The result of ``stack.up()`` or ``stack.preview()``.
    """
    logger.info("Creating stack '%s'", stack_name)

    esc = PulumiESCManager()
    await esc.initialize()

    stack = auto.create_or_select_stack(
        stack_name=stack_name, project_name="sophia-iac", program=program
    )

    env = (
        await esc.get_secret("PULUMI_ENVIRONMENT")
        or (config or {}).get("environment")
        or "development"
    )
    await stack.set_config("environment", auto.ConfigValue(value=env))

    if config:
        for key, value in config.items():
            await stack.set_config(key, auto.ConfigValue(value=str(value)))

    if preview:
        logger.info("Previewing stack '%s'", stack_name)
        return await stack.preview(on_output=logger.debug)

    logger.info("Deploying stack '%s'", stack_name)
    return await stack.up(on_output=logger.debug)


async def scale_stack(stack_name: str, *, replicas: int) -> auto.UpResult:
    """Dynamically scale stack resources.

    The implementation assumes the stack respects a ``replicas`` configuration
    value. This value is updated and the stack is deployed.
    """
    logger.info("Scaling stack '%s' to %s replicas", stack_name, replicas)

    stack = auto.select_stack(
        stack_name=stack_name, project_name="sophia-iac", program=lambda: None
    )
    await stack.set_config("replicas", auto.ConfigValue(value=str(replicas)))
    return await stack.up(on_output=logger.debug)


async def optimize_costs(stack_name: str) -> auto.UpResult:
    """Apply cost optimisation settings to the stack and deploy.

    This sets a ``cost_optimization`` flag in stack configuration which can be
    consumed by the Pulumi program to adjust resources.
    """
    logger.info("Enabling cost optimisation for stack '%s'", stack_name)

    stack = auto.select_stack(
        stack_name=stack_name, project_name="sophia-iac", program=lambda: None
    )
    await stack.set_config("cost_optimization", auto.ConfigValue(value="true"))
    return await stack.up(on_output=logger.debug)
