#!/bin/bash
# Sophia AI - Import Secrets to Pulumi ESC
# This script imports secrets from a .env file to Pulumi ESC

set -e

# Check if Pulumi CLI is installed
if ! command -v pulumi &> /dev/null; then
    echo "Pulumi CLI is not installed. Please install it first."
    echo "Visit https://www.pulumi.com/docs/get-started/install/ for installation instructions."
    exit 1
fi

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <env-file> <stack-name>"
    echo "Example: $0 ../.env development"
    exit 1
fi

ENV_FILE=$1
STACK_NAME=$2

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Environment file $ENV_FILE does not exist."
    exit 1
fi

# Select the stack
echo "Selecting stack $STACK_NAME..."
pulumi stack select $STACK_NAME

# Import secrets from .env file
echo "Importing secrets from $ENV_FILE to Pulumi ESC..."

# Snowflake secrets
if grep -q "SNOWFLAKE_ACCOUNT" "$ENV_FILE"; then
    SNOWFLAKE_ACCOUNT=$(grep "SNOWFLAKE_ACCOUNT" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting snowflake:account..."
    pulumi config set snowflake:account "$SNOWFLAKE_ACCOUNT"
fi

if grep -q "SNOWFLAKE_USER" "$ENV_FILE"; then
    SNOWFLAKE_USER=$(grep "SNOWFLAKE_USER" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting snowflake:user..."
    pulumi config set snowflake:user "$SNOWFLAKE_USER"
fi

if grep -q "SNOWFLAKE_PASSWORD" "$ENV_FILE"; then
    SNOWFLAKE_PASSWORD=$(grep "SNOWFLAKE_PASSWORD" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting snowflake:password (secret)..."
    pulumi config set --secret snowflake:password "$SNOWFLAKE_PASSWORD"
fi

if grep -q "SNOWFLAKE_WAREHOUSE" "$ENV_FILE"; then
    SNOWFLAKE_WAREHOUSE=$(grep "SNOWFLAKE_WAREHOUSE" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting snowflake:warehouse..."
    pulumi config set snowflake:warehouse "$SNOWFLAKE_WAREHOUSE"
fi

if grep -q "SNOWFLAKE_DATABASE" "$ENV_FILE"; then
    SNOWFLAKE_DATABASE=$(grep "SNOWFLAKE_DATABASE" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting snowflake:database..."
    pulumi config set snowflake:database "$SNOWFLAKE_DATABASE"
fi

if grep -q "SNOWFLAKE_SCHEMA" "$ENV_FILE"; then
    SNOWFLAKE_SCHEMA=$(grep "SNOWFLAKE_SCHEMA" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting snowflake:schema..."
    pulumi config set snowflake:schema "$SNOWFLAKE_SCHEMA"
fi

if grep -q "SNOWFLAKE_ROLE" "$ENV_FILE"; then
    SNOWFLAKE_ROLE=$(grep "SNOWFLAKE_ROLE" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting snowflake:role..."
    pulumi config set snowflake:role "$SNOWFLAKE_ROLE"
fi

# Gong secrets
if grep -q "GONG_API_KEY" "$ENV_FILE"; then
    GONG_API_KEY=$(grep "GONG_API_KEY" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting gong:api_key (secret)..."
    pulumi config set --secret gong:api_key "$GONG_API_KEY"
fi

if grep -q "GONG_API_SECRET" "$ENV_FILE"; then
    GONG_API_SECRET=$(grep "GONG_API_SECRET" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting gong:api_secret (secret)..."
    pulumi config set --secret gong:api_secret "$GONG_API_SECRET"
fi

# Vercel secrets
if grep -q "VERCEL_ACCESS_TOKEN" "$ENV_FILE"; then
    VERCEL_ACCESS_TOKEN=$(grep "VERCEL_ACCESS_TOKEN" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting vercel:token (secret)..."
    pulumi config set --secret vercel:token "$VERCEL_ACCESS_TOKEN"
fi

if grep -q "VERCEL_TEAM_ID" "$ENV_FILE"; then
    VERCEL_TEAM_ID=$(grep "VERCEL_TEAM_ID" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting vercel:team_id..."
    pulumi config set vercel:team_id "$VERCEL_TEAM_ID"
fi

# Estuary secrets
if grep -q "ESTUARY_API_KEY" "$ENV_FILE"; then
    ESTUARY_API_KEY=$(grep "ESTUARY_API_KEY" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting estuary:api_key (secret)..."
    pulumi config set --secret estuary:api_key "$ESTUARY_API_KEY"
fi

if grep -q "ESTUARY_API_URL" "$ENV_FILE"; then
    ESTUARY_API_URL=$(grep "ESTUARY_API_URL" "$ENV_FILE" | cut -d '=' -f2)
    echo "Setting estuary:api_url..."
    pulumi config set estuary:api_url "$ESTUARY_API_URL"
fi

echo "Secrets imported successfully!"
echo ""
echo "To view the current configuration, use the following command:"
echo "pulumi config"
echo ""
echo "To deploy the stack, use the following command:"
echo "pulumi up"
