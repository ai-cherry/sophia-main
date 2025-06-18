"""
Sophia AI - AI Agent Integration
Integration with AI agents for automated processing and Slack notifications
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SalesCoachAgent:
    """Sales Coach AI Agent for analyzing sales-related content"""
    
    def __init__(self):
        self.sales_keywords = [
            "pricing", "proposal", "deal", "contract", "negotiation",
            "demo", "presentation", "follow-up", "closing", "objection"
        ]
        
    async def analyze_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chunk for sales coaching insights"""
        
        text = chunk.get("text", "").lower()
        
        # Check if this is sales-related content
        if not any(keyword in text for keyword in self.sales_keywords):
            return {"relevant": False}
        
        insights = {
            "relevant": True,
            "sales_stage": self._identify_sales_stage(text),
            "objections": self._identify_objections(text),
            "next_steps": self._suggest_next_steps(text),
            "coaching_tips": self._generate_coaching_tips(text),
            "deal_health": self._assess_deal_health(text)
        }
        
        return insights
    
    def _identify_sales_stage(self, text: str) -> str:
        """Identify the sales stage from text"""
        
        if any(word in text for word in ["discovery", "qualification", "initial"]):
            return "discovery"
        elif any(word in text for word in ["demo", "presentation", "show"]):
            return "demonstration"
        elif any(word in text for word in ["proposal", "quote", "pricing"]):
            return "proposal"
        elif any(word in text for word in ["negotiation", "terms", "contract"]):
            return "negotiation"
        elif any(word in text for word in ["closing", "sign", "deal"]):
            return "closing"
        else:
            return "unknown"
    
    def _identify_objections(self, text: str) -> List[str]:
        """Identify objections in the text"""
        
        objections = []
        objection_indicators = [
            "concern", "worried", "not sure", "expensive", "complex",
            "difficult", "competitor", "alternative", "budget", "timeline"
        ]
        
        for indicator in objection_indicators:
            if indicator in text:
                objections.append(indicator)
        
        return objections
    
    def _suggest_next_steps(self, text: str) -> List[str]:
        """Suggest next steps based on content"""
        
        next_steps = []
        
        if "pricing" in text:
            next_steps.append("Prepare detailed pricing proposal")
        if "demo" in text:
            next_steps.append("Schedule product demonstration")
        if "objection" in text or "concern" in text:
            next_steps.append("Address objections with specific solutions")
        if "contract" in text:
            next_steps.append("Prepare contract documents")
        
        return next_steps
    
    def _generate_coaching_tips(self, text: str) -> List[str]:
        """Generate coaching tips based on content"""
        
        tips = []
        
        if "objection" in text:
            tips.append("Practice objection handling techniques")
        if "pricing" in text:
            tips.append("Focus on value proposition over price")
        if "competitor" in text:
            tips.append("Highlight competitive advantages")
        
        return tips
    
    def _assess_deal_health(self, text: str) -> str:
        """Assess the health of the deal"""
        
        positive_indicators = ["interested", "excited", "ready", "agree", "yes"]
        negative_indicators = ["concerned", "worried", "not sure", "expensive", "no"]
        
        positive_count = sum(1 for word in positive_indicators if word in text)
        negative_count = sum(1 for word in negative_indicators if word in text)
        
        if positive_count > negative_count:
            return "healthy"
        elif negative_count > positive_count:
            return "at_risk"
        else:
            return "neutral"

