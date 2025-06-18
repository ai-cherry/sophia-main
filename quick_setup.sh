#!/bin/bash
# SOPHIA AI System - Quick Development Setup Script

set -e  # Exit immediately if a command exits with a non-zero status

# Display banner
echo "=================================================="
echo "SOPHIA AI System - Quick Development Setup"
echo "=================================================="
echo "Starting setup at $(date)"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check Python version
python_version=$(python3 --version | cut -d " " -f 2)
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 11 ]); then
    echo "Error: Python 3.11 or higher is required. Found Python $python_version."
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is not installed. Some features may not work."
    read -p "Do you want to continue without Docker? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup aborted."
        exit 1
    fi
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: Docker Compose is not installed. Some features may not work."
    read -p "Do you want to continue without Docker Compose? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup aborted."
        exit 1
    fi
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please edit .env file with your API keys and configuration."
fi

# Initialize database
echo "Initializing database..."
if command -v docker-compose &> /dev/null; then
    echo "Starting PostgreSQL and Redis with Docker..."
    docker-compose up -d postgres redis
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Run database migrations
    echo "Running database migrations..."
    alembic upgrade head
else
    echo "Skipping database initialization (Docker not available)."
    echo "Please set up PostgreSQL manually and run 'alembic upgrade head'."
fi

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Set up frontend
if [ -d "sophia_admin_frontend" ]; then
    echo "Setting up frontend..."
    cd sophia_admin_frontend
    
    # Check for Node.js
    if command -v npm &> /dev/null; then
        npm install
    else
        echo "Warning: Node.js is not installed. Skipping frontend setup."
    fi
    
    cd ..
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data

# Set permissions
echo "Setting permissions..."
chmod +x deploy_production.sh
chmod +x configure_pulumi_esc.sh
chmod +x quick_setup.sh

# Setup complete
echo ""
echo "=================================================="
echo "Setup completed successfully at $(date)"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your API keys and configuration"
echo "2. Start the development server with: make dev"
echo "3. Or start the full environment with: make dev-full"
echo ""
echo "For more commands, run: make help"
echo ""
