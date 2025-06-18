"""
Sophia AI - Main Infrastructure as Code
This module brings together all infrastructure resources for the Sophia AI platform
"""

import pulumi
from pulumi import Config
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import infrastructure modules
import snowflake
import gong
import vercel
import estuary
import portkey
import openrouter
import lambda_labs
import airbyte
import github
import pulumi_esc
import docker
import mcp

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Create a stack output with all the exported values
pulumi.export("environment", env)

# Snowflake outputs
pulumi.export("snowflake", {
    "warehouse_name": snowflake.warehouse.name,
    "database_name": snowflake.database.name,
    "schema_name": snowflake.schema.name,
    "role_name": snowflake.role.name
})

# Gong outputs
pulumi.export("gong", {
    "webhook_url": gong.webhook_urls.get(env, gong.webhook_urls["development"]),
    "environment": env
})

# Vercel outputs
pulumi.export("vercel", {
    "project_name": vercel.project.name,
    "domain": vercel.domain.name,
    "deployment_url": vercel.deployment.url
})

# Estuary outputs
pulumi.export("estuary", {
    "collection": estuary.collection_names.get(env, estuary.collection_names["development"]),
    "api_url": estuary.estuary_api_url,
    "environment": env
})

# Portkey outputs
pulumi.export("portkey", {
    "base_url": portkey.api_base_urls.get(env, portkey.api_base_urls["development"]),
    "virtual_key_name": portkey.virtual_key_config["name"],
    "environment": env
})

# OpenRouter outputs
pulumi.export("openrouter", {
    "base_url": openrouter.api_base_urls.get(env, openrouter.api_base_urls["development"]),
    "default_model": openrouter.openrouter_provider["default_model"],
    "route_prefix": openrouter.openrouter_provider["default_route_prefix"],
    "environment": env
})

# Lambda Labs outputs
pulumi.export("lambda_labs", {
    "instance_type": lambda_labs.instance_config["instance_type"],
    "region": lambda_labs.instance_config["region"],
    "ssh_key_name": lambda_labs.ssh_key.key_name,
    "data_bucket": lambda_labs.data_bucket.bucket,
    "iam_role": lambda_labs.lambda_labs_role.name,
    "environment": env
})

# Airbyte outputs
pulumi.export("airbyte", {
    "base_url": airbyte.airbyte_urls.get(env, airbyte.airbyte_urls["development"]),
    "workspace_name": airbyte.workspace_config["name"],
    "sources": [source["name"] for source in airbyte.source_configs],
    "destinations": [dest["name"] for dest in airbyte.destination_configs],
    "connections": [conn["name"] for conn in airbyte.connection_configs],
    "environment": env
})

# GitHub outputs
pulumi.export("github", {
    "repository_name": github.repo.name,
    "repository_url": github.repo.html_url,
    "team_name": github.team.name,
    "environment": env
})

# Pulumi ESC outputs
pulumi.export("pulumi_esc", {
    "environment": pulumi_esc.esc_environment.name,
    "stack": pulumi_esc.stack.stack,
    "organization": pulumi_esc.pulumi_organization,
    "project": pulumi_esc.pulumi_project
})

# Docker outputs
pulumi.export("docker", {
    "registry": docker.registry_urls.get(env, docker.registry_urls["development"]),
    "images": [image.image_name for image in docker.images],
    "network": docker.network.name,
    "volumes": [volume.name for volume in docker.volumes],
    "containers": [container.name for container in docker.containers],
    "environment": env
})

# MCP outputs
pulumi.export("mcp", {
    "servers": mcp.mcp_servers,
    "images": [image.image_name for image in mcp.mcp_images],
    "containers": [container.name for container in mcp.mcp_containers],
    "environment": env
})

# Create a combined configuration output
pulumi.export("sophia_config", {
    "environment": env,
    "snowflake": {
        "warehouse": snowflake.warehouse.name,
        "database": snowflake.database.name,
        "schema": snowflake.schema.name,
        "role": snowflake.role.name
    },
    "gong": {
        "webhook_url": gong.webhook_urls.get(env, gong.webhook_urls["development"])
    },
    "vercel": {
        "project": vercel.project.name,
        "domain": vercel.domain.name,
        "url": vercel.deployment.url
    },
    "estuary": {
        "collection": estuary.collection_names.get(env, estuary.collection_names["development"]),
        "api_url": estuary.estuary_api_url
    },
    "portkey": {
        "base_url": portkey.api_base_urls.get(env, portkey.api_base_urls["development"]),
        "virtual_key_name": portkey.virtual_key_config["name"]
    },
    "openrouter": {
        "base_url": openrouter.api_base_urls.get(env, openrouter.api_base_urls["development"]),
        "default_model": openrouter.openrouter_provider["default_model"],
        "route_prefix": openrouter.openrouter_provider["default_route_prefix"]
    },
    "lambda_labs": {
        "instance_type": lambda_labs.instance_config["instance_type"],
        "region": lambda_labs.instance_config["region"],
        "data_bucket": lambda_labs.data_bucket.bucket
    },
    "airbyte": {
        "base_url": airbyte.airbyte_urls.get(env, airbyte.airbyte_urls["development"]),
        "workspace_name": airbyte.workspace_config["name"]
    },
    "github": {
        "repository_name": github.repo.name,
        "repository_url": github.repo.html_url
    },
    "pulumi_esc": {
        "environment": pulumi_esc.esc_environment.name,
        "stack": pulumi_esc.stack.stack
    },
    "docker": {
        "registry": docker.registry_urls.get(env, docker.registry_urls["development"]),
        "network": docker.network.name
    },
    "mcp": {
        "servers": [server["name"] for server in mcp.mcp_server_configs]
    }
})

# Print a success message
pulumi.export("message", f"Sophia AI infrastructure for {env} environment has been successfully deployed!")
