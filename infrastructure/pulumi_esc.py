"""
Sophia AI - Pulumi ESC Integration Infrastructure as Code
This module defines Pulumi ESC (Environments, Secrets, and Configuration) resources using Pulumi
"""

import pulumi
import json
from pulumi import Config
import pulumi_pulumiservice as pulumiservice

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get Pulumi credentials from Pulumi config (encrypted)
pulumi_access_token = config.require_secret("pulumi_access_token")
pulumi_organization = config.require("pulumi_organization")
pulumi_project = config.require("pulumi_project")

# Define environment-specific configurations
stack_names = {
    "development": "development",
    "staging": "staging",
    "production": "production"
}

# Create a Pulumi ESC environment
esc_environment = pulumiservice.Environment(f"sophia-{env}",
    organization=pulumi_organization,
    name=f"sophia-{env}",
    description=f"Sophia AI environment for {env}",
    environment_type="managed"
)

# Define secrets to be stored in Pulumi ESC
secrets = [
    {
        "name": "snowflake_account",
        "value": config.require_secret("snowflake_account")
    },
    {
        "name": "snowflake_user",
        "value": config.require_secret("snowflake_user")
    },
    {
        "name": "snowflake_password",
        "value": config.require_secret("snowflake_password")
    },
    {
        "name": "snowflake_warehouse",
        "value": config.require_secret("snowflake_warehouse")
    },
    {
        "name": "snowflake_database",
        "value": config.require_secret("snowflake_database")
    },
    {
        "name": "snowflake_schema",
        "value": config.require_secret("snowflake_schema")
    },
    {
        "name": "snowflake_role",
        "value": config.require_secret("snowflake_role")
    },
    {
        "name": "gong_api_key",
        "value": config.require_secret("gong_api_key")
    },
    {
        "name": "gong_api_secret",
        "value": config.require_secret("gong_api_secret")
    },
    {
        "name": "vercel_access_token",
        "value": config.require_secret("vercel_access_token")
    },
    {
        "name": "vercel_team_id",
        "value": config.require_secret("vercel_team_id")
    },
    {
        "name": "vercel_project_id",
        "value": config.require_secret("vercel_project_id")
    },
    {
        "name": "vercel_org_id",
        "value": config.require_secret("vercel_org_id")
    },
    {
        "name": "estuary_api_key",
        "value": config.require_secret("estuary_api_key")
    },
    {
        "name": "estuary_api_url",
        "value": config.require_secret("estuary_api_url")
    },
    {
        "name": "portkey_api_key",
        "value": config.require_secret("portkey_api_key")
    },
    {
        "name": "openrouter_api_key",
        "value": config.require_secret("openrouter_api_key")
    },
    {
        "name": "lambda_labs_api_key",
        "value": config.require_secret("lambda_labs_api_key")
    },
    {
        "name": "lambda_labs_jupyter_password",
        "value": config.require_secret("lambda_labs_jupyter_password")
    },
    {
        "name": "lambda_labs_ssh_public_key",
        "value": config.require("lambda_labs_ssh_public_key")
    },
    {
        "name": "airbyte_api_key",
        "value": config.require_secret("airbyte_api_key")
    },
    {
        "name": "airbyte_password",
        "value": config.require_secret("airbyte_password")
    },
    {
        "name": "github_token",
        "value": config.require_secret("github_token")
    },
    {
        "name": "github_org",
        "value": config.require("github_org")
    },
    {
        "name": "slack_webhook_url",
        "value": config.require_secret("slack_webhook_url")
    }
]

# Create Pulumi ESC secrets
for secret in secrets:
    esc_secret = pulumiservice.EnvironmentSecret(f"sophia-{env}-{secret['name']}",
        organization=pulumi_organization,
        environment=esc_environment.name,
        name=secret["name"],
        value=secret["value"]
    )

# Define environment-specific secrets
environment_specific_secrets = {
    "development": [
        {
            "name": "snowflake_warehouse_development",
            "value": config.require_secret("snowflake_warehouse_development")
        },
        {
            "name": "snowflake_database_development",
            "value": config.require_secret("snowflake_database_development")
        },
        {
            "name": "snowflake_schema_development",
            "value": config.require_secret("snowflake_schema_development")
        },
        {
            "name": "snowflake_role_development",
            "value": config.require_secret("snowflake_role_development")
        },
        {
            "name": "vercel_project_id_development",
            "value": config.require_secret("vercel_project_id_development")
        }
    ],
    "staging": [
        {
            "name": "snowflake_warehouse_staging",
            "value": config.require_secret("snowflake_warehouse_staging")
        },
        {
            "name": "snowflake_database_staging",
            "value": config.require_secret("snowflake_database_staging")
        },
        {
            "name": "snowflake_schema_staging",
            "value": config.require_secret("snowflake_schema_staging")
        },
        {
            "name": "snowflake_role_staging",
            "value": config.require_secret("snowflake_role_staging")
        },
        {
            "name": "vercel_project_id_staging",
            "value": config.require_secret("vercel_project_id_staging")
        }
    ],
    "production": [
        {
            "name": "snowflake_warehouse_production",
            "value": config.require_secret("snowflake_warehouse_production")
        },
        {
            "name": "snowflake_database_production",
            "value": config.require_secret("snowflake_database_production")
        },
        {
            "name": "snowflake_schema_production",
            "value": config.require_secret("snowflake_schema_production")
        },
        {
            "name": "snowflake_role_production",
            "value": config.require_secret("snowflake_role_production")
        },
        {
            "name": "vercel_project_id_production",
            "value": config.require_secret("vercel_project_id_production")
        }
    ]
}

# Create environment-specific Pulumi ESC secrets
for secret in environment_specific_secrets.get(env, []):
    esc_env_secret = pulumiservice.EnvironmentSecret(f"sophia-{env}-{secret['name']}",
        organization=pulumi_organization,
        environment=esc_environment.name,
        name=secret["name"],
        value=secret["value"]
    )

# Create a Pulumi stack
stack = pulumiservice.Stack(f"sophia-{env}-stack",
    organization=pulumi_organization,
    project=pulumi_project,
    stack=stack_names.get(env, "development"),
    tags={
        "environment": env,
        "application": "sophia"
    }
)

# Associate the stack with the environment
stack_environment_binding = pulumiservice.StackEnvironmentBinding(f"sophia-{env}-stack-binding",
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
        "environment": esc_environment.name
    }, indent=2))
})

# Export outputs
pulumi.export("pulumi_esc_environment", esc_environment.name)
pulumi.export("pulumi_esc_stack", stack.stack)
pulumi.export("pulumi_esc_organization", pulumi_organization)
pulumi.export("pulumi_esc_project", pulumi_project)
