# Sophia AI Integration Management Guide

This guide provides comprehensive instructions for managing integrations with external services (Snowflake, Gong, Vercel, and Estuary) in the Sophia AI platform.

## Table of Contents

1. [Overview](#overview)
2. [Secret Management](#secret-management)
   - [Unified Secret Management CLI](#unified-secret-management-cli)
   - [Secret Storage Best Practices](#secret-storage-best-practices)
   - [Secret Rotation](#secret-rotation)
3. [Integration Testing](#integration-testing)
   - [Unified Integration Test](#unified-integration-test)
   - [Service-Specific Testing](#service-specific-testing)
4. [Service-Specific Configuration](#service-specific-configuration)
   - [Snowflake](#snowflake)
   - [Gong](#gong)
   - [Vercel](#vercel)
   - [Estuary](#estuary)
5. [Troubleshooting](#troubleshooting)
6. [Security Best Practices](#security-best-practices)

## Overview

Sophia AI integrates with several external services to provide comprehensive business intelligence and automation capabilities:

- **Snowflake**: Data warehouse for analytics and reporting
- **Gong**: Call recording and analysis for sales intelligence
- **Vercel**: Frontend deployment and hosting
- **Estuary**: Real-time data streaming and ETL

This guide covers how to manage credentials, test connectivity, and troubleshoot issues with these integrations.

## Secret Management

### Unified Secret Management CLI

The `sophia_secrets.py` tool provides a unified interface for managing secrets across different environments:

```bash
# Import secrets from .env file to Pulumi ESC
./sophia_secrets.py import-env --env-file .env --stack development

# Export secrets from Pulumi ESC to .env file
./sophia_secrets.py export-env --env-file .env.new --stack production

# Sync secrets to GitHub repository
./sophia_secrets.py sync-github --repo payready/sophia

# Sync secrets to GitHub organization
./sophia_secrets.py sync-github-org --org payready

# Rotate secrets for a specific service
./sophia_secrets.py rotate --service snowflake

# Audit secret usage and rotation status
./sophia_secrets.py audit
```

### Secret Storage Best Practices

Sophia AI uses a multi-layered approach to secret management:

1. **Pulumi ESC (Encrypted Secrets Configuration)**: The primary source of truth for all secrets
2. **GitHub Secrets**: Used for CI/CD workflows
3. **Local Development**: `.env` files for local development (never committed to version control)

#### Recommended Workflow

1. Store all secrets in Pulumi ESC
2. Sync secrets to GitHub for CI/CD workflows
3. Export secrets to `.env` files for local development
4. Regularly audit and rotate secrets

### Secret Rotation

Regular rotation of secrets is essential for maintaining security. The `sophia_secrets.py rotate` command helps automate this process:

```bash
# Rotate all secrets
./sophia_secrets.py rotate --service all

# Rotate only Snowflake secrets
./sophia_secrets.py rotate --service snowflake
```

The rotation process:

1. Generates new credentials for the service
2. Updates the environment variables
3. Updates Pulumi ESC
4. Syncs to GitHub
5. Updates the rotation timestamp in the configuration

## Integration Testing

### Unified Integration Test

The `unified_integration_test.py` script tests connectivity to all integrated services and provides a comprehensive report:

```bash
# Run the unified integration test
./unified_integration_test.py
```

The test:

1. Checks for required environment variables
2. Tests connectivity to each service
3. Provides detailed error messages and recommendations
4. Generates a JSON report with results

### Service-Specific Testing

For more detailed testing of specific services, you can use the service-specific test scripts:

```bash
# Test Snowflake connectivity
python test_snowflake.py

# Test Gong API
python test_gong.py

# Test Vercel deployment
python test_vercel.py

# Test Estuary data flow
python test_estuary.py
```

## Service-Specific Configuration

### Snowflake

Required environment variables:

- `SNOWFLAKE_ACCOUNT`: Your Snowflake account identifier
- `SNOWFLAKE_USER`: Username for authentication
- `SNOWFLAKE_PASSWORD`: Password for authentication
- `SNOWFLAKE_WAREHOUSE`: Default warehouse to use
- `SNOWFLAKE_DATABASE`: Default database to use
- `SNOWFLAKE_SCHEMA`: Default schema to use
- `SNOWFLAKE_ROLE`: Default role to use

Example configuration:

```
SNOWFLAKE_ACCOUNT=payready
SNOWFLAKE_USER=sophia_service
SNOWFLAKE_PASSWORD=your-secure-password
SNOWFLAKE_WAREHOUSE=SOPHIA_WH
SNOWFLAKE_DATABASE=SOPHIA_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=SOPHIA_ROLE
```

### Gong

Required environment variables:

- `GONG_API_KEY`: Your Gong API key
- `GONG_API_SECRET`: Your Gong API secret
- `GONG_ACCESS_KEY`: Access key for enhanced functionality

Example configuration:

```
GONG_API_KEY=your-gong-api-key
GONG_API_SECRET=your-gong-api-secret
GONG_ACCESS_KEY=your-gong-access-key
```

### Vercel

Required environment variables:

- `VERCEL_ACCESS_TOKEN`: Your Vercel access token
- `VERCEL_PROJECT_ID`: ID of your Vercel project
- `VERCEL_ORG_ID`: ID of your Vercel organization
- `VERCEL_TEAM_ID`: ID of your Vercel team

Example configuration:

```
VERCEL_ACCESS_TOKEN=your-vercel-access-token
VERCEL_PROJECT_ID=prj_123456789
VERCEL_ORG_ID=team_123456789
VERCEL_TEAM_ID=team_123456789
```

### Estuary

Required environment variables:

- `ESTUARY_API_KEY`: Your Estuary API key
- `ESTUARY_API_URL`: URL of the Estuary API (default: https://api.estuary.dev)

Example configuration:

```
ESTUARY_API_KEY=your-estuary-api-key
ESTUARY_API_URL=https://api.estuary.dev
```

## Troubleshooting

### Common Issues

#### Authentication Failures

- Verify that the credentials are correct
- Check that the environment variables are properly set
- Ensure that the API keys have not expired

#### Connection Issues

- Check network connectivity
- Verify that the service is available
- Check for IP restrictions or firewall rules

#### Permission Issues

- Verify that the credentials have the necessary permissions
- Check role assignments for the service accounts

### Diagnostic Tools

- Use the `unified_integration_test.py` script to diagnose connectivity issues
- Check the service-specific logs for detailed error messages
- Use the `sophia_secrets.py audit` command to verify secret configuration

## Security Best Practices

1. **Rotate Secrets Regularly**: Use the `sophia_secrets.py rotate` command to automate rotation
2. **Use Least Privilege**: Assign only the necessary permissions to service accounts
3. **Audit Access**: Regularly review who has access to secrets
4. **Monitor Usage**: Set up alerts for unusual API usage patterns
5. **Secure Storage**: Always use encrypted storage for secrets (Pulumi ESC)
6. **CI/CD Security**: Use GitHub Secrets for CI/CD workflows
7. **Local Development**: Use `.env` files for local development, never commit them to version control

### Recommended Security Workflow

1. Store all secrets in Pulumi ESC
2. Sync secrets to GitHub for CI/CD workflows
3. Export secrets to `.env` files for local development
4. Regularly audit and rotate secrets
5. Monitor API usage for unusual patterns
6. Review access permissions quarterly

By following these guidelines, you can ensure that your integrations are secure, reliable, and properly managed.
