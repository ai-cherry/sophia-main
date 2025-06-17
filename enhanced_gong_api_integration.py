#!/usr/bin/env python3
"""
Enhanced Gong API Integration with OAuth
Implements advanced features: transcripts, media, webhooks, interaction stats
"""

import os
import json
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationTranscript:
    """Data class for conversation transcript"""
    call_id: str
    transcript_segments: List[Dict[str, Any]]
    speakers: List[Dict[str, str]]
    duration: int
    language: str
    confidence_score: float

@dataclass
class MediaFile:
    """Data class for media file information"""
    call_id: str
    media_url: str
    media_type: str  # audio, video
    duration: int
    file_size: int
    download_expires_at: datetime

@dataclass
class InteractionStats:
    """Data class for interaction statistics"""
    call_id: str
    talk_time_percentage: float
    longest_monologue: int
    questions_asked: int
    interruptions: int
    sentiment_score: float
    engagement_score: float

class EnhancedGongIntegration:
    """
    Enhanced Gong API integration with OAuth authentication
    Provides access to premium features: transcripts, media, webhooks
    """
    
    def __init__(self, oauth_manager):
        self.oauth_manager = oauth_manager
        self.base_url = "https://us-70092.api.gong.io"
        
        # Database configuration
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "database": "sophia_enhanced"
        }
    
    async def setup_enhanced_schema(self):
        """Create enhanced database schema for OAuth features"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Create conversation transcripts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_transcripts (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) UNIQUE NOT NULL,
                    transcript_data JSONB NOT NULL,
                    speakers JSONB,
                    duration INTEGER,
                    language VARCHAR(10),
                    confidence_score FLOAT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    apartment_keywords_count INTEGER DEFAULT 0,
                    apartment_relevance_score FLOAT DEFAULT 0.0,
                    key_topics JSONB,
                    sentiment_analysis JSONB,
                    action_items JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create media files table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_media (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) NOT NULL,
                    media_url TEXT NOT NULL,
                    media_type VARCHAR(50),
                    duration INTEGER,
                    file_size BIGINT,
                    download_expires_at TIMESTAMP,
                    local_file_path TEXT,
                    download_status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create interaction statistics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS interaction_statistics (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) UNIQUE NOT NULL,
                    talk_time_percentage FLOAT,
                    longest_monologue INTEGER,
                    questions_asked INTEGER,
                    interruptions INTEGER,
                    sentiment_score FLOAT,
                    engagement_score FLOAT,
                    speaking_pace FLOAT,
                    filler_words_count INTEGER,
                    energy_level FLOAT,
                    apartment_industry_score FLOAT DEFAULT 0.0,
                    competitive_mentions JSONB,
                    objection_handling JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create webhook events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    call_id VARCHAR(255),
                    user_id VARCHAR(255),
                    workspace_id VARCHAR(255),
                    event_data JSONB NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    processed_at TIMESTAMP,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create enhanced call analytics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_call_analytics (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) UNIQUE NOT NULL,
                    apartment_relevance_score FLOAT DEFAULT 0.0,
                    deal_stage VARCHAR(100),
                    win_probability FLOAT,
                    competitive_threats JSONB,
                    key_decision_makers JSONB,
                    pain_points_identified JSONB,
                    solution_fit_score FLOAT,
                    next_steps JSONB,
                    follow_up_required BOOLEAN DEFAULT FALSE,
                    follow_up_date DATE,
                    revenue_potential DECIMAL(12,2),
                    apartment_units_discussed INTEGER,
                    property_type VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_call_id ON conversation_transcripts(call_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_apartment_score ON conversation_transcripts(apartment_relevance_score)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_media_call_id ON conversation_media(call_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_call_id ON interaction_statistics(call_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_webhooks_event_type ON webhook_events(event_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_call_id ON enhanced_call_analytics(call_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_apartment_score ON enhanced_call_analytics(apartment_relevance_score)")
            
            await conn.close()
            
            logger.info("Enhanced database schema created successfully")
            
        except Exception as e:
            logger.error(f"Error setting up enhanced schema: {str(e)}")
            raise
    
    async def get_conversation_transcript(self, call_id: str) -> Optional[ConversationTranscript]:
        """Get full conversation transcript with speaker identification"""
        
        try:
            # Make authenticated request to transcript endpoint
            result = await self.oauth_manager.make_authenticated_request(
                f"/v2/calls/{call_id}/transcript",
                "GET"
            )
            
            if result["success"]:
                transcript_data = result["data"]
                
                # Process transcript data
                transcript = ConversationTranscript(
                    call_id=call_id,
                    transcript_segments=transcript_data.get("entries", []),
                    speakers=transcript_data.get("speakers", []),
                    duration=transcript_data.get("callDuration", 0),
                    language=transcript_data.get("language", "en"),
                    confidence_score=transcript_data.get("confidence", 0.0)
                )
                
                # Store in database
                await self._store_transcript(transcript)
                
                # Analyze for apartment industry relevance
                await self._analyze_transcript_relevance(transcript)
                
                return transcript
            else:
                logger.error(f"Failed to get transcript for call {call_id}: {result['error']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting transcript for call {call_id}: {str(e)}")
            return None
    
    async def get_conversation_media(self, call_id: str) -> Optional[MediaFile]:
        """Get media file URL for conversation"""
        
        try:
            # Make authenticated request to media endpoint
            result = await self.oauth_manager.make_authenticated_request(
                f"/v2/calls/{call_id}/media-url",
                "GET"
            )
            
            if result["success"]:
                media_data = result["data"]
                
                # Process media data
                media_file = MediaFile(
                    call_id=call_id,
                    media_url=media_data.get("mediaUrl", ""),
                    media_type=media_data.get("mediaType", "audio"),
                    duration=media_data.get("duration", 0),
                    file_size=media_data.get("fileSize", 0),
                    download_expires_at=datetime.fromisoformat(
                        media_data.get("expiresAt", datetime.utcnow().isoformat())
                    )
                )
                
                # Store in database
                await self._store_media_file(media_file)
                
                return media_file
            else:
                logger.error(f"Failed to get media for call {call_id}: {result['error']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting media for call {call_id}: {str(e)}")
            return None
    
    async def get_interaction_statistics(self, call_id: str) -> Optional[InteractionStats]:
        """Get detailed interaction statistics for conversation"""
        
        try:
            # Make authenticated request to interaction stats endpoint
            result = await self.oauth_manager.make_authenticated_request(
                f"/v2/stats/interaction",
                "GET",
                params={"callId": call_id}
            )
            
            if result["success"]:
                stats_data = result["data"]
                
                # Process interaction statistics
                stats = InteractionStats(
                    call_id=call_id,
                    talk_time_percentage=stats_data.get("talkTimePercentage", 0.0),
                    longest_monologue=stats_data.get("longestMonologue", 0),
                    questions_asked=stats_data.get("questionsAsked", 0),
                    interruptions=stats_data.get("interruptions", 0),
                    sentiment_score=stats_data.get("sentimentScore", 0.0),
                    engagement_score=stats_data.get("engagementScore", 0.0)
                )
                
                # Store in database
                await self._store_interaction_stats(stats)
                
                # Analyze for apartment industry insights
                await self._analyze_interaction_insights(stats)
                
                return stats
            else:
                logger.error(f"Failed to get interaction stats for call {call_id}: {result['error']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting interaction stats for call {call_id}: {str(e)}")
            return None
    
    async def get_extensive_call_data(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get extensive call data with all available information"""
        
        try:
            # Make authenticated request to extensive endpoint
            result = await self.oauth_manager.make_authenticated_request(
                f"/v2/calls/{call_id}/extensive",
                "GET"
            )
            
            if result["success"]:
                extensive_data = result["data"]
                
                # Store extensive data
                await self._store_extensive_call_data(call_id, extensive_data)
                
                return extensive_data
            else:
                logger.error(f"Failed to get extensive data for call {call_id}: {result['error']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting extensive data for call {call_id}: {str(e)}")
            return None
    
    async def process_all_conversations_enhanced(self, limit: int = 100) -> Dict[str, Any]:
        """Process all conversations with enhanced features"""
        
        try:
            # Get list of calls
            calls_result = await self.oauth_manager.make_authenticated_request(
                "/v2/calls",
                "GET",
                params={
                    "fromDateTime": "2024-01-01T00:00:00Z",
                    "toDateTime": "2024-12-31T23:59:59Z",
                    "limit": limit
                }
            )
            
            if not calls_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to get calls list",
                    "details": calls_result["error"]
                }
            
            calls = calls_result["data"].get("calls", [])
            
            processing_results = {
                "total_calls": len(calls),
                "transcripts_processed": 0,
                "media_files_processed": 0,
                "interaction_stats_processed": 0,
                "extensive_data_processed": 0,
                "errors": [],
                "apartment_relevant_calls": 0
            }
            
            # Process each call with enhanced features
            for call in calls:
                call_id = call.get("id")
                
                if not call_id:
                    continue
                
                try:
                    # Get transcript
                    transcript = await self.get_conversation_transcript(call_id)
                    if transcript:
                        processing_results["transcripts_processed"] += 1
                    
                    # Get media file
                    media = await self.get_conversation_media(call_id)
                    if media:
                        processing_results["media_files_processed"] += 1
                    
                    # Get interaction statistics
                    stats = await self.get_interaction_statistics(call_id)
                    if stats:
                        processing_results["interaction_stats_processed"] += 1
                    
                    # Get extensive data
                    extensive = await self.get_extensive_call_data(call_id)
                    if extensive:
                        processing_results["extensive_data_processed"] += 1
                    
                    # Check apartment relevance
                    relevance_score = await self._calculate_apartment_relevance(call_id)
                    if relevance_score > 0.7:
                        processing_results["apartment_relevant_calls"] += 1
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    error_msg = f"Error processing call {call_id}: {str(e)}"
                    logger.error(error_msg)
                    processing_results["errors"].append(error_msg)
            
            processing_results["success"] = True
            processing_results["processing_rate"] = {
                "transcripts": f"{processing_results['transcripts_processed']}/{processing_results['total_calls']}",
                "media": f"{processing_results['media_files_processed']}/{processing_results['total_calls']}",
                "stats": f"{processing_results['interaction_stats_processed']}/{processing_results['total_calls']}",
                "extensive": f"{processing_results['extensive_data_processed']}/{processing_results['total_calls']}"
            }
            
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing conversations: {str(e)}")
            return {
                "success": False,
                "error": "Processing failed",
                "details": str(e)
            }
    
    async def _store_transcript(self, transcript: ConversationTranscript):
        """Store conversation transcript in database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                INSERT INTO conversation_transcripts 
                (call_id, transcript_data, speakers, duration, language, confidence_score)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (call_id) DO UPDATE SET
                    transcript_data = EXCLUDED.transcript_data,
                    speakers = EXCLUDED.speakers,
                    duration = EXCLUDED.duration,
                    language = EXCLUDED.language,
                    confidence_score = EXCLUDED.confidence_score,
                    updated_at = CURRENT_TIMESTAMP
            """,
                transcript.call_id,
                json.dumps(transcript.transcript_segments),
                json.dumps(transcript.speakers),
                transcript.duration,
                transcript.language,
                transcript.confidence_score
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error storing transcript: {str(e)}")
            raise
    
    async def _store_media_file(self, media_file: MediaFile):
        """Store media file information in database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                INSERT INTO conversation_media 
                (call_id, media_url, media_type, duration, file_size, download_expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (call_id, media_url) DO UPDATE SET
                    media_type = EXCLUDED.media_type,
                    duration = EXCLUDED.duration,
                    file_size = EXCLUDED.file_size,
                    download_expires_at = EXCLUDED.download_expires_at,
                    updated_at = CURRENT_TIMESTAMP
            """,
                media_file.call_id,
                media_file.media_url,
                media_file.media_type,
                media_file.duration,
                media_file.file_size,
                media_file.download_expires_at
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error storing media file: {str(e)}")
            raise
    
    async def _store_interaction_stats(self, stats: InteractionStats):
        """Store interaction statistics in database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                INSERT INTO interaction_statistics 
                (call_id, talk_time_percentage, longest_monologue, questions_asked, 
                 interruptions, sentiment_score, engagement_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (call_id) DO UPDATE SET
                    talk_time_percentage = EXCLUDED.talk_time_percentage,
                    longest_monologue = EXCLUDED.longest_monologue,
                    questions_asked = EXCLUDED.questions_asked,
                    interruptions = EXCLUDED.interruptions,
                    sentiment_score = EXCLUDED.sentiment_score,
                    engagement_score = EXCLUDED.engagement_score,
                    updated_at = CURRENT_TIMESTAMP
            """,
                stats.call_id,
                stats.talk_time_percentage,
                stats.longest_monologue,
                stats.questions_asked,
                stats.interruptions,
                stats.sentiment_score,
                stats.engagement_score
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error storing interaction stats: {str(e)}")
            raise
    
    async def _store_extensive_call_data(self, call_id: str, extensive_data: Dict[str, Any]):
        """Store extensive call data in enhanced analytics table"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Extract relevant fields from extensive data
            participants = extensive_data.get("participants", [])
            topics = extensive_data.get("topics", [])
            
            # Calculate apartment relevance and other metrics
            apartment_score = await self._calculate_apartment_relevance_from_data(extensive_data)
            deal_stage = self._extract_deal_stage(extensive_data)
            win_probability = self._calculate_win_probability(extensive_data)
            
            await conn.execute("""
                INSERT INTO enhanced_call_analytics 
                (call_id, apartment_relevance_score, deal_stage, win_probability)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (call_id) DO UPDATE SET
                    apartment_relevance_score = EXCLUDED.apartment_relevance_score,
                    deal_stage = EXCLUDED.deal_stage,
                    win_probability = EXCLUDED.win_probability,
                    updated_at = CURRENT_TIMESTAMP
            """,
                call_id,
                apartment_score,
                deal_stage,
                win_probability
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error storing extensive call data: {str(e)}")
            raise
    
    async def _analyze_transcript_relevance(self, transcript: ConversationTranscript):
        """Analyze transcript for apartment industry relevance"""
        
        try:
            # Apartment industry keywords
            apartment_keywords = [
                "apartment", "rental", "lease", "tenant", "resident", "property management",
                "multifamily", "unit", "complex", "building", "rent", "deposit", "amenities",
                "maintenance", "vacancy", "occupancy", "property manager", "leasing office",
                "application", "screening", "background check", "move-in", "move-out"
            ]
            
            # Analyze transcript segments
            total_segments = len(transcript.transcript_segments)
            keyword_matches = 0
            apartment_context_score = 0.0
            
            for segment in transcript.transcript_segments:
                text = segment.get("text", "").lower()
                
                # Count keyword matches
                for keyword in apartment_keywords:
                    if keyword in text:
                        keyword_matches += 1
                        apartment_context_score += 1.0
            
            # Calculate relevance score
            if total_segments > 0:
                relevance_score = min(apartment_context_score / total_segments, 1.0)
            else:
                relevance_score = 0.0
            
            # Update database
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                UPDATE conversation_transcripts 
                SET apartment_keywords_count = $2,
                    apartment_relevance_score = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE call_id = $1
            """,
                transcript.call_id,
                keyword_matches,
                relevance_score
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error analyzing transcript relevance: {str(e)}")
    
    async def _analyze_interaction_insights(self, stats: InteractionStats):
        """Analyze interaction statistics for apartment industry insights"""
        
        try:
            # Calculate apartment industry score based on interaction patterns
            apartment_industry_score = 0.0
            
            # High engagement typically indicates apartment industry discussions
            if stats.engagement_score > 0.7:
                apartment_industry_score += 0.3
            
            # Balanced talk time suggests consultative selling (common in apartment industry)
            if 0.3 <= stats.talk_time_percentage <= 0.7:
                apartment_industry_score += 0.2
            
            # Questions indicate discovery (important in apartment sales)
            if stats.questions_asked > 5:
                apartment_industry_score += 0.2
            
            # Positive sentiment indicates good fit
            if stats.sentiment_score > 0.5:
                apartment_industry_score += 0.3
            
            # Update database
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                UPDATE interaction_statistics 
                SET apartment_industry_score = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE call_id = $1
            """,
                stats.call_id,
                apartment_industry_score
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error analyzing interaction insights: {str(e)}")
    
    async def _calculate_apartment_relevance(self, call_id: str) -> float:
        """Calculate overall apartment relevance score for a call"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Get relevance scores from different sources
            transcript_score = await conn.fetchval("""
                SELECT apartment_relevance_score 
                FROM conversation_transcripts 
                WHERE call_id = $1
            """, call_id)
            
            interaction_score = await conn.fetchval("""
                SELECT apartment_industry_score 
                FROM interaction_statistics 
                WHERE call_id = $1
            """, call_id)
            
            analytics_score = await conn.fetchval("""
                SELECT apartment_relevance_score 
                FROM enhanced_call_analytics 
                WHERE call_id = $1
            """, call_id)
            
            await conn.close()
            
            # Calculate weighted average
            scores = []
            if transcript_score is not None:
                scores.append(transcript_score * 0.5)  # Transcript is most important
            if interaction_score is not None:
                scores.append(interaction_score * 0.3)  # Interaction patterns
            if analytics_score is not None:
                scores.append(analytics_score * 0.2)  # Analytics data
            
            if scores:
                return sum(scores) / len(scores)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating apartment relevance: {str(e)}")
            return 0.0
    
    async def _calculate_apartment_relevance_from_data(self, data: Dict[str, Any]) -> float:
        """Calculate apartment relevance from extensive call data"""
        
        # Simple relevance calculation based on topics and participants
        topics = data.get("topics", [])
        participants = data.get("participants", [])
        
        apartment_indicators = 0
        total_indicators = len(topics) + len(participants)
        
        # Check topics for apartment-related content
        for topic in topics:
            topic_text = topic.get("text", "").lower()
            if any(keyword in topic_text for keyword in ["apartment", "rental", "lease", "property"]):
                apartment_indicators += 1
        
        # Check participants for property management companies
        for participant in participants:
            company = participant.get("company", "").lower()
            if any(indicator in company for indicator in ["property", "apartment", "management", "real estate"]):
                apartment_indicators += 1
        
        if total_indicators > 0:
            return min(apartment_indicators / total_indicators, 1.0)
        else:
            return 0.0
    
    def _extract_deal_stage(self, data: Dict[str, Any]) -> str:
        """Extract deal stage from extensive call data"""
        
        # Simple deal stage extraction based on call content
        topics = data.get("topics", [])
        
        for topic in topics:
            topic_text = topic.get("text", "").lower()
            
            if any(keyword in topic_text for keyword in ["demo", "presentation", "overview"]):
                return "Discovery"
            elif any(keyword in topic_text for keyword in ["proposal", "pricing", "quote"]):
                return "Evaluation"
            elif any(keyword in topic_text for keyword in ["contract", "agreement", "terms"]):
                return "Negotiation"
            elif any(keyword in topic_text for keyword in ["signature", "close", "finalize"]):
                return "Closing"
        
        return "Discovery"  # Default stage
    
    def _calculate_win_probability(self, data: Dict[str, Any]) -> float:
        """Calculate win probability from extensive call data"""
        
        # Simple win probability calculation
        probability_factors = []
        
        # Check for positive indicators
        topics = data.get("topics", [])
        for topic in topics:
            topic_text = topic.get("text", "").lower()
            
            if any(positive in topic_text for positive in ["interested", "excited", "perfect", "exactly"]):
                probability_factors.append(0.8)
            elif any(neutral in topic_text for neutral in ["consider", "think about", "discuss"]):
                probability_factors.append(0.5)
            elif any(negative in topic_text for negative in ["expensive", "budget", "concern"]):
                probability_factors.append(0.2)
        
        if probability_factors:
            return sum(probability_factors) / len(probability_factors)
        else:
            return 0.5  # Default neutral probability

