# Sophia AI - Pay Ready Assistant Orchestrator

<div align="center">
  <h1>🧠 Sophia AI</h1>
  <p><strong>The Intelligent AI Assistant Orchestrator for Pay Ready</strong></p>
  <p>Transform your business operations with AI-powered intelligence</p>
</div>

---

## 🚀 Overview

Sophia AI is an enterprise-grade AI assistant orchestrator designed to serve as the central "Pay Ready Brain" for business operations. It orchestrates multiple specialized AI agents, integrates with business systems, and provides intelligent, contextualized responses to drive business growth and efficiency.

### Key Features

- **🤖 Multi-Agent Orchestration**: Coordinate specialized AI agents for different business functions
- **🔗 Business System Integration**: Seamless integration with HubSpot, Gong.io, Slack, and more
- **📊 Business Intelligence**: Real-time analytics and insights for data-driven decisions
- **🔒 Enterprise Security**: Bank-grade security with encrypted API management
- **📈 Scalable Architecture**: Built for growth with Lambda Labs GPU infrastructure
- **🎯 Custom Workflows**: Support for N8N workflows and domain-specific agents

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│                    API Gateway (Flask)                       │
├─────────────────────────────────────────────────────────────┤
│                  Orchestrator (Sophia Core)                  │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ Call Analysis│  CRM Sync    │ Notification │  Custom       │
│    Agent     │   Agent      │    Agent     │  Agents       │
├──────────────┴──────────────┴──────────────┴───────────────┤
│                    Integration Layer                         │
├────────┬──────────┬──────────┬──────────┬─────────────────┤
│HubSpot │ Gong.io  │  Slack   │PostgreSQL│ Vector DBs      │
└────────┴──────────┴──────────┴──────────┴─────────────────┘
```

## 🚦 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and pnpm
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/payready/sophia-ai.git
   cd sophia-ai
   ```

2. **Set up environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   make install
   ```

4. **Run database migrations**
   ```bash
   make db-migrate
   ```

5. **Start development servers**
   ```bash
   make dev
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - API Documentation: http://localhost:5000/docs

## 🔧 Configuration

### Environment Variables

Key environment variables (see `env.example` for full list):

- `SOPHIA_ENV`: Environment (development/production)
- `OPENAI_API_KEY`: OpenAI API key for AI capabilities
- `HUBSPOT_API_KEY`: HubSpot CRM integration
- `GONG_API_KEY`: Gong.io call analysis
- `SLACK_BOT_TOKEN`: Slack integration

### Database Configuration

PostgreSQL and Redis connection settings are configured in `.env`:

```env
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_USER=sophia
POSTGRES_PASSWORD=your-password
POSTGRES_DB=sophia_payready

REDIS_HOST=your-redis-host
REDIS_PORT=6379
```

## 📚 Documentation

- [Technical Architecture](docs/implementation/sophia_technical_architecture.md)
- [Implementation Plan](docs/implementation/sophia_implementation_plan.md)
- [Development Timeline](docs/implementation/sophia_development_timeline.md)
- [API Documentation](docs/sophia_api_authentication_report.md)
- [MCP Server Documentation](docs/mcp_server_documentation.md)

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=backend --cov-report=html
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and start containers
make docker-build
make docker-up

# Stop containers
make docker-down
```

### Production Deployment (Lambda Labs)

```bash
# Deploy to production
make deploy
```

The deployment uses Pulumi for infrastructure as code. Configure your Lambda Labs credentials in the Pulumi configuration.

## 🛠️ Development

### Common Commands

```bash
# Format code
make format

# Run linting
make lint

# Security check
make security-check

# View logs
make logs

# Database shell
make db-shell

# Python shell with context
make shell
```

### Creating New Agents

```bash
# Create a new specialized agent
make new-agent
# Enter agent name when prompted
```

### Project Structure

```
sophia-ai/
├── backend/               # Python backend
│   ├── agents/           # AI agents
│   ├── app/              # Flask application
│   ├── integrations/     # External integrations
│   ├── monitoring/       # System monitoring
│   └── security/         # Security management
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # UI components
│   │   └── pages/        # Page components
├── infrastructure/       # IaC (Pulumi)
├── tests/               # Test suite
└── docs/                # Documentation
```

## 📊 Monitoring

Access monitoring dashboards:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default: admin/admin)

```bash
# Open monitoring dashboards
make monitor
```

## 🔒 Security

Sophia AI implements enterprise-grade security:

- **Encrypted API Keys**: All sensitive credentials are encrypted at rest
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Protection against abuse
- **Audit Logging**: Comprehensive security event logging
- **Session Management**: Secure session handling

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Python: Black formatter with 88-character line limit
- TypeScript/React: ESLint + Prettier
- Commit messages: Conventional Commits

## 📝 License

This project is proprietary software owned by Pay Ready. All rights reserved.

## 🆘 Support

For support and questions:
- Internal Slack: #sophia-support
- Email: sophia-team@payready.com
- Documentation: [Internal Wiki](https://wiki.payready.com/sophia)

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Core orchestrator framework
- ✅ HubSpot and Gong.io integration
- ✅ Basic agent implementation
- ✅ Security and monitoring

### Phase 2 (Q1 2024)
- 🔄 Hierarchical agent architecture
- 🔄 Advanced analytics dashboard
- 🔄 N8N workflow integration
- 🔄 Mobile application

### Phase 3 (Q2 2024)
- 📋 Multi-tenant support
- 📋 Advanced ML capabilities
- 📋 Voice interface
- 📋 International expansion

---

<div align="center">
  <p>Built with ❤️ by the Pay Ready Team</p>
  <p>Making business intelligence accessible to everyone</p>
</div>