class CustomerHealthAgent:
    """Customer Health AI Agent for analyzing customer relationship content"""
    
    def __init__(self):
        self.health_indicators = {
            "positive": ["satisfied", "happy", "pleased", "excellent", "great"],
            "negative": ["frustrated", "disappointed", "concerned", "issue", "problem"],
            "at_risk": ["cancel", "terminate", "end", "switch", "competitor"]
        }
    
    async def analyze_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chunk for customer health insights"""
        
        text = chunk.get("text", "").lower()
        
        insights = {
            "health_score": self._calculate_health_score(text),
            "risk_factors": self._identify_risk_factors(text),
            "satisfaction_indicators": self._identify_satisfaction_indicators(text),
            "retention_risk": self._assess_retention_risk(text),
            "recommendations": self._generate_recommendations(text)
        }
        
        return insights
    
    def _calculate_health_score(self, text: str) -> float:
        """Calculate customer health score (0-1)"""
        
        positive_count = sum(1 for word in self.health_indicators["positive"] if word in text)
        negative_count = sum(1 for word in self.health_indicators["negative"] if word in text)
        risk_count = sum(1 for word in self.health_indicators["at_risk"] if word in text)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.5
        
        score = (positive_count - negative_count - risk_count * 2) / max(total_words / 10, 1)
        return max(0.0, min(1.0, 0.5 + score))
    
    def _identify_risk_factors(self, text: str) -> List[str]:
        """Identify risk factors in the text"""
        
        risk_factors = []
        for word in self.health_indicators["negative"] + self.health_indicators["at_risk"]:
            if word in text:
                risk_factors.append(word)
        
        return risk_factors
    
    def _identify_satisfaction_indicators(self, text: str) -> List[str]:
        """Identify satisfaction indicators"""
        
        satisfaction_indicators = []
        for word in self.health_indicators["positive"]:
            if word in text:
                satisfaction_indicators.append(word)
        
        return satisfaction_indicators
    
    def _assess_retention_risk(self, text: str) -> str:
        """Assess retention risk level"""
        
        risk_words = self.health_indicators["at_risk"]
        risk_count = sum(1 for word in risk_words if word in text)
        
        if risk_count >= 2:
            return "high"
        elif risk_count == 1:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, text: str) -> List[str]:
        """Generate recommendations based on content"""
        
        recommendations = []
        
        if any(word in text for word in ["issue", "problem", "concern"]):
            recommendations.append("Schedule immediate follow-up call")
        if any(word in text for word in ["cancel", "terminate"]):
            recommendations.append("Escalate to account manager")
        if any(word in text for word in ["satisfied", "happy"]):
            recommendations.append("Request testimonial or referral")
        
        return recommendations

class BusinessIntelligenceAgent:
    """Business Intelligence AI Agent for comprehensive analysis"""
    
    def __init__(self):
        self.business_keywords = [
            "revenue", "growth", "efficiency", "performance", "metrics",
            "strategy", "opportunity", "risk", "compliance", "innovation"
        ]
    
    async def analyze_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chunk for business intelligence insights"""
        
        text = chunk.get("text", "").lower()
        
        insights = {
            "business_impact": self._assess_business_impact(text),
            "opportunities": self._identify_opportunities(text),
            "risks": self._identify_risks(text),
            "trends": self._identify_trends(text),
            "recommendations": self._generate_business_recommendations(text)
        }
        
        return insights
    
    def _assess_business_impact(self, text: str) -> str:
        """Assess business impact level"""
        
        high_impact_words = ["revenue", "growth", "strategy", "opportunity"]
        medium_impact_words = ["efficiency", "performance", "improvement"]
        
        high_count = sum(1 for word in high_impact_words if word in text)
        medium_count = sum(1 for word in medium_impact_words if word in text)
        
        if high_count >= 2:
            return "high"
        elif high_count == 1 or medium_count >= 2:
            return "medium"
        else:
            return "low"
    
    def _identify_opportunities(self, text: str) -> List[str]:
        """Identify business opportunities"""
        
        opportunities = []
        
        if "growth" in text:
            opportunities.append("Revenue growth opportunity")
        if "efficiency" in text:
            opportunities.append("Process optimization opportunity")
        if "innovation" in text:
            opportunities.append("Innovation opportunity")
        
        return opportunities
    
    def _identify_risks(self, text: str) -> List[str]:
        """Identify business risks"""
        
        risks = []
        
        if "risk" in text:
            risks.append("Business risk identified")
        if "compliance" in text:
            risks.append("Compliance risk")
        if "competitor" in text:
            risks.append("Competitive risk")
        
        return risks
    
    def _identify_trends(self, text: str) -> List[str]:
        """Identify business trends"""
        
        trends = []
        
        if "trend" in text or "pattern" in text:
            trends.append("Trend analysis needed")
        if "market" in text:
            trends.append("Market trend identified")
        
        return trends
    
    def _generate_business_recommendations(self, text: str) -> List[str]:
        """Generate business recommendations"""
        
        recommendations = []
        
        if "revenue" in text:
            recommendations.append("Focus on revenue optimization")
        if "efficiency" in text:
            recommendations.append("Implement efficiency improvements")
        if "risk" in text:
            recommendations.append("Develop risk mitigation strategy")
        
        return recommendations

class SlackBot:
    """Slack Bot for sending notifications"""
    
    def __init__(self):
        self.channels = {
            "sales-alerts": "sales-alerts",
            "revenue-alerts": "revenue-alerts",
            "sales-team": "sales-team",
            "customer-success": "customer-success",
            "general": "general"
        }
        
    async def send_notification(self, channel: str, message: str, priority: str = "normal"):
        """Send notification to Slack channel"""
        
        # Mock Slack notification for now
        logger.info(f"Slack notification to {channel}: {message} (priority: {priority})")
        
        # In production, this would use the Slack API
        # await self.slack_client.chat_postMessage(
        #     channel=channel,
        #     text=message,
        #     username="Sophia AI"
        # )

