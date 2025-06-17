# Sophia AI - Development Makefile
# Common commands for development and deployment

.PHONY: help install dev prod test clean docker-build docker-up docker-down db-migrate db-reset lint format security-check deploy

# Default target
help:
	@echo "Sophia AI - Available Commands:"
	@echo "================================"
	@echo "install        - Install all dependencies"
	@echo "dev           - Run in development mode"
	@echo "prod          - Run in production mode"
	@echo "test          - Run all tests"
	@echo "clean         - Clean up generated files"
	@echo ""
	@echo "Docker Commands:"
	@echo "docker-build  - Build Docker images"
	@echo "docker-up     - Start Docker containers"
	@echo "docker-down   - Stop Docker containers"
	@echo ""
	@echo "Database Commands:"
	@echo "db-migrate    - Run database migrations"
	@echo "db-reset      - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Code Quality:"
	@echo "lint          - Run code linting"
	@echo "format        - Format code with Black"
	@echo "security-check - Run security checks"
	@echo ""
	@echo "Deployment:"
	@echo "deploy        - Deploy to production (Lambda Labs)"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pnpm install
	@echo "Creating necessary directories..."
	mkdir -p logs data temp
	@echo "Copying environment template..."
	[ ! -f .env ] && cp env.example .env || echo ".env already exists"
	@echo "Installation complete!"

# Development mode
dev:
	@echo "Starting Sophia AI in development mode..."
	@echo "Starting backend..."
	cd backend && python app/main.py &
	@echo "Starting frontend..."
	cd frontend && pnpm dev &
	@echo "Starting MCP server..."
	cd backend/mcp && python sophia_mcp_server.py &
	@echo "Development servers started!"
	@echo "Backend: http://localhost:5000"
	@echo "Frontend: http://localhost:3000"
	@echo "MCP Server: http://localhost:8002"

# Production mode
prod:
	@echo "Starting Sophia AI in production mode..."
	export SOPHIA_ENV=production && \
	cd backend && \
	gunicorn -w 4 -b 0.0.0.0:5000 app.main:app

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --cov=backend --cov-report=html
	@echo "Test results available in htmlcov/index.html"

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf logs/*.log
	@echo "Cleanup complete!"

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "Docker images built!"

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "Containers started!"
	@echo "Waiting for services to be ready..."
	sleep 10
	docker-compose ps

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "Containers stopped!"

# Database commands
db-migrate:
	@echo "Running database migrations..."
	cd backend && python database/schema_migration_system.py migrate
	@echo "Migrations complete!"

db-reset:
	@echo "WARNING: This will delete all data in the database!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	cd backend && python database/schema_migration_system.py reset
	@echo "Database reset complete!"

# Code quality
lint:
	@echo "Running linters..."
	@echo "Python linting..."
	flake8 backend/ --max-line-length=88 --extend-ignore=E203
	mypy backend/ --ignore-missing-imports
	@echo "Frontend linting..."
	cd frontend && pnpm lint
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	black backend/ --line-length 88
	@echo "Code formatted!"

security-check:
	@echo "Running security checks..."
	@echo "Checking Python dependencies..."
	pip-audit
	@echo "Checking for secrets..."
	grep -r "api_key\|password\|secret" backend/ --include="*.py" | grep -v "os.getenv\|Field\|config\|settings" || echo "No hardcoded secrets found"
	@echo "Security check complete!"

# Deployment
deploy:
	@echo "Deploying to Lambda Labs..."
	@echo "Running pre-deployment checks..."
	make test
	make security-check
	@echo "Building production images..."
	docker build -t sophia-ai:latest .
	@echo "Running Pulumi deployment..."
	cd infrastructure && pulumi up --yes
	@echo "Deployment complete!"

# Development helpers
logs:
	@echo "Tailing application logs..."
	tail -f backend/app_server.log backend/mcp/mcp_server.log

shell:
	@echo "Starting Python shell with Sophia context..."
	cd backend && python -c "from app.main import app; from agents.core.orchestrator import SophiaOrchestrator; import IPython; IPython.embed()"

db-shell:
	@echo "Connecting to PostgreSQL..."
        psql $(POSTGRES_URL)

redis-cli:
	@echo "Connecting to Redis..."
        redis-cli -h $(REDIS_HOST) -p $(REDIS_PORT)

# Monitoring
monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"
	open http://localhost:9090 http://localhost:3000

# API Documentation
api-docs:
	@echo "Generating API documentation..."
	cd backend && python -m pdoc --html --output-dir ../docs/api app

# Backup
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
        pg_dump $(POSTGRES_URL) > backups/sophia_db_$$TIMESTAMP.sql && \
	tar -czf backups/sophia_code_$$TIMESTAMP.tar.gz backend/ frontend/ && \
	echo "Backup created: backups/*_$$TIMESTAMP.*"

# Performance testing
perf-test:
	@echo "Running performance tests..."
	locust -f tests/performance/locustfile.py --host=http://localhost:5000

# Create new agent
new-agent:
	@read -p "Enter agent name (e.g., email_analysis): " agent_name; \
	cp backend/agents/specialized/template_agent.py backend/agents/specialized/$$agent_name_agent.py && \
	echo "Created new agent: backend/agents/specialized/$$agent_name_agent.py"

# Update dependencies
update-deps:
	@echo "Updating Python dependencies..."
	pip list --outdated
	@echo "To update all: pip install --upgrade -r requirements.txt"

# Health check
health:
	@echo "Checking system health..."
	@curl -s http://localhost:5000/health | jq . || echo "Backend not responding"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend: OK" || echo "Frontend: Not responding"
        @nc -zv $(POSTGRES_HOST) 5432 2>&1 | grep succeeded > /dev/null && echo "PostgreSQL: OK" || echo "PostgreSQL: Not responding"
        @nc -zv $(REDIS_HOST) 6379 2>&1 | grep succeeded > /dev/null && echo "Redis: OK" || echo "Redis: Not responding"
