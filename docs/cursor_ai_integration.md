# Sophia AI - Cursor AI Integration Guide

## 🎯 **ENHANCED CURSOR AI INTEGRATION WITH PERMANENT SECRET MANAGEMENT**

This guide demonstrates how to leverage Sophia AI's **PERMANENT GitHub Organization Secrets → Pulumi ESC** solution within Cursor AI for seamless development workflows.

## 🔐 **PERMANENT SECRET MANAGEMENT INTEGRATION**

### **Zero Manual Configuration Required**
Sophia AI now uses a **PERMANENT** secret management solution that eliminates all manual secret handling:

```
GitHub Organization Secrets (ai-cherry)
           ↓
    GitHub Actions (automatic sync)
           ↓
    Pulumi ESC Environments
           ↓
    Sophia AI Backend (automatic loading)
           ↓
    Cursor AI (automatic access)
```

### **✅ What's Automated for Cursor AI**
- ✅ All API keys automatically available
- ✅ No more `.env` file management
- ✅ Automatic service authentication
- ✅ Zero credential configuration
- ✅ Enterprise-grade security

### **🔑 Cursor AI Secret Access Pattern**
```python
# Cursor AI automatically accesses secrets through ESC
from backend.core.auto_esc_config import config

# All secrets automatically available in Cursor AI
openai_key = config.openai_api_key
gong_key = config.gong_access_key
slack_token = config.slack_bot_token
```

## 🚀 **Quick Setup for Cursor AI**

### **1. One-Time Setup**
```bash
# Clone and setup (only needed once)
git clone https://github.com/ai-cherry/sophia-main.git
cd sophia-main

# Set Pulumi organization
export PULUMI_ORG=scoobyjava-org

# Set Pulumi access token
export PULUMI_ACCESS_TOKEN=your_token_here

# Sync secrets from Pulumi ESC
python scripts/setup_all_secrets_once.py

# Test everything works
python scripts/test_permanent_solution.py
```

### **2. Start Development in Cursor AI**
```bash
# Start backend (automatically loads all secrets)
python backend/main.py

# Start frontend
cd frontend && npm run dev

# All integrations work immediately - no configuration needed!
```

## 🛠️ **Cursor AI Natural Language Commands**

### **Infrastructure Management Commands**
- **Deploy Infrastructure**: "Deploy the Lambda Labs infrastructure"
- **Update Secrets**: "Rotate the Gong API credentials"
- **Check Health**: "Verify all service integrations are healthy"
- **Scale Resources**: "Scale up the Snowflake warehouse"

### **MCP Server Integration Commands**
- **Start MCP Servers**: `docker-compose -f docker-compose.mcp.yml up -d`
- **Check MCP Status**: `curl http://localhost:8000/snowflake/health`
- **Query via MCP**: Use the MCP client tools in `backend/mcp/`

### **Development Workflow**
1. **Local Development**: No secret setup required - everything automatic
2. **Secret Management**: Always use GitHub organization secrets
3. **Testing**: Run ESC integration tests before deployment
4. **Deployment**: Use GitHub Actions for all production deployments

### **Security Best Practices**
- Never hardcode secrets in code
- Always use automatic ESC integration
- Update secrets via GitHub organization settings
- Validate all secret operations with comprehensive testing

### **Troubleshooting Commands**
- **Check ESC Status**: `export PULUMI_ORG=scoobyjava-org && pulumi env ls`
- **Validate Secrets**: `python scripts/test_permanent_solution.py`
- **Debug Workflows**: Check GitHub Actions logs and artifacts
- **MCP Debugging**: Check Docker logs with `docker-compose logs`

## 🏗️ **Enhanced Cursor AI Development Patterns**

### **Automatic Configuration Access**
```python
# Cursor AI can immediately use any service
from backend.core.auto_esc_config import config

# All these work automatically without setup:
gong_client = GongClient(
    access_key=config.gong_access_key,
    client_secret=config.gong_client_secret
)

slack_client = SlackClient(token=config.slack_bot_token)
snowflake_client = SnowflakeClient(
    account=config.snowflake_account,
    user=config.snowflake_user,
    password=config.snowflake_password
)
```

### **Natural Language Infrastructure Commands**
```bash
# These commands work immediately in Cursor AI:
"Deploy to Lambda Labs with A100 GPU"
"Query Snowflake for recent sales data"
"Send Slack notification about deployment"
"Analyze Gong calls from this week"
"Update Pinecone vector index"
```

### Backend Configuration Integration Commands
When working with backend configuration, use these enhanced patterns:

