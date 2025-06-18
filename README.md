# SOPHIA AI System

SOPHIA (Strategic Orchestration of PayReady's Hierarchical Intelligence Architecture) is an AI executive intelligence orchestration system for PayReady, designed to coordinate multiple specialized AI agents and integrate with business systems.

## 🌟 Features

- **Multi-Agent Orchestration**: Coordinate specialized AI agents for different business functions
- **Real-Time Data Processing**: Stream data from multiple sources using Estuary Flow
- **Vector Search**: Semantic search capabilities with Pinecone and Weaviate
- **Business Intelligence**: Automated insights from HubSpot, Salesforce, Gong, and more
- **Hierarchical Agent Structure**: CrewAI-based agent hierarchy for complex tasks
- **Persistent Memory**: Long-term context retention with mem0 integration
- **MCP Server Architecture**: Model Context Protocol server for extensible tools
- **Docker Containerization**: Easy deployment and scaling

## 🚀 Specialized Agents

- **Sales Coach Agent**: Analyze Gong calls and provide coaching insights
- **Client Health Agent**: Monitor client health metrics and predict churn
- **Research & Data Scraping Agents**: Gather market intelligence
- **AI Recruiting & HR Agent**: Assist with hiring and HR processes
- **Business Strategy Agents**: Provide strategic recommendations

## 🛠️ Tech Stack

- **Data**: Snowflake, PostgreSQL, Redis
- **Vector Databases**: Pinecone, Weaviate
- **BI**: Looker integration
- **Integrations**: HubSpot, Salesforce, Gong.io, NetSuite, Lattice, Apollo.io, UserGems
- **Infrastructure**: Pulumi (IaC), Lambda Labs (GPU)
- **Development**: Python 3.11+, FastAPI, React, TypeScript
- **AI**: OpenAI, Claude, CrewAI, LangChain
- **Streaming**: Estuary Flow for real-time data pipelines

## 📋 Requirements

- Python 3.11+
- Docker and Docker Compose
- Node.js 18+ (for frontend)
- PostgreSQL 15+
- Redis 7+
- API keys for OpenAI, Pinecone, and other integrated services

## 🔧 Installation

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/payready/sophia.git
cd sophia

# Run the quick setup script
chmod +x quick_setup.sh
./quick_setup.sh
```

### Manual Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Copy the environment variables example:
   ```bash
   cp env.example .env
   ```

4. Edit the `.env` file with your API keys and configuration.

5. Start the required services with Docker:
   ```bash
   docker-compose up -d postgres redis weaviate mem0
   ```

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the development server:
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🏃‍♂️ Running the Application

### Using Make Commands

The project includes a Makefile with common commands:

```bash
# Show available commands
make help

# Start development server
make dev

# Start full development environment
make dev-full

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Build Docker images
make docker-build

# Start Docker containers
make docker-up

# Stop Docker containers
make docker-down
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 🧩 Architecture

SOPHIA is built with a modular architecture:

```
backend/
├── agents/                # AI agents
│   ├── core/              # Base agent classes
│   └── specialized/       # Domain-specific agents
├── app/                   # FastAPI application
├── config/                # Configuration
├── core/                  # Core functionality
├── database/              # Database models and migrations
├── integrations/          # External service integrations
├── mcp/                   # Model Context Protocol server
├── pipelines/             # Data pipelines
└── vector/                # Vector database utilities

frontend/                  # React frontend
infrastructure/            # Pulumi infrastructure code
```

## 🔄 Data Flow

1. **Data Ingestion**: Data is ingested from various sources (HubSpot, Salesforce, Gong, etc.)
2. **Real-Time Processing**: Estuary Flow processes data in real-time
3. **Storage**: Data is stored in PostgreSQL (operational) and Snowflake (warehouse)
4. **Vectorization**: Text data is vectorized and stored in Pinecone/Weaviate
5. **Agent Processing**: Specialized agents process data and generate insights
6. **Orchestration**: Central orchestrator coordinates agent activities
7. **Delivery**: Insights are delivered via API, UI, and Slack notifications

## 🔌 Integrations

### CRM Systems
- **HubSpot**: Contact and deal management
- **Salesforce**: Enterprise CRM integration

### Communication
- **Gong.io**: Call analysis and sales coaching
- **Slack**: Notifications and interactive commands

### Business Intelligence
- **Snowflake**: Data warehousing
- **Looker**: BI dashboards and reports

### HR and Recruiting
- **Lattice**: Performance management
- **Apollo.io**: Prospect data
- **UserGems**: Customer intelligence

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_agents.py
```

## 🚢 Deployment

### Production Deployment

```bash
# Deploy to production
./deploy_production.sh
```

### Docker Deployment

The system is containerized with Docker and can be deployed using Docker Compose:

```bash
# Build and start production containers
docker-compose --profile production up -d
```

### Cloud Deployment

Infrastructure is managed with Pulumi:

```bash
cd infrastructure
pulumi up
```

## 🔒 Security

### Secrets Management

SOPHIA uses a comprehensive multi-layered approach to secrets management:

- **GitHub Organization Secrets**: Shared across all repositories in the organization
- **GitHub Repository Secrets**: Specific to individual repositories
- **Pulumi ESC**: For infrastructure and deployment secrets

Secret management tools:

- `configure_github_org_secrets.py`: Manage GitHub organization secrets
- `import_secrets_to_github.py`: Import secrets to GitHub repository
- `configure_pulumi_esc.sh`: Manage Pulumi ESC secrets

For detailed information, see [Secrets Management Implementation](docs/SECRETS_MANAGEMENT_IMPLEMENTATION.md).

### Security Features

- Authentication using JWT tokens
- Role-based access control
- Encrypted storage for sensitive data
- Regular security audits
- Secret rotation policies

## 📚 Documentation

- API documentation is available at `/docs` when the server is running
- Additional documentation is in the `docs/` directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## 📄 License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

## 📞 Support

For support, contact the PayReady development team.
