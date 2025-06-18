.PHONY: help setup dev test lint format clean docker-build docker-up docker-down deploy-dev deploy-prod

# Default target
help:
	@echo "SOPHIA AI System - Development Commands"
	@echo "-------------------------------------"
	@echo "setup         - Install dependencies and set up development environment"
	@echo "dev           - Run development server"
	@echo "test          - Run tests"
	@echo "lint          - Run linters"
	@echo "format        - Format code"
	@echo "clean         - Clean up temporary files"
	@echo "docker-build  - Build Docker images"
	@echo "docker-up     - Start Docker containers"
	@echo "docker-down   - Stop Docker containers"
	@echo "deploy-dev    - Deploy to development environment"
	@echo "deploy-prod   - Deploy to production environment"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "Development environment setup complete."

# Run development server
dev:
	@echo "Starting development server..."
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --cov=backend

# Run linters
lint:
	@echo "Running linters..."
	flake8 backend tests
	mypy backend
	pylint backend

# Format code
format:
	@echo "Formatting code..."
	black backend tests
	isort backend tests

# Clean up temporary files
clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

# Deployment commands
deploy-dev:
	@echo "Deploying to development environment..."
	./deploy_dev.sh

deploy-prod:
	@echo "Deploying to production environment..."
	./deploy_production.sh

# Database commands
db-migrate:
	@echo "Running database migrations..."
	alembic upgrade head

db-rollback:
	@echo "Rolling back last database migration..."
	alembic downgrade -1

db-reset:
	@echo "Resetting database..."
	alembic downgrade base
	alembic upgrade head

# MCP server commands
mcp-server:
	@echo "Starting MCP server..."
	python -m backend.mcp.server

# Monitoring commands
monitoring-up:
	@echo "Starting monitoring stack..."
	docker-compose --profile monitoring up -d

monitoring-down:
	@echo "Stopping monitoring stack..."
	docker-compose --profile monitoring down

# Frontend commands
frontend-dev:
	@echo "Starting frontend development server..."
	cd sophia_admin_frontend && npm run dev

frontend-build:
	@echo "Building frontend..."
	cd sophia_admin_frontend && npm run build

# Full development environment
dev-full:
	@echo "Starting full development environment..."
	docker-compose up -d postgres redis weaviate mem0
	python -m backend.mcp.server & 
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
