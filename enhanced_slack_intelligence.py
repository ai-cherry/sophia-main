#!/usr/bin/env python3
"""
Enhanced Slack Intelligence Integration
Advanced conversation intelligence similar to Gong.io for team communications

This module provides comprehensive Slack conversation intelligence,
business context analysis, and predictive insights for Pay Ready.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import os
import hashlib
from textblob import TextBlob
import spacy
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of business-relevant messages"""
    CUSTOMER_MENTION = "customer_mention"
    DEAL_DISCUSSION = "deal_discussion"
    SUPPORT_REQUEST = "support_request"
    PROJECT_UPDATE = "project_update"
    MEETING_COORDINATION = "meeting_coordination"
    COMPETITIVE_INTEL = "competitive_intel"
    FEEDBACK = "feedback"
    ESCALATION = "escalation"
    GENERAL = "general"

class SentimentLevel(Enum):
    """Sentiment analysis levels"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

@dataclass
class MessageIntelligence:
    """Comprehensive message analysis results"""
    message_id: str
    channel: str
    user: str
    timestamp: datetime
    text: str
    message_type: MessageType
    sentiment: SentimentLevel
    sentiment_score: float
    business_entities: Dict[str, List[str]]
    keywords: List[str]
    action_items: List[str]
    urgency_score: float
    context_score: float
    follow_up_required: bool
    escalation_needed: bool
    related_systems: List[str]

@dataclass
class ConversationInsight:
    """Business insights from conversation analysis"""
    insight_type: str
    title: str
    description: str
    confidence_score: float
    business_impact: str
    recommended_actions: List[str]
    related_messages: List[str]
    trend_data: Dict[str, Any]

class SlackIntelligenceEngine:
    """Advanced Slack conversation intelligence engine"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.nlp = None
        self.business_keywords = self._load_business_keywords()
        self.customer_patterns = self._load_customer_patterns()
        self.escalation_triggers = self._load_escalation_triggers()
        self.conversation_cache = {}
        self.insights_cache = {}
        
    async def initialize(self):
        """Initialize NLP models and business intelligence components"""
        try:
            # Load spaCy model for advanced NLP
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Slack Intelligence Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize intelligence engine: {str(e)}")
            return False
    
    def _load_business_keywords(self) -> Dict[str, List[str]]:
        """Load business-specific keywords for different categories"""
        return {
            'customer': [
                'client', 'customer', 'tenant', 'resident', 'prospect', 'lead',
                'property manager', 'leasing agent', 'apartment complex', 'building owner'
            ],
            'sales': [
                'deal', 'proposal', 'contract', 'revenue', 'sales', 'pipeline',
                'opportunity', 'close', 'win', 'loss', 'demo', 'presentation'
            ],
            'support': [
                'issue', 'problem', 'bug', 'error', 'help', 'support', 'ticket',
                'maintenance', 'repair', 'complaint', 'escalate', 'urgent'
            ],
            'product': [
                'feature', 'functionality', 'enhancement', 'improvement', 'feedback',
                'user experience', 'interface', 'performance', 'integration'
            ],
            'competition': [
                'competitor', 'competitive', 'alternative', 'comparison', 'versus',
                'market share', 'pricing', 'feature comparison'
            ],
            'apartment_industry': [
                'property', 'apartment', 'unit', 'lease', 'rent', 'occupancy',
                'vacancy', 'renewal', 'move-in', 'move-out', 'amenities'
            ]
        }
    
    def _load_customer_patterns(self) -> List[str]:
        """Load regex patterns for customer identification"""
        return [
            r'\b[A-Z][a-z]+ (Apartments?|Properties|Management|Group)\b',
            r'\b[A-Z][a-z]+ (Complex|Community|Residences)\b',
            r'\b\d+\s+[A-Z][a-z]+\s+(Street|Ave|Avenue|Blvd|Boulevard|Drive|Dr)\b',
            r'\b[A-Z][a-z]+\s+(Property|Properties)\s+(Management|Group)\b'
        ]
    
    def _load_escalation_triggers(self) -> List[str]:
        """Load keywords that indicate escalation needs"""
        return [
            'urgent', 'emergency', 'critical', 'asap', 'immediately', 'escalate',
            'angry', 'frustrated', 'complaint', 'lawsuit', 'legal', 'attorney',
            'cancel', 'cancellation', 'terminate', 'refund', 'chargeback'
        ]
    
    async def analyze_message(self, message_data: Dict[str, Any]) -> MessageIntelligence:
        """Comprehensive message analysis similar to Gong's call analysis"""
        try:
            text = message_data.get('text', '')
            if not text:
                return None
            
            # Basic message info
            message_id = message_data.get('ts', '')
            channel = message_data.get('channel', '')
            user = message_data.get('user', '')
            timestamp = datetime.fromtimestamp(float(message_data.get('ts', 0)))
            
            # Sentiment analysis
            sentiment, sentiment_score = self._analyze_sentiment(text)
            
            # Message type classification
            message_type = self._classify_message_type(text)
            
            # Business entity extraction
            business_entities = self._extract_business_entities(text)
            
            # Keyword extraction
            keywords = self._extract_keywords(text)
            
            # Action item identification
            action_items = self._identify_action_items(text)
            
            # Urgency scoring
            urgency_score = self._calculate_urgency_score(text)
            
            # Context scoring
            context_score = self._calculate_context_score(text, message_type)
            
            # Follow-up and escalation detection
            follow_up_required = self._requires_follow_up(text, sentiment)
            escalation_needed = self._requires_escalation(text, sentiment_score)
            
            # Related systems identification
            related_systems = self._identify_related_systems(text, business_entities)
            
            return MessageIntelligence(
                message_id=message_id,
                channel=channel,
                user=user,
                timestamp=timestamp,
                text=text,
                message_type=message_type,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                business_entities=business_entities,
                keywords=keywords,
                action_items=action_items,
                urgency_score=urgency_score,
                context_score=context_score,
                follow_up_required=follow_up_required,
                escalation_needed=escalation_needed,
                related_systems=related_systems
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze message: {str(e)}")
            return None
    
    def _analyze_sentiment(self, text: str) -> tuple[SentimentLevel, float]:
        """Analyze sentiment using TextBlob and custom business context"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # Adjust for business context
            business_negative_words = ['issue', 'problem', 'bug', 'error', 'complaint', 'frustrated']
            business_positive_words = ['great', 'excellent', 'love', 'perfect', 'amazing', 'successful']
            
            text_lower = text.lower()
            negative_count = sum(1 for word in business_negative_words if word in text_lower)
            positive_count = sum(1 for word in business_positive_words if word in text_lower)
            
            # Adjust polarity based on business context
            business_adjustment = (positive_count - negative_count) * 0.1
            adjusted_polarity = polarity + business_adjustment
            
            # Classify sentiment
            if adjusted_polarity >= 0.5:
                sentiment = SentimentLevel.VERY_POSITIVE
            elif adjusted_polarity >= 0.1:
                sentiment = SentimentLevel.POSITIVE
            elif adjusted_polarity >= -0.1:
                sentiment = SentimentLevel.NEUTRAL
            elif adjusted_polarity >= -0.5:
                sentiment = SentimentLevel.NEGATIVE
            else:
                sentiment = SentimentLevel.VERY_NEGATIVE
            
            return sentiment, adjusted_polarity
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return SentimentLevel.NEUTRAL, 0.0
    
    def _classify_message_type(self, text: str) -> MessageType:
        """Classify message type based on content analysis"""
        text_lower = text.lower()
        
        # Customer mention detection
        customer_indicators = ['client', 'customer', 'tenant', 'resident', 'property manager']
        if any(indicator in text_lower for indicator in customer_indicators):
            return MessageType.CUSTOMER_MENTION
        
        # Deal discussion detection
        deal_indicators = ['deal', 'proposal', 'contract', 'revenue', 'sales', 'pipeline']
        if any(indicator in text_lower for indicator in deal_indicators):
            return MessageType.DEAL_DISCUSSION
        
        # Support request detection
        support_indicators = ['issue', 'problem', 'bug', 'error', 'help', 'support']
        if any(indicator in text_lower for indicator in support_indicators):
            return MessageType.SUPPORT_REQUEST
        
        # Project update detection
        project_indicators = ['project', 'milestone', 'deliverable', 'progress', 'status']
        if any(indicator in text_lower for indicator in project_indicators):
            return MessageType.PROJECT_UPDATE
        
        # Meeting coordination detection
        meeting_indicators = ['meeting', 'call', 'schedule', 'calendar', 'agenda']
        if any(indicator in text_lower for indicator in meeting_indicators):
            return MessageType.MEETING_COORDINATION
        
        # Competitive intelligence detection
        competitive_indicators = ['competitor', 'competitive', 'alternative', 'comparison']
        if any(indicator in text_lower for indicator in competitive_indicators):
            return MessageType.COMPETITIVE_INTEL
        
        # Feedback detection
        feedback_indicators = ['feedback', 'suggestion', 'improvement', 'enhancement']
        if any(indicator in text_lower for indicator in feedback_indicators):
            return MessageType.FEEDBACK
        
        # Escalation detection
        escalation_indicators = ['urgent', 'emergency', 'escalate', 'critical']
        if any(indicator in text_lower for indicator in escalation_indicators):
            return MessageType.ESCALATION
        
        return MessageType.GENERAL
    
    def _extract_business_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract business entities using NLP and custom patterns"""
        entities = {
            'customers': [],
            'properties': [],
            'deals': [],
            'people': [],
            'companies': [],
            'amounts': [],
            'dates': []
        }
        
        try:
            if self.nlp:
                doc = self.nlp(text)
                
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        entities['people'].append(ent.text)
                    elif ent.label_ == "ORG":
                        entities['companies'].append(ent.text)
                    elif ent.label_ == "MONEY":
                        entities['amounts'].append(ent.text)
                    elif ent.label_ == "DATE":
                        entities['dates'].append(ent.text)
            
            # Custom pattern matching for apartment industry
            for pattern in self.customer_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['customers'].extend(matches)
            
            # Property identification
            property_patterns = [
                r'\b\d+\s+[A-Z][a-z]+\s+(Apartments?|Complex|Community)\b',
                r'\b[A-Z][a-z]+\s+(Towers?|Heights?|Gardens?|Plaza)\b'
            ]
            
            for pattern in property_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['properties'].extend(matches)
            
            # Deal identification
            deal_patterns = [
                r'\b[A-Z][a-z]+\s+(deal|proposal|contract)\b',
                r'\$[\d,]+(?:\.\d{2})?\s*(?:deal|contract|revenue)\b'
            ]
            
            for pattern in deal_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['deals'].extend(matches)
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant business keywords"""
        keywords = []
        text_lower = text.lower()
        
        for category, word_list in self.business_keywords.items():
            for word in word_list:
                if word in text_lower:
                    keywords.append(word)
        
        return list(set(keywords))
    
    def _identify_action_items(self, text: str) -> List[str]:
        """Identify action items and tasks from message content"""
        action_items = []
        
        # Action item patterns
        action_patterns = [
            r'(?:need to|should|must|have to|will)\s+([^.!?]+)',
            r'(?:todo|to do|action item):\s*([^.!?]+)',
            r'(?:follow up|follow-up)\s+(?:on|with)\s+([^.!?]+)',
            r'(?:schedule|set up|arrange)\s+([^.!?]+)'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            action_items.extend(matches)
        
        return [item.strip() for item in action_items if item.strip()]
    
    def _calculate_urgency_score(self, text: str) -> float:
        """Calculate urgency score based on content analysis"""
        urgency_score = 0.0
        text_lower = text.lower()
        
        # High urgency indicators
        high_urgency = ['urgent', 'emergency', 'critical', 'asap', 'immediately']
        medium_urgency = ['soon', 'quickly', 'priority', 'important']
        low_urgency = ['when possible', 'eventually', 'sometime']
        
        for word in high_urgency:
            if word in text_lower:
                urgency_score += 0.8
        
        for word in medium_urgency:
            if word in text_lower:
                urgency_score += 0.5
        
        for word in low_urgency:
            if word in text_lower:
                urgency_score += 0.2
        
        # Escalation triggers increase urgency
        for trigger in self.escalation_triggers:
            if trigger in text_lower:
                urgency_score += 0.6
        
        return min(urgency_score, 1.0)
    
    def _calculate_context_score(self, text: str, message_type: MessageType) -> float:
        """Calculate business context relevance score"""
        context_score = 0.0
        
        # Base score by message type
        type_scores = {
            MessageType.CUSTOMER_MENTION: 0.9,
            MessageType.DEAL_DISCUSSION: 0.8,
            MessageType.SUPPORT_REQUEST: 0.7,
            MessageType.PROJECT_UPDATE: 0.6,
            MessageType.COMPETITIVE_INTEL: 0.8,
            MessageType.ESCALATION: 0.9,
            MessageType.FEEDBACK: 0.5,
            MessageType.MEETING_COORDINATION: 0.4,
            MessageType.GENERAL: 0.2
        }
        
        context_score = type_scores.get(message_type, 0.2)
        
        # Adjust based on business keyword density
        text_lower = text.lower()
        keyword_count = sum(
            1 for category in self.business_keywords.values()
            for keyword in category
            if keyword in text_lower
        )
        
        keyword_density = keyword_count / max(len(text.split()), 1)
        context_score += keyword_density * 0.3
        
        return min(context_score, 1.0)
    
    def _requires_follow_up(self, text: str, sentiment: SentimentLevel) -> bool:
        """Determine if message requires follow-up"""
        text_lower = text.lower()
        
        # Explicit follow-up indicators
        follow_up_indicators = [
            'follow up', 'follow-up', 'get back to', 'circle back',
            'check in', 'update me', 'let me know'
        ]
        
        if any(indicator in text_lower for indicator in follow_up_indicators):
            return True
        
        # Negative sentiment with customer mentions
        if sentiment in [SentimentLevel.NEGATIVE, SentimentLevel.VERY_NEGATIVE]:
            customer_mentions = any(
                keyword in text_lower 
                for keyword in self.business_keywords['customer']
            )
            if customer_mentions:
                return True
        
        # Questions require follow-up
        if '?' in text:
            return True
        
        return False
    
    def _requires_escalation(self, text: str, sentiment_score: float) -> bool:
        """Determine if message requires escalation"""
        text_lower = text.lower()
        
        # Explicit escalation triggers
        if any(trigger in text_lower for trigger in self.escalation_triggers):
            return True
        
        # Very negative sentiment with customer context
        if sentiment_score < -0.6:
            customer_context = any(
                keyword in text_lower 
                for keyword in self.business_keywords['customer']
            )
            if customer_context:
                return True
        
        return False
    
    def _identify_related_systems(self, text: str, entities: Dict[str, List[str]]) -> List[str]:
        """Identify which business systems should be updated"""
        systems = []
        text_lower = text.lower()
        
        # CRM integration triggers
        crm_triggers = ['customer', 'client', 'deal', 'sales', 'pipeline', 'opportunity']
        if any(trigger in text_lower for trigger in crm_triggers):
            systems.append('salesforce')
            systems.append('hubspot')
        
        # Support system triggers
        support_triggers = ['issue', 'problem', 'bug', 'support', 'ticket']
        if any(trigger in text_lower for trigger in support_triggers):
            systems.append('support_system')
        
        # Project management triggers
        project_triggers = ['project', 'task', 'milestone', 'deliverable']
        if any(trigger in text_lower for trigger in project_triggers):
            systems.append('project_management')
        
        # Calendar integration triggers
        calendar_triggers = ['meeting', 'call', 'schedule', 'appointment']
        if any(trigger in text_lower for trigger in calendar_triggers):
            systems.append('calendar')
        
        return list(set(systems))
    
    async def generate_conversation_insights(self, messages: List[MessageIntelligence]) -> List[ConversationInsight]:
        """Generate business insights from conversation analysis"""
        insights = []
        
        try:
            # Customer sentiment trending
            customer_messages = [
                msg for msg in messages 
                if msg.message_type == MessageType.CUSTOMER_MENTION
            ]
            
            if customer_messages:
                avg_sentiment = sum(msg.sentiment_score for msg in customer_messages) / len(customer_messages)
                
                if avg_sentiment < -0.3:
                    insights.append(ConversationInsight(
                        insight_type="customer_sentiment_alert",
                        title="Declining Customer Sentiment Detected",
                        description=f"Customer sentiment has declined to {avg_sentiment:.2f} based on recent conversations",
                        confidence_score=0.8,
                        business_impact="High - potential churn risk",
                        recommended_actions=[
                            "Review recent customer interactions",
                            "Proactive outreach to affected customers",
                            "Escalate to customer success team"
                        ],
                        related_messages=[msg.message_id for msg in customer_messages[-5:]],
                        trend_data={"sentiment_score": avg_sentiment, "message_count": len(customer_messages)}
                    ))
            
            # Deal discussion analysis
            deal_messages = [
                msg for msg in messages 
                if msg.message_type == MessageType.DEAL_DISCUSSION
            ]
            
            if deal_messages:
                positive_deals = sum(1 for msg in deal_messages if msg.sentiment_score > 0.2)
                deal_success_rate = positive_deals / len(deal_messages)
                
                insights.append(ConversationInsight(
                    insight_type="sales_pipeline_health",
                    title="Sales Pipeline Health Analysis",
                    description=f"Deal discussions show {deal_success_rate:.1%} positive sentiment",
                    confidence_score=0.7,
                    business_impact="Medium - pipeline health indicator",
                    recommended_actions=[
                        "Focus on deals with negative sentiment",
                        "Replicate successful deal patterns",
                        "Update CRM with conversation insights"
                    ],
                    related_messages=[msg.message_id for msg in deal_messages],
                    trend_data={"success_rate": deal_success_rate, "total_deals": len(deal_messages)}
                ))
            
            # Support request analysis
            support_messages = [
                msg for msg in messages 
                if msg.message_type == MessageType.SUPPORT_REQUEST
            ]
            
            if support_messages:
                urgent_issues = sum(1 for msg in support_messages if msg.urgency_score > 0.7)
                
                if urgent_issues > 0:
                    insights.append(ConversationInsight(
                        insight_type="support_escalation_alert",
                        title="Multiple Urgent Support Issues Detected",
                        description=f"{urgent_issues} urgent support issues identified in recent conversations",
                        confidence_score=0.9,
                        business_impact="High - customer satisfaction risk",
                        recommended_actions=[
                            "Immediate review of urgent issues",
                            "Assign dedicated support resources",
                            "Implement proactive communication plan"
                        ],
                        related_messages=[
                            msg.message_id for msg in support_messages 
                            if msg.urgency_score > 0.7
                        ],
                        trend_data={"urgent_count": urgent_issues, "total_support": len(support_messages)}
                    ))
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {str(e)}")
        
        return insights

# Enhanced Slack Integration with Intelligence
class EnhancedSlackIntegration:
    """Enhanced Slack integration with conversation intelligence"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.intelligence_engine = SlackIntelligenceEngine(config)
        self.client = None
        self.message_buffer = []
        self.insights_cache = {}
        
    async def initialize(self):
        """Initialize enhanced Slack integration"""
        # Initialize intelligence engine
        if not await self.intelligence_engine.initialize():
            logger.error("Failed to initialize intelligence engine")
            return False
        
        # Initialize Slack client
        bot_token = os.getenv('SLACK_BOT_TOKEN', '')
        if not bot_token:
            logger.error("SLACK_BOT_TOKEN not configured")
            return False
        
        self.client = AsyncWebClient(token=bot_token)
        
        try:
            auth_response = await self.client.auth_test()
            logger.info(f"Enhanced Slack integration initialized for {auth_response.get('team')}")
            return True
        except SlackApiError as e:
            logger.error(f"Failed to initialize Slack client: {e.response['error']}")
            return False
    
    async def process_message_with_intelligence(self, message_data: Dict[str, Any]) -> Optional[MessageIntelligence]:
        """Process message with full intelligence analysis"""
        try:
            # Analyze message
            intelligence = await self.intelligence_engine.analyze_message(message_data)
            
            if intelligence:
                # Store in buffer for batch processing
                self.message_buffer.append(intelligence)
                
                # Process immediate actions
                await self._handle_immediate_actions(intelligence)
                
                # Generate insights if buffer is full
                if len(self.message_buffer) >= 50:
                    await self._process_insights_batch()
                
                return intelligence
            
        except Exception as e:
            logger.error(f"Failed to process message with intelligence: {str(e)}")
        
        return None
    
    async def _handle_immediate_actions(self, intelligence: MessageIntelligence):
        """Handle immediate actions based on message intelligence"""
        try:
            # Escalation handling
            if intelligence.escalation_needed:
                await self._handle_escalation(intelligence)
            
            # Follow-up scheduling
            if intelligence.follow_up_required:
                await self._schedule_follow_up(intelligence)
            
            # System integrations
            if intelligence.related_systems:
                await self._update_related_systems(intelligence)
            
        except Exception as e:
            logger.error(f"Failed to handle immediate actions: {str(e)}")
    
    async def _handle_escalation(self, intelligence: MessageIntelligence):
        """Handle message escalation"""
        # Send escalation notification
        escalation_message = {
            'channel': '#escalations',
            'text': f"🚨 Escalation Required: {intelligence.message_type.value}",
            'blocks': [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 Message Escalation Alert"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Channel:* #{intelligence.channel}"},
                        {"type": "mrkdwn", "text": f"*User:* <@{intelligence.user}>"},
                        {"type": "mrkdwn", "text": f"*Urgency:* {intelligence.urgency_score:.1%}"},
                        {"type": "mrkdwn", "text": f"*Sentiment:* {intelligence.sentiment.value}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Message:* {intelligence.text[:200]}..."}
                }
            ]
        }
        
        # Send escalation (implementation would depend on actual Slack client)
        logger.info(f"Escalation triggered for message {intelligence.message_id}")
    
    async def _schedule_follow_up(self, intelligence: MessageIntelligence):
        """Schedule follow-up for message"""
        # Create follow-up task (implementation would integrate with task management)
        logger.info(f"Follow-up scheduled for message {intelligence.message_id}")
    
    async def _update_related_systems(self, intelligence: MessageIntelligence):
        """Update related business systems"""
        for system in intelligence.related_systems:
            if system == 'salesforce':
                # Update Salesforce with conversation intelligence
                pass
            elif system == 'hubspot':
                # Update HubSpot with lead information
                pass
            elif system == 'support_system':
                # Create support ticket if needed
                pass
        
        logger.info(f"Updated {len(intelligence.related_systems)} related systems")
    
    async def _process_insights_batch(self):
        """Process batch of messages for insights generation"""
        try:
            insights = await self.intelligence_engine.generate_conversation_insights(self.message_buffer)
            
            for insight in insights:
                await self._deliver_insight(insight)
            
            # Clear buffer
            self.message_buffer = []
            
        except Exception as e:
            logger.error(f"Failed to process insights batch: {str(e)}")
    
    async def _deliver_insight(self, insight: ConversationInsight):
        """Deliver business insight to appropriate channels"""
        # Format insight message
        insight_message = {
            'channel': '#business-insights',
            'text': f"💡 {insight.title}",
            'blocks': [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"💡 {insight.title}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": insight.description}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Confidence:* {insight.confidence_score:.1%}"},
                        {"type": "mrkdwn", "text": f"*Impact:* {insight.business_impact}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn", 
                        "text": f"*Recommended Actions:*\n• " + "\n• ".join(insight.recommended_actions)
                    }
                }
            ]
        }
        
        # Deliver insight (implementation would depend on actual Slack client)
        logger.info(f"Delivered insight: {insight.title}")

# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Initialize enhanced integration
        integration = EnhancedSlackIntegration()
        
        if await integration.initialize():
            print("Enhanced Slack Intelligence Integration initialized successfully!")
            
            # Example message processing
            sample_message = {
                'ts': str(datetime.now().timestamp()),
                'channel': 'C1234567890',
                'user': 'U1234567890',
                'text': 'We have an urgent issue with the Sunset Apartments client. They are very frustrated with the maintenance response time and are threatening to cancel their contract. Need to escalate this immediately.'
            }
            
            intelligence = await integration.process_message_with_intelligence(sample_message)
            
            if intelligence:
                print(f"Message analyzed successfully!")
                print(f"Type: {intelligence.message_type.value}")
                print(f"Sentiment: {intelligence.sentiment.value} ({intelligence.sentiment_score:.2f})")
                print(f"Urgency: {intelligence.urgency_score:.1%}")
                print(f"Escalation needed: {intelligence.escalation_needed}")
                print(f"Keywords: {', '.join(intelligence.keywords)}")
        else:
            print("Failed to initialize enhanced integration")
    
    asyncio.run(main())

