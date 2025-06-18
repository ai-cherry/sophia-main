#!/usr/bin/env python3
"""
Sophia AI Integration Connectivity Test Script
Tests connectivity to Snowflake, Gong, Vercel, and Estuary
"""

import asyncio
import json
import os
import sys
import logging
import ssl
import certifi
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration-test")

# Try to import required modules
try:
    import aiohttp
    import snowflake.connector
except ImportError as e:
    logger.error(f"Missing required dependency: {e}")
    logger.error("Please install required packages: pip install aiohttp snowflake-connector-python")
    sys.exit(1)

class IntegrationTester:
    """Tests connectivity to various integrations"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "pending"
        }
        self.session = None
        self.ssl_context = None
    
    async def setup(self):
        """Initialize HTTP session with proper SSL context"""
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create connector with SSL context
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        
        # Create session with the connector
        self.session = aiohttp.ClientSession(connector=connector)
        logger.info("Initialized HTTP session with SSL certificate verification")
    
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
            "error": None
        }
        
        # Check for required environment variables
        gong_api_key = os.environ.get("GONG_API_KEY")
        gong_api_secret = os.environ.get("GONG_API_SECRET")
        gong_access_key = os.environ.get("GONG_ACCESS_KEY")
        
        if not gong_api_key or not gong_api_secret:
            result["status"] = "config_error"
            result["error"] = "Missing required environment variables: GONG_API_KEY and/or GONG_API_SECRET"
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
                else:
                    error_text = await response.text()
                    result["status"] = "connection_error"
                    result["error"] = f"API returned status {status_code}: {error_text}"
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")
    
    async def test_snowflake_integration(self):
        """Test Snowflake connectivity"""
        service_name = "snowflake"
        logger.info(f"Testing {service_name} integration...")
        
        result = {
            "status": "unknown",
            "details": {},
            "error": None
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
            
            if snowflake_database:
                conn_config["database"] = snowflake_database
            
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
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")
    
    async def test_estuary_integration(self):
        """Test Estuary Flow connectivity"""
        service_name = "estuary"
        logger.info(f"Testing {service_name} integration...")
        
        result = {
            "status": "unknown",
            "details": {},
            "error": None
        }
        
        # Check for required environment variables
        estuary_api_key = os.environ.get("ESTUARY_API_KEY")
        estuary_api_url = os.environ.get("ESTUARY_API_URL", "https://api.estuary.tech")
        
        if not estuary_api_key:
            result["status"] = "config_error"
            result["error"] = "Missing required environment variable: ESTUARY_API_KEY"
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
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")
    
    async def test_vercel_integration(self):
        """Test Vercel API connectivity"""
        service_name = "vercel"
        logger.info(f"Testing {service_name} integration...")
        
        result = {
            "status": "unknown",
            "details": {},
            "error": None
        }
        
        # Check for required environment variables
        vercel_token = os.environ.get("VERCEL_ACCESS_TOKEN")
        
        if not vercel_token:
            result["status"] = "config_error"
            result["error"] = "Missing required environment variable: VERCEL_ACCESS_TOKEN"
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
                else:
                    error_text = await response.text()
                    result["status"] = "connection_error"
                    result["error"] = f"API returned status {status_code}: {error_text}"
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        self.results["services"][service_name] = result
        logger.info(f"{service_name} test result: {result['status']}")

async def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("SOPHIA AI INTEGRATION CONNECTIVITY TEST")
    print("="*80)
    
    tester = IntegrationTester()
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
