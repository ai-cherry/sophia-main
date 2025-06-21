# Sophia AI Secrets Management Guide

## 🔐 **PERMANENT SECRET MANAGEMENT SOLUTION**

**IMPORTANT**: Sophia AI now uses a **PERMANENT GitHub Organization Secrets → Pulumi ESC** solution that eliminates all manual secret management.

### **✅ What's Automated (No More Manual Work)**
- ❌ No more `.env` file management
- ❌ No more manual secret configuration
- ❌ No more environment variable setup
- ❌ No more API key sharing/copying
- ✅ All secrets managed in [GitHub ai-cherry organization](https://github.com/ai-cherry)
- ✅ Automatic synchronization to Pulumi ESC
- ✅ Backend automatically loads all secrets

### **🔑 How It Works**
```
GitHub Organization Secrets (ai-cherry)
           ↓
    GitHub Actions (automatic sync)
           ↓
    Pulumi ESC Environments
           ↓
    Sophia AI Backend (automatic loading)
```

### **📋 Required GitHub Organization Secrets**

All secrets are managed in the [ai-cherry GitHub organization](https://github.com/ai-cherry/settings/secrets/actions):

#### **Infrastructure Secrets**
- `PULUMI_ACCESS_TOKEN` - Pulumi Cloud access token
- `PULUMI_ORG` - Set to `scoobyjava-org`

#### **AI Service Secrets**
- `OPENAI_API_KEY` - OpenAI API key (starts with `sk-`)
- `ANTHROPIC_API_KEY` - Anthropic Claude API key

#### **Business Integration Secrets**
- `GONG_ACCESS_KEY` - Gong API access key
- `GONG_CLIENT_SECRET` - Gong API client secret
- `GONG_URL` - Your Gong instance URL
- `HUBSPOT_API_TOKEN` - HubSpot API token
- `SLACK_BOT_TOKEN` - Slack bot token (starts with `xoxb-`)

#### **Data Infrastructure Secrets**
- `SNOWFLAKE_ACCOUNT` - Snowflake account identifier
- `SNOWFLAKE_USER` - Snowflake username
- `SNOWFLAKE_PASSWORD` - Snowflake password
- `PINECONE_API_KEY` - Pinecone vector database API key

#### **Cloud Service Secrets**
- `LAMBDA_LABS_API_KEY` - Lambda Labs GPU compute API key
- `VERCEL_ACCESS_TOKEN` - Vercel deployment token

### **🚀 Quick Setup**

```bash
# 1. Clone repository
git clone https://github.com/ai-cherry/sophia-main.git
cd sophia-main

# 2. Set Pulumi organization
export PULUMI_ORG=scoobyjava-org

# 3. Set Pulumi access token
export PULUMI_ACCESS_TOKEN=your_token_here

# 4. Sync secrets from Pulumi ESC
python scripts/setup_all_secrets_once.py

# 5. Test everything works
python scripts/test_permanent_solution.py

# 6. Start developing - all secrets automatically available!
python backend/main.py
```

### **🔧 Troubleshooting the Permanent Solution**

#### **"Secret not found" errors**
1. Check [GitHub organization secrets](https://github.com/ai-cherry/settings/secrets/actions)
2. Verify secret name matches exactly
3. Re-run sync: `python scripts/sync_github_to_pulumi.sh`

#### **"Pulumi ESC access denied"**
1. Update `PULUMI_ACCESS_TOKEN` in GitHub organization
2. Test access: `export PULUMI_ORG=scoobyjava-org && pulumi whoami`

#### **Backend can't load secrets**
1. Run diagnostic: `python scripts/test_permanent_solution.py`
2. Check ESC access: `pulumi env open scoobyjava-org/default/sophia-ai-production`

---

## 📚 **LEGACY DOCUMENTATION (For Reference Only)**

**NOTE**: The following sections are kept for reference but are no longer needed with the permanent solution.

## Overview

This guide provides comprehensive instructions for managing secrets and environment variables across different Sophia AI repositories and environments.

The Sophia AI secrets management system provides a unified approach to handling sensitive information across all repositories and environments. It addresses the following key challenges:

1. **Consistency**: Ensuring all repositories have the same set of required secrets
2. **Security**: Keeping secrets secure and preventing accidental exposure
3. **Synchronization**: Maintaining consistency across different environments
4. **Validation**: Verifying that all required secrets are present and valid
5. **Portability**: Easily transferring secrets between repositories and environments

## Pulumi ESC (Environment Secrets and Configuration)

Pulumi ESC provides centralized secret management for the Sophia AI system. It offers:

- Encrypted storage of secrets
- Environment-based organization
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

# Configure secrets directly
python configure_github_secrets.py --repo payready/sophia
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
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
        run: python scripts/deploy_production_mcp.py
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
2. Update the secret in GitHub organization settings
3. Run `./scripts/sync_github_to_pulumi.sh` to update ESC
4. Deploy the application with the new secrets
5. Verify functionality with the new secrets
6. Revoke the old credentials in the external service

## Tools

The secrets management system includes the following tools:

### 1. `secrets_manager.py`

A comprehensive script for managing secrets and environment variables. It can:

- Detect missing environment variables
- Sync secrets between GitHub and Pulumi ESC
- Validate secret configurations
- Generate template files when needed

### 2. `setup_new_repo.py`

A script to automate the setup of a new Sophia AI repository with all the necessary secrets and configurations. It:

- Creates a new directory for the repository
- Initializes a Git repository
- Copies the secrets_manager.py script
- Pulls secrets from Pulumi ESC
- Sets up the necessary configuration files
- Creates a README.md file with setup instructions

## Secret Storage Locations

The secrets management system supports multiple storage locations:

### 1. Local .env Files

- **Purpose**: Development environments and local testing
- **Format**: Key-value pairs in a .env file
- **Security**: Not committed to Git (included in .gitignore)
- **Usage**: Loaded by the application at runtime

### 2. Pulumi ESC (Environment Secrets and Configuration)

- **Purpose**: Centralized secret management for all environments
- **Format**: JSON object stored in Pulumi's secure storage
- **Security**: Encrypted at rest and in transit
- **Usage**: Accessed via Pulumi API or CLI

### 3. GitHub Secrets

- **Purpose**: CI/CD pipelines and GitHub Actions
- **Format**: Key-value pairs stored in GitHub repository settings
- **Security**: Encrypted at rest and masked in logs
- **Usage**: Accessed via GitHub Actions environment variables

## Required Environment Variables

The following environment variables are required for Sophia AI to function properly:

### Core API Keys

- `ANTHROPIC_API_KEY`: Claude API key for AI capabilities
- `OPENAI_API_KEY`: OpenAI API key for AI capabilities (optional)
- `PULUMI_ACCESS_TOKEN`: Pulumi access token for infrastructure management

### Slack Integration

- `SLACK_BOT_TOKEN`: Slack bot token for Slack integration
- `SLACK_APP_TOKEN`: Slack app token for Slack integration
- `SLACK_SIGNING_SECRET`: Slack signing secret for Slack integration

### Linear Integration

- `LINEAR_API_TOKEN`: Linear API token for project management integration
- `LINEAR_WORKSPACE_ID`: Linear workspace ID for project management integration

### Gong Integration

- `GONG_CLIENT_ID`: Gong client ID for call analysis integration
- `GONG_CLIENT_SECRET`: Gong client secret for call analysis integration

### Database Credentials

- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name

### Vercel Integration

- `VERCEL_ACCESS_TOKEN`: Vercel access token for deployment integration
- `VERCEL_TEAM_ID`: Vercel team ID for deployment integration

### Lambda Labs Integration

- `LAMBDA_LABS_API_KEY`: Lambda Labs API key for compute resources

### Vector Database Integration

- `PINECONE_API_KEY`: Pinecone API key for vector database
- `WEAVIATE_API_KEY`: Weaviate API key for vector database

### Snowflake Integration

- `SNOWFLAKE_ACCOUNT`: Snowflake account identifier
- `SNOWFLAKE_USER`: Snowflake username
- `SNOWFLAKE_PASSWORD`: Snowflake password
- `SNOWFLAKE_DATABASE`: Snowflake database name

### Estuary Integration

- `ESTUARY_API_KEY`: Estuary API key for data flow management

### Airbyte Integration

- `AIRBYTE_API_KEY`: Airbyte API key for data integration

### Environment Configuration

- `SOPHIA_ENVIRONMENT`: Environment name (development, staging, production)
- `PULUMI_ORGANIZATION`: Pulumi organization name
- `PULUMI_PROJECT`: Pulumi project name

## Optional Environment Variables

The following environment variables are optional and have default values:

- `CLAUDE_MODEL`: Claude model to use (default: claude-3-5-sonnet-20241022)
- `CLAUDE_MAX_TOKENS`: Maximum tokens for Claude responses (default: 4096)
- `CLAUDE_ORGANIZATION_ID`: Claude organization ID (default: sophia-ai)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4-turbo)
- `OPENAI_MAX_TOKENS`: Maximum tokens for OpenAI responses (default: 4096)
- `REDIS_URL`: Redis URL (default: redis://localhost:6379)
- `POSTGRES_HOST`: PostgreSQL host (default: localhost)
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `LOG_LEVEL`: Logging level (default: INFO)
- `SSL_CERT_FILE`: SSL certificate file path

## Usage Guide

### Setting Up a New Repository

To set up a new repository with all the necessary secrets and configurations:

```bash
# Create a new repository with a specific name
./setup_new_repo.py --name sophia-new-repo

# Create a new repository and pull secrets from Pulumi ESC
./setup_new_repo.py --name sophia-new-repo --from-pulumi
```

### Managing Secrets in an Existing Repository

#### Detecting Missing Environment Variables

```bash
./secrets_manager.py detect-missing
```

This command will check for missing required environment variables and display them with their descriptions.

#### Importing and Exporting Secrets

The `secrets_manager.py` utility can import or export secrets between GitHub and
Pulumi ESC. Local `.env` files are no longer required.

#### Syncing Secrets to Pulumi ESC

```bash
./secrets_manager.py sync-to-pulumi
```

This command will sync the current environment variables to Pulumi ESC, making them available to all repositories and environments.

#### Syncing Secrets to GitHub

```bash
./secrets_manager.py sync-to-github
```

This command will sync the current environment variables to GitHub Secrets, making them available to GitHub Actions.

#### Validating Secret Configuration

```bash
./secrets_manager.py validate
```

This command will validate the current configuration, checking for missing required variables and displaying a summary of the configuration.

#### Generating a Template .env File

```bash
./secrets_manager.py generate-template --output-file env.template
```

This command will generate a template .env file with all required and optional variables, with sensitive values masked.

#### Syncing All Secrets

```bash
./secrets_manager.py sync-all
```

This command will sync all secrets between GitHub and Pulumi ESC.

## Best Practices

1. **Never commit secrets to version control**: Always use `.gitignore` to exclude `.env` files and other files containing secrets.

2. **Use environment-specific secrets**: Different environments (development, staging, production) should use different secrets.

3. **Rotate secrets regularly**: Follow the rotation schedule defined in this guide.

4. **Use strong, unique secrets**: Generate strong, unique secrets for each service and environment.

5. **Monitor secret usage**: Regularly audit secret usage and access patterns.

6. **Use least privilege access**: Only grant access to secrets that are absolutely necessary.

7. **Encrypt secrets at rest and in transit**: Use encrypted storage and secure transmission protocols.

8. **Implement proper access controls**: Use role-based access controls and audit logging.

9. **Have a secret recovery plan**: Ensure you have a plan for recovering from compromised secrets.

10. **Document secret management procedures**: Keep this guide up-to-date and ensure all team members are familiar with the procedures.

## Security Considerations

1. **Secret Exposure**: Never log secrets or include them in error messages.

2. **Access Logging**: Log all access to secrets for audit purposes.

3. **Network Security**: Use secure networks and VPNs when accessing secrets.

4. **Workstation Security**: Ensure workstations used to access secrets are secure and up-to-date.

5. **Backup Security**: Ensure secret backups are encrypted and stored securely.

6. **Incident Response**: Have a plan for responding to secret compromise incidents.

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Use the `detect-missing` command to identify missing variables.

2. **Invalid Secrets**: Use the `validate` command to check secret validity.

3. **Sync Failures**: Check network connectivity and access permissions.

4. **Access Denied**: Verify access permissions and authentication credentials.

### Getting Help

If you encounter issues not covered in this guide:

1. Check the troubleshooting section of the main documentation
2. Review the logs for error messages
3. Contact the development team for assistance
4. Create an issue in the GitHub repository

## Conclusion

The Sophia AI secrets management system provides a comprehensive, secure, and scalable approach to handling sensitive information. By following the guidelines and procedures outlined in this guide, you can ensure that secrets are managed consistently and securely across all environments and repositories.

---

## 🎯 **PERMANENT SOLUTION GUARANTEE**

**The new permanent solution eliminates 90% of the complexity in this guide. Once set up, you never need to manually manage secrets again.**

- ✅ **Zero Manual Configuration**: Everything automated
- ✅ **Enterprise Security**: GitHub organization + Pulumi ESC
- ✅ **Automatic Sync**: Secrets always up-to-date
- ✅ **Comprehensive Testing**: `python scripts/test_permanent_solution.py`
- ✅ **Forever Solution**: Works without intervention

**🔒 RESULT: PERMANENT SECRET MANAGEMENT - NO MORE MANUAL WORK EVER!**
