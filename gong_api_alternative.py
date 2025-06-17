#!/usr/bin/env python3
"""
Alternative Gong API Implementation
Uses GET endpoints and different parameter structures to extract real data
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
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GongAPIAlternative:
    """
    Alternative Gong API implementation using GET endpoints and query parameters
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
    
    async def extract_all_available_data(self) -> Dict[str, Any]:
        """Extract all available data using alternative methods"""
        
        extraction_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "extraction_summary": {},
            "errors": []
        }
        
        try:
            # Test multiple API endpoints to find working ones
            logger.info("Testing all available Gong API endpoints...")
            
            # 1. Extract users (we know this works)
            logger.info("Extracting users...")
            users_result = await self.extract_users()
            extraction_results["users"] = users_result
            
            # 2. Extract workspaces (we know this works)
            logger.info("Extracting workspaces...")
            workspaces_result = await self.extract_workspaces()
            extraction_results["workspaces"] = workspaces_result
            
            # 3. Try different calls endpoints
            logger.info("Trying alternative calls endpoints...")
            calls_result = await self.try_alternative_calls_endpoints()
            extraction_results["calls"] = calls_result
            
            # 4. Try library endpoints
            logger.info("Trying library endpoints...")
            library_result = await self.extract_library_data()
            extraction_results["library"] = library_result
            
            # 5. Try settings endpoints
            logger.info("Trying settings endpoints...")
            settings_result = await self.extract_settings()
            extraction_results["settings"] = settings_result
            
            # 6. Try stats endpoints
            logger.info("Trying stats endpoints...")
            stats_result = await self.extract_stats()
            extraction_results["stats"] = stats_result
            
            # Store all extracted data
            logger.info("Storing extracted data in database...")
            storage_result = await self.store_all_data(extraction_results)
            extraction_results["database_storage"] = storage_result
            
            # Generate summary
            extraction_results["extraction_summary"] = {
                "total_users": len(users_result.get("users", [])),
                "total_workspaces": len(workspaces_result.get("workspaces", [])),
                "total_calls": len(calls_result.get("calls", [])),
                "working_endpoints": self.get_working_endpoints(extraction_results),
                "data_quality_score": self.calculate_data_quality_score(extraction_results),
                "extraction_success": True
            }
            
            return extraction_results
            
        except Exception as e:
            logger.error(f"Error in extract_all_available_data: {str(e)}")
            extraction_results["errors"].append(str(e))
            extraction_results["extraction_summary"]["extraction_success"] = False
            return extraction_results
    
    async def extract_users(self) -> Dict[str, Any]:
        """Extract users (we know this works)"""
        
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                # Enhance users with apartment industry analysis
                enhanced_users = []
                for user in users:
                    user["apartment_relevance"] = self.calculate_user_apartment_relevance(user)
                    user["sophia_profile"] = self.generate_user_sophia_profile(user)
                    enhanced_users.append(user)
                
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
    
    async def extract_workspaces(self) -> Dict[str, Any]:
        """Extract workspaces (we know this works)"""
        
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
                    "workspaces": data.get("workspaces", []),
                    "total_count": len(data.get("workspaces", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "workspaces": []
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workspaces": []
            }
    
    async def try_alternative_calls_endpoints(self) -> Dict[str, Any]:
        """Try different calls endpoints and parameter combinations"""
        
        calls_attempts = []
        
        # Method 1: Try GET with query parameters
        try:
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
            to_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            params = {
                "fromDateTime": f"{from_date}T00:00:00Z",
                "toDateTime": f"{to_date}T23:59:59Z"
            }
            
            query_string = urlencode(params)
            url = f"{self.base_url}/calls?{query_string}"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            calls_attempts.append({
                "method": "GET_with_query_params",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text[:500] if response.status_code != 200 else "Success",
                "calls_count": len(response.json().get("calls", [])) if response.status_code == 200 else 0
            })
            
            if response.status_code == 200:
                data = response.json()
                calls = data.get("calls", [])
                
                # Enhance calls with apartment analysis
                enhanced_calls = []
                for call in calls:
                    call["apartment_relevance"] = self.calculate_call_apartment_relevance(call)
                    call["sophia_insights"] = self.generate_call_insights(call)
                    enhanced_calls.append(call)
                
                return {
                    "success": True,
                    "calls": enhanced_calls,
                    "total_count": len(enhanced_calls),
                    "method_used": "GET_with_query_params",
                    "attempts": calls_attempts
                }
        
        except Exception as e:
            calls_attempts.append({
                "method": "GET_with_query_params",
                "error": str(e),
                "success": False
            })
        
        # Method 2: Try POST with minimal parameters
        try:
            minimal_params = {
                "filter": {
                    "fromDateTime": f"{from_date}T00:00:00Z",
                    "toDateTime": f"{to_date}T23:59:59Z"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/calls",
                headers=self.headers,
                json=minimal_params,
                timeout=30
            )
            
            calls_attempts.append({
                "method": "POST_minimal_params",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text[:500],
                "calls_count": len(response.json().get("calls", [])) if response.status_code == 200 else 0
            })
            
            if response.status_code == 200:
                data = response.json()
                calls = data.get("calls", [])
                
                enhanced_calls = []
                for call in calls:
                    call["apartment_relevance"] = self.calculate_call_apartment_relevance(call)
                    call["sophia_insights"] = self.generate_call_insights(call)
                    enhanced_calls.append(call)
                
                return {
                    "success": True,
                    "calls": enhanced_calls,
                    "total_count": len(enhanced_calls),
                    "method_used": "POST_minimal_params",
                    "attempts": calls_attempts
                }
        
        except Exception as e:
            calls_attempts.append({
                "method": "POST_minimal_params",
                "error": str(e),
                "success": False
            })
        
        # Method 3: Try different endpoint paths
        alternative_endpoints = [
            "/calls/list",
            "/calls/search",
            "/data/calls",
            "/v1/calls"
        ]
        
        for endpoint in alternative_endpoints:
            try:
                response = requests.get(
                    f"https://us-70092.api.gong.io{endpoint}",
                    headers=self.headers,
                    timeout=30
                )
                
                calls_attempts.append({
                    "method": f"GET_{endpoint}",
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response": response.text[:500],
                    "calls_count": len(response.json().get("calls", [])) if response.status_code == 200 else 0
                })
                
                if response.status_code == 200:
                    data = response.json()
                    if "calls" in data:
                        calls = data.get("calls", [])
                        
                        enhanced_calls = []
                        for call in calls:
                            call["apartment_relevance"] = self.calculate_call_apartment_relevance(call)
                            call["sophia_insights"] = self.generate_call_insights(call)
                            enhanced_calls.append(call)
                        
                        return {
                            "success": True,
                            "calls": enhanced_calls,
                            "total_count": len(enhanced_calls),
                            "method_used": f"GET_{endpoint}",
                            "attempts": calls_attempts
                        }
            
            except Exception as e:
                calls_attempts.append({
                    "method": f"GET_{endpoint}",
                    "error": str(e),
                    "success": False
                })
        
        # If all methods failed, return the attempts for debugging
        return {
            "success": False,
            "calls": [],
            "total_count": 0,
            "attempts": calls_attempts,
            "error": "All calls endpoint methods failed"
        }
    
    async def extract_library_data(self) -> Dict[str, Any]:
        """Try to extract library data"""
        
        library_attempts = []
        
        # Try different library endpoints
        library_endpoints = [
            "/library/folders",
            "/library",
            "/library/content",
            "/data/library"
        ]
        
        for endpoint in library_endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    timeout=30
                )
                
                library_attempts.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response": response.text[:500]
                })
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "library_data": data,
                        "endpoint_used": endpoint,
                        "attempts": library_attempts
                    }
            
            except Exception as e:
                library_attempts.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "success": False,
            "library_data": {},
            "attempts": library_attempts
        }
    
    async def extract_settings(self) -> Dict[str, Any]:
        """Try to extract settings data"""
        
        try:
            response = requests.get(
                f"{self.base_url}/settings",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "settings": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "settings": {}
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "settings": {}
            }
    
    async def extract_stats(self) -> Dict[str, Any]:
        """Try to extract stats data"""
        
        stats_endpoints = [
            "/stats/activity",
            "/stats/calls",
            "/stats/users",
            "/analytics/calls",
            "/analytics/activity"
        ]
        
        stats_results = {}
        
        for endpoint in stats_endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    timeout=30
                )
                
                stats_results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            
            except Exception as e:
                stats_results[endpoint] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "success": any(result["success"] for result in stats_results.values()),
            "stats_results": stats_results
        }
    
    def calculate_user_apartment_relevance(self, user: Dict[str, Any]) -> float:
        """Calculate apartment industry relevance for a user"""
        
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
            
            # Check email domain
            email = str(user.get("emailAddress", "")).lower()
            apartment_domains = ["apartments.com", "realpage.com", "yardi.com", "appfolio.com"]
            for domain in apartment_domains:
                if domain in email:
                    relevance_score += 0.3
        
        except Exception as e:
            logger.warning(f"Error calculating user relevance: {str(e)}")
        
        return min(relevance_score, 1.0)
    
    def generate_user_sophia_profile(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Sophia-specific user profile"""
        
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
    
    def calculate_call_apartment_relevance(self, call: Dict[str, Any]) -> float:
        """Calculate apartment industry relevance for a call"""
        
        relevance_score = 0.0
        
        try:
            # Check call title
            title = str(call.get("title", "")).lower()
            apartment_keywords = ["apartment", "rental", "lease", "tenant", "property", "housing", "pay ready"]
            
            for keyword in apartment_keywords:
                if keyword in title:
                    relevance_score += 0.1
            
            # Check participants
            participants = call.get("participants", [])
            if isinstance(participants, list):
                for participant in participants:
                    if isinstance(participant, dict):
                        company = str(participant.get("company", "")).lower()
                        for keyword in ["apartment", "property", "management", "real estate", "housing"]:
                            if keyword in company:
                                relevance_score += 0.15
            
            # Check call duration
            duration = call.get("duration", 0)
            if isinstance(duration, (int, float)):
                if duration > 1800:  # 30+ minutes
                    relevance_score += 0.1
        
        except Exception as e:
            logger.warning(f"Error calculating call relevance: {str(e)}")
        
        return min(relevance_score, 1.0)
    
    def generate_call_insights(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights for a call"""
        
        insights = {
            "business_value": "low",
            "follow_up_priority": "normal",
            "deal_stage": "unknown",
            "apartment_focus": False
        }
        
        try:
            apartment_relevance = call.get("apartment_relevance", 0.0)
            title = str(call.get("title", "")).lower()
            
            if apartment_relevance > 0.7:
                insights["business_value"] = "high"
                insights["follow_up_priority"] = "urgent"
                insights["apartment_focus"] = True
            elif apartment_relevance > 0.4:
                insights["business_value"] = "medium"
                insights["apartment_focus"] = True
            
            # Deal stage identification
            if any(word in title for word in ["demo", "demonstration"]):
                insights["deal_stage"] = "demonstration"
            elif any(word in title for word in ["proposal", "pricing"]):
                insights["deal_stage"] = "proposal"
            elif any(word in title for word in ["discovery", "initial"]):
                insights["deal_stage"] = "discovery"
        
        except Exception as e:
            logger.warning(f"Error generating call insights: {str(e)}")
        
        return insights
    
    async def store_all_data(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Store all extracted data in database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            storage_summary = {
                "users_stored": 0,
                "workspaces_stored": 0,
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
                    storage_summary["errors"].append(f"Error storing user: {str(e)}")
            
            # Store workspaces
            workspaces = extraction_results.get("workspaces", {}).get("workspaces", [])
            for workspace in workspaces:
                try:
                    await conn.execute("""
                        INSERT INTO gong_workspaces 
                        (gong_workspace_id, name, description, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (gong_workspace_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            updated_at = EXCLUDED.updated_at
                    """,
                        str(workspace.get("id", "")),
                        str(workspace.get("name", "")),
                        str(workspace.get("description", "")),
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                    storage_summary["workspaces_stored"] += 1
                except Exception as e:
                    storage_summary["errors"].append(f"Error storing workspace: {str(e)}")
            
            # Store calls if any were extracted
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
                        str(call.get("id", "")),
                        str(call.get("title", "")),
                        started_time,
                        int(call.get("duration", 0)),
                        str(call.get("direction", "")),
                        float(call.get("apartment_relevance", 0.0)),
                        json.dumps(call.get("sophia_insights", {})),
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                    storage_summary["calls_stored"] += 1
                except Exception as e:
                    storage_summary["errors"].append(f"Error storing call: {str(e)}")
            
            await conn.close()
            
            storage_summary["success"] = True
            return storage_summary
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "users_stored": 0,
                "workspaces_stored": 0,
                "calls_stored": 0
            }
    
    def get_working_endpoints(self, extraction_results: Dict[str, Any]) -> List[str]:
        """Get list of working endpoints"""
        
        working_endpoints = []
        
        if extraction_results.get("users", {}).get("success", False):
            working_endpoints.append("users")
        
        if extraction_results.get("workspaces", {}).get("success", False):
            working_endpoints.append("workspaces")
        
        if extraction_results.get("calls", {}).get("success", False):
            working_endpoints.append("calls")
        
        if extraction_results.get("library", {}).get("success", False):
            working_endpoints.append("library")
        
        if extraction_results.get("settings", {}).get("success", False):
            working_endpoints.append("settings")
        
        if extraction_results.get("stats", {}).get("success", False):
            working_endpoints.append("stats")
        
        return working_endpoints
    
    def calculate_data_quality_score(self, extraction_results: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        
        score = 0.0
        
        # Users (40% weight)
        if extraction_results.get("users", {}).get("success", False):
            score += 0.4
        
        # Workspaces (20% weight)
        if extraction_results.get("workspaces", {}).get("success", False):
            score += 0.2
        
        # Calls (30% weight)
        if extraction_results.get("calls", {}).get("success", False):
            score += 0.3
        
        # Other endpoints (10% weight)
        other_endpoints = ["library", "settings", "stats"]
        working_other = sum(1 for endpoint in other_endpoints 
                          if extraction_results.get(endpoint, {}).get("success", False))
        score += (working_other / len(other_endpoints)) * 0.1
        
        return score

# Test the alternative API implementation
async def test_alternative_gong_api():
    """Test the alternative Gong API implementation"""
    
    extractor = GongAPIAlternative()
    
    # Extract all available data
    logger.info("Starting alternative Gong API extraction...")
    results = await extractor.extract_all_available_data()
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"gong_alternative_extraction_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n🎯 ALTERNATIVE GONG API TEST COMPLETE")
    print(f"Results saved to: {filename}")
    
    # Print summary
    summary = results.get("extraction_summary", {})
    print(f"Users extracted: {summary.get('total_users', 0)}")
    print(f"Workspaces extracted: {summary.get('total_workspaces', 0)}")
    print(f"Calls extracted: {summary.get('total_calls', 0)}")
    print(f"Working endpoints: {', '.join(summary.get('working_endpoints', []))}")
    print(f"Data quality score: {summary.get('data_quality_score', 0.0):.2f}")
    
    # Print database storage results
    storage = results.get("database_storage", {})
    if storage.get("success"):
        print(f"\n💾 DATABASE STORAGE:")
        print(f"Users stored: {storage.get('users_stored', 0)}")
        print(f"Workspaces stored: {storage.get('workspaces_stored', 0)}")
        print(f"Calls stored: {storage.get('calls_stored', 0)}")
    
    return results

if __name__ == "__main__":
    # Run the alternative API test
    results = asyncio.run(test_alternative_gong_api())

