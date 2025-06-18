"""
Sophia AI - Docker Infrastructure as Code
This module defines Docker resources using Pulumi
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
docker_provider = docker.Provider("docker-provider",
    host="unix:///var/run/docker.sock",
    registry_auth=[{
        "address": registry_urls.get(env, registry_urls["development"]),
        "username": registry_username,
        "password": registry_password
    }]
)

# Define Docker image configurations
image_configs = [
    {
        "name": "sophia-api",
        "context": "../",
        "dockerfile": "../Dockerfile",
        "args": {
            "ENV": env,
            "BUILD_DATE": "${BUILD_DATE}",
            "VERSION": "${VERSION}"
        },
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/sophia-api:{env}",
        "always_push": True if env == "production" else False
    },
    {
        "name": "sophia-admin",
        "context": "../sophia_admin_api/",
        "dockerfile": "../sophia_admin_api/Dockerfile",
        "args": {
            "ENV": env,
            "BUILD_DATE": "${BUILD_DATE}",
            "VERSION": "${VERSION}"
        },
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/sophia-admin:{env}",
        "always_push": True if env == "production" else False
    },
    {
        "name": "sophia-frontend",
        "context": "../frontend/",
        "dockerfile": "../frontend/Dockerfile",
        "args": {
            "ENV": env,
            "BUILD_DATE": "${BUILD_DATE}",
            "VERSION": "${VERSION}"
        },
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/sophia-frontend:{env}",
        "always_push": True if env == "production" else False
    },
    {
        "name": "sophia-admin-frontend",
        "context": "../sophia_admin_frontend/",
        "dockerfile": "../sophia_admin_frontend/Dockerfile",
        "args": {
            "ENV": env,
            "BUILD_DATE": "${BUILD_DATE}",
            "VERSION": "${VERSION}"
        },
        "image_name": f"{registry_urls.get(env, registry_urls['development'])}/sophia-admin-frontend:{env}",
        "always_push": True if env == "production" else False
    }
]

# Create Docker images
images = []
for image_config in image_configs:
    image = docker.Image(image_config["name"],
        build=docker.DockerBuildArgs(
            context=image_config["context"],
            dockerfile=image_config["dockerfile"],
            platform="linux/amd64",
            args=image_config["args"]
        ),
        image_name=image_config["image_name"],
        skip_push=not image_config["always_push"],
        provider=docker_provider
    )
    images.append(image)

# Define Docker network configuration
network_config = {
    "name": f"sophia-network-{env}",
    "driver": "bridge",
    "options": {
        "com.docker.network.bridge.enable_icc": "true",
        "com.docker.network.bridge.enable_ip_masquerade": "true"
    },
    "internal": False
}

# Create Docker network
network = docker.Network(network_config["name"],
    name=network_config["name"],
    driver=network_config["driver"],
    options=network_config["options"],
    internal=network_config["internal"],
    provider=docker_provider
)

# Define Docker volume configurations
volume_configs = [
    {
        "name": f"sophia-data-{env}",
        "driver": "local",
        "driver_opts": {
            "type": "none",
            "device": "/data/sophia",
            "o": "bind"
        }
    },
    {
        "name": f"sophia-logs-{env}",
        "driver": "local",
        "driver_opts": {
            "type": "none",
            "device": "/data/logs",
            "o": "bind"
        }
    }
]

# Create Docker volumes
volumes = []
for volume_config in volume_configs:
    volume = docker.Volume(volume_config["name"],
        name=volume_config["name"],
        driver=volume_config["driver"],
        driver_opts=volume_config["driver_opts"],
        provider=docker_provider
    )
    volumes.append(volume)

# Define Docker container configurations
container_configs = [
    {
        "name": f"sophia-api-{env}",
        "image": f"{registry_urls.get(env, registry_urls['development'])}/sophia-api:{env}",
        "ports": [
            {
                "internal": 8000,
                "external": 8000
            }
        ],
        "envs": [
            f"ENVIRONMENT={env}",
            "SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}",
            "SNOWFLAKE_USER=${SNOWFLAKE_USER}",
            "SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}",
            "SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}",
            "SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE}",
            "SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA}",
            "SNOWFLAKE_ROLE=${SNOWFLAKE_ROLE}",
            "GONG_API_KEY=${GONG_API_KEY}",
            "GONG_API_SECRET=${GONG_API_SECRET}",
            "PORTKEY_API_KEY=${PORTKEY_API_KEY}",
            "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}",
            "SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}"
        ],
        "volumes": [
            {
                "volume_name": f"sophia-data-{env}",
                "container_path": "/app/data"
            },
            {
                "volume_name": f"sophia-logs-{env}",
                "container_path": "/app/logs"
            }
        ],
        "networks_advanced": [
            {
                "name": f"sophia-network-{env}",
                "aliases": ["sophia-api"]
            }
        ],
        "restart": "unless-stopped",
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s"
        }
    },
    {
        "name": f"sophia-admin-{env}",
        "image": f"{registry_urls.get(env, registry_urls['development'])}/sophia-admin:{env}",
        "ports": [
            {
                "internal": 8001,
                "external": 8001
            }
        ],
        "envs": [
            f"ENVIRONMENT={env}",
            "SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}",
            "SNOWFLAKE_USER=${SNOWFLAKE_USER}",
            "SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}",
            "SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}",
            "SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE}",
            "SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA}",
            "SNOWFLAKE_ROLE=${SNOWFLAKE_ROLE}",
            "GONG_API_KEY=${GONG_API_KEY}",
            "GONG_API_SECRET=${GONG_API_SECRET}",
            "PORTKEY_API_KEY=${PORTKEY_API_KEY}",
            "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}",
            "SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}"
        ],
        "volumes": [
            {
                "volume_name": f"sophia-data-{env}",
                "container_path": "/app/data"
            },
            {
                "volume_name": f"sophia-logs-{env}",
                "container_path": "/app/logs"
            }
        ],
        "networks_advanced": [
            {
                "name": f"sophia-network-{env}",
                "aliases": ["sophia-admin"]
            }
        ],
        "restart": "unless-stopped",
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8001/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s"
        }
    },
    {
        "name": f"sophia-frontend-{env}",
        "image": f"{registry_urls.get(env, registry_urls['development'])}/sophia-frontend:{env}",
        "ports": [
            {
                "internal": 3000,
                "external": 3000
            }
        ],
        "envs": [
            f"ENVIRONMENT={env}",
            "API_URL=http://sophia-api:8000",
            "NEXT_PUBLIC_API_URL=http://localhost:8000"
        ],
        "networks_advanced": [
            {
                "name": f"sophia-network-{env}",
                "aliases": ["sophia-frontend"]
            }
        ],
        "restart": "unless-stopped",
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:3000"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s"
        }
    },
    {
        "name": f"sophia-admin-frontend-{env}",
        "image": f"{registry_urls.get(env, registry_urls['development'])}/sophia-admin-frontend:{env}",
        "ports": [
            {
                "internal": 3001,
                "external": 3001
            }
        ],
        "envs": [
            f"ENVIRONMENT={env}",
            "API_URL=http://sophia-admin:8001",
            "NEXT_PUBLIC_API_URL=http://localhost:8001"
        ],
        "networks_advanced": [
            {
                "name": f"sophia-network-{env}",
                "aliases": ["sophia-admin-frontend"]
            }
        ],
        "restart": "unless-stopped",
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:3001"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s"
        }
    }
]

# Define MCP server configurations to be merged (ensure these align with mcp.py image naming)
mcp_services_to_add = [
    {
        "base_name": "claude-mcp",
        "port": 8010,
        "envs": [
            "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}",
            "MCP_SERVER_NAME=claude",
            "MCP_SERVER_VERSION=1.0.0"
        ]
    },
    {
        "base_name": "openai-mcp",
        "port": 8011,
        "envs": [
            "OPENAI_API_KEY=${OPENAI_API_KEY}",
            "MCP_SERVER_NAME=openai",
            "MCP_SERVER_VERSION=1.0.0"
        ]
    },
    {
        "base_name": "salesforce-mcp",
        "port": 8012,
        "envs": [
            "SALESFORCE_CLIENT_ID=${SALESFORCE_CLIENT_ID}",
            "SALESFORCE_CLIENT_SECRET=${SALESFORCE_CLIENT_SECRET}",
            "SALESFORCE_USERNAME=${SALESFORCE_USERNAME}",
            "SALESFORCE_PASSWORD=${SALESFORCE_PASSWORD}",
            "MCP_SERVER_NAME=salesforce",
            "MCP_SERVER_VERSION=1.0.0"
        ]
    },
    {
        "base_name": "hubspot-mcp",
        "port": 8013,
        "envs": [
            "HUBSPOT_API_KEY=${HUBSPOT_API_KEY}",
            "MCP_SERVER_NAME=hubspot",
            "MCP_SERVER_VERSION=1.0.0"
        ]
    },
    {
        "base_name": "slack-mcp",
        "port": 8014,
        "envs": [
            "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}",
            "SLACK_APP_TOKEN=${SLACK_APP_TOKEN}",
            "SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}",
            "MCP_SERVER_NAME=slack",
            "MCP_SERVER_VERSION=1.0.0"
        ]
    }
]

for mcp_service in mcp_services_to_add:
    container_configs.append({
        "name": f"{mcp_service['base_name']}-{env}",
        "image": f"{registry_urls.get(env, registry_urls['development'])}/{mcp_service['base_name']}:{env}", # Assumes image is built by mcp.py
        "ports": [
            {
                "internal": mcp_service["port"],
                "external": mcp_service["port"]
            }
        ],
        "envs": [f"ENVIRONMENT={env}"] + mcp_service["envs"],
        "networks_advanced": [
            {
                "name": f"sophia-network-{env}",
                "aliases": [mcp_service["base_name"]]
            }
        ],
        "restart": "unless-stopped",
        "healthcheck": {
            "test": ["CMD", "curl", "-f", f"http://localhost:{mcp_service['port']}/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s"
        }
    })

# Create Docker containers
containers = []
for container_config in container_configs:
    container_volumes = []
    for volume in container_config.get("volumes", []):
        container_volumes.append(docker.ContainerVolumeArgs(
            volume_name=volume["volume_name"],
            container_path=volume["container_path"]
        ))
    
    container_ports = []
    for port in container_config.get("ports", []):
        container_ports.append(docker.ContainerPortArgs(
            internal=port["internal"],
            external=port["external"]
        ))
    
    container_networks = []
    for network in container_config.get("networks_advanced", []):
        container_networks.append(docker.ContainerNetworksAdvancedArgs(
            name=network["name"],
            aliases=network.get("aliases", [])
        ))
    
    healthcheck = None
    if "healthcheck" in container_config:
        healthcheck = docker.ContainerHealthcheckArgs(
            test=container_config["healthcheck"]["test"],
            interval=container_config["healthcheck"]["interval"],
            timeout=container_config["healthcheck"]["timeout"],
            retries=container_config["healthcheck"]["retries"],
            start_period=container_config["healthcheck"]["start_period"]
        )
    
    container = docker.Container(container_config["name"],
        name=container_config["name"],
        image=container_config["image"],
        envs=container_config.get("envs", []),
        ports=container_ports,
        volumes=container_volumes,
        networks_advanced=container_networks,
        restart=container_config.get("restart", "no"),
        healthcheck=healthcheck,
        provider=docker_provider
    )
    containers.append(container)

# Create a Docker Compose file
docker_compose = {
    "version": "3.8",
    "services": {},
    "networks": {
        network_config["name"]: {
            "driver": network_config["driver"],
            "driver_opts": network_config["options"]
        }
    },
    "volumes": {}
}

for container_config in container_configs:
    service_name = container_config["name"]
    docker_compose["services"][service_name] = {
        "image": container_config["image"],
        "environment": [env.split("=")[0] for env in container_config.get("envs", [])],
        "ports": [f"{port['external']}:{port['internal']}" for port in container_config.get("ports", [])],
        "volumes": [f"{volume['volume_name']}:{volume['container_path']}" for volume in container_config.get("volumes", [])],
        "networks": [network["name"] for network in container_config.get("networks_advanced", [])],
        "restart": container_config.get("restart", "no")
    }
    
    if "healthcheck" in container_config:
        docker_compose["services"][service_name]["healthcheck"] = {
            "test": " ".join(container_config["healthcheck"]["test"]),
            "interval": container_config["healthcheck"]["interval"],
            "timeout": container_config["healthcheck"]["timeout"],
            "retries": container_config["healthcheck"]["retries"],
            "start_period": container_config["healthcheck"]["start_period"]
        }

for volume_config in volume_configs:
    docker_compose["volumes"][volume_config["name"]] = {
        "driver": volume_config["driver"],
        "driver_opts": volume_config["driver_opts"]
    }

# Write Docker Compose file
docker_compose_file = pulumi.asset.AssetArchive({
    "docker-compose.yml": pulumi.asset.StringAsset(json.dumps(docker_compose, indent=2))
})

# Export outputs
pulumi.export("docker_registry", registry_urls.get(env, registry_urls["development"]))
pulumi.export("docker_images", [image.image_name for image in images])
pulumi.export("docker_network", network.name)
pulumi.export("docker_volumes", [volume.name for volume in volumes])
pulumi.export("docker_containers", [container.name for container in containers])
pulumi.export("docker_environment", env)
