# HackstreetBoys AI

A 13-agent personal life management system built with Google ADK (Agent Development Kit) and Model Context Protocol (MCP). One AI assistant that manages your Health, Finance, Career, Social life, and Shopping — with agents that collaborate, not just respond.

---

## Architecture

![Architecture Diagram](docs/architecture.png)

Three independently deployed GCP services

---

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) package manager
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) — authenticated and with a project that has billing enabled
- Vertex AI API enabled on your project

```bash
gcloud auth login
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com run.googleapis.com
```

---

## Setup

```bash
git clone <repo-url>
cd cohort1-hackathon-2

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and set GOOGLE_CLOUD_PROJECT to your GCP project ID
```

---

## Local Development

Run all three services in separate terminals:

```bash
# Terminal 1 — MCP Server (tools engine)
uv run python mcp_server/server.py --sse 3000

# Terminal 2 — Shop Agent (A2A service on port 8001)
uv run python run_shop_a2a.py

# Terminal 3 — Personal AI (ADK Web UI at http://localhost:8080)
uv run python run.py
```

> By default, agents connect to `http://localhost:3000` (MCP) and `http://localhost:8001` (Shop Agent). No `.env` changes needed for local dev.

---

## Cloud Deployment

Deploy in this order — each service depends on the one before it.

### 1. Deploy MCP Server → Cloud Run

```bash
GOOGLE_CLOUD_PROJECT=your-project-id ./deploy_mcp.sh
```

Note the deployed URL (e.g. `https://mcp-server-XXXX.us-central1.run.app`).

### 2. Deploy Shop Agent → Cloud Run

```bash
GOOGLE_CLOUD_PROJECT=your-project-id \
MCP_SERVER_URL=https://mcp-server-XXXX.us-central1.run.app \
./deploy_shop.sh
```

Note the deployed URL (e.g. `https://shop-agent-XXXX.us-central1.run.app`).

### 3. Update `.env` with deployed URLs

```bash
MCP_SERVER_URL=https://mcp-server-XXXX.us-central1.run.app
SHOP_AGENT_URL=https://shop-agent-XXXX.us-central1.run.app
```

### 4. Deploy Personal AI → Vertex AI Agent Engine

```bash
uv run adk deploy agent_engine \
  --project your-project-id \
  --region us-central1 \
  --display_name "HackstreetBoys Personal Assistant" \
  --requirements_file requirements.txt \
  --env_file .env \
  hackstreetboys_ai
```

Note the engine resource name from the output and add to `.env`:
```bash
SESSION_SERVICE_URI=agentengine://projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID
```

### 5. Query the deployed agent

```bash
uv run python query.py
```

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | Yes | Your GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | No | Region (default: `us-central1`) |
| `MCP_SERVER_URL` | For cloud | Cloud Run URL of the MCP server |
| `SHOP_AGENT_URL` | For cloud | Cloud Run URL of the shop agent |
| `SESSION_SERVICE_URI` | For cloud | Agent Engine URI for session persistence |
| `AGENT_MODEL` | No | LLM model (default: `gemini-2.5-flash`) |

---

## Key Files

| File | Purpose |
|---|---|
| `hackstreetboys_ai/agent.py` | All 13 agent definitions and orchestration |
| `hackstreetboys_ai/prompt.py` | System prompts for every agent |
| `shop_agent/agent.py` | Shop sub-system agents and checkout pipeline |
| `mcp_server/server.py` | FastMCP tool definitions (45+ tools) |
| `mcp_server/database.py` | SQLite schema and CRUD operations |
| `run.py` | Local ADK Web UI launcher |
| `run_shop_a2a.py` | Wraps shop agent as A2A FastAPI service |
| `query.py` | Terminal client for the deployed Agent Engine |
