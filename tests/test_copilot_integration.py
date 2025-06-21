from datetime import datetime, timedelta

from backend.integrations.sophia_ai_copilot_integration import (
    WorkloadRecord,
    WorkloadMetrics,
    CostTracker,
    CostConfig,
    PredictiveScaler,
)


def test_cost_tracking_within_budget():
    config = CostConfig(
        budget=1000.0,
        snowflake_cost_per_query=0.5,
        pinecone_cost_per_query=0.2,
        ai_cost_per_call=0.05,
    )
    tracker = CostTracker(config)

    tracker.add_usage(WorkloadRecord(timestamp=datetime.utcnow(), snowflake_queries=1000))
    assert tracker.within_budget()
    assert tracker.remaining_budget() == config.budget - 500

    tracker.add_usage(WorkloadRecord(timestamp=datetime.utcnow(), snowflake_queries=1500))
    assert not tracker.within_budget()
    assert tracker.remaining_budget() < 0


def test_scaling_trigger():
    metrics = WorkloadMetrics()
    now = datetime.utcnow()
    for i in range(10):
        metrics.add_record(
            WorkloadRecord(
                timestamp=now - timedelta(minutes=5 * i),
                snowflake_queries=100,
                pinecone_queries=50,
                ai_calls=50,
            )
        )

    scaler = PredictiveScaler(metrics, threshold=0.8)
    recommendation = scaler.scaling_recommendation(current_capacity=150)
    assert recommendation > 150
