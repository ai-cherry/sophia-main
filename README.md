# Sophia AI - Business Intelligence Orchestrator

## 🚀 Overview

Sophia AI is an advanced AI assistant orchestrator designed as the central "Pay Ready Brain" for business intelligence and automation. It orchestrates multiple AI agents and integrates with critical business systems including HubSpot CRM, Gong.io call analysis, Slack communication, and property management platforms.

## 🏗️ Architecture

### Core Infrastructure
- **Type:** Multi-agent AI orchestrator with flat-to-hierarchical evolution
- **Backend:** FastAPI/Python with async support
- **Frontend:** React + Vite with modern dark-themed UI
- **Databases:** PostgreSQL, Redis, Pinecone, Weaviate
- **Infrastructure:** Lambda Labs servers, Vercel frontend deployment
- **Monitoring:** Prometheus + Grafana

### Key Components

1. **Specialized AI Agents** (`backend/agents/`)
   - Call Analysis Agent (Gong.io integration)
   - CRM Sync Agent (HubSpot integration)
   - Notification Agent (Slack integration)
   - Business Intelligence Agent (Revenue/performance reports)

2. **Unified Gateway Orchestrator** (`backend/integrations/unified_gateway_orchestrator.py`)
   - Intelligent routing across LLM providers
   - Automatic failover and cost optimization
   - Performance tracking and monitoring

3. **Property Management MCP Server** (`backend/mcp/property_management_mcp_server.py`)
   - Complete apartment industry integration
   - Support for Yardi, RealPage, AppFolio, Entrata, CoStar

4. **Modern UI Dashboard** (`frontend/`)
   - Dark theme with glassmorphism effects
   - Real-time metrics and KPIs
   - 4-tab interface: Overview, Strategy, Operations, AI Insights

## 🔐 Secret Management

### IMPORTANT: How Secrets Work in This Project

All secrets are managed through a unified system. **For AI assistants and developers working on this project:**

1. **Primary Documentation:** See `docs/SECRET_MANAGEMENT_GUIDE.md` for complete details
2. **Secret Names:** Use EXACT names as specified (e.g., `VERCEL_ACCESS_TOKEN` not `VERCEL_TOKEN`)
3. **Management Tool:** Use `scripts/setup_pulumi_secrets.py` for all secret operations

### Quick Secret Reference

```bash
# Check what secrets are needed
cat env.example

# Import secrets from .env file
python scripts/setup_pulumi_secrets.py import-env --env-file .env

# Sync secrets to GitHub
python scripts/setup_pulumi_secrets.py sync

# Validate all secrets are configured
python scripts/setup_pulumi_secrets.py validate
```

### Critical Deployment Secrets
- `VERCEL_ACCESS_TOKEN` - Frontend deployment (NOT VERCEL_TOKEN!)
- `LAMBDA_LABS_API_KEY` - Backend deployment
- `PORTKEY_API_KEY` - LLM gateway (recommended)
- `OPENROUTER_API_KEY` - Alternative LLM gateway

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker (optional)

### Local Development Setup

1. **Clone and Setup**
   ```bash
   git clone https://github.com/ai-cherry/sophia-main.git
   cd sophia-main
   ```

2. **Configure Environment**
   ```bash
   # Use minimal setup for development
   cp env.minimal.example .env
   # Edit .env with your API keys
   ```

3. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5001
   - API Docs: http://localhost:5001/docs

### Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 📊 Key Features

### Business Intelligence
- Real-time revenue tracking and KPIs
- Customer health monitoring
- Sales performance analytics
- AI-powered insights and predictions

### Integrations
- **HubSpot CRM:** Contact and deal management
- **Gong.io:** Call recording analysis
- **Slack:** Team notifications
- **Property Management:** Yardi, RealPage, AppFolio support

### AI Capabilities
- Natural language business queries
- Automated report generation
- Predictive analytics
- Strategic recommendations

## 🛠️ Configuration

### Environment Variables

See `env.example` for all available options. Key configurations:

```bash
# LLM Gateway (Recommended approach)
LLM_GATEWAY=portkey
PORTKEY_API_KEY=your_key
OPENROUTER_API_KEY=your_key

# Business Integrations
HUBSPOT_API_KEY=your_key
GONG_API_KEY=your_key
SLACK_BOT_TOKEN=your_token

# Vector Databases
PINECONE_API_KEY=your_key
WEAVIATE_URL=your_url
```

## 🚀 Deployment

### GitHub Actions (Automated)

1. Ensure secrets are set in GitHub (see Secret Management section)
2. Push to main branch
3. Actions will automatically deploy to Lambda Labs and Vercel

### Manual Deployment

See `docs/DEPLOYMENT_GUIDE.md` for detailed instructions.

## 📚 Documentation

### Core Documentation
- **Secret Management:** `docs/SECRET_MANAGEMENT_GUIDE.md` 📌
- **Infrastructure Report:** `docs/SOPHIA_AI_INFRASTRUCTURE_REPORT.md`
- **Design System:** `docs/SOPHIA_DESIGN_SYSTEM_INTEGRATION.md`
- **Deployment Guide:** `docs/DEPLOYMENT_GUIDE.md`

### Technical Documentation
- **Architecture:** `docs/implementation/sophia_technical_architecture.md`
- **Implementation Plan:** `docs/implementation/sophia_implementation_plan.md`
- **MCP Servers:** `docs/mcp_server_documentation.md`

## 🧪 Testing

```bash
# Run all tests
pytest

# Test infrastructure
python test_infrastructure.py

# Test specific components
pytest tests/test_auth.py
```

## 🔧 Development

### Project Structure
```
sophia-main/
├── backend/           # Python backend
│   ├── agents/       # AI agents
│   ├── integrations/ # External services
│   └── config/       # Configuration
├── frontend/         # React frontend
│   ├── src/         # Source code
│   └── public/      # Static assets
├── docs/            # Documentation
├── scripts/         # Utility scripts
└── tests/          # Test files
```

### Adding New Features

1. Follow the patterns in `.cursorrules`
2. Use type hints and comprehensive error handling
3. Include tests for new functionality
4. Update relevant documentation

## 🤝 Contributing

1. Check existing issues and PRs
2. Follow the code style in `.cursorrules`
3. Include tests with your changes
4. Update documentation as needed

## 📈 Monitoring

- **Grafana Dashboard:** http://localhost:3000 (when running locally)
- **Prometheus Metrics:** http://localhost:9090
- **Health Check:** http://localhost:5001/health

## 🆘 Support

- GitHub Issues: [Create an issue](https://github.com/ai-cherry/sophia-main/issues)
- Documentation: Check `docs/` directory
- Logs: Check `logs/` directory for debugging

## 🔒 Security

- All API keys must be kept secure
- Use environment variables, never commit secrets
- Follow the secret management guide
- Enable audit logging in production

---

**Sophia AI** - The intelligent business orchestrator for Pay Ready, powered by advanced AI and modern architecture.

