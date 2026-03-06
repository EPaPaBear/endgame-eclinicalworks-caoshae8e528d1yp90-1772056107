#!/usr/bin/env python3
"""
Publish Integration Tool

Uploads integration code and schema to backend.
- Code is read from integrations/{name}.py (run function only)
- Schema is read from integrations/{name}.schema.json

Auth is NOT included - it's managed separately by the platform's auth system.
"""

import os
import sys
import json
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
AGENT_SECRET = os.environ.get("AGENT_CALLBACK_SECRET", "")


def get_session_id() -> str:
    """Get session_id from environment variable (set by backend)."""
    session_id = os.environ.get("SESSION_ID")
    if session_id:
        return session_id
    
    # Fallback: try git branch (legacy)
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = result.stdout.strip()
        # Support both agent/builder/{session_id} and endgame/{session_id}
        if branch.startswith("agent/builder/"):
            return branch.replace("agent/builder/", "")
        if branch.startswith("endgame/"):
            return branch.replace("endgame/", "")
    except Exception as e:
        print(f"Warning: Could not get branch name: {e}")
    return None


def load_schema(integration_name: str) -> dict:
    """Load input schema from integrations/{name}.schema.json"""
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "integrations", f"{integration_name}.schema.json"
    )
    
    if not os.path.exists(schema_path):
        print(f"ERROR: Schema file not found: {schema_path}")
        print(f"Create integrations/{integration_name}.schema.json with your input schema:")
        print('  {')
        print('      "type": "object",')
        print('      "properties": {')
        print('          "param_name": {"type": "string", "description": "Description here"}')
        print('      }')
        print('  }')
        sys.exit(1)
    
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in schema file: {e}")
        sys.exit(1)
    
    if not isinstance(schema, dict) or 'properties' not in schema:
        print("ERROR: Schema must have 'properties' defined")
        sys.exit(1)
    
    return schema


def validate_code(code: str):
    """Validate that the code has a run() function."""
    # Use single namespace to avoid import visibility issues
    namespace = {'__builtins__': __builtins__}
    
    try:
        exec(code, namespace)
    except Exception as e:
        print(f"ERROR: Failed to execute integration code: {e}")
        sys.exit(1)
    
    if 'run' not in namespace or not callable(namespace['run']):
        print("ERROR: Integration missing required run(headers, user_input) function")
        sys.exit(1)


def publish_integration(integration_name: str):
    """Publish integration to backend."""
    session_id = get_session_id()
    if not session_id:
        print("ERROR: Could not determine session_id")
        print("SESSION_ID environment variable should be set by the backend")
        sys.exit(1)
    
    # Read the integration script
    script_path = os.path.join(
        os.path.dirname(__file__), "..", "integrations", f"{integration_name}.py"
    )
    
    if not os.path.exists(script_path):
        print(f"ERROR: Script not found: {script_path}")
        sys.exit(1)
    
    with open(script_path) as f:
        code = f.read()
    
    # Validate code has run() function
    validate_code(code)
    
    # Load schema from separate file
    input_schema = load_schema(integration_name)
    
    # Send to backend
    payload = {
        "session_id": session_id,
        "name": integration_name,
        "code": code,
        "input_schema": input_schema,
    }
    
    url = f"{BACKEND_URL}/webhook/integration"
    
    print(f"Publishing integration: {integration_name}")
    print(f"  -> {url}")
    
    try:
        headers = {"X-Agent-Secret": AGENT_SECRET}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"SUCCESS: Integration {result.get('status', 'saved')}")
            print(f"  Integration ID: {result.get('integration_id')}")
        else:
            print(f"ERROR: {resp.status_code} - {resp.text}")
            sys.exit(1)
            
    except requests.RequestException as e:
        print(f"ERROR: Failed to connect to backend: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python publish_integration.py <integration_name>")
        print("")
        print("Required files:")
        print("  integrations/{name}.py          - Integration code (run function only)")
        print("  integrations/{name}.schema.json - Input schema (JSON object)")
        sys.exit(1)
    
    publish_integration(sys.argv[1])


if __name__ == "__main__":
    main()
