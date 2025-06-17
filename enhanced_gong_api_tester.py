#!/usr/bin/env python3
"""
Enhanced Gong API Testing with New Credentials
Comprehensive testing of all available endpoints and data extraction
"""

import requests
import base64
import json
import asyncio
import asyncpg
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EnhancedGongAPITester:
    """
    Enhanced testing of Gong API with new credentials and comprehensive data extraction
    """
    
    def __init__(self):
        self.credentials = {
            "access_key": "EX5L7AKSGQBOPNK66TDYVVEAKBVQ6IPK",
            "client_secret": "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNjU1NDc5ODksImFjY2Vzc0tleSI6IkVYNUw3QUtTR1FCT1BOSzY2VERZVlZFQUtCVlE2SVBLIn0.djgpFaMkt94HJHYHKbymM2D5aj_tQNJMV3aY_rwOSTY",
            "base_url": "https://us-70092.api.gong.io"
        }
        
        # Create authorization header
        credentials_string = f"{self.credentials['access_key']}:{self.credentials['client_secret']}"
        encoded_credentials = base64.b64encode(credentials_string.encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres", 
            "password": "password",
            "database": "sophia_enhanced"
        }
    
    def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all available Gong API endpoints"""
        
        endpoints = {
            "users": {
                "url": "/v2/users",
                "description": "List all users in the workspace",
                "method": "GET"
            },
            "calls_basic": {
                "url": "/v2/calls",
                "description": "Basic call information",
                "method": "GET",
                "params": {"fromDateTime": "2024-01-01T00:00:00Z", "toDateTime": "2024-12-31T23:59:59Z"}
            },
            "calls_extensive": {
                "url": "/v2/calls/extensive",
                "description": "Extended call data with interaction stats",
                "method": "GET",
                "params": {"fromDateTime": "2024-01-01T00:00:00Z", "toDateTime": "2024-12-31T23:59:59Z"}
            },
            "stats_activity": {
                "url": "/v2/stats/activity/users",
                "description": "User activity statistics",
                "method": "GET",
                "params": {"fromDate": "2024-01-01", "toDate": "2024-12-31"}
            },
            "stats_interaction": {
                "url": "/v2/stats/interaction",
                "description": "Interaction statistics for calls",
                "method": "GET",
                "params": {"fromDate": "2024-01-01", "toDate": "2024-12-31"}
            },
            "library": {
                "url": "/v2/library/folders",
                "description": "Library folders and call organization",
                "method": "GET"
            },
            "settings_trackers": {
                "url": "/v2/settings/trackers",
                "description": "Keyword trackers configuration",
                "method": "GET"
            }
        }
        
        results = {}
        
        for endpoint_name, config in endpoints.items():
            try:
                url = f"{self.credentials['base_url']}{config['url']}"
                params = config.get('params', {})
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "description": config["description"],
                    "response_size": len(response.text),
                    "url": url
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result["data_structure"] = self._analyze_data_structure(data)
                        result["record_count"] = self._count_records(data)
                        result["sample_data"] = self._get_sample_data(data)
                    except json.JSONDecodeError:
                        result["data_structure"] = "non-json"
                        result["raw_response"] = response.text[:500]
                else:
                    result["error"] = response.text
                    result["error_analysis"] = self._analyze_error(response)
                
                results[endpoint_name] = result
                
            except Exception as e:
                results[endpoint_name] = {
                    "success": False,
                    "error": str(e),
                    "description": config["description"]
                }
        
        return results
    
    def _analyze_data_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze the structure of returned data"""
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys()),
                "nested_structure": {k: type(v).__name__ for k, v in data.items()}
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "item_type": type(data[0]).__name__ if data else "empty",
                "sample_keys": list(data[0].keys()) if data and isinstance(data[0], dict) else []
            }
        else:
            return {"type": type(data).__name__}
    
    def _count_records(self, data: Any) -> int:
        """Count records in the response"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Look for common pagination patterns
            for key in ['records', 'data', 'items', 'results', 'calls', 'users']:
                if key in data and isinstance(data[key], list):
                    return len(data[key])
            return 1
        return 0
    
    def _get_sample_data(self, data: Any, max_items: int = 2) -> Any:
        """Get sample data for analysis"""
        if isinstance(data, list):
            return data[:max_items]
        elif isinstance(data, dict):
            # Return a subset of the dictionary
            sample = {}
            for i, (k, v) in enumerate(data.items()):
                if i >= max_items:
                    break
                if isinstance(v, (str, int, float, bool)):
                    sample[k] = v
                elif isinstance(v, list):
                    sample[k] = v[:2] if v else []
                elif isinstance(v, dict):
                    sample[k] = {kk: vv for i, (kk, vv) in enumerate(v.items()) if i < 2}
            return sample
        return data
    
    def _analyze_error(self, response) -> Dict[str, Any]:
        """Analyze error responses"""
        analysis = {
            "status_code": response.status_code,
            "status_text": response.reason,
            "headers": dict(response.headers)
        }
        
        try:
            error_data = response.json()
            analysis["error_structure"] = error_data
        except:
            analysis["raw_error"] = response.text
        
        # Common error interpretations
        if response.status_code == 401:
            analysis["interpretation"] = "Authentication failed - check credentials"
        elif response.status_code == 403:
            analysis["interpretation"] = "Access forbidden - insufficient permissions"
        elif response.status_code == 404:
            analysis["interpretation"] = "Endpoint not found - may not be available"
        elif response.status_code == 429:
            analysis["interpretation"] = "Rate limit exceeded"
        elif response.status_code >= 500:
            analysis["interpretation"] = "Server error - try again later"
        
        return analysis
    
    async def extract_and_populate_data(self, endpoint_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract successful data and populate database"""
        
        population_results = {
            "database_operations": {},
            "data_extracted": {},
            "apartment_analysis": {}
        }
        
        try:
            # Connect to database
            conn = await asyncpg.connect(**self.db_config)
            
            # Process users data
            if endpoint_results.get("users", {}).get("success"):
                users_data = endpoint_results["users"].get("sample_data", [])
                if users_data:
                    population_results["data_extracted"]["users"] = await self._process_users_data(conn, users_data)
            
            # Process calls data
            for call_type in ["calls_basic", "calls_extensive"]:
                if endpoint_results.get(call_type, {}).get("success"):
                    calls_data = endpoint_results[call_type].get("sample_data", [])
                    if calls_data:
                        population_results["data_extracted"][call_type] = await self._process_calls_data(conn, calls_data, call_type)
            
            # Process stats data
            for stats_type in ["stats_activity", "stats_interaction"]:
                if endpoint_results.get(stats_type, {}).get("success"):
                    stats_data = endpoint_results[stats_type].get("sample_data", [])
                    if stats_data:
                        population_results["data_extracted"][stats_type] = await self._process_stats_data(conn, stats_data, stats_type)
            
            await conn.close()
            
        except Exception as e:
            population_results["database_operations"]["error"] = str(e)
        
        return population_results
    
    async def _process_users_data(self, conn, users_data: List[Dict]) -> Dict[str, Any]:
        """Process and store users data"""
        try:
            processed_users = []
            
            for user in users_data:
                # Extract user information
                user_record = {
                    "gong_user_id": user.get("id"),
                    "email": user.get("emailAddress"),
                    "first_name": user.get("firstName"),
                    "last_name": user.get("lastName"),
                    "phone": user.get("phoneNumber"),
                    "title": user.get("title"),
                    "active": user.get("active", True),
                    "created_date": user.get("created"),
                    "last_login": user.get("lastLogin")
                }
                
                processed_users.append(user_record)
                
                # Insert into database
                await conn.execute("""
                    INSERT INTO gong_users (gong_user_id, email, first_name, last_name, phone, title, active, created_date, last_login)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (gong_user_id) DO UPDATE SET
                        email = EXCLUDED.email,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        phone = EXCLUDED.phone,
                        title = EXCLUDED.title,
                        active = EXCLUDED.active,
                        last_login = EXCLUDED.last_login,
                        updated_at = CURRENT_TIMESTAMP
                """, *user_record.values())
            
            return {
                "processed_count": len(processed_users),
                "sample_records": processed_users[:2]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _process_calls_data(self, conn, calls_data: List[Dict], call_type: str) -> Dict[str, Any]:
        """Process and store calls data"""
        try:
            processed_calls = []
            
            for call in calls_data:
                # Extract call information
                call_record = {
                    "gong_call_id": call.get("id"),
                    "title": call.get("title"),
                    "url": call.get("url"),
                    "started": call.get("started"),
                    "duration": call.get("duration"),
                    "language": call.get("language"),
                    "direction": call.get("direction"),
                    "system": call.get("system"),
                    "scope": call.get("scope"),
                    "media": call.get("media"),
                    "purpose": call.get("purpose"),
                    "meeting_url": call.get("meetingUrl"),
                    "is_private": call.get("isPrivate", False),
                    "custom_data": json.dumps(call.get("customData", {})),
                    "client_unique_id": call.get("clientUniqueId")
                }
                
                processed_calls.append(call_record)
                
                # Insert into database
                await conn.execute("""
                    INSERT INTO gong_calls (gong_call_id, title, url, started, duration, language, direction, system, scope, media, purpose, meeting_url, is_private, custom_data, client_unique_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (gong_call_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        url = EXCLUDED.url,
                        started = EXCLUDED.started,
                        duration = EXCLUDED.duration,
                        language = EXCLUDED.language,
                        direction = EXCLUDED.direction,
                        system = EXCLUDED.system,
                        scope = EXCLUDED.scope,
                        media = EXCLUDED.media,
                        purpose = EXCLUDED.purpose,
                        meeting_url = EXCLUDED.meeting_url,
                        is_private = EXCLUDED.is_private,
                        custom_data = EXCLUDED.custom_data,
                        client_unique_id = EXCLUDED.client_unique_id,
                        updated_at = CURRENT_TIMESTAMP
                """, *call_record.values())
                
                # Process participants if available
                if "parties" in call:
                    for party in call["parties"]:
                        participant_record = {
                            "gong_call_id": call.get("id"),
                            "gong_user_id": party.get("userId"),
                            "email": party.get("emailAddress"),
                            "name": party.get("name"),
                            "title": party.get("title"),
                            "affiliation": party.get("affiliation"),
                            "methods": json.dumps(party.get("methods", [])),
                            "phone_number": party.get("phoneNumber"),
                            "is_organizer": party.get("isOrganizer", False),
                            "persona": party.get("persona"),
                            "context": json.dumps(party.get("context", {}))
                        }
                        
                        await conn.execute("""
                            INSERT INTO gong_participants (gong_call_id, gong_user_id, email, name, title, affiliation, methods, phone_number, is_organizer, persona, context)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            ON CONFLICT (gong_call_id, email) DO UPDATE SET
                                gong_user_id = EXCLUDED.gong_user_id,
                                name = EXCLUDED.name,
                                title = EXCLUDED.title,
                                affiliation = EXCLUDED.affiliation,
                                methods = EXCLUDED.methods,
                                phone_number = EXCLUDED.phone_number,
                                is_organizer = EXCLUDED.is_organizer,
                                persona = EXCLUDED.persona,
                                context = EXCLUDED.context,
                                updated_at = CURRENT_TIMESTAMP
                        """, *participant_record.values())
            
            return {
                "call_type": call_type,
                "processed_count": len(processed_calls),
                "sample_records": processed_calls[:2]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _process_stats_data(self, conn, stats_data: List[Dict], stats_type: str) -> Dict[str, Any]:
        """Process and store statistics data"""
        try:
            processed_stats = []
            
            for stat in stats_data:
                # Create a generic stats record
                stats_record = {
                    "stats_type": stats_type,
                    "gong_user_id": stat.get("userId"),
                    "period_start": stat.get("fromDate") or stat.get("fromDateTime"),
                    "period_end": stat.get("toDate") or stat.get("toDateTime"),
                    "metrics": json.dumps(stat),
                    "created_at": datetime.utcnow()
                }
                
                processed_stats.append(stats_record)
                
                # Insert into database (assuming we have a stats table)
                await conn.execute("""
                    INSERT INTO gong_stats (stats_type, gong_user_id, period_start, period_end, metrics, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, *stats_record.values())
            
            return {
                "stats_type": stats_type,
                "processed_count": len(processed_stats),
                "sample_records": processed_stats[:2]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_apartment_industry_relevance(self, endpoint_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data for apartment industry relevance"""
        
        relevance_analysis = {
            "apartment_keywords": [
                "apartment", "property", "lease", "rent", "tenant", "resident",
                "multifamily", "community", "unit", "building", "complex",
                "property management", "leasing", "maintenance", "collections"
            ],
            "competitor_keywords": [
                "yardi", "realpage", "appfolio", "entrata", "rent manager",
                "property solutions", "apartment software", "property tech"
            ],
            "analysis_results": {}
        }
        
        for endpoint_name, result in endpoint_results.items():
            if result.get("success") and result.get("sample_data"):
                relevance_analysis["analysis_results"][endpoint_name] = self._analyze_content_relevance(
                    result["sample_data"], 
                    relevance_analysis["apartment_keywords"],
                    relevance_analysis["competitor_keywords"]
                )
        
        return relevance_analysis
    
    def _analyze_content_relevance(self, data: Any, apartment_keywords: List[str], competitor_keywords: List[str]) -> Dict[str, Any]:
        """Analyze content for apartment industry and competitor relevance"""
        
        # Convert data to searchable text
        text_content = json.dumps(data).lower()
        
        apartment_matches = sum(1 for keyword in apartment_keywords if keyword in text_content)
        competitor_matches = sum(1 for keyword in competitor_keywords if keyword in text_content)
        
        return {
            "apartment_keyword_matches": apartment_matches,
            "competitor_keyword_matches": competitor_matches,
            "apartment_relevance_score": apartment_matches / len(apartment_keywords),
            "competitor_relevance_score": competitor_matches / len(competitor_keywords),
            "total_relevance_score": (apartment_matches + competitor_matches) / (len(apartment_keywords) + len(competitor_keywords))
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive testing and analysis report"""
        
        print("🔍 ENHANCED GONG API TESTING")
        print("="*50)
        
        # Test all endpoints
        print("1. Testing API endpoints...")
        endpoint_results = self.test_all_endpoints()
        
        # Analyze apartment industry relevance
        print("2. Analyzing apartment industry relevance...")
        relevance_analysis = self.analyze_apartment_industry_relevance(endpoint_results)
        
        # Extract and populate data
        print("3. Extracting and populating database...")
        try:
            population_results = asyncio.run(self.extract_and_populate_data(endpoint_results))
        except Exception as e:
            population_results = {"error": str(e)}
        
        # Compile comprehensive report
        report = {
            "test_summary": {
                "timestamp": datetime.utcnow().isoformat(),
                "credentials_used": {
                    "access_key": self.credentials["access_key"],
                    "base_url": self.credentials["base_url"]
                },
                "total_endpoints_tested": len(endpoint_results),
                "successful_endpoints": sum(1 for r in endpoint_results.values() if r.get("success")),
                "failed_endpoints": sum(1 for r in endpoint_results.values() if not r.get("success"))
            },
            "endpoint_results": endpoint_results,
            "apartment_relevance": relevance_analysis,
            "database_population": population_results,
            "recommendations": {
                "immediate_actions": [
                    "Focus on successful endpoints for data extraction",
                    "Investigate failed endpoints for permission issues",
                    "Implement apartment industry keyword tracking",
                    "Set up automated data synchronization"
                ],
                "api_optimization": [
                    "Implement proper error handling for failed endpoints",
                    "Add retry logic for rate-limited requests",
                    "Cache frequently accessed data",
                    "Monitor API usage and performance"
                ],
                "business_intelligence": [
                    "Develop apartment industry conversation scoring",
                    "Create competitor mention tracking",
                    "Implement deal progression analysis",
                    "Build customer success metrics dashboard"
                ]
            }
        }
        
        return report

def main():
    """Main execution function"""
    tester = EnhancedGongAPITester()
    
    # Generate comprehensive report
    report = tester.generate_comprehensive_report()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/home/ubuntu/enhanced_gong_api_testing_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📁 Report saved to: {results_file}")
    
    # Print summary
    summary = report["test_summary"]
    print(f"\n📊 TEST SUMMARY:")
    print(f"   Total endpoints tested: {summary['total_endpoints_tested']}")
    print(f"   Successful: {summary['successful_endpoints']}")
    print(f"   Failed: {summary['failed_endpoints']}")
    print(f"   Success rate: {(summary['successful_endpoints']/summary['total_endpoints_tested']*100):.1f}%")
    
    # Print apartment relevance
    if report["apartment_relevance"]["analysis_results"]:
        print(f"\n🏢 APARTMENT INDUSTRY RELEVANCE:")
        for endpoint, analysis in report["apartment_relevance"]["analysis_results"].items():
            if analysis["total_relevance_score"] > 0:
                print(f"   {endpoint}: {analysis['total_relevance_score']:.2f} relevance score")
    
    return report

if __name__ == "__main__":
    main()

