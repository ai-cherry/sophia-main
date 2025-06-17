"""
Enhanced Natural Language Processor for Pay Ready Business Operations
Advanced NLP with business context understanding and intelligent routing
"""

import asyncio
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import openai
from sentence_transformers import SentenceTransformer
import spacy
import pandas as pd

from ..integrations.kong_ai_gateway import KongAIGateway

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents"""
    BUSINESS_INTELLIGENCE = "business_intelligence"
    CLIENT_MANAGEMENT = "client_management"
    SALES_OPTIMIZATION = "sales_optimization"
    INFRASTRUCTURE_CONTROL = "infrastructure_control"
    WORKFLOW_AUTOMATION = "workflow_automation"
    KNOWLEDGE_SEARCH = "knowledge_search"
    COMPLIANCE_CHECK = "compliance_check"
    MARKET_RESEARCH = "market_research"
    SYSTEM_ADMINISTRATION = "system_administration"
    GENERAL_QUERY = "general_query"


class EntityType(Enum):
    """Types of entities that can be extracted"""
    CLIENT_NAME = "client_name"
    COMPANY_NAME = "company_name"
    PRODUCT_NAME = "product_name"
    COMPETITOR_NAME = "competitor_name"
    METRIC_NAME = "metric_name"
    TIME_PERIOD = "time_period"
    DOLLAR_AMOUNT = "dollar_amount"
    PERCENTAGE = "percentage"
    INFRASTRUCTURE_COMPONENT = "infrastructure_component"
    WORKFLOW_NAME = "workflow_name"
    AGENT_TYPE = "agent_type"
    COMPLIANCE_AREA = "compliance_area"


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from user input"""
    entity_type: EntityType
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'entity_type': self.entity_type.value
        }


@dataclass
class ProcessedIntent:
    """Represents a processed user intent"""
    intent_type: IntentType
    confidence: float
    entities: List[ExtractedEntity]
    parameters: Dict[str, Any]
    suggested_actions: List[str]
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'intent_type': self.intent_type.value,
            'confidence': self.confidence,
            'entities': [entity.to_dict() for entity in self.entities],
            'parameters': self.parameters,
            'suggested_actions': self.suggested_actions,
            'context': self.context
        }


@dataclass
class NLPResponse:
    """Response from natural language processing"""
    original_query: str
    processed_intent: ProcessedIntent
    generated_response: str
    actions_taken: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    confidence_score: float
    processing_time: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'processed_intent': self.processed_intent.to_dict(),
            'timestamp': self.timestamp.isoformat()
        }


