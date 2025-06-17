#!/usr/bin/env python3
"""
Immediate Gong API Data Extraction for Sophia Business Intelligence
Real conversation data extraction using current credentials
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

class SophiaGongDataExtractor:
    """
    Immediate data extraction from Gong API for Sophia business intelligence
    """
    
    def __init__(self):
        # Gong API credentials
        self.access_key = "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"
        self.access_secret = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tZXkiOiJUVjMzQlBaNVVONDRRS1pDWjJVQ0FLUlhIUTZRM0w1TiJ9.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU"
        
        # Create authorization header
        credentials = f"{self.access_key}:{self.access_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        # Gong API base URL
        self.base_url = "https://api.gong.io/v2"
        
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
            "pay ready", "payment", "collection", "portal", "automation"
        ]
    
    async def extract_all_data(self) -> Dict[str, Any]:
        """Extract all available data from Gong API"""
        
        extraction_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "extraction_summary": {},
            "data_quality": {},
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
            
            # Extract users
            logger.info("Extracting Gong users...")
            users_result = await self.extract_users()
            extraction_results["users"] = users_result
            
            # Extract calls
            logger.info("Extracting Gong calls...")
            calls_result = await self.extract_calls()
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
            
            # Generate summary
            extraction_results["extraction_summary"] = {
                "total_users": len(users_result.get("users", [])),
                "total_calls": len(calls_result.get("calls", [])),
                "apartment_relevant_calls": apartment_analysis.get("relevant_calls_count", 0),
                "data_quality_score": self.calculate_data_quality_score(extraction_results),
                "extraction_success": True
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
                    "message": "API connection successful"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "message": "API connection failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "API connection error"
            }
    
    async def extract_users(self) -> Dict[str, Any]:
        """Extract all users from Gong"""
        
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                # Enhance user data with apartment industry analysis
                enhanced_users = []
                for user in users:
                    enhanced_user = user.copy()
                    enhanced_user["apartment_relevance"] = self.calculate_user_apartment_relevance(user)
                    enhanced_users.append(enhanced_user)
                
                return {
                    "success": True,
                    "users": enhanced_users,
                    "total_count": len(enhanced_users),
                    "apartment_relevant_users": len([u for u in enhanced_users if u["apartment_relevance"] > 0.5])
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
    
    async def extract_calls(self) -> Dict[str, Any]:
        """Extract calls from Gong"""
        
        try:
            # Get calls from last 30 days
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
            to_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            params = {
                "fromDateTime": from_date,
                "toDateTime": to_date,
                "cursor": ""
            }
            
            all_calls = []
            page_count = 0
            max_pages = 10  # Limit to prevent excessive API calls
            
            while page_count < max_pages:
                response = requests.post(
                    f"{self.base_url}/calls",
                    headers=self.headers,
                    json=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    calls = data.get("calls", [])
                    
                    if not calls:
                        break
                    
                    # Enhance calls with apartment industry analysis
                    for call in calls:
                        call["apartment_relevance"] = self.calculate_call_apartment_relevance(call)
                        call["sophia_insights"] = self.generate_sophia_insights(call)
                    
                    all_calls.extend(calls)
                    
                    # Check for next page
                    cursor = data.get("records", {}).get("cursor")
                    if not cursor:
                        break
                    
                    params["cursor"] = cursor
                    page_count += 1
                    
                else:
                    logger.error(f"Error extracting calls: HTTP {response.status_code}: {response.text}")
                    break
            
            return {
                "success": True,
                "calls": all_calls,
                "total_count": len(all_calls),
                "pages_extracted": page_count,
                "apartment_relevant_calls": len([c for c in all_calls if c["apartment_relevance"] > 0.5])
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
                return {
                    "success": True,
                    "workspace_data": data,
                    "workspace_count": len(data.get("workspaces", []))
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
    
    def calculate_user_apartment_relevance(self, user: Dict[str, Any]) -> float:
        """Calculate apartment industry relevance for a user"""
        
        relevance_score = 0.0
        
        # Check user title/role
        title = user.get("title", "").lower()
        for keyword in ["property", "apartment", "real estate", "leasing", "management"]:
            if keyword in title:
                relevance_score += 0.2
        
        # Check company name
        company = user.get("company", "").lower()
        for keyword in ["apartment", "property", "management", "real estate"]:
            if keyword in company:
                relevance_score += 0.3
        
        return min(relevance_score, 1.0)
    
    def calculate_call_apartment_relevance(self, call: Dict[str, Any]) -> float:
        """Calculate apartment industry relevance for a call"""
        
        relevance_score = 0.0
        
        # Check call title
        title = call.get("title", "").lower()
        for keyword in self.apartment_keywords:
            if keyword in title:
                relevance_score += 0.1
        
        # Check participants
        participants = call.get("participants", [])
        for participant in participants:
            company = participant.get("company", "").lower()
            for keyword in ["apartment", "property", "management", "real estate"]:
                if keyword in company:
                    relevance_score += 0.2
        
        # Check for Pay Ready mentions
        if "pay ready" in title:
            relevance_score += 0.3
        
        return min(relevance_score, 1.0)
    
    def generate_sophia_insights(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Sophia-specific insights for a call"""
        
        insights = {
            "business_value": "medium",
            "follow_up_priority": "normal",
            "competitive_threats": [],
            "opportunity_indicators": [],
            "recommended_actions": []
        }
        
        apartment_relevance = call.get("apartment_relevance", 0.0)
        
        if apartment_relevance > 0.7:
            insights["business_value"] = "high"
            insights["follow_up_priority"] = "urgent"
            insights["opportunity_indicators"].append("High apartment industry relevance")
            insights["recommended_actions"].append("Prioritize follow-up")
            insights["recommended_actions"].append("Prepare apartment industry proposal")
        
        # Check for competitor mentions
        title = call.get("title", "").lower()
        competitors = ["appfolio", "yardi", "realpage", "entrata", "rent manager"]
        for competitor in competitors:
            if competitor in title:
                insights["competitive_threats"].append(competitor)
                insights["recommended_actions"].append(f"Address {competitor} competitive positioning")
        
        # Check call duration for engagement level
        duration = call.get("duration", 0)
        if duration > 1800:  # 30+ minutes
            insights["opportunity_indicators"].append("Long call duration indicates high engagement")
        
        return insights
    
    async def analyze_apartment_relevance(self, calls_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall apartment industry relevance"""
        
        calls = calls_result.get("calls", [])
        
        if not calls:
            return {
                "relevant_calls_count": 0,
                "total_calls": 0,
                "relevance_percentage": 0.0,
                "high_value_opportunities": [],
                "competitive_landscape": {},
                "business_insights": []
            }
        
        relevant_calls = [c for c in calls if c["apartment_relevance"] > 0.5]
        high_value_calls = [c for c in calls if c["apartment_relevance"] > 0.8]
        
        # Analyze competitive landscape
        competitors_mentioned = {}
        for call in calls:
            for threat in call.get("sophia_insights", {}).get("competitive_threats", []):
                competitors_mentioned[threat] = competitors_mentioned.get(threat, 0) + 1
        
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
                    "insights": call.get("sophia_insights")
                }
                for call in high_value_calls[:10]  # Top 10
            ],
            "competitive_landscape": competitors_mentioned,
            "business_insights": business_insights
        }
    
    async def store_data_in_sophia(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Store extracted data in Sophia database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            storage_summary = {
                "users_stored": 0,
                "calls_stored": 0,
                "insights_stored": 0,
                "errors": []
            }
            
            # Store users
            users = extraction_results.get("users", {}).get("users", [])
            for user in users:
                try:
                    await conn.execute("""
                        INSERT INTO gong_users 
                        (gong_user_id, email, first_name, last_name, title, company, 
                         apartment_relevance, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (gong_user_id) DO UPDATE SET
                            email = EXCLUDED.email,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            title = EXCLUDED.title,
                            company = EXCLUDED.company,
                            apartment_relevance = EXCLUDED.apartment_relevance,
                            updated_at = EXCLUDED.updated_at
                    """,
                        user.get("id", ""),
                        user.get("emailAddress", ""),
                        user.get("firstName", ""),
                        user.get("lastName", ""),
                        user.get("title", ""),
                        user.get("company", ""),
                        user.get("apartment_relevance", 0.0),
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
                    await conn.execute("""
                        INSERT INTO gong_calls 
                        (gong_call_id, title, started, duration, direction, 
                         apartment_relevance, sophia_insights, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (gong_call_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            started = EXCLUDED.started,
                            duration = EXCLUDED.duration,
                            direction = EXCLUDED.direction,
                            apartment_relevance = EXCLUDED.apartment_relevance,
                            sophia_insights = EXCLUDED.sophia_insights,
                            updated_at = EXCLUDED.updated_at
                    """,
                        call.get("id", ""),
                        call.get("title", ""),
                        datetime.fromisoformat(call.get("started", "").replace("Z", "+00:00")) if call.get("started") else None,
                        call.get("duration", 0),
                        call.get("direction", ""),
                        call.get("apartment_relevance", 0.0),
                        json.dumps(call.get("sophia_insights", {})),
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
        """Calculate overall data quality score"""
        
        score = 0.0
        
        # API connection success
        if extraction_results.get("api_connection", {}).get("success", False):
            score += 0.3
        
        # Users extracted
        users_count = len(extraction_results.get("users", {}).get("users", []))
        if users_count > 0:
            score += 0.2
        
        # Calls extracted
        calls_count = len(extraction_results.get("calls", {}).get("calls", []))
        if calls_count > 0:
            score += 0.3
        
        # Apartment relevance analysis
        apartment_analysis = extraction_results.get("apartment_intelligence", {})
        if apartment_analysis.get("relevant_calls_count", 0) > 0:
            score += 0.2
        
        return score

# Test the data extraction
async def test_sophia_gong_extraction():
    """Test Sophia Gong data extraction"""
    
    extractor = SophiaGongDataExtractor()
    
    # Run complete data extraction
    results = await extractor.extract_all_data()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"sophia_gong_extraction_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Sophia Gong data extraction completed. Results saved to {filename}")
    
    # Print summary
    summary = results.get("extraction_summary", {})
    print(f"\nExtraction Summary:")
    print(f"- Total Users: {summary.get('total_users', 0)}")
    print(f"- Total Calls: {summary.get('total_calls', 0)}")
    print(f"- Apartment Relevant Calls: {summary.get('apartment_relevant_calls', 0)}")
    print(f"- Data Quality Score: {summary.get('data_quality_score', 0.0):.2f}")
    print(f"- Extraction Success: {summary.get('extraction_success', False)}")
    
    return results

if __name__ == "__main__":
    # Run the extraction
    results = asyncio.run(test_sophia_gong_extraction())

