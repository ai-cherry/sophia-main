"""Metrics collection utilities."""

from __future__ import annotations

import time
from typing import Any, Dict


class EnhancedMetrics:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}

    def record(self, name: str, value: Any) -> None:
        self.data[name] = {"value": value, "timestamp": time.time()}
