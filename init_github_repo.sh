#!/bin/bash
# Sophia AI - Initialize GitHub Repository
# This script initializes a GitHub repository and pushes the code

set -e

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install it first."
    exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI is not installed. Please install it first."
    echo "Visit https://cli.github.com/ for installation instructions."
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "You are not authenticated with GitHub. Please run 'gh auth login' first."
    exit 1
fi

# Parse arguments
REPO_NAME="sophia-ai"
DESCRIPTION="Sophia AI - Pay Ready's AI Assistant Orchestrator"
VISIBILITY="private"
ORG="payready"

while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            REPO_NAME="$2"
            shift 2
            ;;
        --description)
            DESCRIPTION="$2"
            shift 2
            ;;
        --visibility)
            VISIBILITY="$2"
            shift 2
            ;;
        --org)
            ORG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create GitHub repository
echo "Creating GitHub repository: $ORG/$REPO_NAME..."
gh repo create "$ORG/$REPO_NAME" --description "$DESCRIPTION" --$VISIBILITY

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
fi

# Add remote
echo "Adding remote..."
git remote add origin "https://github.com/$ORG/$REPO_NAME.git"

# Add all files
echo "Adding files..."
git add .

# Commit
echo "Committing..."
git commit -m "Initial commit"

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

# Set up branch protection
echo "Setting up branch protection..."
gh api "repos/$ORG/$REPO_NAME/branches/main/protection" \
    --method PUT \
    --field required_status_checks='{"strict":true,"contexts":["test"]}' \
    --field enforce_admins=true \
    --field required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
    --field restrictions=null

# Set up GitHub Actions secrets
echo "Setting up GitHub Actions secrets..."
# This will be handled by the sophia_secrets.py script

echo "GitHub repository initialized successfully!"
echo "Repository URL: https://github.com/$ORG/$REPO_NAME"
