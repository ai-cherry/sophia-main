# SOPHIA AI System - Multi-stage Dockerfile
# This Dockerfile builds the SOPHIA AI system with optimized layers

# -----------------------------------------------------------------------------
# Base stage with common dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.5.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt .

# -----------------------------------------------------------------------------
# Development stage
# -----------------------------------------------------------------------------
FROM base AS development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy the entire project
COPY . .

# Expose ports
EXPOSE 8000 8002

# Set default command
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Production build stage
# -----------------------------------------------------------------------------
FROM base AS build

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# -----------------------------------------------------------------------------
# Production stage
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy built artifacts from the build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /app /app

# Create non-root user
RUN useradd -m sophia && \
    chown -R sophia:sophia /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R sophia:sophia /app/logs /app/data

# Switch to non-root user
USER sophia

# Expose ports
EXPOSE 8000 8002

# Set default command
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# -----------------------------------------------------------------------------
# MCP Server stage
# -----------------------------------------------------------------------------
FROM production AS mcp-server

# Set environment variables
ENV MCP_SERVER_PORT=8002

# Expose MCP server port
EXPOSE 8002

# Set default command to run MCP server
CMD ["python", "-m", "backend.mcp.server"]
