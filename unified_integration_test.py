#!/usr/bin/env python3
"""
Sophia AI Unified Integration Test
Tests connectivity to Snowflake, Gong, Vercel, and Estuary and provides a comprehensive report
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("unified-integration-test")

# Try to import required modules
try:
    import aiohttp
    import snowflake.connector
except ImportError as e:
    logger.error(f"Missing required dependency: {e}")
    logger.error("Please install required packages: pip install aiohttp snowflake-connector-python")
    sys.exit(1)

class UnifiedIntegrationTester:
    """Tests connectivity to various integrations and provides a comprehensive report"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "pending",
            "recommendations": []
        }
        self.session = None
    
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def test_all_integrations(self):
        """Run all integration tests"""
        try:
            await self.setup()
            
            # Test each integration
            await self.test_gong_integration()
            await self.test_snowflake_integration()
            await self.test_estuary_integration()
            await self.test_vercel_integration()
            
            # Determine overall status
            service_statuses = [s.get("status") for s in self.results["services"].values()]
            if all(status == "connected" for status in service_statuses):
                self.results["overall_status"] = "all_connected"
            elif any(status == "connected" for status in service_statuses):
                self.results["overall_status"] = "partial_connection"
            else:
                self.results["overall_status"] = "all_failed"
                
            # Generate recommendations
            self._generate_recommendations()
                
        except Exception as e:
            logger.error(f"Error during integration tests: {e}")
            self.results["error"] = str(e)
            self.results["overall_status"] = "error"
        finally:
            await self.close()
        
        return self.results
    
    async def test_gong_integration(self):
        """Test Gong API connectivity"""
        service_name = "gong"
        logger.info(f"Testing {service_name} integration...")
        
        result = {
            "status": "unknown",
            "details": {},
            "error": None,
            "recommendations": []
        }
        
        # Check for required environment variables
        gong_api_key = os.environ.get("GONG_API_KEY")
        gong_api_secret = os.environ.get("GONG_API_SECRET")
        gong_access_key = os.environ.get("GONG_ACCESS_KEY")
        
        if not gong_api_key or not gong_api_secret:
            result["status"] = "config_error"
            result["error"] = "Missing required environment variables: GONG_API_KEY and/or GONG_API_SECRET"
            result["recommendations"].append("Set GONG_API_KEY and GONG_API_SECRET environment variables")
            self.results["services"][service_name] = result
            return
        
        try:
            # Create Basic Auth header
            import base64
            credentials = f"{gong_api_key}:{gong_api_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            auth_header = f"Basic {encoded_credentials}"
            
            # Test with workspaces endpoint
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json"
            }
            
            gong_base_url = "https://api.gong.io/v2"
            url = f"{gong_base_url}/settings/workspaces"
            
            async with self.session.get(url, headers=headers) as response:
                status_code = response.status
                
                if status_code == 200:
                    data = await response.json()
                    result["status"] = "connected"
                    result["details"] = {
                        "workspaces_count": len(data.get("workspaces", [])),
                        "api_version": "v2"
                    }
                    
                    # Add recommendations for best practices
                    if not gong_access_key:
                        result["recommendations"].append("Set GONG_ACCESS_KEY environment variable for enhanced functionality")
                else:
                    error_text = await response.text()
                    result["status"] = "connection_error"
                    result["error"] = f"API returned status {status_code}: {error_text}"
                    
                    # Add recommendations based on error
                    if status_code == 401:
                        result["recommendations"].append("Check Gong API credentials (GONG_API_KEY and GONG_API_SECRET)")
                    elif status_code == 403:
                        result["recommendations"].append("Verify Gong API permissions for the provided credentials")
                    elif status_code >= 500:
                        result["recommendations"].append("Gong API service may be experiencing issues, try again later")
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["recommendations"].append(f"Error connecting to Gong API: {str(e)}")
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")
    
    async def test_snowflake_integration(self):
        """Test Snowflake connectivity"""
        service_name = "snowflake"
        logger.info(f"Testing {service_name} integration...")
        
        result = {
            "status": "unknown",
            "details": {},
            "error": None,
            "recommendations": []
        }
        
        # Check for required environment variables
        snowflake_account = os.environ.get("SNOWFLAKE_ACCOUNT")
        snowflake_user = os.environ.get("SNOWFLAKE_USER")
        snowflake_password = os.environ.get("SNOWFLAKE_PASSWORD")
        snowflake_warehouse = os.environ.get("SNOWFLAKE_WAREHOUSE")
        snowflake_database = os.environ.get("SNOWFLAKE_DATABASE")
        
        if not snowflake_account or not snowflake_user or not snowflake_password:
            result["status"] = "config_error"
            result["error"] = "Missing required environment variables for Snowflake connection"
            result["recommendations"].append("Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and SNOWFLAKE_PASSWORD environment variables")
            self.results["services"][service_name] = result
            return
        
        try:
            # Configure Snowflake connection
            conn_config = {
                "account": snowflake_account,
                "user": snowflake_user,
                "password": snowflake_password
            }
            
            if snowflake_warehouse:
                conn_config["warehouse"] = snowflake_warehouse
            else:
                result["recommendations"].append("Set SNOWFLAKE_WAREHOUSE environment variable for better performance")
            
            if snowflake_database:
                conn_config["database"] = snowflake_database
            else:
                result["recommendations"].append("Set SNOWFLAKE_DATABASE environment variable to specify default database")
            
            # Test connection
            conn = snowflake.connector.connect(**conn_config)
            cursor = conn.cursor()
            
            # Execute a simple query to verify connection
            cursor.execute("SELECT current_version()")
            version = cursor.fetchone()[0]
            
            # Get account details
            cursor.execute("SELECT current_account(), current_role(), current_warehouse(), current_database(), current_schema()")
            account_info = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            result["status"] = "connected"
            result["details"] = {
                "version": version,
                "account": account_info[0],
                "role": account_info[1],
                "warehouse": account_info[2],
                "database": account_info[3],
                "schema": account_info[4]
            }
            
            # Add recommendations based on connection details
            if not account_info[1]:
                result["recommendations"].append("Set SNOWFLAKE_ROLE environment variable to specify default role")
            
            if not account_info[4]:
                result["recommendations"].append("Set SNOWFLAKE_SCHEMA environment variable to specify default schema")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            
            # Add recommendations based on error
            if "Authentication failed" in str(e):
                result["recommendations"].append("Check Snowflake credentials (SNOWFLAKE_USER and SNOWFLAKE_PASSWORD)")
            elif "Account does not exist" in str(e):
                result["recommendations"].append("Verify SNOWFLAKE_ACCOUNT value")
            else:
                result["recommendations"].append(f"Error connecting to Snowflake: {str(e)}")
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")
    
    async def test_estuary_integration(self):
        """Test Estuary Flow connectivity"""
        service_name = "estuary"
        logger.info(f"Testing {service_name} integration...")
        
        result = {
            "status": "unknown",
            "details": {},
            "error": None,
            "recommendations": []
        }
        
        # Check for required environment variables
        estuary_api_key = os.environ.get("ESTUARY_API_KEY")
        estuary_api_url = os.environ.get("ESTUARY_API_URL", "https://api.estuary.dev")
        
        if not estuary_api_key:
            result["status"] = "config_error"
            result["error"] = "Missing required environment variable: ESTUARY_API_KEY"
            result["recommendations"].append("Set ESTUARY_API_KEY environment variable")
            self.results["services"][service_name] = result
            return
        
        try:
            # Test connection to Estuary API
            headers = {
                "Authorization": f"Bearer {estuary_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # List collections endpoint
            url = f"{estuary_api_url}/v1/collections"
            
            async with self.session.get(url, headers=headers) as response:
                status_code = response.status
                
                if status_code == 200:
                    data = await response.json()
                    result["status"] = "connected"
                    result["details"] = {
                        "collections_count": len(data.get("collections", [])),
                        "api_url": estuary_api_url
                    }
                else:
                    error_text = await response.text()
                    result["status"] = "connection_error"
                    result["error"] = f"API returned status {status_code}: {error_text}"
                    
                    # Add recommendations based on error
                    if status_code == 401:
                        result["recommendations"].append("Check Estuary API key (ESTUARY_API_KEY)")
                    elif status_code == 403:
                        result["recommendations"].append("Verify Estuary API permissions for the provided key")
                    elif status_code >= 500:
                        result["recommendations"].append("Estuary API service may be experiencing issues, try again later")
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["recommendations"].append(f"Error connecting to Estuary API: {str(e)}")
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")
    
    async def test_vercel_integration(self):
        """Test Vercel API connectivity"""
        service_name = "vercel"
        logger.info(f"Testing {service_name} integration...")
        
        result = {
            "status": "unknown",
            "details": {},
            "error": None,
            "recommendations": []
        }
        
        # Check for required environment variables
        vercel_token = os.environ.get("VERCEL_ACCESS_TOKEN")
        
        if not vercel_token:
            result["status"] = "config_error"
            result["error"] = "Missing required environment variable: VERCEL_ACCESS_TOKEN"
            result["recommendations"].append("Set VERCEL_ACCESS_TOKEN environment variable")
            self.results["services"][service_name] = result
            return
        
        try:
            # Test connection to Vercel API
            headers = {
                "Authorization": f"Bearer {vercel_token}",
                "Content-Type": "application/json"
            }
            
            # Get user information
            url = "https://api.vercel.com/v2/user"
            
            async with self.session.get(url, headers=headers) as response:
                status_code = response.status
                
                if status_code == 200:
                    data = await response.json()
                    result["status"] = "connected"
                    result["details"] = {
                        "user": data.get("user", {}).get("username") or data.get("user", {}).get("email"),
                        "account_type": data.get("user", {}).get("account", {}).get("type"),
                        "team": data.get("user", {}).get("team", {}).get("name") if data.get("user", {}).get("team") else None
                    }
                    
                    # Get projects
                    projects_url = "https://api.vercel.com/v9/projects"
                    async with self.session.get(projects_url, headers=headers) as projects_response:
                        if projects_response.status == 200:
                            projects_data = await projects_response.json()
                            result["details"]["projects_count"] = len(projects_data.get("projects", []))
                            
                    # Check for team ID
                    if not os.environ.get("VERCEL_TEAM_ID") and result["details"].get("team"):
                        result["recommendations"].append("Set VERCEL_TEAM_ID environment variable for team-scoped operations")
                else:
                    error_text = await response.text()
                    result["status"] = "connection_error"
                    result["error"] = f"API returned status {status_code}: {error_text}"
                    
                    # Add recommendations based on error
                    if status_code == 401:
                        result["recommendations"].append("Check Vercel access token (VERCEL_ACCESS_TOKEN)")
                    elif status_code == 403:
                        result["recommendations"].append("Verify Vercel API permissions for the provided token")
                    elif status_code >= 500:
                        result["recommendations"].append("Vercel API service may be experiencing issues, try again later")
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["recommendations"].append(f"Error connecting to Vercel API: {str(e)}")
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")
    
    def _generate_recommendations(self):
        """Generate overall recommendations based on test results"""
        # Collect all service-specific recommendations
        for service_name, service_result in self.results["services"].items():
            for recommendation in service_result.get("recommendations", []):
                self.results["recommendations"].append(f"[{service_name.upper()}] {recommendation}")
        
        # Add overall recommendations
        if self.results["overall_status"] == "all_connected":
            self.results["recommendations"].append("[GENERAL] All integrations are connected successfully")
        elif self.results["overall_status"] == "partial_connection":
            self.results["recommendations"].append("[GENERAL] Some integrations failed, review individual service results")
        elif self.results["overall_status"] == "all_failed":
            self.results["recommendations"].append("[GENERAL] All integrations failed, check environment variables and network connectivity")
        
        # Add recommendations for secret management
        self.results["recommendations"].append("[SECURITY] Regularly rotate API keys and credentials using sophia_secrets.py rotate")
        self.results["recommendations"].append("[SECURITY] Ensure all secrets are stored in Pulumi ESC and synced to GitHub using sophia_secrets.py")


async def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("SOPHIA AI UNIFIED INTEGRATION TEST")
    print("="*80)
    
    tester = UnifiedIntegrationTester()
    results = await tester.test_all_integrations()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"integration_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print("\nINTEGRATION TEST RESULTS:")
    print(f"Overall Status: {results['overall_status'].upper().replace('_', ' ')}")
    print("\nService Status Summary:")
    
    for service, details in results["services"].items():
        status = details["status"]
        status_icon = "✅" if status == "connected" else "❌"
        print(f"{status_icon} {service.upper()}: {status.upper().replace('_', ' ')}")
        
        if status == "connected":
            print(f"   Details: {json.dumps(details.get('details', {}), indent=2)}")
        elif details.get("error"):
            print(f"   Error: {details['error']}")
    
    print("\nRecommendations:")
    for i, recommendation in enumerate(results["recommendations"], 1):
        print(f"{i}. {recommendation}")
    
    print(f"\nDetailed results saved to: {results_file}")
    print("="*80)
    
    # Return exit code based on overall status
    if results["overall_status"] == "all_connected":
        return 0
    elif results["overall_status"] == "partial_connection":
        return 1
    else:
        return 2

if __name__ == "__main__":
    asyncio.run(main())
