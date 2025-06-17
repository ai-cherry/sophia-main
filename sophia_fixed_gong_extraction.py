#!/usr/bin/env python3
"""
Fixed Sophia Gong Data Extraction - Corrected API Calls
Real conversation data extraction with proper API formatting
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

class SophiaGongDataExtractorFixed:
    """
    Fixed data extraction from Gong API for Sophia business intelligence
    """
    
    def __init__(self):
        # Updated Gong API credentials
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
    
    async def extract_all_data(self) -> Dict[str, Any]:
        """Extract all available data from Gong API with fixed formatting"""
        
        extraction_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "credentials_used": {
                "access_key": self.access_key[:10] + "...",
                "base_url": self.base_url
            },
            "extraction_summary": {},
            "apartment_intelligence": {},
            "errors": []
        }
        
        try:
            # Test API connection
            logger.info("Testing Gong API connection...")
            connection_test = await self.test_api_connection()
            extraction_results["api_connection"] = connection_test
            
            if not connection_test["success"]:
                extraction_results["errors"].append("API connection failed")
                return extraction_results
            
            logger.info("✅ API connection successful!")
            
            # Extract users with fixed formatting
            logger.info("Extracting Gong users...")
            users_result = await self.extract_users_fixed()
            extraction_results["users"] = users_result
            
            # Extract calls with proper JSON formatting
            logger.info("Extracting Gong calls...")
            calls_result = await self.extract_calls_fixed()
            extraction_results["calls"] = calls_result
            
            # Extract workspaces
            logger.info("Extracting workspace information...")
            workspace_result = await self.extract_workspace_info()
            extraction_results["workspace"] = workspace_result
            
            # Analyze apartment industry relevance
            logger.info("Analyzing apartment industry relevance...")
            apartment_analysis = await self.analyze_apartment_relevance(calls_result)
            extraction_results["apartment_intelligence"] = apartment_analysis
            
            # Store data in Sophia database
            logger.info("Storing data in Sophia database...")
            storage_result = await self.store_data_in_sophia(extraction_results)
            extraction_results["database_storage"] = storage_result
            
            # Generate comprehensive summary
            extraction_results["extraction_summary"] = {
                "total_users": len(users_result.get("users", [])),
                "total_calls": len(calls_result.get("calls", [])),
                "apartment_relevant_calls": apartment_analysis.get("relevant_calls_count", 0),
                "high_value_opportunities": len(apartment_analysis.get("high_value_opportunities", [])),
                "data_quality_score": self.calculate_data_quality_score(extraction_results),
                "extraction_success": True,
                "api_endpoints_working": [
                    endpoint for endpoint in ["users", "calls", "workspaces"] 
                    if extraction_results.get(endpoint, {}).get("success", False)
                ]
            }
            
            return extraction_results
            
        except Exception as e:
            logger.error(f"Error in data extraction: {str(e)}")
            extraction_results["errors"].append(str(e))
            extraction_results["extraction_summary"]["extraction_success"] = False
            return extraction_results
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test Gong API connection"""
        
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "user_count": len(data.get("users", [])),
                    "message": "API connection successful",
                    "base_url": self.base_url
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "message": "API connection failed",
                    "base_url": self.base_url
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "API connection error",
                "base_url": self.base_url
            }
    
    async def extract_users_fixed(self) -> Dict[str, Any]:
        """Extract users with fixed data handling"""
        
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                # Enhanced user data with safe handling
                enhanced_users = []
                for user in users:
                    enhanced_user = user.copy()
                    enhanced_user["apartment_relevance"] = self.calculate_user_apartment_relevance_safe(user)
                    enhanced_user["sophia_profile"] = self.generate_user_sophia_profile_safe(user)
                    enhanced_users.append(enhanced_user)
                
                return {
                    "success": True,
                    "users": enhanced_users,
                    "total_count": len(enhanced_users),
                    "apartment_relevant_users": len([u for u in enhanced_users if u["apartment_relevance"] > 0.5]),
                    "user_roles": self.analyze_user_roles_safe(enhanced_users)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "users": []
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "users": []
            }
    
    async def extract_calls_fixed(self) -> Dict[str, Any]:
        """Extract calls with proper JSON formatting"""
        
        try:
            # Use basic calls endpoint first, then try extensive if available
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
            to_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Try basic calls endpoint first
            params = {
                "fromDateTime": from_date,
                "toDateTime": to_date
            }
            
            response = requests.post(
                f"{self.base_url}/calls",
                headers=self.headers,
                json=params,
                timeout=30
            )
            
            all_calls = []
            
            if response.status_code == 200:
                data = response.json()
                calls = data.get("calls", [])
                
                # Enhance calls with apartment industry analysis
                for call in calls:
                    call["apartment_relevance"] = self.calculate_call_apartment_relevance_safe(call)
                    call["sophia_insights"] = self.generate_sophia_insights_safe(call)
                    call["business_intelligence"] = self.extract_business_intelligence_safe(call)
                
                all_calls.extend(calls)
                
                logger.info(f"Successfully extracted {len(all_calls)} calls")
                
                return {
                    "success": True,
                    "calls": all_calls,
                    "total_count": len(all_calls),
                    "apartment_relevant_calls": len([c for c in all_calls if c["apartment_relevance"] > 0.5]),
                    "high_value_calls": len([c for c in all_calls if c["apartment_relevance"] > 0.8]),
                    "date_range": {
                        "from": from_date,
                        "to": to_date
                    },
                    "endpoint_used": "basic_calls"
                }
            else:
                logger.error(f"Error extracting calls: HTTP {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "calls": []
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "calls": []
            }
    
    async def extract_workspace_info(self) -> Dict[str, Any]:
        """Extract workspace information"""
        
        try:
            response = requests.get(
                f"{self.base_url}/workspaces",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                workspaces = data.get("workspaces", [])
                
                # Analyze workspace for apartment industry focus
                workspace_analysis = {}
                for workspace in workspaces:
                    workspace_analysis[workspace.get("id", "unknown")] = {
                        "name": workspace.get("name", ""),
                        "apartment_focus": self.analyze_workspace_apartment_focus_safe(workspace)
                    }
                
                return {
                    "success": True,
                    "workspace_data": data,
                    "workspace_count": len(workspaces),
                    "workspace_analysis": workspace_analysis
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "workspace_data": {}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workspace_data": {}
            }
    
    def calculate_user_apartment_relevance_safe(self, user: Dict[str, Any]) -> float:
        """Safe apartment industry relevance calculation for users"""
        
        relevance_score = 0.0
        
        try:
            # Check user title/role
            title = str(user.get("title", "")).lower()
            for keyword in ["property", "apartment", "real estate", "leasing", "management", "housing"]:
                if keyword in title:
                    relevance_score += 0.15
            
            # Check company name
            company = str(user.get("company", "")).lower()
            for keyword in ["apartment", "property", "management", "real estate", "housing", "residential"]:
                if keyword in company:
                    relevance_score += 0.25
            
            # Check email domain for apartment industry indicators
            email = str(user.get("emailAddress", "")).lower()
            apartment_domains = ["apartments.com", "realpage.com", "yardi.com", "appfolio.com"]
            for domain in apartment_domains:
                if domain in email:
                    relevance_score += 0.3
        
        except Exception as e:
            logger.warning(f"Error calculating user relevance: {str(e)}")
        
        return min(relevance_score, 1.0)
    
    def calculate_call_apartment_relevance_safe(self, call: Dict[str, Any]) -> float:
        """Safe apartment industry relevance calculation for calls"""
        
        relevance_score = 0.0
        
        try:
            # Check call title
            title = str(call.get("title", "")).lower()
            for keyword in self.apartment_keywords:
                if keyword in title:
                    relevance_score += 0.05
            
            # Check participants with safe handling
            participants = call.get("participants", [])
            if isinstance(participants, list):
                for participant in participants:
                    if isinstance(participant, dict):
                        company = str(participant.get("company", "")).lower()
                        for keyword in ["apartment", "property", "management", "real estate", "housing"]:
                            if keyword in company:
                                relevance_score += 0.15
            
            # Check for Pay Ready mentions
            if "pay ready" in title:
                relevance_score += 0.4
            
            # Check call duration
            duration = call.get("duration", 0)
            if isinstance(duration, (int, float)):
                if duration > 1800:  # 30+ minutes
                    relevance_score += 0.1
                elif duration > 3600:  # 60+ minutes
                    relevance_score += 0.2
        
        except Exception as e:
            logger.warning(f"Error calculating call relevance: {str(e)}")
        
        return min(relevance_score, 1.0)
    
    def generate_sophia_insights_safe(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """Generate safe Sophia-specific insights for a call"""
        
        insights = {
            "business_value": "low",
            "follow_up_priority": "normal",
            "competitive_threats": [],
            "opportunity_indicators": [],
            "recommended_actions": [],
            "deal_stage": "unknown"
        }
        
        try:
            apartment_relevance = call.get("apartment_relevance", 0.0)
            title = str(call.get("title", "")).lower()
            
            # Business value assessment
            if apartment_relevance > 0.8:
                insights["business_value"] = "high"
                insights["follow_up_priority"] = "urgent"
                insights["opportunity_indicators"].append("High apartment industry relevance")
                insights["recommended_actions"].append("Prioritize follow-up")
            elif apartment_relevance > 0.6:
                insights["business_value"] = "medium"
                insights["follow_up_priority"] = "high"
            
            # Competitive analysis
            competitors = ["appfolio", "yardi", "realpage", "entrata", "rent manager", "buildium"]
            for competitor in competitors:
                if competitor in title:
                    insights["competitive_threats"].append(competitor)
                    insights["recommended_actions"].append(f"Address {competitor} competitive positioning")
            
            # Deal stage identification
            if any(word in title for word in ["demo", "demonstration", "presentation"]):
                insights["deal_stage"] = "demonstration"
            elif any(word in title for word in ["proposal", "pricing", "quote"]):
                insights["deal_stage"] = "proposal"
            elif any(word in title for word in ["contract", "agreement", "signing"]):
                insights["deal_stage"] = "closing"
            elif any(word in title for word in ["discovery", "initial", "introduction"]):
                insights["deal_stage"] = "discovery"
        
        except Exception as e:
            logger.warning(f"Error generating insights: {str(e)}")
        
        return insights
    
    def extract_business_intelligence_safe(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """Safe business intelligence extraction from call"""
        
        bi_data = {
            "market_segment": "unknown",
            "company_size": "unknown",
            "technology_stack": [],
            "timeline_indicators": []
        }
        
        try:
            title = str(call.get("title", "")).lower()
            
            # Market segment analysis
            if any(word in title for word in ["luxury", "high-end", "premium"]):
                bi_data["market_segment"] = "luxury"
            elif any(word in title for word in ["affordable", "budget", "low-income"]):
                bi_data["market_segment"] = "affordable"
            elif any(word in title for word in ["student", "university", "college"]):
                bi_data["market_segment"] = "student_housing"
            
            # Company size indicators
            if any(word in title for word in ["enterprise", "large", "portfolio"]):
                bi_data["company_size"] = "enterprise"
            elif any(word in title for word in ["small", "independent", "single"]):
                bi_data["company_size"] = "small"
            
            # Technology stack detection
            tech_keywords = ["salesforce", "hubspot", "yardi", "appfolio", "api", "integration"]
            for keyword in tech_keywords:
                if keyword in title:
                    bi_data["technology_stack"].append(keyword)
            
            # Timeline indicators
            timeline_keywords = ["urgent", "asap", "immediate", "q1", "q2", "q3", "q4"]
            for keyword in timeline_keywords:
                if keyword in title:
                    bi_data["timeline_indicators"].append(keyword)
        
        except Exception as e:
            logger.warning(f"Error extracting business intelligence: {str(e)}")
        
        return bi_data
    
    def generate_user_sophia_profile_safe(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Safe Sophia-specific user profile generation"""
        
        profile = {
            "role_category": "unknown",
            "influence_level": "low",
            "apartment_focus": False,
            "contact_priority": "normal"
        }
        
        try:
            title = str(user.get("title", "")).lower()
            
            # Role categorization
            if any(role in title for role in ["sales", "account", "business development"]):
                profile["role_category"] = "sales"
            elif any(role in title for role in ["manager", "director", "vp", "president", "ceo"]):
                profile["role_category"] = "management"
            elif any(role in title for role in ["property", "leasing", "maintenance"]):
                profile["role_category"] = "operations"
            
            # Influence level
            if any(role in title for role in ["ceo", "president", "founder", "owner"]):
                profile["influence_level"] = "high"
            elif any(role in title for role in ["director", "vp", "manager"]):
                profile["influence_level"] = "medium"
            
            # Apartment focus
            profile["apartment_focus"] = user.get("apartment_relevance", 0.0) > 0.5
            
            # Contact priority
            if profile["influence_level"] == "high" and profile["apartment_focus"]:
                profile["contact_priority"] = "urgent"
            elif profile["apartment_focus"]:
                profile["contact_priority"] = "high"
        
        except Exception as e:
            logger.warning(f"Error generating user profile: {str(e)}")
        
        return profile
    
    def analyze_user_roles_safe(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Safe user roles analysis"""
        
        role_analysis = {
            "total_users": len(users),
            "role_distribution": {},
            "apartment_focused_roles": {},
            "decision_makers": 0
        }
        
        try:
            for user in users:
                profile = user.get("sophia_profile", {})
                role_category = profile.get("role_category", "unknown")
                
                # Count role distribution
                role_analysis["role_distribution"][role_category] = role_analysis["role_distribution"].get(role_category, 0) + 1
                
                # Count apartment-focused roles
                if profile.get("apartment_focus", False):
                    role_analysis["apartment_focused_roles"][role_category] = role_analysis["apartment_focused_roles"].get(role_category, 0) + 1
                
                # Count decision makers
                if profile.get("influence_level") == "high":
                    role_analysis["decision_makers"] += 1
        
        except Exception as e:
            logger.warning(f"Error analyzing user roles: {str(e)}")
        
        return role_analysis
    
    def analyze_workspace_apartment_focus_safe(self, workspace: Dict[str, Any]) -> Dict[str, Any]:
        """Safe workspace apartment focus analysis"""
        
        focus_analysis = {
            "apartment_keywords_found": [],
            "focus_score": 0.0,
            "industry_indicators": []
        }
        
        try:
            name = str(workspace.get("name", "")).lower()
            
            for keyword in self.apartment_keywords:
                if keyword in name:
                    focus_analysis["apartment_keywords_found"].append(keyword)
                    focus_analysis["focus_score"] += 0.1
            
            focus_analysis["focus_score"] = min(focus_analysis["focus_score"], 1.0)
            
            if focus_analysis["focus_score"] > 0.5:
                focus_analysis["industry_indicators"].append("Strong apartment industry focus")
        
        except Exception as e:
            logger.warning(f"Error analyzing workspace focus: {str(e)}")
        
        return focus_analysis
    
    async def analyze_apartment_relevance(self, calls_result: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive apartment industry relevance analysis"""
        
        calls = calls_result.get("calls", [])
        
        if not calls:
            return {
                "relevant_calls_count": 0,
                "total_calls": 0,
                "relevance_percentage": 0.0,
                "high_value_opportunities": [],
                "competitive_landscape": {},
                "business_insights": [],
                "deal_pipeline": {}
            }
        
        relevant_calls = [c for c in calls if c.get("apartment_relevance", 0.0) > 0.5]
        high_value_calls = [c for c in calls if c.get("apartment_relevance", 0.0) > 0.8]
        
        # Competitive landscape analysis
        competitors_mentioned = {}
        deal_stages = {}
        
        for call in calls:
            insights = call.get("sophia_insights", {})
            
            # Count competitive threats
            for threat in insights.get("competitive_threats", []):
                competitors_mentioned[threat] = competitors_mentioned.get(threat, 0) + 1
            
            # Count deal stages
            stage = insights.get("deal_stage", "unknown")
            deal_stages[stage] = deal_stages.get(stage, 0) + 1
        
        # Generate business insights
        business_insights = []
        if len(relevant_calls) > 0:
            relevance_percentage = (len(relevant_calls) / len(calls)) * 100
            business_insights.append(f"{relevance_percentage:.1f}% of calls are apartment industry relevant")
        
        if len(high_value_calls) > 0:
            business_insights.append(f"{len(high_value_calls)} high-value apartment opportunities identified")
        
        if competitors_mentioned:
            top_competitor = max(competitors_mentioned.items(), key=lambda x: x[1])
            business_insights.append(f"Most mentioned competitor: {top_competitor[0]} ({top_competitor[1]} mentions)")
        
        return {
            "relevant_calls_count": len(relevant_calls),
            "total_calls": len(calls),
            "relevance_percentage": (len(relevant_calls) / len(calls)) * 100 if calls else 0,
            "high_value_opportunities": [
                {
                    "call_id": call.get("id"),
                    "title": call.get("title"),
                    "relevance": call.get("apartment_relevance"),
                    "insights": call.get("sophia_insights"),
                    "business_intelligence": call.get("business_intelligence")
                }
                for call in high_value_calls[:10]  # Top 10
            ],
            "competitive_landscape": competitors_mentioned,
            "deal_pipeline": deal_stages,
            "business_insights": business_insights
        }
    
    async def store_data_in_sophia(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Store extracted data in Sophia database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            storage_summary = {
                "users_stored": 0,
                "calls_stored": 0,
                "errors": []
            }
            
            # Store users
            users = extraction_results.get("users", {}).get("users", [])
            for user in users:
                try:
                    await conn.execute("""
                        INSERT INTO gong_users 
                        (gong_user_id, email, first_name, last_name, title, company, 
                         apartment_relevance, sophia_profile, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (gong_user_id) DO UPDATE SET
                            email = EXCLUDED.email,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            title = EXCLUDED.title,
                            company = EXCLUDED.company,
                            apartment_relevance = EXCLUDED.apartment_relevance,
                            sophia_profile = EXCLUDED.sophia_profile,
                            updated_at = EXCLUDED.updated_at
                    """,
                        str(user.get("id", "")),
                        str(user.get("emailAddress", "")),
                        str(user.get("firstName", "")),
                        str(user.get("lastName", "")),
                        str(user.get("title", "")),
                        str(user.get("company", "")),
                        float(user.get("apartment_relevance", 0.0)),
                        json.dumps(user.get("sophia_profile", {})),
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                    storage_summary["users_stored"] += 1
                except Exception as e:
                    storage_summary["errors"].append(f"Error storing user {user.get('id', 'unknown')}: {str(e)}")
            
            # Store calls
            calls = extraction_results.get("calls", {}).get("calls", [])
            for call in calls:
                try:
                    started_time = None
                    if call.get("started"):
                        try:
                            started_time = datetime.fromisoformat(call.get("started", "").replace("Z", "+00:00"))
                        except:
                            pass
                    
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
                except Exception as e:
                    storage_summary["errors"].append(f"Error storing call {call.get('id', 'unknown')}: {str(e)}")
            
            await conn.close()
            
            storage_summary["success"] = True
            return storage_summary
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "users_stored": 0,
                "calls_stored": 0
            }
    
    def calculate_data_quality_score(self, extraction_results: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        
        score = 0.0
        
        # API connection success (30%)
        if extraction_results.get("api_connection", {}).get("success", False):
            score += 0.3
        
        # Users extracted (30%)
        users_count = len(extraction_results.get("users", {}).get("users", []))
        if users_count > 0:
            score += 0.3
        
        # Calls extracted (30%)
        calls_count = len(extraction_results.get("calls", {}).get("calls", []))
        if calls_count > 0:
            score += 0.3
        
        # Apartment relevance analysis (10%)
        apartment_analysis = extraction_results.get("apartment_intelligence", {})
        if apartment_analysis.get("relevant_calls_count", 0) > 0:
            score += 0.1
        
        return score

# Test the fixed data extraction
async def test_fixed_sophia_gong_extraction():
    """Test fixed Sophia Gong data extraction"""
    
    extractor = SophiaGongDataExtractorFixed()
    
    # Run complete data extraction
    results = await extractor.extract_all_data()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"sophia_gong_extraction_fixed_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✅ Sophia Gong data extraction completed. Results saved to {filename}")
    
    # Print comprehensive summary
    summary = results.get("extraction_summary", {})
    apartment_intel = results.get("apartment_intelligence", {})
    
    print(f"\n🎯 EXTRACTION SUMMARY:")
    print(f"- API Connection: {'✅ Success' if results.get('api_connection', {}).get('success') else '❌ Failed'}")
    print(f"- Total Users: {summary.get('total_users', 0)}")
    print(f"- Total Calls: {summary.get('total_calls', 0)}")
    print(f"- Apartment Relevant Calls: {apartment_intel.get('relevant_calls_count', 0)}")
    print(f"- High Value Opportunities: {summary.get('high_value_opportunities', 0)}")
    print(f"- Relevance Percentage: {apartment_intel.get('relevance_percentage', 0.0):.1f}%")
    print(f"- Data Quality Score: {summary.get('data_quality_score', 0.0):.2f}")
    print(f"- Extraction Success: {'✅ Yes' if summary.get('extraction_success', False) else '❌ No'}")
    
    # Print business insights
    insights = apartment_intel.get("business_insights", [])
    if insights:
        print(f"\n💡 BUSINESS INSIGHTS:")
        for insight in insights:
            print(f"- {insight}")
    
    # Print competitive landscape
    competitors = apartment_intel.get("competitive_landscape", {})
    if competitors:
        print(f"\n🏢 COMPETITIVE LANDSCAPE:")
        for competitor, count in competitors.items():
            print(f"- {competitor}: {count} mentions")
    
    # Print database storage results
    storage = results.get("database_storage", {})
    if storage.get("success"):
        print(f"\n💾 DATABASE STORAGE:")
        print(f"- Users Stored: {storage.get('users_stored', 0)}")
        print(f"- Calls Stored: {storage.get('calls_stored', 0)}")
    
    return results

if __name__ == "__main__":
    # Run the fixed extraction
    results = asyncio.run(test_fixed_sophia_gong_extraction())

