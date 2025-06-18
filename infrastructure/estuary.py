"""
Sophia AI - Estuary Integration Infrastructure as Code
This module defines Estuary data flow resources using Pulumi
"""

import pulumi
import json
import pulumi_command as command
from pulumi import Config

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get Estuary credentials from Pulumi config (encrypted)
estuary_api_key = config.require_secret("estuary_api_key")
estuary_api_url = config.get("estuary_api_url") or "https://api.estuary.tech"

# Define environment-specific configurations
collection_names = {
    "development": "sophia_dev",
    "staging": "sophia_staging",
    "production": "sophia_prod"
}

# Create an Estuary collection using the Estuary API
# This is a custom resource that uses the Pulumi Command provider to call the Estuary API
estuary_collection = command.local.Command("estuary_collection",
    create=pulumi.Output.concat(
        "curl -X POST '", estuary_api_url, "/collections' ",
        "-H 'Content-Type: application/json' ",
        "-H 'Authorization: Bearer ", estuary_api_key, "' ",
        "-d '{",
        "\"name\": \"", collection_names.get(env, collection_names["development"]), "\",",
        "\"description\": \"Sophia AI data collection for ", env, " environment\"",
        "}'"
    ),
    update=pulumi.Output.concat(
        "curl -X PUT '", estuary_api_url, "/collections/${COLLECTION_UUID}' ",
        "-H 'Content-Type: application/json' ",
        "-H 'Authorization: Bearer ", estuary_api_key, "' ",
        "-d '{",
        "\"name\": \"", collection_names.get(env, collection_names["development"]), "\",",
        "\"description\": \"Sophia AI data collection for ", env, " environment\"",
        "}'"
    ),
    delete=pulumi.Output.concat(
        "curl -X DELETE '", estuary_api_url, "/collections/${COLLECTION_UUID}' ",
        "-H 'Authorization: Bearer ", estuary_api_key, "'"
    ),
    environment={
        "COLLECTION_UUID": "${COLLECTION_UUID}"  # This would be populated by the create command in a real implementation
    }
)

# Define Estuary data flow configuration
data_flow_config = {
    "name": f"sophia_{env}_data_flow",
    "description": f"Sophia AI data flow for {env} environment",
    "source": {
        "type": "snowflake",
        "config": {
            "account": "${SNOWFLAKE_ACCOUNT}",
            "user": "${SNOWFLAKE_USER}",
            "password": "${SNOWFLAKE_PASSWORD}",
            "warehouse": "${SNOWFLAKE_WAREHOUSE}",
            "database": "${SNOWFLAKE_DATABASE}",
            "schema": "${SNOWFLAKE_SCHEMA}",
            "query": "SELECT * FROM call_data"
        }
    },
    "destination": {
        "type": "estuary",
        "config": {
            "collection": collection_names.get(env, collection_names["development"])
        }
    },
    "schedule": {
        "frequency": "hourly"
    }
}

# Create an Estuary data flow using the Estuary API
estuary_data_flow = command.local.Command("estuary_data_flow",
    create=pulumi.Output.concat(
        "curl -X POST '", estuary_api_url, "/flows' ",
        "-H 'Content-Type: application/json' ",
        "-H 'Authorization: Bearer ", estuary_api_key, "' ",
        "-d '", json.dumps(data_flow_config), "'"
    ),
    update=pulumi.Output.concat(
        "curl -X PUT '", estuary_api_url, "/flows/${FLOW_UUID}' ",
        "-H 'Content-Type: application/json' ",
        "-H 'Authorization: Bearer ", estuary_api_key, "' ",
        "-d '", json.dumps(data_flow_config), "'"
    ),
    delete=pulumi.Output.concat(
        "curl -X DELETE '", estuary_api_url, "/flows/${FLOW_UUID}' ",
        "-H 'Authorization: Bearer ", estuary_api_key, "'"
    ),
    environment={
        "FLOW_UUID": "${FLOW_UUID}",  # This would be populated by the create command in a real implementation
        "SNOWFLAKE_ACCOUNT": "${SNOWFLAKE_ACCOUNT}",
        "SNOWFLAKE_USER": "${SNOWFLAKE_USER}",
        "SNOWFLAKE_PASSWORD": "${SNOWFLAKE_PASSWORD}",
        "SNOWFLAKE_WAREHOUSE": "${SNOWFLAKE_WAREHOUSE}",
        "SNOWFLAKE_DATABASE": "${SNOWFLAKE_DATABASE}",
        "SNOWFLAKE_SCHEMA": "${SNOWFLAKE_SCHEMA}"
    }
)

# Create an Estuary API configuration file
estuary_config = pulumi.asset.AssetArchive({
    "estuary_config.json": pulumi.asset.StringAsset(json.dumps({
        "api_key": estuary_api_key,
        "api_url": estuary_api_url,
        "collection": collection_names.get(env, collection_names["development"]),
        "environment": env
    }, indent=2))
})

# Export outputs
pulumi.export("estuary_collection", collection_names.get(env, collection_names["development"]))
pulumi.export("estuary_api_url", estuary_api_url)
pulumi.export("estuary_environment", env)
