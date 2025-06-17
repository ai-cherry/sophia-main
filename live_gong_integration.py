#!/usr/bin/env python3
"""
Live Gong API Integration - Production Implementation
Connects to real Gong workspace and populates database with actual conversation data
"""

import asyncio
import asyncpg
import aiohttp
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gong API Configuration
GONG_ACCESS_KEY = "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"
GONG_SECRET = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tZXkiOiJUVjMzQlBaNVVONDRRS1pDWjJVQ0FLUlhIUTZRM0w1TiJ9.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU"
GONG_BASE_URL = "https://api.gong.io/v2"

# Database Configuration
DATABASE_URL = "postgresql://postgres:password@localhost:5432/sophia_enhanced"

class LiveGongIntegration:
    """Live Gong API integration with real data extraction"""
    
    def __init__(self):
        self.session = None
        self.db_connection = None
        self.auth_header = self._create_auth_header()
        self.apartment_keywords = [
            'apartment', 'apartments', 'rental', 'lease', 'tenant', 'resident',
            'property', 'unit', 'complex', 'community', 'multifamily', 'housing',
            'rent', 'renter', 'landlord', 'property management', 'leasing',
            'maintenance', 'amenities', 'vacancy', 'occupancy', 'studio',
            'bedroom', 'bathroom', 'square feet', 'deposit', 'utilities'
        ]
    
    def _create_auth_header(self) -> str:
        """Create Basic Auth header for Gong API"""
        credentials = f"{GONG_ACCESS_KEY}:{GONG_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def initialize(self):
        """Initialize HTTP session and database connection"""
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Connect to database
        self.db_connection = await asyncpg.connect(DATABASE_URL)
        logger.info("Initialized Gong API session and database connection")
    
    async def close(self):
        """Close connections"""
        if self.session:
            await self.session.close()
        if self.db_connection:
            await self.db_connection.close()
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test Gong API connectivity and get workspace info"""
        try:
            url = f"{GONG_BASE_URL}/settings/workspaces"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"API connection successful. Workspaces: {len(data.get('workspaces', []))}")
                    return {"success": True, "data": data}
                else:
                    error_text = await response.text()
                    logger.error(f"API connection failed: {response.status} - {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"API connection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users from Gong workspace"""
        try:
            url = f"{GONG_BASE_URL}/users"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    users = data.get('users', [])
                    logger.info(f"Retrieved {len(users)} users")
                    return users
                else:
                    logger.error(f"Failed to get users: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def get_calls(self, from_date: datetime, to_date: datetime, cursor: str = None) -> Dict[str, Any]:
        """Get calls from Gong API with pagination"""
        try:
            url = f"{GONG_BASE_URL}/calls"
            params = {
                "fromDateTime": from_date.isoformat(),
                "toDateTime": to_date.isoformat()
            }
            
            if cursor:
                params["cursor"] = cursor
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    calls = data.get('calls', [])
                    logger.info(f"Retrieved {len(calls)} calls")
                    return {
                        "calls": calls,
                        "cursor": data.get('records', {}).get('cursor'),
                        "total_records": data.get('records', {}).get('totalRecords', 0)
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get calls: {response.status} - {error_text}")
                    return {"calls": [], "cursor": None, "total_records": 0}
        except Exception as e:
            logger.error(f"Error getting calls: {e}")
            return {"calls": [], "cursor": None, "total_records": 0}
    
    async def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """Get detailed call information"""
        try:
            url = f"{GONG_BASE_URL}/calls/{call_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Failed to get call details for {call_id}: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting call details for {call_id}: {e}")
            return {}
    
    def calculate_apartment_relevance(self, text: str) -> float:
        """Calculate apartment industry relevance score"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in self.apartment_keywords if keyword in text_lower)
        
        # Calculate relevance score based on keyword density
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        keyword_density = keyword_matches / word_count
        relevance_score = min(keyword_density * 10, 1.0)  # Cap at 1.0
        
        # Boost score for specific apartment industry phrases
        apartment_phrases = [
            'property management', 'apartment complex', 'rental property',
            'lease agreement', 'tenant screening', 'rent collection',
            'maintenance request', 'vacancy rate', 'occupancy rate'
        ]
        
        phrase_matches = sum(1 for phrase in apartment_phrases if phrase in text_lower)
        if phrase_matches > 0:
            relevance_score = min(relevance_score + (phrase_matches * 0.2), 1.0)
        
        return round(relevance_score, 3)
    
    def analyze_conversation_intelligence(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation for business intelligence"""
        title = call_data.get('title', '')
        
        # Generate AI summary (simplified for demo)
        summary = f"Conversation with {len(call_data.get('parties', []))} participants"
        if 'apartment' in title.lower() or 'property' in title.lower():
            summary += " discussing apartment industry solutions and payment processing opportunities."
        else:
            summary += " covering business development and partnership opportunities."
        
        # Calculate deal health score
        positive_indicators = ['interested', 'excited', 'budget', 'timeline', 'next steps']
        negative_indicators = ['concerned', 'expensive', 'competitor', 'delay', 'budget constraints']
        
        title_lower = title.lower()
        positive_count = sum(1 for indicator in positive_indicators if indicator in title_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in title_lower)
        
        deal_health = max(0.1, min(0.9, 0.5 + (positive_count * 0.1) - (negative_count * 0.1)))
        
        return {
            'ai_summary': summary,
            'confidence_level': 0.85,
            'key_insights': {
                'apartment_focus': 'apartment' in title_lower,
                'payment_discussion': 'payment' in title_lower or 'pay' in title_lower,
                'partnership_opportunity': 'partner' in title_lower
            },
            'recommended_actions': [
                'Follow up within 24 hours',
                'Send apartment industry case studies',
                'Schedule technical demo'
            ],
            'deal_health_score': deal_health
        }
    
    def analyze_apartment_context(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze apartment industry specific context"""
        title = call_data.get('title', '').lower()
        
        # Determine market segment
        market_segment = 'general'
        if 'luxury' in title or 'premium' in title:
            market_segment = 'luxury'
        elif 'affordable' in title or 'budget' in title:
            market_segment = 'affordable'
        elif 'student' in title or 'university' in title:
            market_segment = 'student'
        elif 'senior' in title or 'retirement' in title:
            market_segment = 'senior'
        
        # Count apartment terminology
        terminology_count = sum(1 for keyword in self.apartment_keywords if keyword in title)
        
        return {
            'market_segment': market_segment,
            'apartment_terminology_count': terminology_count,
            'industry_relevance_factors': {
                'property_management_focus': 'management' in title,
                'payment_processing_need': 'payment' in title or 'pay' in title,
                'technology_discussion': 'tech' in title or 'software' in title
            }
        }
    
    def analyze_deal_signals(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze deal progression signals"""
        title = call_data.get('title', '').lower()
        
        # Positive signals
        positive_signals = []
        if 'demo' in title:
            positive_signals.append('Product demo scheduled')
        if 'proposal' in title:
            positive_signals.append('Proposal discussion')
        if 'contract' in title:
            positive_signals.append('Contract negotiation')
        if 'budget' in title:
            positive_signals.append('Budget discussion')
        
        # Negative signals
        negative_signals = []
        if 'concern' in title:
            negative_signals.append('Customer concerns raised')
        if 'competitor' in title:
            negative_signals.append('Competitive pressure')
        if 'delay' in title:
            negative_signals.append('Timeline delays')
        
        # Determine deal stage
        deal_stage = 'discovery'
        if 'demo' in title or 'presentation' in title:
            deal_stage = 'evaluation'
        elif 'proposal' in title or 'quote' in title:
            deal_stage = 'negotiation'
        elif 'contract' in title or 'close' in title:
            deal_stage = 'closing'
        
        # Calculate win probability
        win_probability = 0.5
        win_probability += len(positive_signals) * 0.1
        win_probability -= len(negative_signals) * 0.1
        win_probability = max(0.1, min(0.9, win_probability))
        
        return {
            'positive_signals': positive_signals,
            'negative_signals': negative_signals,
            'deal_progression_stage': deal_stage,
            'win_probability': win_probability
        }
    
    def analyze_competitive_intelligence(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive mentions and threats"""
        title = call_data.get('title', '').lower()
        
        # Common apartment industry competitors
        competitors = ['yardi', 'realpage', 'appfolio', 'buildium', 'rent manager', 'entrata']
        competitors_mentioned = [comp for comp in competitors if comp in title]
        
        # Determine threat level
        threat_level = 'none'
        if competitors_mentioned:
            if len(competitors_mentioned) > 1:
                threat_level = 'high'
            else:
                threat_level = 'medium'
        
        # Calculate win probability impact
        win_probability_impact = 0.0
        if threat_level == 'high':
            win_probability_impact = -0.3
        elif threat_level == 'medium':
            win_probability_impact = -0.1
        
        return {
            'competitors_mentioned': competitors_mentioned,
            'competitive_threat_level': threat_level,
            'win_probability_impact': win_probability_impact
        }
    
    async def store_call_data(self, call_data: Dict[str, Any]) -> bool:
        """Store call data in database with intelligence analysis"""
        try:
            call_id = call_data.get('id')
            if not call_id:
                return False
            
            # Calculate apartment relevance
            title = call_data.get('title', '')
            apartment_relevance = self.calculate_apartment_relevance(title)
            
            # Business impact score (simplified calculation)
            business_impact = min(apartment_relevance + 0.2, 1.0)
            
            # Store main call record
            await self.db_connection.execute("""
                INSERT INTO gong_calls (
                    call_id, title, url, started, duration_seconds, direction, system,
                    apartment_relevance_score, business_impact_score, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (call_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    apartment_relevance_score = EXCLUDED.apartment_relevance_score,
                    business_impact_score = EXCLUDED.business_impact_score,
                    updated_at = EXCLUDED.updated_at
            """, 
                call_id,
                title,
                call_data.get('url', ''),
                datetime.fromisoformat(call_data.get('started', '').replace('Z', '+00:00')) if call_data.get('started') else None,
                call_data.get('duration'),
                call_data.get('direction', 'unknown'),
                call_data.get('system', 'gong'),
                apartment_relevance,
                business_impact,
                datetime.utcnow(),
                datetime.utcnow()
            )
            
            # Store participants
            for party in call_data.get('parties', []):
                await self.db_connection.execute("""
                    INSERT INTO gong_participants (
                        call_id, participant_id, email_address, name, title, company_name,
                        participation_type, talk_time_percentage, is_customer, is_internal,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (call_id, participant_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        title = EXCLUDED.title,
                        company_name = EXCLUDED.company_name,
                        updated_at = EXCLUDED.updated_at
                """,
                    call_id,
                    party.get('id', ''),
                    party.get('emailAddress', ''),
                    party.get('name', ''),
                    party.get('title', ''),
                    party.get('companyName', ''),
                    'participant',
                    0.0,  # Will be updated with actual talk time if available
                    not party.get('emailAddress', '').endswith('@payready.com'),
                    party.get('emailAddress', '').endswith('@payready.com'),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            
            # Store conversation intelligence
            intelligence = self.analyze_conversation_intelligence(call_data)
            await self.db_connection.execute("""
                INSERT INTO sophia_conversation_intelligence (
                    call_id, ai_summary, confidence_level, key_insights, recommended_actions,
                    deal_health_score, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (call_id) DO UPDATE SET
                    ai_summary = EXCLUDED.ai_summary,
                    confidence_level = EXCLUDED.confidence_level,
                    key_insights = EXCLUDED.key_insights,
                    recommended_actions = EXCLUDED.recommended_actions,
                    deal_health_score = EXCLUDED.deal_health_score,
                    updated_at = EXCLUDED.updated_at
            """,
                call_id,
                intelligence['ai_summary'],
                intelligence['confidence_level'],
                json.dumps(intelligence['key_insights']),
                json.dumps(intelligence['recommended_actions']),
                intelligence['deal_health_score'],
                datetime.utcnow(),
                datetime.utcnow()
            )
            
            # Store apartment analysis
            apartment_analysis = self.analyze_apartment_context(call_data)
            await self.db_connection.execute("""
                INSERT INTO sophia_apartment_analysis (
                    call_id, market_segment, apartment_terminology_count, industry_relevance_factors,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (call_id) DO UPDATE SET
                    market_segment = EXCLUDED.market_segment,
                    apartment_terminology_count = EXCLUDED.apartment_terminology_count,
                    industry_relevance_factors = EXCLUDED.industry_relevance_factors,
                    updated_at = EXCLUDED.updated_at
            """,
                call_id,
                apartment_analysis['market_segment'],
                apartment_analysis['apartment_terminology_count'],
                json.dumps(apartment_analysis['industry_relevance_factors']),
                datetime.utcnow(),
                datetime.utcnow()
            )
            
            # Store deal signals
            deal_signals = self.analyze_deal_signals(call_data)
            await self.db_connection.execute("""
                INSERT INTO sophia_deal_signals (
                    call_id, positive_signals, negative_signals, deal_progression_stage,
                    win_probability, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (call_id) DO UPDATE SET
                    positive_signals = EXCLUDED.positive_signals,
                    negative_signals = EXCLUDED.negative_signals,
                    deal_progression_stage = EXCLUDED.deal_progression_stage,
                    win_probability = EXCLUDED.win_probability,
                    updated_at = EXCLUDED.updated_at
            """,
                call_id,
                json.dumps(deal_signals['positive_signals']),
                json.dumps(deal_signals['negative_signals']),
                deal_signals['deal_progression_stage'],
                deal_signals['win_probability'],
                datetime.utcnow(),
                datetime.utcnow()
            )
            
            # Store competitive intelligence
            competitive = self.analyze_competitive_intelligence(call_data)
            await self.db_connection.execute("""
                INSERT INTO sophia_competitive_intelligence (
                    call_id, competitors_mentioned, competitive_threat_level, win_probability_impact,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (call_id) DO UPDATE SET
                    competitors_mentioned = EXCLUDED.competitors_mentioned,
                    competitive_threat_level = EXCLUDED.competitive_threat_level,
                    win_probability_impact = EXCLUDED.win_probability_impact,
                    updated_at = EXCLUDED.updated_at
            """,
                call_id,
                competitive['competitors_mentioned'],
                competitive['competitive_threat_level'],
                competitive['win_probability_impact'],
                datetime.utcnow(),
                datetime.utcnow()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing call data for {call_data.get('id')}: {e}")
            return False
    
    async def store_users(self, users: List[Dict[str, Any]]) -> int:
        """Store users in database"""
        stored_count = 0
        for user in users:
            try:
                await self.db_connection.execute("""
                    INSERT INTO gong_users (
                        user_id, email_address, first_name, last_name, active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_address = EXCLUDED.email_address,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        active = EXCLUDED.active,
                        updated_at = EXCLUDED.updated_at
                """,
                    user.get('id', ''),
                    user.get('emailAddress', ''),
                    user.get('firstName', ''),
                    user.get('lastName', ''),
                    user.get('active', True),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                stored_count += 1
            except Exception as e:
                logger.error(f"Error storing user {user.get('id')}: {e}")
        
        return stored_count
    
    async def run_full_sync(self, days_back: int = 30) -> Dict[str, Any]:
        """Run full synchronization of Gong data"""
        start_time = time.time()
        results = {
            'api_test': None,
            'users_synced': 0,
            'calls_synced': 0,
            'total_calls_available': 0,
            'errors': [],
            'execution_time': 0
        }
        
        try:
            # Test API connection
            logger.info("Testing API connection...")
            api_test = await self.test_api_connection()
            results['api_test'] = api_test
            
            if not api_test['success']:
                results['errors'].append(f"API connection failed: {api_test['error']}")
                return results
            
            # Sync users
            logger.info("Syncing users...")
            users = await self.get_users()
            results['users_synced'] = await self.store_users(users)
            
            # Sync calls
            logger.info("Syncing calls...")
            from_date = datetime.utcnow() - timedelta(days=days_back)
            to_date = datetime.utcnow()
            
            cursor = None
            total_calls_processed = 0
            
            while True:
                call_data = await self.get_calls(from_date, to_date, cursor)
                calls = call_data['calls']
                
                if not calls:
                    break
                
                results['total_calls_available'] = call_data['total_records']
                
                # Process calls in batches
                for call in calls:
                    success = await self.store_call_data(call)
                    if success:
                        total_calls_processed += 1
                    else:
                        results['errors'].append(f"Failed to store call {call.get('id')}")
                    
                    # Rate limiting - respect Gong's 3 calls per second limit
                    await asyncio.sleep(0.34)  # Slightly more than 1/3 second
                
                cursor = call_data['cursor']
                if not cursor:
                    break
                
                logger.info(f"Processed {total_calls_processed} calls so far...")
            
            results['calls_synced'] = total_calls_processed
            
        except Exception as e:
            logger.error(f"Error in full sync: {e}")
            results['errors'].append(f"Full sync error: {str(e)}")
        
        results['execution_time'] = time.time() - start_time
        return results

async def main():
    """Main execution function"""
    integration = LiveGongIntegration()
    
    try:
        await integration.initialize()
        logger.info("Starting live Gong API integration...")
        
        # Run full synchronization
        results = await integration.run_full_sync(days_back=30)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/home/ubuntu/live_gong_integration_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*60)
        print("LIVE GONG INTEGRATION RESULTS")
        print("="*60)
        print(f"API Connection: {'✅ SUCCESS' if results['api_test']['success'] else '❌ FAILED'}")
        print(f"Users Synced: {results['users_synced']}")
        print(f"Calls Available: {results['total_calls_available']}")
        print(f"Calls Synced: {results['calls_synced']}")
        print(f"Execution Time: {results['execution_time']:.2f} seconds")
        
        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        print(f"\nResults saved to: {results_file}")
        print("="*60)
        
    finally:
        await integration.close()

if __name__ == "__main__":
    asyncio.run(main())

