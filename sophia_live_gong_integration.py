#!/usr/bin/env python3
"""
Live Gong API Integration with Database Population
Implements complete data extraction and population with real Gong credentials
"""

import asyncio
import asyncpg
import aiohttp
import json
import logging
import base64
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import re
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GongAPIClient:
    """Production Gong API client with real credentials"""
    
    def __init__(self):
        # Real Gong credentials
        self.access_key = "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"
        self.access_key_secret = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tZXkiOiJUVjMzQlBaNVVONDRRS1pDWjJVQ0FLUlhIUTZRM0w1TiJ9.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU"
        self.base_url = "https://api.gong.io"
        self.session = None
        
    def get_auth_header(self) -> str:
        """Generate Basic Auth header"""
        credentials = f"{self.access_key}:{self.access_key_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": self.get_auth_header(),
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_workspaces(self) -> Dict[str, Any]:
        """Get available workspaces"""
        try:
            async with self.session.get(f"{self.base_url}/v2/workspaces") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Retrieved {len(data.get('workspaces', []))} workspaces")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Workspaces request failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"❌ Exception in get_workspaces: {e}")
            return {"error": str(e)}
    
    async def get_users(self, workspace_id: str = None) -> Dict[str, Any]:
        """Get users in workspace"""
        try:
            url = f"{self.base_url}/v2/users"
            params = {}
            if workspace_id:
                params["workspaceId"] = workspace_id
                
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Retrieved {len(data.get('users', []))} users")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Users request failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"❌ Exception in get_users: {e}")
            return {"error": str(e)}
    
    async def get_calls(self, from_date: datetime, to_date: datetime, 
                       workspace_id: str = None, cursor: str = None) -> Dict[str, Any]:
        """Get calls with proper parameters"""
        try:
            payload = {
                "filter": {
                    "fromDateTime": from_date.isoformat(),
                    "toDateTime": to_date.isoformat()
                }
            }
            
            if workspace_id:
                payload["filter"]["workspaceId"] = workspace_id
            if cursor:
                payload["cursor"] = cursor
                
            logger.info(f"🔍 Requesting calls from {from_date} to {to_date}")
            
            async with self.session.post(f"{self.base_url}/v2/calls", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    calls_count = len(data.get('calls', []))
                    logger.info(f"✅ Retrieved {calls_count} calls")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Calls request failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"❌ Exception in get_calls: {e}")
            return {"error": str(e)}
    
    async def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """Get detailed call information"""
        try:
            async with self.session.get(f"{self.base_url}/v2/calls/{call_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Retrieved details for call {call_id}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Call details request failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"❌ Exception in get_call_details: {e}")
            return {"error": str(e)}

class ApartmentIndustryAnalyzer:
    """Apartment industry-specific analysis engine"""
    
    def __init__(self):
        self.apartment_keywords = [
            'apartment', 'apartments', 'property', 'properties', 'rental', 'rentals',
            'tenant', 'tenants', 'lease', 'leasing', 'unit', 'units', 'building',
            'complex', 'portfolio', 'multifamily', 'resident', 'residents',
            'property management', 'rent collection', 'maintenance', 'vacancy',
            'occupancy', 'NOI', 'cap rate', 'rent roll', 'amenities', 'concierge',
            'doorman', 'parking', 'gym', 'pool', 'laundry', 'utilities'
        ]
        
        self.competitors = [
            'AppFolio', 'RentManager', 'Yardi', 'RealPage', 'Buildium', 
            'TenantCloud', 'Rent Spree', 'Zego', 'Doorloop', 'Innago',
            'Avail', 'Cozy', 'Zillow Rental Manager', 'Rentec Direct',
            'Property Matrix', 'Console', 'Entrata', 'ResMan'
        ]
        
        self.pain_points = [
            'rent collection', 'maintenance requests', 'vacancy rates',
            'tenant communication', 'lease renewals', 'property inspections',
            'accounting integration', 'compliance management', 'screening',
            'background checks', 'credit checks', 'evictions', 'late fees'
        ]
        
        self.positive_signals = [
            'budget approved', 'timeline confirmed', 'stakeholder buy-in',
            'ready to move forward', 'interested in proceeding', 'looks good',
            'excited about', 'perfect solution', 'exactly what we need',
            'when can we start', 'next steps', 'implementation timeline'
        ]
        
        self.negative_signals = [
            'too expensive', 'not in budget', 'need to think about it',
            'not the right time', 'concerns about', 'worried about',
            'not sure if', 'might not work', 'current solution works',
            'happy with current', 'switching costs', 'training time'
        ]
    
    def analyze_apartment_relevance(self, text: str) -> float:
        """Calculate apartment industry relevance score"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in self.apartment_keywords if keyword in text_lower)
        
        # Weight by text length
        words = text.split()
        if len(words) == 0:
            return 0.0
            
        # Calculate relevance score (0.0 to 1.0)
        relevance_score = min(1.0, keyword_matches / max(len(words) / 20, 1))
        return relevance_score
    
    def analyze_competitive_mentions(self, text: str) -> Dict[str, Any]:
        """Analyze competitor mentions"""
        if not text:
            return {"competitors_mentioned": [], "competitive_context": [], "threat_level": "none"}
            
        text_lower = text.lower()
        mentioned_competitors = []
        competitive_contexts = []
        
        for competitor in self.competitors:
            if competitor.lower() in text_lower:
                mentioned_competitors.append(competitor)
                # Extract context around mention
                pattern = rf'.{{0,50}}{re.escape(competitor.lower())}.{{0,50}}'
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    competitive_contexts.append({
                        "competitor": competitor,
                        "context": match.strip()
                    })
        
        # Determine threat level
        threat_level = "none"
        if len(mentioned_competitors) >= 3:
            threat_level = "high"
        elif len(mentioned_competitors) >= 2:
            threat_level = "medium"
        elif len(mentioned_competitors) >= 1:
            threat_level = "low"
        
        return {
            "competitors_mentioned": mentioned_competitors,
            "competitive_context": competitive_contexts,
            "threat_level": threat_level,
            "competitive_intensity": len(mentioned_competitors)
        }
    
    def analyze_deal_signals(self, text: str) -> Dict[str, Any]:
        """Analyze deal progression signals"""
        if not text:
            return {
                "positive_signals": [], "negative_signals": [],
                "deal_stage": "unknown", "win_probability": 0.5
            }
            
        text_lower = text.lower()
        
        found_positive = [signal for signal in self.positive_signals if signal in text_lower]
        found_negative = [signal for signal in self.negative_signals if signal in text_lower]
        
        # Calculate win probability
        positive_weight = len(found_positive) * 0.15
        negative_weight = len(found_negative) * -0.1
        base_probability = 0.5
        
        win_probability = max(0.0, min(1.0, base_probability + positive_weight + negative_weight))
        
        # Determine deal stage
        deal_stage = "discovery"
        if any(signal in text_lower for signal in ['budget approved', 'timeline confirmed']):
            deal_stage = "evaluation"
        if any(signal in text_lower for signal in ['ready to move forward', 'when can we start']):
            deal_stage = "negotiation"
        if any(signal in text_lower for signal in ['implementation', 'next steps', 'contract']):
            deal_stage = "closing"
        
        return {
            "positive_signals": found_positive,
            "negative_signals": found_negative,
            "deal_stage": deal_stage,
            "win_probability": win_probability,
            "signal_strength": len(found_positive) - len(found_negative)
        }
    
    def calculate_business_impact(self, apartment_relevance: float, 
                                competitive_analysis: Dict[str, Any],
                                deal_signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall business impact score"""
        
        # Base score from apartment relevance (40% weight)
        relevance_score = apartment_relevance * 0.4
        
        # Competitive impact (30% weight)
        competitive_score = 0
        if competitive_analysis["competitive_intensity"] > 0:
            competitive_score = min(0.3, competitive_analysis["competitive_intensity"] * 0.1)
        
        # Deal progression impact (30% weight)
        deal_score = deal_signals.get("win_probability", 0.5) * 0.3
        
        total_score = relevance_score + competitive_score + deal_score
        
        return {
            "overall_score": min(1.0, max(0.0, total_score)),
            "relevance_contribution": relevance_score,
            "competitive_contribution": competitive_score,
            "deal_contribution": deal_score,
            "confidence_level": self._calculate_confidence(apartment_relevance, competitive_analysis, deal_signals)
        }
    
    def _calculate_confidence(self, apartment_relevance: float,
                            competitive_analysis: Dict[str, Any],
                            deal_signals: Dict[str, Any]) -> float:
        """Calculate confidence in the analysis"""
        confidence_factors = []
        
        # Apartment relevance confidence
        if apartment_relevance > 0.7:
            confidence_factors.append(0.9)
        elif apartment_relevance > 0.4:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Competitive analysis confidence
        if competitive_analysis["competitive_intensity"] > 0:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        # Deal signals confidence
        total_signals = len(deal_signals.get("positive_signals", [])) + len(deal_signals.get("negative_signals", []))
        if total_signals >= 3:
            confidence_factors.append(0.9)
        elif total_signals >= 1:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        return sum(confidence_factors) / len(confidence_factors)

class SophiaDataPopulator:
    """Database population engine for Sophia"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        self.analyzer = ApartmentIndustryAnalyzer()
    
    async def connect(self):
        """Connect to database"""
        try:
            self.connection = await asyncpg.connect(self.database_url)
            logger.info("✅ Connected to Sophia database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
    
    async def populate_workspaces(self, workspaces_data: Dict[str, Any]) -> int:
        """Populate workspaces table"""
        if "error" in workspaces_data:
            logger.error(f"❌ Cannot populate workspaces: {workspaces_data['error']}")
            return 0
        
        workspaces = workspaces_data.get("workspaces", [])
        populated_count = 0
        
        for workspace in workspaces:
            try:
                workspace_id = workspace.get("id")
                workspace_name = workspace.get("name", "Unknown")
                company_name = workspace.get("companyName")
                created_date = workspace.get("createdDate")
                
                # Convert created_date if it exists
                created_timestamp = None
                if created_date:
                    try:
                        created_timestamp = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    except:
                        pass
                
                await self.connection.execute("""
                    INSERT INTO gong_workspaces 
                    (workspace_id, workspace_name, company_name, created_date, settings, last_sync)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (workspace_id) DO UPDATE SET
                        workspace_name = EXCLUDED.workspace_name,
                        company_name = EXCLUDED.company_name,
                        settings = EXCLUDED.settings,
                        last_sync = EXCLUDED.last_sync,
                        updated_at = CURRENT_TIMESTAMP
                """, workspace_id, workspace_name, company_name, created_timestamp, 
                json.dumps(workspace), datetime.utcnow())
                
                populated_count += 1
                logger.info(f"📊 Populated workspace: {workspace_name}")
                
            except Exception as e:
                logger.error(f"❌ Error populating workspace {workspace.get('id', 'unknown')}: {e}")
        
        logger.info(f"✅ Populated {populated_count} workspaces")
        return populated_count
    
    async def populate_users(self, users_data: Dict[str, Any], workspace_id: str = None) -> int:
        """Populate users table"""
        if "error" in users_data:
            logger.error(f"❌ Cannot populate users: {users_data['error']}")
            return 0
        
        users = users_data.get("users", [])
        populated_count = 0
        
        for user in users:
            try:
                user_id = user.get("id")
                email_address = user.get("emailAddress", "")
                first_name = user.get("firstName", "")
                last_name = user.get("lastName", "")
                full_name = f"{first_name} {last_name}".strip()
                phone_number = user.get("phoneNumber")
                title = user.get("title")
                
                await self.connection.execute("""
                    INSERT INTO gong_users 
                    (user_id, workspace_id, email_address, first_name, last_name, 
                     full_name, phone_number, title, settings, last_activity)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email_address = EXCLUDED.email_address,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        full_name = EXCLUDED.full_name,
                        phone_number = EXCLUDED.phone_number,
                        title = EXCLUDED.title,
                        settings = EXCLUDED.settings,
                        updated_at = CURRENT_TIMESTAMP
                """, user_id, workspace_id, email_address, first_name, last_name,
                full_name, phone_number, title, json.dumps(user), datetime.utcnow())
                
                populated_count += 1
                logger.info(f"👥 Populated user: {full_name} ({email_address})")
                
            except Exception as e:
                logger.error(f"❌ Error populating user {user.get('id', 'unknown')}: {e}")
        
        logger.info(f"✅ Populated {populated_count} users")
        return populated_count
    
    async def populate_calls(self, calls_data: Dict[str, Any], workspace_id: str = None) -> int:
        """Populate calls table with intelligence analysis"""
        if "error" in calls_data:
            logger.error(f"❌ Cannot populate calls: {calls_data['error']}")
            return 0
        
        calls = calls_data.get("calls", [])
        populated_count = 0
        
        for call in calls:
            try:
                call_id = call.get("id")
                title = call.get("title", "")
                url = call.get("url")
                started = call.get("started")
                duration = call.get("duration")
                direction = call.get("direction")
                system = call.get("system")
                scope = call.get("scope")
                media = call.get("media")
                language = call.get("language")
                primary_user_id = call.get("primaryUserId")
                meeting_url = call.get("meetingUrl")
                
                # Convert started timestamp
                started_timestamp = None
                if started:
                    try:
                        started_timestamp = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    except:
                        pass
                
                # Analyze apartment industry relevance
                analysis_text = f"{title} {call.get('purpose', '')}"
                apartment_relevance = self.analyzer.analyze_apartment_relevance(analysis_text)
                competitive_analysis = self.analyzer.analyze_competitive_mentions(analysis_text)
                deal_signals = self.analyzer.analyze_deal_signals(analysis_text)
                business_impact = self.analyzer.calculate_business_impact(
                    apartment_relevance, competitive_analysis, deal_signals
                )
                
                await self.connection.execute("""
                    INSERT INTO gong_calls 
                    (call_id, workspace_id, title, url, started, duration_seconds, 
                     direction, system, scope, media, language, primary_user_id, 
                     meeting_url, custom_data, apartment_relevance_score, 
                     business_impact_score, processing_status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    ON CONFLICT (call_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        url = EXCLUDED.url,
                        started = EXCLUDED.started,
                        duration_seconds = EXCLUDED.duration_seconds,
                        direction = EXCLUDED.direction,
                        apartment_relevance_score = EXCLUDED.apartment_relevance_score,
                        business_impact_score = EXCLUDED.business_impact_score,
                        updated_at = CURRENT_TIMESTAMP
                """, call_id, workspace_id, title, url, started_timestamp, duration,
                direction, system, scope, media, language, primary_user_id,
                meeting_url, json.dumps(call), apartment_relevance,
                business_impact["overall_score"], "processed")
                
                # Populate participants if available
                participants = call.get("participants", [])
                await self.populate_call_participants(call_id, participants)
                
                # Create intelligence record
                await self.create_conversation_intelligence(call_id, analysis_text, 
                                                          apartment_relevance, competitive_analysis, 
                                                          deal_signals, business_impact)
                
                populated_count += 1
                logger.info(f"📞 Populated call: {title[:50]}... (Relevance: {apartment_relevance:.2f})")
                
            except Exception as e:
                logger.error(f"❌ Error populating call {call.get('id', 'unknown')}: {e}")
        
        logger.info(f"✅ Populated {populated_count} calls")
        return populated_count
    
    async def populate_call_participants(self, call_id: str, participants: List[Dict[str, Any]]) -> int:
        """Populate call participants"""
        populated_count = 0
        
        for participant in participants:
            try:
                participant_id = f"{call_id}_{participant.get('userId', str(uuid.uuid4()))}"
                user_id = participant.get("userId")
                email_address = participant.get("emailAddress", "")
                name = participant.get("name", "")
                title = participant.get("title", "")
                company_name = participant.get("companyName", "")
                phone_number = participant.get("phoneNumber")
                
                await self.connection.execute("""
                    INSERT INTO gong_participants 
                    (participant_id, call_id, user_id, email_address, name, title, 
                     company_name, phone_number, interaction_stats, is_customer)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (participant_id) DO UPDATE SET
                        email_address = EXCLUDED.email_address,
                        name = EXCLUDED.name,
                        title = EXCLUDED.title,
                        company_name = EXCLUDED.company_name
                """, participant_id, call_id, user_id, email_address, name, title,
                company_name, phone_number, json.dumps(participant), 
                not participant.get("internal", False))
                
                populated_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error populating participant: {e}")
        
        return populated_count
    
    async def create_conversation_intelligence(self, call_id: str, analysis_text: str,
                                             apartment_relevance: float, competitive_analysis: Dict[str, Any],
                                             deal_signals: Dict[str, Any], business_impact: Dict[str, Any]):
        """Create conversation intelligence record"""
        try:
            intelligence_id = str(uuid.uuid4())
            
            # Generate AI summary
            ai_summary = f"Apartment industry relevance: {apartment_relevance:.2f}. "
            if competitive_analysis["competitors_mentioned"]:
                ai_summary += f"Competitors mentioned: {', '.join(competitive_analysis['competitors_mentioned'])}. "
            if deal_signals["positive_signals"]:
                ai_summary += f"Positive signals: {', '.join(deal_signals['positive_signals'][:3])}. "
            
            # Generate recommended actions
            recommended_actions = []
            if apartment_relevance > 0.7:
                recommended_actions.append("High apartment industry relevance - prioritize follow-up")
            if competitive_analysis["threat_level"] != "none":
                recommended_actions.append(f"Competitive threat level: {competitive_analysis['threat_level']} - prepare competitive response")
            if deal_signals["win_probability"] > 0.7:
                recommended_actions.append("High win probability - accelerate deal progression")
            
            await self.connection.execute("""
                INSERT INTO sophia_conversation_intelligence 
                (intelligence_id, call_id, apartment_relevance_score, business_impact_score,
                 confidence_level, processing_version, ai_summary, key_insights,
                 recommended_actions, sentiment_analysis, deal_health_score, processing_timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (intelligence_id) DO NOTHING
            """, intelligence_id, call_id, apartment_relevance, business_impact["overall_score"],
            business_impact["confidence_level"], "3.0", ai_summary, 
            json.dumps({"apartment_keywords_found": apartment_relevance > 0.3}),
            json.dumps(recommended_actions), 
            json.dumps({"overall_sentiment": "neutral"}),
            deal_signals["win_probability"], datetime.utcnow())
            
            # Create apartment analysis record
            await self.create_apartment_analysis(call_id, analysis_text, apartment_relevance)
            
            # Create competitive intelligence record if competitors mentioned
            if competitive_analysis["competitors_mentioned"]:
                await self.create_competitive_intelligence(call_id, competitive_analysis)
            
            # Create deal signals record
            await self.create_deal_signals(call_id, deal_signals)
            
        except Exception as e:
            logger.error(f"❌ Error creating conversation intelligence: {e}")
    
    async def create_apartment_analysis(self, call_id: str, analysis_text: str, relevance_score: float):
        """Create apartment industry analysis record"""
        try:
            analysis_id = str(uuid.uuid4())
            
            # Count apartment terminology
            apartment_terms = sum(1 for keyword in self.analyzer.apartment_keywords 
                                if keyword in analysis_text.lower())
            
            await self.connection.execute("""
                INSERT INTO sophia_apartment_analysis 
                (analysis_id, call_id, apartment_terminology_count, industry_relevance_factors)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (analysis_id) DO NOTHING
            """, analysis_id, call_id, apartment_terms, 
            json.dumps({"relevance_score": relevance_score, "keywords_found": apartment_terms}))
            
        except Exception as e:
            logger.error(f"❌ Error creating apartment analysis: {e}")
    
    async def create_competitive_intelligence(self, call_id: str, competitive_analysis: Dict[str, Any]):
        """Create competitive intelligence record"""
        try:
            competitive_id = str(uuid.uuid4())
            
            await self.connection.execute("""
                INSERT INTO sophia_competitive_intelligence 
                (competitive_id, call_id, competitors_mentioned, competitive_context,
                 competitive_threat_level, win_probability_impact)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (competitive_id) DO NOTHING
            """, competitive_id, call_id, competitive_analysis["competitors_mentioned"],
            json.dumps(competitive_analysis["competitive_context"]),
            competitive_analysis["threat_level"], 
            0.1 * competitive_analysis["competitive_intensity"])
            
        except Exception as e:
            logger.error(f"❌ Error creating competitive intelligence: {e}")
    
    async def create_deal_signals(self, call_id: str, deal_signals: Dict[str, Any]):
        """Create deal signals record"""
        try:
            signal_id = str(uuid.uuid4())
            
            await self.connection.execute("""
                INSERT INTO sophia_deal_signals 
                (signal_id, call_id, positive_signals, negative_signals,
                 deal_progression_stage, win_probability)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (signal_id) DO NOTHING
            """, signal_id, call_id, json.dumps(deal_signals["positive_signals"]),
            json.dumps(deal_signals["negative_signals"]),
            deal_signals["deal_stage"], deal_signals["win_probability"])
            
        except Exception as e:
            logger.error(f"❌ Error creating deal signals: {e}")

async def execute_live_gong_integration():
    """Execute complete live Gong integration with database population"""
    logger.info("🚀 Starting Live Gong API Integration with Database Population")
    
    # Database configuration
    database_url = "postgresql://postgres:password@localhost:5432/sophia_enhanced"
    
    # Initialize components
    populator = SophiaDataPopulator(database_url)
    
    try:
        # Connect to database
        connected = await populator.connect()
        if not connected:
            logger.error("❌ Failed to connect to database")
            return False
        
        async with GongAPIClient() as gong_client:
            # Step 1: Get and populate workspaces
            logger.info("📊 Extracting and populating workspaces...")
            workspaces_data = await gong_client.get_workspaces()
            workspaces_count = await populator.populate_workspaces(workspaces_data)
            
            # Step 2: Get and populate users
            logger.info("👥 Extracting and populating users...")
            users_data = await gong_client.get_users()
            users_count = await populator.populate_users(users_data)
            
            # Step 3: Get and populate calls (last 30 days)
            logger.info("📞 Extracting and populating calls...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            calls_data = await gong_client.get_calls(start_date, end_date)
            calls_count = await populator.populate_calls(calls_data)
            
            # Generate integration report
            integration_results = {
                "integration_timestamp": datetime.utcnow().isoformat(),
                "data_extraction_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "populated_records": {
                    "workspaces": workspaces_count,
                    "users": users_count,
                    "calls": calls_count
                },
                "database_status": "populated",
                "apartment_intelligence": "enabled",
                "competitive_analysis": "enabled",
                "deal_signals": "enabled"
            }
            
            # Save integration results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f'/home/ubuntu/sophia_live_integration_results_{timestamp}.json'
            
            with open(results_file, 'w') as f:
                json.dump(integration_results, f, indent=2)
            
            logger.info("🎉 Live Gong Integration Complete!")
            logger.info(f"📊 Populated: {workspaces_count} workspaces, {users_count} users, {calls_count} calls")
            logger.info(f"💾 Results saved to: {results_file}")
            
            return results_file
            
    except Exception as e:
        logger.error(f"❌ Integration failed: {e}")
        return False
        
    finally:
        await populator.close()

if __name__ == "__main__":
    asyncio.run(execute_live_gong_integration())

