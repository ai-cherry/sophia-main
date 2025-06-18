# SOPHIA AI System - LLM Gateway Setup Guide

## Overview

This guide outlines the setup and configuration of the LLM (Large Language Model) Gateway for the SOPHIA AI System. The LLM Gateway provides a unified interface for accessing various language models, optimizing costs, and ensuring reliability.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Model Routing](#model-routing)
7. [Fallback Mechanisms](#fallback-mechanisms)
8. [Monitoring](#monitoring)
9. [Cost Optimization](#cost-optimization)
10. [Troubleshooting](#troubleshooting)

## Introduction

The LLM Gateway serves as a central access point for all language model interactions in the SOPHIA AI System. It provides:

- Unified API for multiple LLM providers (OpenAI, Anthropic, etc.)
- Intelligent routing based on task requirements
- Fallback mechanisms for reliability
- Cost optimization
- Consistent logging and monitoring
- Caching for improved performance

By centralizing LLM access through the gateway, we ensure consistent behavior, optimize costs, and simplify the integration of new models.

## Architecture

The LLM Gateway follows a layered architecture:

1. **API Layer**: Handles incoming requests and authentication
2. **Routing Layer**: Determines which model to use for a given request
3. **Provider Layer**: Manages connections to specific LLM providers
4. **Caching Layer**: Caches responses for improved performance
5. **Monitoring Layer**: Tracks usage, performance, and costs

```
┌─────────────────────────────────────────────────────┐
│                   LLM Gateway                        │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  API Layer  │  │   Routing   │  │   Caching   │  │
│  │             │  │    Layer    │  │    Layer    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Provider   │  │  Fallback   │  │ Monitoring  │  │
│  │    Layer    │  │ Mechanisms  │  │    Layer    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   OpenAI    │  │  Anthropic  │  │  Other LLM  │
│  Provider   │  │  Provider   │  │  Providers  │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- Redis (for caching)
- Docker (optional, for containerized deployment)

### Installation Steps

1. Install the required packages:

```bash
pip install portkey openrouter redis fastapi uvicorn pydantic
```

2. Clone the repository:

```bash
git clone https://github.com/payready/sophia.git
cd sophia
```

3. Install the project dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The LLM Gateway is configured through the `llm_gateway_config.json` file:

```json
{
  "api": {
    "host": "0.0.0.0",
    "port": 8001,
    "workers": 4,
    "timeout": 120
  },
  "providers": {
    "openai": {
      "api_key": "${OPENAI_API_KEY}",
      "models": {
        "gpt-4": {
          "max_tokens": 8192,
          "temperature": 0.7,
          "timeout": 60
        },
        "gpt-3.5-turbo": {
          "max_tokens": 4096,
          "temperature": 0.7,
          "timeout": 30
        }
      }
    },
    "anthropic": {
      "api_key": "${ANTHROPIC_API_KEY}",
      "models": {
        "claude-3-opus": {
          "max_tokens": 100000,
          "temperature": 0.7,
          "timeout": 120
        },
        "claude-3-sonnet": {
          "max_tokens": 100000,
          "temperature": 0.7,
          "timeout": 60
        }
      }
    },
    "openrouter": {
      "api_key": "${OPENROUTER_API_KEY}",
      "models": {
        "anthropic/claude-3-opus": {
          "max_tokens": 100000,
          "temperature": 0.7,
          "timeout": 120
        },
        "google/gemini-pro": {
          "max_tokens": 8192,
          "temperature": 0.7,
          "timeout": 60
        }
      }
    }
  },
  "routing": {
    "default_provider": "openai",
    "default_model": "gpt-4",
    "routing_rules": [
      {
        "task_type": "sales_coaching",
        "provider": "anthropic",
        "model": "claude-3-opus"
      },
      {
        "task_type": "client_health",
        "provider": "openai",
        "model": "gpt-4"
      },
      {
        "task_type": "data_analysis",
        "provider": "anthropic",
        "model": "claude-3-sonnet"
      }
    ]
  },
  "caching": {
    "enabled": true,
    "ttl": 3600,
    "redis_url": "redis://redis:6379/0"
  },
  "fallback": {
    "enabled": true,
    "max_retries": 3,
    "retry_delay": 1,
    "fallback_map": {
      "openai/gpt-4": ["anthropic/claude-3-sonnet", "openai/gpt-3.5-turbo"],
      "anthropic/claude-3-opus": ["openai/gpt-4", "anthropic/claude-3-sonnet"]
    }
  },
  "monitoring": {
    "log_level": "INFO",
    "metrics_enabled": true,
    "prometheus_port": 8002
  }
}
```

### Environment Variables

The following environment variables should be set:

```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Usage

### Starting the Gateway

To start the LLM Gateway:

```bash
python -m backend.llm_gateway.server
```

Or using Docker:

```bash
docker-compose up llm-gateway
```

### API Endpoints

The LLM Gateway exposes the following endpoints:

#### 1. Chat Completion

```
POST /v1/chat/completions
```

Request body:

```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "task_type": "general"
}
```

Response:

```json
{
  "id": "chatcmpl-123456789",
  "object": "chat.completion",
  "created": 1677858242,
  "model": "gpt-4",
  "provider": "openai",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "I'm doing well, thank you for asking! How can I assist you today?"
      },
      "finish_reason": "stop",
      "index": 0
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 15,
    "total_tokens": 40
  }
}
```

#### 2. Embeddings

```
POST /v1/embeddings
```

Request body:

```json
{
  "model": "text-embedding-ada-002",
  "input": "The quick brown fox jumps over the lazy dog"
}
```

Response:

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.1, 0.2, 0.3, ...],
      "index": 0
    }
  ],
  "model": "text-embedding-ada-002",
  "provider": "openai",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}
```

#### 3. Health Check

```
GET /health
```

Response:

```json
{
  "status": "healthy",
  "providers": {
    "openai": "available",
    "anthropic": "available",
    "openrouter": "available"
  },
  "version": "1.0.0"
}
```

## Model Routing

The LLM Gateway routes requests to the appropriate model based on:

1. **Explicit Model Selection**: If a specific model is requested, it will be used if available
2. **Task Type**: Different task types are routed to different models based on configuration
3. **Default Routing**: If no specific routing is defined, the default model is used

### Task Types

The following task types are defined:

- `general`: General-purpose conversations
- `sales_coaching`: Sales coaching and feedback
- `client_health`: Client health analysis
- `data_analysis`: Data analysis and insights
- `research`: Research and information gathering
- `content_generation`: Content creation and writing
- `summarization`: Summarizing long texts

### Custom Routing

To add custom routing rules, update the `routing_rules` section in the configuration:

```json
"routing_rules": [
  {
    "task_type": "custom_task",
    "provider": "anthropic",
    "model": "claude-3-opus"
  }
]
```

## Fallback Mechanisms

The LLM Gateway includes fallback mechanisms to ensure reliability:

1. **Retry Logic**: Failed requests are automatically retried
2. **Model Fallback**: If a model is unavailable, requests are routed to fallback models
3. **Provider Fallback**: If a provider is down, requests are routed to alternative providers

### Fallback Configuration

Fallback behavior is configured in the `fallback` section:

```json
"fallback": {
  "enabled": true,
  "max_retries": 3,
  "retry_delay": 1,
  "fallback_map": {
    "openai/gpt-4": ["anthropic/claude-3-sonnet", "openai/gpt-3.5-turbo"],
    "anthropic/claude-3-opus": ["openai/gpt-4", "anthropic/claude-3-sonnet"]
  }
}
```

## Monitoring

The LLM Gateway includes comprehensive monitoring:

1. **Logging**: Structured logs for all requests and responses
2. **Metrics**: Prometheus metrics for monitoring performance and usage
3. **Alerts**: Configurable alerts for error rates and latency

### Metrics

The following metrics are available:

- `llm_gateway_requests_total`: Total number of requests
- `llm_gateway_request_duration_seconds`: Request duration
- `llm_gateway_tokens_total`: Total tokens used
- `llm_gateway_errors_total`: Total number of errors
- `llm_gateway_cache_hits_total`: Total cache hits
- `llm_gateway_cache_misses_total`: Total cache misses

### Grafana Dashboard

A Grafana dashboard is available for visualizing metrics:

```
http://localhost:3000/d/llm-gateway/llm-gateway-dashboard
```

## Cost Optimization

The LLM Gateway includes several cost optimization features:

1. **Intelligent Routing**: Route requests to the most cost-effective model for the task
2. **Caching**: Cache responses to avoid redundant API calls
3. **Token Optimization**: Optimize prompts to reduce token usage
4. **Usage Tracking**: Track usage by agent, task, and user

### Cost Tracking

Cost tracking is available through the monitoring dashboard:

```
http://localhost:3000/d/llm-gateway-cost/llm-gateway-cost-dashboard
```

## Troubleshooting

### Common Issues

#### 1. Connection Errors

If you encounter connection errors:

1. Check that the API keys are correctly set
2. Verify network connectivity to the LLM providers
3. Check if the provider is experiencing downtime

#### 2. Timeout Errors

If requests are timing out:

1. Increase the timeout in the configuration
2. Reduce the complexity of the prompt
3. Check if the provider is experiencing high load

#### 3. Rate Limit Errors

If you hit rate limits:

1. Implement request throttling
2. Use multiple API keys
3. Contact the provider to increase limits

#### 4. High Costs

If costs are higher than expected:

1. Review the routing configuration
2. Implement caching
3. Optimize prompts to reduce token usage
4. Use cheaper models for appropriate tasks

### Logs

Check the logs for detailed error information:

```bash
docker-compose logs llm-gateway
```

### Support

For additional support, contact the SOPHIA AI team at sophia-support@payready.com.
