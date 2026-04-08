# Dockerfile.mcp — MCP Server (SSE Transport)
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only copy the MCP server code
COPY mcp_server/ ./mcp_server/

RUN mkdir -p /app/data

EXPOSE 8080

# Run MCP SSE server via uvicorn (imports sse_app from server.py)
CMD ["sh", "-c", "uvicorn mcp_server.server:sse_app --host 0.0.0.0 --port ${PORT}"]
