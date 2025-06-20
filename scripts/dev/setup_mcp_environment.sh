#!/bin/bash
# MCP Environment Setup Script
# Sets up all required environment variables for MCP servers

echo "🔧 Setting up MCP Environment Variables..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp config/environment/env.template .env
fi

# Required environment variables for MCP servers
export PULUMI_ORG="${PULUMI_ORG:-sophia-ai}"
export ESTUARY_API_KEY="${ESTUARY_API_KEY:-dummy_key_for_local_dev}"
export AGNO_API_KEY="${AGNO_API_KEY:-dummy_key_for_local_dev}"

# Linear API key (if not set, use dummy for local dev)
if [ -z "$LINEAR_API_KEY" ]; then
    echo "⚠️  LINEAR_API_KEY not set, using dummy key for local development"
    export LINEAR_API_KEY="dummy_linear_key_for_local_dev"
fi

# Validate critical environment variables
echo "🔍 Validating environment variables..."

critical_vars=("PINECONE_API_KEY" "OPENAI_API_KEY" "ANTHROPIC_API_KEY")
missing_vars=()

for var in "${critical_vars[@]}"; do
    eval "value=\$$var"
    if [ -z "$value" ]; then
        missing_vars+=("$var")
    else
        echo "  ✅ $var: Set (length: ${#value})"
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing critical environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  • $var"
    done
    echo ""
    echo "Please set these variables in your environment or .env file:"
    echo "export PINECONE_API_KEY=your_pinecone_key"
    echo "export OPENAI_API_KEY=your_openai_key"
    echo "export ANTHROPIC_API_KEY=your_anthropic_key"
    exit 1
fi

# Non-critical variables with defaults
echo "🔧 Setting non-critical variables with defaults..."
export PULUMI_ORG="${PULUMI_ORG:-sophia-ai}"
export ESTUARY_API_KEY="${ESTUARY_API_KEY:-dummy_key}"
export AGNO_API_KEY="${AGNO_API_KEY:-dummy_key}"
export LINEAR_API_KEY="${LINEAR_API_KEY:-dummy_key}"
export RETOOL_API_TOKEN="${RETOOL_API_TOKEN:-dummy_key}"

echo "✅ Environment setup complete!"
echo ""
echo "📋 Current environment status:"
echo "  PULUMI_ORG: $PULUMI_ORG"
echo "  PINECONE_API_KEY: Set (${#PINECONE_API_KEY} chars)"
echo "  OPENAI_API_KEY: Set (${#OPENAI_API_KEY} chars)"
echo "  ANTHROPIC_API_KEY: Set (${#ANTHROPIC_API_KEY} chars)"
echo "  LINEAR_API_KEY: Set (${#LINEAR_API_KEY} chars)"
echo ""
echo "🚀 Ready to start MCP servers!"
