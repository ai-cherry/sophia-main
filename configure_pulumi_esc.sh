#!/bin/bash
# SOPHIA AI System - Pulumi ESC Configuration Script
# This script configures Pulumi ESC for secure secret management

set -e  # Exit immediately if a command exits with a non-zero status

# Display banner
echo "=================================================="
echo "SOPHIA AI System - Pulumi ESC Configuration"
echo "=================================================="
echo "Starting configuration at $(date)"
echo ""

# Check for Pulumi CLI
if ! command -v pulumi &> /dev/null; then
    echo "Error: Pulumi CLI is required but not installed."
    echo "Please install Pulumi: https://www.pulumi.com/docs/get-started/install/"
    exit 1
fi

# Check for required environment variables
if [ -z "$PULUMI_ACCESS_TOKEN" ]; then
    echo "Error: PULUMI_ACCESS_TOKEN environment variable is not set."
    echo "Please set it with your Pulumi access token."
    exit 1
fi

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found. Using existing environment variables."
fi

# Set default values
ORGANIZATION=${PULUMI_ORGANIZATION:-"payready"}
PROJECT=${PULUMI_PROJECT:-"sophia"}
STACK=${PULUMI_STACK:-"production"}
ENV_FILE=${1:-".env"}

# Function to create or update a secret
create_or_update_secret() {
    local name=$1
    local value=$2
    
    echo "Setting secret: $name"
    
    # Check if secret exists
    if pulumi config get "$name" --show-secrets &> /dev/null; then
        # Update existing secret
        pulumi config set --secret "$name" "$value"
    else
        # Create new secret
        pulumi config set --secret "$name" "$value"
    fi
}

# Function to import secrets from .env file
import_env_secrets() {
    local env_file=$1
    
    echo "Importing secrets from $env_file..."
    
    if [ ! -f "$env_file" ]; then
        echo "Error: $env_file not found."
        exit 1
    fi
    
    # Read each line from .env file
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        if [[ $line =~ ^#.*$ ]] || [[ -z $line ]]; then
            continue
        fi
        
        # Extract key and value
        key=$(echo "$line" | cut -d '=' -f 1)
        value=$(echo "$line" | cut -d '=' -f 2-)
        
        # Skip if key or value is empty
        if [ -z "$key" ] || [ -z "$value" ]; then
            continue
        fi
        
        # Create or update secret
        create_or_update_secret "$key" "$value"
    done < "$env_file"
    
    echo "Secrets imported successfully from $env_file."
}

# Function to sync secrets to GitHub Actions
sync_to_github() {
    echo "Syncing secrets to GitHub Actions..."
    
    # Check if GitHub CLI is installed
    if ! command -v gh &> /dev/null; then
        echo "Warning: GitHub CLI is not installed. Skipping GitHub sync."
        echo "Please install GitHub CLI to sync secrets to GitHub Actions."
        return
    fi
    
    # Check if authenticated with GitHub
    if ! gh auth status &> /dev/null; then
        echo "Error: Not authenticated with GitHub."
        echo "Please run 'gh auth login' to authenticate."
        return
    fi
    
    # Get repository name
    REPO=$(git config --get remote.origin.url | sed 's/.*github.com[:\/]\(.*\)\.git/\1/')
    
    if [ -z "$REPO" ]; then
        echo "Error: Could not determine GitHub repository."
        echo "Please run this script from a git repository with a GitHub remote."
        return
    fi
    
    echo "Syncing secrets to GitHub repository: $REPO"
    
    # Get all secrets from Pulumi
    secrets=$(pulumi config --show-secrets | grep -v "^KEY" | awk '{print $1 "=" $2}')
    
    # Create GitHub Actions secrets
    for secret in $secrets; do
        key=$(echo "$secret" | cut -d '=' -f 1)
        value=$(echo "$secret" | cut -d '=' -f 2-)
        
        echo "Setting GitHub secret: $key"
        echo "$value" | gh secret set "$key" --repo "$REPO"
    done
    
    echo "Secrets synced to GitHub Actions successfully."
}

# Function to list all secrets (masked)
list_secrets() {
    echo "Listing all secrets (values are masked):"
    pulumi config
    echo ""
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  import-env [file]    Import secrets from .env file (default: .env)"
    echo "  sync                 Sync secrets to GitHub Actions"
    echo "  list                 List all secrets (values are masked)"
    echo "  help                 Show this help message"
    echo ""
    echo "Options:"
    echo "  --org, -o [name]     Pulumi organization name (default: $ORGANIZATION)"
    echo "  --project, -p [name] Pulumi project name (default: $PROJECT)"
    echo "  --stack, -s [name]   Pulumi stack name (default: $STACK)"
    echo ""
    echo "Examples:"
    echo "  $0 import-env .env.production"
    echo "  $0 sync --stack staging"
    echo "  $0 list"
    echo ""
}

# Parse command line arguments
COMMAND=${1:-"help"}
shift 1 || true

# Handle the file path for import-env command
if [[ "$COMMAND" == "import-env" && $# -gt 0 && ! "$1" =~ ^-- ]]; then
    ENV_FILE="$1"
    shift 1
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --org|-o)
            ORGANIZATION="$2"
            shift 2
            ;;
        --project|-p)
            PROJECT="$2"
            shift 2
            ;;
        --stack|-s)
            STACK="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Select Pulumi stack
echo "Selecting Pulumi stack: $ORGANIZATION/$PROJECT/$STACK"
pulumi stack select "$ORGANIZATION/$PROJECT/$STACK"

# Execute command
case $COMMAND in
    import-env)
        import_env_secrets "$ENV_FILE"
        ;;
    sync)
        sync_to_github
        ;;
    list)
        list_secrets
        ;;
    help)
        show_usage
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "Configuration completed successfully at $(date)"
echo "=================================================="