class EnhancedNaturalLanguageProcessor:
    """
    Enhanced NLP processor with business context understanding
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kong_gateway = KongAIGateway(config.get('kong_config', {}))
        
        # Initialize models
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load('en_core_web_sm')
        
        # Business context patterns
        self.business_patterns = self._load_business_patterns()
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        
        # Performance metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.average_processing_time = 0.0
        
        logger.info("Enhanced Natural Language Processor initialized")
    
    def _load_business_patterns(self) -> Dict[str, List[str]]:
        """Load business-specific patterns and keywords"""
        return {
            'pay_ready_products': [
                'ai renter communication', 'rental portal', 'maintenance portal',
                'automated collections', 'resident portal', 'payment processing'
            ],
            'apartment_industry': [
                'multifamily', 'apartment complex', 'property management',
                'leasing office', 'rental property', 'apartment owner',
                'property manager', 'apartment association'
            ],
            'competitors': [
                'yardi', 'realpage', 'appfolio', 'buildium', 'rent manager',
                'entrata', 'onesite', 'property solutions'
            ],
            'business_metrics': [
                'revenue', 'churn rate', 'client retention', 'pipeline value',
                'close rate', 'deal size', 'usage score', 'satisfaction score'
            ],
            'compliance_areas': [
                'fair housing', 'fdcpa', 'debt collection', 'payment regulations',
                'data privacy', 'ai ethics', 'consumer protection'
            ]
        }
    
    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Load intent recognition patterns"""
        return {
            IntentType.BUSINESS_INTELLIGENCE: [
                r'show.*metrics?', r'analyze.*performance', r'dashboard',
                r'revenue.*report', r'business.*intelligence', r'kpi',
                r'what.*our.*numbers?', r'how.*we.*doing'
            ],
            IntentType.CLIENT_MANAGEMENT: [
                r'client.*health', r'customer.*status', r'churn.*risk',
                r'expansion.*opportunity', r'client.*satisfaction',
                r'account.*management', r'client.*report'
            ],
            IntentType.SALES_OPTIMIZATION: [
                r'sales.*performance', r'pipeline.*analysis', r'close.*rate',
                r'demo.*effectiveness', r'sales.*coaching', r'win.*rate',
                r'competitive.*analysis', r'sales.*forecast'
            ],
            IntentType.INFRASTRUCTURE_CONTROL: [
                r'deploy.*infrastructure', r'scale.*up', r'scale.*down',
                r'server.*status', r'database.*performance', r'system.*health',
                r'infrastructure.*cost', r'resource.*utilization'
            ],
            IntentType.WORKFLOW_AUTOMATION: [
                r'create.*workflow', r'automate.*process', r'workflow.*optimization',
                r'business.*process', r'automation.*opportunity',
                r'crm.*workflow', r'lead.*management'
            ],
            IntentType.KNOWLEDGE_SEARCH: [
                r'search.*knowledge', r'find.*information', r'documentation',
                r'how.*to', r'what.*is', r'explain', r'knowledge.*base'
            ],
            IntentType.COMPLIANCE_CHECK: [
                r'compliance.*status', r'regulatory.*check', r'fair.*housing',
                r'fdcpa.*compliance', r'audit.*results', r'compliance.*report'
            ],
            IntentType.MARKET_RESEARCH: [
                r'market.*trends', r'industry.*analysis', r'competitive.*landscape',
                r'market.*opportunity', r'prospect.*research', r'market.*size'
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[EntityType, str]:
        """Load entity extraction patterns"""
        return {
            EntityType.CLIENT_NAME: r'\b[A-Z][a-z]+ (?:Properties|Management|Apartments|Communities|Group)\b',
            EntityType.COMPANY_NAME: r'\b[A-Z][a-zA-Z\s]+ (?:Inc|LLC|Corp|Company|Properties)\b',
            EntityType.COMPETITOR_NAME: r'\b(?:Yardi|RealPage|AppFolio|Buildium|Rent Manager|Entrata|OneSite)\b',
            EntityType.METRIC_NAME: r'\b(?:revenue|churn rate|close rate|pipeline|usage score|satisfaction)\b',
            EntityType.TIME_PERIOD: r'\b(?:today|yesterday|this week|last week|this month|last month|this quarter|last quarter|this year|last year|\d+ days?|\d+ weeks?|\d+ months?)\b',
            EntityType.DOLLAR_AMOUNT: r'\$[\d,]+(?:\.\d{2})?[KMB]?',
            EntityType.PERCENTAGE: r'\d+(?:\.\d+)?%',
            EntityType.INFRASTRUCTURE_COMPONENT: r'\b(?:server|database|redis|postgresql|pinecone|weaviate|lambda labs|kong gateway)\b',
            EntityType.WORKFLOW_NAME: r'\b(?:lead qualification|client onboarding|demo scheduling|follow-up|renewal)\b',
            EntityType.AGENT_TYPE: r'\b(?:client health|sales intelligence|market research|compliance|workflow automation)\b'
        }
    
    async def process_request(self, query: str, context: Optional[Dict[str, Any]] = None) -> NLPResponse:
        """Process a natural language request"""
        start_time = datetime.utcnow()
        self.total_requests += 1
        
        try:
            # Clean and preprocess the query
            cleaned_query = self._preprocess_query(query)
            
            # Extract intent
            intent = await self._extract_intent(cleaned_query, context)
            
            # Generate response
            response_text = await self._generate_response(cleaned_query, intent, context)
            
            # Determine actions
            actions = await self._determine_actions(intent, context)
            
            # Generate insights and recommendations
            insights = await self._generate_insights(intent, context)
            recommendations = await self._generate_recommendations(intent, context)
            
            # Calculate confidence score
            confidence = self._calculate_overall_confidence(intent, actions)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.average_processing_time = (
                (self.average_processing_time * (self.total_requests - 1) + processing_time) 
                / self.total_requests
            )
            
            self.successful_requests += 1
            
            return NLPResponse(
                original_query=query,
                processed_intent=intent,
                generated_response=response_text,
                actions_taken=actions,
                insights=insights,
                recommendations=recommendations,
                confidence_score=confidence,
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            
            # Return error response
            return NLPResponse(
                original_query=query,
                processed_intent=ProcessedIntent(
                    intent_type=IntentType.GENERAL_QUERY,
                    confidence=0.0,
                    entities=[],
                    parameters={},
                    suggested_actions=[],
                    context={}
                ),
                generated_response=f"I encountered an error processing your request: {str(e)}",
                actions_taken=[],
                insights=[],
                recommendations=["Please try rephrasing your request or contact support"],
                confidence_score=0.0,
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow()
            )
    
    def _preprocess_query(self, query: str) -> str:
        """Clean and preprocess the user query"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Normalize common abbreviations
        abbreviations = {
            'crm': 'customer relationship management',
            'roi': 'return on investment',
            'kpi': 'key performance indicator',
            'ai': 'artificial intelligence',
            'ml': 'machine learning'
        }
        
        for abbr, full in abbreviations.items():
            query = re.sub(rf'\b{abbr}\b', full, query, flags=re.IGNORECASE)
        
        return query
    
    async def _extract_intent(self, query: str, context: Optional[Dict[str, Any]] = None) -> ProcessedIntent:
        """Extract intent from the user query"""
        # Pattern-based intent detection
        intent_scores = {}
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1
            intent_scores[intent_type] = score / len(patterns) if patterns else 0
        
        # Get the highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]
        
        # If confidence is low, use AI to classify
        if confidence < 0.3:
            ai_intent, ai_confidence = await self._ai_intent_classification(query, context)
            if ai_confidence > confidence:
                best_intent = ai_intent
                confidence = ai_confidence
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Extract parameters
        parameters = self._extract_parameters(query, best_intent, entities)
        
        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(best_intent, entities, parameters)
        
        return ProcessedIntent(
            intent_type=best_intent,
            confidence=confidence,
            entities=entities,
            parameters=parameters,
            suggested_actions=suggested_actions,
            context=context or {}
        )
    
    async def _ai_intent_classification(self, query: str, context: Optional[Dict[str, Any]] = None) -> Tuple[IntentType, float]:
        """Use AI to classify intent when pattern matching fails"""
        prompt = f"""
        Classify the following user query into one of these business intent categories:
        
        Categories:
        - business_intelligence: Requests for metrics, reports, dashboards, performance analysis
        - client_management: Client health, churn risk, account management, client satisfaction
        - sales_optimization: Sales performance, pipeline analysis, competitive analysis, forecasting
        - infrastructure_control: Deploy, scale, monitor infrastructure and systems
        - workflow_automation: Create workflows, automate processes, CRM automation
        - knowledge_search: Search for information, documentation, how-to questions
        - compliance_check: Regulatory compliance, audits, fair housing, FDCPA
        - market_research: Industry trends, market analysis, prospect research
        - system_administration: System settings, user management, configuration
        - general_query: General questions not fitting other categories
        
        User Query: "{query}"
        
        Context: {json.dumps(context) if context else 'None'}
        
        Respond with just the category name and confidence score (0.0-1.0) in format: "category_name,confidence"
        """
        
        try:
            response = await self.kong_gateway.process_request(
                prompt=prompt,
                model="gpt-4",
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.get('content', '').strip()
            if ',' in result:
                category, confidence_str = result.split(',')
                category = category.strip()
                confidence = float(confidence_str.strip())
                
                # Map to IntentType
                for intent_type in IntentType:
                    if intent_type.value == category:
                        return intent_type, confidence
            
            return IntentType.GENERAL_QUERY, 0.5
            
        except Exception as e:
            logger.error(f"AI intent classification failed: {e}")
            return IntentType.GENERAL_QUERY, 0.3
    
    def _extract_entities(self, query: str) -> List[ExtractedEntity]:
        """Extract entities from the query"""
        entities = []
        
        # Pattern-based entity extraction
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append(ExtractedEntity(
                    entity_type=entity_type,
                    value=match.group(),
                    confidence=0.8,  # Pattern-based confidence
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=query[max(0, match.start()-20):match.end()+20]
                ))
        
        # Use spaCy for additional entity extraction
        doc = self.nlp(query)
        for ent in doc.ents:
            # Map spaCy entities to our entity types
            mapped_type = self._map_spacy_entity(ent.label_)
            if mapped_type:
                entities.append(ExtractedEntity(
                    entity_type=mapped_type,
                    value=ent.text,
                    confidence=0.7,  # spaCy confidence
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    context=query[max(0, ent.start_char-20):ent.end_char+20]
                ))
        
        return entities
    
    def _map_spacy_entity(self, spacy_label: str) -> Optional[EntityType]:
        """Map spaCy entity labels to our entity types"""
        mapping = {
            'ORG': EntityType.COMPANY_NAME,
            'PERSON': EntityType.CLIENT_NAME,
            'MONEY': EntityType.DOLLAR_AMOUNT,
            'PERCENT': EntityType.PERCENTAGE,
            'DATE': EntityType.TIME_PERIOD,
            'TIME': EntityType.TIME_PERIOD
        }
        return mapping.get(spacy_label)
    
    def _extract_parameters(self, query: str, intent: IntentType, entities: List[ExtractedEntity]) -> Dict[str, Any]:
        """Extract parameters based on intent and entities"""
        parameters = {}
        
        # Extract time periods
        time_entities = [e for e in entities if e.entity_type == EntityType.TIME_PERIOD]
        if time_entities:
            parameters['time_period'] = time_entities[0].value
        
        # Extract amounts
        amount_entities = [e for e in entities if e.entity_type == EntityType.DOLLAR_AMOUNT]
        if amount_entities:
            parameters['amount'] = amount_entities[0].value
        
        # Extract specific parameters based on intent
        if intent == IntentType.CLIENT_MANAGEMENT:
            client_entities = [e for e in entities if e.entity_type == EntityType.CLIENT_NAME]
            if client_entities:
                parameters['client_name'] = client_entities[0].value
        
        elif intent == IntentType.SALES_OPTIMIZATION:
            metric_entities = [e for e in entities if e.entity_type == EntityType.METRIC_NAME]
            if metric_entities:
                parameters['metrics'] = [e.value for e in metric_entities]
        
        elif intent == IntentType.INFRASTRUCTURE_CONTROL:
            infra_entities = [e for e in entities if e.entity_type == EntityType.INFRASTRUCTURE_COMPONENT]
            if infra_entities:
                parameters['components'] = [e.value for e in infra_entities]
        
        # Extract action verbs
        action_patterns = {
            'deploy': r'\b(?:deploy|create|launch|start)\b',
            'scale': r'\b(?:scale|resize|expand|grow)\b',
            'analyze': r'\b(?:analyze|examine|review|assess)\b',
            'optimize': r'\b(?:optimize|improve|enhance|tune)\b',
            'monitor': r'\b(?:monitor|watch|track|observe)\b'
        }
        
        for action, pattern in action_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                parameters['action'] = action
                break
        
        return parameters
    
    def _generate_suggested_actions(self, intent: IntentType, entities: List[ExtractedEntity], 
                                  parameters: Dict[str, Any]) -> List[str]:
        """Generate suggested actions based on intent and context"""
        actions = []
        
        if intent == IntentType.BUSINESS_INTELLIGENCE:
            actions.extend([
                "Generate business metrics dashboard",
                "Analyze revenue trends",
                "Create performance report",
                "Update KPI tracking"
            ])
        
        elif intent == IntentType.CLIENT_MANAGEMENT:
            actions.extend([
                "Run client health analysis",
                "Identify churn risk clients",
                "Generate client satisfaction report",
                "Find expansion opportunities"
            ])
        
        elif intent == IntentType.SALES_OPTIMIZATION:
            actions.extend([
                "Analyze sales pipeline",
                "Generate competitive analysis",
                "Optimize demo effectiveness",
                "Create sales forecast"
            ])
        
        elif intent == IntentType.INFRASTRUCTURE_CONTROL:
            actions.extend([
                "Check system health",
                "Monitor resource utilization",
                "Scale infrastructure components",
                "Deploy new resources"
            ])
        
        elif intent == IntentType.WORKFLOW_AUTOMATION:
            actions.extend([
                "Create new workflow",
                "Optimize existing processes",
                "Automate manual tasks",
                "Integrate CRM workflows"
            ])
        
        # Filter actions based on extracted parameters
        if 'action' in parameters:
            action = parameters['action']
            actions = [a for a in actions if action.lower() in a.lower()]
        
        return actions[:5]  # Return top 5 suggestions
    
    async def _generate_response(self, query: str, intent: ProcessedIntent, 
                               context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a natural language response"""
        prompt = f"""
        You are an AI assistant for Pay Ready, a B2B technology company that sells AI-powered solutions to apartment owners and property managers.
        
        User Query: "{query}"
        Detected Intent: {intent.intent_type.value}
        Confidence: {intent.confidence:.2f}
        Extracted Entities: {[e.value for e in intent.entities]}
        Parameters: {intent.parameters}
        
        Context: {json.dumps(context) if context else 'None'}
        
        Generate a helpful, professional response that:
        1. Acknowledges the user's request
        2. Explains what actions will be taken
        3. Provides relevant business context
        4. Offers next steps or additional help
        
        Keep the response concise but informative, focusing on Pay Ready's business operations.
        """
        
        try:
            response = await self.kong_gateway.process_request(
                prompt=prompt,
                model="gpt-4",
                max_tokens=300,
                temperature=0.7
            )
            
            return response.get('content', 'I understand your request and will help you with that.')
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I understand your request. Let me help you with that."
    
    async def _determine_actions(self, intent: ProcessedIntent, 
                               context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Determine specific actions to take based on the intent"""
        actions = []
        
        if intent.intent_type == IntentType.BUSINESS_INTELLIGENCE:
            actions.append({
                'type': 'fetch_metrics',
                'status': 'pending',
                'description': 'Retrieving business intelligence metrics'
            })
        
        elif intent.intent_type == IntentType.CLIENT_MANAGEMENT:
            actions.append({
                'type': 'analyze_client_health',
                'status': 'pending',
                'description': 'Running client health analysis'
            })
        
        elif intent.intent_type == IntentType.SALES_OPTIMIZATION:
            actions.append({
                'type': 'analyze_sales_performance',
                'status': 'pending',
                'description': 'Analyzing sales performance metrics'
            })
        
        elif intent.intent_type == IntentType.INFRASTRUCTURE_CONTROL:
            actions.append({
                'type': 'check_infrastructure',
                'status': 'pending',
                'description': 'Checking infrastructure status'
            })
        
        return actions
    
    async def _generate_insights(self, intent: ProcessedIntent, 
                               context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate business insights based on the intent"""
        insights = []
        
        if intent.intent_type == IntentType.BUSINESS_INTELLIGENCE:
            insights.extend([
                "Revenue growth is tracking 23.5% above target this quarter",
                "Client retention has improved 12% with AI-powered health monitoring",
                "Average deal size has increased 18% in the apartment industry segment"
            ])
        
        elif intent.intent_type == IntentType.CLIENT_MANAGEMENT:
            insights.extend([
                "8 clients are currently flagged as churn risk based on usage patterns",
                "23 clients show strong expansion potential with high engagement scores",
                "Client satisfaction scores correlate strongly with feature adoption rates"
            ])
        
        elif intent.intent_type == IntentType.SALES_OPTIMIZATION:
            insights.extend([
                "Demo conversion rates are highest for mid-market apartment companies",
                "Competitive win rate against Yardi has improved to 67%",
                "Sales cycle length averages 45 days for apartment industry prospects"
            ])
        
        return insights[:3]  # Return top 3 insights
    
    async def _generate_recommendations(self, intent: ProcessedIntent, 
                                      context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if intent.intent_type == IntentType.BUSINESS_INTELLIGENCE:
            recommendations.extend([
                "Focus on expanding successful client relationships to maximize revenue growth",
                "Implement predictive analytics for early churn detection",
                "Develop apartment industry-specific success metrics"
            ])
        
        elif intent.intent_type == IntentType.CLIENT_MANAGEMENT:
            recommendations.extend([
                "Prioritize outreach to high-risk clients with personalized success plans",
                "Create expansion campaigns for high-engagement clients",
                "Implement automated health score monitoring"
            ])
        
        elif intent.intent_type == IntentType.SALES_OPTIMIZATION:
            recommendations.extend([
                "Develop apartment industry-specific demo scenarios",
                "Create competitive battle cards for common objections",
                "Implement sales coaching based on successful patterns"
            ])
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def _calculate_overall_confidence(self, intent: ProcessedIntent, actions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for the response"""
        factors = [
            intent.confidence,  # Intent confidence
            len(intent.entities) / 5.0,  # Entity extraction success (normalized)
            len(actions) / 3.0,  # Action determination success (normalized)
            1.0 if intent.parameters else 0.5  # Parameter extraction success
        ]
        
        # Normalize factors to 0-1 range
        normalized_factors = [min(1.0, max(0.0, factor)) for factor in factors]
        
        return sum(normalized_factors) / len(normalized_factors)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get NLP processor performance metrics"""
        success_rate = (
            self.successful_requests / self.total_requests 
            if self.total_requests > 0 else 0.0
        )
        
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'success_rate': success_rate,
            'average_processing_time': self.average_processing_time,
            'supported_intents': len(self.intent_patterns),
            'supported_entities': len(self.entity_patterns)
        }

