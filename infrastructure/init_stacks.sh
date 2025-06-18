#!/bin/bash
# Sophia AI - Initialize Pulumi Stacks
# This script initializes Pulumi stacks for different environments

set -e

# Check if Pulumi CLI is installed
if ! command -v pulumi &> /dev/null; then
    echo "Pulumi CLI is not installed. Please install it first."
    echo "Visit https://www.pulumi.com/docs/get-started/install/ for installation instructions."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize Pulumi stacks
echo "Initializing Pulumi stacks..."

# Development stack
echo "Initializing development stack..."
pulumi stack init development
pulumi config set environment development --stack development

# Staging stack
echo "Initializing staging stack..."
pulumi stack init staging
pulumi config set environment staging --stack staging

# Production stack
echo "Initializing production stack..."
pulumi stack init production
pulumi config set environment production --stack production

echo "Pulumi stacks initialized successfully!"
echo ""
echo "To set configuration values for each stack, use the following commands:"
echo ""
echo "For development stack:"
echo "pulumi stack select development"
echo "pulumi config set snowflake:account <value>"
echo "pulumi config set --secret snowflake:password <value>"
echo "... and so on for other configuration values"
echo ""
echo "For staging stack:"
echo "pulumi stack select staging"
echo "pulumi config set snowflake:account <value>"
echo "pulumi config set --secret snowflake:password <value>"
echo "... and so on for other configuration values"
echo ""
echo "For production stack:"
echo "pulumi stack select production"
echo "pulumi config set snowflake:account <value>"
echo "pulumi config set --secret snowflake:password <value>"
echo "... and so on for other configuration values"
echo ""
echo "To deploy a stack, use the following command:"
echo "pulumi stack select <stack-name>"
echo "pulumi up"
