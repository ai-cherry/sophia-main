"""
Sophia AI - Advanced Multi-Strategy Chunking Pipeline
Implements comprehensive metadata extraction and chunking for business intelligence
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .speaker_boundary_chunker import SpeakerBoundaryChunker
from .topic_boundary_chunker import TopicBoundaryChunker
from .decision_point_chunker import DecisionPointChunker
from .emotional_boundary_chunker import EmotionalBoundaryChunker
from .business_intelligence_extractor import BusinessIntelligenceExtractor
from .sentiment_analyzer import SentimentAnalyzer
from .decision_maker_extractor import DecisionMakerExtractor
from .real_time_processor import RealTimeProcessor
from .context_preserver import ContextPreserver
from .hierarchical_topic_classifier import HierarchicalTopicClassifier
from .ai_agent_integration import AIAgentIntegration

logger = logging.getLogger(__name__)

@dataclass
class SophiaEnhancedMetadata:
    """Comprehensive metadata for Sophia AI chunks"""
    
    # Core identification
    chunk_id: str
    source_id: str
    content_type: str  # gong_call, slack_message, hubspot_contact, document
    chunk_index: int
    
    # Speaker and conversation context
    speaker: Optional[str]
    conversation_context: Dict[str, Any]
    full_context_available: bool
    
    # Topic classification (hierarchical)
    primary_topic: str
    secondary_topics: List[str]
    subtopics: List[str]
    topic_confidence: float
    
    # Business intelligence
    business_intelligence: Dict[str, Any]
    revenue_potential: float
    technology_relevance: float
    performance_impact: float
    
    # Decision and action tracking
    decision_makers: List[str]
    action_items: List[str]
    requires_follow_up: bool
    decision_value: Optional[float]
    
    # Sentiment and emotional context
    sentiment_score: float
    primary_emotion: Optional[str]
    emotion_intensity: float
    emotional_shift: bool
    
    # Temporal context
    created_timestamp: datetime
    urgency_level: str  # immediate, short_term, medium_term, long_term
    time_sensitivity: str  # high, medium, low
    
    # Quality and processing
    confidence_score: float
    processing_mode: str  # realtime, basic, enhanced
    processing_time: float
    
    # Integration metadata
    ai_agent_ready: bool
    slack_notification_triggered: bool
    crm_update_required: bool

class SophiaChunkingPipeline:
    """Sophia AI - Advanced Multi-Strategy Chunking Pipeline"""
    
    def __init__(self):
        # Core chunking strategies
        self.speaker_chunker = SpeakerBoundaryChunker()
        self.topic_chunker = TopicBoundaryChunker()
        self.decision_chunker = DecisionPointChunker()
        self.emotional_chunker = EmotionalBoundaryChunker()
        
        # Business intelligence extractors
        self.business_intelligence = BusinessIntelligenceExtractor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.decision_maker_extractor = DecisionMakerExtractor()
        
        # Real-time processors
        self.real_time_processor = RealTimeProcessor()
        self.context_preserver = ContextPreserver()
        
        # Topic classification
        self.topic_classifier = HierarchicalTopicClassifier()
        
        # AI agent integration
        self.ai_agent_integration = AIAgentIntegration()
        
        logger.info("Sophia Chunking Pipeline initialized")
    
    async def process_content(
        self, 
        content: str, 
        content_type: str,
        source_id: str,
        priority: str = "normal"
    ) -> List[Dict[str, Any]]:
        """Process content through multi-strategy pipeline"""
        
        # Real-time processing with context preservation
        start_time = time.time()
        
        try:
            # 1. Initial chunking by primary boundaries
            primary_chunks = await self._create_primary_chunks(content, content_type)
            
            # 2. Apply business intelligence extraction
            enhanced_chunks = await self._enhance_with_business_intelligence(
                primary_chunks, content_type, source_id
            )
            
            # 3. Preserve conversation context
            context_enhanced_chunks = await self._preserve_context(enhanced_chunks)
            
            # 4. Real-time metadata extraction
            final_chunks = await self._extract_comprehensive_metadata(
                context_enhanced_chunks, priority
            )
            
            # 5. AI agent integration
            ai_enhanced_chunks = await self.ai_agent_integration.process_with_ai_agents(
                final_chunks
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Processed {len(ai_enhanced_chunks)} chunks in {processing_time:.2f}s")
            
            return ai_enhanced_chunks
            
        except Exception as e:
            logger.error(f"Error in chunking pipeline: {str(e)}")
            # Fall back to basic processing
            return await self._basic_processing(content, content_type, source_id)
    
    async def _create_primary_chunks(
        self, 
        content: str, 
        content_type: str
    ) -> List[Dict[str, Any]]:
        """Create primary chunks using speaker boundaries"""
        
        if content_type == "gong_call":
            # Use speaker boundary chunking for call transcripts
            chunks = await self.speaker_chunker.chunk_by_speaker_boundaries(content)
        elif content_type == "slack_message":
            # Use topic boundary chunking for Slack messages
            chunks = await self.topic_chunker.chunk_by_topic_boundaries(content)
        else:
            # Default to topic-based chunking
            chunks = await self.topic_chunker.chunk_by_topic_boundaries(content)
        
        # Apply decision point chunking
        decision_chunks = await self.decision_chunker.chunk_around_decisions(chunks)
        
        # Apply emotional boundary chunking
        emotional_chunks = await self.emotional_chunker.chunk_by_emotional_shifts(decision_chunks)
        
        return emotional_chunks
    
    async def _enhance_with_business_intelligence(
        self, 
        chunks: List[Dict[str, Any]], 
        content_type: str,
        source_id: str
    ) -> List[Dict[str, Any]]:
        """Enhance chunks with business intelligence extraction"""
        
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Extract business intelligence
            bi_data = await self.business_intelligence.extract_business_intelligence([chunk])
            
            # Extract sentiment
            sentiment_data = await self.sentiment_analyzer.analyze_sentiment(chunk["text"])
            
            # Extract decision makers
            decision_makers = await self.decision_maker_extractor.extract_decision_makers(chunk["text"])
            
            # Classify topics hierarchically
            topic_data = await self.topic_classifier.classify_topics_hierarchically(chunk["text"])
            
            enhanced_chunk = {
                **chunk,
                "source_id": source_id,
                "content_type": content_type,
                "chunk_index": i,
                "business_intelligence": bi_data[0] if bi_data else {},
                "sentiment_score": sentiment_data.get("score", 0.0),
                "primary_emotion": sentiment_data.get("primary_emotion"),
                "emotion_intensity": sentiment_data.get("intensity", 0.0),
                "decision_makers": decision_makers,
                "primary_topic": topic_data.get("primary_topic", "general"),
                "secondary_topics": topic_data.get("secondary_topics", []),
                "subtopics": topic_data.get("subtopics", []),
                "topic_confidence": topic_data.get("confidence_scores", {}).get("overall", 0.0)
            }
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    async def _preserve_context(
        self, 
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Preserve conversation context across chunks"""
        
        return await self.context_preserver.preserve_context(chunks)
    
    async def _extract_comprehensive_metadata(
        self, 
        chunks: List[Dict[str, Any]], 
        priority: str
    ) -> List[Dict[str, Any]]:
        """Extract comprehensive metadata for each chunk"""
        
        final_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Create enhanced metadata
            metadata = SophiaEnhancedMetadata(
                chunk_id=f"{chunk.get('content_type', 'unknown')}_{i}_{uuid.uuid4().hex[:8]}",
                source_id=chunk.get("source_id", ""),
                content_type=chunk.get("content_type", "unknown"),
                chunk_index=i,
                speaker=chunk.get("speaker"),
                conversation_context=chunk.get("conversation_context", {}),
                full_context_available=chunk.get("full_context_available", False),
                primary_topic=chunk.get("primary_topic", "general"),
                secondary_topics=chunk.get("secondary_topics", []),
                subtopics=chunk.get("subtopics", []),
                topic_confidence=chunk.get("topic_confidence", 0.0),
                business_intelligence=chunk.get("business_intelligence", {}),
                revenue_potential=chunk.get("business_intelligence", {}).get("financial", {}).get("revenue_potential", 0.0),
                technology_relevance=chunk.get("business_intelligence", {}).get("technology", {}).get("relevance_score", 0.0),
                performance_impact=chunk.get("business_intelligence", {}).get("performance", {}).get("impact_score", 0.0),
                decision_makers=chunk.get("decision_makers", []),
                action_items=chunk.get("action_items", []),
                requires_follow_up=chunk.get("requires_follow_up", False),
                decision_value=chunk.get("decision_value"),
                sentiment_score=chunk.get("sentiment_score", 0.0),
                primary_emotion=chunk.get("primary_emotion"),
                emotion_intensity=chunk.get("emotion_intensity", 0.0),
                emotional_shift=chunk.get("emotional_shift", False),
                created_timestamp=datetime.now(),
                urgency_level=self._determine_urgency_level(chunk),
                time_sensitivity=self._determine_time_sensitivity(chunk),
                confidence_score=chunk.get("confidence_score", 0.8),
                processing_mode="realtime" if priority == "high" else "enhanced",
                processing_time=0.0,  # Will be set by caller
                ai_agent_ready=True,
                slack_notification_triggered=False,
                crm_update_required=False
            )
            
            final_chunk = {
                "text": chunk.get("text", ""),
                "metadata": asdict(metadata),
                "chunk_type": chunk.get("chunk_type", "semantic"),
                "source_id": chunk.get("source_id", ""),
                "content_type": chunk.get("content_type", "unknown")
            }
            
            final_chunks.append(final_chunk)
        
        return final_chunks
    
    def _determine_urgency_level(self, chunk: Dict[str, Any]) -> str:
        """Determine urgency level based on chunk content"""
        
        text = chunk.get("text", "").lower()
        
        # Immediate urgency indicators
        immediate_indicators = ["asap", "urgent", "emergency", "critical", "now", "immediately"]
        if any(indicator in text for indicator in immediate_indicators):
            return "immediate"
        
        # Short-term urgency indicators
        short_term_indicators = ["this week", "next week", "soon", "quickly", "fast"]
        if any(indicator in text for indicator in short_term_indicators):
            return "short_term"
        
        # Medium-term indicators
        medium_term_indicators = ["this month", "next month", "quarter", "timeline"]
        if any(indicator in text for indicator in medium_term_indicators):
            return "medium_term"
        
        return "long_term"
    
    def _determine_time_sensitivity(self, chunk: Dict[str, Any]) -> str:
        """Determine time sensitivity based on chunk content"""
        
        urgency_level = self._determine_urgency_level(chunk)
        
        if urgency_level == "immediate":
            return "high"
        elif urgency_level == "short_term":
            return "medium"
        else:
            return "low"
    
    async def _basic_processing(
        self, 
        content: str, 
        content_type: str,
        source_id: str
    ) -> List[Dict[str, Any]]:
        """Basic processing fallback"""
        
        logger.warning("Using basic processing fallback")
        
        # Simple chunking by sentences
        sentences = content.split('.')
        chunks = []
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                chunk = {
                    "text": sentence.strip(),
                    "metadata": asdict(SophiaEnhancedMetadata(
                        chunk_id=f"basic_{i}_{uuid.uuid4().hex[:8]}",
                        source_id=source_id,
                        content_type=content_type,
                        chunk_index=i,
                        speaker=None,
                        conversation_context={},
                        full_context_available=False,
                        primary_topic="general",
                        secondary_topics=[],
                        subtopics=[],
                        topic_confidence=0.5,
                        business_intelligence={},
                        revenue_potential=0.0,
                        technology_relevance=0.0,
                        performance_impact=0.0,
                        decision_makers=[],
                        action_items=[],
                        requires_follow_up=False,
                        decision_value=None,
                        sentiment_score=0.0,
                        primary_emotion=None,
                        emotion_intensity=0.0,
                        emotional_shift=False,
                        created_timestamp=datetime.now(),
                        urgency_level="long_term",
                        time_sensitivity="low",
                        confidence_score=0.5,
                        processing_mode="basic",
                        processing_time=0.0,
                        ai_agent_ready=False,
                        slack_notification_triggered=False,
                        crm_update_required=False
                    )),
                    "chunk_type": "basic",
                    "source_id": source_id,
                    "content_type": content_type
                }
                chunks.append(chunk)
        
        return chunks 