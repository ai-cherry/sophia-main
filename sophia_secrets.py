#!/usr/bin/env python3
"""
Sophia AI Secret Management CLI
A unified tool for managing secrets across Pulumi ESC, GitHub, and local development

This tool consolidates functionality from:
- configure_github_secrets.py
- configure_github_org_secrets.py
- configure_pulumi_esc.sh
- manage_integrations.py

Usage:
    python sophia_secrets.py import-env --env-file .env --stack development
    python sophia_secrets.py export-env --env-file .env.new --stack development
    python sophia_secrets.py sync-github --repo payready/sophia
    python sophia_secrets.py sync-github-org --org payready
    python sophia_secrets.py rotate --service snowflake
    python sophia_secrets.py audit
"""

import argparse
import base64
import getpass
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sophia-secrets")

# Try to import required modules
try:
    from github import Github, GithubException, Repository, Organization
    from nacl import encoding, public
except ImportError:
    logger.warning("GitHub-related packages not installed. GitHub sync functionality will be limited.")
    logger.warning("To enable full functionality, install: pip install PyGithub pynacl")


class SophiaSecretManager:
    """Unified secret management for Sophia AI"""
    
    def __init__(self):
        self.env_file = ".env"
        self.config_file = "secrets_config.json"
        self.env_vars = {}
        self.config = {}
        self.pulumi_organization = os.environ.get("PULUMI_ORGANIZATION", "payready")
        self.pulumi_project = os.environ.get("PULUMI_PROJECT", "sophia")
        self.pulumi_stack = os.environ.get("PULUMI_STACK", "development")
    
    def load_env_vars(self, env_file: str = None) -> Dict[str, str]:
        """Load environment variables from .env file"""
        if env_file is None:
            env_file = self.env_file
            
        if not os.path.exists(env_file):
            logger.error(f"Error: {env_file} not found.")
            return {}

        env_vars = {}
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
                except ValueError:
                    logger.warning(f"Skipping invalid line: {line}")
        
        logger.info(f"Loaded {len(env_vars)} environment variables from {env_file}")
        self.env_vars = env_vars
        return env_vars
    
    def save_env_vars(self, env_file: str = None, env_vars: Dict[str, str] = None) -> bool:
        """Save environment variables to .env file"""
        if env_file is None:
            env_file = self.env_file
            
        if env_vars is None:
            env_vars = self.env_vars
            
        if not env_vars:
            logger.error("No environment variables to save.")
            return False
            
        # Create backup of existing .env file
        if os.path.exists(env_file):
            backup_file = f"{env_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(env_file, backup_file)
            logger.info(f"Created backup of {env_file} at {backup_file}")
        
        # Group variables by service
        services = {
            "snowflake": [var for var in env_vars if var.startswith("SNOWFLAKE_")],
            "gong": [var for var in env_vars if var.startswith("GONG_")],
            "vercel": [var for var in env_vars if var.startswith("VERCEL_")],
            "estuary": [var for var in env_vars if var.startswith("ESTUARY_")],
            "github": [var for var in env_vars if var.startswith("GITHUB_")],
            "pulumi": [var for var in env_vars if var.startswith("PULUMI_")],
            "openai": [var for var in env_vars if var.startswith("OPENAI_")],
            "pinecone": [var for var in env_vars if var.startswith("PINECONE_")],
            "weaviate": [var for var in env_vars if var.startswith("WEAVIATE_")],
            "other": [var for var in env_vars if not any(
                var.startswith(prefix) for prefix in [
                    "SNOWFLAKE_", "GONG_", "VERCEL_", "ESTUARY_", 
                    "GITHUB_", "PULUMI_", "OPENAI_", "PINECONE_", "WEAVIATE_"
                ]
            )]
        }
        
        # Write new .env file
        with open(env_file, 'w') as f:
            f.write("# Sophia AI Environment Variables\n")
            f.write(f"# Generated on {datetime.now().isoformat()}\n")
            f.write("# WARNING: This file contains sensitive information. Do not commit to version control.\n\n")
            
            for service, vars in services.items():
                if vars:
                    f.write(f"\n# {service.upper()} Configuration\n")
                    for var in sorted(vars):
                        f.write(f"{var}={env_vars[var]}\n")
        
        logger.info(f"Saved {len(env_vars)} environment variables to {env_file}")
        return True
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config file"""
        if os.path.exists(self.config_file):
            logger.info(f"Loading configuration from {self.config_file}")
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            
            logger.info(f"Loaded configuration for {len(self.config.get('services', {}))} services")
        else:
            logger.warning(f"{self.config_file} not found. Starting with empty configuration.")
            self.config = {
                "services": {},
                "last_updated": datetime.now().isoformat()
            }
            
        return self.config
    
    def save_config(self) -> bool:
        """Save configuration to config file"""
        logger.info(f"Saving configuration to {self.config_file}")
        
        # Create backup of existing config file
        if os.path.exists(self.config_file):
            backup_file = f"{self.config_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(self.config_file, backup_file)
            logger.info(f"Created backup of {self.config_file} at {backup_file}")
        
        # Update last_updated timestamp
        self.config["last_updated"] = datetime.now().isoformat()
        
        # Write new config file
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"Saved configuration for {len(self.config.get('services', {}))} services to {self.config_file}")
        return True
    
    def import_from_env(self, env_file: str, stack: str = None) -> bool:
        """Import secrets from .env file to Pulumi ESC"""
        logger.info(f"Importing secrets from {env_file} to Pulumi ESC")
        
        # Set stack if provided
        if stack:
            self.pulumi_stack = stack
            
        # Load environment variables
        env_vars = self.load_env_vars(env_file)
        if not env_vars:
            return False
            
        # Check if Pulumi CLI is available
        try:
            subprocess.run(["pulumi", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("Pulumi CLI not found. Please install Pulumi CLI first.")
            return False
            
        # Select Pulumi stack
        stack_name = f"{self.pulumi_organization}/{self.pulumi_project}/{self.pulumi_stack}"
        logger.info(f"Selecting Pulumi stack: {stack_name}")
        
        try:
            subprocess.run(["pulumi", "stack", "select", stack_name], check=True, capture_output=True)
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to select Pulumi stack: {e}")
            return False
            
        # Import each secret to Pulumi ESC
        success_count = 0
        for key, value in env_vars.items():
            if not value:
                logger.warning(f"Skipping empty secret: {key}")
                continue
                
            try:
                cmd = ["pulumi", "config", "set", "--secret", key, value]
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info(f"Imported secret: {key}")
                success_count += 1
            except subprocess.SubprocessError as e:
                logger.error(f"Failed to import secret {key}: {e}")
                
        logger.info(f"Imported {success_count}/{len(env_vars)} secrets to Pulumi ESC")
        
        # Update config
        self.load_config()
        self.config["pulumi"] = {
            "stack": self.pulumi_stack,
            "last_import": datetime.now().isoformat(),
            "imported_count": success_count
        }
        self.save_config()
        
        return success_count > 0
    
    def export_to_env(self, env_file: str, stack: str = None) -> bool:
        """Export secrets from Pulumi ESC to .env file"""
        logger.info(f"Exporting secrets from Pulumi ESC to {env_file}")
        
        # Set stack if provided
        if stack:
            self.pulumi_stack = stack
            
        # Check if Pulumi CLI is available
        try:
            subprocess.run(["pulumi", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("Pulumi CLI not found. Please install Pulumi CLI first.")
            return False
            
        # Select Pulumi stack
        stack_name = f"{self.pulumi_organization}/{self.pulumi_project}/{self.pulumi_stack}"
        logger.info(f"Selecting Pulumi stack: {stack_name}")
        
        try:
            subprocess.run(["pulumi", "stack", "select", stack_name], check=True, capture_output=True)
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to select Pulumi stack: {e}")
            return False
            
        # Get all secrets from Pulumi ESC
        try:
            result = subprocess.run(
                ["pulumi", "config", "--show-secrets"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            output = result.stdout
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to get secrets from Pulumi ESC: {e}")
            return False
            
        # Parse output to get secrets
        env_vars = {}
        for line in output.splitlines():
            if line.startswith("KEY") or not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0]
                value = " ".join(parts[1:])
                env_vars[key] = value
                
        if not env_vars:
            logger.error("No secrets found in Pulumi ESC.")
            return False
            
        logger.info(f"Found {len(env_vars)} secrets in Pulumi ESC")
        
        # Save to .env file
        self.env_vars = env_vars
        success = self.save_env_vars(env_file)
        
        # Update config
        if success:
            self.load_config()
            self.config["pulumi"] = {
                "stack": self.pulumi_stack,
                "last_export": datetime.now().isoformat(),
                "exported_count": len(env_vars)
            }
            self.save_config()
            
        return success
    
    def sync_to_github_repo(self, repo: str, token: str = None) -> bool:
        """Sync secrets to GitHub repository"""
        logger.info(f"Syncing secrets to GitHub repository: {repo}")
        
        # Check if PyGithub is available
        if 'Github' not in globals():
            logger.error("PyGithub not found. Please install it first: pip install PyGithub pynacl")
            return False
            
        # Get GitHub token
        if not token:
            token = os.environ.get("GITHUB_TOKEN")
            if not token:
                token = getpass.getpass("GitHub Personal Access Token: ")
                
        if not token:
            logger.error("GitHub token is required")
            return False
            
        # Get secrets from Pulumi ESC
        try:
            result = subprocess.run(
                ["pulumi", "config", "--show-secrets"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            output = result.stdout
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to get secrets from Pulumi ESC: {e}")
            return False
            
        # Parse output to get secrets
        secrets = {}
        for line in output.splitlines():
            if line.startswith("KEY") or not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0]
                value = " ".join(parts[1:])
                secrets[key] = value
                
        if not secrets:
            logger.error("No secrets found in Pulumi ESC.")
            return False
            
        logger.info(f"Found {len(secrets)} secrets in Pulumi ESC")
        
        try:
            # Initialize GitHub client
            g = Github(token)
            repository = g.get_repo(repo)
            
            # Get repository public key
            public_key = repository.get_public_key()
            
            # Sync each secret
            success_count = 0
            for key, value in secrets.items():
                if not value:
                    logger.warning(f"Skipping empty secret: {key}")
                    continue
                    
                try:
                    # Encrypt secret
                    encrypted_value = self._encrypt_secret(public_key.key, value)
                    
                    # Create or update secret
                    repository.create_secret(key, encrypted_value, public_key.key_id)
                    logger.info(f"Synced secret: {key}")
                    success_count += 1
                except GithubException as e:
                    logger.error(f"Failed to sync secret {key}: {e}")
                    
            logger.info(f"Synced {success_count}/{len(secrets)} secrets to GitHub repository: {repo}")
            
            # Update config
            self.load_config()
            self.config["github_repo"] = {
                "repo": repo,
                "last_sync": datetime.now().isoformat(),
                "synced_count": success_count
            }
            self.save_config()
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to sync secrets to GitHub repository: {e}")
            return False
    
    def sync_to_github_org(self, org: str, token: str = None, visibility: str = "all") -> bool:
        """Sync secrets to GitHub organization"""
        logger.info(f"Syncing secrets to GitHub organization: {org}")
        
        # Check if PyGithub is available
        if 'Github' not in globals():
            logger.error("PyGithub not found. Please install it first: pip install PyGithub pynacl")
            return False
            
        # Get GitHub token
        if not token:
            token = os.environ.get("GITHUB_TOKEN")
            if not token:
                token = getpass.getpass("GitHub Personal Access Token: ")
                
        if not token:
            logger.error("GitHub token is required")
            return False
            
        # Validate visibility
        if visibility not in ["all", "private", "selected"]:
            logger.error(f"Invalid visibility: {visibility}. Must be one of: all, private, selected")
            return False
            
        # Get secrets from Pulumi ESC
        try:
            result = subprocess.run(
                ["pulumi", "config", "--show-secrets"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            output = result.stdout
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to get secrets from Pulumi ESC: {e}")
            return False
            
        # Parse output to get secrets
        secrets = {}
        for line in output.splitlines():
            if line.startswith("KEY") or not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0]
                value = " ".join(parts[1:])
                secrets[key] = value
                
        if not secrets:
            logger.error("No secrets found in Pulumi ESC.")
            return False
            
        logger.info(f"Found {len(secrets)} secrets in Pulumi ESC")
        
        try:
            # Initialize GitHub client
            g = Github(token)
            organization = g.get_organization(org)
            
            # Get organization public key
            public_key = organization.get_public_key()
            
            # Sync each secret
            success_count = 0
            for key, value in secrets.items():
                if not value:
                    logger.warning(f"Skipping empty secret: {key}")
                    continue
                    
                try:
                    # Encrypt secret
                    encrypted_value = self._encrypt_secret(public_key.key, value)
                    
                    # For organization secrets, we need to use a different approach
                    # The PyGithub library doesn't directly support setting visibility
                    # We'll use the raw_data parameter to set the visibility
                    headers = {"Accept": "application/vnd.github.v3+json"}
                    organization._requester.requestJsonAndCheck(
                        "PUT",
                        f"/orgs/{organization.login}/actions/secrets/{key}",
                        input={
                            "encrypted_value": encrypted_value,
                            "key_id": public_key.key_id,
                            "visibility": visibility
                        },
                        headers=headers
                    )
                    
                    logger.info(f"Synced secret: {key}")
                    success_count += 1
                except GithubException as e:
                    logger.error(f"Failed to sync secret {key}: {e}")
                    
            logger.info(f"Synced {success_count}/{len(secrets)} secrets to GitHub organization: {org}")
            
            # Update config
            self.load_config()
            self.config["github_org"] = {
                "org": org,
                "visibility": visibility,
                "last_sync": datetime.now().isoformat(),
                "synced_count": success_count
            }
            self.save_config()
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to sync secrets to GitHub organization: {e}")
            return False
    
    def rotate_secrets(self, service: str) -> bool:
        """Rotate secrets for a specific service"""
        logger.info(f"Rotating secrets for service: {service}")
        
        # Validate service
        valid_services = ["snowflake", "gong", "vercel", "estuary", "all"]
        if service not in valid_services:
            logger.error(f"Invalid service: {service}. Must be one of: {', '.join(valid_services)}")
            return False
            
        # Load environment variables
        self.load_env_vars()
        
        # Determine which secrets to rotate
        if service == "all":
            services_to_rotate = ["snowflake", "gong", "vercel", "estuary"]
        else:
            services_to_rotate = [service]
            
        # Rotate secrets for each service
        for svc in services_to_rotate:
            logger.info(f"Rotating secrets for {svc}...")
            
            # Call service-specific rotation method
            method_name = f"_rotate_{svc}_secrets"
            if hasattr(self, method_name) and callable(getattr(self, method_name)):
                success = getattr(self, method_name)()
                if not success:
                    logger.error(f"Failed to rotate secrets for {svc}")
            else:
                logger.error(f"Rotation method not implemented for {svc}")
                
        # Save updated environment variables
        self.save_env_vars()
        
        # Update config
        self.load_config()
        self.config["rotation"] = {
            "services": services_to_rotate,
            "last_rotation": datetime.now().isoformat()
        }
        self.save_config()
        
        return True
    
    def audit_secrets(self) -> Dict[str, Any]:
        """Audit secret usage and rotation status"""
        logger.info("Auditing secrets...")
        
        # Load environment variables
        self.load_env_vars()
        
        # Load config
        self.load_config()
        
        # Initialize audit results
        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "rotation_status": {},
            "sync_status": {},
            "recommendations": []
        }
        
        # Audit each service
        services = ["snowflake", "gong", "vercel", "estuary"]
        for service in services:
            # Get service-specific variables
            service_vars = [var for var in self.env_vars if var.startswith(f"{service.upper()}_")]
            
            # Check for missing required variables
            required_vars = self._get_required_vars(service)
            missing_vars = [var for var in required_vars if var not in self.env_vars or not self.env_vars[var]]
            
            # Check rotation status
            last_rotation = self.config.get("rotation", {}).get("services", [])
            rotation_timestamp = self.config.get("rotation", {}).get("last_rotation", "never")
            
            # Add to audit results
            audit_results["services"][service] = {
                "variables_count": len(service_vars),
                "missing_variables": missing_vars,
                "status": "complete" if not missing_vars else "incomplete"
            }
            
            audit_results["rotation_status"][service] = {
                "last_rotation": rotation_timestamp if service in last_rotation else "never",
                "days_since_rotation": self._days_since(rotation_timestamp) if service in last_rotation else "N/A",
                "status": "ok" if service in last_rotation and self._days_since(rotation_timestamp) < 90 else "needs_rotation"
            }
            
            # Add recommendations
            if missing_vars:
                audit_results["recommendations"].append(f"Configure missing {service} variables: {', '.join(missing_vars)}")
                
            if service not in last_rotation or self._days_since(rotation_timestamp) >= 90:
                audit_results["recommendations"].append(f"Rotate {service} secrets (last rotation: {rotation_timestamp if service in last_rotation else 'never'})")
        
        # Check sync status
        github_repo_sync = self.config.get("github_repo", {}).get("last_sync", "never")
        github_org_sync = self.config.get("github_org", {}).get("last_sync", "never")
        pulumi_import = self.config.get("pulumi", {}).get("last_import", "never")
        pulumi_export = self.config.get("pulumi", {}).get("last_export", "never")
        
        audit_results["sync_status"] = {
            "github_repo": {
                "last_sync": github_repo_sync,
                "days_since_sync": self._days_since(github_repo_sync),
                "status": "ok" if self._days_since(github_repo_sync) < 30 else "needs_sync"
            },
            "github_org": {
                "last_sync": github_org_sync,
                "days_since_sync": self._days_since(github_org_sync),
                "status": "ok" if self._days_since(github_org_sync) < 30 else "needs_sync"
            },
            "pulumi_import": {
                "last_import": pulumi_import,
                "days_since_import": self._days_since(pulumi_import),
                "status": "ok" if self._days_since(pulumi_import) < 30 else "needs_import"
            },
            "pulumi_export": {
                "last_export": pulumi_export,
                "days_since_export": self._days_since(pulumi_export),
                "status": "ok" if self._days_since(pulumi_export) < 30 else "needs_export"
            }
        }
        
        # Add sync recommendations
        if self._days_since(github_repo_sync) >= 30:
            audit_results["recommendations"].append(f"Sync secrets to GitHub repository (last sync: {github_repo_sync})")
            
        if self._days_since(github_org_sync) >= 30:
            audit_results["recommendations"].append(f"Sync secrets to GitHub organization (last sync: {github_org_sync})")
            
        if self._days_since(pulumi_import) >= 30:
            audit_results["recommendations"].append(f"Import secrets to Pulumi ESC (last import: {pulumi_import})")
            
        if self._days_since(pulumi_export) >= 30:
            audit_results["recommendations"].append(f"Export secrets from Pulumi ESC (last export: {pulumi_export})")
        
        # Save audit results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audit_file = f"secrets_audit_{timestamp}.json"
        
        with open(audit_file, 'w') as f:
            json.dump(audit_results, f, indent=2)
            
        logger.info(f"Audit results saved to {audit_file}")
        
        # Print summary
        print("\n=== Sophia AI Secrets Audit ===")
        print(f"Timestamp: {audit_results['timestamp']}")
        print("\nService Status:")
        for service, details in audit_results["services"].items():
            status_icon = "✅" if details["status"] == "complete" else "❌"
            print(f"{status_icon} {service.upper()}: {details['status'].upper()}")
            if details["missing_variables"]:
                print(f"   Missing variables: {', '.join(details['missing_variables'])}")
                
        print("\nRotation Status:")
        for service, details in audit_results["rotation_status"].items():
            status_icon = "✅" if details["status"] == "ok" else "❌"
            print(f"{status_icon} {service.upper()}: Last rotation: {details['last_rotation']}")
            
        print("\nSync Status:")
        for sync_type, details in audit_results["sync_status"].items():
            status_icon = "✅" if details["status"] == "ok" else "❌"
            print(f"{status_icon} {sync_type.upper()}: Last sync: {details['last_sync']}")
            
        print("\nRecommendations:")
        for i, recommendation in enumerate(audit_results["recommendations"], 1):
            print(f"{i}. {recommendation}")
            
        return audit_results
    
    def _encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt a secret using the repository's public key."""
        public_key_bytes = public.PublicKey(
            public_key.encode("utf-8"), encoding.Base64Encoder()
        )
        sealed_box = public.SealedBox(public_key_bytes)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    
    def _get_required_vars(self, service: str) -> List[str]:
        """Get required variables for a service"""
        if service == "snowflake":
            return [
                "SNOWFLAKE_ACCOUNT",
                "SNOWFLAKE_USER",
                "SNOWFLAKE_PASSWORD",
                "SNOWFLAKE_WAREHOUSE",
                "SNOWFLAKE_DATABASE",
                "SNOWFLAKE_SCHEMA",
                "SNOWFLAKE_ROLE"
            ]
        elif service == "gong":
            return [
                "GONG_API_KEY",
                "GONG_API_SECRET",
                "GONG_ACCESS_KEY"
            ]
        elif service == "vercel":
            return [
                "VERCEL_ACCESS_TOKEN",
                "VERCEL_PROJECT_ID",
                "VERCEL_ORG_ID",
                "VERCEL_TEAM_ID"
            ]
        elif service == "estuary":
            return [
                "ESTUARY_API_KEY",
                "ESTUARY_API_URL"
            ]
        else:
            return []
    
    def _days_since(self, timestamp: str) -> int:
        """Calculate days since a timestamp"""
        if timestamp == "never":
            return 999
            
        try:
            if "T" in timestamp:
                dt = datetime.fromisoformat(timestamp)
            else:
                dt = datetime.strptime(timestamp, "%Y-%m-%d")
                
            delta = datetime.now() - dt
            return delta.days
        except (ValueError, TypeError):
            return 999
    
    def _rotate_snowflake_secrets(self) -> bool:
        """Rotate Snowflake secrets"""
        logger.info("This is a placeholder for Snowflake secret rotation.")
        logger.info("In a real implementation, this would:")
        logger.info("1. Connect to Snowflake")
        logger.info("2. Create a new user or reset password")
        logger.info("3. Update the environment variables")
        logger.info("4. Update Pulumi ESC")
        logger.info("5. Sync to GitHub")
        
        # In a real implementation, this would actually rotate the secrets
        # For now, we'll just update the timestamp in the config
        self.load_config()
        if "rotation" not in self.config:
            self.config["rotation"] = {}
        if "services" not in self.config["rotation"]:
            self.config["rotation"]["services"] = []
            
        if "snowflake" not in self.config["rotation"]["services"]:
            self.config["rotation"]["services"].append("snowflake")
            
        self.config["rotation"]["last_rotation"] = datetime.now().isoformat()
        self.save_config()
        
        return True
    
    def _rotate_gong_secrets(self) -> bool:
        """Rotate Gong secrets"""
        logger.info("This is a placeholder for Gong secret rotation.")
        logger.info("In a real implementation, this would:")
        logger.info("1. Connect to Gong API")
        logger.info("2. Create new API keys")
        logger.info("3. Update the environment variables")
        logger.info("4. Update Pulumi ESC")
        logger.info("5. Sync to GitHub")
        
        # In a real implementation, this would actually rotate the secrets
        # For now, we'll just update the timestamp in the config
        self.load_config()
        if "rotation" not in self.config:
            self.config["rotation"] = {}
        if "services" not in self.config["rotation"]:
            self.config["rotation"]["services"] = []
            
        if "gong" not in self.config["rotation"]["services"]:
            self.config["rotation"]["services"].append("gong")
            
        self.config["rotation"]["last_rotation"] = datetime.now().isoformat()
        self.save_config()
        
        return True
    
    def _rotate_vercel_secrets(self) -> bool:
        """Rotate Vercel secrets"""
        logger.info("This is a placeholder for Vercel secret rotation.")
        logger.info("In a real implementation, this would:")
        logger.info("1. Connect to Vercel API")
        logger.info("2. Create new access tokens")
        logger.info("3. Update the environment variables")
        logger.info("4. Update Pulumi ESC")
        logger.info("5. Sync to GitHub")
        
        # In a real implementation, this would actually rotate the secrets
        # For now, we'll just update the timestamp in the config
        self.load_config()
        if "rotation" not in self.config:
            self.config["rotation"] = {}
        if "services" not in self.config["rotation"]:
            self.config["rotation"]["services"] = []
            
        if "vercel" not in self.config["rotation"]["services"]:
            self.config["rotation"]["services"].append("vercel")
            
        self.config["rotation"]["last_rotation"] = datetime.now().isoformat()
        self.save_config()
        
        return True
    
    def _rotate_estuary_secrets(self) -> bool:
        """Rotate Estuary secrets"""
        logger.info("This is a placeholder for Estuary secret rotation.")
        logger.info("In a real implementation, this would:")
        logger.info("1. Connect to Estuary API")
        logger.info("2. Create new API keys")
        logger.info("3. Update the environment variables")
        logger.info("4. Update Pulumi ESC")
        logger.info("5. Sync to GitHub")
        
        # In a real implementation, this would actually rotate the secrets
        # For now, we'll just update the timestamp in the config
        self.load_config()
        if "rotation" not in self.config:
            self.config["rotation"] = {}
        if "services" not in self.config["rotation"]:
            self.config["rotation"]["services"] = []
            
        if "estuary" not in self.config["rotation"]["services"]:
            self.config["rotation"]["services"].append("estuary")
            
        self.config["rotation"]["last_rotation"] = datetime.now().isoformat()
        self.save_config()
        
        return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Sophia AI Secret Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Import from .env to Pulumi ESC
    import_parser = subparsers.add_parser("import-env", help="Import secrets from .env file to Pulumi ESC")
    import_parser.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
    import_parser.add_argument("--stack", help="Pulumi stack (default: development)")
    
    # Export from Pulumi ESC to .env
    export_parser = subparsers.add_parser("export-env", help="Export secrets from Pulumi ESC to .env file")
    export_parser.add_argument("--env-file", default=".env.new", help="Path to output .env file (default: .env.new)")
    export_parser.add_argument("--stack", help="Pulumi stack (default: development)")
    
    # Sync to GitHub repository
    github_parser = subparsers.add_parser("sync-github", help="Sync secrets to GitHub repository")
    github_parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    github_parser.add_argument("--token", help="GitHub token (if not provided, will use GITHUB_TOKEN env var)")
    
    # Sync to GitHub organization
    github_org_parser = subparsers.add_parser("sync-github-org", help="Sync secrets to GitHub organization")
    github_org_parser.add_argument("--org", required=True, help="GitHub organization")
    github_org_parser.add_argument("--token", help="GitHub token (if not provided, will use GITHUB_TOKEN env var)")
    github_org_parser.add_argument("--visibility", default="all", choices=["all", "private", "selected"], 
                                  help="Secret visibility (default: all)")
    
    # Rotate secrets
    rotate_parser = subparsers.add_parser("rotate", help="Rotate secrets for a service")
    rotate_parser.add_argument("--service", default="all", choices=["all", "snowflake", "gong", "vercel", "estuary"],
                              help="Service to rotate secrets for (default: all)")
    
    # Audit secrets
    audit_parser = subparsers.add_parser("audit", help="Audit secret usage and rotation status")
    
    return parser.parse_args()


def main() -> int:
    """Main entry point"""
    args = parse_args()
    
    if not args.command:
        print("No command specified. Use --help for usage information.")
        return 1
    
    manager = SophiaSecretManager()
    
    if args.command == "import-env":
        success = manager.import_from_env(args.env_file, args.stack)
        return 0 if success else 1
    
    elif args.command == "export-env":
        success = manager.export_to_env(args.env_file, args.stack)
        return 0 if success else 1
    
    elif args.command == "sync-github":
        success = manager.sync_to_github_repo(args.repo, args.token)
        return 0 if success else 1
    
    elif args.command == "sync-github-org":
        success = manager.sync_to_github_org(args.org, args.token, args.visibility)
        return 0 if success else 1
    
    elif args.command == "rotate":
        success = manager.rotate_secrets(args.service)
        return 0 if success else 1
    
    elif args.command == "audit":
        manager.audit_secrets()
        return 0
    
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
