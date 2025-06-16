"""
Sophia AI - Gong.io Integration
Sales call recording analysis and insights extraction

This module provides integration with Gong.io for analyzing sales calls,
extracting insights, and syncing with the AI orchestrator.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
from aiohttp import ClientTimeout
import backoff
from pydantic import BaseModel, Field
import os

logger = logging.getLogger(__name__)

class GongConfig(BaseModel):
    """Gong.io API configuration"""
    api_key: str = Field(default_factory=lambda: os.getenv('GONG_API_KEY', ''))
    api_secret: str = Field(default_factory=lambda: os.getenv('GONG_API_SECRET', ''))
    base_url: str = "https://api.gong.io/v2"
    rate_limit_delay: float = 0.1  # 100ms between requests
    max_retries: int = 3
    timeout: int = 30
    max_concurrent_requests: int = 5

class CallTranscript(BaseModel):
    """Call transcript segment"""
    speaker_id: str
    speaker_name: str
    start_time: float
    end_time: float
    text: str
    sentiment: Optional[str] = None

class CallInsights(BaseModel):
    """Structured call insights"""
    call_id: str
    date: datetime
    duration: int
    participants: List[Dict[str, Any]]
    key_topics: List[str]
    pain_points: List[str]
    next_steps: List[str]
    objections: List[str]
    competitor_mentions: List[str]
    success_probability: Optional[int] = None
    sentiment_score: Optional[float] = None
    talk_ratio: Optional[Dict[str, float]] = None

class GongIntegration:
    """Comprehensive Gong.io integration for call analysis"""
    
    def __init__(self, config: GongConfig = None):
        self.config = config or GongConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = datetime.now()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Gong API"""
        import base64
        auth_string = f"{self.config.api_key}:{self.config.api_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        return {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        }
    
    async def _rate_limit_delay(self):
        """Implement rate limiting"""
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed)
        self.last_request_time = datetime.now()
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=60
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None, 
        params: Dict = None
    ) -> Dict[str, Any]:
        """Make rate-limited API request with retry logic"""
        async with self._semaphore:
            await self._rate_limit_delay()
            
            url = f"{self.config.base_url}{endpoint}"
            headers = self._get_auth_headers()
            
            try:
                async with self.session.request(
                    method, url,
                    json=data,
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 1))
                        logger.warning(f"Rate limited by Gong API, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        raise aiohttp.ClientError("Rate limited")
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                logger.error(f"Gong API request failed: {str(e)}")
                raise
    
    # Call Management
    async def get_calls(
        self, 
        from_date: datetime, 
        to_date: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get calls within date range"""
        try:
            params = {
                'fromDateTime': from_date.isoformat(),
                'toDateTime': to_date.isoformat(),
                'limit': min(limit, 100)  # Gong max is 100
            }
            
            response = await self._make_request('GET', '/calls', params=params)
            calls = response.get('calls', [])
            
            logger.info(f"Retrieved {len(calls)} calls from Gong")
            return calls
            
        except Exception as e:
            logger.error(f"Failed to get calls from Gong: {str(e)}")
            return []
    
    async def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed call information"""
        try:
            endpoint = f"/calls/{call_id}"
            response = await self._make_request('GET', endpoint)
            
            return response.get('call')
            
        except Exception as e:
            logger.error(f"Failed to get call details for {call_id}: {str(e)}")
            return None
    
    async def get_call_transcript(self, call_id: str) -> List[CallTranscript]:
        """Get call transcript with speaker information"""
        try:
            endpoint = f"/calls/{call_id}/transcript"
            response = await self._make_request('GET', endpoint)
            
            transcripts = []
            for segment in response.get('transcript', []):
                transcript = CallTranscript(
                    speaker_id=segment.get('speakerId', ''),
                    speaker_name=segment.get('speakerName', 'Unknown'),
                    start_time=segment.get('start', 0),
                    end_time=segment.get('end', 0),
                    text=segment.get('text', ''),
                    sentiment=segment.get('sentiment')
                )
                transcripts.append(transcript)
            
            return transcripts
            
        except Exception as e:
            logger.error(f"Failed to get transcript for call {call_id}: {str(e)}")
            return []
    
    # Analytics and Insights
    async def extract_call_insights(self, call_id: str) -> Optional[CallInsights]:
        """Extract comprehensive insights from a call"""
        try:
            # Get call details
            call_details = await self.get_call_details(call_id)
            if not call_details:
                return None
            
            # Get transcript
            transcript = await self.get_call_transcript(call_id)
            
            # Get call stats
            stats = await self.get_call_stats(call_id)
            
            # Extract insights
            insights = await self._analyze_call_content(call_details, transcript, stats)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to extract insights for call {call_id}: {str(e)}")
            return None
    
    async def get_call_stats(self, call_id: str) -> Dict[str, Any]:
        """Get call statistics (talk time, sentiment, etc.)"""
        try:
            endpoint = f"/calls/{call_id}/stats"
            response = await self._make_request('GET', endpoint)
            
            return response.get('stats', {})
            
        except Exception as e:
            logger.error(f"Failed to get call stats for {call_id}: {str(e)}")
            return {}
    
    async def analyze_call_sentiment(self, call_id: str) -> Dict[str, Any]:
        """Analyze sentiment throughout the call"""
        try:
            transcript = await self.get_call_transcript(call_id)
            
            # Calculate sentiment scores
            sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
            for segment in transcript:
                if segment.sentiment:
                    sentiments[segment.sentiment.lower()] += 1
            
            total_segments = sum(sentiments.values())
            if total_segments > 0:
                sentiment_distribution = {
                    k: v / total_segments for k, v in sentiments.items()
                }
            else:
                sentiment_distribution = sentiments
            
            # Calculate overall sentiment score (-1 to 1)
            sentiment_score = (
                sentiments['positive'] - sentiments['negative']
            ) / max(total_segments, 1)
            
            return {
                'overall_score': sentiment_score,
                'distribution': sentiment_distribution,
                'total_segments': total_segments
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment for call {call_id}: {str(e)}")
            return {}
    
    async def _analyze_call_content(
        self,
        call_details: Dict[str, Any],
        transcript: List[CallTranscript],
        stats: Dict[str, Any]
    ) -> CallInsights:
        """Analyze call content to extract insights"""
        # Extract key information
        call_id = call_details.get('id', '')
        call_date = datetime.fromisoformat(
            call_details.get('startTime', datetime.now().isoformat())
        )
        duration = call_details.get('duration', 0)
        
        # Extract participants
        participants = []
        for participant in call_details.get('participants', []):
            participants.append({
                'name': participant.get('name', 'Unknown'),
                'email': participant.get('email', ''),
                'type': participant.get('type', 'Unknown')
            })
        
        # Analyze transcript for insights
        full_text = ' '.join([seg.text for seg in transcript])
        
        # Extract key topics (simplified - in production use NLP)
        key_topics = await self._extract_key_topics(full_text)
        
        # Extract pain points
        pain_points = await self._extract_pain_points(full_text)
        
        # Extract next steps
        next_steps = await self._extract_next_steps(full_text)
        
        # Extract objections
        objections = await self._extract_objections(full_text)
        
        # Extract competitor mentions
        competitor_mentions = await self._extract_competitors(full_text)
        
        # Calculate success probability (simplified heuristic)
        success_probability = await self._calculate_success_probability(
            pain_points, next_steps, objections
        )
        
        # Get sentiment score
        sentiment_analysis = await self.analyze_call_sentiment(call_id)
        sentiment_score = sentiment_analysis.get('overall_score', 0.0)
        
        # Extract talk ratio from stats
        talk_ratio = stats.get('talkRatio', {})
        
        return CallInsights(
            call_id=call_id,
            date=call_date,
            duration=duration,
            participants=participants,
            key_topics=key_topics,
            pain_points=pain_points,
            next_steps=next_steps,
            objections=objections,
            competitor_mentions=competitor_mentions,
            success_probability=success_probability,
            sentiment_score=sentiment_score,
            talk_ratio=talk_ratio
        )
    
    async def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from call text"""
        # Simplified keyword extraction
        # In production, use NLP models for better extraction
        keywords = [
            'pricing', 'implementation', 'integration', 'support',
            'features', 'security', 'compliance', 'timeline',
            'budget', 'decision', 'contract', 'pilot'
        ]
        
        topics = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                topics.append(keyword)
        
        return topics[:5]  # Top 5 topics
    
    async def _extract_pain_points(self, text: str) -> List[str]:
        """Extract pain points mentioned in the call"""
        pain_indicators = [
            'challenge', 'problem', 'issue', 'struggle',
            'difficult', 'pain', 'frustrat', 'concern'
        ]
        
        pain_points = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for indicator in pain_indicators:
                if indicator in sentence_lower:
                    pain_points.append(sentence.strip())
                    break
        
        return pain_points[:5]  # Top 5 pain points
    
    async def _extract_next_steps(self, text: str) -> List[str]:
        """Extract agreed next steps"""
        next_step_indicators = [
            'next step', 'follow up', 'will send', 'will schedule',
            'let\'s meet', 'we\'ll discuss', 'action item'
        ]
        
        next_steps = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for indicator in next_step_indicators:
                if indicator in sentence_lower:
                    next_steps.append(sentence.strip())
                    break
        
        return next_steps[:5]
    
    async def _extract_objections(self, text: str) -> List[str]:
        """Extract objections raised during the call"""
        objection_indicators = [
            'concern', 'worried', 'not sure', 'expensive',
            'complex', 'difficult', 'competitor', 'alternative'
        ]
        
        objections = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for indicator in objection_indicators:
                if indicator in sentence_lower and '?' in sentence:
                    objections.append(sentence.strip())
                    break
        
        return objections[:5]
    
    async def _extract_competitors(self, text: str) -> List[str]:
        """Extract competitor mentions"""
        # Add your competitors here
        competitors = [
            'salesforce', 'hubspot', 'pipedrive', 'zoho',
            'microsoft', 'oracle', 'sap'
        ]
        
        mentioned = []
        text_lower = text.lower()
        
        for competitor in competitors:
            if competitor in text_lower:
                mentioned.append(competitor)
        
        return mentioned
    
    async def _calculate_success_probability(
        self,
        pain_points: List[str],
        next_steps: List[str],
        objections: List[str]
    ) -> int:
        """Calculate probability of deal success"""
        score = 50  # Base score
        
        # Positive indicators
        score += len(pain_points) * 5  # Pain points we can solve
        score += len(next_steps) * 10  # Clear next steps
        
        # Negative indicators
        score -= len(objections) * 7  # Unresolved objections
        
        # Normalize to 0-100
        return max(0, min(100, score))
    
    # Coaching and Analytics
    async def get_rep_performance(
        self,
        rep_email: str,
        from_date: datetime,
        to_date: datetime
    ) -> Dict[str, Any]:
        """Get performance metrics for a sales rep"""
        try:
            # Get rep's calls
            params = {
                'fromDateTime': from_date.isoformat(),
                'toDateTime': to_date.isoformat(),
                'userEmail': rep_email,
                'limit': 100
            }
            
            response = await self._make_request('GET', '/calls', params=params)
            calls = response.get('calls', [])
            
            # Calculate metrics
            total_calls = len(calls)
            total_duration = sum(call.get('duration', 0) for call in calls)
            
            # Get detailed metrics for recent calls
            recent_metrics = []
            for call in calls[:10]:  # Analyze last 10 calls
                call_id = call.get('id')
                if call_id:
                    insights = await self.extract_call_insights(call_id)
                    if insights:
                        recent_metrics.append({
                            'call_id': call_id,
                            'success_probability': insights.success_probability,
                            'sentiment_score': insights.sentiment_score
                        })
            
            # Calculate averages
            avg_success_prob = sum(
                m['success_probability'] for m in recent_metrics
            ) / len(recent_metrics) if recent_metrics else 0
            
            avg_sentiment = sum(
                m['sentiment_score'] for m in recent_metrics
            ) / len(recent_metrics) if recent_metrics else 0
            
            return {
                'rep_email': rep_email,
                'period': {
                    'from': from_date.isoformat(),
                    'to': to_date.isoformat()
                },
                'total_calls': total_calls,
                'total_duration_minutes': total_duration // 60,
                'average_call_duration': total_duration // total_calls if total_calls else 0,
                'recent_performance': {
                    'average_success_probability': avg_success_prob,
                    'average_sentiment_score': avg_sentiment,
                    'calls_analyzed': len(recent_metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get rep performance for {rep_email}: {str(e)}")
            return {}
    
    # Webhook Support
    async def validate_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Validate Gong webhook signature"""
        # Implement webhook validation based on Gong's documentation
        # This is a placeholder implementation
        return True
    
    async def process_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook event from Gong"""
        try:
            event_type = event.get('eventType')
            call_id = event.get('callId')
            
            if event_type == 'CALL_COMPLETED':
                # Automatically analyze completed calls
                insights = await self.extract_call_insights(call_id)
                return {
                    'processed': True,
                    'event_type': event_type,
                    'call_id': call_id,
                    'insights': insights.dict() if insights else None
                }
            
            return {
                'processed': True,
                'event_type': event_type,
                'message': 'Event processed'
            }
            
        except Exception as e:
            logger.error(f"Failed to process webhook event: {str(e)}")
            return {
                'processed': False,
                'error': str(e)
            }

# Example usage and testing
if __name__ == "__main__":
    async def main():
        config = GongConfig()
        
        async with GongIntegration(config) as gong:
            # Test getting recent calls
            from_date = datetime.now() - timedelta(days=7)
            to_date = datetime.now()
            
            calls = await gong.get_calls(from_date, to_date, limit=10)
            print(f"Found {len(calls)} calls")
            
            # Test analyzing a call
            if calls:
                call_id = calls[0]['id']
                insights = await gong.extract_call_insights(call_id)
                if insights:
                    print(f"Call insights: {insights.dict()}")
    
    asyncio.run(main())

