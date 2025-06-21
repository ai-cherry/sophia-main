"""Sophia AI Copilot Integration

This module analyzes BI workloads across Snowflake, Pinecone and AI services.
It provides predictive scaling recommendations based on historical demand and
tracks service costs to ensure the monthly budget is not exceeded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class WorkloadRecord:
    """Single workload usage record."""

    timestamp: datetime
    snowflake_queries: int = 0
    pinecone_queries: int = 0
    ai_calls: int = 0


@dataclass
class CostConfig:
    """Configuration for cost tracking."""

    budget: float = 1000.0
    snowflake_cost_per_query: float = 0.0005
    pinecone_cost_per_query: float = 0.0001
    ai_cost_per_call: float = 0.0002


@dataclass
class WorkloadMetrics:
    """Stores historical workload records."""

    history: List[WorkloadRecord] = field(default_factory=list)

    def add_record(self, record: WorkloadRecord) -> None:
        logger.debug("Adding workload record: %s", record)
        self.history.append(record)

    def recent_records(self, window: timedelta) -> List[WorkloadRecord]:
        cutoff = datetime.utcnow() - window
        return [r for r in self.history if r.timestamp >= cutoff]

    def average_demand(self, window: timedelta) -> float:
        records = self.recent_records(window)
        if not records:
            return 0.0
        total = sum(
            r.snowflake_queries + r.pinecone_queries + r.ai_calls for r in records
        )
        return total / len(records)


class CostTracker:
    """Tracks cost of workloads and validates budget."""

    def __init__(self, config: CostConfig | None = None) -> None:
        self.config = config or CostConfig()
        self.monthly_cost = 0.0

    def add_usage(self, record: WorkloadRecord) -> None:
        cost = (
            record.snowflake_queries * self.config.snowflake_cost_per_query
            + record.pinecone_queries * self.config.pinecone_cost_per_query
            + record.ai_calls * self.config.ai_cost_per_call
        )
        logger.debug("Adding cost %.4f for record %s", cost, record)
        self.monthly_cost += cost

    def within_budget(self) -> bool:
        return self.monthly_cost <= self.config.budget

    def remaining_budget(self) -> float:
        return self.config.budget - self.monthly_cost


class PredictiveScaler:
    """Simple predictive scaler using moving average."""

    def __init__(self, metrics: WorkloadMetrics, threshold: float = 0.8) -> None:
        self.metrics = metrics
        self.threshold = threshold

    def predict_demand(self, window: timedelta = timedelta(hours=1)) -> float:
        return self.metrics.average_demand(window)

    def scaling_recommendation(self, current_capacity: int) -> int:
        predicted = self.predict_demand()
        logger.debug(
            "Predicted demand %.2f with current capacity %d", predicted, current_capacity
        )
        if predicted > current_capacity * self.threshold:
            return current_capacity + 1
        if predicted < current_capacity * self.threshold / 2 and current_capacity > 1:
            return current_capacity - 1
        return current_capacity
