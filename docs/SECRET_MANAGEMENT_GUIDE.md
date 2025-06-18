# SOPHIA AI System - Secret Management Guide

## Overview

This guide outlines the secure management of secrets and sensitive configuration values in the SOPHIA AI System. Following these practices is critical for maintaining the security and integrity of the system.

## Table of Contents

1. [Introduction](#introduction)
2. [Secret Management Principles](#secret-management-principles)
3. [Pulumi ESC](#pulumi-esc)
4. [Environment Variables](#environment-variables)
5. [GitHub Secrets](#github-secrets)
6. [Secret Rotation](#secret-rotation)
7. [Development Workflow](#development-workflow)
8. [Production Workflow](#production-workflow)
9. [Emergency Procedures](#emergency-procedures)
10. [Compliance and Auditing](#compliance-and-auditing)

## Introduction

The SOPHIA AI System integrates with multiple external services, each requiring authentication credentials and API keys. Proper management of these secrets is essential to:

- Prevent unauthorized access to integrated systems
- Maintain compliance with security policies
- Enable secure CI/CD workflows
- Support multiple deployment environments
- Facilitate secret rotation and revocation

## Secret Management Principles

1. **Never hardcode secrets** in source code, configuration files, or documentation
2. **Use environment variables** for runtime configuration
3. **Store secrets securely** using Pulumi ESC (Encrypted Secrets Configuration)
4. **Rotate secrets regularly** according to security policies
5. **Limit access** to secrets based on the principle of least privilege
6. **Audit secret usage** to detect and respond to potential security incidents
7. **Separate secrets** by environment (development, staging, production)
8. **Use consistent naming conventions** for all secrets

## Pulumi ESC

Pulumi ESC (Encrypted Secrets Configuration) is the primary secret management system for SOPHIA. It provides:

- Secure storage of encrypted secrets
- Environment-specific secret management
- Integration with CI/CD pipelines
- Access control and audit logging

### Configuration

The Pulumi ESC configuration is defined in `pulumi-esc-environment.yaml`:

```yaml
name: sophia-esc
description: SOPHIA AI System Encrypted Secrets Configuration
organization: payready

environments:
  - name: development
  - name: staging
  - name: production

secretGroups:
  - name: api-keys
  - name: database-credentials
  - name: security-tokens
  - name: integration-credentials
  - name: infrastructure-credentials
```

### Secret Groups

Secrets are organized into logical groups:

1. **api-keys**: API keys for external services (OpenAI, Pinecone, etc.)
2. **database-credentials**: Database passwords and connection strings
3. **security-tokens**: JWT secrets, signing keys, etc.
4. **integration-credentials**: Credentials for integrated services (HubSpot, Salesforce, etc.)
5. **infrastructure-credentials**: Cloud provider credentials (AWS, etc.)

### Access Control

Access to secrets is controlled through access policies defined in `pulumi-esc-environment.yaml`:

```yaml
accessPolicies:
  - name: admin-access
    secretGroups:
      - api-keys
      - database-credentials
      - security-tokens
      - integration-credentials
      - infrastructure-credentials
    environments:
      - development
      - staging
      - production
    identities:
      - type: user
        name: admin@payready.com
```

## Environment Variables

Environment variables are used to provide secrets to the application at runtime.

### .env Files

For local development, a `.env` file can be used to store environment variables. This file should **never** be committed to version control.

A template file (`env.example`) is provided with placeholder values:

```
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Database Credentials
POSTGRES_PASSWORD=your_postgres_password_here
REDIS_PASSWORD=your_redis_password_here
```

### Docker Environment Variables

For Docker deployments, environment variables are defined in `docker-compose.yml`:

```yaml
services:
  sophia-api:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/sophia
```

## GitHub Secrets

GitHub Actions workflows use secrets stored in the GitHub repository settings.

### Setting Up GitHub Secrets

Use the `configure_github_secrets.py` script to set up GitHub secrets:

```bash
# Install required packages
pip install PyGithub pynacl

# Configure secrets from .env file
python configure_github_secrets.py --env-file .env --repo payready/sophia
```

### GitHub Actions Usage

In GitHub Actions workflows, secrets are accessed using the `${{ secrets.SECRET_NAME }}` syntax:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
        run: ./deploy_production.sh
```

## Secret Rotation

Secrets should be rotated regularly according to the following schedule:

| Secret Type | Rotation Frequency | Responsible Team |
|-------------|-------------------|------------------|
| API Keys | 90 days | DevOps |
| Database Credentials | 180 days | Database Admin |
| JWT Secrets | 365 days | Security |
| Integration Credentials | 90 days | Integration Team |
| Infrastructure Credentials | 90 days | DevOps |

### Rotation Procedure

1. Generate new credentials in the external service
2. Update the secret in Pulumi ESC:
   ```bash
   ./configure_pulumi_esc.sh import-env .env.new
   ```
3. Sync the secret to GitHub:
   ```bash
   ./configure_pulumi_esc.sh sync
   ```
4. Deploy the application with the new secrets
5. Verify functionality with the new secrets
6. Revoke the old credentials in the external service

## Development Workflow

### Setting Up Local Environment

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Fill in your development credentials in `.env`

3. Start the development environment:
   ```bash
   source .env
   docker-compose up -d
   ```

### Adding a New Secret

1. Add the secret to your `.env` file:
   ```
   NEW_API_KEY=your_new_api_key_here
   ```

2. Import the secret to Pulumi ESC:
   ```bash
   ./configure_pulumi_esc.sh import-env .env --stack development
   ```

3. Update `env.example` with a placeholder for the new secret:
   ```
   NEW_API_KEY=your_new_api_key_here
   ```

4. Update the application code to use the new secret

## Production Workflow

### Deploying Secrets to Production

1. Create a production-specific `.env` file:
   ```bash
   cp env.example .env.production
   ```

2. Fill in production credentials in `.env.production`

3. Import the secrets to Pulumi ESC:
   ```bash
   ./configure_pulumi_esc.sh import-env .env.production --stack production
   ```

4. Sync the secrets to GitHub:
   ```bash
   ./configure_pulumi_esc.sh sync --stack production
   ```

5. Deploy the application:
   ```bash
   ./deploy_production.sh
   ```

### Updating Production Secrets

1. Update the production `.env` file:
   ```bash
   nano .env.production
   ```

2. Import the updated secrets to Pulumi ESC:
   ```bash
   ./configure_pulumi_esc.sh import-env .env.production --stack production
   ```

3. Sync the secrets to GitHub:
   ```bash
   ./configure_pulumi_esc.sh sync --stack production
   ```

4. Redeploy the application:
   ```bash
   ./deploy_production.sh
   ```

## Emergency Procedures

### Secret Compromise Response

If a secret is compromised:

1. Immediately revoke the compromised credentials in the external service
2. Generate new credentials
3. Update the secret in Pulumi ESC:
   ```bash
   ./configure_pulumi_esc.sh import-env .env.emergency --stack production
   ```
4. Sync the secret to GitHub:
   ```bash
   ./configure_pulumi_esc.sh sync --stack production
   ```
5. Deploy the application with the new secrets:
   ```bash
   ./deploy_production.sh
   ```
6. Document the incident and perform a post-mortem analysis

### Emergency Access

In case of emergency, authorized personnel can access secrets through:

1. Pulumi ESC web console (requires Pulumi account with appropriate permissions)
2. GitHub repository settings (requires GitHub admin access)
3. Backup secrets stored in a secure location (requires physical access or multi-factor authentication)

## Compliance and Auditing

### Audit Logging

All secret access and modifications are logged:

1. Pulumi ESC maintains an audit log of all secret operations
2. GitHub maintains an audit log of all secret access in Actions workflows
3. Application logs record the use of secrets (without revealing the actual values)

### Compliance Requirements

The secret management practices in this guide are designed to comply with:

1. SOC 2 Type II requirements
2. GDPR data protection requirements
3. HIPAA security requirements (where applicable)
4. PCI DSS requirements (where applicable)

### Regular Audits

Conduct regular audits of secret management practices:

1. Quarterly review of all secrets and their rotation status
2. Annual review of access policies and permissions
3. Regular testing of emergency procedures
4. Verification of secret usage in application code

## Conclusion

Proper secret management is critical to the security of the SOPHIA AI System. By following the practices outlined in this guide, you can ensure that secrets are managed securely throughout the development and deployment lifecycle.

For questions or concerns about secret management, contact the security team at security@payready.com.
