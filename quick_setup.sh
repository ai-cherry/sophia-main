#!/bin/bash

echo "🚀 Quick Setup for Sophia AI"
echo "=========================="

# Generate SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "✅ Generated SECRET_KEY"

# Create a temporary env file with the updates
cat > .env.new << EOF
# Sophia AI Local Environment Configuration
# Updated with essential values

# LLM Gateway (Recommended approach)
LLM_GATEWAY=portkey
PORTKEY_API_KEY=${PORTKEY_API_KEY:-your-portkey-api-key-here}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-your-openrouter-api-key-here}

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sophia
POSTGRES_PASSWORD=sophia_pass
POSTGRES_DB=sophia_payready

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
SECRET_KEY=$SECRET_KEY
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SophiaAdmin2025

# Basic Settings
SOPHIA_ENV=development
HOST=0.0.0.0
PORT=5000
DEBUG=False
FLASK_ENV=development

# Direct LLM APIs (fallback if not using Portkey)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

# Optional integrations (add as needed)
HUBSPOT_API_KEY=${HUBSPOT_API_KEY:-}
GONG_API_KEY=${GONG_API_KEY:-}
GONG_API_SECRET=${GONG_API_SECRET:-}
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:-}
SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET:-}
EOF

# Backup old .env
cp .env .env.backup.$(date +%s)
mv .env.new .env

echo "✅ Updated .env file with:"
echo "   - SECRET_KEY: $SECRET_KEY"
echo "   - ADMIN_PASSWORD: SophiaAdmin2025"
echo ""
echo "⚠️  IMPORTANT: You still need to add your API keys!"
echo ""
echo "To complete setup, edit .env and add ONE of these:"
echo "1. Portkey + OpenRouter keys (recommended)"
echo "2. OpenAI API key"
echo "3. Anthropic API key"
echo ""
echo "Your organization secrets are at:"
echo "https://github.com/organizations/ai-cherry/settings/secrets/actions" 