#!/bin/bash
# SOPHIA AI System - Production Deployment Script

set -e  # Exit immediately if a command exits with a non-zero status

# Display banner
echo "=================================================="
echo "SOPHIA AI System - Production Deployment"
echo "=================================================="
echo "Starting deployment at $(date)"
echo ""

# Check if running with correct permissions
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
  echo "Loading environment variables from .env file..."
  export $(grep -v '^#' .env | xargs)
else
  echo "Error: .env file not found!"
  echo "Please create a .env file with the required environment variables."
  exit 1
fi

# Verify required environment variables
required_vars=(
  "OPENAI_API_KEY"
  "PINECONE_API_KEY"
  "POSTGRES_PASSWORD"
  "REDIS_PASSWORD"
  "JWT_SECRET"
  "DEPLOYMENT_ENV"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: Required environment variable $var is not set!"
    exit 1
  fi
done

# Check deployment environment
if [ "$DEPLOYMENT_ENV" != "production" ]; then
  echo "Warning: DEPLOYMENT_ENV is not set to 'production'!"
  read -p "Do you want to continue with deployment? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment aborted."
    exit 1
  fi
fi

# Pull latest code
echo "Pulling latest code from repository..."
git pull origin main

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Build frontend
echo "Building frontend..."
cd sophia_admin_frontend
npm install
npm run build
cd ..

# Run security checks
echo "Running security checks..."
safety check
bandit -r backend/

# Run tests
echo "Running tests..."
pytest tests/ -v

# Build Docker images
echo "Building Docker images..."
docker-compose build

# Deploy with Docker Compose
echo "Deploying with Docker Compose..."
docker-compose --profile production down
docker-compose --profile production up -d

# Verify deployment
echo "Verifying deployment..."
sleep 10  # Wait for services to start

# Check if API is running
if curl -s http://localhost:8000/health | grep -q "status.*ok"; then
  echo "API is running successfully."
else
  echo "Error: API is not running properly!"
  echo "Check logs with: docker-compose logs sophia-api"
  exit 1
fi

# Check if frontend is running
if curl -s http://localhost:3000 | grep -q "SOPHIA"; then
  echo "Frontend is running successfully."
else
  echo "Error: Frontend is not running properly!"
  echo "Check logs with: docker-compose logs sophia-admin"
  exit 1
fi

# Check if MCP server is running
if curl -s http://localhost:8002/health | grep -q "status.*ok"; then
  echo "MCP server is running successfully."
else
  echo "Error: MCP server is not running properly!"
  echo "Check logs with: docker-compose logs mcp-server"
  exit 1
fi

# Setup monitoring
echo "Setting up monitoring..."
docker-compose --profile monitoring up -d

# Run Pulumi deployment for cloud infrastructure
if [ "$DEPLOY_CLOUD_INFRA" = "true" ]; then
  echo "Deploying cloud infrastructure with Pulumi..."
  cd infrastructure
  pulumi up --yes
  cd ..
fi

# Update secrets in Pulumi ESC
echo "Updating secrets in Pulumi ESC..."
./configure_pulumi_esc.sh

# Final steps
echo "Running post-deployment tasks..."
python production_data_populator.py

echo ""
echo "=================================================="
echo "Deployment completed successfully at $(date)"
echo "=================================================="
echo ""
echo "Services deployed:"
echo "- API: http://localhost:8000"
echo "- Admin UI: http://localhost:3000"
echo "- MCP Server: http://localhost:8002"
echo "- Monitoring: http://localhost:3001"
echo ""
echo "To view logs:"
echo "docker-compose logs -f"
echo ""
echo "To stop the services:"
echo "docker-compose --profile production down"
echo ""