class AIAgentIntegration:
    """Integration with AI agents for automated processing"""
    
    def __init__(self):
        self.sales_coach_agent = SalesCoachAgent()
        self.customer_health_agent = CustomerHealthAgent()
        self.business_intelligence_agent = BusinessIntelligenceAgent()
        self.slack_bot = SlackBot()
        
        logger.info("AI Agent Integration initialized")
    
    async def process_with_ai_agents(
        self, 
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process chunks with AI agents for enhanced intelligence"""
        
        enhanced_chunks = []
        
        for chunk in chunks:
            # Route to appropriate AI agents based on content
            ai_enhancements = await self._route_to_ai_agents(chunk)
            
            # Generate automated actions
            automated_actions = await self._generate_automated_actions(chunk, ai_enhancements)
            
            # Trigger Slack notifications
            slack_notifications = await self._trigger_slack_notifications(chunk, ai_enhancements)
            
            enhanced_chunk = {
                **chunk,
                "ai_enhancements": ai_enhancements,
                "automated_actions": automated_actions,
                "slack_notifications": slack_notifications
            }
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    async def _route_to_ai_agents(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Route chunk to appropriate AI agents"""
        
        enhancements = {}
        
        # Sales Coach Agent for sales-related content
        if chunk.get("metadata", {}).get("primary_topic") == "sales":
            sales_insights = await self.sales_coach_agent.analyze_chunk(chunk)
            enhancements["sales_coach"] = sales_insights
        
        # Customer Health Agent for relationship content
        if "customer" in chunk.get("text", "").lower():
            health_insights = await self.customer_health_agent.analyze_chunk(chunk)
            enhancements["customer_health"] = health_insights
        
        # Business Intelligence Agent for all content
        bi_insights = await self.business_intelligence_agent.analyze_chunk(chunk)
        enhancements["business_intelligence"] = bi_insights
        
        return enhancements
    
    async def _generate_automated_actions(self, chunk: Dict[str, Any], ai_enhancements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate automated actions based on chunk content"""
        
        actions = []
        metadata = chunk.get("metadata", {})
        
        # High urgency actions
        if metadata.get("urgency_level") == "immediate":
            actions.append({
                "type": "immediate_alert",
                "recipient": "sales_team",
                "message": f"Urgent: {chunk.get('text', '')[:100]}...",
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        # Decision point actions
        if chunk.get("chunk_type") == "decision_point":
            actions.append({
                "type": "crm_update",
                "action": "update_deal_stage",
                "deal_id": metadata.get("source_id"),
                "new_stage": "decision_made",
                "timestamp": datetime.now().isoformat()
            })
        
        # Follow-up actions
        if metadata.get("requires_follow_up"):
            actions.append({
                "type": "schedule_follow_up",
                "recipient": metadata.get("speaker"),
                "timeline": "24_hours",
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            })
        
        # Sales coaching actions
        sales_insights = ai_enhancements.get("sales_coach", {})
        if sales_insights.get("relevant"):
            actions.append({
                "type": "sales_coaching",
                "insights": sales_insights,
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            })
        
        # Customer health actions
        health_insights = ai_enhancements.get("customer_health", {})
        if health_insights.get("health_score", 1.0) < 0.5:
            actions.append({
                "type": "customer_health_intervention",
                "health_score": health_insights.get("health_score"),
                "risk_factors": health_insights.get("risk_factors", []),
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        return actions
    
    async def _trigger_slack_notifications(self, chunk: Dict[str, Any], ai_enhancements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trigger Slack notifications based on chunk content"""
        
        notifications = []
        metadata = chunk.get("metadata", {})
        
        # High business impact notifications
        if metadata.get("revenue_potential", 0) > 10000:
            notifications.append({
                "channel": "revenue-alerts",
                "message": f"💰 Revenue Opportunity: ${metadata.get('revenue_potential'):,.0f} potential",
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        # Decision maker notifications
        if metadata.get("decision_makers"):
            notifications.append({
                "channel": "sales-team",
                "message": f"👥 Decision Maker: {', '.join(metadata.get('decision_makers'))} in conversation",
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            })
        
        # High urgency notifications
        if metadata.get("urgency_level") == "immediate":
            notifications.append({
                "channel": "sales-alerts",
                "message": f"🚨 High Urgency: {chunk.get('text', '')[:150]}...",
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        # Customer health notifications
        health_insights = ai_enhancements.get("customer_health", {})
        if health_insights.get("health_score", 1.0) < 0.3:
            notifications.append({
                "channel": "customer-success",
                "message": f"⚠️ Customer Health Alert: Score {health_insights.get('health_score'):.2f}",
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        # Send notifications
        for notification in notifications:
            await self.slack_bot.send_notification(
                notification["channel"],
                notification["message"],
                notification["priority"]
            )
        
        return notifications 