"""
Sophia AI - GitHub Secrets Synchronization
This module synchronizes secrets between GitHub organization and Pulumi ESC
"""

import pulumi
import json
import subprocess
import os
import logging
from typing import Dict, List, Any, Optional
from pulumi import Config
import pulumi_pulumiservice as pulumiservice

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubSecretSync:
    """
    Synchronizes secrets between GitHub organization and Pulumi ESC
    """
    
    def __init__(self, organization: str = "ai-cherry"):
        self.organization = organization
        self.config = Config()
        self.github_token = self.config.require_secret("github_token")
        self.pulumi_organization = self.config.get("pulumi_organization") or "ai-cherry"
        self.environment = "production"
        
        # Load secret mappings
        self.secret_mappings = self._load_secret_mappings()
    
    def _load_secret_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load secret mappings from Pulumi ESC configuration"""
        try:
            # Try to load from a local file first (for development)
            if os.path.exists("pulumi_esc_config.json"):
                with open("pulumi_esc_config.json", "r") as f:
                    config = json.load(f)
                    return config.get("secret_mappings", {})
            
            # Otherwise, use the mappings from the main ESC module
            from . import __main__ as esc_main
            return {name: mapping for name, mapping in esc_main.all_secret_mappings.items()}
        except Exception as e:
            logger.error(f"Failed to load secret mappings: {e}")
            return {}
    
    def _get_github_secrets(self) -> List[Dict[str, Any]]:
        """Get all GitHub organization secrets"""
        try:
            # Set GitHub token for CLI
            os.environ["GITHUB_TOKEN"] = self.github_token
            
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
            logger.error(f"Failed to get GitHub secrets: {e}")
            logger.error(f"GitHub CLI output: {e.stdout}")
            logger.error(f"GitHub CLI error: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Failed to get GitHub secrets: {e}")
            return []
    
    def _get_github_secret_value(self, secret_name: str) -> Optional[str]:
        """
        Get GitHub secret value
        
        Note: GitHub CLI doesn't support getting secret values directly.
        This is a workaround using Pulumi config as a proxy.
        In a real implementation, you would use the GitHub API with proper authentication.
        """
        try:
            # Try to get from Pulumi config
            return self.config.require_secret(secret_name.lower())
        except Exception as e:
            logger.error(f"Failed to get GitHub secret value for {secret_name}: {e}")
            return None
    
    def _map_github_secret_to_esc(self, secret_name: str) -> Dict[str, str]:
        """Map GitHub secret name to Pulumi ESC secret details"""
        # Try direct mapping first
        if secret_name.lower() in self.secret_mappings:
            return self.secret_mappings[secret_name.lower()]
        
        # Try to infer mapping from name
        if secret_name.startswith("SNOWFLAKE_"):
            service = "snowflake"
            key = secret_name[len("SNOWFLAKE_"):].lower()
            group = "database-credentials"
        elif secret_name.startswith("GONG_"):
            service = "gong"
            key = secret_name[len("GONG_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("VERCEL_"):
            service = "vercel"
            key = secret_name[len("VERCEL_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("ESTUARY_"):
            service = "estuary"
            key = secret_name[len("ESTUARY_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("LAMBDA_"):
            service = "lambda_labs"
            key = secret_name[len("LAMBDA_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("AIRBYTE_"):
            service = "airbyte"
            key = secret_name[len("AIRBYTE_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("PINECONE_"):
            service = "pinecone"
            key = secret_name[len("PINECONE_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("WEAVIATE_"):
            service = "weaviate"
            key = secret_name[len("WEAVIATE_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("OPENAI_"):
            service = "openai"
            key = secret_name[len("OPENAI_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("ANTHROPIC_"):
            service = "anthropic"
            key = secret_name[len("ANTHROPIC_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("GITHUB_"):
            service = "github"
            key = secret_name[len("GITHUB_"):].lower()
            group = "security-tokens"
        else:
            # Default to api-keys for unknown secrets
            service = "other"
            key = secret_name.lower()
            group = "api-keys"
        
        return {
            "group": group,
            "description": f"{service.title()} {key.replace('_', ' ')}",
            "service": service
        }
    
    def sync_github_to_esc(self) -> Dict[str, Any]:
        """Synchronize GitHub secrets to Pulumi ESC"""
        results = {
            "total": 0,
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        # Get GitHub secrets
        github_secrets = self._get_github_secrets()
        results["total"] = len(github_secrets)
        
        # Process each secret
        for secret in github_secrets:
            secret_name = secret["name"]
            try:
                # Get secret value
                secret_value = self._get_github_secret_value(secret_name)
                if not secret_value:
                    results["skipped"] += 1
                    continue
                
                # Map to ESC secret
                esc_mapping = self._map_github_secret_to_esc(secret_name)
                esc_name = f"{esc_mapping['service']}_{secret_name.lower()}"
                
                # Create Pulumi ESC secret
                pulumiservice.EnvironmentSecret(f"github-{secret_name.lower()}",
                    organization=self.pulumi_organization,
                    environment=f"sophia-{self.environment}",
                    name=esc_name,
                    value=secret_value,
                    secret_group=esc_mapping["group"]
                )
                
                results["synced"] += 1
                logger.info(f"Synced GitHub secret {secret_name} to Pulumi ESC as {esc_name}")
            except Exception as e:
                results["failed"] += 1
                error_message = f"Failed to sync GitHub secret {secret_name}: {str(e)}"
                results["errors"].append(error_message)
                logger.error(error_message)
        
        return results

# Create GitHub secret synchronization
github_sync = GitHubSecretSync()
sync_results = github_sync.sync_github_to_esc()

# Export results
pulumi.export("github_sync_total", sync_results["total"])
pulumi.export("github_sync_synced", sync_results["synced"])
pulumi.export("github_sync_failed", sync_results["failed"])
pulumi.export("github_sync_skipped", sync_results["skipped"])

