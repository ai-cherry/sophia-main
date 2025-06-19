#!/usr/bin/env python3
"""
Sophia AI - Secret Rotation Framework
This script provides a framework for automated secret rotation for various services.
"""

import os
import json
import logging
import datetime
import time
import random
import string
import argparse
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecretRotator(ABC):
    """
    Abstract base class for secret rotators
    """
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.config = config
        self.rotation_schedule = config.get("rotation_schedule", "90d")
        self.secret_keys = config.get("secret_keys", [])
        self.config_keys = config.get("config_keys", [])
        self.owner = config.get("owner", "")
        self.description = config.get("description", "")
        self.last_rotation = {}
        self.next_rotation = {}
    
    def should_rotate(self, key: str) -> bool:
        """Check if a secret should be rotated"""
        # Get last rotation time
        last_rotation = self.last_rotation.get(key)
        if not last_rotation:
            # If no last rotation time, assume it should be rotated
            return True
        
        # Parse rotation schedule
        schedule = self.rotation_schedule
        if schedule.endswith("d"):
            days = int(schedule[:-1])
            next_rotation = last_rotation + datetime.timedelta(days=days)
        elif schedule.endswith("h"):
            hours = int(schedule[:-1])
            next_rotation = last_rotation + datetime.timedelta(hours=hours)
        else:
            # Default to 90 days
            next_rotation = last_rotation + datetime.timedelta(days=90)
        
        # Store next rotation time
        self.next_rotation[key] = next_rotation
        
        # Check if it's time to rotate
        return datetime.datetime.now() >= next_rotation
    
    def generate_password(self, length: int = 32, include_special: bool = True) -> str:
        """Generate a secure random password"""
        chars = string.ascii_letters + string.digits
        if include_special:
            chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_api_key(self, length: int = 40, prefix: str = "") -> str:
        """Generate a secure random API key"""
        chars = string.ascii_letters + string.digits
        
        if prefix:
            return prefix + ''.join(random.choice(chars) for _ in range(length - len(prefix)))
        else:
            return ''.join(random.choice(chars) for _ in range(length))
    
    @abstractmethod
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """
        Rotate a secret
        
        Returns:
            Tuple[bool, Optional[str]]: (success, new_value)
        """
        pass
    
    def rotate_all_secrets(self, dry_run: bool = False) -> Dict[str, Any]:
        """Rotate all secrets for this service"""
        results = {
            "service": self.service_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "dry_run": dry_run,
            "rotated": [],
            "skipped": [],
            "failed": [],
            "errors": []
        }
        
        for key in self.secret_keys:
            try:
                if self.should_rotate(key):
                    if not dry_run:
                        success, new_value = self.rotate_secret(key)
                        if success:
                            self.last_rotation[key] = datetime.datetime.now()
                            results["rotated"].append(key)
                            
                            # Update Pulumi ESC and GitHub with new value
                            self.update_secret_stores(key, new_value)
                        else:
                            results["failed"].append(key)
                            results["errors"].append(f"Failed to rotate {key} for {self.service_name}")
                    else:
                        logger.info(f"Would rotate {key} for {self.service_name} (dry run)")
                        results["rotated"].append(key)
                else:
                    results["skipped"].append(key)
            except Exception as e:
                results["failed"].append(key)
                error_message = f"Failed to rotate {key} for {self.service_name}: {str(e)}"
                results["errors"].append(error_message)
                logger.error(error_message)
        
        return results
    
    def update_secret_stores(self, key: str, value: str) -> bool:
        """Update Pulumi ESC and GitHub with new secret value"""
        try:
            # Update Pulumi ESC
            pulumi_key = f"{self.service_name}_{key}"
            group = "api-keys"
            if key in ["password", "user", "username"]:
                group = "database-credentials"
            elif key in ["token", "private_key"]:
                group = "security-tokens"
            
            # In a real implementation, this would call the Pulumi API to set the secret value
            logger.info(f"Updating Pulumi ESC secret {pulumi_key} in group {group}")
            
            # Update GitHub
            github_key = f"{self.service_name.upper()}_{key.upper()}"
            
            # In a real implementation, this would call the GitHub API to set the secret value
            logger.info(f"Updating GitHub secret {github_key}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to update secret stores for {key}: {str(e)}")
            return False


class SnowflakeRotator(SecretRotator):
    """Rotator for Snowflake credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("snowflake", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate a Snowflake secret"""
        try:
            if key == "password":
                # Generate a new password
                new_password = self.generate_password(length=24, include_special=True)
                
                # In a real implementation, this would call the Snowflake API to update the password
                logger.info(f"Rotating Snowflake password")
                
                return True, new_password
            else:
                logger.warning(f"Rotation not implemented for Snowflake {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Snowflake {key}: {str(e)}")
            return False, None


