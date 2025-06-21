# Sophia AI Platform

A comprehensive AI platform with MCP (Model Context Protocol) integration, deployed on Lambda Labs infrastructure.

## Quick Start

### Prerequisites
- Docker installed and configured
- Pulumi CLI with access token
- SSH access to Lambda Labs server
- GitHub organization access for secrets

### Deployment
```bash
# Clone the repository
git clone https://github.com/ai-cherry/sophia-main.git
cd sophia-main
# Set Pulumi token (required for all setup scripts)
export PULUMI_ACCESS_TOKEN=your_token_here

# Deploy the platform
./deploy_sophia_platform.sh
```

## Current Infrastructure

### Server Configuration
- **Provider**: Lambda Labs
- **Instance**: gpu_1x_a10 (1x A10 24GB, 30 vCPUs, 200GB RAM)
- **IP**: 170.9.9.253
- **Cost**: $0.75/hour (~$540/month)
- **SSH Key**: cherry-ai-key

### Key Components
- **Kubernetes**: K3s cluster for container orchestration
- **MCP Servers**: Snowflake, Pulumi, and custom integrations
- **Data Pipeline**: Airbyte + Snowflake + Pinecone
- **AI Models**: Anthropic Claude, OpenAI GPT
- **Monitoring**: Comprehensive logging and metrics

## Architecture

### MCP Integration
The platform uses Model Context Protocol (MCP) for standardized AI-tool communication:
- **Snowflake MCP**: Data warehouse operations
- **Pulumi MCP**: Infrastructure management
- **Custom MCPs**: Business-specific integrations

### Data Flow
```
External APIs → Airbyte → Snowflake → Vector Processing → Pinecone → AI Models
```

### Service Integrations
- **CRM**: HubSpot integration for customer data
- **Sales**: Gong.io for conversation intelligence
- **Communication**: Slack for team collaboration
- **Analytics**: Arize for AI model monitoring

## Configuration Management

### Secret Management
- **Primary**: GitHub Organization Secrets (158 configured)
- **Distribution**: Pulumi ESC
- **Runtime**: Environment variables
- **Rotation**: Quarterly automated rotation

### Key Secrets
- `ANTHROPIC_API_KEY`: AI model access
- `SNOWFLAKE_*`: Data warehouse credentials
- `PINECONE_API_KEY`: Vector database
- `LAMBDA_API_KEY`: Infrastructure management

## Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
make dev
```

### MCP Server Development
```bash
cd mcp-servers/[server-name]
python main.py
```

## Deployment

### Infrastructure Deployment
```bash
cd infrastructure
pulumi stack select sophia-prod-on-lambda
pulumi up
```

### Application Deployment
Applications are automatically deployed via Kubernetes manifests when infrastructure is updated.

### Monitoring
- **Logs**: Centralized logging via Kubernetes
- **Metrics**: Prometheus + Grafana
- **Alerts**: Automated alerting for critical issues

## Security

### Access Control
- SSH key-based authentication
- GitHub organization-level secrets
- Least-privilege access principles
- Regular access reviews

### Best Practices
- No secrets in code
- Encrypted communication
- Regular security updates
- Audit logging

## Performance

### Current Capacity
- **AI Workloads**: Up to 24GB GPU memory
- **Concurrent Users**: 50-100 users
- **Data Processing**: 1TB+ daily throughput
- **Response Time**: <2s for most operations

### Scaling Options
- **Vertical**: Upgrade to H100 instances
- **Horizontal**: Multi-instance deployment
- **Auto-scaling**: Kubernetes HPA

## Troubleshooting

### Common Issues
1. **SSH Connection Failed**: Verify SSH key configuration
2. **Pulumi Deployment Failed**: Check ESC environment
3. **MCP Server Down**: Restart via Kubernetes
4. **High Costs**: Monitor resource usage

### Support
- **Documentation**: See `/docs` directory
- **Issues**: GitHub Issues
- **Emergency**: Contact platform team

## Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Deploy after review

### Code Standards
- Python: Black formatting, type hints
- JavaScript: ESLint + Prettier
- Infrastructure: Pulumi best practices
- Documentation: Markdown with clear examples

## License

This project is proprietary to AI-Cherry organization.

---

**Status**: Production Ready
**Last Updated**: June 21, 2025
**Maintained By**: Sophia AI Platform Team

For detailed configuration information, see [DEPLOYMENT_CONFIGURATION_GUIDE.md](./DEPLOYMENT_CONFIGURATION_GUIDE.md)

