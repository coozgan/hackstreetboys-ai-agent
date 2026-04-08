import os
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

from . import prompt

from google.adk.models.google_llm import Gemini
from google.genai import types

MODEL_STR = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")
MODEL = Gemini(
    model=MODEL_STR,
    retry_options=types.HttpRetryOptions(initial_delay=3, max_delay=15, attempts=5)
)

# Remote MCP Server URL (deployed on Cloud Run)
# Falls back to local SSE for development
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:3000")

def _mcp_toolset(tool_filter: list[str]) -> McpToolset:
    return McpToolset(
        connection_params=SseConnectionParams(
            url=f"{MCP_SERVER_URL}/sse",
            timeout=10,
        ),
        tool_filter=tool_filter,
    )

# --- Basic Domain Agents ---

catalog_agent = LlmAgent(
    model=MODEL,
    name="catalog_agent",
    instruction=prompt.CATALOG_PROMPT,
    tools=[_mcp_toolset(["browse_products", "search_products", "get_categories"])],
)

cart_agent = LlmAgent(
    model=MODEL,
    name="cart_agent",
    instruction=prompt.CART_PROMPT,
    tools=[_mcp_toolset(["view_cart", "add_to_cart", "remove_from_cart", "update_cart_quantity", "clear_cart"])],
)

# --- Checkout Pipeline (Sequential -> Loop -> Parallel -> Single) ---

from google.adk.tools import exit_loop

cart_validator = LlmAgent(
    model=MODEL,
    name="cart_validator",
    instruction=prompt.CART_VALIDATOR_PROMPT,
    tools=[_mcp_toolset(["view_cart"])],
    output_key="cart_validation_result"
)

cart_fixer = LlmAgent(
    model=MODEL,
    name="cart_fixer",
    instruction=prompt.CART_FIXER_PROMPT,
    tools=[exit_loop]
)

cart_validation_loop = LoopAgent(
    name="cart_validation_loop",
    description="Validates the cart logic.",
    max_iterations=3,
    sub_agents=[cart_validator, cart_fixer]
)

inventory_checker = LlmAgent(
    model=MODEL,
    name="inventory_checker",
    instruction=prompt.INVENTORY_PROMPT,
    tools=[_mcp_toolset(["check_stock", "reserve_stock"])],
    output_key="inventory_result"
)

payment_validator = LlmAgent(
    model=MODEL,
    name="payment_validator",
    instruction=prompt.PAYMENT_PROMPT,
    output_key="payment_result"
)

parallel_verification = ParallelAgent(
    name="parallel_verification",
    description="Simultaneously verifies stock and validates payment.",
    sub_agents=[inventory_checker, payment_validator]
)

order_finalizer = LlmAgent(
    model=MODEL,
    name="order_finalizer",
    instruction=prompt.ORDER_FINALIZER_PROMPT,
    tools=[_mcp_toolset(["create_order", "process_payment", "update_order_status"])]
)

checkout_pipeline = SequentialAgent(
    name="checkout_pipeline",
    description="Handles the full checkout process: Cart Validation -> Stock & Payment Verification -> Order Finalization.",
    sub_agents=[
        cart_validation_loop,
        parallel_verification,
        order_finalizer
    ]
)

# --- Shop Root Orchestrator ---

shop_root_agent = LlmAgent(
    model=MODEL,
    name="shop_orchestrator",
    instruction=prompt.SHOP_ROOT_PROMPT,
    sub_agents=[
        catalog_agent,
        cart_agent,
        checkout_pipeline
    ]
)

root_agent = shop_root_agent
