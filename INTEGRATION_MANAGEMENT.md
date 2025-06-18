# Sophia AI Integration Management Guide

This guide provides instructions for managing integrations with external services in the Sophia AI platform.

## Overview

Sophia AI integrates with several external services to provide a comprehensive business intelligence and automation platform:

- **Snowflake**: Data warehouse for storing and analyzing structured data
- **Gong**: Call recording and analysis platform
- **Vercel**: Deployment platform for frontend applications
- **Estuary**: Data streaming and ETL platform
- **MCP**: Model Context Protocol servers for AI tool integration

This guide covers how to set up, test, and manage these integrations.

## Prerequisites

- Python 3.11+
- pip
- Access credentials for the services you want to integrate with

## Setup

### Installation

1. Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/pay-ready/sophia-ai.git
cd sophia-ai
```

2. Install the required dependencies:

```bash
pip install -r integration_requirements.txt
```

### Environment Configuration

The integration tools use environment variables for configuration. You can set these up in a `.env` file:

```bash
cp integration.env.example .env
```

Then edit the `.env` file with your credentials for each service.

## Integration Management

The `manage_integrations.py` script provides a command-line interface for managing integrations:

```bash
./manage_integrations.py [command] [options]
```

### Available Commands

- `setup`: Set up a new integration
- `update`: Update credentials for an existing integration
- `test`: Test connectivity for an integration
- `rotate`: Rotate API keys for an integration
- `import`: Import configuration from a file
- `export`: Export configuration to a file
- `list`: List configured integrations

### Examples

#### Setting up a new integration

```bash
./manage_integrations.py setup snowflake
```

This will prompt you for the necessary credentials and configuration options.

#### Testing an integration

```bash
./manage_integrations.py test gong
```

This will run connectivity tests for the specified integration.

#### Rotating API keys

```bash
./manage_integrations.py rotate vercel
```

This will guide you through the process of rotating API keys for the specified integration.

#### Listing configured integrations

```bash
./manage_integrations.py list
```

This will display a list of all configured integrations and their details.

## Running Integration Tests

The `test_all_integrations.sh` script provides a convenient way to run integration tests for all configured services:

```bash
./test_all_integrations.sh
```

This will:
- Check for dependencies
- Load environment variables
- Run all integration tests
- Generate a summary report

You can also run tests for specific integrations using the `unified_integration_test.py` script:

```bash
./unified_integration_test.py --tests snowflake,gong,vercel
```

## CI/CD Integration

The integration tests are integrated with the CI/CD pipeline in GitHub Actions. The workflow is defined in `.github/workflows/test_integrations.yml`.

The tests run automatically:
- On pull requests to the main branch
- On a schedule (daily at midnight UTC)
- Manually via workflow dispatch

Secrets for the integration tests are stored in GitHub Secrets and are automatically injected into the test environment.

## Security Considerations

- Never commit your `.env` file to version control
- Use GitHub Secrets for storing sensitive credentials in CI/CD
- Rotate API keys regularly using the `rotate` command
- Use the principle of least privilege when creating API keys for testing

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify that your API keys and credentials in the `.env` file are correct
   - Check if the API keys have expired or been revoked
   - Ensure you have the necessary permissions for the operations being tested

2. **Network Issues**:
   - Check your internet connection
   - Verify that your network allows connections to the required services
   - Check if you need to configure a proxy

3. **Missing Dependencies**:
   - Run `pip install -r integration_requirements.txt` to ensure all dependencies are installed
   - Check for any version conflicts between packages

### Logs

Detailed logs are printed to the console during test execution. For more verbose logging, you can modify the logging level in `unified_integration_test.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
```

## Adding New Integrations

To add a new integration:

1. Create a new integration test class in `unified_integration_test.py`
2. Add the integration to the `manage_integrations.py` script
3. Update the environment example file with the new variables
4. Update the GitHub Actions workflow to include the new integration

## Best Practices

1. **Regular Testing**: Run integration tests regularly to ensure continued connectivity
2. **Key Rotation**: Rotate API keys on a regular schedule (e.g., monthly)
3. **Monitoring**: Set up monitoring for integration failures in production
4. **Documentation**: Keep documentation up to date with any changes to the integrations
5. **Version Control**: Track changes to integration configurations in version control
6. **Secrets Management**: Use a secure method for managing secrets (e.g., Pulumi ESC)

## Reference

For more detailed information, refer to the following resources:

- [Snowflake Documentation](https://docs.snowflake.com/)
- [Gong API Documentation](https://app.gong.io/settings/api)
- [Vercel API Documentation](https://vercel.com/docs/api)
- [Estuary Documentation](https://docs.estuary.dev/)
- [MCP Documentation](https://modelcontextprotocol.github.io/)

## Support

If you encounter any issues with the integrations, please contact the Pay Ready DevOps team.
