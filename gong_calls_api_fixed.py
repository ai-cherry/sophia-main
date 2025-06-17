#!/usr/bin/env python3
"""
Fixed Gong Calls API Implementation
Resolves parameter requirements and extracts real conversation data
"""

import os
import json
import base64
import asyncio
import asyncpg
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GongCallsAPIFixed:
    """
    Fixed implementation of Gong Calls API with proper parameter handling
    """
    
    def __init__(self):
        # Updated Gong API credentials from the attachment
        self.access_key = "EX5L7AKSGQBOPNK66TDYVVEAKBVQ6IPK"
        self.access_secret = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNjU1NDc5ODksImFjY2Vzc0tleSI6IkVYNUw3QUtTR1FCT1BOSzY2VERZVlZFQUtCVlE2SVBLIn0.djgpFaMkt94HJHYHKbymM2D5aj_tQNJMV3aY_rwOSTY"
        
        # Create authorization header
        credentials = f"{self.access_key}:{self.access_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        # Updated Gong API base URL
        self.base_url = "https://us-70092.api.gong.io/v2"
        
        # Database configuration
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres", 
            "password": "password",
            "database": "sophia_enhanced"
        }
        
        # Apartment industry keywords for relevance scoring
        self.apartment_keywords = [
            "apartment", "rental", "lease", "tenant", "resident", "property management",
            "multifamily", "unit", "complex", "building", "rent", "deposit", "amenities",
            "maintenance", "vacancy", "occupancy", "property manager", "leasing office",
            "application", "screening", "background check", "move-in", "move-out",
            "pay ready", "payment", "collection", "portal", "automation", "renter",
            "landlord", "property owner", "real estate", "housing"
        ]
    
    async def extract_calls_with_fixed_parameters(self) -> Dict[str, Any]:
        """Extract calls with properly formatted parameters"""
        
        try:
            # First, get the list of calls using the basic endpoint
            from_date = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d")
            to_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Use the correct filter format for calls
            filter_params = {
                "filter": {
                    "fromDateTime": f"{from_date}T00:00:00Z",
                    "toDateTime": f"{to_date}T23:59:59Z"
                }
            }
            
            logger.info(f"Extracting calls from {from_date} to {to_date}")
            
            response = requests.post(
                f"{self.base_url}/calls",
                headers=self.headers,
                json=filter_params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                calls = data.get("calls", [])
                
                logger.info(f"Successfully extracted {len(calls)} calls")
                
                # Now try to get extensive data for each call
                enhanced_calls = []
                for call in calls[:10]:  # Limit to first 10 for testing
                    call_id = call.get("id")
                    if call_id:
                        extensive_data = await self.get_extensive_call_data(call_id)
                        if extensive_data:
                            call.update(extensive_data)
                        
                        # Add apartment industry analysis
                        call["apartment_relevance"] = self.calculate_apartment_relevance(call)
                        call["sophia_insights"] = self.generate_sophia_insights(call)
                        call["business_intelligence"] = self.extract_business_intelligence(call)
                        
                        enhanced_calls.append(call)
                
                return {
                    "success": True,
                    "calls": enhanced_calls,
                    "total_count": len(calls),
                    "enhanced_count": len(enhanced_calls),
                    "date_range": {
                        "from": from_date,
                        "to": to_date
                    },
                    "apartment_relevant_calls": len([c for c in enhanced_calls if c.get("apartment_relevance", 0) > 0.5]),
                    "high_value_calls": len([c for c in enhanced_calls if c.get("apartment_relevance", 0) > 0.8])
                }
            else:
                logger.error(f"Error extracting calls: HTTP {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "calls": []
                }
                
        except Exception as e:
            logger.error(f"Exception in extract_calls_with_fixed_parameters: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "calls": []
            }
    
    async def get_extensive_call_data(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get extensive call data for a specific call"""
        
        try:
            # Try the extensive endpoint with proper parameters
            extensive_params = {
                "callId": call_id,
                "contentSelector": {
                    "exposedFields": {
                        "parties": True,
                        "content": True,
                        "context": True,
                        "structure": True,
                        "collaboration": True,
                        "media": True
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/calls/extensive",
                headers=self.headers,
                json=extensive_params,
                timeout=30
            )
            
            if response.status_code == 200:
                extensive_data = response.json()
                logger.info(f"Got extensive data for call {call_id}")
                return extensive_data
            else:
                logger.warning(f"Could not get extensive data for call {call_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Error getting extensive data for call {call_id}: {str(e)}")
            return None
    
    def calculate_apartment_relevance(self, call: Dict[str, Any]) -> float:
        """Calculate apartment industry relevance for a call"""
        
        relevance_score = 0.0
        
        try:
            # Check call title
            title = str(call.get("title", "")).lower()
            for keyword in self.apartment_keywords:
                if keyword in title:
                    relevance_score += 0.05
            
            # Check participants
            parties = call.get("parties", [])
            if isinstance(parties, list):
                for party in parties:
                    if isinstance(party, dict):
                        # Check company name
                        company = str(party.get("company", "")).lower()
                        for keyword in ["apartment", "property", "management", "real estate", "housing"]:
                            if keyword in company:
                                relevance_score += 0.15
                        
                        # Check email domain
                        email = str(party.get("emailAddress", "")).lower()
                        apartment_domains = ["apartments.com", "realpage.com", "yardi.com", "appfolio.com"]
                        for domain in apartment_domains:
                            if domain in email:
                                relevance_score += 0.2
            
            # Check for Pay Ready mentions
            if "pay ready" in title:
                relevance_score += 0.4
            
            # Check call duration (longer calls often more valuable)
            duration = call.get("duration", 0)
            if isinstance(duration, (int, float)):
                if duration > 1800:  # 30+ minutes
                    relevance_score += 0.1
                elif duration > 3600:  # 60+ minutes
                    relevance_score += 0.2
            
            # Check for content keywords if available
            content = call.get("content", {})
            if isinstance(content, dict):
                transcript = str(content.get("transcript", "")).lower()
                for keyword in self.apartment_keywords:
                    if keyword in transcript:
                        relevance_score += 0.02  # Small boost per keyword in transcript
        
        except Exception as e:
            logger.warning(f"Error calculating apartment relevance: {str(e)}")
        
        return min(relevance_score, 1.0)
    
    def generate_sophia_insights(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Sophia-specific insights for a call"""
        
        insights = {
            "business_value": "low",
            "follow_up_priority": "normal",
            "competitive_threats": [],
            "opportunity_indicators": [],
            "recommended_actions": [],
            "deal_stage": "unknown",
            "apartment_focus": False
        }
        
        try:
            apartment_relevance = call.get("apartment_relevance", 0.0)
            title = str(call.get("title", "")).lower()
            
            # Business value assessment
            if apartment_relevance > 0.8:
                insights["business_value"] = "high"
                insights["follow_up_priority"] = "urgent"
                insights["opportunity_indicators"].append("High apartment industry relevance")
                insights["recommended_actions"].append("Prioritize immediate follow-up")
                insights["apartment_focus"] = True
            elif apartment_relevance > 0.6:
                insights["business_value"] = "medium"
                insights["follow_up_priority"] = "high"
                insights["apartment_focus"] = True
            elif apartment_relevance > 0.3:
                insights["business_value"] = "medium"
                insights["apartment_focus"] = True
            
            # Competitive analysis
            competitors = ["appfolio", "yardi", "realpage", "entrata", "rent manager", "buildium", "resman"]
            for competitor in competitors:
                if competitor in title:
                    insights["competitive_threats"].append(competitor)
                    insights["recommended_actions"].append(f"Address {competitor} competitive positioning")
            
            # Deal stage identification
            if any(word in title for word in ["demo", "demonstration", "presentation"]):
                insights["deal_stage"] = "demonstration"
                insights["recommended_actions"].append("Prepare compelling demo materials")
            elif any(word in title for word in ["proposal", "pricing", "quote"]):
                insights["deal_stage"] = "proposal"
                insights["recommended_actions"].append("Follow up on pricing discussion")
            elif any(word in title for word in ["contract", "agreement", "signing"]):
                insights["deal_stage"] = "closing"
                insights["recommended_actions"].append("Expedite contract finalization")
            elif any(word in title for word in ["discovery", "initial", "introduction"]):
                insights["deal_stage"] = "discovery"
                insights["recommended_actions"].append("Gather detailed requirements")
            
            # Opportunity indicators
            if any(word in title for word in ["urgent", "asap", "immediate"]):
                insights["opportunity_indicators"].append("Urgent timeline indicated")
                insights["follow_up_priority"] = "urgent"
            
            if any(word in title for word in ["budget", "approved", "funding"]):
                insights["opportunity_indicators"].append("Budget discussion")
                insights["business_value"] = "high"
            
            if any(word in title for word in ["decision", "maker", "owner", "ceo", "president"]):
                insights["opportunity_indicators"].append("Decision maker involvement")
                insights["follow_up_priority"] = "high"
        
        except Exception as e:
            logger.warning(f"Error generating insights: {str(e)}")
        
        return insights
    
    def extract_business_intelligence(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """Extract business intelligence from call"""
        
        bi_data = {
            "market_segment": "unknown",
            "company_size": "unknown",
            "technology_stack": [],
            "timeline_indicators": [],
            "pain_points": [],
            "decision_factors": []
        }
        
        try:
            title = str(call.get("title", "")).lower()
            
            # Market segment analysis
            if any(word in title for word in ["luxury", "high-end", "premium", "class a"]):
                bi_data["market_segment"] = "luxury"
            elif any(word in title for word in ["affordable", "budget", "low-income", "class c"]):
                bi_data["market_segment"] = "affordable"
            elif any(word in title for word in ["student", "university", "college"]):
                bi_data["market_segment"] = "student_housing"
            elif any(word in title for word in ["senior", "assisted", "independent"]):
                bi_data["market_segment"] = "senior_living"
            
            # Company size indicators
            if any(word in title for word in ["enterprise", "large", "portfolio", "reit"]):
                bi_data["company_size"] = "enterprise"
            elif any(word in title for word in ["small", "independent", "single", "family"]):
                bi_data["company_size"] = "small"
            elif any(word in title for word in ["medium", "regional", "multi"]):
                bi_data["company_size"] = "medium"
            
            # Technology stack detection
            tech_keywords = ["salesforce", "hubspot", "yardi", "appfolio", "realpage", "api", "integration", "software"]
            for keyword in tech_keywords:
                if keyword in title:
                    bi_data["technology_stack"].append(keyword)
            
            # Timeline indicators
            timeline_keywords = ["urgent", "asap", "immediate", "q1", "q2", "q3", "q4", "january", "february", "march"]
            for keyword in timeline_keywords:
                if keyword in title:
                    bi_data["timeline_indicators"].append(keyword)
            
            # Pain points detection
            pain_keywords = ["problem", "issue", "challenge", "difficulty", "manual", "inefficient", "slow"]
            for keyword in pain_keywords:
                if keyword in title:
                    bi_data["pain_points"].append(keyword)
            
            # Decision factors
            decision_keywords = ["roi", "cost", "savings", "efficiency", "automation", "compliance", "security"]
            for keyword in decision_keywords:
                if keyword in title:
                    bi_data["decision_factors"].append(keyword)
        
        except Exception as e:
            logger.warning(f"Error extracting business intelligence: {str(e)}")
        
        return bi_data
    
    async def store_calls_in_database(self, calls_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store extracted calls in Sophia database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            storage_summary = {
                "calls_stored": 0,
                "participants_stored": 0,
                "insights_stored": 0,
                "errors": []
            }
            
            calls = calls_data.get("calls", [])
            
            for call in calls:
                try:
                    # Parse started time
                    started_time = None
                    if call.get("started"):
                        try:
                            started_time = datetime.fromisoformat(call.get("started", "").replace("Z", "+00:00"))
                        except:
                            pass
                    
                    # Store call
                    await conn.execute("""
                        INSERT INTO gong_calls 
                        (gong_call_id, title, started, duration, direction, 
                         apartment_relevance, sophia_insights, business_intelligence, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (gong_call_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            started = EXCLUDED.started,
                            duration = EXCLUDED.duration,
                            direction = EXCLUDED.direction,
                            apartment_relevance = EXCLUDED.apartment_relevance,
                            sophia_insights = EXCLUDED.sophia_insights,
                            business_intelligence = EXCLUDED.business_intelligence,
                            updated_at = EXCLUDED.updated_at
                    """,
                        str(call.get("id", "")),
                        str(call.get("title", "")),
                        started_time,
                        int(call.get("duration", 0)),
                        str(call.get("direction", "")),
                        float(call.get("apartment_relevance", 0.0)),
                        json.dumps(call.get("sophia_insights", {})),
                        json.dumps(call.get("business_intelligence", {})),
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                    storage_summary["calls_stored"] += 1
                    
                    # Store participants
                    parties = call.get("parties", [])
                    if isinstance(parties, list):
                        for party in parties:
                            if isinstance(party, dict):
                                try:
                                    await conn.execute("""
                                        INSERT INTO gong_participants 
                                        (gong_call_id, gong_user_id, email, name, company, 
                                         title, phone_number, created_at, updated_at)
                                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                        ON CONFLICT (gong_call_id, email) DO UPDATE SET
                                            name = EXCLUDED.name,
                                            company = EXCLUDED.company,
                                            title = EXCLUDED.title,
                                            phone_number = EXCLUDED.phone_number,
                                            updated_at = EXCLUDED.updated_at
                                    """,
                                        str(call.get("id", "")),
                                        str(party.get("userId", "")),
                                        str(party.get("emailAddress", "")),
                                        str(party.get("name", "")),
                                        str(party.get("company", "")),
                                        str(party.get("title", "")),
                                        str(party.get("phoneNumber", "")),
                                        datetime.utcnow(),
                                        datetime.utcnow()
                                    )
                                    storage_summary["participants_stored"] += 1
                                except Exception as e:
                                    storage_summary["errors"].append(f"Error storing participant: {str(e)}")
                    
                    storage_summary["insights_stored"] += 1
                    
                except Exception as e:
                    storage_summary["errors"].append(f"Error storing call {call.get('id', 'unknown')}: {str(e)}")
            
            await conn.close()
            
            storage_summary["success"] = True
            return storage_summary
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "calls_stored": 0,
                "participants_stored": 0,
                "insights_stored": 0
            }

# Test the fixed calls API
async def test_fixed_gong_calls_api():
    """Test the fixed Gong calls API implementation"""
    
    extractor = GongCallsAPIFixed()
    
    # Extract calls with fixed parameters
    logger.info("Starting fixed Gong calls extraction...")
    calls_result = await extractor.extract_calls_with_fixed_parameters()
    
    if calls_result["success"]:
        logger.info(f"✅ Successfully extracted {calls_result['total_count']} calls")
        logger.info(f"Enhanced {calls_result['enhanced_count']} calls with apartment analysis")
        logger.info(f"Found {calls_result['apartment_relevant_calls']} apartment-relevant calls")
        logger.info(f"Found {calls_result['high_value_calls']} high-value opportunities")
        
        # Store in database
        logger.info("Storing calls in Sophia database...")
        storage_result = await extractor.store_calls_in_database(calls_result)
        
        if storage_result["success"]:
            logger.info(f"✅ Stored {storage_result['calls_stored']} calls in database")
            logger.info(f"✅ Stored {storage_result['participants_stored']} participants")
            logger.info(f"✅ Generated {storage_result['insights_stored']} business insights")
        else:
            logger.error(f"❌ Database storage failed: {storage_result.get('error', 'Unknown error')}")
    else:
        logger.error(f"❌ Calls extraction failed: {calls_result.get('error', 'Unknown error')}")
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"gong_calls_fixed_extraction_{timestamp}.json"
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "extraction_result": calls_result,
        "storage_result": storage_result if 'storage_result' in locals() else None
    }
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n🎯 FIXED GONG CALLS API TEST COMPLETE")
    print(f"Results saved to: {filename}")
    print(f"Calls extracted: {calls_result.get('total_count', 0)}")
    print(f"Apartment relevant: {calls_result.get('apartment_relevant_calls', 0)}")
    print(f"High value opportunities: {calls_result.get('high_value_calls', 0)}")
    
    return results

if __name__ == "__main__":
    # Run the fixed calls API test
    results = asyncio.run(test_fixed_gong_calls_api())

