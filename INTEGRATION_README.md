# Sophia AI Integration Management

This repository contains tools and utilities for managing Sophia AI's integrations with external services:

- **Snowflake**: Data warehouse for analytics and business intelligence
- **Gong**: Call recording and analysis platform
- **Vercel**: Deployment and hosting platform
- **Estuary**: Data streaming and ETL platform
- **MCP**: Model Context Protocol for AI agent orchestration

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Access credentials for the services you want to integrate with

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/pay-ready/sophia-ai-integrations.git
   cd sophia-ai-integrations
   ```

2. Install dependencies:
   ```bash
   pip install -r integration_requirements.txt
   ```

3. Set up your environment:
   ```bash
   cp integration.env.example .env
   # Edit .env with your credentials
   ```

## Usage

### Testing Integrations

Use the `test_all_integrations.sh` script to test connectivity with all configured services:

```bash
./test_all_integrations.sh
```

You can also test specific integrations:

```bash
./test_all_integrations.sh --tests snowflake,gong
```

Or run the Python script directly:

```bash
python unified_integration_test.py --tests all --output test_results.json
```

### Managing Integrations

The `manage_integrations.py` script provides utilities for checking, configuring, and rotating credentials for integrations:

```bash
# Check status of all integrations
python manage_integrations.py --action check --service all

# Configure a specific integration
python manage_integrations.py --action configure --service snowflake

# Rotate credentials for a specific integration
python manage_integrations.py --action rotate --service gong
```

## Integration Details

### Snowflake

Snowflake is used as the primary data warehouse for Sophia AI. It stores:

- User activity data
- Business metrics
- Analytics results
- Historical conversation data

Configuration variables:
- `SNOWFLAKE_ACCOUNT`: Your Snowflake account identifier
- `SNOWFLAKE_USER`: Username for authentication
- `SNOWFLAKE_PASSWORD`: Password for authentication
- `SNOWFLAKE_WAREHOUSE`: Warehouse to use for queries
- `SNOWFLAKE_DATABASE`: Database to connect to
- `SNOWFLAKE_SCHEMA`: Schema to use
- `SNOWFLAKE_ROLE`: Role to assume when connecting

### Gong

Gong is used for call recording, transcription, and analysis. Sophia AI integrates with Gong to:

- Retrieve call recordings and transcripts
- Analyze sales conversations
- Extract insights from customer interactions
- Monitor sales team performance

Configuration variables:
- `GONG_API_KEY`: API key for authentication
- `GONG_API_SECRET`: API secret for authentication

### Vercel

Vercel is used for deploying and hosting the Sophia AI frontend and API services. The integration allows:

- Automated deployments
- Environment management
- Domain configuration
- Performance monitoring

Configuration variables:
- `VERCEL_API_TOKEN`: API token for authentication
- `VERCEL_TEAM_ID`: Team ID for organization access
- `VERCEL_PROJECT_ID`: Project ID for deployment target

### Estuary

Estuary is used for data streaming and ETL processes. Sophia AI uses Estuary to:

- Stream data between systems
- Transform data for analytics
- Archive important information
- Manage data pipelines

Configuration variables:
- `ESTUARY_API_KEY`: API key for authentication
- `ESTUARY_API_URL`: API endpoint URL

### MCP (Model Context Protocol)

MCP is used for AI agent orchestration and communication. It enables:

- Communication between AI agents
- Access to external tools and resources
- Structured data exchange
- Context management

Configuration variables:
- `MCP_CONFIG_PATH`: Path to the MCP configuration file

## CI/CD Integration

This repository includes GitHub Actions workflows for:

- Testing integrations on pull requests and scheduled runs
- Rotating credentials on a regular schedule
- Deploying infrastructure changes

## Security Considerations

- All credentials are stored in environment variables or secure storage
- Credential rotation is supported for all integrations
- Access is limited to necessary permissions only
- All API communications use HTTPS
- Sensitive data is encrypted at rest and in transit

## Troubleshooting

If you encounter issues with integrations:

1. Check your credentials in the `.env` file
2. Ensure network connectivity to the service
3. Verify that your account has the necessary permissions
4. Check the service status page for outages
5. Run the integration test with `--verbose` flag for detailed logs

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run integration tests to ensure everything works
4. Submit a pull request

## License

Proprietary - Pay Ready, Inc.
