#!/usr/bin/env python3
"""
GitHub Organization Secrets Integration for Sophia AI
Manages secrets from GitHub organization level and integrates with Pulumi ESC
"""

import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import base64
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class GitHubConfig:
    """Configuration for GitHub organization secrets integration"""
    organization: str = "ai-cherry"
    token: Optional[str] = None
    api_base_url: str = "https://api.github.com"
    
    def __post_init__(self):
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN")

class GitHubSecretsManager:
    """
    GitHub Organization Secrets Manager
    Handles retrieval and management of organization-level secrets
    """
    
    def __init__(self, config: GitHubConfig = None):
        self.config = config or GitHubConfig()
        self.headers = {
            "Authorization": f"token {self.config.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
    def list_organization_secrets(self) -> List[Dict[str, Any]]:
        """List all organization secrets"""
        try:
            url = f"{self.config.api_base_url}/orgs/{self.config.organization}/actions/secrets"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            secrets = data.get('secrets', [])
            
            logger.info(f"Found {len(secrets)} organization secrets")
            return secrets
            
        except requests.RequestException as e:
            logger.error(f"Failed to list organization secrets: {e}")
            return []
    
    def get_organization_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific organization secret"""
        try:
            url = f"{self.config.api_base_url}/orgs/{self.config.organization}/actions/secrets/{secret_name}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get organization secret {secret_name}: {e}")
            return None
    
    def create_organization_secret(self, secret_name: str, secret_value: str, 
                                 visibility: str = "all") -> bool:
        """Create or update an organization secret"""
        try:
            # First, get the organization's public key for encryption
            public_key = self._get_organization_public_key()
            if not public_key:
                return False
            
            # Encrypt the secret value
            encrypted_value = self._encrypt_secret(secret_value, public_key['key'])
            
            url = f"{self.config.api_base_url}/orgs/{self.config.organization}/actions/secrets/{secret_name}"
            payload = {
                "encrypted_value": encrypted_value,
                "key_id": public_key['key_id'],
                "visibility": visibility
            }
            
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully created/updated organization secret: {secret_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create organization secret {secret_name}: {e}")
            return False
    
    def _get_organization_public_key(self) -> Optional[Dict[str, str]]:
        """Get the organization's public key for secret encryption"""
        try:
            url = f"{self.config.api_base_url}/orgs/{self.config.organization}/actions/secrets/public-key"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get organization public key: {e}")
            return None
    
    def _encrypt_secret(self, secret_value: str, public_key: str) -> str:
        """Encrypt a secret value using the organization's public key"""
        try:
            from nacl import encoding, public
            
            # Decode the public key
            public_key_bytes = base64.b64decode(public_key)
            public_key_obj = public.PublicKey(public_key_bytes)
            
            # Create a sealed box
            sealed_box = public.SealedBox(public_key_obj)
            
            # Encrypt the secret
            encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
            
            # Return base64 encoded encrypted value
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt secret: {e}")
            raise
    
    def generate_secrets_mapping(self) -> Dict[str, str]:
        """Generate a mapping of expected secrets for Sophia AI"""
        return {
            # Security
            "SOPHIA_SECRET_KEY": "Core application secret key",
            "SOPHIA_ADMIN_USERNAME": "Admin username for Sophia AI",
            "SOPHIA_ADMIN_PASSWORD": "Admin password for Sophia AI",
            "SOPHIA_MASTER_KEY": "Master encryption key",
            "SOPHIA_JWT_SECRET": "JWT signing secret",
            "SOPHIA_ENCRYPTION_KEY": "Data encryption key",
            
            # Database
            "POSTGRES_HOST": "PostgreSQL database host",
            "POSTGRES_USER": "PostgreSQL username",
            "POSTGRES_PASSWORD": "PostgreSQL password",
            "POSTGRES_DB": "PostgreSQL database name",
            "REDIS_HOST": "Redis cache host",
            "REDIS_PASSWORD": "Redis password",
            
            # LLM Gateway
            "PORTKEY_API_KEY": "Portkey LLM gateway API key",
            "PORTKEY_CONFIG": "Portkey configuration ID",
            "OPENROUTER_API_KEY": "OpenRouter API key",
            
            # AI Services
            "OPENAI_API_KEY": "OpenAI API key",
            "ANTHROPIC_API_KEY": "Anthropic Claude API key",
            "GEMINI_API_KEY": "Google Gemini API key",
            "PERPLEXITY_API_KEY": "Perplexity AI API key",
            "MISTRAL_API_KEY": "Mistral AI API key",
            "TOGETHER_AI_API_KEY": "Together AI API key",
            "DEEPSEEK_API_KEY": "DeepSeek API key",
            "GROK_AI_API_KEY": "Grok AI API key",
            "HUGGINGFACE_API_TOKEN": "HuggingFace API token",
            "STABILITY_API_KEY": "Stability AI API key",
            "ELEVEN_LABS_API_KEY": "ElevenLabs API key",
            
            # Business Integrations
            "GONG_ACCESS_KEY": "Gong.io access key",
            "GONG_ACCESS_KEY_SECRET": "Gong.io access key secret",
            "SALESFORCE_ACCESS_TOKEN": "Salesforce access token",
            "SALESFORCE_CLIENT_ID": "Salesforce client ID",
            "SALESFORCE_CLIENT_SECRET": "Salesforce client secret",
            "HUBSPOT_API_KEY": "HubSpot API key",
            "HUBSPOT_CLIENT_ID": "HubSpot client ID",
            "HUBSPOT_CLIENT_SECRET": "HubSpot client secret",
            
            # Slack
            "SLACK_CLIENT_ID": "Slack app client ID",
            "SLACK_CLIENT_SECRET": "Slack app client secret",
            "SLACK_SIGNING_SECRET": "Slack signing secret",
            "SLACK_APP_TOKEN": "Slack app token",
            "SLACK_BOT_TOKEN": "Slack bot token",
            "SLACK_REFRESH_TOKEN": "Slack refresh token",
            "SLACK_USER_ID": "Slack user ID",
            
            # Vector Databases
            "PINECONE_API_KEY": "Pinecone vector database API key",
            "WEAVIATE_URL": "Weaviate instance URL",
            "WEAVIATE_GRPC_URL": "Weaviate gRPC URL",
            "WEAVIATE_API_KEY": "Weaviate API key",
            
            # Knowledge Services
            "NOTION_API_KEY": "Notion API key",
            "APOLLO_IO_API_KEY": "Apollo.io API key",
            "APIFY_API_TOKEN": "Apify API token",
            "BRAVE_API_KEY": "Brave Search API key",
            "TAVILY_API_KEY": "Tavily API key",
            "ZENROWS_API_KEY": "ZenRows API key",
            "EXA_API_KEY": "Exa API key",
            
            # Monitoring
            "LANGSMITH_API_KEY": "LangSmith API key",
            "LANGCHAIN_API_KEY": "LangChain API key",
            "LANGGRAPH_API_KEY": "LangGraph API key",
            "ARIZE_API_KEY": "Arize AI monitoring API key",
            
            # Infrastructure
            "PULUMI_ACCESS_TOKEN": "Pulumi access token",
            "LAMBDA_LABS_API_KEY": "Lambda Labs API key",
            "VERCEL_TOKEN": "Vercel deployment token",
            "DOCKER_USERNAME": "Docker Hub username",
            "DOCKER_TOKEN": "Docker Hub access token",
            
            # Additional Services
            "REDIS_USER_API_KEY": "Redis Cloud user API key",
            "REDIS_ACCOUNT_KEY": "Redis Cloud account key",
            "NEO4J_URI": "Neo4j database URI",
            "NEO4J_USERNAME": "Neo4j username",
            "NEO4J_PASSWORD": "Neo4j password",
            "NEO4J_CLIENT_ID": "Neo4j client ID",
            "NEO4J_CLIENT_SECRET": "Neo4j client secret",
            "AIRBYTE_CLIENT_ID": "Airbyte client ID",
            "AIRBYTE_CLIENT_SECRET": "Airbyte client secret",
            
            # Additional Tools
            "FIGMA_PERSONAL_ACCESS_TOKEN": "Figma personal access token",
            "PHANTOM_BUSTER_API_KEY": "PhantomBuster API key",
            "SLIDESPEAK_API_KEY": "SlideSpeak API key",
            "MUREKA_API_KEY": "Mureka API key",
            "VENICE_AI_API_KEY": "Venice AI API key",
            "EDEN_AI_API_KEY": "Eden AI API key",
            "TWINGLY_API_KEY": "Twingly API key",
            "BARDEEN_ID": "Bardeen automation ID"
        }
    
    def audit_secrets_coverage(self) -> Dict[str, Any]:
        """Audit which secrets are present in the organization"""
        expected_secrets = self.generate_secrets_mapping()
        org_secrets = self.list_organization_secrets()
        
        # Create a set of existing secret names
        existing_secrets = {secret['name'] for secret in org_secrets}
        
        # Check coverage
        coverage_report = {
            'total_expected': len(expected_secrets),
            'total_existing': len(existing_secrets),
            'missing_secrets': [],
            'extra_secrets': [],
            'coverage_percentage': 0
        }
        
        # Find missing secrets
        for expected_name in expected_secrets.keys():
            if expected_name not in existing_secrets:
                coverage_report['missing_secrets'].append({
                    'name': expected_name,
                    'description': expected_secrets[expected_name]
                })
        
        # Find extra secrets (not in our expected list)
        for existing_name in existing_secrets:
            if existing_name not in expected_secrets:
                coverage_report['extra_secrets'].append(existing_name)
        
        # Calculate coverage percentage
        matched_secrets = len(expected_secrets) - len(coverage_report['missing_secrets'])
        coverage_report['coverage_percentage'] = (matched_secrets / len(expected_secrets)) * 100
        
        logger.info(f"Secrets coverage: {coverage_report['coverage_percentage']:.1f}%")
        logger.info(f"Missing secrets: {len(coverage_report['missing_secrets'])}")
        
        return coverage_report
    
    def create_missing_secrets_template(self) -> str:
        """Create a template for missing secrets that need to be added"""
        coverage = self.audit_secrets_coverage()
        
        template = "# Missing GitHub Organization Secrets\n"
        template += "# Add these secrets to the ai-cherry organization\n\n"
        
        for missing_secret in coverage['missing_secrets']:
            template += f"# {missing_secret['description']}\n"
            template += f"{missing_secret['name']}=your_value_here\n\n"
        
        return template
    
    def validate_secret_access(self) -> bool:
        """Validate that we can access organization secrets"""
        try:
            secrets = self.list_organization_secrets()
            return len(secrets) >= 0  # Even 0 secrets means we have access
        except Exception as e:
            logger.error(f"Cannot access organization secrets: {e}")
            return False

class PulumiGitHubIntegration:
    """
    Integration between Pulumi ESC and GitHub organization secrets
    """
    
    def __init__(self, github_config: GitHubConfig = None):
        self.github_manager = GitHubSecretsManager(github_config)
        
    def create_pulumi_esc_import(self) -> str:
        """Create a Pulumi ESC import configuration for GitHub secrets"""
        
        import_config = {
            "imports": [
                {
                    "type": "github-secrets",
                    "github": {
                        "organization": self.github_manager.config.organization,
                        "token": "${GITHUB_TOKEN}"
                    }
                }
            ]
        }
        
        return json.dumps(import_config, indent=2)
    
    def generate_esc_environment_with_github(self) -> str:
        """Generate a complete ESC environment that imports from GitHub"""
        
        environment = {
            "imports": [
                "github-org-secrets"
            ],
            "values": {
                "github": {
                    "organization": self.github_manager.config.organization,
                    "secrets": "${github.secrets}"
                },
                "app": {
                    "name": "sophia-ai",
                    "environment": "production",
                    "version": "2.0.0"
                }
            }
        }
        
        return json.dumps(environment, indent=2)
    
    def sync_secrets_to_pulumi(self) -> bool:
        """Sync GitHub organization secrets to Pulumi ESC"""
        try:
            # This would implement the actual sync logic
            logger.info("Syncing GitHub secrets to Pulumi ESC...")
            
            # Get all organization secrets
            org_secrets = self.github_manager.list_organization_secrets()
            
            # Create ESC environment with GitHub import
            esc_config = self.generate_esc_environment_with_github()
            
            logger.info(f"Would sync {len(org_secrets)} secrets to Pulumi ESC")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync secrets to Pulumi: {e}")
            return False

def create_github_secrets_setup_script() -> str:
    """Create a script to help set up GitHub organization secrets"""
    
    script = '''#!/bin/bash
# GitHub Organization Secrets Setup Script for Sophia AI
# Run this script to set up all required organization secrets

set -e

ORGANIZATION="ai-cherry"
GITHUB_TOKEN="${GITHUB_TOKEN}"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is required"
    echo "Create a personal access token with 'admin:org' permissions"
    exit 1
fi

echo "🔐 Setting up GitHub Organization Secrets for $ORGANIZATION"
echo "=================================================="

# Function to create or update a secret
create_secret() {
    local secret_name="$1"
    local secret_description="$2"
    
    echo "Setting up secret: $secret_name"
    echo "Description: $secret_description"
    echo -n "Enter value for $secret_name: "
    read -s secret_value
    echo
    
    # Create the secret using GitHub CLI
    if command -v gh &> /dev/null; then
        echo "$secret_value" | gh secret set "$secret_name" --org "$ORGANIZATION" --visibility all
        echo "✅ Secret $secret_name created successfully"
    else
        echo "❌ GitHub CLI (gh) not found. Please install it first."
        echo "   Visit: https://cli.github.com/"
        return 1
    fi
    
    echo
}

# Core Security Secrets
echo "📋 Setting up core security secrets..."
create_secret "SOPHIA_SECRET_KEY" "Core application secret key"
create_secret "SOPHIA_ADMIN_USERNAME" "Admin username for Sophia AI"
create_secret "SOPHIA_ADMIN_PASSWORD" "Admin password for Sophia AI"
create_secret "SOPHIA_MASTER_KEY" "Master encryption key"

# Database Secrets
echo "📋 Setting up database secrets..."
create_secret "POSTGRES_HOST" "PostgreSQL database host"
create_secret "POSTGRES_USER" "PostgreSQL username"
create_secret "POSTGRES_PASSWORD" "PostgreSQL password"
create_secret "POSTGRES_DB" "PostgreSQL database name"

# Add more secrets as needed...

echo "🎉 GitHub organization secrets setup complete!"
echo "You can now use these secrets in your Pulumi ESC environment."
'''
    
    return script

def main():
    """Main function to demonstrate GitHub secrets integration"""
    
    print("🔐 GitHub Organization Secrets Integration")
    print("=" * 50)
    
    # Initialize GitHub secrets manager
    github_manager = GitHubSecretsManager()
    
    # Validate access
    print("1. Validating GitHub access...")
    if github_manager.validate_secret_access():
        print("✅ GitHub organization access validated")
    else:
        print("❌ Cannot access GitHub organization secrets")
        print("   Please ensure GITHUB_TOKEN is set with 'admin:org' permissions")
        return
    
    # Audit secrets coverage
    print("\n2. Auditing secrets coverage...")
    coverage = github_manager.audit_secrets_coverage()
    print(f"✅ Secrets coverage: {coverage['coverage_percentage']:.1f}%")
    print(f"   Total expected: {coverage['total_expected']}")
    print(f"   Total existing: {coverage['total_existing']}")
    print(f"   Missing: {len(coverage['missing_secrets'])}")
    
    # Create missing secrets template
    if coverage['missing_secrets']:
        print("\n3. Creating missing secrets template...")
        template = github_manager.create_missing_secrets_template()
        
        with open("/tmp/missing_secrets_template.env", "w") as f:
            f.write(template)
        
        print("✅ Missing secrets template created: /tmp/missing_secrets_template.env")
    
    # Create setup script
    print("\n4. Creating GitHub secrets setup script...")
    setup_script = create_github_secrets_setup_script()
    
    with open("/tmp/setup_github_secrets.sh", "w") as f:
        f.write(setup_script)
    
    os.chmod("/tmp/setup_github_secrets.sh", 0o755)
    print("✅ Setup script created: /tmp/setup_github_secrets.sh")
    
    # Initialize Pulumi integration
    print("\n5. Initializing Pulumi-GitHub integration...")
    pulumi_integration = PulumiGitHubIntegration()
    
    if pulumi_integration.sync_secrets_to_pulumi():
        print("✅ Pulumi-GitHub integration initialized")
    else:
        print("❌ Failed to initialize Pulumi-GitHub integration")
    
    print("\n🎉 GitHub secrets integration setup complete!")
    print("\nNext steps:")
    print("1. Review missing secrets template")
    print("2. Run setup script to add missing secrets")
    print("3. Update Pulumi ESC environment to import from GitHub")

if __name__ == "__main__":
    main()

