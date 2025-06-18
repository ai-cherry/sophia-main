"""
Sophia AI - OpenRouter Integration Infrastructure as Code
This module defines OpenRouter API resources using Pulumi
"""

import pulumi
import json
from pulumi import Config

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get OpenRouter credentials from Pulumi config (encrypted)
openrouter_api_key = config.require_secret("openrouter_api_key")

# Define environment-specific configurations
api_base_urls = {
    "development": "https://openrouter.ai/api/v1",
    "staging": "https://openrouter.ai/api/v1",
    "production": "https://openrouter.ai/api/v1"
}

# Define OpenRouter provider configuration
openrouter_provider = {
    "api_key": openrouter_api_key,
    "base_url": api_base_urls.get(env, api_base_urls["development"]),
    "default_model": "openai/gpt-4-turbo",
    "default_route_prefix": f"sophia-{env}"
}

# Define OpenRouter model configuration
model_configs = [
    {
        "model": "openai/gpt-4-turbo",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    {
        "model": "anthropic/claude-3-opus",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    {
        "model": "anthropic/claude-3-sonnet",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    {
        "model": "meta-llama/llama-3-70b-instruct",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
]

# Create an OpenRouter configuration file
openrouter_config = pulumi.asset.AssetArchive({
    "openrouter_config.json": pulumi.asset.StringAsset(json.dumps({
        "api_key": openrouter_api_key,
        "base_url": api_base_urls.get(env, api_base_urls["development"]),
        "default_model": openrouter_provider["default_model"],
        "default_route_prefix": openrouter_provider["default_route_prefix"],
        "models": model_configs
    }, indent=2))
})

# Export outputs
pulumi.export("openrouter_base_url", api_base_urls.get(env, api_base_urls["development"]))
pulumi.export("openrouter_default_model", openrouter_provider["default_model"])
pulumi.export("openrouter_route_prefix", openrouter_provider["default_route_prefix"])
pulumi.export("openrouter_environment", env)
