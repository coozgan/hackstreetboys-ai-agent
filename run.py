"""
HackstreetBoys AI Local Runner
─────────────────────────────
Runs the ADK web interface for the Personal AI Orchestrator.
Make sure to also run `run_shop_a2a.py` in another terminal so the Shop A2A agent works!
"""

import os
import subprocess
import sys

def main():
    try:
        import mcp
        import google.adk
    except ImportError as e:
        print(f"Missing required dependencies ({e}). Please run: pip install -r requirements.txt")
        sys.exit(1)
        
    print("🚀 Starting HackstreetBoys-AI Local Environment...")
    print("Starting ADK Web UI on http://localhost:8080")
    print("⚠️ WARNING: Ensure run_shop_a2a.py is running in another terminal for Shopping features!")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(project_root, ".env"))

        session_uri = os.environ.get("SESSION_SERVICE_URI", f"sqlite:///{os.path.join(data_dir, 'sessions.db')}")
        
        adk_args = [
            "adk", "web",
            project_root,
            "--session_service_uri", session_uri
        ]
        
        print(f"Using Session Service: {session_uri}\n")
        subprocess.run(adk_args, check=True)
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