class GongRotator(SecretRotator):
    """Rotator for Gong API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("gong", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate a Gong secret"""
        try:
            if key == "api_key":
                # Generate a new API key
                new_api_key = self.generate_api_key(length=40, prefix="gong_")
                
                # In a real implementation, this would call the Gong API to update the API key
                logger.info(f"Rotating Gong API key")
                
                return True, new_api_key
            elif key == "api_secret" or key == "client_secret":
                # Generate a new secret
                new_secret = self.generate_api_key(length=64)
                
                # In a real implementation, this would call the Gong API to update the secret
                logger.info(f"Rotating Gong {key}")
                
                return True, new_secret
            else:
                logger.warning(f"Rotation not implemented for Gong {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Gong {key}: {str(e)}")
            return False, None


class VercelRotator(SecretRotator):
    """Rotator for Vercel API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("vercel", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate a Vercel secret"""
        try:
            if key == "token":
                # Generate a new token
                new_token = self.generate_api_key(length=32, prefix="vercel_")
                
                # In a real implementation, this would call the Vercel API to update the token
                logger.info(f"Rotating Vercel token")
                
                return True, new_token
            else:
                logger.warning(f"Rotation not implemented for Vercel {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Vercel {key}: {str(e)}")
            return False, None


class EstuaryRotator(SecretRotator):
    """Rotator for Estuary API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("estuary", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate an Estuary secret"""
        try:
            if key == "api_key":
                # Generate a new API key
                new_api_key = self.generate_api_key(length=40, prefix="est_")
                
                # In a real implementation, this would call the Estuary API to update the API key
                logger.info(f"Rotating Estuary API key")
                
                return True, new_api_key
            else:
                logger.warning(f"Rotation not implemented for Estuary {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Estuary {key}: {str(e)}")
            return False, None


class PineconeRotator(SecretRotator):
    """Rotator for Pinecone API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("pinecone", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate a Pinecone secret"""
        try:
            if key == "api_key":
                # Generate a new API key
                new_api_key = self.generate_api_key(length=40, prefix="pinecone_")
                
                # In a real implementation, this would call the Pinecone API to update the API key
                logger.info(f"Rotating Pinecone API key")
                
                return True, new_api_key
            else:
                logger.warning(f"Rotation not implemented for Pinecone {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Pinecone {key}: {str(e)}")
            return False, None


class AirbyteRotator(SecretRotator):
    """Rotator for Airbyte API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("airbyte", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate an Airbyte secret"""
        try:
            if key == "api_key":
                # Generate a new API key
                new_api_key = self.generate_api_key(length=40, prefix="airbyte_")
                
                # In a real implementation, this would call the Airbyte API to update the API key
                logger.info(f"Rotating Airbyte API key")
                
                return True, new_api_key
            elif key == "password":
                # Generate a new password
                new_password = self.generate_password(length=24, include_special=True)
                
                # In a real implementation, this would call the Airbyte API to update the password
                logger.info(f"Rotating Airbyte password")
                
                return True, new_password
            else:
                logger.warning(f"Rotation not implemented for Airbyte {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Airbyte {key}: {str(e)}")
            return False, None


class LambdaLabsRotator(SecretRotator):
    """Rotator for Lambda Labs API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("lambda_labs", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate a Lambda Labs secret"""
        try:
            if key == "api_key":
                # Generate a new API key
                new_api_key = self.generate_api_key(length=40, prefix="lambda_")
                
                # In a real implementation, this would call the Lambda Labs API to update the API key
                logger.info(f"Rotating Lambda Labs API key")
                
                return True, new_api_key
            elif key == "jupyter_password":
                # Generate a new password
                new_password = self.generate_password(length=24, include_special=True)
                
                # In a real implementation, this would call the Lambda Labs API to update the password
                logger.info(f"Rotating Lambda Labs Jupyter password")
                
                return True, new_password
            elif key == "ssh_public_key" or key == "ssh_private_key":
                # In a real implementation, this would generate a new SSH key pair
                logger.info(f"Rotating Lambda Labs {key}")
                
                # For this example, we'll just return a placeholder
                return True, "PLACEHOLDER_SSH_KEY"
            else:
                logger.warning(f"Rotation not implemented for Lambda Labs {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Lambda Labs {key}: {str(e)}")
            return False, None


class OpenAIRotator(SecretRotator):
    """Rotator for OpenAI API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("openai", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate an OpenAI secret"""
        try:
            if key == "api_key":
                # Generate a new API key
                new_api_key = self.generate_api_key(length=40, prefix="sk-")
                
                # In a real implementation, this would call the OpenAI API to update the API key
                logger.info(f"Rotating OpenAI API key")
                
                return True, new_api_key
            else:
                logger.warning(f"Rotation not implemented for OpenAI {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate OpenAI {key}: {str(e)}")
            return False, None


