# SOPHIA AI System - Secrets Management Implementation

This document outlines the secrets management implementation for the SOPHIA AI System, including GitHub organization secrets, repository secrets, and Pulumi ESC integration.

## Overview

The SOPHIA AI System uses a multi-layered approach to secrets management:

1. **GitHub Organization Secrets**: Shared across all repositories in the organization
2. **GitHub Repository Secrets**: Specific to individual repositories
3. **Pulumi ESC**: For infrastructure and deployment secrets

## GitHub Organization Secrets

Organization secrets are managed using the `configure_github_org_secrets.py` script, which allows for:

- Setting organization-level secrets with visibility controls
- Listing existing secrets
- Deleting specific or all secrets

### Usage

```bash
# Set organization secrets using the provided script
python configure_github_org_secrets.py --org ai-cherry

# List existing secrets
python configure_github_org_secrets.py --org ai-cherry --list

# Delete a specific secret
python configure_github_org_secrets.py --org ai-cherry --delete SECRET_NAME

# Delete all secrets (with confirmation)
python configure_github_org_secrets.py --org ai-cherry --delete-all
```

### Visibility Controls

Organization secrets can have different visibility settings:

- `all`: Visible to all repositories (default)
- `private`: Visible only to private repositories
- `selected`: Visible only to selected repositories

## GitHub Repository Secrets

Repository secrets are managed using the `import_secrets_to_github.py` script, which allows for setting repository-level secrets and supports a dry-run mode for testing.

### Usage

```bash
# Set repository secrets
python import_secrets_to_github.py --repo ai-cherry/sophia

# Test without making changes
python import_secrets_to_github.py --repo ai-cherry/sophia --dry-run
```

## Pulumi ESC Integration

Pulumi ESC (Encrypted Secrets Configuration) is used for managing secrets across different environments (development, staging, production). The configuration is defined in `pulumi-esc-environment.yaml`.

### Secret Groups

Secrets are organized into groups:

- `api-keys`: API keys for external services
- `database-credentials`: Database credentials
- `security-tokens`: Security tokens and secrets
- `integration-credentials`: Credentials for integrated services
- `infrastructure-credentials`: Credentials for infrastructure services

### Access Policies

Access policies define who can access which secrets in which environments:

- `admin-access`: Full access to all secrets in all environments
- `developer-access`: Access to development secrets only
- `ci-cd-access`: Access for CI/CD pipelines in all environments

### Usage

```bash
# Sync secrets from GitHub to ESC
./scripts/sync_github_to_pulumi.sh

# List all secrets (values are masked)
./configure_pulumi_esc.sh list
```

## Security Considerations

- **GitHub PAT**: Secrets starting with `GITHUB_` are not allowed in GitHub Actions
- **Encryption**: All secrets are encrypted using GitHub's public key system
- **Access Control**: Secrets are only accessible to authorized users and repositories
- **Visibility**: Organization secrets can have different visibility settings
- **Rotation**: Secrets should be rotated regularly

## Implementation Details

### GitHub Organization Secrets

The `configure_github_org_secrets.py` script uses the GitHub API through the PyGithub library to manage organization secrets. It encrypts secrets using the organization's public key before sending them to GitHub.

### GitHub Repository Secrets

The `import_secrets_to_github.py` script uses the GitHub CLI to set repository secrets based on key/value pairs provided at runtime or via environment variables.

### Pulumi ESC

The `configure_pulumi_esc.sh` script uses the Pulumi CLI to manage secrets in Pulumi ESC. It can synchronize secrets with GitHub Actions and list existing values.

## Next Steps

1. Set up GitHub Actions workflows to use these secrets
2. Implement secret rotation policies
3. Add monitoring for secret usage
4. Integrate with a secrets manager like HashiCorp Vault or AWS Secrets Manager
