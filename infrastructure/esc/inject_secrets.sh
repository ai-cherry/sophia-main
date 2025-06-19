#!/bin/bash
# Sophia AI - Inject Secrets from Pulumi ESC
# This script injects secrets from Pulumi ESC into GitHub Actions environment variables.

set -e

# Parse arguments
ORGANIZATION="ai-cherry"
PROJECT="sophia"
ENVIRONMENT="production"
SERVICE=""
OUTPUT_FILE=""
GITHUB_ENV_FILE="${GITHUB_ENV:-/dev/null}"

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --organization|--org|-o)
      ORGANIZATION="$2"
      shift
      shift
      ;;
    --project|-p)
      PROJECT="$2"
      shift
      shift
      ;;
    --environment|--env|-e)
      ENVIRONMENT="$2"
      shift
      shift
      ;;
    --service|-s)
      SERVICE="$2"
      shift
      shift
      ;;
    --output|-f)
      OUTPUT_FILE="$2"
      shift
      shift
      ;;
    --github-env)
      GITHUB_ENV_FILE="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Injecting secrets from Pulumi ESC into GitHub Actions environment variables..."
echo "Organization: $ORGANIZATION"
echo "Project: $PROJECT"
echo "Environment: $ENVIRONMENT"
echo "Service: $SERVICE"
echo "GitHub Environment File: $GITHUB_ENV_FILE"

# Check if Pulumi is installed
if ! command -v pulumi &> /dev/null; then
  echo "Pulumi is not installed. Installing..."
  curl -fsSL https://get.pulumi.com | sh
  export PATH=$PATH:$HOME/.pulumi/bin
fi

# Check if Pulumi is logged in
if ! pulumi whoami &> /dev/null; then
  if [ -z "$PULUMI_ACCESS_TOKEN" ]; then
    echo "PULUMI_ACCESS_TOKEN is not set. Please set it before running this script."
    exit 1
  fi
  
  echo "Logging in to Pulumi..."
  pulumi login
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  echo "Python 3 is not installed. Please install it before running this script."
  exit 1
fi

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Get the service registry
REGISTRY_FILE="$PROJECT_ROOT/infrastructure/integration_registry.json"
if [ ! -f "$REGISTRY_FILE" ]; then
  echo "Service registry not found at $REGISTRY_FILE"
  exit 1
fi

# If no service is specified, get all services from the registry
if [ -z "$SERVICE" ]; then
  SERVICES=$(jq -r 'keys[]' "$REGISTRY_FILE")
else
  SERVICES="$SERVICE"
fi

# Create output file if specified
if [ -n "$OUTPUT_FILE" ]; then
  echo "{}" > "$OUTPUT_FILE"
fi

# Process each service
for SERVICE in $SERVICES; do
  echo "Processing service: $SERVICE"
  
  # Get secret keys for the service
  SECRET_KEYS=$(jq -r ".[\"$SERVICE\"].secret_keys[]" "$REGISTRY_FILE" 2>/dev/null || echo "")
  
  if [ -z "$SECRET_KEYS" ]; then
    echo "No secret keys found for service: $SERVICE"
    continue
  fi
  
  # Get each secret and inject it into the environment
  for KEY in $SECRET_KEYS; do
    echo "Getting secret: ${SERVICE}_${KEY}"
    
    # Get the secret using the Python script
    SECRET_VALUE=$(python3 "$PROJECT_ROOT/infrastructure/esc/get_secret.py" \
      --service "$SERVICE" \
      --key "$KEY" \
      --organization "$ORGANIZATION" \
      --project "$PROJECT" \
      --environment "$ENVIRONMENT" 2>/dev/null || echo "")
    
    if [ -z "$SECRET_VALUE" ]; then
      echo "Secret not found: ${SERVICE}_${KEY}"
      continue
    fi
    
    # Inject the secret into the GitHub environment
    ENV_VAR_NAME="${SERVICE}_${KEY}"
    echo "Injecting secret: $ENV_VAR_NAME"
    echo "$ENV_VAR_NAME=$SECRET_VALUE" >> "$GITHUB_ENV_FILE"
    
    # Add to output file if specified
    if [ -n "$OUTPUT_FILE" ]; then
      # Update the JSON file with the new secret (masked)
      jq --arg service "$SERVICE" --arg key "$KEY" --arg value "${SECRET_VALUE:0:3}...${SECRET_VALUE: -3}" \
        '.[$service] = (.[$service] // {}) | .[$service][$key] = $value' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
      mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
    fi
  done
  
  # Get config keys for the service
  CONFIG_KEYS=$(jq -r ".[\"$SERVICE\"].config_keys[]" "$REGISTRY_FILE" 2>/dev/null || echo "")
  
  if [ -z "$CONFIG_KEYS" ]; then
    echo "No config keys found for service: $SERVICE"
    continue
  fi
  
  # Get each config and inject it into the environment
  for KEY in $CONFIG_KEYS; do
    echo "Getting config: ${SERVICE}_${KEY}"
    
    # Get the config using the Python script
    CONFIG_VALUE=$(python3 "$PROJECT_ROOT/infrastructure/esc/get_secret.py" \
      --service "$SERVICE" \
      --key "$KEY" \
      --organization "$ORGANIZATION" \
      --project "$PROJECT" \
      --environment "$ENVIRONMENT" \
      --config 2>/dev/null || echo "")
    
    if [ -z "$CONFIG_VALUE" ]; then
      echo "Config not found: ${SERVICE}_${KEY}"
      continue
    fi
    
    # Inject the config into the GitHub environment
    ENV_VAR_NAME="${SERVICE}_${KEY}"
    echo "Injecting config: $ENV_VAR_NAME"
    echo "$ENV_VAR_NAME=$CONFIG_VALUE" >> "$GITHUB_ENV_FILE"
    
    # Add to output file if specified
    if [ -n "$OUTPUT_FILE" ]; then
      # Update the JSON file with the new config
      jq --arg service "$SERVICE" --arg key "$KEY" --arg value "$CONFIG_VALUE" \
        '.[$service] = (.[$service] // {}) | .[$service][$key] = $value' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
      mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
    fi
  done
done

echo "Secrets and configs injected successfully."

