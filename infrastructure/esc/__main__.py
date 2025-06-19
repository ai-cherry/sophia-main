"""
Sophia AI - Pulumi ESC Environment Configuration
This module defines the Pulumi ESC environment for centralized secret management
"""

import pulumi
import json
import os
from pulumi import Config
import pulumi_pulumiservice as pulumiservice

# Load configuration
config = Config()

# Define environment (using only production as per recommendation)
environment = "production"

# Get Pulumi credentials from Pulumi config (encrypted)
pulumi_access_token = config.require_secret("pulumi_access_token")
pulumi_organization = config.get("pulumi_organization") or "ai-cherry"
pulumi_project = config.get("pulumi_project") or "sophia"

# Create a Pulumi ESC environment
esc_environment = pulumiservice.Environment(f"sophia-{environment}",
    organization=pulumi_organization,
    name=f"sophia-{environment}",
    description=f"Sophia AI environment for {environment}",
    environment_type="managed"
)

# Define secret groups
secret_groups = {
    "api-keys": "API keys for external services",
    "database-credentials": "Database credentials for various data stores",
    "security-tokens": "Security tokens and secrets",
    "integration-credentials": "Credentials for integrated services",
    "infrastructure-credentials": "Credentials for infrastructure services"
}

# Create secret groups
for group_name, description in secret_groups.items():
    pulumiservice.SecretGroup(f"sophia-{environment}-{group_name}",
        organization=pulumi_organization,
        environment=esc_environment.name,
        name=group_name,
        description=description
    )

# Define service-specific secret mappings
service_secret_mappings = {
    "snowflake": {
        "account": {"group": "database-credentials", "description": "Snowflake account identifier"},
        "user": {"group": "database-credentials", "description": "Snowflake user"},
        "password": {"group": "database-credentials", "description": "Snowflake password"},
        "warehouse": {"group": "database-credentials", "description": "Snowflake warehouse"},
        "database": {"group": "database-credentials", "description": "Snowflake database"},
        "schema": {"group": "database-credentials", "description": "Snowflake schema"},
        "role": {"group": "database-credentials", "description": "Snowflake role"}
    },
    "gong": {
        "api_key": {"group": "api-keys", "description": "Gong API key"},
        "api_secret": {"group": "api-keys", "description": "Gong API secret"},
        "client_secret": {"group": "api-keys", "description": "Gong client secret"},
        "base_url": {"group": "api-keys", "description": "Gong base URL"}
    },
    "vercel": {
        "token": {"group": "api-keys", "description": "Vercel access token"},
        "team_id": {"group": "api-keys", "description": "Vercel team ID"},
        "project_id": {"group": "api-keys", "description": "Vercel project ID"},
        "org_id": {"group": "api-keys", "description": "Vercel organization ID"}
    },
    "estuary": {
        "api_key": {"group": "api-keys", "description": "Estuary API key"},
        "api_url": {"group": "api-keys", "description": "Estuary API URL"}
    },
    "lambda_labs": {
        "api_key": {"group": "api-keys", "description": "Lambda Labs API key"},
        "jupyter_password": {"group": "security-tokens", "description": "Lambda Labs Jupyter password"},
        "ssh_public_key": {"group": "security-tokens", "description": "Lambda Labs SSH public key"},
        "ssh_private_key": {"group": "security-tokens", "description": "Lambda Labs SSH private key"}
    },
    "airbyte": {
        "api_key": {"group": "api-keys", "description": "Airbyte API key"},
        "password": {"group": "security-tokens", "description": "Airbyte password"}
    },
    "pinecone": {
        "api_key": {"group": "api-keys", "description": "Pinecone API key"},
        "environment": {"group": "api-keys", "description": "Pinecone environment"}
    },
    "weaviate": {
        "api_key": {"group": "api-keys", "description": "Weaviate API key"},
        "url": {"group": "api-keys", "description": "Weaviate URL"}
    },
    "openai": {
        "api_key": {"group": "api-keys", "description": "OpenAI API key"}
    },
    "anthropic": {
        "api_key": {"group": "api-keys", "description": "Anthropic API key"}
    },
    "github": {
        "token": {"group": "security-tokens", "description": "GitHub personal access token"},
        "org": {"group": "security-tokens", "description": "GitHub organization"}
    }
}

# Create a flat list of all secret mappings
all_secret_mappings = {}
for service, mappings in service_secret_mappings.items():
    for key, details in mappings.items():
        secret_name = f"{service}_{key}"
        all_secret_mappings[secret_name] = {
            "group": details["group"],
            "description": details["description"],
            "service": service
        }

# Define access policies
access_policies = [
    {
        "name": "admin-access",
        "description": "Full access to all secrets",
        "secret_groups": list(secret_groups.keys()),
        "identities": [
            {"type": "user", "name": "admin@payready.com"},
            {"type": "user", "name": "musillynnl@gmail.com"}
        ]
    },
    {
        "name": "ci-cd-access",
        "description": "Access for CI/CD pipelines",
        "secret_groups": list(secret_groups.keys()),
        "identities": [
            {"type": "github", "name": "payready/sophia"},
            {"type": "github", "name": "ai-cherry/sophia"}
        ]
    }
]

# Create access policies
for policy in access_policies:
    policy_identities = []
    for identity in policy["identities"]:
        if identity["type"] == "user":
            policy_identities.append(pulumiservice.AccessPolicyIdentityArgs(
                type="user",
                name=identity["name"]
            ))
        elif identity["type"] == "github":
            policy_identities.append(pulumiservice.AccessPolicyIdentityArgs(
                type="github",
                name=identity["name"]
            ))
    
    pulumiservice.AccessPolicy(f"sophia-{environment}-{policy['name']}",
        organization=pulumi_organization,
        name=policy["name"],
        description=policy["description"],
        secret_groups=policy["secret_groups"],
        environments=[environment],
        identities=policy_identities
    )

# Create a Pulumi stack
stack = pulumiservice.Stack(f"sophia-{environment}-stack",
    organization=pulumi_organization,
    project=pulumi_project,
    stack=environment,
    tags={
        "environment": environment,
        "application": "sophia"
    }
)

# Associate the stack with the environment
stack_environment_binding = pulumiservice.StackEnvironmentBinding(f"sophia-{environment}-stack-binding",
    organization=pulumi_organization,
    project=pulumi_project,
    stack=stack.stack,
    environment=esc_environment.name
)

# Create a Pulumi ESC configuration file
pulumi_esc_config = pulumi.asset.AssetArchive({
    "pulumi_esc_config.json": pulumi.asset.StringAsset(json.dumps({
        "organization": pulumi_organization,
        "project": pulumi_project,
        "stack": stack.stack,
        "environment": esc_environment.name,
        "secret_mappings": all_secret_mappings
    }, indent=2))
})

# Export outputs
pulumi.export("pulumi_esc_environment", esc_environment.name)
pulumi.export("pulumi_esc_stack", stack.stack)
pulumi.export("pulumi_esc_organization", pulumi_organization)
pulumi.export("pulumi_esc_project", pulumi_project)
pulumi.export("secret_groups", list(secret_groups.keys()))
pulumi.export("secret_mappings_count", len(all_secret_mappings))
pulumi.export("access_policies", [policy["name"] for policy in access_policies])

