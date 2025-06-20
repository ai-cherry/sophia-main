import logging
from typing import Any, Dict, List, Optional

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


class SalesCoachAgent(BaseAgent):
    """Analyzes sales calls to provide coaching and performance insights."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.snowflake_conn = None

    async def _get_snowflake_connection(self):
        """Establishes a connection to Snowflake."""
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
            logger.info("Successfully connected to Snowflake.")
            return self.snowflake_conn
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            return None

    async def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_gong_call",
                description="Analyzes a specific Gong call for sales coaching insights.",
                input_types=["gong_call_id"],
                output_types=["coaching_report"],
                estimated_duration=60.0,
            )
        ]

    async def _get_coaching_report_data(
        self, gong_call_id: str
    ) -> Optional[Dict[str, Any]]:
        """Queries Snowflake for all data related to a Gong call to build a coaching report."""
        conn = await self._get_snowflake_connection()
        if not conn:
            return None

        try:
            with conn.cursor(snowflake.connector.DictCursor) as cursor:
                # 1. Get base call info
                cursor.execute(
                    "SELECT * FROM GONG_CALLS WHERE conversation_id = %s",
                    (gong_call_id,),
                )
                call_info = cursor.fetchone()
                if not call_info:
                    return None

                conversation_key = call_info["CONVERSATION_KEY"]

                # 2. Get participants and talk ratios
                cursor.execute(
                    "SELECT * FROM GONG_PARTICIPANTS WHERE conversation_key = %s",
                    (conversation_key,),
                )
                participants = cursor.fetchall()

                # 3. Get trackers and their sentiment
                cursor.execute(
                    "SELECT * FROM GONG_CONVERSATION_TRACKERS WHERE conversation_key = %s",
                    (conversation_key,),
                )
                trackers = cursor.fetchall()

                # 4. Get transcript text
                cursor.execute(
                    "SELECT transcript_text FROM GONG_CALL_TRANSCRIPTS WHERE conversation_key = %s",
                    (conversation_key,),
                )
                transcript = cursor.fetchone()

                return {
                    "call_info": call_info,
                    "participants": participants,
                    "trackers": trackers,
                    "transcript": transcript["TRANSCRIPT_TEXT"] if transcript else "",
                }
        except Exception as e:
            logger.error(f"Failed to query coaching data for call {gong_call_id}: {e}")
            return None

    def _analyze_report_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes the raw data to produce coaching insights."""
        analysis = {}

        # Calculate talk/listen ratio for the owner
        owner_id = report_data["call_info"]["OWNER_ID"]
        owner_talk_time = 0
        total_talk_time = 0
        for p in report_data["participants"]:
            if p["TALK_TIME_PERCENTAGE"]:
                total_talk_time += p["TALK_TIME_PERCENTAGE"]
                if p["PARTICIPANT_ID"] == owner_id:
                    owner_talk_time = p["TALK_TIME_PERCENTAGE"]

        analysis["talk_listen_ratio"] = (
            f"{owner_talk_time}% / {100-owner_talk_time}%"
            if total_talk_time > 0
            else "N/A"
        )

        # Summarize trackers
        analysis["positive_topics"] = [
            t["TRACKER_NAME"]
            for t in report_data["trackers"]
            if t["TRACKER_SENTIMENT"] == "positive"
        ]
        analysis["negative_topics"] = [
            t["TRACKER_NAME"]
            for t in report_data["trackers"]
            if t["TRACKER_SENTIMENT"] == "negative"
        ]

        # Other metrics
        analysis["question_count"] = report_data["call_info"].get(
            "QUESTION_COMPANY_COUNT", 0
        ) + report_data["call_info"].get("QUESTION_NON_COMPANY_COUNT", 0)
        analysis["spotlight_summary"] = report_data["call_info"].get(
            "CALL_SPOTLIGHT_BRIEF"
        )

        return analysis

    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Processes a task to analyze a Gong call."""
        if task.task_type == "analyze_gong_call":
            gong_call_id = task.task_data.get("gong_call_id")
            if not gong_call_id:
                return await create_agent_response(
                    False, error="gong_call_id is required."
                )

            raw_data = await self._get_coaching_report_data(gong_call_id)
            if not raw_data:
                return await create_agent_response(
                    False, error=f"Could not retrieve data for call_id {gong_call_id}"
                )

            # Analyze the data to generate insights
            analysis = self._analyze_report_data(raw_data)

            # Assemble the final report
            report = {
                "gong_call_id": gong_call_id,
                "call_url": raw_data["call_info"]["CALL_URL"],
                "summary": analysis["spotlight_summary"],
                "metrics": {
                    "talk_listen_ratio": analysis["talk_listen_ratio"],
                    "question_count": analysis["question_count"],
                },
                "positive_topics_discussed": analysis["positive_topics"],
                "negative_topics_discussed": analysis["negative_topics"],
            }

            return await create_agent_response(True, data=report)
        else:
            return await create_agent_response(
                False, error=f"Unknown task type: {task.task_type}"
            )
