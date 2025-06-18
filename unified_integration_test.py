#!/usr/bin/env python3
# Sophia AI - Unified Integration Test
# This script tests connectivity to Snowflake, Gong, Vercel, and Estuary

import os
import sys
import json
import logging
import datetime
import asyncio
import aiohttp
import traceback
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('unified-integration-test')

# Define result structure
class TestResult:
    def __init__(self, service: str, status: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.service = service
        self.status = status  # SUCCESS, FAILED, CONFIG_ERROR
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service": self.service,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }

class IntegrationTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.recommendations: List[str] = []

    async def test_snowflake(self) -> TestResult:
        """Test connectivity to Snowflake."""
        logger.info("Testing snowflake integration...")
        
        # Check for required environment variables
        required_vars = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            return TestResult(
                "SNOWFLAKE", 
                "CONFIG_ERROR",
                f"Missing required environment variables: {', '.join(missing_vars)}",
                {"missing_vars": missing_vars}
            )
        
        try:
            # Import snowflake connector
            import snowflake.connector
            
            # Connect to Snowflake
            conn = snowflake.connector.connect(
                user=os.environ.get("SNOWFLAKE_USER"),
                password=os.environ.get("SNOWFLAKE_PASSWORD"),
                account=os.environ.get("SNOWFLAKE_ACCOUNT"),
                warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", ""),
                database=os.environ.get("SNOWFLAKE_DATABASE", ""),
                schema=os.environ.get("SNOWFLAKE_SCHEMA", ""),
                role=os.environ.get("SNOWFLAKE_ROLE", "")
            )
            
            # Execute a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT current_version()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return TestResult(
                "SNOWFLAKE", 
                "SUCCESS",
                f"Successfully connected to Snowflake (Version: {version})",
                {"version": version}
            )
        except ImportError:
            return TestResult(
                "SNOWFLAKE", 
                "FAILED",
                "Failed to import snowflake-connector-python. Please install it with: pip install snowflake-connector-python",
                {"error_type": "ImportError"}
            )
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            return TestResult(
                "SNOWFLAKE", 
                "FAILED",
                f"Failed to connect to Snowflake: {str(e)}",
                error_details
            )

    async def test_gong(self) -> TestResult:
        """Test connectivity to Gong."""
        logger.info("Testing gong integration...")
        
        # Check for required environment variables
        required_vars = ["GONG_API_KEY", "GONG_API_SECRET"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            return TestResult(
                "GONG", 
                "CONFIG_ERROR",
                f"Missing required environment variables: {', '.join(missing_vars)}",
                {"missing_vars": missing_vars}
            )
        
        try:
            # Test Gong API connectivity
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('GONG_API_SECRET')}"
                }
                
                # Use the Gong API to get workspace information
                url = "https://us-70092.api.gong.io/v2/workspaces"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return TestResult(
                            "GONG", 
                            "SUCCESS",
                            "Successfully connected to Gong API",
                            {"response": data}
                        )
                    else:
                        error_text = await response.text()
                        return TestResult(
                            "GONG", 
                            "FAILED",
                            f"Failed to connect to Gong API: HTTP {response.status}",
                            {"status_code": response.status, "response": error_text}
                        )
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            return TestResult(
                "GONG", 
                "FAILED",
                f"Failed to connect to Gong API: {str(e)}",
                error_details
            )

    async def test_vercel(self) -> TestResult:
        """Test connectivity to Vercel."""
        logger.info("Testing vercel integration...")
        
        # Check for required environment variables
        if not os.environ.get("VERCEL_ACCESS_TOKEN"):
            return TestResult(
                "VERCEL", 
                "CONFIG_ERROR",
                "Missing required environment variable: VERCEL_ACCESS_TOKEN",
                {"missing_vars": ["VERCEL_ACCESS_TOKEN"]}
            )
        
        try:
            # Test Vercel API connectivity
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.environ.get('VERCEL_ACCESS_TOKEN')}"
                }
                
                # Use the Vercel API to get user information
                url = "https://api.vercel.com/v2/user"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return TestResult(
                            "VERCEL", 
                            "SUCCESS",
                            "Successfully connected to Vercel API",
                            {"user": data.get("user", {})}
                        )
                    else:
                        error_text = await response.text()
                        return TestResult(
                            "VERCEL", 
                            "FAILED",
                            f"Failed to connect to Vercel API: HTTP {response.status}",
                            {"status_code": response.status, "response": error_text}
                        )
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            return TestResult(
                "VERCEL", 
                "FAILED",
                f"Failed to connect to Vercel API: {str(e)}",
                error_details
            )

    async def test_estuary(self) -> TestResult:
        """Test connectivity to Estuary."""
        logger.info("Testing estuary integration...")
        
        # Check for required environment variables
        if not os.environ.get("ESTUARY_API_KEY"):
            return TestResult(
                "ESTUARY", 
                "CONFIG_ERROR",
                "Missing required environment variable: ESTUARY_API_KEY",
                {"missing_vars": ["ESTUARY_API_KEY"]}
            )
        
        try:
            # Test Estuary API connectivity
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.environ.get('ESTUARY_API_KEY')}",
                    "Accept": "application/json"
                }
                
                # Use the Estuary API to get user information
                url = f"{os.environ.get('ESTUARY_API_URL', 'https://api.estuary.dev')}/user/stats"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return TestResult(
                            "ESTUARY", 
                            "SUCCESS",
                            "Successfully connected to Estuary API",
                            {"stats": data}
                        )
                    else:
                        error_text = await response.text()
                        return TestResult(
                            "ESTUARY", 
                            "FAILED",
                            f"Failed to connect to Estuary API: HTTP {response.status}",
                            {"status_code": response.status, "response": error_text}
                        )
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            return TestResult(
                "ESTUARY", 
                "FAILED",
                f"Failed to connect to Estuary API: {str(e)}",
                error_details
            )

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check for failed services
        failed_services = [r for r in self.results if r.status != "SUCCESS"]
        
        # Service-specific recommendations
        for result in self.results:
            if result.service == "SNOWFLAKE" and result.status != "SUCCESS":
                if result.status == "CONFIG_ERROR":
                    recommendations.append("[SNOWFLAKE] Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and SNOWFLAKE_PASSWORD environment variables")
                else:
                    recommendations.append("[SNOWFLAKE] Check Snowflake credentials and network connectivity")
            
            elif result.service == "GONG" and result.status != "SUCCESS":
                if result.status == "CONFIG_ERROR":
                    recommendations.append("[GONG] Set GONG_API_KEY and GONG_API_SECRET environment variables")
                else:
                    recommendations.append("[GONG] Check Gong API credentials and network connectivity")
            
            elif result.service == "VERCEL" and result.status != "SUCCESS":
                if result.status == "CONFIG_ERROR":
                    recommendations.append("[VERCEL] Set VERCEL_ACCESS_TOKEN environment variable")
                else:
                    recommendations.append("[VERCEL] Check Vercel access token and network connectivity")
            
            elif result.service == "ESTUARY" and result.status != "SUCCESS":
                if result.status == "CONFIG_ERROR":
                    recommendations.append("[ESTUARY] Set ESTUARY_API_KEY environment variable")
                else:
                    recommendations.append("[ESTUARY] Check Estuary API key and network connectivity")
        
        # General recommendations
        if len(failed_services) == len(self.results):
            recommendations.append("[GENERAL] All integrations failed, check environment variables and network connectivity")
        elif len(failed_services) > 0:
            recommendations.append(f"[GENERAL] {len(failed_services)} of {len(self.results)} integrations failed, check specific service recommendations")
        
        # Security recommendations
        recommendations.append("[SECURITY] Regularly rotate API keys and credentials using sophia_secrets.py rotate")
        recommendations.append("[SECURITY] Ensure all secrets are stored in Pulumi ESC and synced to GitHub using sophia_secrets.py")
        
        return recommendations

    async def run_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        # Run tests concurrently
        tasks = [
            self.test_snowflake(),
            self.test_gong(),
            self.test_vercel(),
            self.test_estuary()
        ]
        
        self.results = await asyncio.gather(*tasks)
        
        # Generate recommendations
        self.recommendations = self.generate_recommendations()
        
        # Determine overall status
        success_count = sum(1 for r in self.results if r.status == "SUCCESS")
        if success_count == len(self.results):
            overall_status = "ALL SUCCEEDED"
        elif success_count == 0:
            overall_status = "ALL FAILED"
        else:
            overall_status = "PARTIAL SUCCESS"
        
        # Create result report
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "overall_status": overall_status,
            "success_count": success_count,
            "total_count": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "recommendations": self.recommendations
        }
        
        return report

    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save the test report to a file."""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"integration_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filename

    def print_report(self, report: Dict[str, Any]) -> None:
        """Print a human-readable version of the report."""
        print("\n" + "=" * 80)
        print("SOPHIA AI UNIFIED INTEGRATION TEST")
        print("=" * 80)
        
        # Print service results
        print("\nINTEGRATION TEST RESULTS:")
        print(f"Overall Status: {report['overall_status']}")
        print()
        
        print("Service Status Summary:")
        for result in report['results']:
            status_icon = "✅" if result['status'] == "SUCCESS" else "❌"
            print(f"{status_icon} {result['service']}: {result['status']}")
            print(f"   Error: {result['message']}")
        
        print("\nRecommendations:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"{i}. {recommendation}")
        
        # Print report file location
        print(f"\nDetailed results saved to: {self.report_filename}")
        print("=" * 80)

async def main():
    """Main function to run the integration tests."""
    tester = IntegrationTester()
    report = await tester.run_tests()
    tester.report_filename = tester.save_report(report)
    tester.print_report(report)
    
    # Return exit code based on success
    return 0 if report['overall_status'] == "ALL SUCCEEDED" else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
