"""
Sophia AI - Gong.io Integration
Sales Call Analysis and Intelligence for Pay Ready

This module provides comprehensive Gong.io integration for Sophia AI,
enabling automated call analysis, transcript processing, and sales insights.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import aiohttp
import openai
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class GongConfig:
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://api.gong.io/v2"
    rate_limit_delay: float = 0.2  # 200ms between requests
    max_retries: int = 3
    timeout: int = 60
    openai_api_key: str = ""

class GongIntegration:
    """Comprehensive Gong.io integration for call analysis and insights"""
    
    def __init__(self, config: GongConfig = None):
        self.config = config or GongConfig()
        self.session = None
        self.last_request_time = datetime.now()
        
        # Initialize OpenAI for advanced analysis
        if self.config.openai_api_key:
            openai.api_key = self.config.openai_api_key
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={
                'Authorization': f'Basic {self._get_auth_token()}',
                'Content-Type': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_auth_token(self) -> str:
        """Generate base64 encoded auth token"""
        import base64
        credentials = f"{self.config.api_key}:{self.config.api_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    async def _rate_limit_delay(self):
        """Implement rate limiting"""
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed)
        self.last_request_time = datetime.now()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Make rate-limited API request with retry logic"""
        await self._rate_limit_delay()
        
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.request(
                    method, url,
                    json=data,
                    params=params
                ) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 2))
                        await asyncio.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    logger.error(f"Gong API request failed after {self.config.max_retries} attempts: {str(e)}")
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Call Management
    async def get_calls(self, from_date: datetime = None, to_date: datetime = None, 
                       workspace_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get calls from Gong with optional filters"""
        try:
            endpoint = "/calls"
            
            # Default to last 30 days if no dates provided
            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            if not to_date:
                to_date = datetime.now()
            
            params = {
                'fromDateTime': from_date.isoformat(),
                'toDateTime': to_date.isoformat(),
                'limit': limit
            }
            
            if workspace_id:
                params['workspaceId'] = workspace_id
            
            result = await self._make_request('GET', endpoint, params=params)
            calls = result.get('calls', [])
            
            logger.info(f"Retrieved {len(calls)} calls from Gong")
            return calls
            
        except Exception as e:
            logger.error(f"Failed to get calls from Gong: {str(e)}")
            return []
    
    async def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific call"""
        try:
            endpoint = f"/calls/{call_id}"
            result = await self._make_request('GET', endpoint)
            
            logger.info(f"Retrieved details for call {call_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get call details for {call_id}: {str(e)}")
            return None
    
    async def get_call_transcript(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript for a specific call"""
        try:
            endpoint = f"/calls/{call_id}/transcript"
            result = await self._make_request('GET', endpoint)
            
            logger.info(f"Retrieved transcript for call {call_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get transcript for call {call_id}: {str(e)}")
            return None
    
    async def get_call_recording(self, call_id: str) -> Optional[str]:
        """Get recording URL for a specific call"""
        try:
            endpoint = f"/calls/{call_id}/media"
            result = await self._make_request('GET', endpoint)
            
            # Extract recording URL
            recording_url = result.get('recordingUrl')
            if recording_url:
                logger.info(f"Retrieved recording URL for call {call_id}")
                return recording_url
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get recording for call {call_id}: {str(e)}")
            return None
    
    # Call Analysis
    async def analyze_call_sentiment(self, call_id: str) -> Dict[str, Any]:
        """Analyze sentiment of a call using Gong's built-in analytics"""
        try:
            endpoint = f"/calls/{call_id}/stats"
            result = await self._make_request('GET', endpoint)
            
            # Extract sentiment and engagement metrics
            stats = result.get('stats', {})
            sentiment_analysis = {
                'call_id': call_id,
                'overall_sentiment': stats.get('sentiment', 'neutral'),
                'engagement_score': stats.get('engagementScore', 0),
                'talk_ratio': stats.get('talkRatio', 0),
                'longest_monologue': stats.get('longestMonologue', 0),
                'questions_asked': stats.get('questionsAsked', 0),
                'interactivity': stats.get('interactivity', 0),
                'energy_level': stats.get('energyLevel', 'medium')
            }
            
            logger.info(f"Analyzed sentiment for call {call_id}")
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment for call {call_id}: {str(e)}")
            return {}
    
    async def extract_call_insights(self, call_id: str) -> Dict[str, Any]:
        """Extract comprehensive insights from a call"""
        try:
            # Get call details, transcript, and sentiment
            call_details = await self.get_call_details(call_id)
            transcript_data = await self.get_call_transcript(call_id)
            sentiment_data = await self.analyze_call_sentiment(call_id)
            
            if not call_details or not transcript_data:
                return {}
            
            # Extract basic call information
            call_info = {
                'call_id': call_id,
                'title': call_details.get('title', ''),
                'duration': call_details.get('duration', 0),
                'started': call_details.get('started'),
                'participants': call_details.get('participants', []),
                'outcome': call_details.get('outcome', 'unknown')
            }
            
            # Process transcript for insights
            transcript = transcript_data.get('transcript', [])
            insights = await self._analyze_transcript_with_ai(transcript, call_info)
            
            # Combine all data
            comprehensive_insights = {
                **call_info,
                **sentiment_data,
                **insights,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Extracted comprehensive insights for call {call_id}")
            return comprehensive_insights
            
        except Exception as e:
            logger.error(f"Failed to extract insights for call {call_id}: {str(e)}")
            return {}
    
    async def _analyze_transcript_with_ai(self, transcript: List[Dict], call_info: Dict) -> Dict[str, Any]:
        """Use OpenAI to analyze transcript for business insights"""
        try:
            if not self.config.openai_api_key or not transcript:
                return {}
            
            # Prepare transcript text
            transcript_text = ""
            for entry in transcript:
                speaker = entry.get('speakerId', 'Unknown')
                text = entry.get('text', '')
                transcript_text += f"{speaker}: {text}\n"
            
            # Limit transcript length for API
            if len(transcript_text) > 8000:
                transcript_text = transcript_text[:8000] + "..."
            
            # AI analysis prompt
            prompt = f"""
            Analyze this sales call transcript and provide business insights:
            
            Call Information:
            - Title: {call_info.get('title', 'Unknown')}
            - Duration: {call_info.get('duration', 0)} minutes
            - Participants: {len(call_info.get('participants', []))}
            
            Transcript:
            {transcript_text}
            
            Please provide analysis in JSON format with these fields:
            - key_topics: List of main topics discussed
            - pain_points: Customer pain points mentioned
            - objections: Any objections raised by the prospect
            - next_steps: Agreed next steps or follow-up actions
            - deal_stage: Estimated deal stage (discovery, demo, proposal, negotiation, closed)
            - urgency_level: How urgent is this opportunity (low, medium, high)
            - decision_makers: Who are the decision makers mentioned
            - budget_indicators: Any budget or pricing discussions
            - competitor_mentions: Competitors mentioned
            - success_probability: Estimated probability of success (0-100)
            - recommended_actions: Recommended follow-up actions
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a sales intelligence analyst. Provide accurate, actionable insights from sales call transcripts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            # Parse AI response
            ai_analysis = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                insights = json.loads(ai_analysis)
            except:
                # If JSON parsing fails, create structured response
                insights = {
                    'ai_analysis': ai_analysis,
                    'analysis_method': 'text_fallback'
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to analyze transcript with AI: {str(e)}")
            return {'error': str(e)}
    
    # Deal and Opportunity Tracking
    async def get_deals_from_calls(self, from_date: datetime = None, to_date: datetime = None) -> List[Dict[str, Any]]:
        """Get deals/opportunities identified from calls"""
        try:
            endpoint = "/deals"
            
            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            if not to_date:
                to_date = datetime.now()
            
            params = {
                'fromDateTime': from_date.isoformat(),
                'toDateTime': to_date.isoformat()
            }
            
            result = await self._make_request('GET', endpoint, params=params)
            deals = result.get('deals', [])
            
            logger.info(f"Retrieved {len(deals)} deals from Gong")
            return deals
            
        except Exception as e:
            logger.error(f"Failed to get deals from Gong: {str(e)}")
            return []
    
    async def get_deal_details(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific deal"""
        try:
            endpoint = f"/deals/{deal_id}"
            result = await self._make_request('GET', endpoint)
            
            logger.info(f"Retrieved details for deal {deal_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get deal details for {deal_id}: {str(e)}")
            return None
    
    # User and Team Analytics
    async def get_user_stats(self, user_id: str, from_date: datetime = None, to_date: datetime = None) -> Dict[str, Any]:
        """Get performance statistics for a specific user"""
        try:
            endpoint = f"/users/{user_id}/stats"
            
            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            if not to_date:
                to_date = datetime.now()
            
            params = {
                'fromDateTime': from_date.isoformat(),
                'toDateTime': to_date.isoformat()
            }
            
            result = await self._make_request('GET', endpoint, params=params)
            
            logger.info(f"Retrieved stats for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {str(e)}")
            return {}
    
    async def get_team_performance(self, workspace_id: str = None, from_date: datetime = None, to_date: datetime = None) -> Dict[str, Any]:
        """Get team performance analytics"""
        try:
            # Get all users in workspace
            users_endpoint = "/users"
            users_result = await self._make_request('GET', users_endpoint)
            users = users_result.get('users', [])
            
            # Get performance data for each user
            team_performance = {
                'workspace_id': workspace_id,
                'analysis_period': {
                    'from': from_date.isoformat() if from_date else None,
                    'to': to_date.isoformat() if to_date else None
                },
                'users': [],
                'team_totals': {
                    'total_calls': 0,
                    'total_duration': 0,
                    'average_sentiment': 0,
                    'total_deals': 0
                }
            }
            
            for user in users:
                user_id = user.get('id')
                if user_id:
                    user_stats = await self.get_user_stats(user_id, from_date, to_date)
                    team_performance['users'].append({
                        'user_id': user_id,
                        'name': user.get('firstName', '') + ' ' + user.get('lastName', ''),
                        'email': user.get('emailAddress', ''),
                        'stats': user_stats
                    })
            
            logger.info(f"Retrieved team performance for {len(users)} users")
            return team_performance
            
        except Exception as e:
            logger.error(f"Failed to get team performance: {str(e)}")
            return {}
    
    # Advanced Analytics
    async def get_call_trends(self, from_date: datetime = None, to_date: datetime = None) -> Dict[str, Any]:
        """Analyze call trends and patterns"""
        try:
            calls = await self.get_calls(from_date, to_date, limit=500)
            
            if not calls:
                return {}
            
            # Analyze trends
            trends = {
                'total_calls': len(calls),
                'date_range': {
                    'from': from_date.isoformat() if from_date else None,
                    'to': to_date.isoformat() if to_date else None
                },
                'average_duration': sum(call.get('duration', 0) for call in calls) / len(calls),
                'calls_by_outcome': {},
                'calls_by_day': {},
                'top_participants': {},
                'duration_distribution': {
                    'short': 0,  # < 15 min
                    'medium': 0,  # 15-45 min
                    'long': 0    # > 45 min
                }
            }
            
            # Process each call for trends
            for call in calls:
                # Outcome distribution
                outcome = call.get('outcome', 'unknown')
                trends['calls_by_outcome'][outcome] = trends['calls_by_outcome'].get(outcome, 0) + 1
                
                # Daily distribution
                call_date = call.get('started', '')[:10]  # Extract date part
                trends['calls_by_day'][call_date] = trends['calls_by_day'].get(call_date, 0) + 1
                
                # Duration distribution
                duration = call.get('duration', 0)
                if duration < 15:
                    trends['duration_distribution']['short'] += 1
                elif duration < 45:
                    trends['duration_distribution']['medium'] += 1
                else:
                    trends['duration_distribution']['long'] += 1
                
                # Participant frequency
                for participant in call.get('participants', []):
                    email = participant.get('emailAddress', 'unknown')
                    trends['top_participants'][email] = trends['top_participants'].get(email, 0) + 1
            
            logger.info(f"Analyzed trends for {len(calls)} calls")
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze call trends: {str(e)}")
            return {}
    
    async def identify_coaching_opportunities(self, user_id: str = None, from_date: datetime = None, to_date: datetime = None) -> List[Dict[str, Any]]:
        """Identify coaching opportunities based on call analysis"""
        try:
            # Get calls for analysis
            calls = await self.get_calls(from_date, to_date, limit=100)
            
            coaching_opportunities = []
            
            for call in calls:
                call_id = call.get('id')
                if not call_id:
                    continue
                
                # Filter by user if specified
                if user_id:
                    participants = call.get('participants', [])
                    if not any(p.get('userId') == user_id for p in participants):
                        continue
                
                # Analyze call for coaching opportunities
                sentiment_data = await self.analyze_call_sentiment(call_id)
                
                opportunities = []
                
                # Check for low engagement
                if sentiment_data.get('engagement_score', 0) < 0.5:
                    opportunities.append({
                        'type': 'low_engagement',
                        'description': 'Low customer engagement detected',
                        'recommendation': 'Focus on asking more engaging questions and active listening'
                    })
                
                # Check for poor talk ratio
                talk_ratio = sentiment_data.get('talk_ratio', 0.5)
                if talk_ratio > 0.7:
                    opportunities.append({
                        'type': 'excessive_talking',
                        'description': 'Rep talking too much (>70% of call)',
                        'recommendation': 'Practice discovery questions and let prospect talk more'
                    })
                
                # Check for few questions
                if sentiment_data.get('questions_asked', 0) < 3:
                    opportunities.append({
                        'type': 'insufficient_discovery',
                        'description': 'Few discovery questions asked',
                        'recommendation': 'Prepare more discovery questions to understand prospect needs'
                    })
                
                if opportunities:
                    coaching_opportunities.append({
                        'call_id': call_id,
                        'call_title': call.get('title', ''),
                        'call_date': call.get('started', ''),
                        'opportunities': opportunities,
                        'priority': 'high' if len(opportunities) > 2 else 'medium'
                    })
            
            logger.info(f"Identified {len(coaching_opportunities)} coaching opportunities")
            return coaching_opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify coaching opportunities: {str(e)}")
            return []
    
    # Webhook and Real-time Processing
    async def process_call_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming call webhook from Gong"""
        try:
            event_type = webhook_data.get('eventType')
            call_data = webhook_data.get('call', {})
            call_id = call_data.get('id')
            
            if not call_id:
                return {'error': 'No call ID in webhook data'}
            
            # Process based on event type
            if event_type == 'call.recorded':
                # New call recorded - extract insights
                insights = await self.extract_call_insights(call_id)
                return {
                    'event_type': event_type,
                    'call_id': call_id,
                    'insights': insights,
                    'processed_at': datetime.now().isoformat()
                }
            
            elif event_type == 'call.transcribed':
                # Call transcribed - analyze transcript
                transcript_data = await self.get_call_transcript(call_id)
                return {
                    'event_type': event_type,
                    'call_id': call_id,
                    'transcript_available': bool(transcript_data),
                    'processed_at': datetime.now().isoformat()
                }
            
            return {
                'event_type': event_type,
                'call_id': call_id,
                'status': 'processed',
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process call webhook: {str(e)}")
            return {'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    async def main():
        config = GongConfig(
            api_key=os.getenv('GONG_API_KEY', ''),
            api_secret=os.getenv('GONG_API_SECRET', ''),
            openai_api_key=os.getenv('OPENAI_API_KEY', '')
        )
        
        async with GongIntegration(config) as gong:
            # Test getting recent calls
            calls = await gong.get_calls(limit=5)
            print(f"Retrieved {len(calls)} calls")
            
            # Test call analysis if calls exist
            if calls:
                call_id = calls[0].get('id')
                if call_id:
                    insights = await gong.extract_call_insights(call_id)
                    print(f"Call insights: {json.dumps(insights, indent=2)}")
    
    asyncio.run(main())

