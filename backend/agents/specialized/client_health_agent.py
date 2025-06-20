import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

import snowflake.connector

from ...core.config_manager import get_secret
from ..core.base_agent import (
    AgentCapability,
    AgentConfig,
    BaseAgent,
    Task,
    create_agent_response,
)

logger = logging.getLogger(__name__)


class ClientHealthAgent(BaseAgent):
    """Monitors client health based on various data sources and predicts churn risk."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.snowflake_conn = None

    async def _get_snowflake_connection(self):
        # ... (same as in SalesCoachAgent, can be refactored into a shared utility)
        if self.snowflake_conn and self.snowflake_conn.is_open():
            return self.snowflake_conn
        try:
            sf_config = {
                "account": await get_secret("account", "snowflake"),
                "user": await get_secret("user", "snowflake"),
                "password": await get_secret("password", "snowflake"),
                "warehouse": "COMPUTE_WH",
                "database": "SOPHIA_DB",
                "schema": "RAW_DATA",
            }
            self.snowflake_conn = snowflake.connector.connect(**sf_config)
            return self.snowflake_conn
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            return None

    async def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="calculate_health_score",
                description="Calculates the health score for a given client.",
                input_types=["client_id"],
                output_types=["health_score_report"],
                estimated_duration=30.0,
            )
        ]

    def _calculate_health_score(
        self, interaction_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """A simple rule-based algorithm to calculate a client health score."""
        score = 70  # Start with a baseline score
        positive_factors = []
        risk_factors = []

        if not interaction_history:
            risk_factors.append("No recent interactions found.")
            return {"score": 40, "positive_factors": [], "risk_factors": risk_factors}

        # Factor 1: Recency of last interaction
        last_interaction_date = max(
            row["CONVERSATION_DATETIME"] for row in interaction_history
        )
        days_since_last_interaction = (
            datetime.now(last_interaction_date.tzinfo) - last_interaction_date
        ).days

        if days_since_last_interaction > 30:
            score -= 20
            risk_factors.append(
                f"No interaction for {days_since_last_interaction} days."
            )
        elif days_since_last_interaction < 7:
            score += 10
            positive_factors.append("Interaction within the last week.")

        # Factor 2: Sentiment of interactions
        # This is a placeholder; real implementation would use tracker sentiment
        # or NLP on transcripts.
        has_negative_sentiment = any(
            "complaint" in (t.get("TRACKER_NAME") or "").lower()
            for row in interaction_history
            for t in row.get("trackers", [])
        )
        if has_negative_sentiment:
            score -= 15
            risk_factors.append(
                "Negative sentiment detected in trackers (e.g., complaints)."
            )

        # Factor 3: Interaction frequency
        if len(interaction_history) > 5:
            score += 10
            positive_factors.append("High interaction frequency.")

        return {
            "score": max(0, min(100, score)),
            "positive_factors": positive_factors,
            "risk_factors": risk_factors,
        }

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Processes a task to calculate a client's health score."""
        if task.task_type == "calculate_health_score":
            client_id = task.task_data.get("client_id")
            if not client_id:
                return await create_agent_response(
                    False, error="client_id is required."
                )

            conn = await self._get_snowflake_connection()
            if not conn:
                return await create_agent_response(
                    False, error="Could not connect to database."
                )

            try:
                with conn.cursor(snowflake.connector.DictCursor) as cursor:
                    # This query is a placeholder. A real implementation would be more complex,
                    # joining with an entities table to resolve client_id to conversation participants.
                    query = """
                    SELECT c.conversation_datetime, t.tracker_name, t.tracker_sentiment
                    FROM GONG_CONVERSATIONS c
                    JOIN GONG_CONVERSATION_CONTEXTS ctx ON c.conversation_key = ctx.conversation_key
                    LEFT JOIN GONG_CONVERSATION_TRACKERS t ON c.conversation_key = t.conversation_key
                    WHERE ctx.crm_object_type = 'Account' AND ctx.crm_object_id = %s
                    AND c.conversation_datetime > DATEADD(day, -90, CURRENT_TIMESTAMP())
                    ORDER BY c.conversation_datetime DESC;
                    """
                    cursor.execute(query, (client_id,))
                    interaction_history = cursor.fetchall()

                # Calculate score
                health_analysis = self._calculate_health_score(interaction_history)

                # TODO: Fetch and incorporate external data from Apify/CoStar

                # Store the new score in the database
                score_id = f"score_{uuid.uuid4().hex}"
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO CLIENT_HEALTH_SCORES (score_id, client_entity_id, score, positive_factors, risk_factors)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                        (
                            score_id,
                            client_id,
                            health_analysis["score"],
                            json.dumps(health_analysis["positive_factors"]),
                            json.dumps(health_analysis["risk_factors"]),
                        ),
                    )

                report = {
                    "client_id": client_id,
                    "health_score": health_analysis["score"],
                    "summary": "Client health score calculated successfully.",
                    "positive_factors": health_analysis["positive_factors"],
                    "risk_factors": health_analysis["risk_factors"],
                }

                return await create_agent_response(True, data=report)
            except Exception as e:
                logger.error(
                    f"Error calculating health score for client {client_id}: {e}"
                )
                return await create_agent_response(False, error=str(e))
        else:
            return await create_agent_response(
                False, error=f"Unknown task type: {task.task_type}"
            )
