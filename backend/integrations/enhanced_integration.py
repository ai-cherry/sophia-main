"""
Enhanced Sophia AI Integration Module
Bardeen + Arize + Enhanced Portkey Integration
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import requests
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationConfig:
    """Configuration for enhanced integrations"""
    bardeen_id: str
    arize_api_key: str
    portkey_api_key: str
    environment: str = "production"

class BardeenWorkflowManager:
    """Bardeen automation workflow management"""
    
    def __init__(self, bardeen_id: str):
        self.bardeen_id = bardeen_id
        self.base_url = "https://api.bardeen.ai/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {bardeen_id}",
            "Content-Type": "application/json"
        })
    
    async def execute_workflow(self, workflow_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Bardeen workflow with provided data"""
        try:
            payload = {
                "workflow": workflow_name,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(
                f"{self.base_url}/workflows/execute",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Bardeen workflow {workflow_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Bardeen workflow execution failed: {str(e)}")
            raise
    
    async def sync_gong_to_hubspot(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Gong.io call data to HubSpot"""
        workflow_data = {
            "call_id": call_data.get("call_id"),
            "participants": call_data.get("participants", []),
            "duration": call_data.get("duration"),
            "sentiment_score": call_data.get("sentiment_score"),
            "key_topics": call_data.get("key_topics", []),
            "action_items": call_data.get("action_items", []),
            "deal_id": call_data.get("deal_id"),
            "contact_ids": call_data.get("contact_ids", [])
        }
        
        return await self.execute_workflow("gong_to_hubspot_sync", workflow_data)
    
    async def automate_lead_enrichment(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Automate lead enrichment process"""
        enrichment_data = {
            "email": lead_data.get("email"),
            "company": lead_data.get("company"),
            "name": lead_data.get("name"),
            "source": lead_data.get("source"),
            "enrichment_fields": [
                "company_size",
                "industry",
                "revenue",
                "technologies",
                "social_profiles",
                "contact_info"
            ]
        }
        
        return await self.execute_workflow("automated_lead_enrichment", enrichment_data)
    
    async def slack_team_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send automated Slack notifications to team"""
        slack_data = {
            "channel": notification_data.get("channel", "#sales-team"),
            "message": notification_data.get("message"),
            "priority": notification_data.get("priority", "normal"),
            "attachments": notification_data.get("attachments", []),
            "mention_users": notification_data.get("mention_users", [])
        }
        
        return await self.execute_workflow("slack_team_notification", slack_data)

class ArizeMonitoringManager:
    """Arize AI monitoring and observability management"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.arize.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    async def log_model_prediction(self, model_id: str, prediction_data: Dict[str, Any]) -> bool:
        """Log model prediction for monitoring"""
        try:
            payload = {
                "model_id": model_id,
                "prediction_id": prediction_data.get("prediction_id"),
                "features": prediction_data.get("features", {}),
                "prediction": prediction_data.get("prediction"),
                "actual": prediction_data.get("actual"),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": prediction_data.get("metadata", {})
            }
            
            response = self.session.post(
                f"{self.base_url}/models/{model_id}/predictions",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Logged prediction for model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log prediction: {str(e)}")
            return False
    
    async def track_sophia_ai_response(self, response_data: Dict[str, Any]) -> bool:
        """Track Sophia AI response quality and performance"""
        prediction_data = {
            "prediction_id": response_data.get("request_id"),
            "features": {
                "prompt_length": len(response_data.get("prompt", "")),
                "model_used": response_data.get("model", "unknown"),
                "response_time": response_data.get("response_time"),
                "user_context": response_data.get("user_context", {}),
                "business_domain": response_data.get("business_domain", "general")
            },
            "prediction": response_data.get("response"),
            "actual": response_data.get("user_feedback"),
            "metadata": {
                "user_satisfaction": response_data.get("user_satisfaction"),
                "accuracy_score": response_data.get("accuracy_score"),
                "relevance_score": response_data.get("relevance_score")
            }
        }
        
        return await self.log_model_prediction("sophia_ai_responses", prediction_data)
    
    async def monitor_business_intelligence(self, insight_data: Dict[str, Any]) -> bool:
        """Monitor business intelligence quality and accuracy"""
        prediction_data = {
            "prediction_id": insight_data.get("insight_id"),
            "features": {
                "data_sources": insight_data.get("data_sources", []),
                "analysis_type": insight_data.get("analysis_type"),
                "data_quality_score": insight_data.get("data_quality_score"),
                "confidence_level": insight_data.get("confidence_level"),
                "business_context": insight_data.get("business_context", {})
            },
            "prediction": insight_data.get("insight"),
            "actual": insight_data.get("actual_outcome"),
            "metadata": {
                "business_impact": insight_data.get("business_impact"),
                "accuracy_score": insight_data.get("accuracy_score"),
                "actionability_score": insight_data.get("actionability_score")
            }
        }
        
        return await self.log_model_prediction("sophia_business_intelligence", prediction_data)
    
    async def create_performance_alert(self, alert_config: Dict[str, Any]) -> bool:
        """Create performance monitoring alert"""
        try:
            payload = {
                "alert_name": alert_config.get("name"),
                "model_id": alert_config.get("model_id"),
                "metric": alert_config.get("metric"),
                "threshold": alert_config.get("threshold"),
                "condition": alert_config.get("condition", "less_than"),
                "notification_channels": alert_config.get("notification_channels", [])
            }
            
            response = self.session.post(
                f"{self.base_url}/alerts",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Created alert: {alert_config.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
            return False

class EnhancedPortkeyGateway:
    """Enhanced Portkey gateway with Arize monitoring integration"""
    
    def __init__(self, portkey_api_key: str, arize_manager: ArizeMonitoringManager):
        self.portkey_api_key = portkey_api_key
        self.arize_manager = arize_manager
        self.base_url = "https://api.portkey.ai/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {portkey_api_key}",
            "Content-Type": "application/json"
        })
    
    async def enhanced_completion(self, prompt: str, model: str = "gpt-4", **kwargs) -> Dict[str, Any]:
        """Enhanced completion with monitoring and optimization"""
        start_time = datetime.utcnow()
        request_id = f"req_{int(start_time.timestamp())}"
        
        try:
            # Prepare request payload
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "metadata": {
                    "request_id": request_id,
                    "arize_tracking": True
                },
                **kwargs
            }
            
            # Execute request through Portkey
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            result = response.json()
            
            # Track with Arize
            await self.arize_manager.track_sophia_ai_response({
                "request_id": request_id,
                "prompt": prompt,
                "model": model,
                "response": result.get("choices", [{}])[0].get("message", {}).get("content"),
                "response_time": response_time,
                "user_context": kwargs.get("user_context", {}),
                "business_domain": kwargs.get("business_domain", "general")
            })
            
            logger.info(f"Enhanced completion completed in {response_time:.2f}s")
            return {
                "response": result,
                "request_id": request_id,
                "response_time": response_time,
                "model_used": model
            }
            
        except Exception as e:
            logger.error(f"Enhanced completion failed: {str(e)}")
            raise
    
    async def get_usage_analytics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get usage analytics from Portkey"""
        try:
            response = self.session.get(
                f"{self.base_url}/analytics/usage",
                params={"time_range": time_range}
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get usage analytics: {str(e)}")
            return {}

class SophiaAIEnhancedIntegration:
    """Main integration manager for enhanced Sophia AI capabilities"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.bardeen_manager = BardeenWorkflowManager(config.bardeen_id)
        self.arize_manager = ArizeMonitoringManager(config.arize_api_key)
        self.portkey_gateway = EnhancedPortkeyGateway(config.portkey_api_key, self.arize_manager)
        
        # Initialize monitoring alerts
        asyncio.create_task(self._setup_monitoring_alerts())
    
    async def _setup_monitoring_alerts(self):
        """Setup initial monitoring alerts"""
        alerts = [
            {
                "name": "Sophia AI Response Time Alert",
                "model_id": "sophia_ai_responses",
                "metric": "response_time",
                "threshold": 5.0,
                "condition": "greater_than",
                "notification_channels": ["slack", "email"]
            },
            {
                "name": "Business Intelligence Accuracy Alert",
                "model_id": "sophia_business_intelligence",
                "metric": "accuracy_score",
                "threshold": 0.85,
                "condition": "less_than",
                "notification_channels": ["slack", "email"]
            },
            {
                "name": "Cost Optimization Alert",
                "model_id": "sophia_ai_responses",
                "metric": "cost_per_request",
                "threshold": 0.10,
                "condition": "greater_than",
                "notification_channels": ["slack"]
            }
        ]
        
        for alert in alerts:
            await self.arize_manager.create_performance_alert(alert)
    
    async def process_gong_call_analysis(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Gong.io call analysis with enhanced AI and automation"""
        try:
            # Generate AI insights from call data
            ai_prompt = f"""
            Analyze this sales call data and provide business intelligence insights:
            
            Call Duration: {call_data.get('duration', 'Unknown')}
            Participants: {', '.join(call_data.get('participants', []))}
            Key Topics: {', '.join(call_data.get('key_topics', []))}
            Sentiment Score: {call_data.get('sentiment_score', 'Unknown')}
            
            Provide insights on:
            1. Deal progression likelihood
            2. Customer health score
            3. Next best actions
            4. Risk factors
            5. Opportunity assessment
            """
            
            # Get AI analysis
            ai_response = await self.portkey_gateway.enhanced_completion(
                prompt=ai_prompt,
                model="gpt-4",
                business_domain="sales_intelligence",
                user_context={"call_id": call_data.get("call_id")}
            )
            
            # Sync to HubSpot via Bardeen
            hubspot_sync = await self.bardeen_manager.sync_gong_to_hubspot(call_data)
            
            # Send Slack notification if high priority
            if call_data.get("sentiment_score", 0) < 0.3:  # Low sentiment
                await self.bardeen_manager.slack_team_notification({
                    "channel": "#sales-alerts",
                    "message": f"🚨 Low sentiment call detected: {call_data.get('call_id')}",
                    "priority": "high",
                    "mention_users": ["@sales-manager"]
                })
            
            # Track business intelligence quality
            await self.arize_manager.monitor_business_intelligence({
                "insight_id": f"call_analysis_{call_data.get('call_id')}",
                "data_sources": ["gong.io"],
                "analysis_type": "call_intelligence",
                "insight": ai_response.get("response"),
                "business_context": {
                    "call_id": call_data.get("call_id"),
                    "deal_stage": call_data.get("deal_stage"),
                    "customer_segment": call_data.get("customer_segment")
                }
            })
            
            return {
                "ai_insights": ai_response.get("response"),
                "hubspot_sync_status": hubspot_sync.get("status"),
                "processing_time": ai_response.get("response_time"),
                "call_id": call_data.get("call_id")
            }
            
        except Exception as e:
            logger.error(f"Failed to process Gong call analysis: {str(e)}")
            raise
    
    async def automated_lead_processing(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Automated lead processing with enrichment and scoring"""
        try:
            # Enrich lead data via Bardeen
            enriched_data = await self.bardeen_manager.automate_lead_enrichment(lead_data)
            
            # Generate AI-powered lead scoring
            scoring_prompt = f"""
            Score this lead based on the enriched data:
            
            Company: {enriched_data.get('company', 'Unknown')}
            Industry: {enriched_data.get('industry', 'Unknown')}
            Company Size: {enriched_data.get('company_size', 'Unknown')}
            Revenue: {enriched_data.get('revenue', 'Unknown')}
            Technologies: {', '.join(enriched_data.get('technologies', []))}
            
            Provide:
            1. Lead score (0-100)
            2. Qualification status (Hot/Warm/Cold)
            3. Recommended next actions
            4. Priority level
            5. Estimated deal size
            """
            
            scoring_response = await self.portkey_gateway.enhanced_completion(
                prompt=scoring_prompt,
                model="gpt-4",
                business_domain="lead_scoring",
                user_context={"lead_email": lead_data.get("email")}
            )
            
            # Send notification for high-value leads
            if "Hot" in scoring_response.get("response", {}).get("choices", [{}])[0].get("message", {}).get("content", ""):
                await self.bardeen_manager.slack_team_notification({
                    "channel": "#sales-team",
                    "message": f"🔥 Hot lead detected: {lead_data.get('email')}",
                    "priority": "high"
                })
            
            return {
                "enriched_data": enriched_data,
                "ai_scoring": scoring_response.get("response"),
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to process lead: {str(e)}")
            raise
    
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        try:
            # Get Portkey usage analytics
            portkey_analytics = await self.portkey_gateway.get_usage_analytics("24h")
            
            # Compile dashboard data
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "portkey_analytics": portkey_analytics,
                "integration_status": {
                    "bardeen": "active",
                    "arize": "monitoring",
                    "portkey": "operational"
                },
                "performance_metrics": {
                    "avg_response_time": portkey_analytics.get("avg_response_time", 0),
                    "total_requests": portkey_analytics.get("total_requests", 0),
                    "cost_optimization": portkey_analytics.get("cost_savings", 0),
                    "error_rate": portkey_analytics.get("error_rate", 0)
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get performance dashboard: {str(e)}")
            return {}

# Configuration and initialization
def create_enhanced_integration() -> SophiaAIEnhancedIntegration:
    """Create enhanced integration instance with environment configuration"""
    config = IntegrationConfig(
        bardeen_id=os.getenv("BARDEEN_ID", "4519f8fe2a6d1416201c3653dbd9a3d20641f93ca7c05b852a6f7db29059d1e7"),
        arize_api_key=os.getenv("ARIZE_API_KEY", "ak-0ea39c4f-d87e-492c-afa3-cc34b69dfdba-2cqWixdMIgv9RqR8DWTqkIGugAicXQ0e"),
        portkey_api_key=os.getenv("PORTKEY_API_KEY", ""),
        environment=os.getenv("ENVIRONMENT", "production")
    )
    
    return SophiaAIEnhancedIntegration(config)

# Example usage
async def main():
    """Example usage of enhanced integration"""
    integration = create_enhanced_integration()
    
    # Example: Process Gong call analysis
    call_data = {
        "call_id": "call_12345",
        "participants": ["john@payready.com", "client@example.com"],
        "duration": 1800,  # 30 minutes
        "sentiment_score": 0.75,
        "key_topics": ["pricing", "implementation", "timeline"],
        "action_items": ["Send proposal", "Schedule demo", "Connect with technical team"]
    }
    
    result = await integration.process_gong_call_analysis(call_data)
    print(f"Call analysis result: {result}")
    
    # Example: Process new lead
    lead_data = {
        "email": "prospect@newcompany.com",
        "company": "New Company Inc",
        "name": "Jane Prospect",
        "source": "website_form"
    }
    
    lead_result = await integration.automated_lead_processing(lead_data)
    print(f"Lead processing result: {lead_result}")

if __name__ == "__main__":
    asyncio.run(main())

