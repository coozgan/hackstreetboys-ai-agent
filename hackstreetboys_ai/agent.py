import os
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

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

# Patch McpToolset to be picklable by excluding TextIOWrapper (_errlog)
def _mcp_toolset_getstate(self):
    state = dict(self.__dict__)
    state.pop('_errlog', None)
    return state
McpToolset.__getstate__ = _mcp_toolset_getstate

def _mcp_toolset(tool_filter: list[str]) -> McpToolset:
    return McpToolset(
        connection_params=SseConnectionParams(
            url=f"{MCP_SERVER_URL}/sse",
            timeout=10,
        ),
        tool_filter=tool_filter,
    )

# --- Base Domain Agents ---

health_agent = LlmAgent(
    model=MODEL,
    name="health_agent",
    instruction=prompt.HEALTH_PROMPT,
    tools=[_mcp_toolset(["log_health_entry", "get_health_logs", "set_health_goal", "get_health_goals", "update_health_goal_progress"])],
)

finance_agent = LlmAgent(
    model=MODEL,
    name="finance_agent",
    instruction=prompt.FINANCE_PROMPT,
    tools=[_mcp_toolset(["add_transaction", "list_transactions", "set_budget", "get_budgets"])],
)

career_agent = LlmAgent(
    model=MODEL,
    name="career_agent",
    instruction=prompt.CAREER_PROMPT,
    tools=[_mcp_toolset(["create_career_task", "list_career_tasks", "update_career_task"])],
)

social_agent = LlmAgent(
    model=MODEL,
    name="social_agent",
    instruction=prompt.SOCIAL_PROMPT,
    tools=[_mcp_toolset(["add_contact", "list_contacts", "log_interaction", "create_social_event", "list_social_events"])],
)

# --- Remote Shop Agent (A2A) ---
# Reads URL from env for cloud deployment, falls back to localhost for local dev
SHOP_AGENT_URL = os.environ.get("SHOP_AGENT_URL", "http://localhost:8001")

shop_agent = RemoteA2aAgent(
    name="shop_agent",
    description="External store agent. Routes shopping, cart, and checkout queries to the boutique.",
    agent_card=f"{SHOP_AGENT_URL}/.well-known/agent.json"
)

# --- Macro Workflows ---

# 1. Daily Briefing (Parallel)
health_briefing_agent = LlmAgent(model=MODEL, name="health_briefing", instruction=prompt.BRIEFING_HEALTH_PROMPT, tools=[_mcp_toolset(["get_health_logs"])], output_key="health_briefing")
finance_briefing_agent = LlmAgent(model=MODEL, name="finance_briefing", instruction=prompt.BRIEFING_FINANCE_PROMPT, tools=[_mcp_toolset(["get_budgets"])], output_key="finance_briefing")
career_briefing_agent = LlmAgent(model=MODEL, name="career_briefing", instruction=prompt.BRIEFING_CAREER_PROMPT, tools=[_mcp_toolset(["list_career_tasks"])], output_key="career_briefing")
social_briefing_agent = LlmAgent(model=MODEL, name="social_briefing", instruction=prompt.BRIEFING_SOCIAL_PROMPT, tools=[_mcp_toolset(["list_social_events"])], output_key="social_briefing")

daily_briefing = ParallelAgent(
    name="daily_briefing",
    description="Gets a full snapshot of today across all domains simultaneously.",
    sub_agents=[health_briefing_agent, finance_briefing_agent, career_briefing_agent, social_briefing_agent]
)

# 2. Goal Review (Loop)
from google.adk.tools import exit_loop

goal_assessor = LlmAgent(
    model=MODEL, 
    name="goal_assessor", 
    instruction=prompt.GOAL_ASSESSOR_PROMPT, 
    tools=[_mcp_toolset(["get_health_goals", "get_budgets", "list_career_tasks"])],
    output_key="assessment_report"
)

goal_advisor = LlmAgent(
    model=MODEL,
    name="goal_advisor",
    instruction=prompt.GOAL_ADVISOR_PROMPT,
    tools=[_mcp_toolset(["set_health_goal", "set_budget", "update_career_task"]), exit_loop]
)

goal_review_loop = LoopAgent(
    name="goal_review_loop",
    description="Iteratively reviews goals and suggests adjustments.",
    max_iterations=3,
    sub_agents=[goal_assessor, goal_advisor]
)

# 3. Weekly Planning (Sequential)
weekly_plan = SequentialAgent(
    name="weekly_plan",
    description="Plans the week ahead by sequentially checking Career, Health, Finance, and Social.",
    sub_agents=[
        LlmAgent(model=MODEL, name="weekly_career_agent", instruction=prompt.CAREER_PROMPT, tools=[_mcp_toolset(["create_career_task", "list_career_tasks", "update_career_task"])]),
        LlmAgent(model=MODEL, name="weekly_health_agent", instruction=prompt.HEALTH_PROMPT, tools=[_mcp_toolset(["log_health_entry", "get_health_logs", "set_health_goal", "get_health_goals", "update_health_goal_progress"])]),
        LlmAgent(model=MODEL, name="weekly_finance_agent", instruction=prompt.FINANCE_PROMPT, tools=[_mcp_toolset(["add_transaction", "list_transactions", "set_budget", "get_budgets"])]),
        LlmAgent(model=MODEL, name="weekly_social_agent", instruction=prompt.SOCIAL_PROMPT, tools=[_mcp_toolset(["add_contact", "list_contacts", "log_interaction", "create_social_event", "list_social_events"])]),
    ]
)

# --- Root Orchestrator ---

root_agent = LlmAgent(
    model=MODEL,
    name="hackstreetboys_ai",
    instruction=prompt.ROOT_PROMPT,
    sub_agents=[
        health_agent,
        finance_agent,
        career_agent,
        social_agent,
        shop_agent,
        daily_briefing,
        goal_review_loop,
        weekly_plan
    ]
)
