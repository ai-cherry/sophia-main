#!/bin/bash
# Sophia AI - Setup Pulumi ESC Environment
# This script sets up the Pulumi ESC environment for use in GitHub Actions workflows.

set -e

# Parse arguments
ORGANIZATION="ai-cherry"
PROJECT="sophia"
ENVIRONMENT="production"
SYNC_SECRETS=true
SYNC_DIRECTION="github-to-pulumi"
OUTPUT_FILE=""

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
    --no-sync)
      SYNC_SECRETS=false
      shift
      ;;
    --direction|-d)
      SYNC_DIRECTION="$2"
      shift
      shift
      ;;
    --output|-o)
      OUTPUT_FILE="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Setting up Pulumi ESC environment..."
echo "Organization: $ORGANIZATION"
echo "Project: $PROJECT"
echo "Environment: $ENVIRONMENT"
echo "Sync Secrets: $SYNC_SECRETS"
echo "Sync Direction: $SYNC_DIRECTION"

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

# Create Pulumi ESC stack if it doesn't exist
cd "$(dirname "$0")"

if ! pulumi stack ls | grep -q "$ENVIRONMENT"; then
  echo "Creating Pulumi ESC stack: $ENVIRONMENT..."
  pulumi stack init "$ENVIRONMENT"
fi

echo "Selecting Pulumi ESC stack: $ENVIRONMENT..."
pulumi stack select "$ENVIRONMENT"

# Set config values
echo "Setting config values..."
pulumi config set organization "$ORGANIZATION"
pulumi config set project "$PROJECT"
pulumi config set environment "$ENVIRONMENT"

# Sync secrets if requested
if [ "$SYNC_SECRETS" = true ]; then
  echo "Synchronizing secrets from GitHub to Pulumi ESC..."
  
  # Check if GitHub CLI is installed
  if ! command -v gh &> /dev/null; then
    echo "GitHub CLI is not installed. Installing..."
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh -y
  fi
  
  # Check if GitHub CLI is logged in
  if ! gh auth status &> /dev/null; then
    if [ -z "$GITHUB_TOKEN" ]; then
      echo "GITHUB_TOKEN is not set. Please set it before running this script."
      exit 1
    fi
    
    echo "Logging in to GitHub..."
    echo "$GITHUB_TOKEN" | gh auth login --with-token
  fi
  
  # Run the sync script
  echo "Running sync script..."
  bash ../esc/sync_secrets_ci.sh \
    --github-org "$ORGANIZATION" \
    --pulumi-org "$ORGANIZATION" \
    --pulumi-env "$PROJECT-$ENVIRONMENT" \
    --direction "$SYNC_DIRECTION" \
    --output "${OUTPUT_FILE:-sync_results.json}"
fi

echo "Pulumi ESC environment setup complete."

