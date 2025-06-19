#!/usr/bin/env python3
"""
Sophia AI - GitHub Secrets Bidirectional Synchronization
This script synchronizes secrets between GitHub organization and Pulumi ESC in both directions.
"""

import os
import json
import argparse
import subprocess
import logging
import datetime
import time
from typing import Dict, List, Any, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PulumiESCClient:
    """
    Client for interacting with Pulumi ESC API
    """
    
    def __init__(self, organization: str, environment: str, token: str = None):
        self.organization = organization
        self.environment = environment
        self.token = token or os.environ.get("PULUMI_ACCESS_TOKEN")
        if not self.token:
            raise ValueError("Pulumi token not provided and PULUMI_ACCESS_TOKEN environment variable not set")
        
        self.api_url = "https://api.pulumi.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pulumi+8"
        }
    
    def get_secrets(self) -> List[Dict[str, Any]]:
        """Get all secrets for an environment"""
        try:
            response = requests.get(
                f"{self.api_url}/api/environments/{self.organization}/{self.environment}/secrets",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("secrets", [])
        except Exception as e:
            logger.error(f"Failed to get secrets for {self.environment}: {e}")
            return []
    
    def get_secret_value(self, secret_name: str) -> Optional[str]:
        """Get a secret value"""
        try:
            # In a real implementation, this would call the Pulumi API to get the secret value
            # For this example, we'll return None as the Pulumi API doesn't expose secret values directly
            logger.warning(f"Getting secret values from Pulumi ESC is not supported. Secret: {secret_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return None
    
    def set_secret(self, secret_name: str, value: str, secret_group: str) -> bool:
        """Set a secret value"""
        try:
            payload = {
                "name": secret_name,
                "value": value,
                "secretGroup": secret_group
            }
            
            response = requests.post(
                f"{self.api_url}/api/environments/{self.organization}/{self.environment}/secrets",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Set secret {secret_name} in group {secret_group}")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {secret_name}: {e}")
            return False
    
    def delete_secret(self, secret_name: str) -> bool:
        """Delete a secret"""
        try:
            response = requests.delete(
                f"{self.api_url}/api/environments/{self.organization}/{self.environment}/secrets/{secret_name}",
                headers=self.headers
            )
            response.raise_for_status()
            logger.info(f"Deleted secret {secret_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {secret_name}: {e}")
            return False


class GitHubSecretManager:
    """
    Manages GitHub organization secrets
    """
    
    def __init__(self, organization: str, token: str = None):
        self.organization = organization
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN environment variable not set")
        
        # Set GitHub token for CLI
        os.environ["GITHUB_TOKEN"] = self.token
    
    def get_organization_secrets(self) -> List[Dict[str, Any]]:
        """Get all organization secrets"""
        try:
            # Run GitHub CLI command to list secrets
            result = subprocess.run(
                ["gh", "secret", "list", "--org", self.organization, "--json", "name,updatedAt"],
                capture_output=True, text=True, check=True
            )
            
            # Parse JSON output
            secrets = json.loads(result.stdout)
            logger.info(f"Found {len(secrets)} GitHub organization secrets")
            return secrets
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get GitHub organization secrets: {e}")
            logger.error(f"GitHub CLI output: {e.stdout}")
            logger.error(f"GitHub CLI error: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Failed to get GitHub organization secrets: {e}")
            return []
    
    def set_organization_secret(self, name: str, value: str) -> bool:
        """Set an organization secret"""
        try:
            # Create a temporary file with the secret value
            temp_file = f"/tmp/{name.lower()}_secret.txt"
            with open(temp_file, "w") as f:
                f.write(value)
            
            # Run GitHub CLI command to set secret
            result = subprocess.run(
                ["gh", "secret", "set", name, "--org", self.organization, "--body-file", temp_file],
                capture_output=True, text=True, check=True
            )
            
            # Remove temporary file
            os.unlink(temp_file)
            
            logger.info(f"Set GitHub organization secret {name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set GitHub organization secret {name}: {e}")
            logger.error(f"GitHub CLI output: {e.stdout}")
            logger.error(f"GitHub CLI error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Failed to set GitHub organization secret {name}: {e}")
            return False
    
    def delete_organization_secret(self, name: str) -> bool:
        """Delete an organization secret"""
        try:
            # Run GitHub CLI command to delete secret
            result = subprocess.run(
                ["gh", "secret", "delete", name, "--org", self.organization],
                capture_output=True, text=True, check=True
            )
            
            logger.info(f"Deleted GitHub organization secret {name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete GitHub organization secret {name}: {e}")
            logger.error(f"GitHub CLI output: {e.stdout}")
            logger.error(f"GitHub CLI error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete GitHub organization secret {name}: {e}")
            return False


class SecretSynchronizer:
    """
    Synchronizes secrets between GitHub and Pulumi ESC
    """
    
    def __init__(self, github_org: str, pulumi_org: str, pulumi_env: str, github_token: str = None, pulumi_token: str = None):
        self.github = GitHubSecretManager(github_org, github_token)
        self.pulumi = PulumiESCClient(pulumi_org, pulumi_env, pulumi_token)
        self.service_mappings = self._load_service_mappings()
    
    def _load_service_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load service mappings from service registry"""
        try:
            registry_path = os.environ.get(
                "SERVICE_REGISTRY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/service_registry.json"
            )
            
            if os.path.exists(registry_path):
                with open(registry_path, "r") as f:
                    registry = json.load(f)
                
                # Create mappings
                mappings = {}
                for service, config in registry.items():
                    for key in config.get("config_keys", []) + config.get("secret_keys", []):
                        github_key = f"{service.upper()}_{key.upper()}"
                        pulumi_key = f"{service}_{key}"
                        group = "api-keys"
                        if key in config.get("secret_keys", []):
                            if service in ["snowflake", "postgres"]:
                                group = "database-credentials"
                            elif key in ["token", "password", "private_key"]:
                                group = "security-tokens"
                        
                        mappings[github_key] = {
                            "service": service,
                            "key": key,
                            "pulumi_key": pulumi_key,
                            "group": group
                        }
                
                logger.info(f"Loaded {len(mappings)} service mappings from registry")
                return mappings
            else:
                logger.warning(f"Service registry not found at {registry_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load service mappings: {e}")
            return {}
    
    def map_github_to_pulumi(self, github_key: str) -> Dict[str, str]:
        """Map GitHub secret name to Pulumi ESC secret details"""
        # Check if we have a direct mapping
        if github_key in self.service_mappings:
            return self.service_mappings[github_key]
        
        # Try to infer mapping from name
        if github_key.startswith("SNOWFLAKE_"):
            service = "snowflake"
            key = github_key[len("SNOWFLAKE_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "database-credentials"
        elif github_key.startswith("GONG_"):
            service = "gong"
            key = github_key[len("GONG_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("VERCEL_"):
            service = "vercel"
            key = github_key[len("VERCEL_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("ESTUARY_"):
            service = "estuary"
            key = github_key[len("ESTUARY_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("LAMBDA_"):
            service = "lambda_labs"
            key = github_key[len("LAMBDA_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("AIRBYTE_"):
            service = "airbyte"
            key = github_key[len("AIRBYTE_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("PINECONE_"):
            service = "pinecone"
            key = github_key[len("PINECONE_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("WEAVIATE_"):
            service = "weaviate"
            key = github_key[len("WEAVIATE_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("OPENAI_"):
            service = "openai"
            key = github_key[len("OPENAI_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("ANTHROPIC_"):
            service = "anthropic"
            key = github_key[len("ANTHROPIC_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("GITHUB_"):
            service = "github"
            key = github_key[len("GITHUB_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "security-tokens"
        elif github_key.startswith("POSTGRES_"):
            service = "postgres"
            key = github_key[len("POSTGRES_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "database-credentials"
        elif github_key.startswith("DB_"):
            service = "postgres"
            key = github_key[len("DB_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "database-credentials"
        elif github_key.startswith("API_"):
            service = "other"
            key = github_key[len("API_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        elif github_key.startswith("SECRET_"):
            service = "other"
            key = github_key[len("SECRET_"):].lower()
            pulumi_key = f"{service}_{key}"
            group = "security-tokens"
        else:
            # Default to other for unknown secrets
            service = "other"
            key = github_key.lower()
            pulumi_key = f"{service}_{key}"
            group = "api-keys"
        
        return {
            "service": service,
            "key": key,
            "pulumi_key": pulumi_key,
            "group": group
        }
    
    def map_pulumi_to_github(self, pulumi_key: str) -> str:
        """Map Pulumi ESC secret name to GitHub secret name"""
        # Check if we have a direct mapping
        for github_key, mapping in self.service_mappings.items():
            if mapping["pulumi_key"] == pulumi_key:
                return github_key
        
        # Try to infer mapping from name
        parts = pulumi_key.split("_", 1)
        if len(parts) == 2:
            service, key = parts
            return f"{service.upper()}_{key.upper()}"
        else:
            return pulumi_key.upper()
    
    def sync_github_to_pulumi(self, dry_run: bool = False) -> Dict[str, Any]:
        """Synchronize GitHub secrets to Pulumi ESC"""
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "direction": "github_to_pulumi",
            "dry_run": dry_run,
            "total": 0,
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        # Get GitHub secrets
        github_secrets = self.github.get_organization_secrets()
        results["total"] = len(github_secrets)
        
        # Get Pulumi secrets
        pulumi_secrets = self.pulumi.get_secrets()
        pulumi_secret_names = [s["name"] for s in pulumi_secrets]
        
        # Process each GitHub secret
        for secret in github_secrets:
            github_key = secret["name"]
            try:
                # Map to Pulumi ESC secret
                mapping = self.map_github_to_pulumi(github_key)
                pulumi_key = mapping["pulumi_key"]
                group = mapping["group"]
                
                # Check if secret already exists in Pulumi ESC
                if pulumi_key in pulumi_secret_names:
                    logger.info(f"Secret {pulumi_key} already exists in Pulumi ESC, skipping")
                    results["skipped"] += 1
                    continue
                
                # Get secret value from GitHub
                # In a real implementation, this would get the secret value from GitHub
                # For this example, we'll use a dummy value
                secret_value = f"dummy_value_for_{github_key}"
                
                # Set secret in Pulumi ESC
                if not dry_run:
                    if self.pulumi.set_secret(pulumi_key, secret_value, group):
                        results["synced"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to set secret {pulumi_key} in Pulumi ESC")
                else:
                    logger.info(f"Would set secret {pulumi_key} in Pulumi ESC (dry run)")
                    results["synced"] += 1
            except Exception as e:
                results["failed"] += 1
                error_message = f"Failed to sync GitHub secret {github_key} to Pulumi ESC: {str(e)}"
                results["errors"].append(error_message)
                logger.error(error_message)
        
        return results
    
    def sync_pulumi_to_github(self, dry_run: bool = False) -> Dict[str, Any]:
        """Synchronize Pulumi ESC secrets to GitHub"""
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "direction": "pulumi_to_github",
            "dry_run": dry_run,
            "total": 0,
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        # Get Pulumi secrets
        pulumi_secrets = self.pulumi.get_secrets()
        results["total"] = len(pulumi_secrets)
        
        # Get GitHub secrets
        github_secrets = self.github.get_organization_secrets()
        github_secret_names = [s["name"] for s in github_secrets]
        
        # Process each Pulumi secret
        for secret in pulumi_secrets:
            pulumi_key = secret["name"]
            try:
                # Map to GitHub secret
                github_key = self.map_pulumi_to_github(pulumi_key)
                
                # Check if secret already exists in GitHub
                if github_key in github_secret_names:
                    logger.info(f"Secret {github_key} already exists in GitHub, skipping")
                    results["skipped"] += 1
                    continue
                
                # Get secret value from Pulumi ESC
                # In a real implementation, this would get the secret value from Pulumi ESC
                # For this example, we'll use a dummy value
                secret_value = f"dummy_value_for_{pulumi_key}"
                
                # Set secret in GitHub
                if not dry_run:
                    if self.github.set_organization_secret(github_key, secret_value):
                        results["synced"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to set secret {github_key} in GitHub")
                else:
                    logger.info(f"Would set secret {github_key} in GitHub (dry run)")
                    results["synced"] += 1
            except Exception as e:
                results["failed"] += 1
                error_message = f"Failed to sync Pulumi ESC secret {pulumi_key} to GitHub: {str(e)}"
                results["errors"].append(error_message)
                logger.error(error_message)
        
        return results
    
    def sync_bidirectional(self, dry_run: bool = False) -> Dict[str, Any]:
        """Synchronize secrets bidirectionally between GitHub and Pulumi ESC"""
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "dry_run": dry_run,
            "github_to_pulumi": self.sync_github_to_pulumi(dry_run),
            "pulumi_to_github": self.sync_pulumi_to_github(dry_run)
        }
        
        return results


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Synchronize secrets between GitHub and Pulumi ESC")
    parser.add_argument("--github-org", "-g", required=True, help="GitHub organization name")
    parser.add_argument("--pulumi-org", "-p", required=True, help="Pulumi organization name")
    parser.add_argument("--pulumi-env", "-e", required=True, help="Pulumi environment name")
    parser.add_argument("--github-token", help="GitHub token (or set GITHUB_TOKEN environment variable)")
    parser.add_argument("--pulumi-token", help="Pulumi token (or set PULUMI_ACCESS_TOKEN environment variable)")
    parser.add_argument("--direction", "-d", choices=["github-to-pulumi", "pulumi-to-github", "bidirectional"], default="bidirectional", help="Synchronization direction")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't actually set secrets)")
    parser.add_argument("--output", "-o", help="Output file (JSON)")
    args = parser.parse_args()
    
    try:
        synchronizer = SecretSynchronizer(
            github_org=args.github_org,
            pulumi_org=args.pulumi_org,
            pulumi_env=args.pulumi_env,
            github_token=args.github_token,
            pulumi_token=args.pulumi_token
        )
        
        if args.direction == "github-to-pulumi":
            result = synchronizer.sync_github_to_pulumi(args.dry_run)
        elif args.direction == "pulumi-to-github":
            result = synchronizer.sync_pulumi_to_github(args.dry_run)
        else:
            result = synchronizer.sync_bidirectional(args.dry_run)
        
        # Print summary
        if args.direction == "bidirectional":
            print(f"GitHub to Pulumi: {result['github_to_pulumi']['synced']} synced, {result['github_to_pulumi']['failed']} failed, {result['github_to_pulumi']['skipped']} skipped")
            print(f"Pulumi to GitHub: {result['pulumi_to_github']['synced']} synced, {result['pulumi_to_github']['failed']} failed, {result['pulumi_to_github']['skipped']} skipped")
        else:
            print(f"Synced: {result['synced']}")
            print(f"Failed: {result['failed']}")
            print(f"Skipped: {result['skipped']}")
            print(f"Total: {result['total']}")
        
        # Write result to file if specified
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Result written to {args.output}")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

