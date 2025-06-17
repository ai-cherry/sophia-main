#!/usr/bin/env python3
"""
GitHub Organization Secrets Configuration
Configures all required secrets for Sophia AI at organization level
"""

import os
import json
import requests
import base64
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubSecretsManager:
    """Manages GitHub organization secrets for Sophia AI"""
    
    def __init__(self, org: str, token: str):
        self.org = org
        self.token = token
        self.base_url = f"https://api.github.com/orgs/{org}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def get_public_key(self) -> Dict[str, str]:
        """Get organization public key for secret encryption"""
        response = requests.get(f"{self.base_url}/actions/secrets/public-key", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt secret value using organization public key"""
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        
        # Load the public key
        public_key_bytes = base64.b64decode(public_key)
        public_key_obj = serialization.load_der_public_key(public_key_bytes)
        
        # Encrypt the secret
        encrypted = public_key_obj.encrypt(
            secret_value.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def create_or_update_secret(self, secret_name: str, secret_value: str, visibility: str = "all") -> bool:
        """Create or update an organization secret"""
        try:
            # Get public key
            public_key_data = self.get_public_key()
            
            # Encrypt the secret
            encrypted_value = self.encrypt_secret(public_key_data['key'], secret_value)
            
            # Create/update the secret
            data = {
                "encrypted_value": encrypted_value,
                "key_id": public_key_data['key_id'],
                "visibility": visibility
            }
            
            response = requests.put(
                f"{self.base_url}/actions/secrets/{secret_name}",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [201, 204]:
                logger.info(f"✅ Secret '{secret_name}' configured successfully")
                return True
            else:
                logger.error(f"❌ Failed to configure secret '{secret_name}': {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error configuring secret '{secret_name}': {e}")
            return False
    
    def list_secrets(self) -> List[str]:
        """List all organization secrets"""
        response = requests.get(f"{self.base_url}/actions/secrets", headers=self.headers)
        response.raise_for_status()
        return [secret['name'] for secret in response.json().get('secrets', [])]
    
    def configure_sophia_secrets(self, secrets_config: Dict[str, str]) -> Dict[str, bool]:
        """Configure all Sophia AI secrets"""
        results = {}
        
        logger.info("🔐 Configuring Sophia AI organization secrets...")
        
        for secret_name, secret_value in secrets_config.items():
            if secret_value and secret_value != "your-secret-here":
                results[secret_name] = self.create_or_update_secret(secret_name, secret_value)
            else:
                logger.warning(f"⚠️  Skipping '{secret_name}' - no value provided")
                results[secret_name] = False
        
        return results

def get_sophia_secrets_template() -> Dict[str, str]:
    """Get template of all required Sophia AI secrets"""
    return {
        # Database Configuration
        "POSTGRES_HOST": "your-postgres-host",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "sophia",
        "POSTGRES_PASSWORD": "your-postgres-password",
        "POSTGRES_DB": "sophia_payready",
        "REDIS_HOST": "your-redis-host",
        "REDIS_PORT": "6379",
        "REDIS_PASSWORD": "your-redis-password",
        "REDIS_DB": "0",
        
        # AI/ML Service APIs
        "OPENAI_API_KEY": "your-openai-api-key",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key",
        "HUGGINGFACE_API_KEY": "your-huggingface-api-key",
        "COHERE_API_KEY": "your-cohere-api-key",
        "REPLICATE_API_KEY": "your-replicate-api-key",
        "TOGETHER_API_KEY": "your-together-api-key",
        
        # Gateway Services
        "PORTKEY_API_KEY": "your-portkey-api-key",
        "OPENROUTER_API_KEY": "your-openrouter-api-key",
        "KONG_ACCESS_TOKEN": "your-kong-access-token",
        "ARIZE_API_KEY": "your-arize-api-key",
        
        # Vector Databases
        "PINECONE_API_KEY": "your-pinecone-api-key",
        "PINECONE_ENVIRONMENT": "us-west1-gcp",
        "PINECONE_INDEX_NAME": "sophia-index",
        "WEAVIATE_URL": "your-weaviate-url",
        "WEAVIATE_API_KEY": "your-weaviate-api-key",
        
        # Business Intelligence
        "HUBSPOT_API_KEY": "your-hubspot-api-key",
        "GONG_API_KEY": "your-gong-api-key",
        "GONG_API_SECRET": "your-gong-api-secret",
        "SALESFORCE_CLIENT_ID": "your-salesforce-client-id",
        "SALESFORCE_CLIENT_SECRET": "your-salesforce-client-secret",
        "SALESFORCE_USERNAME": "your-salesforce-username",
        "SALESFORCE_PASSWORD": "your-salesforce-password",
        "SALESFORCE_SECURITY_TOKEN": "your-salesforce-security-token",
        
        # Communication
        "SLACK_BOT_TOKEN": "your-slack-bot-token",
        "SLACK_APP_TOKEN": "your-slack-app-token",
        "SLACK_SIGNING_SECRET": "your-slack-signing-secret",
        "SLACK_WEBHOOK_URL": "your-slack-webhook-url",
        "SMTP_HOST": "your-smtp-host",
        "SMTP_PORT": "587",
        "SMTP_USER": "your-smtp-user",
        "SMTP_PASSWORD": "your-smtp-password",
        
        # Infrastructure
        "AWS_ACCESS_KEY_ID": "your-aws-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "your-aws-secret-access-key",
        "AWS_REGION": "us-east-1",
        "LAMBDA_LABS_API_KEY": "your-lambda-labs-api-key",
        "LAMBDA_LABS_SSH_KEY": "your-lambda-labs-ssh-key",
        
        # Security
        "SECRET_KEY": "your-secret-key-32-chars-minimum",
        "SOPHIA_MASTER_KEY": "your-sophia-master-key",
        "JWT_SECRET_KEY": "your-jwt-secret-key",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "your-admin-password",
        
        # Monitoring
        "GRAFANA_ADMIN_PASSWORD": "your-grafana-admin-password",
        "PROMETHEUS_AUTH_TOKEN": "your-prometheus-auth-token",
        
        # Data Integration
        "AIRBYTE_CLIENT_ID": "your-airbyte-client-id",
        "AIRBYTE_CLIENT_SECRET": "your-airbyte-client-secret",
        "AIRBYTE_WORKSPACE_ID": "your-airbyte-workspace-id",
        "DBT_API_KEY": "your-dbt-api-key",
        "DBT_ACCOUNT_ID": "your-dbt-account-id",
        
        # Development
        "GITHUB_TOKEN": "your-github-token",
        "GITHUB_WEBHOOK_SECRET": "your-github-webhook-secret",
        "PULUMI_ACCESS_TOKEN": "your-pulumi-access-token"
    }

def main():
    """Main function to configure GitHub organization secrets"""
    print("🔐 SOPHIA AI - GITHUB ORGANIZATION SECRETS CONFIGURATION")
    print("========================================================")
    
    # Get configuration from environment
    org = os.getenv("GITHUB_ORG", "ai-cherry")
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("❌ GITHUB_TOKEN environment variable is required")
        print("   Please set your GitHub personal access token with 'admin:org' scope")
        return
    
    # Initialize secrets manager
    secrets_manager = GitHubSecretsManager(org, token)
    
    # Get secrets template
    secrets_template = get_sophia_secrets_template()
    
    # Load actual secrets from environment or config file
    actual_secrets = {}
    config_file = "github_secrets_config.json"
    
    if os.path.exists(config_file):
        print(f"📁 Loading secrets from {config_file}")
        with open(config_file, 'r') as f:
            actual_secrets = json.load(f)
    else:
        print(f"📝 Creating template config file: {config_file}")
        with open(config_file, 'w') as f:
            json.dump(secrets_template, f, indent=2)
        print(f"✅ Template created. Please edit {config_file} with actual values and run again.")
        return
    
    # Configure secrets
    results = secrets_manager.configure_sophia_secrets(actual_secrets)
    
    # Report results
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n📊 CONFIGURATION RESULTS:")
    print(f"✅ Successfully configured: {successful}/{total} secrets")
    
    if successful < total:
        print(f"⚠️  Failed to configure: {total - successful} secrets")
        failed_secrets = [name for name, success in results.items() if not success]
        print(f"   Failed secrets: {', '.join(failed_secrets)}")
    
    print(f"\n🎉 GitHub organization secrets configuration completed!")
    print(f"   Organization: {org}")
    print(f"   Configured secrets are now available for all repositories")

if __name__ == "__main__":
    main()

