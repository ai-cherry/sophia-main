# GitHub Secrets Setup for Sophia AI

## Overview

Instead of managing dozens of API keys locally, we use GitHub Secrets with a unified LLM gateway (Portkey + OpenRouter) for a cleaner, more secure setup.

## LLM Strategy: Portkey + OpenRouter

### Why This Approach?

1. **Single API Key**: Use Portkey as the gateway with OpenRouter as primary provider
2. **Automatic Fallbacks**: If OpenRouter is down, automatically falls back to OpenAI/Anthropic
3. **Cost Optimization**: OpenRouter provides access to many models at competitive prices
4. **No Vendor Lock-in**: Easy to switch providers without code changes
5. **Built-in Monitoring**: Portkey provides usage analytics and logging

### Architecture

```
Your App -> Portkey Gateway -> OpenRouter (Primary)
                            -> OpenAI (Fallback)
                            -> Anthropic (Fallback)
```

## Required GitHub Secrets

### Core Secrets (Minimum)

1. **`SECRET_KEY`** - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
2. **`ADMIN_PASSWORD`** - Strong password for admin access
3. **`PORTKEY_API_KEY`** - From [Portkey Dashboard](https://app.portkey.ai)
4. **`OPENROUTER_API_KEY`** - From [OpenRouter](https://openrouter.ai/keys)

### Database Secrets

5. **`POSTGRES_HOST`** - Database host (e.g., `localhost` or your server IP)
6. **`POSTGRES_PORT`** - Default: `5432`
7. **`POSTGRES_USER`** - Default: `sophia`
8. **`POSTGRES_PASSWORD`** - Database password
9. **`POSTGRES_DB`** - Default: `sophia_payready`
10. **`REDIS_HOST`** - Redis host
11. **`REDIS_PORT`** - Default: `6379`
12. **`REDIS_PASSWORD`** - Redis password (if configured)

### Optional Integration Secrets

Only add these as you need them:

- **`HUBSPOT_API_KEY`** - For CRM integration
- **`GONG_API_KEY`** & **`GONG_API_SECRET`** - For call analysis
- **`SLACK_BOT_TOKEN`** & **`SLACK_SIGNING_SECRET`** - For Slack notifications
- **`PINECONE_API_KEY`** - For vector search
- **`LAMBDA_LABS_API_KEY`** - For deployment

## Setting Up Secrets in GitHub

### Step 1: Navigate to Repository Settings

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**

### Step 2: Add Core Secrets

Click **New repository secret** for each:

```bash
# Generate these values
SECRET_KEY=<generated-64-char-hex>
ADMIN_PASSWORD=<strong-password>

# From Portkey dashboard
PORTKEY_API_KEY=<your-portkey-key>

# From OpenRouter
OPENROUTER_API_KEY=<your-openrouter-key>

# Database (adjust for your setup)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sophia
POSTGRES_PASSWORD=<db-password>
POSTGRES_DB=sophia_payready
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Step 3: Configure Portkey

1. Log into [Portkey Dashboard](https://app.portkey.ai)
2. Add your provider API keys:
   - OpenRouter API key
   - OpenAI API key (optional fallback)
   - Anthropic API key (optional fallback)
3. Create a virtual key for each provider
4. Note your Portkey API key

### Step 4: Configure OpenRouter

1. Sign up at [OpenRouter](https://openrouter.ai)
2. Add credits to your account
3. Copy your API key
4. OpenRouter gives you access to:
   - Claude 3 Opus/Sonnet
   - GPT-4 Turbo
   - Llama 3
   - Mistral
   - And many more models

## Local Development

For local development, create a minimal `.env` file:

```bash
# Minimal .env for local development
PORTKEY_API_KEY=your-portkey-key
OPENROUTER_API_KEY=your-openrouter-key

# Local database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sophia
POSTGRES_PASSWORD=sophia_pass
POSTGRES_DB=sophia_payready

REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=local-development-key
ADMIN_PASSWORD=changeme
```

## Deployment

The GitHub Action automatically creates the `.env` file from secrets during deployment:

```yaml
- name: Create .env from GitHub Secrets
  run: |
    cat > .env << EOF
    PORTKEY_API_KEY=${{ secrets.PORTKEY_API_KEY }}
    OPENROUTER_API_KEY=${{ secrets.OPENROUTER_API_KEY }}
    # ... other secrets
    EOF
```

## Cost Optimization Tips

1. **Use OpenRouter's Model Routing**: Let OpenRouter choose the cheapest available model
2. **Set Model Preferences**: Configure preferred models in Portkey dashboard
3. **Enable Caching**: Portkey's semantic caching reduces API calls
4. **Monitor Usage**: Both Portkey and OpenRouter provide detailed usage analytics

## Verifying Your Setup

After setting up secrets, test the configuration:

```python
# Test script
from backend.agents.core.llm_client import get_llm_client

async def test_llm():
    client = get_llm_client()
    response = await client.complete_with_context(
        prompt="Hello, what's 2+2?",
        temperature=0
    )
    print(f"Response: {response}")
    print(f"Available models: {client.get_available_models()}")

# Run: python -m asyncio test_llm()
```

## Benefits of This Approach

1. **Simplified Configuration**: Just 2 LLM-related keys instead of multiple provider keys
2. **Automatic Failover**: If one provider fails, requests automatically route to another
3. **Cost Visibility**: Single dashboard to monitor all LLM costs
4. **Easy Testing**: Switch models without code changes
5. **Future Proof**: Add new providers without updating application code

## Troubleshooting

### "No LLM provider configured"
- Ensure `PORTKEY_API_KEY` and `OPENROUTER_API_KEY` are set
- Check that keys are valid in respective dashboards

### High Latency
- Portkey automatically routes to fastest provider
- Check Portkey dashboard for latency metrics

### Rate Limits
- OpenRouter handles rate limits across providers
- Portkey automatically retries with backoff

## Summary

With GitHub Secrets + Portkey + OpenRouter:
- ✅ Secure API key management
- ✅ Single unified LLM interface
- ✅ Automatic failovers
- ✅ Cost optimization
- ✅ Easy provider switching
- ✅ Built-in monitoring

This approach scales from development to production without configuration changes! 