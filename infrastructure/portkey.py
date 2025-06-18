"""
Sophia AI - Portkey Integration Infrastructure as Code
This module defines Portkey API Gateway resources using Pulumi
"""

import pulumi
import json
from pulumi import Config

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get Portkey credentials from Pulumi config (encrypted)
portkey_api_key = config.require_secret("portkey_api_key")

# Define environment-specific configurations
api_base_urls = {
    "development": "https://api.dev.portkey.ai",
    "staging": "https://api.staging.portkey.ai",
    "production": "https://api.portkey.ai"
}

# Define Portkey provider configuration
portkey_provider = {
    "api_key": portkey_api_key,
    "base_url": api_base_urls.get(env, api_base_urls["development"])
}

# Define Portkey virtual key configuration
virtual_key_config = {
    "name": f"sophia-{env}",
    "description": f"Sophia AI virtual key for {env} environment",
    "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"],
    "providers": ["openai", "anthropic"],
    "routing_strategy": "least-cost",
    "cache_config": {
        "enabled": True,
        "ttl": 3600
    },
    "rate_limit_config": {
        "enabled": True,
        "requests_per_minute": 100
    },
    "retry_config": {
        "enabled": True,
        "max_retries": 3,
        "initial_retry_delay": 1,
        "retry_multiplier": 2,
        "jitter": 0.1
    }
}

# Create a Portkey configuration file
portkey_config = pulumi.asset.AssetArchive({
    "portkey_config.json": pulumi.asset.StringAsset(json.dumps({
        "api_key": portkey_api_key,
        "base_url": api_base_urls.get(env, api_base_urls["development"]),
        "virtual_key": virtual_key_config
    }, indent=2))
})

# Export outputs
pulumi.export("portkey_base_url", api_base_urls.get(env, api_base_urls["development"]))
pulumi.export("portkey_virtual_key_name", virtual_key_config["name"])
pulumi.export("portkey_environment", env)
