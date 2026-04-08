"""
Terminal client for HackstreetBoys-AI on Vertex AI Agent Engine.
Features:
  - Short-term memory: Session ID persisted to .session.json (survives restarts)
  - Long-term memory: Calls add_session_to_memory on quit, search_memory on start
Run: python query.py
"""
import os
import sys
import json
import pathlib

from dotenv import load_dotenv
load_dotenv()

try:
    import vertexai
    from vertexai.preview import reasoning_engines
    from google.cloud.aiplatform_v1beta1.services.reasoning_engine_execution_service import (
        ReasoningEngineExecutionServiceClient,
    )
    from google.protobuf import struct_pb2
except ImportError:
    print("Missing dependencies. Run: pip install google-cloud-aiplatform python-dotenv")
    sys.exit(1)

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or exit("Error: GOOGLE_CLOUD_PROJECT not set. Copy .env.example to .env and fill in your values.")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
USER_ID = "joshua"

# Session persistence file
SESSION_FILE = pathlib.Path(__file__).parent / ".session.json"


def _save_session(session_id: str, engine_name: str):
    """Save session info to disk for short-term memory persistence."""
    SESSION_FILE.write_text(json.dumps({
        "session_id": session_id,
        "engine_name": engine_name,
        "user_id": USER_ID,
    }))


def _load_session() -> dict | None:
    """Load a previously saved session."""
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def _rpc(exec_client, engine_resource: str, method: str, params: dict):
    """Make an RPC call to the deployed reasoning engine."""
    input_struct = struct_pb2.Struct()
    input_struct.update(params)
    resp = exec_client.query_reasoning_engine(
        request={"name": engine_resource, "class_method": method, "input": input_struct}
    )
    return dict(resp.output)


def _create_session(exec_client, engine_resource: str) -> str:
    data = _rpc(exec_client, engine_resource, "create_session", {"user_id": USER_ID})
    return data.get("id", "unknown")


def _verify_session(exec_client, engine_resource: str, session_id: str) -> bool:
    try:
        _rpc(exec_client, engine_resource, "get_session", {
            "user_id": USER_ID, "session_id": session_id
        })
        return True
    except Exception:
        return False


def _save_to_long_term_memory(exec_client, engine_resource: str, session_id: str):
    """Save the current session to long-term memory via add_session_to_memory."""
    try:
        print("💾 Saving session to long-term memory...", end="", flush=True)
        # First get the full session object
        session_data = _rpc(exec_client, engine_resource, "get_session", {
            "user_id": USER_ID, "session_id": session_id
        })
        # Call add_session_to_memory with the session dict
        _rpc(exec_client, engine_resource, "add_session_to_memory", {
            "session": session_data
        })
        print(" ✅ Done!")
    except Exception as e:
        print(f" ⚠️ Could not save ({e})")


def _recall_long_term_memory(exec_client, engine_resource: str) -> str | None:
    """Search long-term memory for anything about this user."""
    try:
        result = _rpc(exec_client, engine_resource, "search_memory", {
            "user_id": USER_ID,
            "query": "personal information preferences name facts about the user"
        })
        memories = result.get("memories", [])
        if memories:
            lines = []
            for mem in memories:
                content = mem.get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    text = part.get("text", "")
                    if text:
                        lines.append(text[:200])  # Truncate long entries
            if lines:
                return "\n".join(lines[:10])  # Max 10 memory entries
    except Exception as e:
        # Memory search may not be available - that's OK
        pass
    return None


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # --- Find the deployed engine ---
    print("Fetching deployed Reasoning Engines...")
    engines = reasoning_engines.ReasoningEngine.list()
    if not engines:
        print("❌ No Reasoning Engines found. Is the deploy finished?")
        sys.exit(1)

    engine_resource = engines[0].resource_name
    print(f"Using engine: {engines[0].display_name}")

    # --- Build the low-level streaming client ---
    exec_client = ReasoningEngineExecutionServiceClient(
        client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
    )

    # --- Session management (short-term memory) ---
    saved = _load_session()
    resumed = False
    if saved and saved.get("engine_name") == engine_resource:
        session_id = saved["session_id"]
        if _verify_session(exec_client, engine_resource, session_id):
            print(f"📂 Resumed session: {session_id[:16]}...")
            resumed = True
        else:
            print("Previous session expired. Creating new one...")
            session_id = _create_session(exec_client, engine_resource)
    else:
        session_id = _create_session(exec_client, engine_resource)

    _save_session(session_id, engine_resource)

    # --- Long-term memory recall ---
    if not resumed:
        memories = _recall_long_term_memory(exec_client, engine_resource)
        if memories:
            print(f"\n🧠 Recalled from long-term memory:\n{memories}\n")

    print("=" * 60)
    print("🤖 HackstreetBoys-AI (Cloud Deployment)")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Session: {session_id[:16]}...")
    print("=" * 60)
    print("Commands: 'quit' to exit, 'new' for fresh session\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            _save_to_long_term_memory(exec_client, engine_resource, session_id)
            print("Goodbye! 👋")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            _save_to_long_term_memory(exec_client, engine_resource, session_id)
            print("Goodbye! 👋")
            break
        if user_input.lower() == "new":
            _save_to_long_term_memory(exec_client, engine_resource, session_id)
            session_id = _create_session(exec_client, engine_resource)
            _save_session(session_id, engine_resource)
            print(f"🔄 New session created: {session_id[:16]}...\n")
            continue

        try:
            query_input = struct_pb2.Struct()
            query_input.update({
                "message": user_input,
                "user_id": USER_ID,
                "session_id": session_id,
            })

            responses = exec_client.stream_query_reasoning_engine(
                request={
                    "name": engine_resource,
                    "class_method": "stream_query",
                    "input": query_input,
                }
            )

            print("\nAI: ", end="", flush=True)
            for chunk in responses:
                try:
                    event = json.loads(chunk.data)
                    content = event.get("content", {})
                    parts = content.get("parts", [])
                    for part in parts:
                        text = part.get("text", "")
                        if text:
                            print(text, end="", flush=True)
                except (json.JSONDecodeError, KeyError):
                    pass
            print("\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
