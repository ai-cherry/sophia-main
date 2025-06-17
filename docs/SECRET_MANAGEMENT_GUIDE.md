# 🔐 Sophia AI Secret Management Guide

## 🎯 The Problem We're Solving

Managing 50+ API keys across multiple services (GitHub, Vercel, Lambda Labs, local dev) is a fucking nightmare. This guide provides ONE unified approach.

## ✅ The Solution: Pulumi ESC + GitHub Secrets

### Why This Approach?
- **Single Source of Truth**: Pulumi ESC stores all secrets
- **Automatic Sync**: Push to GitHub, Vercel, etc. with one command
- **Version Control**: Track secret changes
- **Environment Support**: Dev, staging, production
- **No More Manual Updates**: Ever.

## 🚀 Quick Start

### 1. Initial Setup (One Time Only)

```bash
# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh

# Login to Pulumi
pulumi login

# Run the unified setup
python scripts/setup_pulumi_secrets.py full-setup
```

### 2. Import Your Existing Secrets

```bash
# From your .env file
python scripts/setup_pulumi_secrets.py import-env --env-file .env

# Or from .env.backup
python scripts/setup_pulumi_secrets.py import-env --env-file .env.backup
```

### 3. Sync to GitHub

```bash
# This syncs ALL secrets to GitHub org secrets
python scripts/setup_pulumi_secrets.py sync
```

## 📋 Secret Naming Convention

### IMPORTANT: Use These EXACT Names

| Service | Secret Name in GitHub | Notes |
|---------|---------------------|-------|
| Vercel | `VERCEL_ACCESS_TOKEN` | NOT `VERCEL_TOKEN`! |
| Lambda Labs | `LAMBDA_LABS_API_KEY` | For backend deployment |
| Pulumi | `PULUMI_ACCESS_TOKEN` | For infrastructure |
| OpenAI | `OPENAI_API_KEY` | Direct API access |
| Portkey | `PORTKEY_API_KEY` | LLM gateway (recommended) |
| Kong | `KONG_ACCESS_TOKEN` | API gateway |

### Complete Secret List

```bash
# Core Security
SECRET_KEY              # Django/FastAPI secret
ADMIN_USERNAME          # Admin login
ADMIN_PASSWORD          # Admin password
SOPHIA_MASTER_KEY       # Master encryption key

# Database
POSTGRES_HOST           # Default: localhost
POSTGRES_PORT           # Default: 5432
POSTGRES_USER           # Database user
POSTGRES_PASSWORD       # Database password
POSTGRES_DB             # Database name
REDIS_HOST              # Default: localhost
REDIS_PORT              # Default: 6379
REDIS_PASSWORD          # Redis password (optional)

# LLM Services (Pick One Strategy)
## Option 1: Gateway (Recommended)
PORTKEY_API_KEY         # Unified LLM gateway
OPENROUTER_API_KEY      # Alternative gateway

## Option 2: Direct APIs
OPENAI_API_KEY          # OpenAI direct
ANTHROPIC_API_KEY       # Anthropic direct

# Business APIs
HUBSPOT_API_KEY         # CRM integration
GONG_API_KEY            # Call analysis
GONG_API_SECRET         # Gong secret

# Communication
SLACK_BOT_TOKEN         # Slack bot
SLACK_APP_TOKEN         # Slack app
SLACK_SIGNING_SECRET    # Slack security
SLACK_WEBHOOK_URL       # Slack webhooks

# Vector Databases
PINECONE_API_KEY        # Vector search
WEAVIATE_URL            # Weaviate endpoint
WEAVIATE_API_KEY        # Weaviate auth

# Deployment
LAMBDA_LABS_API_KEY     # Backend hosting
VERCEL_ACCESS_TOKEN     # Frontend hosting
PULUMI_ACCESS_TOKEN     # Infrastructure

# Monitoring
GRAFANA_ADMIN_PASSWORD  # Grafana login
```

## 🔧 Common Tasks

### Add a New Secret

```bash
# Using Pulumi ESC
pulumi env set ai-cherry/production sophia/new-category/secret-name "secret-value" --secret

# Then sync to GitHub
python scripts/setup_pulumi_secrets.py sync
```

### Update a Secret

```bash
# Same as adding - Pulumi handles versioning
pulumi env set ai-cherry/production sophia/llm/openai-key "new-key-value" --secret

# Sync to GitHub
python scripts/setup_pulumi_secrets.py sync
```

### View All Secrets

```bash
# List all secrets (values hidden)
pulumi env get ai-cherry/production

# Export to .env file
python scripts/setup_pulumi_secrets.py export --output .env.production
```

### Validate Configuration

```bash
# Check all required secrets are set
python scripts/setup_pulumi_secrets.py validate
```

## 🚨 Troubleshooting

### "Secret not found" in GitHub Actions

1. Check the EXACT secret name (e.g., `VERCEL_ACCESS_TOKEN` not `VERCEL_TOKEN`)
2. Run sync: `python scripts/setup_pulumi_secrets.py sync`
3. Verify in GitHub: Settings → Secrets → Organization secrets

### Deployment Failing

1. Check workflow logs for which secrets are missing
2. The simplified workflow will show: "No Vercel token - skipping frontend deployment"
3. Add the missing secret and re-run

### Local Development

```bash
# Generate .env from Pulumi
python scripts/setup_pulumi_secrets.py export --output .env

# Or use minimal setup
cp env.minimal.example .env
# Add only the keys you need
```

## 🎯 Best Practices

### 1. Use Gateways When Possible
Instead of managing 5 LLM API keys, use Portkey or OpenRouter:
```bash
# Just need these two
PORTKEY_API_KEY=...
OPENROUTER_API_KEY=...
```

### 2. Environment-Specific Secrets
```bash
# Development
pulumi env init ai-cherry/development

# Production
pulumi env init ai-cherry/production
```

### 3. Regular Rotation
```bash
# Rotate a secret
pulumi env set ai-cherry/production sophia/core/secret-key "$(openssl rand -base64 32)" --secret
python scripts/setup_pulumi_secrets.py sync
```

## 🚀 Migration Path

### From Current Mess → Clean Setup

1. **Export current secrets**:
   ```bash
   # If you have them in .env
   cp .env .env.backup.$(date +%s)
   ```

2. **Import to Pulumi**:
   ```bash
   python scripts/setup_pulumi_secrets.py import-env --env-file .env.backup
   ```

3. **Sync everywhere**:
   ```bash
   python scripts/setup_pulumi_secrets.py sync
   ```

4. **Update workflows**:
   - Use `.github/workflows/deploy-simplified.yml`
   - Or fix the main workflow with correct secret names

5. **Test deployment**:
   ```bash
   git push origin main
   # Watch GitHub Actions for any issues
   ```

## 📝 Summary

- **Pulumi ESC** = Single source of truth
- **`setup_pulumi_secrets.py`** = Your secret management tool
- **Correct secret names** = Critical (especially VERCEL_ACCESS_TOKEN)
- **One command sync** = No more manual updates

Stop fucking around with manual secret management. Use this system and move on to building features!

---

**Questions?** The script has `--help` for all commands:
```bash
python scripts/setup_pulumi_secrets.py --help
``` 