class AnthropicRotator(SecretRotator):
    """Rotator for Anthropic API credentials"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("anthropic", config)
    
    def rotate_secret(self, key: str) -> Tuple[bool, Optional[str]]:
        """Rotate an Anthropic secret"""
        try:
            if key == "api_key":
                # Generate a new API key
                new_api_key = self.generate_api_key(length=40, prefix="sk-ant-")
                
                # In a real implementation, this would call the Anthropic API to update the API key
                logger.info(f"Rotating Anthropic API key")
                
                return True, new_api_key
            else:
                logger.warning(f"Rotation not implemented for Anthropic {key}")
                return False, None
        except Exception as e:
            logger.error(f"Failed to rotate Anthropic {key}: {str(e)}")
            return False, None


class RotationManager:
    """
    Manages secret rotation for all services
    """
    
    def __init__(self):
        self.rotators = {}
        self.service_registry = self._load_service_registry()
        self._initialize_rotators()
    
    def _load_service_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load service registry"""
        try:
            registry_path = os.environ.get(
                "SERVICE_REGISTRY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/service_registry.json"
            )
            
            if os.path.exists(registry_path):
                with open(registry_path, "r") as f:
                    registry = json.load(f)
                
                logger.info(f"Loaded service registry with {len(registry)} services")
                return registry
            else:
                logger.warning(f"Service registry not found at {registry_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load service registry: {e}")
            return {}
    
    def _initialize_rotators(self):
        """Initialize rotators for all services"""
        for service, config in self.service_registry.items():
            try:
                if service == "snowflake":
                    self.rotators[service] = SnowflakeRotator(config)
                elif service == "gong":
                    self.rotators[service] = GongRotator(config)
                elif service == "vercel":
                    self.rotators[service] = VercelRotator(config)
                elif service == "estuary":
                    self.rotators[service] = EstuaryRotator(config)
                elif service == "pinecone":
                    self.rotators[service] = PineconeRotator(config)
                elif service == "airbyte":
                    self.rotators[service] = AirbyteRotator(config)
                elif service == "lambda_labs":
                    self.rotators[service] = LambdaLabsRotator(config)
                elif service == "openai":
                    self.rotators[service] = OpenAIRotator(config)
                elif service == "anthropic":
                    self.rotators[service] = AnthropicRotator(config)
                else:
                    # Default rotator
                    self.rotators[service] = SecretRotator(service, config)
            except Exception as e:
                logger.error(f"Failed to initialize rotator for {service}: {e}")
    
    def rotate_service_secrets(self, service: str, dry_run: bool = False) -> Dict[str, Any]:
        """Rotate secrets for a specific service"""
        if service not in self.rotators:
            return {
                "service": service,
                "timestamp": datetime.datetime.now().isoformat(),
                "dry_run": dry_run,
                "error": f"Service {service} not found"
            }
        
        return self.rotators[service].rotate_all_secrets(dry_run)
    
    def rotate_all_secrets(self, dry_run: bool = False) -> Dict[str, Any]:
        """Rotate secrets for all services"""
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "dry_run": dry_run,
            "services": {}
        }
        
        for service, rotator in self.rotators.items():
            results["services"][service] = rotator.rotate_all_secrets(dry_run)
        
        return results
    
    def get_rotation_schedule(self) -> Dict[str, Any]:
        """Get rotation schedule for all services"""
        schedule = {
            "timestamp": datetime.datetime.now().isoformat(),
            "services": {}
        }
        
        for service, rotator in self.rotators.items():
            schedule["services"][service] = {
                "rotation_schedule": rotator.rotation_schedule,
                "secret_keys": rotator.secret_keys,
                "last_rotation": {k: v.isoformat() if v else None for k, v in rotator.last_rotation.items()},
                "next_rotation": {k: v.isoformat() if v else None for k, v in rotator.next_rotation.items()}
            }
        
        return schedule


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Rotate secrets")
    parser.add_argument("--service", "-s", help="Service to rotate secrets for (default: all)")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Dry run (don't actually rotate secrets)")
    parser.add_argument("--schedule", action="store_true", help="Show rotation schedule")
    parser.add_argument("--output", "-o", help="Output file (JSON)")
    args = parser.parse_args()
    
    try:
        manager = RotationManager()
        
        if args.schedule:
            result = manager.get_rotation_schedule()
        elif args.service:
            result = manager.rotate_service_secrets(args.service, args.dry_run)
        else:
            result = manager.rotate_all_secrets(args.dry_run)
        
        # Print summary
        if args.schedule:
            print("Rotation Schedule:")
            for service, schedule in result["services"].items():
                print(f"  {service}: {schedule['rotation_schedule']}")
                for key in schedule["secret_keys"]:
                    last = schedule["last_rotation"].get(key, "Never")
                    next_rot = schedule["next_rotation"].get(key, "ASAP")
                    print(f"    {key}: Last={last}, Next={next_rot}")
        else:
            if args.service:
                service_result = result
                rotated = len(service_result.get("rotated", []))
                skipped = len(service_result.get("skipped", []))
                failed = len(service_result.get("failed", []))
                print(f"Service {args.service}: {rotated} rotated, {skipped} skipped, {failed} failed")
            else:
                total_rotated = 0
                total_skipped = 0
                total_failed = 0
                for service, service_result in result["services"].items():
                    rotated = len(service_result.get("rotated", []))
                    skipped = len(service_result.get("skipped", []))
                    failed = len(service_result.get("failed", []))
                    total_rotated += rotated
                    total_skipped += skipped
                    total_failed += failed
                    print(f"Service {service}: {rotated} rotated, {skipped} skipped, {failed} failed")
                print(f"Total: {total_rotated} rotated, {total_skipped} skipped, {total_failed} failed")
        
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