#### Configuration Management
- "Check service configuration for Gong" → `python -c "import asyncio; from backend.core.config_manager import get_config; print(asyncio.run(get_config('gong')))"`
- "Validate all integrations" → `python -c "import asyncio; from backend.core.config_manager import list_services, health_check; services = asyncio.run(list_services()); [print(f'{s}: {asyncio.run(health_check(s))}') for s in services]"`
- "List registered services" → `python -c "import asyncio; from backend.core.config_manager import list_services; print(asyncio.run(list_services()))"`
- "Refresh configuration cache" → `python -c "import asyncio; from backend.core.config_manager import refresh_cache; asyncio.run(refresh_cache())"`

#### Secret Management with Backend Integration
- "Get database connection string" → Automatic via ESC integration
- "Initialize Pinecone client" → Automatic via ESC integration
- "Test Gong API access" → Automatic via ESC integration

#### Integration Testing Commands
- "Check all service health" → Batch health check across all configured services
- "Validate all configurations" → Comprehensive configuration validation
- "Test API response times" → Performance benchmarking for all services

#### Advanced Backend Operations
- "Update service configuration" → Runtime configuration updates with ESC
- "Diagnose configuration issues" → Automated troubleshooting with ESC
- "Optimize cache settings" → Performance tuning with automatic fallbacks

### Natural Language Command Patterns for Backend Integration
Use these natural language patterns for complex backend operations:

#### Conditional Operations
- "If Snowflake is unavailable, use backup database"
- "Deploy only if all health checks pass"
- "Rotate secrets for services with expired credentials"

#### Batch Operations
- "Check health of all API services"
- "Refresh cache for all database connections"
- "Validate configuration for all integrations"

#### Troubleshooting Operations
- "Diagnose why Gong integration is failing"
- "Show configuration issues for all services"
- "Check secret expiration status"

### MCP Agent Integration with Backend Configuration
Enhanced MCP integration leveraging centralized configuration:

#### Dynamic MCP Operations
- **Service-Aware MCP**: MCP agents automatically discover available services
- **Configuration-Driven MCP**: MCP operations use centralized configuration
- **Health-Aware MCP**: MCP agents check service health before operations

#### Natural Language MCP Commands
- "Use MCP to query Gong for recent data" → MCP agent with Gong integration
- "Deploy via MCP using current Vercel config" → MCP deployment with configuration
- "Sync data between services via MCP" → Cross-service MCP orchestration

### Error Handling and Recovery Patterns
Enhanced error handling with backend integration:

#### Automatic Fallbacks
- Configuration fallback to environment variables
- Service health check with automatic retry
- Cache invalidation on configuration errors

#### Error Diagnostics
- Comprehensive error logging with context
- Configuration validation with detailed feedback
- Service dependency checking

### Performance and Monitoring Integration
Backend configuration system includes performance monitoring:

#### Performance Metrics
- Configuration cache hit rates
- Service response time tracking
- Secret rotation monitoring

#### Optimization Features
- Intelligent caching with TTL
- Connection pooling for API clients
- Batch operations for efficiency

### Security Best Practices with Backend Integration
Enhanced security with centralized configuration:

#### Secret Security
- Secure secret caching with TTL
- Automatic secret masking in logs
- Secret rotation tracking

#### Access Control
- Service-level access validation
- Configuration audit logging
- Secure fallback mechanisms

### Development Workflow with Enhanced Backend
Streamlined development workflow:

1. **Configuration Setup**: Use centralized configuration manager
2. **Service Registration**: Register services in integration registry
3. **Health Validation**: Validate all service health before deployment
4. **Performance Monitoring**: Monitor service performance continuously
5. **Error Recovery**: Automatic error recovery with fallback mechanisms

### Best Practices for Backend Configuration Integration
1. **Always use centralized configuration**: Never hardcode service configurations
2. **Validate configurations**: Always validate configuration completeness
3. **Monitor service health**: Regular health checks for all services
4. **Cache efficiently**: Use intelligent caching for performance
5. **Handle errors gracefully**: Implement comprehensive error handling
6. **Secure secrets**: Use secure secret management practices
7. **Monitor performance**: Track performance metrics continuously
8. **Document configurations**: Maintain clear configuration documentation

## 🎯 **Success Indicators for Cursor AI**

When everything is working correctly in Cursor AI:
- ✅ Backend starts without any credential errors
- ✅ All natural language commands execute successfully
- ✅ MCP servers respond to health checks
- ✅ All API integrations work immediately
- ✅ No manual secret management required ever
- ✅ Comprehensive testing passes: `python scripts/test_permanent_solution.py`

## 🔒 **Security Guarantee for Cursor AI**

The permanent solution ensures:
- **Zero exposed credentials** in Cursor AI workspace
- **Automatic secret synchronization** across all environments
- **Enterprise-grade security** with encrypted storage
- **Comprehensive audit trail** for all secret access
- **Zero manual intervention** required for secret management

**🎯 RESULT: CURSOR AI WITH PERMANENT SECRET MANAGEMENT - DEVELOP WITHOUT EVER THINKING ABOUT CREDENTIALS!**
