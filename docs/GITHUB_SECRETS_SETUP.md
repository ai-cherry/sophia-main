# SOPHIA AI System - GitHub Secrets Setup Guide

## Overview

This guide outlines the process for setting up and managing GitHub secrets for the SOPHIA AI System. GitHub secrets are used to securely store sensitive information such as API keys, passwords, and tokens that are needed for CI/CD workflows.

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Setting Up GitHub Secrets](#setting-up-github-secrets)
4. [Using GitHub Secrets in Workflows](#using-github-secrets-in-workflows)
5. [Rotating GitHub Secrets](#rotating-github-secrets)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Introduction

GitHub secrets provide a secure way to store sensitive information in your GitHub repository. These secrets are encrypted and can only be accessed by GitHub Actions workflows during execution. This ensures that sensitive information is not exposed in your codebase or logs.

For the SOPHIA AI System, GitHub secrets are used for:

- API keys for external services (OpenAI, Pinecone, etc.)
- Database credentials
- Deployment credentials
- JWT secrets
- Integration credentials (HubSpot, Salesforce, etc.)

## Prerequisites

Before setting up GitHub secrets, ensure you have:

1. Admin access to the GitHub repository
2. The necessary secrets to be stored
3. Python 3.11+ installed (for using the automation script)
4. PyGithub and pynacl packages installed:
   ```bash
   pip install PyGithub pynacl
   ```

## Setting Up GitHub Secrets

### Manual Setup

You can manually set up GitHub secrets through the GitHub UI:

1. Navigate to your repository on GitHub
2. Go to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Enter the name and value of the secret
5. Click "Add secret"

### Automated Setup

For easier management, use the provided `configure_github_secrets.py` script:

1. Create a `.env` file with your secrets (or use an existing one)
2. Run the script:
   ```bash
   python configure_github_secrets.py --env-file .env --repo payready/sophia
   ```

The script will:
- Read secrets from the `.env` file
- Connect to the GitHub repository
- Create or update secrets in the repository

### Required Secrets

The following secrets should be set up for the SOPHIA AI System:

#### API Keys
- `OPENAI_API_KEY`: OpenAI API key
- `PINECONE_API_KEY`: Pinecone API key
- `WEAVIATE_API_KEY`: Weaviate API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `ESTUARY_API_KEY`: Estuary Flow API key

#### Database Credentials
- `POSTGRES_PASSWORD`: PostgreSQL password
- `REDIS_PASSWORD`: Redis password
- `SNOWFLAKE_PASSWORD`: Snowflake password

#### Security Tokens
- `JWT_SECRET`: JWT secret key
- `SLACK_SIGNING_SECRET`: Slack signing secret

#### Integration Credentials
- `HUBSPOT_API_KEY`: HubSpot API key
- `HUBSPOT_CLIENT_SECRET`: HubSpot client secret
- `SALESFORCE_PASSWORD`: Salesforce password
- `SALESFORCE_SECURITY_TOKEN`: Salesforce security token
- `GONG_API_KEY`: Gong API key
- `GONG_API_SECRET`: Gong API secret
- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_APP_TOKEN`: Slack app token

#### Infrastructure Credentials
- `AWS_ACCESS_KEY_ID`: AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key
- `PULUMI_ACCESS_TOKEN`: Pulumi access token
- `DOCKERHUB_TOKEN`: Docker Hub token

## Using GitHub Secrets in Workflows

GitHub secrets can be accessed in GitHub Actions workflows using the `secrets` context:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Deploy to production
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
          JWT_SECRET: ${{ secrets.JWT_SECRET }}
        run: ./deploy_production.sh
```

### Important Notes

1. Secrets are not passed to workflows that are triggered by a pull request from a fork
2. Secrets are masked in logs if they appear in output
3. Secrets cannot be used in `if:` conditions in workflows
4. Secrets are exposed as environment variables to the workflow

## Rotating GitHub Secrets

Secrets should be rotated regularly according to security policies. To rotate a GitHub secret:

1. Generate a new secret value in the external service
2. Update the secret in GitHub:
   ```bash
   python configure_github_secrets.py --env-file .env.new --repo payready/sophia
   ```
3. Verify that workflows still work with the new secret
4. Revoke the old secret in the external service

### Automated Rotation

For automated rotation, you can set up a scheduled workflow:

```yaml
name: Rotate Secrets

on:
  schedule:
    - cron: '0 0 1 * *'  # Run on the 1st of every month

jobs:
  rotate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Rotate secrets
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/rotate_secrets.py
```

## Best Practices

1. **Use descriptive names**: Choose secret names that clearly indicate their purpose
2. **Limit access**: Only grant access to secrets to those who need it
3. **Rotate regularly**: Rotate secrets according to security policies
4. **Audit usage**: Regularly audit which workflows use which secrets
5. **Use environment secrets**: For different environments (dev, staging, prod), use environment-specific secrets
6. **Avoid hardcoding**: Never hardcode secrets in your codebase or workflows
7. **Use least privilege**: Only use the secrets that are necessary for each workflow

## Troubleshooting

### Secret Not Available in Workflow

If a secret is not available in a workflow:

1. Check that the secret is correctly set up in the repository
2. Verify that the workflow is using the correct syntax to access the secret
3. Ensure that the workflow has permission to access the secret
4. Check if the workflow is triggered by a pull request from a fork

### Secret Value Changed But Workflow Still Uses Old Value

If a workflow is still using an old secret value:

1. Ensure that the secret was correctly updated in GitHub
2. Check if the workflow is using a cached version of the secret
3. Try re-running the workflow

### Secret Value Visible in Logs

If a secret value is visible in logs:

1. Ensure that the secret is correctly set up in GitHub
2. Check if the workflow is explicitly printing the secret
3. Verify that the secret is being masked correctly by GitHub

### Permission Issues

If you encounter permission issues when setting up secrets:

1. Ensure that you have admin access to the repository
2. Check if there are any organization policies that restrict secret management
3. Verify that your GitHub token has the necessary permissions

## Conclusion

Proper management of GitHub secrets is essential for the security of the SOPHIA AI System. By following the guidelines in this document, you can ensure that sensitive information is securely stored and used in your CI/CD workflows.

For more information, refer to the [GitHub Secrets documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets).
