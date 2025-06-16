# Sophia AI - Minimal Setup Guide

## Quick Start with Minimal Configuration

### NEW: Simplified LLM Setup with Portkey + OpenRouter

We now use **Portkey** as our LLM gateway with **OpenRouter** as the primary provider. This means:
- ✅ Just 2 API keys for all LLM access
- ✅ Automatic failovers between providers
- ✅ Access to 100+ models through one interface
- ✅ Built-in cost tracking and monitoring

### 1. Create a Basic .env File

You only need these essential keys to get started:

```bash
# Create .env file
cat > .env << 'EOF'
# LLM Gateway (NEW - Recommended!)
LLM_GATEWAY=portkey
PORTKEY_API_KEY=your-portkey-api-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here

# Database (using Docker containers)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sophia
POSTGRES_PASSWORD=sophia_pass
POSTGRES_DB=sophia_payready

REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=your-random-secret-key-here-change-me
JWT_ALGORITHM=HS256

# Admin Access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme123

# Basic Settings
SOPHIA_ENV=development
HOST=0.0.0.0
PORT=5000
DEBUG=False
EOF
```

### 2. Get Your API Keys

1. **Portkey** (5 minutes):
   - Sign up at [app.portkey.ai](https://app.portkey.ai)
   - Copy your API key from the dashboard
   - Free tier available!

2. **OpenRouter** (2 minutes):
   - Sign up at [openrouter.ai](https://openrouter.ai)
   - Add some credits ($5 goes a long way)
   - Copy your API key

3. Update your `.env` file with the actual keys

### 3. Start the System

```bash
# Start database containers
docker-compose up -d sophia-postgres sophia-redis

# Install dependencies
pip install -r requirements.txt

# Run the application
python backend/app/main.py
```

### 4. Features Available with Minimal Config

With just the minimal configuration, you'll have:
- ✅ Core AI capabilities (with your chosen provider)
- ✅ User authentication and sessions
- ✅ Database storage (PostgreSQL + Redis)
- ✅ Basic API endpoints
- ✅ Web interface

### 5. Adding Features Incrementally

As you need more features, add the corresponding API keys:

#### For Gong.io Call Analysis:
```bash
GONG_API_KEY=your-gong-key
GONG_API_SECRET=your-gong-secret
```

#### For HubSpot CRM Integration:
```bash
HUBSPOT_API_KEY=your-hubspot-key
```

#### For Slack Notifications:
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
```

#### For Vector Search:
```bash
# Pinecone
PINECONE_API_KEY=your-pinecone-key
# OR Weaviate
WEAVIATE_URL=your-weaviate-url
WEAVIATE_API_KEY=your-weaviate-key
```

### 6. Check What's Enabled

The system will automatically detect which features are available based on your API keys. Check the logs on startup:

```
INFO: Enabled features: ai_enabled, call_analysis, crm_sync
WARNING: Slack notifications enabled but Slack API not configured
```

### 7. Production Deployment

When ready for production:
1. Generate a strong SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Change ADMIN_PASSWORD to something secure
3. Set `SOPHIA_ENV=production`
4. Add monitoring keys if desired
5. Configure your production database URLs

## Summary

With the new **Portkey + OpenRouter** approach:
- 🚀 **Just 2 API keys** for complete LLM access (instead of separate OpenAI/Anthropic keys)
- 💰 **Cost effective** - OpenRouter finds the cheapest model for your request
- 🔄 **Automatic fallbacks** - Never worry about provider outages
- 📊 **Built-in analytics** - Track usage and costs in one place
- 🎯 **100+ models** - Access Claude, GPT-4, Llama, Mistral, and more

Start with this minimal setup and add integrations (HubSpot, Gong, Slack) only as you need them! 