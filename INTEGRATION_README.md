# Sophia AI Integration Management

This directory contains tools for managing integrations with external services (Snowflake, Gong, Vercel, and Estuary) in the Sophia AI platform.

## Quick Start

1. Install required dependencies:
   ```bash
   pip install -r integration_requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp integration.env.example .env
   # Edit .env with your actual credentials
   ```

3. Test connectivity to all services:
   ```bash
   ./test_all_integrations.sh
   ```

4. Manage secrets:
   ```bash
   ./sophia_secrets.py audit
   ```

## Available Tools

### Secret Management

- **sophia_secrets.py**: Unified CLI for managing secrets across Pulumi ESC, GitHub, and local development
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

### Integration Testing

- **unified_integration_test.py**: Tests connectivity to all integrated services and provides a comprehensive report
  ```bash
  ./unified_integration_test.py
  ```

- **test_all_integrations.sh**: Shell script wrapper for unified_integration_test.py with additional environment checks
  ```bash
  ./test_all_integrations.sh
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

### Gong

Required environment variables:
- `GONG_API_KEY`: Your Gong API key
- `GONG_API_SECRET`: Your Gong API secret
- `GONG_ACCESS_KEY`: Access key for enhanced functionality

### Vercel

Required environment variables:
- `VERCEL_ACCESS_TOKEN`: Your Vercel access token
- `VERCEL_PROJECT_ID`: ID of your Vercel project
- `VERCEL_ORG_ID`: ID of your Vercel organization
- `VERCEL_TEAM_ID`: ID of your Vercel team

### Estuary

Required environment variables:
- `ESTUARY_API_KEY`: Your Estuary API key
- `ESTUARY_API_URL`: URL of the Estuary API (default: https://api.estuary.dev)

## Documentation

For more detailed information, see:

- [Integration Management Guide](docs/INTEGRATION_MANAGEMENT_GUIDE.md): Comprehensive guide for managing integrations
- [Secret Management Guide](docs/SECRET_MANAGEMENT_GUIDE.md): Detailed guide for secret management
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md): Guide for deploying Sophia AI with proper integrations

## Security Best Practices

1. **Never commit .env files** to version control
2. **Rotate secrets regularly** using the `sophia_secrets.py rotate` command
3. **Use Pulumi ESC** as the primary source of truth for all secrets
4. **Sync secrets to GitHub** for CI/CD workflows
5. **Audit secret usage** regularly using the `sophia_secrets.py audit` command

## Troubleshooting

If you encounter issues with the integration tools:

1. Verify that all required environment variables are set
2. Check that you have the necessary permissions for each service
3. Run the unified integration test to diagnose connectivity issues
4. Check the service-specific logs for detailed error messages
5. Use the `sophia_secrets.py audit` command to verify secret configuration

For more detailed troubleshooting, see the [Integration Management Guide](docs/INTEGRATION_MANAGEMENT_GUIDE.md).
