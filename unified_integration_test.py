#!/usr/bin/env python3
"""
Unified Integration Test Script for Sophia AI

This script tests the connectivity and functionality of all integrations:
- Snowflake
- Gong
- Vercel
- Estuary
- MCP

Usage:
    python unified_integration_test.py --tests all --output test_results.json
    python unified_integration_test.py --tests snowflake,gong --output snowflake_gong_results.json
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import ssl
import certifi
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("integration_tests")
console = Console()

# Load environment variables
dotenv.load_dotenv()

# Create global SSL context for all HTTP requests
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

class IntegrationTest:
    """Base class for all integration tests"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "pending"
        self.details = {}
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    async def setup(self) -> bool:
        """Setup the test environment"""
        return True
    
    async def run(self) -> bool:
        """Run the integration test"""
        self.start_time = time.time()
        try:
            result = await self._run_test()
            self.status = "success" if result else "failure"
            return result
        except Exception as e:
            logger.exception(f"Error running {self.name} test")
            self.details["error"] = str(e)
            self.status = "error"
            return False
        finally:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
    
    async def _run_test(self) -> bool:
        """Implement the actual test logic in subclasses"""
        raise NotImplementedError("Subclasses must implement _run_test")
    
    async def teardown(self) -> bool:
        """Clean up after the test"""
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test results to dictionary"""
        return {
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }


class SnowflakeTest(IntegrationTest):
    """Test Snowflake connectivity and functionality"""
    
    def __init__(self):
        super().__init__("snowflake")
        self.details = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
            "user": os.getenv("SNOWFLAKE_USER", ""),
            "database": os.getenv("SNOWFLAKE_DATABASE", ""),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", ""),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", ""),
            "role": os.getenv("SNOWFLAKE_ROLE", "")
        }
    
    async def _run_test(self) -> bool:
        """Test Snowflake connectivity and functionality"""
        try:
            # Import here to avoid dependency issues if not testing Snowflake
            import snowflake.connector
            
            # Check if credentials are provided
            if not all([
                os.getenv("SNOWFLAKE_ACCOUNT"),
                os.getenv("SNOWFLAKE_USER"),
                os.getenv("SNOWFLAKE_PASSWORD")
            ]):
                logger.error("Snowflake credentials not provided")
                self.details["error"] = "Credentials not provided"
                return False
            
            # Connect to Snowflake
            conn = snowflake.connector.connect(
                user=os.getenv("SNOWFLAKE_USER"),
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
                database=os.getenv("SNOWFLAKE_DATABASE"),
                schema=os.getenv("SNOWFLAKE_SCHEMA"),
                role=os.getenv("SNOWFLAKE_ROLE")
            )
            
            # Test query
            cursor = conn.cursor()
            cursor.execute("SELECT current_version()")
            version = cursor.fetchone()[0]
            self.details["version"] = version
            
            # Test warehouse
            cursor.execute("SELECT current_warehouse()")
            warehouse = cursor.fetchone()[0]
            self.details["active_warehouse"] = warehouse
            
            # Test role
            cursor.execute("SELECT current_role()")
            role = cursor.fetchone()[0]
            self.details["active_role"] = role
            
            # Close connection
            cursor.close()
            conn.close()
            
            logger.info(f"Snowflake connection successful: {version}")
            return True
            
        except Exception as e:
            logger.exception("Snowflake connection failed")
            self.details["error"] = str(e)
            return False


class GongTest(IntegrationTest):
    """Test Gong API connectivity and functionality"""
    
    def __init__(self):
        super().__init__("gong")
        self.details = {
            "api_key": bool(os.getenv("GONG_API_KEY", "")),
            "api_secret": bool(os.getenv("GONG_API_SECRET", ""))
        }
    
    async def _run_test(self) -> bool:
        """Test Gong API connectivity and functionality"""
        try:
            import requests
            import base64
            
            # Check if credentials are provided
            if not all([
                os.getenv("GONG_API_KEY"),
                os.getenv("GONG_API_SECRET")
            ]):
                logger.error("Gong credentials not provided")
                self.details["error"] = "Credentials not provided"
                return False
            
            # Prepare authentication
            auth_string = f"{os.getenv('GONG_API_KEY')}:{os.getenv('GONG_API_SECRET')}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json"
            }
            
            # Test API connection (get users endpoint)
            response = requests.get(
                "https://api.gong.io/v2/users",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.details["users_count"] = len(data.get("users", []))
                logger.info(f"Gong API connection successful: {self.details['users_count']} users found")
                return True
            else:
                logger.error(f"Gong API connection failed: {response.status_code} {response.text}")
                self.details["error"] = f"API returned {response.status_code}: {response.text}"
                return False
                
        except Exception as e:
            logger.exception("Gong API connection failed")
            self.details["error"] = str(e)
            return False


class VercelTest(IntegrationTest):
    """Test Vercel API connectivity and functionality"""
    
    def __init__(self):
        super().__init__("vercel")
        self.details = {
            "api_token": bool(os.getenv("VERCEL_API_TOKEN", "")),
            "team_id": os.getenv("VERCEL_TEAM_ID", ""),
            "project_id": os.getenv("VERCEL_PROJECT_ID", "")
        }
    
    async def _run_test(self) -> bool:
        """Test Vercel API connectivity and functionality"""
        try:
            import requests
            
            # Check if credentials are provided
            if not os.getenv("VERCEL_API_TOKEN"):
                logger.error("Vercel API token not provided")
                self.details["error"] = "API token not provided"
                return False
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {os.getenv('VERCEL_API_TOKEN')}",
                "Content-Type": "application/json"
            }
            
            # Test API connection (get user info)
            response = requests.get(
                "https://api.vercel.com/v2/user",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.details["user"] = data.get("user", {}).get("username")
                self.details["email"] = data.get("user", {}).get("email")
                
                # If team ID is provided, get team info
                if os.getenv("VERCEL_TEAM_ID"):
                    team_response = requests.get(
                        f"https://api.vercel.com/v2/teams/{os.getenv('VERCEL_TEAM_ID')}",
                        headers=headers
                    )
                    
                    if team_response.status_code == 200:
                        team_data = team_response.json()
                        self.details["team"] = team_data.get("name")
                
                logger.info(f"Vercel API connection successful: {self.details['user']}")
                return True
            else:
                logger.error(f"Vercel API connection failed: {response.status_code} {response.text}")
                self.details["error"] = f"API returned {response.status_code}: {response.text}"
                return False
                
        except Exception as e:
            logger.exception("Vercel API connection failed")
            self.details["error"] = str(e)
            return False


class EstuaryTest(IntegrationTest):
    """Test Estuary API connectivity and functionality"""

    def __init__(self):
        super().__init__("estuary")
        self.details = {
            "api_key": bool(os.getenv("ESTUARY_API_KEY", "")),
            "api_url": os.getenv("ESTUARY_API_URL", "https://api.estuary.tech")
        }
    
    async def _run_test(self) -> bool:
        """Test Estuary API connectivity and functionality"""
        try:
            import requests
            import urllib3
            
            # Create a session with SSL verification using certifi
            session = requests.Session()
            session.verify = certifi.where()
            
            # Check if credentials are provided
            if not os.getenv("ESTUARY_API_KEY"):
                logger.error("Estuary API key not provided")
                self.details["error"] = "API key not provided"
                return False
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {os.getenv('ESTUARY_API_KEY')}",
                "Accept": "application/json"
            }
            
            # Test API connection (get collections)
            api_url = os.getenv("ESTUARY_API_URL", "https://api.estuary.tech")
            self.details["api_url_used"] = api_url  # Log which URL is being used
            
            response = session.get(
                f"{api_url}/v1/collections",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.details["total_size"] = data.get("totalSize", 0)
                self.details["total_files"] = data.get("totalFiles", 0)
                
                logger.info(f"Estuary API connection successful: {self.details['total_files']} files")
                return True
            else:
                logger.error(f"Estuary API connection failed: {response.status_code} {response.text}")
                self.details["error"] = f"API returned {response.status_code}: {response.text}"
                return False
                
        except Exception as e:
            logger.exception("Estuary API connection failed")
            self.details["error"] = str(e)
            return False


class MCPTest(IntegrationTest):
    """Test MCP connectivity and functionality"""
    
    def __init__(self):
        super().__init__("mcp")
        self.details = {
            "config_path": os.getenv("MCP_CONFIG_PATH", "mcp_config.json")
        }
    
    async def _run_test(self) -> bool:
        """Test MCP connectivity and functionality"""
        try:
            # Check if config file exists
            config_path = os.getenv("MCP_CONFIG_PATH", "mcp_config.json")
            if not os.path.exists(config_path):
                logger.error(f"MCP config file not found: {config_path}")
                self.details["error"] = f"Config file not found: {config_path}"
                return False
            
            # Load config file
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Check if config is valid
            if not isinstance(config, dict):
                logger.error("MCP config is not a valid JSON object")
                self.details["error"] = "Config is not a valid JSON object"
                return False
            
            # Check if servers are defined
            if "servers" not in config:
                logger.error("MCP config does not contain servers")
                self.details["error"] = "Config does not contain servers"
                return False
            
            # Count servers
            servers = config.get("servers", [])
            self.details["servers_count"] = len(servers)
            
            # Get server names
            server_names = [server.get("name", "unnamed") for server in servers]
            self.details["servers"] = server_names
            
            logger.info(f"MCP config loaded successfully: {len(servers)} servers")
            return True
                
        except Exception as e:
            logger.exception("MCP config loading failed")
            self.details["error"] = str(e)
            return False


async def run_tests(test_names: List[str], output_file: Optional[str] = None) -> Dict[str, Any]:
    """Run the specified integration tests"""
    
    # Map test names to test classes
    test_classes = {
        "snowflake": SnowflakeTest,
        "gong": GongTest,
        "vercel": VercelTest,
        "estuary": EstuaryTest,
        "mcp": MCPTest,
        "all": None  # Special case, handled below
    }
    
    # Determine which tests to run
    tests_to_run = []
    if "all" in test_names:
        tests_to_run = [cls() for name, cls in test_classes.items() if name != "all"]
    else:
        for name in test_names:
            if name in test_classes and test_classes[name] is not None:
                tests_to_run.append(test_classes[name]())
            else:
                logger.warning(f"Unknown test: {name}")
    
    # Run the tests
    results = []
    overall_success = True
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        for test in tests_to_run:
            task = progress.add_task(f"Running {test.name} test...", total=None)
            
            # Setup
            await test.setup()
            
            # Run
            success = await test.run()
            if not success:
                overall_success = False
            
            # Teardown
            await test.teardown()
            
            # Store result
            results.append(test.to_dict())
            
            # Update progress
            progress.update(task, description=f"{test.name}: {test.status.upper()}")
            progress.remove_task(task)
    
    # Prepare final result
    final_result = {
        "status": "success" if overall_success else "failure",
        "timestamp": datetime.now().isoformat(),
        "tests": results
    }
    
    # Save to file if requested
    if output_file:
        with open(output_file, "w") as f:
            json.dump(final_result, f, indent=2)
        logger.info(f"Test results saved to {output_file}")
    
    # Print summary
    console.print("\n[bold]Test Summary:[/bold]")
    for test in results:
        status_color = "green" if test["status"] == "success" else "red"
        console.print(f"  {test['name']}: [{status_color}]{test['status'].upper()}[/{status_color}]")
    
    overall_color = "green" if overall_success else "red"
    console.print(f"\nOverall status: [{overall_color}]{final_result['status'].upper()}[/{overall_color}]")
    
    return final_result


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run integration tests for Sophia AI")
    parser.add_argument(
        "--tests",
        type=str,
        default="all",
        help="Comma-separated list of tests to run (snowflake,gong,vercel,estuary,mcp,all)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for test results (JSON format)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Parse test names
    test_names = [name.strip().lower() for name in args.tests.split(",")]
    
    # Run tests
    await run_tests(test_names, args.output)


if __name__ == "__main__":
    asyncio.run(main())
