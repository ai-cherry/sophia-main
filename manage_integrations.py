#!/usr/bin/env python3
"""
Sophia AI Integration Management Script

This script provides utilities for managing integrations with external services:
- Snowflake
- Gong
- Vercel
- Estuary
- MCP

Usage:
    python manage_integrations.py --action check --service all
    python manage_integrations.py --action rotate --service gong
    python manage_integrations.py --action configure --service snowflake
"""

import argparse
import base64
import json
import logging
import os
import secrets
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import dotenv
import requests
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("integration_management")
console = Console()

# Load environment variables
dotenv.load_dotenv()


class IntegrationManager:
    """Base class for all integration managers"""
    
    def __init__(self, name: str):
        self.name = name
        self.env_file = ".env"
        self.env_example_file = "integration.env.example"
    
    def check(self) -> Dict[str, Any]:
        """Check the integration status"""
        raise NotImplementedError("Subclasses must implement check")
    
    def rotate(self) -> Dict[str, Any]:
        """Rotate the integration credentials"""
        raise NotImplementedError("Subclasses must implement rotate")
    
    def configure(self) -> Dict[str, Any]:
        """Configure the integration"""
        raise NotImplementedError("Subclasses must implement configure")
    
    def _update_env_file(self, updates: Dict[str, str]) -> bool:
        """Update the .env file with new values"""
        try:
            # Load current .env file
            env_vars = {}
            if os.path.exists(self.env_file):
                with open(self.env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key] = value
            
            # Update with new values
            env_vars.update(updates)
            
            # Write back to .env file
            with open(self.env_file, "w") as f:
                for key, value in sorted(env_vars.items()):
                    f.write(f"{key}={value}\n")
            
            # Also update environment variables in current process
            for key, value in updates.items():
                os.environ[key] = value
            
            return True
        except Exception as e:
            logger.exception(f"Error updating .env file: {e}")
            return False
    
    def _generate_password(self, length: int = 24) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class SnowflakeManager(IntegrationManager):
    """Manager for Snowflake integration"""
    
    def __init__(self):
        super().__init__("snowflake")
        self.required_vars = [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
            "SNOWFLAKE_ROLE"
        ]
    
    def check(self) -> Dict[str, Any]:
        """Check Snowflake connection"""
        result = {
            "name": self.name,
            "status": "unconfigured",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all required variables are set
        missing_vars = [var for var in self.required_vars if not os.getenv(var)]
        if missing_vars:
            result["details"]["missing_vars"] = missing_vars
            return result
        
        try:
            # Import here to avoid dependency issues
            import snowflake.connector
            
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
            result["details"]["version"] = version
            
            # Test warehouse
            cursor.execute("SELECT current_warehouse()")
            warehouse = cursor.fetchone()[0]
            result["details"]["warehouse"] = warehouse
            
            # Test role
            cursor.execute("SELECT current_role()")
            role = cursor.fetchone()[0]
            result["details"]["role"] = role
            
            # Close connection
            cursor.close()
            conn.close()
            
            result["status"] = "connected"
            logger.info(f"Snowflake connection successful: {version}")
            
        except Exception as e:
            logger.exception("Snowflake connection failed")
            result["status"] = "error"
            result["details"]["error"] = str(e)
        
        return result
    
    def rotate(self) -> Dict[str, Any]:
        """Rotate Snowflake credentials"""
        result = {
            "name": self.name,
            "status": "not_supported",
            "details": {
                "message": "Automatic credential rotation is not supported for Snowflake. Please rotate credentials manually in the Snowflake console."
            },
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[yellow]Snowflake credential rotation must be done manually.[/yellow]")
        console.print("Please follow these steps:")
        console.print("1. Log in to the Snowflake console")
        console.print("2. Navigate to User Management")
        console.print("3. Reset the password for the user")
        console.print("4. Update the .env file with the new password")
        
        # Prompt for new password
        if Confirm.ask("Have you reset the password in Snowflake?"):
            new_password = Prompt.ask("Enter the new password", password=True)
            if new_password:
                if self._update_env_file({"SNOWFLAKE_PASSWORD": new_password}):
                    result["status"] = "rotated"
                    result["details"]["message"] = "Password updated in .env file"
                    logger.info("Snowflake password updated in .env file")
                else:
                    result["status"] = "error"
                    result["details"]["message"] = "Failed to update password in .env file"
        
        return result
    
    def configure(self) -> Dict[str, Any]:
        """Configure Snowflake integration"""
        result = {
            "name": self.name,
            "status": "pending",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[bold]Configuring Snowflake Integration[/bold]")
        console.print("Please provide the following information:")
        
        # Collect configuration
        config = {}
        config["SNOWFLAKE_ACCOUNT"] = Prompt.ask("Snowflake Account", default=os.getenv("SNOWFLAKE_ACCOUNT", ""))
        config["SNOWFLAKE_USER"] = Prompt.ask("Snowflake User", default=os.getenv("SNOWFLAKE_USER", ""))
        config["SNOWFLAKE_PASSWORD"] = Prompt.ask("Snowflake Password", password=True, default="")
        config["SNOWFLAKE_WAREHOUSE"] = Prompt.ask("Snowflake Warehouse", default=os.getenv("SNOWFLAKE_WAREHOUSE", "SOPHIA_DEV_WH"))
        config["SNOWFLAKE_DATABASE"] = Prompt.ask("Snowflake Database", default=os.getenv("SNOWFLAKE_DATABASE", "SOPHIA_DEV"))
        config["SNOWFLAKE_SCHEMA"] = Prompt.ask("Snowflake Schema", default=os.getenv("SNOWFLAKE_SCHEMA", "SOPHIA_MAIN"))
        config["SNOWFLAKE_ROLE"] = Prompt.ask("Snowflake Role", default=os.getenv("SNOWFLAKE_ROLE", "SOPHIA_DEV_ROLE"))
        
        # Update .env file
        if self._update_env_file(config):
            result["status"] = "configured"
            logger.info("Snowflake configuration updated")
        else:
            result["status"] = "error"
            result["details"]["error"] = "Failed to update configuration"
        
        return result


class GongManager(IntegrationManager):
    """Manager for Gong integration"""
    
    def __init__(self):
        super().__init__("gong")
        self.required_vars = [
            "GONG_API_KEY",
            "GONG_API_SECRET"
        ]
    
    def check(self) -> Dict[str, Any]:
        """Check Gong API connection"""
        result = {
            "name": self.name,
            "status": "unconfigured",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all required variables are set
        missing_vars = [var for var in self.required_vars if not os.getenv(var)]
        if missing_vars:
            result["details"]["missing_vars"] = missing_vars
            return result
        
        try:
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
                result["details"]["users_count"] = len(data.get("users", []))
                result["status"] = "connected"
                logger.info(f"Gong API connection successful: {result['details']['users_count']} users found")
            else:
                result["status"] = "error"
                result["details"]["error"] = f"API returned {response.status_code}: {response.text}"
                logger.error(f"Gong API connection failed: {response.status_code} {response.text}")
            
        except Exception as e:
            logger.exception("Gong API connection failed")
            result["status"] = "error"
            result["details"]["error"] = str(e)
        
        return result
    
    def rotate(self) -> Dict[str, Any]:
        """Rotate Gong credentials"""
        result = {
            "name": self.name,
            "status": "not_supported",
            "details": {
                "message": "Automatic credential rotation is not supported for Gong. Please rotate credentials manually in the Gong dashboard."
            },
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[yellow]Gong credential rotation must be done manually.[/yellow]")
        console.print("Please follow these steps:")
        console.print("1. Log in to the Gong dashboard")
        console.print("2. Navigate to Settings > Integrations > API")
        console.print("3. Generate a new API key and secret")
        console.print("4. Update the .env file with the new credentials")
        
        # Prompt for new credentials
        if Confirm.ask("Have you generated new credentials in the Gong dashboard?"):
            new_api_key = Prompt.ask("Enter the new API key")
            new_api_secret = Prompt.ask("Enter the new API secret", password=True)
            
            if new_api_key and new_api_secret:
                updates = {
                    "GONG_API_KEY": new_api_key,
                    "GONG_API_SECRET": new_api_secret
                }
                
                if self._update_env_file(updates):
                    result["status"] = "rotated"
                    result["details"]["message"] = "Credentials updated in .env file"
                    logger.info("Gong credentials updated in .env file")
                else:
                    result["status"] = "error"
                    result["details"]["message"] = "Failed to update credentials in .env file"
        
        return result
    
    def configure(self) -> Dict[str, Any]:
        """Configure Gong integration"""
        result = {
            "name": self.name,
            "status": "pending",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[bold]Configuring Gong Integration[/bold]")
        console.print("Please provide the following information:")
        
        # Collect configuration
        config = {}
        config["GONG_API_KEY"] = Prompt.ask("Gong API Key", default=os.getenv("GONG_API_KEY", ""))
        config["GONG_API_SECRET"] = Prompt.ask("Gong API Secret", password=True, default="")
        
        # Update .env file
        if self._update_env_file(config):
            result["status"] = "configured"
            logger.info("Gong configuration updated")
        else:
            result["status"] = "error"
            result["details"]["error"] = "Failed to update configuration"
        
        return result


class VercelManager(IntegrationManager):
    """Manager for Vercel integration"""
    
    def __init__(self):
        super().__init__("vercel")
        self.required_vars = [
            "VERCEL_API_TOKEN",
            "VERCEL_TEAM_ID",
            "VERCEL_PROJECT_ID"
        ]
    
    def check(self) -> Dict[str, Any]:
        """Check Vercel API connection"""
        result = {
            "name": self.name,
            "status": "unconfigured",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all required variables are set
        missing_vars = [var for var in self.required_vars if not os.getenv(var)]
        if missing_vars:
            result["details"]["missing_vars"] = missing_vars
            if "VERCEL_API_TOKEN" not in missing_vars:
                result["status"] = "partially_configured"
            return result
        
        try:
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
                result["details"]["user"] = data.get("user", {}).get("username")
                result["details"]["email"] = data.get("user", {}).get("email")
                
                # If team ID is provided, get team info
                if os.getenv("VERCEL_TEAM_ID"):
                    team_response = requests.get(
                        f"https://api.vercel.com/v2/teams/{os.getenv('VERCEL_TEAM_ID')}",
                        headers=headers
                    )
                    
                    if team_response.status_code == 200:
                        team_data = team_response.json()
                        result["details"]["team"] = team_data.get("name")
                    else:
                        result["details"]["team_error"] = f"API returned {team_response.status_code}: {team_response.text}"
                
                result["status"] = "connected"
                logger.info(f"Vercel API connection successful: {result['details']['user']}")
            else:
                result["status"] = "error"
                result["details"]["error"] = f"API returned {response.status_code}: {response.text}"
                logger.error(f"Vercel API connection failed: {response.status_code} {response.text}")
            
        except Exception as e:
            logger.exception("Vercel API connection failed")
            result["status"] = "error"
            result["details"]["error"] = str(e)
        
        return result
    
    def rotate(self) -> Dict[str, Any]:
        """Rotate Vercel credentials"""
        result = {
            "name": self.name,
            "status": "not_supported",
            "details": {
                "message": "Automatic credential rotation is not supported for Vercel. Please rotate credentials manually in the Vercel dashboard."
            },
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[yellow]Vercel credential rotation must be done manually.[/yellow]")
        console.print("Please follow these steps:")
        console.print("1. Log in to the Vercel dashboard")
        console.print("2. Navigate to Settings > Tokens")
        console.print("3. Generate a new token")
        console.print("4. Update the .env file with the new token")
        
        # Prompt for new token
        if Confirm.ask("Have you generated a new token in the Vercel dashboard?"):
            new_token = Prompt.ask("Enter the new API token", password=True)
            
            if new_token:
                if self._update_env_file({"VERCEL_API_TOKEN": new_token}):
                    result["status"] = "rotated"
                    result["details"]["message"] = "Token updated in .env file"
                    logger.info("Vercel token updated in .env file")
                else:
                    result["status"] = "error"
                    result["details"]["message"] = "Failed to update token in .env file"
        
        return result
    
    def configure(self) -> Dict[str, Any]:
        """Configure Vercel integration"""
        result = {
            "name": self.name,
            "status": "pending",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[bold]Configuring Vercel Integration[/bold]")
        console.print("Please provide the following information:")
        
        # Collect configuration
        config = {}
        config["VERCEL_API_TOKEN"] = Prompt.ask("Vercel API Token", password=True, default="")
        config["VERCEL_TEAM_ID"] = Prompt.ask("Vercel Team ID", default=os.getenv("VERCEL_TEAM_ID", ""))
        config["VERCEL_PROJECT_ID"] = Prompt.ask("Vercel Project ID", default=os.getenv("VERCEL_PROJECT_ID", ""))
        
        # Update .env file
        if self._update_env_file(config):
            result["status"] = "configured"
            logger.info("Vercel configuration updated")
        else:
            result["status"] = "error"
            result["details"]["error"] = "Failed to update configuration"
        
        return result


class EstuaryManager(IntegrationManager):
    """Manager for Estuary integration"""
    
    def __init__(self):
        super().__init__("estuary")
        self.required_vars = [
            "ESTUARY_API_KEY",
            "ESTUARY_API_URL"
        ]
    
    def check(self) -> Dict[str, Any]:
        """Check Estuary API connection"""
        result = {
            "name": self.name,
            "status": "unconfigured",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all required variables are set
        missing_vars = [var for var in self.required_vars if not os.getenv(var)]
        if missing_vars:
            result["details"]["missing_vars"] = missing_vars
            if "ESTUARY_API_KEY" not in missing_vars:
                result["status"] = "partially_configured"
            return result
        
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {os.getenv('ESTUARY_API_KEY')}",
                "Accept": "application/json"
            }
            
            # Test API connection (get collections)
            api_url = os.getenv("ESTUARY_API_URL", "https://api.estuary.tech")
            response = requests.get(
                f"{api_url}/v1/collections",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                result["details"]["total_size"] = data.get("totalSize", 0)
                result["details"]["total_files"] = data.get("totalFiles", 0)
                
                result["status"] = "connected"
                logger.info(f"Estuary API connection successful: {result['details']['total_files']} files")
            else:
                result["status"] = "error"
                result["details"]["error"] = f"API returned {response.status_code}: {response.text}"
                logger.error(f"Estuary API connection failed: {response.status_code} {response.text}")
            
        except Exception as e:
            logger.exception("Estuary API connection failed")
            result["status"] = "error"
            result["details"]["error"] = str(e)
        
        return result
    
    def rotate(self) -> Dict[str, Any]:
        """Rotate Estuary credentials"""
        result = {
            "name": self.name,
            "status": "not_supported",
            "details": {
                "message": "Automatic credential rotation is not supported for Estuary. Please rotate credentials manually in the Estuary dashboard."
            },
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[yellow]Estuary credential rotation must be done manually.[/yellow]")
        console.print("Please follow these steps:")
        console.print("1. Log in to the Estuary dashboard")
        console.print("2. Navigate to API Keys")
        console.print("3. Generate a new API key")
        console.print("4. Update the .env file with the new key")
        
        # Prompt for new key
        if Confirm.ask("Have you generated a new API key in the Estuary dashboard?"):
            new_key = Prompt.ask("Enter the new API key", password=True)
            
            if new_key:
                if self._update_env_file({"ESTUARY_API_KEY": new_key}):
                    result["status"] = "rotated"
                    result["details"]["message"] = "API key updated in .env file"
                    logger.info("Estuary API key updated in .env file")
                else:
                    result["status"] = "error"
                    result["details"]["message"] = "Failed to update API key in .env file"
        
        return result
    
    def configure(self) -> Dict[str, Any]:
        """Configure Estuary integration"""
        result = {
            "name": self.name,
            "status": "pending",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[bold]Configuring Estuary Integration[/bold]")
        console.print("Please provide the following information:")
        
        # Collect configuration
        config = {}
        config["ESTUARY_API_KEY"] = Prompt.ask("Estuary API Key", password=True, default="")
        config["ESTUARY_API_URL"] = Prompt.ask("Estuary API URL", default=os.getenv("ESTUARY_API_URL", "https://api.estuary.tech"))
        
        # Update .env file
        if self._update_env_file(config):
            result["status"] = "configured"
            logger.info("Estuary configuration updated")
        else:
            result["status"] = "error"
            result["details"]["error"] = "Failed to update configuration"
        
        return result


class MCPManager(IntegrationManager):
    """Manager for MCP integration"""
    
    def __init__(self):
        super().__init__("mcp")
        self.required_vars = [
            "MCP_CONFIG_PATH"
        ]
    
    def check(self) -> Dict[str, Any]:
        """Check MCP configuration"""
        result = {
            "name": self.name,
            "status": "unconfigured",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all required variables are set
        missing_vars = [var for var in self.required_vars if not os.getenv(var)]
        if missing_vars:
            result["details"]["missing_vars"] = missing_vars
            return result
        
        try:
            # Check if config file exists
            config_path = os.getenv("MCP_CONFIG_PATH", "mcp_config.json")
            if not os.path.exists(config_path):
                result["status"] = "error"
                result["details"]["error"] = f"Config file not found: {config_path}"
                logger.error(f"MCP config file not found: {config_path}")
                return result
            
            # Load config file
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Check if config is valid
            if not isinstance(config, dict):
                result["status"] = "error"
                result["details"]["error"] = "Config is not a valid JSON object"
                logger.error("MCP config is not a valid JSON object")
                return result
            
            # Check if servers are defined
            if "servers" not in config:
                result["status"] = "error"
                result["details"]["error"] = "Config does not contain servers"
                logger.error("MCP config does not contain servers")
                return result
            
            # Count servers
            servers = config.get("servers", [])
            result["details"]["servers_count"] = len(servers)
            
            # Get server names
            server_names = [server.get("name", "unnamed") for server in servers]
            result["details"]["servers"] = server_names
            
            result["status"] = "configured"
            logger.info(f"MCP config loaded successfully: {len(servers)} servers")
            
        except Exception as e:
            logger.exception("MCP config loading failed")
            result["status"] = "error"
            result["details"]["error"] = str(e)
        
        return result
    
    def rotate(self) -> Dict[str, Any]:
        """Rotate MCP credentials"""
        result = {
            "name": self.name,
            "status": "not_supported",
            "details": {
                "message": "Credential rotation is not applicable for MCP configuration."
            },
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[yellow]MCP credential rotation is not applicable.[/yellow]")
        console.print("MCP configuration does not contain credentials that need rotation.")
        
        return result
    
    def configure(self) -> Dict[str, Any]:
        """Configure MCP integration"""
        result = {
            "name": self.name,
            "status": "pending",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[bold]Configuring MCP Integration[/bold]")
        console.print("Please provide the following information:")
        
        # Collect configuration
        config = {}
        config["MCP_CONFIG_PATH"] = Prompt.ask("MCP Config Path", default=os.getenv("MCP_CONFIG_PATH", "mcp_config.json"))
        
        # Check if config file exists
        if not os.path.exists(config["MCP_CONFIG_PATH"]):
            # Create a basic config file
            if Confirm.ask(f"Config file {config['MCP_CONFIG_PATH']} does not exist. Create it?"):
                try:
                    with open(config["MCP_CONFIG_PATH"], "w") as f:
                        json.dump({
                            "servers": []
                        }, f, indent=2)
                    logger.info(f"Created MCP config file: {config['MCP_CONFIG_PATH']}")
                except Exception as e:
                    logger.exception(f"Failed to create MCP config file: {e}")
                    result["status"] = "error"
                    result["details"]["error"] = f"Failed to create config file: {str(e)}"
                    return result
        
        # Update .env file
        if self._update_env_file(config):
            result["status"] = "configured"
            logger.info("MCP configuration updated")
        else:
            result["status"] = "error"
            result["details"]["error"] = "Failed to update configuration"
        
        return result


def check_all_integrations() -> Dict[str, Any]:
    """Check all integrations"""
    managers = [
        SnowflakeManager(),
        GongManager(),
        VercelManager(),
        EstuaryManager(),
        MCPManager()
    ]
    
    results = {}
    for manager in managers:
        results[manager.name] = manager.check()
    
    return results


def display_check_results(results: Dict[str, Any]) -> None:
    """Display check results in a table"""
    table = Table(title="Integration Status")
    table.add_column("Integration", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    for name, result in results.items():
        status = result["status"]
        status_style = {
            "connected": "green",
            "configured": "green",
            "partially_configured": "yellow",
            "unconfigured": "red",
            "error": "red"
        }.get(status, "white")
        
        details = []
        if "error" in result["details"]:
            details.append(f"[red]Error: {result['details']['error']}[/red]")
        
        if status == "connected":
            if name == "snowflake":
                details.append(f"Version: {result['details'].get('version', 'N/A')}")
                details.append(f"Warehouse: {result['details'].get('warehouse', 'N/A')}")
            elif name == "gong":
                details.append(f"Users: {result['details'].get('users_count', 'N/A')}")
            elif name == "vercel":
                details.append(f"User: {result['details'].get('user', 'N/A')}")
                details.append(f"Team: {result['details'].get('team', 'N/A')}")
            elif name == "estuary":
                details.append(f"Files: {result['details'].get('total_files', 'N/A')}")
            elif name == "mcp":
                details.append(f"Servers: {result['details'].get('servers_count', 'N/A')}")
        
        if "missing_vars" in result["details"]:
            details.append(f"[yellow]Missing: {', '.join(result['details']['missing_vars'])}[/yellow]")
        
        table.add_row(
            name,
            f"[{status_style}]{status.upper()}[/{status_style}]",
            "\n".join(details) if details else ""
        )
    
    console.print(table)


def save_results_to_file(results: Dict[str, Any], output_file: str) -> None:
    """Save results to a JSON file"""
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.exception(f"Failed to save results to {output_file}: {e}")


def get_manager(service: str) -> Optional[IntegrationManager]:
    """Get the appropriate manager for a service"""
    managers = {
        "snowflake": SnowflakeManager,
        "gong": GongManager,
        "vercel": VercelManager,
        "estuary": EstuaryManager,
        "mcp": MCPManager
    }
    
    if service in managers:
        return managers[service]()
    
    return None


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Manage Sophia AI integrations")
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["check", "rotate", "configure"],
        help="Action to perform"
    )
    parser.add_argument(
        "--service",
        type=str,
        default="all",
        help="Service to manage (snowflake, gong, vercel, estuary, mcp, all)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results (JSON format)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Print header
    console.print("[bold blue]=======================================[/bold blue]")
    console.print("[bold blue]   Sophia AI Integration Management    [/bold blue]")
    console.print("[bold blue]=======================================[/bold blue]")
    console.print("")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        console.print("[yellow]No .env file found. Creating from template...[/yellow]")
        if os.path.exists("integration.env.example"):
            try:
                with open("integration.env.example", "r") as src, open(".env", "w") as dst:
                    dst.write(src.read())
                console.print("[green]Created .env file from template.[/green]")
                console.print("[yellow]Please edit .env file to add your credentials.[/yellow]")
                dotenv.load_dotenv()
            except Exception as e:
                console.print(f"[red]Error creating .env file: {e}[/red]")
                return 1
        else:
            console.print("[red]Error: integration.env.example file not found.[/red]")
            return 1
    
    # Perform action
    if args.action == "check":
        console.print(f"[blue]Checking {'all' if args.service == 'all' else args.service} integration(s)...[/blue]")
        
        if args.service == "all":
            results = check_all_integrations()
            display_check_results(results)
            
            if args.output:
                save_results_to_file(results, args.output)
        else:
            manager = get_manager(args.service)
            if manager:
                result = manager.check()
                display_check_results({args.service: result})
                
                if args.output:
                    save_results_to_file({args.service: result}, args.output)
            else:
                console.print(f"[red]Unknown service: {args.service}[/red]")
                return 1
    
    elif args.action == "rotate":
        if args.service == "all":
            console.print("[yellow]Rotating credentials for all services is not recommended.[/yellow]")
            console.print("Please rotate credentials for each service individually.")
            return 1
        
        console.print(f"[blue]Rotating credentials for {args.service}...[/blue]")
        
        manager = get_manager(args.service)
        if manager:
            result = manager.rotate()
            
            if result["status"] == "rotated":
                console.print(f"[green]Credentials for {args.service} rotated successfully.[/green]")
            elif result["status"] == "not_supported":
                console.print(f"[yellow]Automatic credential rotation not supported for {args.service}.[/yellow]")
            else:
                console.print(f"[red]Failed to rotate credentials for {args.service}: {result['details'].get('message', 'Unknown error')}[/red]")
            
            if args.output:
                save_results_to_file({args.service: result}, args.output)
        else:
            console.print(f"[red]Unknown service: {args.service}[/red]")
            return 1
    
    elif args.action == "configure":
        if args.service == "all":
            console.print("[yellow]Configuring all services at once is not supported.[/yellow]")
            console.print("Please configure each service individually.")
            return 1
        
        console.print(f"[blue]Configuring {args.service}...[/blue]")
        
        manager = get_manager(args.service)
        if manager:
            result = manager.configure()
            
            if result["status"] == "configured":
                console.print(f"[green]{args.service} configured successfully.[/green]")
            else:
                console.print(f"[red]Failed to configure {args.service}: {result['details'].get('error', 'Unknown error')}[/red]")
            
            if args.output:
                save_results_to_file({args.service: result}, args.output)
        else:
            console.print(f"[red]Unknown service: {args.service}[/red]")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
