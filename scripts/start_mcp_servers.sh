#!/bin/bash
# Startup script for Sophia AI MCP Servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MCP_DIR="$(dirname "$0")/.."
COMPOSE_FILE="docker-compose.mcp.yml"
ENV_FILE=".env"

echo -e "${GREEN}🚀 Starting Sophia AI MCP Infrastructure${NC}"
echo "========================================="

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check Docker Compose
if ! docker-compose --version &> /dev/null 2>&1; then
    # Try docker compose (v2)
    if ! docker compose version &> /dev/null 2>&1; then
        echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"

# Check environment file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ .env file not found. Creating from template...${NC}"
    cp env.example .env
    echo -e "${YELLOW}⚠️  Please update .env with your credentials before continuing.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p mcp-servers/snowflake
mkdir -p mcp-config
mkdir -p mcp-logs
mkdir -p keys

# Check for Snowflake key pair if using keypair auth
SNOWFLAKE_AUTH_METHOD=$(grep SNOWFLAKE_AUTH_METHOD .env | cut -d '=' -f2 | tr -d '"' || echo "password")
if [ "$SNOWFLAKE_AUTH_METHOD" = "keypair" ]; then
    if [ ! -f "keys/snowflake_rsa_key.p8" ]; then
        echo -e "${YELLOW}⚠️  Snowflake private key not found at keys/snowflake_rsa_key.p8${NC}"
        echo -e "${YELLOW}   Generate it with: python3 scripts/generate_snowflake_keypair.py${NC}"
    fi
fi

# Generate MCP auth token if not exists
if ! grep -q "MCP_AUTH_TOKEN" .env; then
    echo -e "\n${YELLOW}Generating MCP auth token...${NC}"
    MCP_TOKEN=$(openssl rand -hex 32)
    echo "MCP_AUTH_TOKEN=$MCP_TOKEN" >> .env
    echo -e "${GREEN}✅ Generated MCP auth token${NC}"
fi

# Stop any existing containers
echo -e "\n${YELLOW}Stopping any existing MCP containers...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE down --remove-orphans 2>/dev/null || true

# Build custom MCP servers
echo -e "\n${YELLOW}Building MCP gateway and Snowflake server...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE build mcp-gateway snowflake-mcp

# Start MCP infrastructure
echo -e "\n${YELLOW}Starting MCP servers...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d mcp-gateway snowflake-mcp

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Check service status
echo -e "\n${GREEN}Service Status:${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE ps

# Test MCP gateway
echo -e "\n${YELLOW}Testing MCP gateway...${NC}"
if curl -s -f http://localhost:8090/health > /dev/null; then
    echo -e "${GREEN}✅ MCP gateway is healthy${NC}"
    curl -s http://localhost:8090/health
    echo ""
else
    echo -e "${RED}❌ MCP gateway health check failed${NC}"
    echo -e "${YELLOW}Check logs with: $DOCKER_COMPOSE -f $COMPOSE_FILE logs mcp-gateway${NC}"
fi

# Display connection information
echo -e "\n${GREEN}🎉 Snowflake MCP Server Started Successfully!${NC}"
echo "========================================="
echo -e "MCP Gateway URL: ${GREEN}http://localhost:8090${NC}"
echo -e ""
echo -e "${YELLOW}Available commands:${NC}"
echo -e "View logs:    ${GREEN}$DOCKER_COMPOSE -f $COMPOSE_FILE logs -f${NC}"
echo -e "Stop servers: ${GREEN}$DOCKER_COMPOSE -f $COMPOSE_FILE down${NC}"
echo -e "Test MCP:     ${GREEN}python3 scripts/test_snowflake_mcp.py${NC}"

# Check if Snowflake is configured
if ! grep -q "SNOWFLAKE_ACCOUNT=" .env || [ "$(grep SNOWFLAKE_ACCOUNT= .env | cut -d '=' -f2)" = "your_snowflake_account" ]; then
    echo -e "\n${YELLOW}⚠️  Note: Snowflake credentials not configured in .env${NC}"
    echo -e "${YELLOW}   Update .env with your Snowflake credentials to use data operations${NC}"
fi

echo -e "\n${GREEN}Next steps:${NC}"
echo "1. Configure Snowflake credentials in .env (if not done)"
echo "2. Test with: python3 scripts/test_snowflake_mcp.py"
echo "3. Use MCP tools in your AI agents"
echo ""
echo -e "${YELLOW}To add more services later:${NC}"
echo "- Uncomment services in docker-compose.mcp.yml"
echo "- Add their credentials to .env"
echo "- Run this script again"

echo -e "\n${GREEN}Ready to use Snowflake MCP with Sophia AI!${NC}" 