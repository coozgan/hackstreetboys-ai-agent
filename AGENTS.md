# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

HackstreetBoys AI is a multi-agent Personal AI System built with Google ADK and MCP. It runs as **three independent microservices**: a Personal AI Orchestrator (Vertex AI Agent Engine), a Shop Agent (Cloud Run via A2A), and an MCP Server (Cloud Run via SSE).

Package manager: `uv`. All commands should be prefixed with `uv run`.

## Local Development

Three terminals are required to run the full system locally:

```bash
# Terminal 1 — MCP Server (SSE on port 3000)
uv run python mcp_server/server.py --sse 3000

# Terminal 2 — Shop Agent A2A server (port 8001)
uv run python run_shop_a2a.py

# Terminal 3 — ADK Web UI (http://localhost:8080)
uv run python run.py
```

The ADK web UI requires both the MCP server and Shop A2A server to be running for all features.

To interact with a **deployed** cloud instance from the terminal:
```bash
uv run python query.py
```

## Environment Variables

Create a `.env` file at the project root. Key variables:

| Variable | Purpose |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | Region (e.g. `us-central1`) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set `true` to use Vertex AI backend |
| `MCP_SERVER_URL` | MCP server URL (defaults to deployed Cloud Run URL) |
| `SHOP_AGENT_URL` | Shop Agent URL (defaults to deployed Cloud Run URL) |
| `AGENT_MODEL` | Gemini model string (defaults to `gemini-2.5-flash`) |
| `HACKSTREETBOYS_DB_PATH` | Override SQLite DB path (defaults to `data/hackstreetboys.db`) |

## Deployment

Each service uses a different Dockerfile. The deploy scripts handle the Dockerfile swap automatically:

```bash
# Deploy MCP Server to Cloud Run
bash deploy_mcp.sh

# Deploy Shop Agent to Cloud Run
bash deploy_shop.sh

# Deploy Personal AI Orchestrator to Vertex AI Agent Engine
uv run adk deploy agent_engine hackstreetboys_ai \
  --project <YOUR_PROJECT_ID> \
  --region us-central1 \
  --display_name "HackstreetBoys Personal Assistant"
```

After deploying MCP Server and Shop Agent, update `MCP_SERVER_URL` and `SHOP_AGENT_URL` in `hackstreetboys_ai/agent.py` (or set them via env vars) before deploying the orchestrator.

**Important:** `Dockerfile` at the root is always the **MCP Server** dockerfile. `Dockerfile.shop` and `Dockerfile.mcp` are the alternate service dockerfiles. The deploy scripts swap them in place.

## Architecture

### Service Topology

```
User
 └── Personal AI Orchestrator (Vertex AI Agent Engine)
       ├── Domain sub-agents: health, finance, career, social
       │     └── All connect to MCP Server via SSE (tool_filter per agent)
       ├── Macro workflows: daily_briefing (Parallel), weekly_plan (Sequential), goal_review_loop (Loop)
       └── shop_agent (RemoteA2aAgent → Shop Agent Cloud Run)
                         └── Connects to MCP Server via SSE
```

### hackstreetboys_ai/ — Personal AI Orchestrator

- `agent.py`: Defines `root_agent` (the ADK `LlmAgent` entry point). All sub-agents and macro workflows are constructed here. Each domain agent receives a `McpToolset` filtered to only the tools it needs.
- `prompt.py`: All system prompt strings for every agent in the orchestrator.
- `agent_engine_app.py`: Wraps `root_agent` in an `AdkApp` with `VertexAiMemoryBankService` for long-term cross-session memory. This is the module used by Agent Engine.

### shop_agent/ — External A2A Shop Service

- `agent.py`: Defines `shop_root_agent`. Implements a checkout pipeline as a nested `SequentialAgent` → `LoopAgent` → `ParallelAgent` pattern (cart validation → stock+payment verification → order finalization).
- `prompt.py`: Prompts for all shop sub-agents.
- Exposed via `run_shop_a2a.py` which wraps the agent with `google.adk.a2a.utils.agent_to_a2a.to_a2a`.

### mcp_server/ — Action Engine (FastMCP)

- `server.py`: Defines 45+ tools via `@mcp.tool()` decorators, organized in sections: Shopping, Health, Finance, Career, Social, and a cross-domain `get_daily_briefing_data` tool. Exposes `sse_app` for uvicorn import.
- `database.py`: SQLite-backed persistence layer. Database auto-initializes and seeds product/contact/budget data on first run at `data/hackstreetboys.db`. All CRUD operations are synchronous.

### ADK Agent Patterns Used

- `LlmAgent`: All leaf agents; receives scoped `McpToolset` via `tool_filter`.
- `ParallelAgent`: `daily_briefing` (4 domain briefings run concurrently).
- `SequentialAgent`: `weekly_plan` (career → health → finance → social in order), `checkout_pipeline`.
- `LoopAgent` + `exit_loop`: `goal_review_loop` (assess → advise, max 3 iterations), `cart_validation_loop`.
- `RemoteA2aAgent`: `shop_agent` in the orchestrator — fetches agent card from `SHOP_AGENT_URL/.well-known/agent.json`.

### MCP Connection Pattern

Every agent that needs tools calls `_mcp_toolset(tool_filter)` — a local helper in each `agent.py` that returns a `McpToolset` with `SseConnectionParams` pointing to `MCP_SERVER_URL/sse`. This means each agent creates its own SSE connection; they are not shared.

### Data Flow for Shopping

The shop checkout flow exercises all three agent composition patterns:
1. `cart_validation_loop` (Loop): `cart_validator` writes `output_key="cart_validation_result"`, `cart_fixer` reads it and calls `exit_loop`.
2. `parallel_verification` (Parallel): `inventory_checker` and `payment_validator` run concurrently, each writing to their own `output_key`.
3. `order_finalizer` (LlmAgent): Reads both output keys and calls MCP tools `create_order`, `process_payment`, `update_order_status`.
