"""
Sophia AI - Gong Integration Infrastructure as Code
This module defines Gong integration resources using Pulumi
"""

import pulumi
import json
import pulumi_command as command
from pulumi import Config

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get Gong credentials from Pulumi config (encrypted)
gong_api_key = config.require_secret("gong_api_key")
gong_api_secret = config.require_secret("gong_api_secret")

# Define environment-specific configurations
webhook_urls = {
    "development": "https://dev-api.payready.com/sophia/gong/webhook",
    "staging": "https://staging-api.payready.com/sophia/gong/webhook",
    "production": "https://api.payready.com/sophia/gong/webhook"
}

# Create a Gong webhook configuration using the Gong API
# This is a custom resource that uses the Pulumi Command provider to call the Gong API
gong_webhook = command.local.Command("gong_webhook",
    create=pulumi.Output.concat(
        "curl -X POST 'https://us-70092.api.gong.io/v2/webhooks' ",
        "-H 'Content-Type: application/json' ",
        "-H 'Authorization: Bearer ", gong_api_secret, "' ",
        "-d '{",
        "\"name\": \"Sophia AI Integration - ", env, "\",",
        "\"url\": \"", webhook_urls.get(env, webhook_urls["development"]), "\",",
        "\"description\": \"Webhook for Sophia AI integration\",",
        "\"events\": [\"call.done\", \"call.metadata.changed\"],",
        "\"active\": true",
        "}'"
    ),
    update=pulumi.Output.concat(
        "curl -X PUT 'https://us-70092.api.gong.io/v2/webhooks/${WEBHOOK_ID}' ",
        "-H 'Content-Type: application/json' ",
        "-H 'Authorization: Bearer ", gong_api_secret, "' ",
        "-d '{",
        "\"name\": \"Sophia AI Integration - ", env, "\",",
        "\"url\": \"", webhook_urls.get(env, webhook_urls["development"]), "\",",
        "\"description\": \"Webhook for Sophia AI integration\",",
        "\"events\": [\"call.done\", \"call.metadata.changed\"],",
        "\"active\": true",
        "}'"
    ),
    delete=pulumi.Output.concat(
        "curl -X DELETE 'https://us-70092.api.gong.io/v2/webhooks/${WEBHOOK_ID}' ",
        "-H 'Authorization: Bearer ", gong_api_secret, "'"
    ),
    environment={
        "WEBHOOK_ID": "${WEBHOOK_ID}"  # This would be populated by the create command in a real implementation
    }
)

# Create a Gong API configuration file
gong_config = pulumi.asset.AssetArchive({
    "gong_config.json": pulumi.asset.StringAsset(json.dumps({
        "api_key": gong_api_key,
        "api_secret": gong_api_secret,
        "webhook_url": webhook_urls.get(env, webhook_urls["development"]),
        "environment": env
    }, indent=2))
})

# Export outputs
pulumi.export("gong_webhook_url", webhook_urls.get(env, webhook_urls["development"]))
pulumi.export("gong_environment", env)
