#!/usr/bin/env python3
# Sophia AI - Secret Management Tool
# This script provides a unified interface for managing secrets across different environments

import os
import sys
import json
import argparse
import logging
import datetime
import subprocess
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('sophia-secrets')

class SecretManager:
    def __init__(self):
        self.env_vars = {}
        self.pulumi_stack = None
        self.github_repo = None
        self.github_org = None
    
    def load_env_file(self, env_file: str) -> Dict[str, str]:
        """Load environment variables from a .env file."""
        env_vars = {}
        
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
            
            logger.info(f"Loaded {len(env_vars)} environment variables from {env_file}")
            return env_vars
        except Exception as e:
            logger.error(f"Failed to load environment variables from {env_file}: {e}")
            return {}
    
    def save_env_file(self, env_vars: Dict[str, str], env_file: str) -> bool:
        """Save environment variables to a .env file."""
        try:
            with open(env_file, 'w') as f:
                f.write("# Sophia AI Integration Environment Variables\n")
                f.write("# IMPORTANT: This file contains sensitive credentials and should never be committed to version control\n\n")
                
                # Group variables by service
                services = {
                    "Snowflake": [k for k in env_vars if k.startswith("SNOWFLAKE_")],
                    "Gong": [k for k in env_vars if k.startswith("GONG_")],
                    "Vercel": [k for k in env_vars if k.startswith("VERCEL_")],
                    "Estuary": [k for k in env_vars if k.startswith("ESTUARY_")],
                    "GitHub": [k for k in env_vars if k.startswith("GITHUB_")],
                    "Pulumi": [k for k in env_vars if k.startswith("PULUMI_")],
                    "Other": [k for k in env_vars if not any(k.startswith(p) for p in ["SNOWFLAKE_", "GONG_", "VERCEL_", "ESTUARY_", "GITHUB_", "PULUMI_"])]
                }
                
                for service, keys in services.items():
                    if keys:
                        f.write(f"# {service} Configuration\n")
                        for key in sorted(keys):
                            f.write(f"{key}={env_vars[key]}\n")
                        f.write("\n")
            
            logger.info(f"Saved {len(env_vars)} environment variables to {env_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save environment variables to {env_file}: {e}")
            return False
    
    def import_env_to_pulumi(self, env_vars: Dict[str, str], stack: str) -> bool:
        """Import environment variables to Pulumi ESC."""
        try:
            # Check if Pulumi CLI is installed
            subprocess.run(["pulumi", "--version"], check=True, capture_output=True)
            
            # Set the stack
            subprocess.run(["pulumi", "stack", "select", stack], check=True, capture_output=True)
            
            # Import each environment variable
            for key, value in env_vars.items():
                logger.info(f"Importing {key} to Pulumi ESC")
                subprocess.run(
                    ["pulumi", "config", "set", "--secret", key, value],
                    check=True,
                    capture_output=True
                )
            
            logger.info(f"Imported {len(env_vars)} environment variables to Pulumi ESC stack {stack}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to import environment variables to Pulumi ESC: {e}")
            logger.error(f"Pulumi CLI output: {e.stdout.decode() if e.stdout else ''}")
            logger.error(f"Pulumi CLI error: {e.stderr.decode() if e.stderr else ''}")
            return False
        except Exception as e:
            logger.error(f"Failed to import environment variables to Pulumi ESC: {e}")
            return False
    
    def export_pulumi_to_env(self, stack: str) -> Dict[str, str]:
        """Export environment variables from Pulumi ESC."""
        env_vars = {}
        
        try:
            # Check if Pulumi CLI is installed
            subprocess.run(["pulumi", "--version"], check=True, capture_output=True)
            
            # Set the stack
            subprocess.run(["pulumi", "stack", "select", stack], check=True, capture_output=True)
            
            # Get all config values
            result = subprocess.run(
                ["pulumi", "config", "--json"],
                check=True,
                capture_output=True,
                text=True
            )
            
            config = json.loads(result.stdout)
            
            # Extract environment variables
            for key, value in config.items():
                if isinstance(value, dict) and "value" in value:
                    env_vars[key] = value["value"]
            
            logger.info(f"Exported {len(env_vars)} environment variables from Pulumi ESC stack {stack}")
            return env_vars
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to export environment variables from Pulumi ESC: {e}")
            logger.error(f"Pulumi CLI output: {e.stdout.decode() if e.stdout else ''}")
            logger.error(f"Pulumi CLI error: {e.stderr.decode() if e.stderr else ''}")
            return {}
        except Exception as e:
            logger.error(f"Failed to export environment variables from Pulumi ESC: {e}")
            return {}
    
    def sync_to_github_repo(self, env_vars: Dict[str, str], repo: str) -> bool:
        """Sync environment variables to GitHub repository secrets."""
        try:
            # Check if GitHub CLI is installed
            subprocess.run(["gh", "--version"], check=True, capture_output=True)
            
            # Check if authenticated
            subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
            
            # Sync each environment variable
            for key, value in env_vars.items():
                logger.info(f"Syncing {key} to GitHub repository {repo}")
                subprocess.run(
                    ["gh", "secret", "set", key, "--body", value, "--repo", repo],
                    check=True,
                    capture_output=True
                )
            
            logger.info(f"Synced {len(env_vars)} environment variables to GitHub repository {repo}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to sync environment variables to GitHub repository: {e}")
            logger.error(f"GitHub CLI output: {e.stdout.decode() if e.stdout else ''}")
            logger.error(f"GitHub CLI error: {e.stderr.decode() if e.stderr else ''}")
            return False
        except Exception as e:
            logger.error(f"Failed to sync environment variables to GitHub repository: {e}")
            return False
    
    def sync_to_github_org(self, env_vars: Dict[str, str], org: str) -> bool:
        """Sync environment variables to GitHub organization secrets."""
        try:
            # Check if GitHub CLI is installed
            subprocess.run(["gh", "--version"], check=True, capture_output=True)
            
            # Check if authenticated
            subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
            
            # Sync each environment variable
            for key, value in env_vars.items():
                logger.info(f"Syncing {key} to GitHub organization {org}")
                subprocess.run(
                    ["gh", "secret", "set", key, "--body", value, "--org", org],
                    check=True,
                    capture_output=True
                )
            
            logger.info(f"Synced {len(env_vars)} environment variables to GitHub organization {org}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to sync environment variables to GitHub organization: {e}")
            logger.error(f"GitHub CLI output: {e.stdout.decode() if e.stdout else ''}")
            logger.error(f"GitHub CLI error: {e.stderr.decode() if e.stderr else ''}")
            return False
        except Exception as e:
            logger.error(f"Failed to sync environment variables to GitHub organization: {e}")
            return False
    
    def rotate_secrets(self, service: str) -> Dict[str, str]:
        """Rotate secrets for a specific service."""
        if service.lower() == "all":
            logger.info("Rotating secrets for all services")
            services = ["snowflake", "gong", "vercel", "estuary"]
            rotated_secrets = {}
            
            for svc in services:
                rotated = self.rotate_secrets(svc)
                rotated_secrets.update(rotated)
            
            return rotated_secrets
        
        rotated_secrets = {}
        
        if service.lower() == "snowflake":
            logger.info("Rotating Snowflake secrets")
            # In a real implementation, this would call the Snowflake API to rotate credentials
            logger.warning("Snowflake secret rotation requires manual steps")
            logger.warning("Please update your Snowflake password manually and then update the SNOWFLAKE_PASSWORD environment variable")
        
        elif service.lower() == "gong":
            logger.info("Rotating Gong secrets")
            # In a real implementation, this would call the Gong API to rotate credentials
            logger.warning("Gong secret rotation requires manual steps")
            logger.warning("Please generate new API keys in the Gong dashboard and then update the GONG_API_KEY and GONG_API_SECRET environment variables")
        
        elif service.lower() == "vercel":
            logger.info("Rotating Vercel secrets")
            # In a real implementation, this would call the Vercel API to rotate credentials
            logger.warning("Vercel secret rotation requires manual steps")
            logger.warning("Please generate a new access token in the Vercel dashboard and then update the VERCEL_ACCESS_TOKEN environment variable")
        
        elif service.lower() == "estuary":
            logger.info("Rotating Estuary secrets")
            # In a real implementation, this would call the Estuary API to rotate credentials
            logger.warning("Estuary secret rotation requires manual steps")
            logger.warning("Please generate a new API key in the Estuary dashboard and then update the ESTUARY_API_KEY environment variable")
        
        else:
            logger.error(f"Unknown service: {service}")
            return {}
        
        return rotated_secrets
    
    def audit_secrets(self) -> Dict[str, Any]:
        """Audit secret usage and rotation status."""
        audit_report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "services": {},
            "recommendations": []
        }
        
        # Check for environment variables
        env_vars = os.environ
        
        # Snowflake
        snowflake_vars = {k: v for k, v in env_vars.items() if k.startswith("SNOWFLAKE_")}
        audit_report["services"]["snowflake"] = {
            "configured": len(snowflake_vars) > 0,
            "variables": list(snowflake_vars.keys()),
            "last_rotation": "unknown"
        }
        
        # Gong
        gong_vars = {k: v for k, v in env_vars.items() if k.startswith("GONG_")}
        audit_report["services"]["gong"] = {
            "configured": len(gong_vars) > 0,
            "variables": list(gong_vars.keys()),
            "last_rotation": "unknown"
        }
        
        # Vercel
        vercel_vars = {k: v for k, v in env_vars.items() if k.startswith("VERCEL_")}
        audit_report["services"]["vercel"] = {
            "configured": len(vercel_vars) > 0,
            "variables": list(vercel_vars.keys()),
            "last_rotation": "unknown"
        }
        
        # Estuary
        estuary_vars = {k: v for k, v in env_vars.items() if k.startswith("ESTUARY_")}
        audit_report["services"]["estuary"] = {
            "configured": len(estuary_vars) > 0,
            "variables": list(estuary_vars.keys()),
            "last_rotation": "unknown"
        }
        
        # Generate recommendations
        if not audit_report["services"]["snowflake"]["configured"]:
            audit_report["recommendations"].append("Configure Snowflake environment variables")
        
        if not audit_report["services"]["gong"]["configured"]:
            audit_report["recommendations"].append("Configure Gong environment variables")
        
        if not audit_report["services"]["vercel"]["configured"]:
            audit_report["recommendations"].append("Configure Vercel environment variables")
        
        if not audit_report["services"]["estuary"]["configured"]:
            audit_report["recommendations"].append("Configure Estuary environment variables")
        
        # Add general recommendations
        audit_report["recommendations"].append("Rotate all secrets every 90 days")
        audit_report["recommendations"].append("Store all secrets in Pulumi ESC")
        audit_report["recommendations"].append("Sync secrets to GitHub for CI/CD workflows")
        
        return audit_report
    
    def print_audit_report(self, audit_report: Dict[str, Any]) -> None:
        """Print a human-readable version of the audit report."""
        print("\n" + "=" * 80)
        print("SOPHIA AI SECRET AUDIT REPORT")
        print("=" * 80)
        print(f"Timestamp: {audit_report['timestamp']}")
        print()
        
        print("Service Configuration:")
        for service, config in audit_report["services"].items():
            status_icon = "✅" if config["configured"] else "❌"
            print(f"{status_icon} {service.upper()}: {'Configured' if config['configured'] else 'Not Configured'}")
            if config["configured"]:
                print(f"   Variables: {', '.join(config['variables'])}")
                print(f"   Last Rotation: {config['last_rotation']}")
        
        print("\nRecommendations:")
        for i, recommendation in enumerate(audit_report["recommendations"], 1):
            print(f"{i}. {recommendation}")
        
        print("=" * 80)

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="Sophia AI Secret Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Import environment variables from .env file to Pulumi ESC
    import_parser = subparsers.add_parser("import-env", help="Import environment variables from .env file to Pulumi ESC")
    import_parser.add_argument("--env-file", required=True, help="Path to .env file")
    import_parser.add_argument("--stack", required=True, help="Pulumi stack name")
    
    # Export environment variables from Pulumi ESC to .env file
    export_parser = subparsers.add_parser("export-env", help="Export environment variables from Pulumi ESC to .env file")
    export_parser.add_argument("--env-file", required=True, help="Path to .env file")
    export_parser.add_argument("--stack", required=True, help="Pulumi stack name")
    
    # Sync environment variables to GitHub repository
    sync_github_parser = subparsers.add_parser("sync-github", help="Sync environment variables to GitHub repository")
    sync_github_parser.add_argument("--repo", required=True, help="GitHub repository name (e.g., owner/repo)")
    sync_github_parser.add_argument("--env-file", help="Path to .env file (optional)")
    sync_github_parser.add_argument("--stack", help="Pulumi stack name (optional)")
    
    # Sync environment variables to GitHub organization
    sync_github_org_parser = subparsers.add_parser("sync-github-org", help="Sync environment variables to GitHub organization")
    sync_github_org_parser.add_argument("--org", required=True, help="GitHub organization name")
    sync_github_org_parser.add_argument("--env-file", help="Path to .env file (optional)")
    sync_github_org_parser.add_argument("--stack", help="Pulumi stack name (optional)")
    
    # Rotate secrets
    rotate_parser = subparsers.add_parser("rotate", help="Rotate secrets for a specific service")
    rotate_parser.add_argument("--service", required=True, choices=["all", "snowflake", "gong", "vercel", "estuary"], help="Service to rotate secrets for")
    
    # Audit secrets
    audit_parser = subparsers.add_parser("audit", help="Audit secret usage and rotation status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    secret_manager = SecretManager()
    
    if args.command == "import-env":
        env_vars = secret_manager.load_env_file(args.env_file)
        if env_vars:
            secret_manager.import_env_to_pulumi(env_vars, args.stack)
    
    elif args.command == "export-env":
        env_vars = secret_manager.export_pulumi_to_env(args.stack)
        if env_vars:
            secret_manager.save_env_file(env_vars, args.env_file)
    
    elif args.command == "sync-github":
        env_vars = {}
        
        if args.env_file:
            env_vars = secret_manager.load_env_file(args.env_file)
        elif args.stack:
            env_vars = secret_manager.export_pulumi_to_env(args.stack)
        else:
            logger.error("Either --env-file or --stack must be specified")
            return
        
        if env_vars:
            secret_manager.sync_to_github_repo(env_vars, args.repo)
    
    elif args.command == "sync-github-org":
        env_vars = {}
        
        if args.env_file:
            env_vars = secret_manager.load_env_file(args.env_file)
        elif args.stack:
            env_vars = secret_manager.export_pulumi_to_env(args.stack)
        else:
            logger.error("Either --env-file or --stack must be specified")
            return
        
        if env_vars:
            secret_manager.sync_to_github_org(env_vars, args.org)
    
    elif args.command == "rotate":
        rotated_secrets = secret_manager.rotate_secrets(args.service)
        if rotated_secrets:
            logger.info(f"Rotated {len(rotated_secrets)} secrets for {args.service}")
    
    elif args.command == "audit":
        audit_report = secret_manager.audit_secrets()
        secret_manager.print_audit_report(audit_report)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
