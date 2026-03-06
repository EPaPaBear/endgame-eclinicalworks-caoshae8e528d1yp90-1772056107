#!/usr/bin/env python3
"""
Test Integration Tool

Runs the integration locally using the run() function.
- Code is read from integrations/{name}.py
- Auth is read from auth/headers.json (global auth file)
"""

import os
import sys
import json


def load_integration(name: str) -> str:
    """Load integration code from file."""
    path = os.path.join(os.path.dirname(__file__), "..", "integrations", f"{name}.py")
    if not os.path.exists(path):
        print(f"ERROR: Integration not found: {path}")
        sys.exit(1)
    with open(path) as f:
        return f.read()


def load_auth() -> dict:
    """Load auth headers from auth/headers.json (global auth file)."""
    auth_path = os.path.join(os.path.dirname(__file__), "..", "auth", "headers.json")

    if not os.path.exists(auth_path):
        print(f"WARNING: Auth file not found: {auth_path}")
        print(f"Using empty headers.")
        return {}

    try:
        with open(auth_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in auth file: {e}")
        sys.exit(1)


def test_integration(name: str, user_input: dict = None):
    """Test an integration by executing its run() function."""
    user_input = user_input or {}

    print(f"Testing integration: {name}")
    print("-" * 40)

    code = load_integration(name)
    auth_headers = load_auth()
    
    # Use single namespace to avoid import visibility issues
    namespace = {'__builtins__': __builtins__}
    
    try:
        exec(code, namespace)
    except Exception as e:
        print(f"ERROR: Code execution failed: {e}")
        sys.exit(1)
    
    # Validate structure
    run_fn = namespace.get('run')
    
    if not run_fn or not callable(run_fn):
        print("ERROR: Integration missing run() function")
        sys.exit(1)
    
    print(f"Auth headers: {list(auth_headers.keys()) if auth_headers else '(none)'}")
    print(f"User input: {user_input}")
    print("-" * 40)
    
    # Execute run()
    print("Executing run()...")
    try:
        result = run_fn(auth_headers, user_input)
        
        print(f"\nResult ({type(result).__name__}):")
        result_str = json.dumps(result, indent=2)
        print(result_str[:1000])
        if len(result_str) > 1000:
            print("... (truncated)")
            
        print("\n" + "=" * 40)
        print("SUCCESS: Integration executed")
        
    except Exception as e:
        print(f"\nERROR: run() failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/test_integration.py <name> [--input '{...}']")
        print("")
        print("Required files:")
        print("  integrations/{name}.py  - Integration code")
        print("  auth/headers.json       - Auth headers (global)")
        sys.exit(1)
    
    name = sys.argv[1]
    user_input = {}
    
    if '--input' in sys.argv:
        idx = sys.argv.index('--input')
        if idx + 1 < len(sys.argv):
            try:
                user_input = json.loads(sys.argv[idx + 1])
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON input: {e}")
                sys.exit(1)
    
    test_integration(name, user_input)


if __name__ == "__main__":
    main()
