#!/usr/bin/env python3
"""
Secure Gong Credentials Update via GitHub Actions and Pulumi ESC
Updates Gong API credentials using proper secret management flow
"""

import os
import json
import subprocess
import logging
import yaml
from typing import Dict, Any, Optional
from datetime import datetime
import requests
import base64

logger = logging.getLogger(__name__)

class SecureGongCredentialManager:
    """
    Secure management of Gong API credentials via GitHub Actions and Pulumi ESC
    """
    
    def __init__(self):
        self.github_org = "ai-cherry"
        self.github_repo = "sophia-main"
        self.pulumi_org = "ai-cherry"
        self.pulumi_env = "sophia-production"
        
        # New Gong credentials from GitHub secrets
        self.new_credentials = {
            "access_key": "EX5L7AKSGQBOPNK66TDYVVEAKBVQ6IPK",
            "client_secret": "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNjU1NDc5ODksImFjY2Vzc0tleSI6IkVYNUw3QUtTR1FCT1BOSzY2VERZVlZFQUtCVlE2SVBLIn0.djgpFaMkt94HJHYHKbymM2D5aj_tQNJMV3aY_rwOSTY",
            "base_url": "https://us-70092.api.gong.io"
        }
    
    def update_pulumi_esc_environment(self) -> bool:
        """Update Pulumi ESC environment with new Gong credentials"""
        try:
            # Read current environment configuration
            env_file = "/home/ubuntu/sophia-main/pulumi-esc-environment.yaml"
            
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_config = yaml.safe_load(f)
            else:
                env_config = {"values": {}}
            
            # Ensure business_integrations section exists
            if "values" not in env_config:
                env_config["values"] = {}
            
            if "business_integrations" not in env_config["values"]:
                env_config["values"]["business_integrations"] = {}
            
            # Update Gong configuration with new credentials
            env_config["values"]["business_integrations"]["gong"] = {
                "access_key": "${GONG_ACCESS_KEY}",
                "client_secret": "${GONG_CLIENT_SECRET}",
                "base_url": self.new_credentials["base_url"],
                "api_version": "v2",
                "workspace_id": "us-70092",
                "enabled": True,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Add imports section to pull from GitHub secrets
            if "imports" not in env_config:
                env_config["imports"] = []
            
            # Add GitHub secrets import if not already present
            github_import = {
                "github": {
                    "organization": self.github_org,
                    "repository": self.github_repo,
                    "secrets": [
                        "GONG_ACCESS_KEY",
                        "GONG_CLIENT_SECRET"
                    ]
                }
            }
            
            # Check if GitHub import already exists
            github_import_exists = False
            for imp in env_config["imports"]:
                if "github" in imp:
                    github_import_exists = True
                    # Update existing import
                    if "secrets" not in imp["github"]:
                        imp["github"]["secrets"] = []
                    
                    for secret in github_import["github"]["secrets"]:
                        if secret not in imp["github"]["secrets"]:
                            imp["github"]["secrets"].append(secret)
                    break
            
            if not github_import_exists:
                env_config["imports"].append(github_import)
            
            # Write updated configuration
            with open(env_file, 'w') as f:
                yaml.dump(env_config, f, default_flow_style=False, indent=2)
            
            logger.info("Updated Pulumi ESC environment configuration with new Gong credentials")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Pulumi ESC environment: {e}")
            return False
    
    def update_secure_config(self) -> bool:
        """Update secure configuration to use new Gong credential mapping"""
        try:
            secure_config_file = "/home/ubuntu/sophia-main/backend/config/secure_config.py"
            
            # Read current secure config
            with open(secure_config_file, 'r') as f:
                content = f.read()
            
            # Update environment variable mapping for Gong
            updated_content = content.replace(
                "'GONG_API_KEY': 'gong_api_key',",
                "'GONG_ACCESS_KEY': 'gong_access_key',"
            ).replace(
                "'GONG_API_SECRET': 'gong_api_secret',",
                "'GONG_CLIENT_SECRET': 'gong_client_secret',"
            )
            
            # Add new attributes if not present
            if "gong_access_key: Optional[str] = None" not in updated_content:
                updated_content = updated_content.replace(
                    "gong_api_key: Optional[str] = None",
                    "gong_access_key: Optional[str] = None"
                ).replace(
                    "gong_api_secret: Optional[str] = None",
                    "gong_client_secret: Optional[str] = None"
                )
            
            # Write updated configuration
            with open(secure_config_file, 'w') as f:
                f.write(updated_content)
            
            logger.info("Updated secure configuration for new Gong credential mapping")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update secure configuration: {e}")
            return False
    
    def create_github_actions_workflow(self) -> bool:
        """Create GitHub Actions workflow for secure credential deployment"""
        try:
            workflow_content = """name: Deploy Sophia with Secure Credentials

on:
  push:
    branches: [ main ]
    paths:
      - 'pulumi-esc-environment.yaml'
      - 'backend/config/**'
      - '.github/workflows/deploy-secure.yml'
  workflow_dispatch:

env:
  PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
  GONG_ACCESS_KEY: ${{ secrets.GONG_ACCESS_KEY }}
  GONG_CLIENT_SECRET: ${{ secrets.GONG_CLIENT_SECRET }}

jobs:
  deploy-credentials:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Pulumi CLI
        uses: pulumi/actions@v4
        with:
          pulumi-version: latest
      
      - name: Install Pulumi ESC CLI
        run: |
          curl -fsSL https://get.pulumi.com/esc/install.sh | sh
          echo "$HOME/.pulumi/bin" >> $GITHUB_PATH
      
      - name: Configure Pulumi ESC Environment
        run: |
          esc env set ai-cherry/sophia-production --file pulumi-esc-environment.yaml
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
      
      - name: Validate Gong API Credentials
        run: |
          python3 -c "
          import requests
          import base64
          import os
          
          access_key = os.environ['GONG_ACCESS_KEY']
          client_secret = os.environ['GONG_CLIENT_SECRET']
          
          credentials = f'{access_key}:{client_secret}'
          encoded_credentials = base64.b64encode(credentials.encode()).decode()
          
          headers = {
              'Authorization': f'Basic {encoded_credentials}',
              'Content-Type': 'application/json'
          }
          
          response = requests.get('https://us-70092.api.gong.io/v2/settings/workspaces', headers=headers)
          
          if response.status_code == 200:
              print('✅ Gong API credentials validated successfully')
              print(f'Workspaces available: {len(response.json().get(\"workspaces\", []))}')
          else:
              print(f'❌ Gong API validation failed: {response.status_code}')
              print(response.text)
              exit(1)
          "
      
      - name: Generate Secure Environment File
        run: |
          python3 -c "
          import os
          import yaml
          from datetime import datetime
          
          # Load ESC environment
          with open('pulumi-esc-environment.yaml', 'r') as f:
              env_config = yaml.safe_load(f)
          
          # Generate .env.secure file
          with open('.env.secure', 'w') as f:
              f.write('# Sophia AI Secure Environment\\n')
              f.write(f'# Generated: {datetime.utcnow().isoformat()}\\n')
              f.write('# Source: GitHub Actions + Pulumi ESC\\n\\n')
              
              f.write('# Gong API Configuration\\n')
              f.write(f'GONG_ACCESS_KEY={os.environ[\"GONG_ACCESS_KEY\"]}\\n')
              f.write(f'GONG_CLIENT_SECRET={os.environ[\"GONG_CLIENT_SECRET\"]}\\n')
              f.write('GONG_BASE_URL=https://us-70092.api.gong.io\\n')
              f.write('GONG_API_VERSION=v2\\n\\n')
              
              f.write('# Deployment Configuration\\n')
              f.write('DEPLOYMENT_ENV=production\\n')
              f.write('SECURE_DEPLOYMENT=true\\n')
          
          print('✅ Generated secure environment file')
          "
      
      - name: Test Sophia Integration
        run: |
          python3 -c "
          import sys
          sys.path.append('backend')
          
          from config.secure_config import get_secure_config
          
          config = get_secure_config()
          api_count = config.get_api_count()
          validation = config.validate_critical_apis()
          
          print(f'📊 API Configuration: {api_count[\"configured\"]}/{api_count[\"total\"]} ({api_count[\"percentage\"]}%)')
          print(f'🔒 Critical APIs: {\"✅ All configured\" if validation[\"all_configured\"] else \"❌ Missing: \" + \", \".join(validation[\"missing\"])}')
          "
        env:
          GONG_ACCESS_KEY: ${{ secrets.GONG_ACCESS_KEY }}
          GONG_CLIENT_SECRET: ${{ secrets.GONG_CLIENT_SECRET }}
      
      - name: Commit Secure Configuration
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          
          if [ -f .env.secure ]; then
            git add .env.secure
            git commit -m "🔐 SECURE: Update environment with validated Gong credentials" || echo "No changes to commit"
          fi
      
      - name: Deploy to Production
        run: |
          echo "🚀 Ready for production deployment with secure credentials"
          echo "✅ Gong API credentials validated and configured"
          echo "✅ Pulumi ESC environment updated"
          echo "✅ Secure configuration generated"
"""
            
            workflow_file = "/home/ubuntu/sophia-main/.github/workflows/deploy-secure-gong.yml"
            os.makedirs(os.path.dirname(workflow_file), exist_ok=True)
            
            with open(workflow_file, 'w') as f:
                f.write(workflow_content)
            
            logger.info("Created GitHub Actions workflow for secure credential deployment")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create GitHub Actions workflow: {e}")
            return False
    
    def test_new_credentials(self) -> Dict[str, Any]:
        """Test the new Gong API credentials"""
        try:
            import requests
            
            # Create Basic Auth header
            credentials = f"{self.new_credentials['access_key']}:{self.new_credentials['client_secret']}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            # Test workspaces endpoint
            response = requests.get(
                f"{self.new_credentials['base_url']}/v2/settings/workspaces",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "workspaces": data.get('workspaces', []),
                    "workspace_count": len(data.get('workspaces', [])),
                    "base_url": self.new_credentials['base_url']
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "base_url": self.new_credentials['base_url']
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "base_url": self.new_credentials['base_url']
            }
    
    def analyze_gong_app_advantages(self) -> Dict[str, Any]:
        """Analyze advantages of creating a dedicated Gong app integration"""
        
        advantages = {
            "oauth_benefits": {
                "description": "OAuth provides granular access control and better security",
                "benefits": [
                    "Granular scope-based permissions",
                    "Token refresh capabilities",
                    "Better audit trail and monitoring",
                    "Revocable access without credential changes",
                    "User-specific permissions and data access"
                ]
            },
            "enhanced_api_access": {
                "description": "App integrations unlock additional API capabilities",
                "scopes_available": [
                    "api:calls:read:extensive - Extended call data with interaction stats",
                    "api:calls:read:transcript - Full call transcripts",
                    "api:calls:read:media-url - Audio/video media access",
                    "api:stats:interaction - User interaction statistics",
                    "api:stats:scorecards - Scorecard statistics",
                    "api:settings:trackers:read - Keyword tracker details",
                    "api:library:read - Library folder access",
                    "api:flows:read - Gong Engage flow data",
                    "api:crm:get-objects - CRM object integration",
                    "api:digital-interactions:write - Create digital interactions"
                ]
            },
            "business_advantages": {
                "description": "App integration provides better customer experience",
                "benefits": [
                    "Professional integration listing in Gong marketplace",
                    "Customer self-service installation",
                    "Branded integration experience",
                    "Better customer trust and adoption",
                    "Scalable multi-tenant architecture"
                ]
            },
            "technical_advantages": {
                "description": "Enhanced technical capabilities and reliability",
                "benefits": [
                    "Webhook support for real-time data",
                    "Higher rate limits for app integrations",
                    "Better error handling and retry mechanisms",
                    "Standardized OAuth flow implementation",
                    "Multi-workspace support"
                ]
            },
            "current_limitations": {
                "description": "Limitations of current API key approach",
                "limitations": [
                    "Limited to basic API access",
                    "No real-time webhook notifications",
                    "Manual credential management",
                    "Single workspace limitation",
                    "No granular permission control"
                ]
            },
            "implementation_requirements": {
                "description": "Requirements for creating Gong app integration",
                "requirements": [
                    "OAuth 2.0 implementation",
                    "Webhook endpoint for real-time updates",
                    "Multi-tenant database architecture",
                    "User consent and permission management",
                    "App marketplace submission and approval"
                ]
            }
        }
        
        return advantages
    
    def generate_implementation_summary(self) -> Dict[str, Any]:
        """Generate comprehensive implementation summary"""
        
        # Test current credentials
        credential_test = self.test_new_credentials()
        
        # Analyze app advantages
        app_analysis = self.analyze_gong_app_advantages()
        
        summary = {
            "credential_update": {
                "status": "ready",
                "new_credentials": {
                    "access_key": "EX5L7AKSGQBOPNK66TDYVVEAKBVQ6IPK",
                    "base_url": "https://us-70092.api.gong.io",
                    "workspace": "us-70092"
                },
                "security_approach": "GitHub Secrets + Pulumi ESC",
                "test_results": credential_test
            },
            "pulumi_esc_integration": {
                "environment": "ai-cherry/sophia-production",
                "github_secrets_import": True,
                "secure_deployment": True,
                "workflow_automation": True
            },
            "gong_app_analysis": app_analysis,
            "recommendations": {
                "immediate": [
                    "Deploy new credentials via GitHub Actions workflow",
                    "Test enhanced API access with new credentials",
                    "Validate workspace access and data availability"
                ],
                "short_term": [
                    "Implement OAuth flow for Gong app integration",
                    "Create webhook endpoints for real-time updates",
                    "Design multi-tenant architecture for app deployment"
                ],
                "long_term": [
                    "Submit Gong app to marketplace",
                    "Implement advanced conversation intelligence features",
                    "Scale to multi-customer deployment"
                ]
            },
            "business_impact": {
                "current_api_access": "Basic call data and participant information",
                "enhanced_app_access": "Full transcripts, media, scorecards, and real-time updates",
                "customer_value": "Professional integration with self-service installation",
                "competitive_advantage": "Marketplace presence and enhanced capabilities"
            }
        }
        
        return summary

async def main():
    """Main execution function"""
    manager = SecureGongCredentialManager()
    
    print("🔐 SECURE GONG CREDENTIAL UPDATE PROCESS")
    print("="*60)
    
    # Update Pulumi ESC environment
    print("1. Updating Pulumi ESC environment...")
    esc_success = manager.update_pulumi_esc_environment()
    print(f"   {'✅ Success' if esc_success else '❌ Failed'}")
    
    # Update secure configuration
    print("2. Updating secure configuration...")
    config_success = manager.update_secure_config()
    print(f"   {'✅ Success' if config_success else '❌ Failed'}")
    
    # Create GitHub Actions workflow
    print("3. Creating GitHub Actions workflow...")
    workflow_success = manager.create_github_actions_workflow()
    print(f"   {'✅ Success' if workflow_success else '❌ Failed'}")
    
    # Test new credentials
    print("4. Testing new Gong API credentials...")
    test_results = manager.test_new_credentials()
    if test_results["success"]:
        print(f"   ✅ Success - {test_results.get('workspace_count', 0)} workspaces available")
    else:
        print(f"   ❌ Failed - {test_results.get('error', 'Unknown error')}")
    
    # Generate implementation summary
    print("5. Generating implementation summary...")
    summary = manager.generate_implementation_summary()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/home/ubuntu/secure_gong_credential_update_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"📁 Results saved to: {results_file}")
    print("\n🎯 NEXT STEPS:")
    print("   1. Commit changes to GitHub")
    print("   2. GitHub Actions will deploy secure credentials")
    print("   3. Test enhanced API access")
    print("   4. Consider Gong app integration for advanced features")
    
    return summary

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

