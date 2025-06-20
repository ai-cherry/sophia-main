"""Natural Language Processor for AI Agent Control
Converts natural language commands into structured agent requests
"""

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import openai
from flask import Blueprint, Flask, jsonify, request

# Optional spacy import
try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None
from flask_cors import CORS

from .kong_ai_gateway import AgentRequest, AgentType, get_kong_gateway

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of intents the system can recognize"""

    DEPLOY_INFRASTRUCTURE = "deploy_infrastructure"
    SCALE_RESOURCES = "scale_resources"
    MONITOR_PERFORMANCE = "monitor_performance"
    ANALYZE_CONVERSATION = "analyze_conversation"
    CREATE_WORKFLOW = "create_workflow"
    UPDATE_CRM = "update_crm"
    GENERATE_REPORT = "generate_report"
    TROUBLESHOOT_ISSUE = "troubleshoot_issue"
    OPTIMIZE_COSTS = "optimize_costs"
    MANAGE_AGENTS = "manage_agents"


@dataclass
class ParsedIntent:
    """Parsed natural language intent"""

    intent: IntentType
    entities: Dict[str, Any]
    confidence: float
    original_text: str
    suggested_actions: List[str]
    required_parameters: List[str]
    context: Optional[Dict[str, Any]] = None


class NaturalLanguageProcessor:
    """Advanced NLP processor for AI agent control"""

    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Load spaCy model for NER
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found, using basic NLP")
                self.nlp = None
        else:
            logger.warning("spaCy not available, using basic NLP")
            self.nlp = None

        # Initialize conversation context
        self.conversation_context: Dict[str, Any] = {}

        # Intent patterns for quick matching
        self.intent_patterns = {
            IntentType.DEPLOY_INFRASTRUCTURE: [
                r"deploy.*infrastructure",
                r"create.*server",
                r"provision.*resources",
                r"set up.*environment",
                r"launch.*instance",
            ],
            IntentType.SCALE_RESOURCES: [
                r"scale.*up",
                r"scale.*down",
                r"increase.*capacity",
                r"reduce.*resources",
                r"auto.*scale",
            ],
            IntentType.MONITOR_PERFORMANCE: [
                r"monitor.*performance",
                r"check.*health",
                r"show.*metrics",
                r"performance.*dashboard",
                r"system.*status",
            ],
            IntentType.ANALYZE_CONVERSATION: [
                r"analyze.*conversation",
                r"conversation.*insights",
                r"call.*analysis",
                r"meeting.*summary",
                r"sentiment.*analysis",
            ],
            IntentType.CREATE_WORKFLOW: [
                r"create.*workflow",
                r"automate.*process",
                r"set up.*automation",
                r"build.*pipeline",
                r"workflow.*automation",
            ],
            IntentType.UPDATE_CRM: [
                r"update.*crm",
                r"sync.*contact",
                r"create.*lead",
                r"update.*deal",
                r"crm.*integration",
            ],
        }

        # Entity extraction patterns
        self.entity_patterns = {
            "service_type": r"(web app|database|api|microservice|frontend|backend)",
            "environment": r"(production|staging|development|dev|prod|test)",
            "cloud_provider": r"(aws|azure|gcp|lambda labs|digital ocean)",
            "scale": r"(small|medium|large|xl|2xl|micro|nano)",
            "time_range": r"(last hour|today|yesterday|last week|last month)",
            "priority": r"(high|medium|low|urgent|critical)",
        }

    async def process_natural_language(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> ParsedIntent:
        """Process natural language input and extract intent"""
        try:
            # Clean and normalize input
            cleaned_text = self._clean_text(text)

            # Extract intent using multiple methods
            intent = await self._extract_intent(cleaned_text)

            # Extract entities
            entities = await self._extract_entities(cleaned_text, intent)

            # Calculate confidence score
            confidence = await self._calculate_confidence(
                cleaned_text, intent, entities
            )

            # Generate suggested actions
            suggested_actions = await self._generate_suggested_actions(intent, entities)

            # Determine required parameters
            required_parameters = self._get_required_parameters(intent)

            return ParsedIntent(
                intent=intent,
                entities=entities,
                confidence=confidence,
                original_text=text,
                suggested_actions=suggested_actions,
                required_parameters=required_parameters,
                context=context,
            )

        except Exception as e:
            logger.error(f"Error processing natural language: {e}")
            # Return default intent with low confidence
            return ParsedIntent(
                intent=IntentType.MANAGE_AGENTS,
                entities={},
                confidence=0.1,
                original_text=text,
                suggested_actions=["clarify_request"],
                required_parameters=[],
                context=context,
            )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text"""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())

        # Convert to lowercase for processing
        text = text.lower()

        # Remove special characters but keep important punctuation
        text = re.sub(r"[^\w\s\-\.\,\?\!]", "", text)

        return text

    async def _extract_intent(self, text: str) -> IntentType:
        """Extract intent from text using pattern matching and AI"""
        # First try pattern matching for quick results
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent_type

        # If no pattern match, use AI for more complex intent recognition
        try:
            prompt = f"""
            Analyze the following text and determine the primary intent for an AI infrastructure management system.

            Text: "{text}"

            Available intents:
            - deploy_infrastructure: Deploy or create new infrastructure
            - scale_resources: Scale up or down existing resources
            - monitor_performance: Monitor system performance or health
            - analyze_conversation: Analyze conversations or calls
            - create_workflow: Create automated workflows
            - update_crm: Update CRM or customer data
            - generate_report: Generate reports or analytics
            - troubleshoot_issue: Troubleshoot problems
            - optimize_costs: Optimize costs or resources
            - manage_agents: Manage AI agents

            Return only the intent name.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1,
            )

            intent_str = response.choices[0].message.content.strip().lower()

            # Map response to IntentType
            for intent_type in IntentType:
                if intent_type.value in intent_str:
                    return intent_type

        except Exception as e:
            logger.error(f"AI intent extraction failed: {e}")

        # Default to manage_agents if nothing else matches
        return IntentType.MANAGE_AGENTS

    async def _extract_entities(self, text: str, intent: IntentType) -> Dict[str, Any]:
        """Extract entities from text"""
        entities = {}

        # Pattern-based entity extraction
        for entity_type, pattern in self.entity_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities[entity_type] = match.group(1)

        # Use spaCy for additional entity extraction if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    entities["organization"] = ent.text
                elif ent.label_ == "PERSON":
                    entities["person"] = ent.text
                elif ent.label_ == "GPE":
                    entities["location"] = ent.text
                elif ent.label_ == "MONEY":
                    entities["budget"] = ent.text
                elif ent.label_ == "DATE":
                    entities["date"] = ent.text

        # Intent-specific entity extraction
        if intent == IntentType.DEPLOY_INFRASTRUCTURE:
            # Look for infrastructure-specific entities
            if "database" in text:
                entities["requires_database"] = True
            if "load balancer" in text or "lb" in text:
                entities["requires_load_balancer"] = True
            if "ssl" in text or "https" in text:
                entities["requires_ssl"] = True

        elif intent == IntentType.SCALE_RESOURCES:
            # Look for scaling-specific entities
            scale_match = re.search(r"(\d+)\s*(instance|server|node)", text)
            if scale_match:
                entities["target_count"] = int(scale_match.group(1))

        elif intent == IntentType.ANALYZE_CONVERSATION:
            # Look for conversation-specific entities
            if "meeting" in text:
                entities["conversation_type"] = "meeting"
            elif "call" in text:
                entities["conversation_type"] = "call"
            elif "email" in text:
                entities["conversation_type"] = "email"

        return entities

    async def _calculate_confidence(
        self, text: str, intent: IntentType, entities: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the parsed intent"""
        confidence = 0.5  # Base confidence

        # Increase confidence if pattern matched
        for pattern in self.intent_patterns.get(intent, []):
            if re.search(pattern, text, re.IGNORECASE):
                confidence += 0.3
                break

        # Increase confidence based on entity extraction
        entity_bonus = min(len(entities) * 0.1, 0.3)
        confidence += entity_bonus

        # Decrease confidence for very short or unclear text
        if len(text.split()) < 3:
            confidence -= 0.2

        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

    async def _generate_suggested_actions(
        self, intent: IntentType, entities: Dict[str, Any]
    ) -> List[str]:
        """Generate suggested actions based on intent and entities"""
        if intent == IntentType.DEPLOY_INFRASTRUCTURE:
            actions = [
                "generate_infrastructure_code",
                "estimate_costs",
                "create_deployment_plan",
            ]
            if entities.get("requires_database"):
                actions.append("configure_database")
            if entities.get("requires_ssl"):
                actions.append("setup_ssl_certificate")

        elif intent == IntentType.SCALE_RESOURCES:
            actions = [
                "analyze_current_usage",
                "calculate_scaling_requirements",
                "update_auto_scaling_policies",
            ]
            if entities.get("target_count"):
                actions.append("scale_to_target_count")

        elif intent == IntentType.MONITOR_PERFORMANCE:
            actions = [
                "fetch_system_metrics",
                "generate_performance_report",
                "check_alert_status",
            ]

        elif intent == IntentType.ANALYZE_CONVERSATION:
            actions = [
                "extract_conversation_insights",
                "analyze_sentiment",
                "identify_action_items",
            ]
            if entities.get("conversation_type") == "meeting":
                actions.append("generate_meeting_summary")

        elif intent == IntentType.CREATE_WORKFLOW:
            actions = ["design_workflow_steps", "configure_triggers", "test_workflow"]

        elif intent == IntentType.UPDATE_CRM:
            actions = ["identify_crm_records", "prepare_updates", "sync_data"]

        else:
            actions = ["clarify_request", "provide_help", "show_available_commands"]

        return actions

    def _get_required_parameters(self, intent: IntentType) -> List[str]:
        """Get required parameters for each intent type"""
        parameter_map = {
            IntentType.DEPLOY_INFRASTRUCTURE: ["service_type", "environment"],
            IntentType.SCALE_RESOURCES: ["resource_id", "scale_direction"],
            IntentType.MONITOR_PERFORMANCE: ["time_range"],
            IntentType.ANALYZE_CONVERSATION: ["conversation_id"],
            IntentType.CREATE_WORKFLOW: ["workflow_description"],
            IntentType.UPDATE_CRM: ["record_type", "record_id"],
            IntentType.GENERATE_REPORT: ["report_type", "time_range"],
            IntentType.TROUBLESHOOT_ISSUE: ["issue_description"],
            IntentType.OPTIMIZE_COSTS: ["resource_type"],
            IntentType.MANAGE_AGENTS: ["agent_action"],
        }

        return parameter_map.get(intent, [])

    async def convert_to_agent_requests(
        self, parsed_intent: ParsedIntent
    ) -> List[AgentRequest]:
        """Convert parsed intent to specific agent requests"""
        requests = []

        try:
            if parsed_intent.intent == IntentType.DEPLOY_INFRASTRUCTURE:
                # Create Pulumi infrastructure request
                requests.append(
                    AgentRequest(
                        agent_type=AgentType.PULUMI_INFRASTRUCTURE,
                        action="generate_infrastructure",
                        parameters={
                            "description": parsed_intent.original_text,
                            "service_type": parsed_intent.entities.get(
                                "service_type", "web_application"
                            ),
                            "environment": parsed_intent.entities.get(
                                "environment", "development"
                            ),
                            "scale": parsed_intent.entities.get("scale", "medium"),
                        },
                        context=parsed_intent.context,
                    )
                )

            elif parsed_intent.intent == IntentType.ANALYZE_CONVERSATION:
                # Create Gong conversation analysis request
                requests.append(
                    AgentRequest(
                        agent_type=AgentType.GONG_CONVERSATION,
                        action="analyze_conversation",
                        parameters={
                            "conversation_id": parsed_intent.entities.get(
                                "conversation_id"
                            ),
                            "analysis_type": "full",
                        },
                        context=parsed_intent.context,
                    )
                )

                # Also update CRM with insights
                requests.append(
                    AgentRequest(
                        agent_type=AgentType.HUBSPOT_BREEZE,
                        action="update_contact",
                        parameters={
                            "contact_id": parsed_intent.entities.get("contact_id"),
                            "updates": {"last_interaction": datetime.now().isoformat()},
                        },
                        context=parsed_intent.context,
                    )
                )

            elif parsed_intent.intent == IntentType.CREATE_WORKFLOW:
                # Create Bardeen workflow request
                requests.append(
                    AgentRequest(
                        agent_type=AgentType.BARDEEN_WORKFLOW,
                        action="create_workflow",
                        parameters={
                            "description": parsed_intent.original_text,
                            "triggers": parsed_intent.entities.get("triggers", []),
                            "actions": parsed_intent.entities.get("actions", []),
                        },
                        context=parsed_intent.context,
                    )
                )

            elif parsed_intent.intent == IntentType.MONITOR_PERFORMANCE:
                # Create Arize monitoring request
                requests.append(
                    AgentRequest(
                        agent_type=AgentType.ARIZE_EVALUATION,
                        action="monitor_performance",
                        parameters={
                            "time_range": parsed_intent.entities.get(
                                "time_range", "1h"
                            ),
                            "metrics": ["latency", "accuracy", "cost"],
                        },
                        context=parsed_intent.context,
                    )
                )

            elif parsed_intent.intent == IntentType.SCALE_RESOURCES:
                # Create infrastructure scaling request
                requests.append(
                    AgentRequest(
                        agent_type=AgentType.PULUMI_INFRASTRUCTURE,
                        action="scale_resources",
                        parameters={
                            "resource_type": parsed_intent.entities.get(
                                "resource_type", "compute"
                            ),
                            "scale_direction": (
                                "up" if "up" in parsed_intent.original_text else "down"
                            ),
                            "target_count": parsed_intent.entities.get("target_count"),
                        },
                        context=parsed_intent.context,
                    )
                )

            # If no specific requests generated, create a general NL processing request
            if not requests:
                requests.append(
                    AgentRequest(
                        agent_type=AgentType.NATURAL_LANGUAGE,
                        action="generate_response",
                        parameters={
                            "query": parsed_intent.original_text,
                            "intent": parsed_intent.intent.value,
                            "entities": parsed_intent.entities,
                        },
                        context=parsed_intent.context,
                    )
                )

        except Exception as e:
            logger.error(f"Error converting intent to agent requests: {e}")
            # Return error handling request
            requests.append(
                AgentRequest(
                    agent_type=AgentType.NATURAL_LANGUAGE,
                    action="handle_error",
                    parameters={
                        "error": str(e),
                        "original_text": parsed_intent.original_text,
                    },
                    context=parsed_intent.context,
                )
            )

        return requests

    async def process_and_execute(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process natural language and execute corresponding agent requests"""
        try:
            # Parse the natural language input
            parsed_intent = await self.process_natural_language(text, context)

            # Convert to agent requests
            agent_requests = await self.convert_to_agent_requests(parsed_intent)

            # Execute agent requests
            results = []
            for agent_request in agent_requests:
                try:
                    response = await get_kong_gateway().route_request(agent_request)
                    results.append(
                        {
                            "agent_type": agent_request.agent_type.value,
                            "action": agent_request.action,
                            "success": response.success,
                            "data": response.data,
                            "error": response.error,
                            "execution_time": response.execution_time,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "agent_type": agent_request.agent_type.value,
                            "action": agent_request.action,
                            "success": False,
                            "error": str(e),
                        }
                    )

            return {
                "success": True,
                "parsed_intent": {
                    "intent": parsed_intent.intent.value,
                    "confidence": parsed_intent.confidence,
                    "entities": parsed_intent.entities,
                    "suggested_actions": parsed_intent.suggested_actions,
                },
                "agent_results": results,
                "summary": self._generate_summary(parsed_intent, results),
            }

        except Exception as e:
            logger.error(f"Error in process_and_execute: {e}")
            return {"success": False, "error": str(e), "original_text": text}

    def _generate_summary(
        self, parsed_intent: ParsedIntent, results: List[Dict[str, Any]]
    ) -> str:
        """Generate a human-readable summary of the execution"""
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        summary = f"Processed request with {parsed_intent.confidence:.0%} confidence. "
        summary += f"Intent: {parsed_intent.intent.value.replace('_', ' ').title()}. "

        if successful_results:
            summary += f"Successfully executed {len(successful_results)} action(s). "

        if failed_results:
            summary += f"Failed to execute {len(failed_results)} action(s). "

        return summary


# Initialize NLP processor
nlp_processor = NaturalLanguageProcessor()

# Flask Blueprint for NLP API
nlp_bp = Blueprint("nlp", __name__, url_prefix="/api/nlp")


@nlp_bp.route("/process", methods=["POST"])
async def process_natural_language():
    """Process natural language input"""
    try:
        data = request.get_json()
        text = data.get("text", "")
        context = data.get("context")

        if not text:
            return jsonify({"success": False, "error": "Text input is required"}), 400

        result = await nlp_processor.process_and_execute(text, context)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@nlp_bp.route("/parse", methods=["POST"])
async def parse_intent():
    """Parse natural language intent without execution"""
    try:
        data = request.get_json()
        text = data.get("text", "")
        context = data.get("context")

        if not text:
            return jsonify({"success": False, "error": "Text input is required"}), 400

        parsed_intent = await nlp_processor.process_natural_language(text, context)

        return jsonify(
            {
                "success": True,
                "intent": parsed_intent.intent.value,
                "entities": parsed_intent.entities,
                "confidence": parsed_intent.confidence,
                "suggested_actions": parsed_intent.suggested_actions,
                "required_parameters": parsed_intent.required_parameters,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def create_nlp_app():
    """Create Flask app with NLP integration"""
    app = Flask(__name__)
    CORS(app, origins="*")

    app.register_blueprint(nlp_bp)

    return app


if __name__ == "__main__":
    app = create_nlp_app()
    app.run(host="0.0.0.0", port=5002, debug=True)