# Test the enhanced integration
async def test_enhanced_integration():
    """Test enhanced Gong integration features"""
    
    # This would normally use the OAuth manager from the main application
    # For testing, we'll create a mock implementation
    
    class MockOAuthManager:
        async def make_authenticated_request(self, endpoint, method="GET", params=None):
            # Mock successful responses for testing
            if "transcript" in endpoint:
                return {
                    "success": True,
                    "data": {
                        "entries": [
                            {"text": "We're looking for apartment management software", "speaker": "Customer"},
                            {"text": "Pay Ready can help with that", "speaker": "Sales Rep"}
                        ],
                        "speakers": [{"id": "1", "name": "Customer"}, {"id": "2", "name": "Sales Rep"}],
                        "callDuration": 1800,
                        "language": "en",
                        "confidence": 0.95
                    }
                }
            elif "media-url" in endpoint:
                return {
                    "success": True,
                    "data": {
                        "mediaUrl": "https://example.com/call-recording.mp3",
                        "mediaType": "audio",
                        "duration": 1800,
                        "fileSize": 15000000,
                        "expiresAt": (datetime.utcnow() + timedelta(hours=24)).isoformat()
                    }
                }
            elif "interaction" in endpoint:
                return {
                    "success": True,
                    "data": {
                        "talkTimePercentage": 0.45,
                        "longestMonologue": 120,
                        "questionsAsked": 8,
                        "interruptions": 2,
                        "sentimentScore": 0.75,
                        "engagementScore": 0.85
                    }
                }
            else:
                return {"success": False, "error": "Endpoint not mocked"}
    
    # Test enhanced integration
    mock_oauth = MockOAuthManager()
    enhanced_integration = EnhancedGongIntegration(mock_oauth)
    
    # Setup schema
    await enhanced_integration.setup_enhanced_schema()
    
    # Test transcript processing
    transcript = await enhanced_integration.get_conversation_transcript("test-call-123")
    print(f"Transcript processed: {transcript is not None}")
    
    # Test media processing
    media = await enhanced_integration.get_conversation_media("test-call-123")
    print(f"Media processed: {media is not None}")
    
    # Test interaction stats
    stats = await enhanced_integration.get_interaction_statistics("test-call-123")
    print(f"Stats processed: {stats is not None}")
    
    return {
        "enhanced_schema_created": True,
        "transcript_processing": transcript is not None,
        "media_processing": media is not None,
        "interaction_stats": stats is not None
    }

if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_enhanced_integration())
    print(f"Enhanced integration test results: {json.dumps(result, indent=2)}")

