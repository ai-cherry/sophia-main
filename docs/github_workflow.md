# GitHub Workflow Documentation

## Overview

This document provides information about the GitHub workflow for the Sophia AI project, which uses Pulumi ESC (Environment, Secrets, and Configuration) for centralized secret management.

## Main Workflow

The main workflow (`sophia-main.yml`) is responsible for testing, building, and deploying the Sophia AI project. It supports multiple environments (development, staging, production) and can be triggered automatically by pushes to the main branch or manually via workflow dispatch.

### Triggering the Workflow

The workflow can be triggered in two ways:

1. **Automatically**: When code is pushed to the main branch or a pull request is created against the main branch.
2. **Manually**: By using the "Run workflow" button in the GitHub Actions UI.

When triggered manually, you can specify:
- The environment to deploy to (development, staging, production)
- Whether to deploy infrastructure, backend, and/or frontend
- Whether to rotate secrets
- Which service to rotate secrets for (if rotating secrets)

### Workflow Structure

The workflow consists of the following jobs:

1. **initialize**: Sets up environment variables and deployment options
2. **setup-pulumi-esc**: Initializes Pulumi ESC and synchronizes secrets
3. **security-scan**: Runs security scans on code and dependencies
4. **test-backend**: Runs backend tests
5. **test-frontend**: Runs frontend tests and builds the frontend
6. **rotate-secrets**: Rotates secrets if requested
7. **deploy-infrastructure**: Deploys infrastructure using Pulumi
8. **deploy-backend**: Deploys backend to Lambda Labs
9. **deploy-frontend**: Deploys frontend to Vercel
10. **health-check**: Runs post-deployment health checks
11. **notify**: Sends notifications about deployment status

### Environment Support

The workflow supports multiple environments:
- **development**: Used for development and testing
- **staging**: Used for pre-production testing
- **production**: Used for production deployment

When triggered automatically, the environment is determined based on the branch:
- main branch: production
- other branches: development

When triggered manually, you can specify the environment.

## Secret Management

The workflow uses Pulumi ESC for secret management. This provides several benefits:
- Centralized management of secrets across all environments
- Secure storage and access control
- Automated secret rotation
- Integration with GitHub Actions

### Secret Synchronization

Secrets are synchronized between GitHub and Pulumi ESC using the `sync_secrets_ci.sh` script. This script can synchronize secrets in both directions:
- **github-to-pulumi**: Copies secrets from GitHub to Pulumi ESC
- **pulumi-to-github**: Copies secrets from Pulumi ESC to GitHub
- **bidirectional**: Synchronizes secrets in both directions

The workflow automatically synchronizes secrets from GitHub to Pulumi ESC at the start of each run.

### Secret Retrieval

Secrets are retrieved from Pulumi ESC using the `get_secret.py` script. This script can retrieve:
- A specific secret for a service
- All secrets for a service
- A specific configuration value for a service

### Secret Injection

Secrets are injected into the GitHub Actions environment using the `inject_secrets.sh` script. This script:
- Retrieves secrets from Pulumi ESC
- Injects them into the GitHub Actions environment
- Masks sensitive values in logs

### Secret Rotation

Secrets can be rotated using the `secret_rotation_framework.py` script. This script:
- Rotates secrets for a specific service or all services
- Updates the rotated secrets in Pulumi ESC
- Synchronizes the rotated secrets back to GitHub

## Testing the Workflow

A test workflow (`test_esc_integration.yml`) is provided to test the Pulumi ESC integration. This workflow:
- Tests the setup of Pulumi ESC
- Tests secret synchronization
- Tests secret retrieval
- Tests secret injection
- Generates a test report

To run the test workflow:
1. Go to the "Actions" tab in the GitHub repository
2. Select "Test Pulumi ESC Integration" from the list of workflows
3. Click "Run workflow"
4. Specify the environment to test and optionally a specific service
5. Click "Run workflow" again

## Troubleshooting

If you encounter issues with the workflow, check the following:

1. **Secret Access**: Ensure that the workflow has access to the required secrets:
   - `PULUMI_ACCESS_TOKEN`: Token for accessing Pulumi
   - `GH_TOKEN`: Token for accessing GitHub

2. **Environment Configuration**: Ensure that the environment is properly configured in Pulumi ESC:
   - Check that the stack exists: `pulumi stack ls`
   - Check that the configuration is set: `pulumi config`

3. **Service Registry**: Ensure that the service registry (`integration_registry.json`) is up to date:
   - Check that all services are listed
   - Check that all secret and configuration keys are listed

4. **Logs**: Check the workflow logs for error messages:
   - Look for errors in the "setup-pulumi-esc" job
   - Look for errors in the secret retrieval and injection steps

## Adding a New Service

To add a new service to the workflow:

1. Add the service to the service registry (`infrastructure/integration_registry.json`):
   ```json
   "new_service": {
     "type": "service_type",
     "description": "Description of the service",
     "config_keys": ["key1", "key2"],
     "secret_keys": ["key3", "key4"],
     "rotation_schedule": "90d",
     "owner": "team-name",
     "dependencies": []
   }
   ```

2. Add the service's secrets to GitHub:
   - Go to the repository settings
   - Select "Secrets and variables" > "Actions"
   - Add the secrets with the naming convention: `NEW_SERVICE_KEY3`, `NEW_SERVICE_KEY4`

3. Synchronize the secrets to Pulumi ESC:
   - Run the main workflow manually
   - Select the appropriate environment
   - The workflow will automatically synchronize the secrets

4. Update the deployment code to use the new service:
   - Use the `get_secret.py` script to retrieve the secrets
   - Use the `inject_secrets.sh` script to inject the secrets into the environment

## Best Practices

1. **Secret Naming**: Use consistent naming for secrets:
   - Service names should be lowercase and use underscores
   - Secret keys should be lowercase and use underscores
   - GitHub secrets should be uppercase and use underscores

2. **Secret Rotation**: Rotate secrets regularly:
   - Use the workflow to rotate secrets
   - Set appropriate rotation schedules in the service registry

3. **Testing**: Test changes to the workflow:
   - Use the test workflow to test changes
   - Check the test report for issues

4. **Documentation**: Keep documentation up to date:
   - Update this document when making changes to the workflow
   - Document new services and their secrets

