"""
Sophia AI - Pulumi ESC Integration Module
Centralized secrets and configuration management for Pay Ready operations
"""

import os
import json
import subprocess
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ESCConfig:
    """Configuration for Pulumi ESC integration"""
    environment_name: str = "sophia-ai/sophia-production"
    project_name: str = "sophia-ai"
    organization: str = "scoobyjava-org"

class SophiaESCManager:
    """
    Pulumi ESC integration for Sophia AI
    Provides centralized secrets and configuration management
    """
    
    def __init__(self, config: ESCConfig = None):
        self.config = config or ESCConfig()
        self.environment_path = f"{self.config.organization}/{self.config.environment_name}"
        
    def get_environment_values(self) -> Dict[str, Any]:
        """Retrieve all environment values from Pulumi ESC"""
        try:
            result = subprocess.run(
                ["esc", "env", "get", self.environment_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the YAML output - handle the specific ESC output format
            import yaml
            
            # ESC output includes metadata, we need to extract just the values
            lines = result.stdout.strip().split('\n')
            yaml_content = []
            in_values_section = False
            
            for line in lines:
                if line.strip().startswith('values:'):
                    in_values_section = True
                    yaml_content.append(line)
                elif in_values_section:
                    yaml_content.append(line)
            
            if yaml_content:
                yaml_str = '\n'.join(yaml_content)
                env_data = yaml.safe_load(yaml_str)
                return env_data.get('values', {}) if env_data else {}
            else:
                # Fallback: try to parse the entire output
                env_data = yaml.safe_load(result.stdout)
                return env_data.get('values', {}) if isinstance(env_data, dict) else {}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get ESC environment: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing ESC environment: {e}")
            return {}
    
    def get_secret(self, key_path: str) -> Optional[str]:
        """
        Get a specific secret value from the environment
        
        Args:
            key_path: Dot-separated path to the secret (e.g., 'database.password')
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
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration from ESC"""
        values = self.get_environment_values()
        return values.get('database', {})
    
    def get_ai_service_config(self) -> Dict[str, Any]:
        """Get AI service configuration (OpenAI, Anthropic, HuggingFace)"""
        values = self.get_environment_values()
        return {
            'openai': values.get('openai', {}),
            'anthropic': values.get('anthropic', {}),
            'huggingface': values.get('huggingface', {})
        }
    
    def get_business_integration_config(self) -> Dict[str, Any]:
        """Get business integration configuration (Gong, Salesforce, Slack)"""
        values = self.get_environment_values()
        return {
            'gong': values.get('gong', {}),
            'salesforce': values.get('salesforce', {}),
            'slack': values.get('slack', {})
        }
    
    def get_vector_database_config(self) -> Dict[str, Any]:
        """Get vector database configuration (Pinecone, Weaviate)"""
        values = self.get_environment_values()
        return {
            'pinecone': values.get('pinecone', {}),
            'weaviate': values.get('weaviate', {})
        }
    
    def run_with_environment(self, command: list) -> subprocess.CompletedProcess:
        """
        Run a command with ESC environment variables injected
        
        Args:
            command: Command to run as a list of strings
        """
        try:
            # Use esc run to inject environment variables
            esc_command = ["esc", "run", self.environment_path, "--"] + command
            
            result = subprocess.run(
                esc_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Command executed successfully with ESC environment")
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with ESC environment: {e}")
            raise
    
    def update_local_env_file(self, env_file_path: str = ".env") -> bool:
        """
        Update local .env file with values from ESC environment
        Useful for development and testing
        """
        try:
            values = self.get_environment_values()
            
            # Flatten the nested configuration for .env format
            env_vars = self._flatten_config(values)
            
            # Write to .env file
            with open(env_file_path, 'w') as f:
                f.write("# Sophia AI Environment Configuration\n")
                f.write("# Generated from Pulumi ESC\n\n")
                
                for key, value in env_vars.items():
                    # Skip complex objects, only write simple values
                    if isinstance(value, (str, int, float, bool)):
                        f.write(f"{key}={value}\n")
            
            logger.info(f"Updated {env_file_path} with ESC environment values")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
            return False
    
    def _flatten_config(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested configuration dictionary for .env format"""
        flattened = {}
        
        for key, value in config.items():
            new_key = f"{prefix}_{key}".upper() if prefix else key.upper()
            
            if isinstance(value, dict):
                # Skip secret objects, only process regular nested dicts
                if 'fn::secret' not in value:
                    flattened.update(self._flatten_config(value, new_key))
            else:
                flattened[new_key] = value
        
        return flattened
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate that all required configuration is present"""
        validation_results = {}
        
        try:
            values = self.get_environment_values()
            
            # Check required sections
            required_sections = [
                'app', 'database', 'redis', 'pinecone', 'weaviate',
                'openai', 'huggingface', 'monitoring', 'security'
            ]
            
            for section in required_sections:
                validation_results[section] = section in values and bool(values[section])
            
            # Check specific required keys
            required_keys = [
                'database.host',
                'database.name',
                'pinecone.api_key',
                'weaviate.url',
                'openai.api_key',
                'huggingface.api_key'
            ]
            
            for key_path in required_keys:
                validation_results[key_path] = self.get_secret(key_path) is not None
            
            logger.info(f"Environment validation completed: {validation_results}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return {}

# Flask integration for ESC
from flask import Blueprint, jsonify, request

esc_bp = Blueprint('esc', __name__, url_prefix='/api/esc')

# Initialize ESC manager
sophia_esc = SophiaESCManager()

@esc_bp.route('/config')
def get_config():
    """Get non-sensitive configuration values"""
    try:
        values = sophia_esc.get_environment_values()
        
        # Remove sensitive data before returning
        safe_config = {}
        for key, value in values.items():
            if key not in ['database', 'openai', 'anthropic', 'huggingface', 'slack', 'gong', 'salesforce']:
                safe_config[key] = value
        
        return jsonify({
            'status': 'success',
            'config': safe_config
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@esc_bp.route('/validate')
def validate_environment():
    """Validate environment configuration"""
    try:
        validation_results = sophia_esc.validate_environment()
        
        all_valid = all(validation_results.values())
        
        return jsonify({
            'status': 'success',
            'valid': all_valid,
            'results': validation_results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@esc_bp.route('/health')
def esc_health():
    """Check ESC integration health"""
    try:
        # Test basic ESC connectivity
        values = sophia_esc.get_environment_values()
        
        return jsonify({
            'status': 'healthy',
            'esc_connected': bool(values),
            'environment': sophia_esc.environment_path,
            'config_sections': list(values.keys()) if values else []
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Example usage
def main():
    """Example usage of Sophia ESC integration"""
    esc_manager = SophiaESCManager()
    
    # Get database configuration
    db_config = esc_manager.get_database_config()
    print(f"Database host: {db_config.get('host')}")
    
    # Get AI service configuration
    ai_config = esc_manager.get_ai_service_config()
    print(f"AI services configured: {list(ai_config.keys())}")
    
    # Validate environment
    validation = esc_manager.validate_environment()
    print(f"Environment valid: {all(validation.values())}")
    
    # Update local .env file for development
    esc_manager.update_local_env_file()

if __name__ == "__main__":
    main()

