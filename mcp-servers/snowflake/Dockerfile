FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY snowflake_mcp_server.py .
COPY mcp_base.py .

# Set environment variables
ENV MCP_SERVER_NAME=snowflake-mcp
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "snowflake_mcp_server.py"] 