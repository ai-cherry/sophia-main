#!/usr/bin/env python3
"""
Sophia AI - GitHub Secrets Inventory
This script inventories all secrets in a GitHub organization and outputs them in a format
that can be used by the GitHub secrets synchronization script.
"""

import os
import json
import argparse
import subprocess
import logging
from typing import Dict, List, Any, Optional
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubSecretInventory:
    """
    Inventories all secrets in a GitHub organization
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
    
    def get_repository_secrets(self, repository: str) -> List[Dict[str, Any]]:
        """Get all repository secrets"""
        try:
            # Run GitHub CLI command to list secrets
            result = subprocess.run(
                ["gh", "secret", "list", "--repo", f"{self.organization}/{repository}", "--json", "name,updatedAt"],
                capture_output=True, text=True, check=True
            )
            
            # Parse JSON output
            secrets = json.loads(result.stdout)
            logger.info(f"Found {len(secrets)} GitHub repository secrets for {repository}")
            return secrets
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get GitHub repository secrets for {repository}: {e}")
            logger.error(f"GitHub CLI output: {e.stdout}")
            logger.error(f"GitHub CLI error: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Failed to get GitHub repository secrets for {repository}: {e}")
            return []
    
    def get_repositories(self) -> List[str]:
        """Get all repositories in the organization"""
        try:
            # Run GitHub CLI command to list repositories
            result = subprocess.run(
                ["gh", "repo", "list", self.organization, "--json", "name", "--limit", "100"],
                capture_output=True, text=True, check=True
            )
            
            # Parse JSON output
            repositories = json.loads(result.stdout)
            repo_names = [repo["name"] for repo in repositories]
            logger.info(f"Found {len(repo_names)} GitHub repositories")
            return repo_names
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get GitHub repositories: {e}")
            logger.error(f"GitHub CLI output: {e.stdout}")
            logger.error(f"GitHub CLI error: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"Failed to get GitHub repositories: {e}")
            return []
    
    def map_secret_to_service(self, secret_name: str) -> Dict[str, str]:
        """Map GitHub secret name to service and key"""
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
        elif secret_name.startswith("POSTGRES_"):
            service = "postgres"
            key = secret_name[len("POSTGRES_"):].lower()
            group = "database-credentials"
        elif secret_name.startswith("DB_"):
            service = "postgres"
            key = secret_name[len("DB_"):].lower()
            group = "database-credentials"
        elif secret_name.startswith("API_"):
            service = "other"
            key = secret_name[len("API_"):].lower()
            group = "api-keys"
        elif secret_name.startswith("SECRET_"):
            service = "other"
            key = secret_name[len("SECRET_"):].lower()
            group = "security-tokens"
        else:
            # Default to other for unknown secrets
            service = "other"
            key = secret_name.lower()
            group = "api-keys"
        
        return {
            "service": service,
            "key": key,
            "group": group
        }
    
    def create_inventory(self, output_file: str = None) -> Dict[str, Any]:
        """Create inventory of all GitHub secrets"""
        inventory = {
            "organization": self.organization,
            "timestamp": datetime.datetime.now().isoformat(),
            "organization_secrets": [],
            "repository_secrets": {}
        }
        
        # Get organization secrets
        org_secrets = self.get_organization_secrets()
        for secret in org_secrets:
            secret_name = secret["name"]
            mapping = self.map_secret_to_service(secret_name)
            inventory["organization_secrets"].append({
                "name": secret_name,
                "updated_at": secret["updatedAt"],
                "service": mapping["service"],
                "key": mapping["key"],
                "group": mapping["group"]
            })
        
        # Get repository secrets
        repositories = self.get_repositories()
        for repo in repositories:
            repo_secrets = self.get_repository_secrets(repo)
            if repo_secrets:
                inventory["repository_secrets"][repo] = []
                for secret in repo_secrets:
                    secret_name = secret["name"]
                    mapping = self.map_secret_to_service(secret_name)
                    inventory["repository_secrets"][repo].append({
                        "name": secret_name,
                        "updated_at": secret["updatedAt"],
                        "service": mapping["service"],
                        "key": mapping["key"],
                        "group": mapping["group"]
                    })
        
        # Write inventory to file if specified
        if output_file:
            with open(output_file, "w") as f:
                json.dump(inventory, f, indent=2)
            logger.info(f"Wrote inventory to {output_file}")
        
        return inventory

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Inventory GitHub secrets")
    parser.add_argument("--organization", "-o", required=True, help="GitHub organization name")
    parser.add_argument("--token", "-t", help="GitHub token (or set GITHUB_TOKEN environment variable)")
    parser.add_argument("--output", "-f", help="Output file (JSON)")
    args = parser.parse_args()
    
    try:
        inventory = GitHubSecretInventory(args.organization, args.token)
        result = inventory.create_inventory(args.output)
        
        # Print summary
        print(f"Organization: {result['organization']}")
        print(f"Organization secrets: {len(result['organization_secrets'])}")
        print(f"Repositories with secrets: {len(result['repository_secrets'])}")
        total_repo_secrets = sum(len(secrets) for secrets in result['repository_secrets'].values())
        print(f"Repository secrets: {total_repo_secrets}")
        print(f"Total secrets: {len(result['organization_secrets']) + total_repo_secrets}")
        
        if args.output:
            print(f"Inventory written to {args.output}")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

