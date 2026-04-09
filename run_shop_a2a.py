"""
Shop Agent A2A Server Runner
─────────────────────────────
Runs the Shop Agent as a standalone FastAPI application exposing the A2A protocol.
This allows the Personal AI Orchestrator to consume it via RemoteA2aAgent.
"""

import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path, override=True)

try:
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    import uvicorn
    from shop_agent import shop_root_agent
except ImportError:
    print("Missing ADK dependencies. Please run: pip install -r requirements.txt")
    sys.exit(1)

# Read environment variables
is_cloud_run = "K_SERVICE" in os.environ

if is_cloud_run:
    # SHOP_AGENT_HOST must be set to the full Cloud Run hostname (without https://)
    # e.g. shop-agent-abc123-uc.a.run.app
    # deploy_shop.sh sets this automatically after deployment.
    host = os.environ.get("SHOP_AGENT_HOST")
    if not host:
        raise RuntimeError(
            "SHOP_AGENT_HOST is not set. Re-run deploy_shop.sh — it sets this automatically."
        )
    port = 443
    protocol = "https"
    # Uvicorn itself still binds to the internal PORT for receiving traffic
    bind_port = int(os.environ.get("PORT", 8080))
else:
    host = "localhost"
    port = int(os.environ.get("PORT", 8001))
    protocol = "http"
    bind_port = port

# Wrap the agent into a FastAPI A2A app
a2a_app = to_a2a(shop_root_agent, host=host, port=port, protocol=protocol)

if __name__ == "__main__":
    print(f"🛍️ Starting Shop A2A Server on port {bind_port}...")
    print(f"The agent card will be available at: {protocol}://{host}:{port}/.well-known/agent.json")
    
    # Run the server
    uvicorn.run("run_shop_a2a:a2a_app", host="0.0.0.0", port=bind_port, reload=False)
