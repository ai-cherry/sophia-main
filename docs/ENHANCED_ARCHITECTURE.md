# Enhanced Architecture

This document outlines the high level architecture after integrating workflow orchestration, advanced LLM routing and browser automation.

## Components

- **Workflow Orchestrator** powered by n8n for automation of common tasks.
- **Enhanced LLM Gateway** using Portkey with OpenRouter fallback for intelligent model selection.
- **Browser Automation** via Apify actors and Playwright scripts.
- **Natural Language Interface** allowing users to trigger workflows through freeform text.
- **Knowledge Manager** providing hybrid vector and keyword search across data sources.

## Deployment

The GitHub workflows now populate additional environment variables including `N8N_BASE_URL`, `N8N_API_KEY` and `APIFY_API_TOKEN`.
