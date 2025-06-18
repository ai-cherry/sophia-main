"""
Sophia AI - Airbyte Integration Infrastructure as Code
This module defines Airbyte resources using Pulumi
"""

import pulumi
import json
from pulumi import Config
import pulumi_kubernetes as k8s

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get Airbyte credentials from Pulumi config (encrypted)
airbyte_api_key = config.require_secret("airbyte_api_key")
airbyte_password = config.require_secret("airbyte_password")

# Define environment-specific configurations
airbyte_urls = {
    "development": "http://airbyte-dev.payready.internal:8000",
    "staging": "http://airbyte-staging.payready.internal:8000",
    "production": "http://airbyte.payready.internal:8000"
}

# Define Airbyte provider configuration
airbyte_provider = {
    "api_key": airbyte_api_key,
    "base_url": airbyte_urls.get(env, airbyte_urls["development"]),
    "username": "airbyte",
    "password": airbyte_password
}

# Define Airbyte workspace configuration
workspace_config = {
    "name": f"sophia-{env}",
    "email": "sophia-ai@payready.com",
    "anonymous_data_collection": False,
    "news": False,
    "security_updates": True,
    "notification_config": {
        "slack_webhook": config.get_secret("slack_webhook_url"),
        "send_on_success": True,
        "send_on_failure": True
    }
}

# Define Airbyte source configurations
source_configs = [
    {
        "name": f"snowflake-{env}",
        "source_type": "snowflake",
        "connection_configuration": {
            "host": config.require("snowflake_account"),
            "role": config.require("snowflake_role"),
            "warehouse": config.require("snowflake_warehouse"),
            "database": config.require("snowflake_database"),
            "schema": config.require("snowflake_schema"),
            "username": config.require("snowflake_user"),
            "password": config.require_secret("snowflake_password"),
            "credentials": {
                "auth_type": "username/password"
            }
        }
    },
    {
        "name": f"hubspot-{env}",
        "source_type": "hubspot",
        "connection_configuration": {
            "credentials": {
                "credentials_title": "api_key",
                "api_key": config.require_secret("hubspot_api_key")
            },
            "start_date": "2023-01-01T00:00:00Z"
        }
    },
    {
        "name": f"gong-{env}",
        "source_type": "gong",
        "connection_configuration": {
            "access_key": config.require_secret("gong_api_key"),
            "access_key_secret": config.require_secret("gong_api_secret"),
            "start_date": "2023-01-01T00:00:00Z"
        }
    }
]

# Define Airbyte destination configurations
destination_configs = [
    {
        "name": f"snowflake-{env}",
        "destination_type": "snowflake",
        "connection_configuration": {
            "host": config.require("snowflake_account"),
            "role": config.require("snowflake_role"),
            "warehouse": config.require("snowflake_warehouse"),
            "database": config.require("snowflake_database"),
            "schema": f"AIRBYTE_{env.upper()}",
            "username": config.require("snowflake_user"),
            "password": config.require_secret("snowflake_password"),
            "credentials": {
                "auth_type": "username/password"
            }
        }
    }
]

# Define Airbyte connection configurations
connection_configs = [
    {
        "name": f"hubspot-to-snowflake-{env}",
        "source_name": f"hubspot-{env}",
        "destination_name": f"snowflake-{env}",
        "sync_catalog": {
            "streams": [
                {
                    "stream": {
                        "name": "companies",
                        "json_schema": {},
                        "supported_sync_modes": ["full_refresh", "incremental"],
                        "source_defined_cursor": True,
                        "default_cursor_field": ["updatedAt"]
                    },
                    "sync_mode": "incremental",
                    "cursor_field": ["updatedAt"],
                    "destination_sync_mode": "append_dedup",
                    "primary_key": [["id"]]
                },
                {
                    "stream": {
                        "name": "contacts",
                        "json_schema": {},
                        "supported_sync_modes": ["full_refresh", "incremental"],
                        "source_defined_cursor": True,
                        "default_cursor_field": ["updatedAt"]
                    },
                    "sync_mode": "incremental",
                    "cursor_field": ["updatedAt"],
                    "destination_sync_mode": "append_dedup",
                    "primary_key": [["id"]]
                },
                {
                    "stream": {
                        "name": "deals",
                        "json_schema": {},
                        "supported_sync_modes": ["full_refresh", "incremental"],
                        "source_defined_cursor": True,
                        "default_cursor_field": ["updatedAt"]
                    },
                    "sync_mode": "incremental",
                    "cursor_field": ["updatedAt"],
                    "destination_sync_mode": "append_dedup",
                    "primary_key": [["id"]]
                }
            ]
        },
        "schedule": {
            "schedule_type": "cron",
            "cron_expression": "0 */6 * * *"  # Every 6 hours
        },
        "namespace_definition": "destination",
        "namespace_format": "${SOURCE_NAMESPACE}",
        "prefix": "",
        "operation_ids": []
    },
    {
        "name": f"gong-to-snowflake-{env}",
        "source_name": f"gong-{env}",
        "destination_name": f"snowflake-{env}",
        "sync_catalog": {
            "streams": [
                {
                    "stream": {
                        "name": "calls",
                        "json_schema": {},
                        "supported_sync_modes": ["full_refresh", "incremental"],
                        "source_defined_cursor": True,
                        "default_cursor_field": ["lastModifiedAt"]
                    },
                    "sync_mode": "incremental",
                    "cursor_field": ["lastModifiedAt"],
                    "destination_sync_mode": "append_dedup",
                    "primary_key": [["id"]]
                },
                {
                    "stream": {
                        "name": "users",
                        "json_schema": {},
                        "supported_sync_modes": ["full_refresh"],
                        "source_defined_cursor": False
                    },
                    "sync_mode": "full_refresh",
                    "destination_sync_mode": "overwrite",
                    "primary_key": [["id"]]
                }
            ]
        },
        "schedule": {
            "schedule_type": "cron",
            "cron_expression": "0 */12 * * *"  # Every 12 hours
        },
        "namespace_definition": "destination",
        "namespace_format": "${SOURCE_NAMESPACE}",
        "prefix": "",
        "operation_ids": []
    }
]

# Create an Airbyte configuration file
airbyte_config = pulumi.asset.AssetArchive({
    "airbyte_config.json": pulumi.asset.StringAsset(json.dumps({
        "api_key": airbyte_api_key,
        "base_url": airbyte_urls.get(env, airbyte_urls["development"]),
        "username": airbyte_provider["username"],
        "password": airbyte_password,
        "workspace": workspace_config,
        "sources": source_configs,
        "destinations": destination_configs,
        "connections": connection_configs
    }, indent=2))
})

# Export outputs
pulumi.export("airbyte_base_url", airbyte_urls.get(env, airbyte_urls["development"]))
pulumi.export("airbyte_workspace_name", workspace_config["name"])
pulumi.export("airbyte_sources", [source["name"] for source in source_configs])
pulumi.export("airbyte_destinations", [dest["name"] for dest in destination_configs])
pulumi.export("airbyte_connections", [conn["name"] for conn in connection_configs])
pulumi.export("airbyte_environment", env)
