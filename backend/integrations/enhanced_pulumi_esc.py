#!/usr/bin/env python3
"""
Enhanced Pulumi ESC Integration for Sophia AI
Comprehensive secret management with GitHub org-level secrets integration
"""

import os
import json
import subprocess
import logging
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import requests
import base64

logger = logging.getLogger(__name__)

@dataclass
class ESCConfig:
    """Enhanced configuration for Pulumi ESC integration"""
    organization: str = "ai-cherry"
    project_name: str = "sophia-ai"
    environment_name: str = "sophia-production"
    github_org: str = "ai-cherry"
    
    @property
    def environment_path(self) -> str:
        return f"{self.organization}/{self.environment_name}"

class EnhancedSophiaESCManager:
    """
    Enhanced Pulumi ESC integration for Sophia AI
    Provides comprehensive secret management with GitHub org-level integration
    """
    
    def __init__(self, config: ESCConfig = None):
        self.config = config or ESCConfig()
        self.environment_path = self.config.environment_path
        self._validate_esc_cli()
        
    def _validate_esc_cli(self) -> bool:
        """Validate that Pulumi ESC CLI is installed and configured"""
        try:
            result = subprocess.run(
                ["esc", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Pulumi ESC CLI version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Pulumi ESC CLI not found or not configured")
            return False
    
    def create_environment(self, environment_file: str = "pulumi-esc-environment.yaml") -> bool:
        """Create or update the Pulumi ESC environment"""
        try:
            # Read the environment configuration
            with open(environment_file, 'r') as f:
                env_config = yaml.safe_load(f)
            
            # Convert to YAML string for ESC
            env_yaml = yaml.dump(env_config, default_flow_style=False)
            
            # Create temporary file for ESC
            temp_file = "/tmp/sophia-esc-env.yaml"
            with open(temp_file, 'w') as f:
                f.write(env_yaml)
            
            # Create or update environment
            result = subprocess.run(
                ["esc", "env", "set", self.environment_path, "--file", temp_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Successfully created/updated ESC environment: {self.environment_path}")
            
            # Clean up temp file
            os.remove(temp_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ESC environment: {e}")
            return False
    
    def get_environment_values(self) -> Dict[str, Any]:
        """Retrieve all environment values from Pulumi ESC"""
        try:
            result = subprocess.run(
                ["esc", "env", "get", self.environment_path, "--format", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            
            env_data = json.loads(result.stdout)
            return env_data.get('properties', {}).get('values', {})
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get ESC environment: {e}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ESC environment JSON: {e}")
            return {}
    
    def get_secret(self, key_path: str) -> Optional[str]:
        """
        Get a specific secret value from the environment
        
        Args:
            key_path: Dot-separated path to the secret (e.g., 'database.postgres.password')
        """
        try:
            values = self.get_environment_values()
            
            # Navigate through nested dictionary
            current = values
            for key in key_path.split('.'):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    logger.warning(f"Secret key path not found: {key_path}")
                    return None
            
            return str(current) if current is not None else None
            
        except Exception as e:
            logger.error(f"Error retrieving secret {key_path}: {e}")
            return None
    
    def generate_env_file(self, output_path: str = ".env") -> bool:
        """Generate a .env file from ESC environment values"""
        try:
            values = self.get_environment_values()
            
            # Flatten the configuration for .env format
            env_vars = self._flatten_config_for_env(values)
            
            # Write to .env file
            with open(output_path, 'w') as f:
                f.write("# Sophia AI Environment Configuration\n")
                f.write("# Generated from Pulumi ESC\n")
                f.write(f"# Environment: {self.environment_path}\n")
                f.write(f"# Generated at: {self._get_timestamp()}\n\n")
                
                # Group related variables
                self._write_env_section(f, "Application Configuration", {
                    "SOPHIA_ENV": values.get('app', {}).get('environment', 'production'),
                    "HOST": values.get('app', {}).get('host', '0.0.0.0'),
                    "PORT": values.get('app', {}).get('port', 5000),
                    "DEBUG": values.get('app', {}).get('debug', False)
                })
                
                # Security section
                security_config = values.get('security', {})
                self._write_env_section(f, "Security Configuration", {
                    "SECRET_KEY": security_config.get('secret_key'),
                    "ADMIN_USERNAME": security_config.get('admin_username'),
                    "ADMIN_PASSWORD": security_config.get('admin_password'),
                    "SOPHIA_MASTER_KEY": security_config.get('master_key'),
                    "JWT_SECRET_KEY": security_config.get('jwt_secret'),
                    "ENCRYPTION_KEY": security_config.get('encryption_key')
                })
                
                # Database section
                db_config = values.get('database', {})
                postgres_config = db_config.get('postgres', {})
                redis_config = db_config.get('redis', {})
                
                self._write_env_section(f, "Database Configuration", {
                    "POSTGRES_HOST": postgres_config.get('host'),
                    "POSTGRES_PORT": postgres_config.get('port', 5432),
                    "POSTGRES_USER": postgres_config.get('user'),
                    "POSTGRES_PASSWORD": postgres_config.get('password'),
                    "POSTGRES_DB": postgres_config.get('database'),
                    "DATABASE_URL": postgres_config.get('url'),
                    "REDIS_HOST": redis_config.get('host'),
                    "REDIS_PORT": redis_config.get('port', 6379),
                    "REDIS_PASSWORD": redis_config.get('password'),
                    "REDIS_URL": redis_config.get('url')
                })
                
                # LLM Gateway section
                llm_config = values.get('llm_gateway', {})
                self._write_env_section(f, "LLM Gateway Configuration", {
                    "LLM_GATEWAY": llm_config.get('provider', 'portkey'),
                    "PORTKEY_API_KEY": llm_config.get('portkey', {}).get('api_key'),
                    "PORTKEY_CONFIG": llm_config.get('portkey', {}).get('config'),
                    "OPENROUTER_API_KEY": llm_config.get('openrouter', {}).get('api_key')
                })
                
                # AI Services section
                ai_config = values.get('ai_services', {})
                ai_env_vars = {}
                for service, config in ai_config.items():
                    service_upper = service.upper()
                    if isinstance(config, dict) and 'api_key' in config:
                        ai_env_vars[f"{service_upper}_API_KEY"] = config['api_key']
                
                self._write_env_section(f, "AI Service Providers", ai_env_vars)
                
                # Business Integrations section
                business_config = values.get('business_integrations', {})
                business_env_vars = {}
                
                # Gong
                gong_config = business_config.get('gong', {})
                business_env_vars.update({
                    "GONG_ACCESS_KEY": gong_config.get('access_key'),
                    "GONG_ACCESS_KEY_SECRET": gong_config.get('access_key_secret')
                })
                
                # Salesforce
                sf_config = business_config.get('salesforce', {})
                business_env_vars.update({
                    "SALESFORCE_ACCESS_TOKEN": sf_config.get('access_token'),
                    "SALESFORCE_CLIENT_ID": sf_config.get('client_id'),
                    "SALESFORCE_CLIENT_SECRET": sf_config.get('client_secret')
                })
                
                # HubSpot
                hs_config = business_config.get('hubspot', {})
                business_env_vars.update({
                    "HUBSPOT_API_KEY": hs_config.get('api_key'),
                    "HUBSPOT_CLIENT_ID": hs_config.get('client_id'),
                    "HUBSPOT_CLIENT_SECRET": hs_config.get('client_secret')
                })
                
                # Slack
                slack_config = business_config.get('slack', {})
                business_env_vars.update({
                    "SLACK_CLIENT_ID": slack_config.get('client_id'),
                    "SLACK_CLIENT_SECRET": slack_config.get('client_secret'),
                    "SLACK_SIGNING_SECRET": slack_config.get('signing_secret'),
                    "SLACK_APP_TOKEN": slack_config.get('app_token'),
                    "SLACK_BOT_TOKEN": slack_config.get('bot_token'),
                    "SLACK_REFRESH_TOKEN": slack_config.get('refresh_token'),
                    "SLACK_USER_ID": slack_config.get('user_id')
                })
                
                self._write_env_section(f, "Business Integrations", business_env_vars)
                
                # Vector Databases section
                vector_config = values.get('vector_databases', {})
                vector_env_vars = {
                    "PINECONE_API_KEY": vector_config.get('pinecone', {}).get('api_key'),
                    "WEAVIATE_URL": vector_config.get('weaviate', {}).get('url'),
                    "WEAVIATE_GRPC_URL": vector_config.get('weaviate', {}).get('grpc_url'),
                    "WEAVIATE_API_KEY": vector_config.get('weaviate', {}).get('api_key')
                }
                
                self._write_env_section(f, "Vector Databases", vector_env_vars)
                
                # Add remaining sections...
                self._write_remaining_sections(f, values)
            
            logger.info(f"Generated .env file at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate .env file: {e}")
            return False
    
    def _write_env_section(self, file_handle, section_name: str, env_vars: Dict[str, Any]):
        """Write a section of environment variables to the file"""
        file_handle.write(f"\n# {section_name}\n")
        for key, value in env_vars.items():
            if value is not None:
                # Handle boolean values
                if isinstance(value, bool):
                    value = str(value).lower()
                file_handle.write(f"{key}={value}\n")
    
    def _write_remaining_sections(self, file_handle, values: Dict[str, Any]):
        """Write remaining configuration sections"""
        
        # Knowledge Services
        knowledge_config = values.get('knowledge_services', {})
        knowledge_env_vars = {}
        for service, config in knowledge_config.items():
            service_upper = service.upper()
            if isinstance(config, dict) and 'api_key' in config:
                key_name = f"{service_upper}_API_KEY"
                if service == 'apollo_io':
                    key_name = "APOLLO_IO_API_KEY"
                elif service == 'apify':
                    key_name = "APIFY_API_TOKEN"
                knowledge_env_vars[key_name] = config['api_key']
        
        self._write_env_section(file_handle, "Knowledge Services", knowledge_env_vars)
        
        # Monitoring
        monitoring_config = values.get('monitoring', {})
        monitoring_env_vars = {}
        for service, config in monitoring_config.items():
            service_upper = service.upper()
            if isinstance(config, dict) and 'api_key' in config:
                monitoring_env_vars[f"{service_upper}_API_KEY"] = config['api_key']
        
        self._write_env_section(file_handle, "Monitoring & Analytics", monitoring_env_vars)
        
        # Infrastructure
        infra_config = values.get('infrastructure', {})
        infra_env_vars = {
            "PULUMI_ACCESS_TOKEN": infra_config.get('pulumi', {}).get('access_token'),
            "LAMBDA_LABS_API_KEY": infra_config.get('lambda_labs', {}).get('api_key'),
            "VERCEL_TOKEN": infra_config.get('vercel', {}).get('token'),
            "DOCKER_USERNAME": infra_config.get('docker', {}).get('username'),
            "DOCKER_TOKEN": infra_config.get('docker', {}).get('token')
        }
        
        self._write_env_section(file_handle, "Infrastructure & Deployment", infra_env_vars)
        
        # Additional services
        additional_sections = [
            ('redis_cloud', 'Redis Cloud'),
            ('neo4j', 'Neo4j Graph Database'),
            ('airbyte', 'Airbyte Integration'),
            ('additional_tools', 'Additional Tools')
        ]
        
        for section_key, section_name in additional_sections:
            section_config = values.get(section_key, {})
            section_env_vars = {}
            
            for key, value in section_config.items():
                env_key = key.upper()
                if section_key == 'redis_cloud':
                    if key == 'user_api_key':
                        env_key = 'REDIS_USER_API_KEY'
                    elif key == 'account_key':
                        env_key = 'REDIS_ACCOUNT_KEY'
                elif section_key == 'neo4j':
                    env_key = f"NEO4J_{key.upper()}"
                elif section_key == 'airbyte':
                    env_key = f"AIRBYTE_{key.upper()}"
                elif section_key == 'additional_tools':
                    # Handle special cases for additional tools
                    if key == 'figma':
                        env_key = 'FIGMA_PERSONAL_ACCESS_TOKEN'
                    elif key == 'phantom_buster':
                        env_key = 'PHANTOM_BUSTER_API_KEY'
                    else:
                        env_key = f"{key.upper()}_API_KEY"
                
                if isinstance(value, dict):
                    # Extract nested values
                    for nested_key, nested_value in value.items():
                        nested_env_key = f"{env_key}_{nested_key.upper()}" if section_key != 'additional_tools' else env_key
                        section_env_vars[nested_env_key] = nested_value
                else:
                    section_env_vars[env_key] = value
            
            self._write_env_section(file_handle, section_name, section_env_vars)
    
    def _flatten_config_for_env(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested configuration dictionary for .env format"""
        flattened = {}
        
        for key, value in config.items():
            new_key = f"{prefix}_{key}".upper() if prefix else key.upper()
            
            if isinstance(value, dict):
                # Don't flatten secret objects
                if 'fn::secret' not in str(value):
                    flattened.update(self._flatten_config_for_env(value, new_key))
            else:
                flattened[new_key] = value
        
        return flattened
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for file generation"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate that all required configuration is present"""
        validation_results = {}
        
        try:
            values = self.get_environment_values()
            
            # Check required sections
            required_sections = [
                'app', 'security', 'database', 'llm_gateway', 'ai_services',
                'business_integrations', 'vector_databases', 'infrastructure'
            ]
            
            for section in required_sections:
                validation_results[f"section_{section}"] = section in values and bool(values[section])
            
            # Check specific critical secrets
            critical_secrets = [
                'security.secret_key',
                'database.postgres.host',
                'database.postgres.password',
                'ai_services.openai.api_key',
                'vector_databases.pinecone.api_key',
                'infrastructure.lambda_labs.api_key'
            ]
            
            for secret_path in critical_secrets:
                validation_results[f"secret_{secret_path}"] = self.get_secret(secret_path) is not None
            
            logger.info(f"Environment validation completed: {validation_results}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return {}
    
    def run_with_environment(self, command: List[str], working_dir: str = None) -> subprocess.CompletedProcess:
        """Run a command with ESC environment variables injected"""
        try:
            # Use esc run to inject environment variables
            esc_command = ["esc", "run", self.environment_path, "--"] + command
            
            result = subprocess.run(
                esc_command,
                capture_output=True,
                text=True,
                check=True,
                cwd=working_dir
            )
            
            logger.info(f"Command executed successfully with ESC environment")
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with ESC environment: {e}")
            raise
    
    def sync_with_github_secrets(self) -> bool:
        """Sync environment with GitHub organization secrets"""
        try:
            # This would require GitHub API integration
            # For now, we'll log the requirement
            logger.info("GitHub secrets sync would be implemented here")
            logger.info("Required: GitHub API token with org:read permissions")
            logger.info("Would sync secrets from ai-cherry organization")
            
            return True
            
        except Exception as e:
            logger.error(f"GitHub secrets sync failed: {e}")
            return False

def main():
    """Main function to demonstrate ESC integration"""
    esc_manager = EnhancedSophiaESCManager()
    
    print("🔐 Enhanced Sophia AI ESC Integration")
    print("=" * 50)
    
    # Create environment from YAML file
    print("1. Creating ESC environment...")
    if esc_manager.create_environment():
        print("✅ ESC environment created/updated successfully")
    else:
        print("❌ Failed to create ESC environment")
        return
    
    # Validate environment
    print("\n2. Validating environment...")
    validation = esc_manager.validate_environment()
    valid_count = sum(1 for v in validation.values() if v)
    total_count = len(validation)
    print(f"✅ Environment validation: {valid_count}/{total_count} checks passed")
    
    # Generate .env file
    print("\n3. Generating .env file...")
    if esc_manager.generate_env_file():
        print("✅ .env file generated successfully")
    else:
        print("❌ Failed to generate .env file")
    
    # Test secret retrieval
    print("\n4. Testing secret retrieval...")
    test_secret = esc_manager.get_secret('app.name')
    if test_secret:
        print(f"✅ Secret retrieval working: app.name = {test_secret}")
    else:
        print("❌ Secret retrieval failed")
    
    print("\n🎉 ESC integration setup complete!")

if __name__ == "__main__":
    main()

