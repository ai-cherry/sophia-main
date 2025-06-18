"""
Sophia AI - MCP (Model Context Protocol) Infrastructure as Code
This module defines MCP server resources using Pulumi
"""

import pulumi
import json
from pulumi import Config
import pulumi_docker as docker

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Define environment-specific configurations
registry_urls = {
    "development": "sophiaai.azurecr.io",
    "staging": "sophiaai.azurecr.io",
    "production": "sophiaai.azurecr.io"
}

# Get Docker registry credentials from Pulumi config (encrypted)
registry_username = config.require_secret("docker_registry_username")
registry_password = config.require_secret("docker_registry_password")

# Create a Docker provider
docker_provider = docker.Provider("mcp-docker-provider",
    host="unix:///var/run/docker.sock",
    registry_auth=[{
        "address": registry_urls.get(env, registry_urls["development"]),
        "username": registry_username,
        "password": registry_password
    }]
)

# Define MCP server configurations
mcp_server_configs = [
    {
        "name": "claude-mcp",
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/claude-mcp:{env}",
        "context": "../backend/mcp/claude/",
        "dockerfile": "../backend/mcp/claude/Dockerfile",
        "port": 8010,
        "envs": [
            f"ENVIRONMENT={env}",
            "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}",
            "MCP_SERVER_NAME=claude",
            "MCP_SERVER_VERSION=1.0.0"
        ],
        "network": f"sophia-network-{env}",
        "restart": "unless-stopped"
    },
    {
        "name": "openai-mcp",
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/openai-mcp:{env}",
        "context": "../backend/mcp/openai/",
        "dockerfile": "../backend/mcp/openai/Dockerfile",
        "port": 8011,
        "envs": [
            f"ENVIRONMENT={env}",
            "OPENAI_API_KEY=${OPENAI_API_KEY}",
            "MCP_SERVER_NAME=openai",
            "MCP_SERVER_VERSION=1.0.0"
        ],
        "network": f"sophia-network-{env}",
        "restart": "unless-stopped"
    },
    {
        "name": "salesforce-mcp",
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/salesforce-mcp:{env}",
        "context": "../backend/mcp/salesforce/",
        "dockerfile": "../backend/mcp/salesforce/Dockerfile",
        "port": 8012,
        "envs": [
            f"ENVIRONMENT={env}",
            "SALESFORCE_CLIENT_ID=${SALESFORCE_CLIENT_ID}",
            "SALESFORCE_CLIENT_SECRET=${SALESFORCE_CLIENT_SECRET}",
            "SALESFORCE_USERNAME=${SALESFORCE_USERNAME}",
            "SALESFORCE_PASSWORD=${SALESFORCE_PASSWORD}",
            "MCP_SERVER_NAME=salesforce",
            "MCP_SERVER_VERSION=1.0.0"
        ],
        "network": f"sophia-network-{env}",
        "restart": "unless-stopped"
    },
    {
        "name": "hubspot-mcp",
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/hubspot-mcp:{env}",
        "context": "../backend/mcp/hubspot/",
        "dockerfile": "../backend/mcp/hubspot/Dockerfile",
        "port": 8013,
        "envs": [
            f"ENVIRONMENT={env}",
            "HUBSPOT_API_KEY=${HUBSPOT_API_KEY}",
            "MCP_SERVER_NAME=hubspot",
            "MCP_SERVER_VERSION=1.0.0"
        ],
        "network": f"sophia-network-{env}",
        "restart": "unless-stopped"
    },
    {
        "name": "slack-mcp",
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/slack-mcp:{env}",
        "context": "../backend/mcp/slack/",
        "dockerfile": "../backend/mcp/slack/Dockerfile",
        "port": 8014,
        "envs": [
            f"ENVIRONMENT={env}",
            "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}",
            "SLACK_APP_TOKEN=${SLACK_APP_TOKEN}",
            "SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}",
            "MCP_SERVER_NAME=slack",
            "MCP_SERVER_VERSION=1.0.0"
        ],
        "network": f"sophia-network-{env}",
        "restart": "unless-stopped"
    }
]

# Create MCP server images
mcp_images = []
for server_config in mcp_server_configs:
    image = docker.Image(server_config["name"],
        build=docker.DockerBuildArgs(
            context=server_config["context"],
            dockerfile=server_config["dockerfile"],
            platform="linux/amd64",
            args={
                "ENV": env,
                "BUILD_DATE": "${BUILD_DATE}",
                "VERSION": "${VERSION}"
            }
        ),
        image_name=server_config["image_name"],
        skip_push=env != "production",
        provider=docker_provider
    )
    mcp_images.append(image)

# Create MCP server containers
mcp_containers = []
for i, server_config in enumerate(mcp_server_configs):
    container = docker.Container(f"{server_config['name']}-container",
        name=f"{server_config['name']}-{env}",
        image=mcp_images[i].image_name,
        envs=server_config["envs"],
        ports=[docker.ContainerPortArgs(
            internal=server_config["port"],
            external=server_config["port"]
        )],
        networks_advanced=[docker.ContainerNetworksAdvancedArgs(
            name=server_config["network"],
            aliases=[server_config["name"]]
        )],
        restart=server_config["restart"],
        healthcheck=docker.ContainerHealthcheckArgs(
            test=["CMD", "curl", "-f", f"http://localhost:{server_config['port']}/health"],
            interval="30s",
            timeout="10s",
            retries=3,
            start_period="30s"
        ),
        provider=docker_provider
    )
    mcp_containers.append(container)

# Create MCP configuration file
mcp_config = {
    "version": "1.0.0",
    "environment": env,
    "servers": []
}

for server_config in mcp_server_configs:
    mcp_config["servers"].append({
        "name": server_config["name"],
        "url": f"http://{server_config['name']}:{server_config['port']}",
        "description": f"{server_config['name'].capitalize()} MCP Server"
    })

# Write MCP configuration file
mcp_config_file = pulumi.asset.AssetArchive({
    "mcp_config.json": pulumi.asset.StringAsset(json.dumps(mcp_config, indent=2))
})

# Export outputs
pulumi.export("mcp_servers", [server["name"] for server in mcp_server_configs])
pulumi.export("mcp_images", [image.image_name for image in mcp_images])
pulumi.export("mcp_containers", [container.name for container in mcp_containers])
pulumi.export("mcp_environment", env)
