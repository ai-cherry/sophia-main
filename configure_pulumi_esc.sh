#!/bin/bash
# Sophia AI - Pulumi ESC Configuration Script
# Configures production environment with GitHub org-level secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_status "🔐 SOPHIA AI - PULUMI ESC CONFIGURATION"
echo "========================================"

# Check if Pulumi is installed
if ! command -v pulumi &> /dev/null; then
    print_error "Pulumi CLI not found. Please install Pulumi first."
    exit 1
fi

print_success "Pulumi CLI found: $(pulumi version)"

# Set Pulumi access token if provided
if [ -n "$PULUMI_ACCESS_TOKEN" ]; then
    print_status "Setting Pulumi access token..."
    pulumi login --cloud-url https://app.pulumi.com
    print_success "Pulumi login successful"
else
    print_warning "PULUMI_ACCESS_TOKEN not set. You may need to login manually."
    print_status "Run: pulumi login"
fi

# Create Pulumi ESC environment
print_status "Creating Pulumi ESC environment: ai-cherry/sophia-production"

# Check if environment exists
if pulumi env get ai-cherry/sophia-production &> /dev/null; then
    print_warning "Environment ai-cherry/sophia-production already exists"
    print_status "Updating existing environment..."
else
    print_status "Creating new environment..."
fi

# Create the ESC environment configuration
cat > /tmp/sophia-esc-config.yaml << 'EOF'
values:
  # Database Configuration
  database:
    postgres:
      host: ${POSTGRES_HOST}
      port: ${POSTGRES_PORT}
      user: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
      database: ${POSTGRES_DB}
    redis:
      host: ${REDIS_HOST}
      port: ${REDIS_PORT}
      password: ${REDIS_PASSWORD}
      database: ${REDIS_DB}
  
  # AI/ML Service APIs
  ai_services:
    openai:
      api_key: ${OPENAI_API_KEY}
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
    huggingface:
      api_key: ${HUGGINGFACE_API_KEY}
    cohere:
      api_key: ${COHERE_API_KEY}
    replicate:
      api_key: ${REPLICATE_API_KEY}
    together:
      api_key: ${TOGETHER_API_KEY}
  
  # Gateway Services
  gateways:
    portkey:
      api_key: ${PORTKEY_API_KEY}
    openrouter:
      api_key: ${OPENROUTER_API_KEY}
    kong:
      access_token: ${KONG_ACCESS_TOKEN}
    arize:
      api_key: ${ARIZE_API_KEY}
  
  # Vector Databases
  vector_dbs:
    pinecone:
      api_key: ${PINECONE_API_KEY}
      environment: ${PINECONE_ENVIRONMENT}
      index_name: ${PINECONE_INDEX_NAME}
    weaviate:
      url: ${WEAVIATE_URL}
      api_key: ${WEAVIATE_API_KEY}
  
  # Business Intelligence
  business_intel:
    hubspot:
      api_key: ${HUBSPOT_API_KEY}
    gong:
      api_key: ${GONG_API_KEY}
      api_secret: ${GONG_API_SECRET}
    salesforce:
      client_id: ${SALESFORCE_CLIENT_ID}
      client_secret: ${SALESFORCE_CLIENT_SECRET}
      username: ${SALESFORCE_USERNAME}
      password: ${SALESFORCE_PASSWORD}
      security_token: ${SALESFORCE_SECURITY_TOKEN}
  
  # Communication
  communication:
    slack:
      bot_token: ${SLACK_BOT_TOKEN}
      app_token: ${SLACK_APP_TOKEN}
      signing_secret: ${SLACK_SIGNING_SECRET}
      webhook_url: ${SLACK_WEBHOOK_URL}
    email:
      smtp_host: ${SMTP_HOST}
      smtp_port: ${SMTP_PORT}
      smtp_user: ${SMTP_USER}
      smtp_password: ${SMTP_PASSWORD}
  
  # Infrastructure
  infrastructure:
    aws:
      access_key_id: ${AWS_ACCESS_KEY_ID}
      secret_access_key: ${AWS_SECRET_ACCESS_KEY}
      region: ${AWS_REGION}
    lambda_labs:
      api_key: ${LAMBDA_LABS_API_KEY}
      ssh_key: ${LAMBDA_LABS_SSH_KEY}
  
  # Security
  security:
    secret_key: ${SECRET_KEY}
    master_key: ${SOPHIA_MASTER_KEY}
    jwt_secret: ${JWT_SECRET_KEY}
    admin_username: ${ADMIN_USERNAME}
    admin_password: ${ADMIN_PASSWORD}
  
  # Monitoring
  monitoring:
    grafana:
      admin_password: ${GRAFANA_ADMIN_PASSWORD}
    prometheus:
      auth_token: ${PROMETHEUS_AUTH_TOKEN}
  
  # Data Integration
  data_integration:
    airbyte:
      client_id: ${AIRBYTE_CLIENT_ID}
      client_secret: ${AIRBYTE_CLIENT_SECRET}
      workspace_id: ${AIRBYTE_WORKSPACE_ID}
    dbt:
      api_key: ${DBT_API_KEY}
      account_id: ${DBT_ACCOUNT_ID}
  
  # Development
  development:
    github:
      token: ${GITHUB_TOKEN}
      webhook_secret: ${GITHUB_WEBHOOK_SECRET}
    pulumi:
      access_token: ${PULUMI_ACCESS_TOKEN}

# Environment imports from GitHub organization secrets
imports:
  - type: github-secrets
    organization: ai-cherry
    repository: sophia-main

# Environment configuration
environment:
  SOPHIA_ENV: production
  APP_NAME: "Sophia AI - Pay Ready Assistant"
  COMPANY_NAME: "Pay Ready"
  
# Computed values
computed:
  database_url: "postgresql://${database.postgres.user}:${database.postgres.password}@${database.postgres.host}:${database.postgres.port}/${database.postgres.database}"
  redis_url: "redis://:${database.redis.password}@${database.redis.host}:${database.redis.port}/${database.redis.database}"
EOF

# Apply the ESC configuration
print_status "Applying Pulumi ESC configuration..."
if pulumi env set ai-cherry/sophia-production --file /tmp/sophia-esc-config.yaml; then
    print_success "Pulumi ESC environment configured successfully"
else
    print_error "Failed to configure Pulumi ESC environment"
    exit 1
fi

# Verify the configuration
print_status "Verifying ESC environment configuration..."
if pulumi env get ai-cherry/sophia-production > /dev/null; then
    print_success "ESC environment verification successful"
else
    print_error "ESC environment verification failed"
    exit 1
fi

# Test secret retrieval
print_status "Testing secret retrieval..."
if pulumi env open ai-cherry/sophia-production --json > /tmp/esc-test.json; then
    print_success "Secret retrieval test successful"
    rm -f /tmp/esc-test.json
else
    print_warning "Secret retrieval test failed - some secrets may not be configured"
fi

# Clean up temporary files
rm -f /tmp/sophia-esc-config.yaml

print_success "🎉 PULUMI ESC CONFIGURATION COMPLETED!"
echo ""
print_status "Next Steps:"
echo "1. Configure GitHub organization secrets using the template"
echo "2. Test the configuration: pulumi env open ai-cherry/sophia-production"
echo "3. Deploy Sophia AI using the secure pipeline"
echo ""
print_success "Sophia AI is now ready for enterprise-grade deployment! 🚀"

