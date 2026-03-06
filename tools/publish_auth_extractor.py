#!/usr/bin/env python3
"""
Publish Auth Extractor Tool

Uploads the auth extractor script to the backend.
The extractor script reads auth_dump.json and outputs HTTP headers.

Usage:
    python tools/publish_auth_extractor.py <platform_name>

Required files:
    extractors/{platform_name}.py  - Extractor code with:
                                     - extract(auth_dump) -> dict
                                     - determine_base_url(provided_url, auth_dump, network_capture) -> str
"""

import os
import sys
import json
import requests
import subprocess


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
AGENT_SECRET = os.environ.get("AGENT_CALLBACK_SECRET", "")


def get_platform_id_from_branch() -> str | None:
    """
    Extract platform_id from git branch name.
    Branch format: endgame/auth-{platform_id}
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = result.stdout.strip()
        print(f"[DEBUG] Current branch: {branch}")

        if branch.startswith("endgame/auth-"):
            platform_id = branch.replace("endgame/auth-", "")
            print(f"[DEBUG] Extracted platform_id: {platform_id}")
            return platform_id
        else:
            print(f"[ERROR] Branch '{branch}' does not match pattern 'endgame/auth-{{platform_id}}'")
            return None
    except Exception as e:
        print(f"[ERROR] Could not get branch name: {e}")
        return None


def get_account_id_from_env() -> str | None:
    """
    Get account_id from ACCOUNT_ID environment variable.
    This is set by the backend when starting the agent.
    """
    account_id = os.environ.get("ACCOUNT_ID")
    if account_id:
        print(f"[DEBUG] ACCOUNT_ID from env: {account_id}")
    return account_id


def load_extractor_code(platform_name: str) -> str:
    """Load extractor code from extractors/{platform_name}.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    extractor_path = os.path.join(script_dir, "..", "extractors", f"{platform_name}.py")
    extractor_path = os.path.normpath(extractor_path)
    
    print(f"[DEBUG] Looking for extractor at: {extractor_path}")
    
    if not os.path.exists(extractor_path):
        print(f"[ERROR] Extractor file not found: {extractor_path}")
        print(f"[ERROR] Create extractors/{platform_name}.py with your extract(auth_dump) function")
        sys.exit(1)
    
    with open(extractor_path) as f:
        code = f.read()
    
    print(f"[DEBUG] Loaded extractor code: {len(code)} bytes, {len(code.splitlines())} lines")
    return code


def validate_extractor(code: str) -> bool:
    """
    Validate that extractor code has both required functions.
    """
    print("[DEBUG] Validating extractor code...")
    
    namespace = {'__builtins__': __builtins__}
    
    try:
        exec(code, namespace)
    except Exception as e:
        print(f"[ERROR] Failed to execute extractor code: {e}")
        return False
    
    if 'extract' not in namespace or not callable(namespace['extract']):
        print("[ERROR] Extractor missing required extract(auth_dump) function")
        print("[ERROR] Your extractor must define:")
        print("    def extract(auth_dump: dict) -> dict:")
        print('        """Extract headers from auth dump."""')
        print("        cookies = auth_dump.get('cookies', {})")
        print("        # ... your logic ...")
        print("        return {'Cookie': '...', 'Authorization': '...'}")
        return False

    if 'determine_base_url' not in namespace or not callable(namespace['determine_base_url']):
        print(
            "[ERROR] Extractor missing required determine_base_url("
            "provided_url, auth_dump, network_capture) function"
        )
        print("[ERROR] Your extractor must define:")
        print("    def determine_base_url(provided_url: str, auth_dump: dict, network_capture: list[dict]) -> str:")
        print("        return provided_url")
        return False
    
    print("[DEBUG] Extractor validation passed!")
    return True


def test_extractor_locally(code: str) -> dict | None:
    """
    Test the extractor against the local auth_dump.json if available.
    Returns the extracted headers or None if test fails.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    auth_dump_path = os.path.join(script_dir, "..", "scraped_data", "auth", "auth_dump.json")
    auth_dump_path = os.path.normpath(auth_dump_path)
    
    if not os.path.exists(auth_dump_path):
        print(f"[WARNING] auth_dump.json not found at {auth_dump_path}")
        print("[WARNING] Skipping local test - will test on server")
        return None
    
    print(f"[DEBUG] Testing extractor with {auth_dump_path}...")
    
    try:
        with open(auth_dump_path) as f:
            auth_dump = json.load(f)
        
        namespace = {'__builtins__': __builtins__}
        exec(code, namespace)
        
        headers = namespace['extract'](auth_dump)
        
        if not isinstance(headers, dict):
            print(f"[ERROR] extract() returned {type(headers).__name__}, expected dict")
            return None
        
        print(f"[DEBUG] Extractor returned {len(headers)} headers:")
        for key in list(headers.keys())[:5]:
            value = str(headers[key])
            print(f"[DEBUG]   {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
        if len(headers) > 5:
            print(f"[DEBUG]   ... and {len(headers) - 5} more")
        
        # Optional local test for determine_base_url if network_capture is available.
        network_capture_path = os.path.join(
            script_dir, "..", "scraped_data", "auth", "network_capture.json"
        )
        network_capture = []
        if os.path.exists(network_capture_path):
            with open(network_capture_path) as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                network_capture = loaded
        resolved = namespace["determine_base_url"](
            os.environ.get("PROVIDED_URL", "https://example.com"),
            auth_dump,
            network_capture,
        )
        if not isinstance(resolved, str) or not resolved.strip():
            print("[ERROR] determine_base_url() must return a non-empty string")
            return None
        print(f"[DEBUG] determine_base_url() -> {resolved.strip()}")

        return headers
        
    except Exception as e:
        print(f"[ERROR] Local test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def publish_extractor(platform_name: str):
    """Publish the auth extractor to the backend."""
    print("=" * 50)
    print(f"Publishing Auth Extractor: {platform_name}")
    print("=" * 50)

    # 1. Get platform_id from branch
    platform_id = get_platform_id_from_branch()
    if not platform_id:
        print("[ERROR] Could not determine platform_id from git branch")
        print("[ERROR] Make sure you're on a branch named 'endgame/auth-{platform_id}'")
        sys.exit(1)

    # 2. Get account_id from environment
    account_id = get_account_id_from_env()
    if not account_id:
        print("[ERROR] ACCOUNT_ID not set in environment")
        print("[ERROR] This should be set by the backend when starting the agent")
        sys.exit(1)

    # 3. Load extractor code
    code = load_extractor_code(platform_name)

    # 4. Validate extractor
    if not validate_extractor(code):
        sys.exit(1)

    # 5. Test locally (optional but recommended)
    test_headers = test_extractor_locally(code)
    if test_headers:
        print("[DEBUG] Local test passed!")

    # 6. Send to backend
    payload = {
        "platform_id": platform_id,
        "account_id": account_id,
        "extractor_code": code,
        "platform_name": platform_name,
    }
    
    url = f"{BACKEND_URL}/webhook/auth-extractor"
    
    print("-" * 50)
    print(f"[INFO] Sending to: {url}")
    print(f"[INFO] Platform ID: {platform_id}")
    print(f"[INFO] Code size: {len(code)} bytes")
    print("-" * 50)
    
    try:
        headers = {"X-Agent-Secret": AGENT_SECRET} if AGENT_SECRET else {}
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if resp.status_code == 200:
            result = resp.json()
            print("=" * 50)
            print("[SUCCESS] Auth extractor published!")
            print(f"  Status: {result.get('status', 'unknown')}")
            if result.get('headers_valid'):
                print("  Headers validated: ✓")
            if result.get('headers_count'):
                print(f"  Headers extracted: {result.get('headers_count')}")
            print("=" * 50)
        else:
            print("=" * 50)
            print(f"[ERROR] Server returned {resp.status_code}")
            print(f"[ERROR] Response: {resp.text}")
            print("=" * 50)
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Could not connect to backend at {BACKEND_URL}")
        print("[ERROR] Make sure the backend server is running")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python publish_auth_extractor.py <platform_name>")
        print("")
        print("Required files:")
        print("  extractors/{platform_name}.py  - Extractor with extract() and determine_base_url()")
        print("")
        print("The extractor should define:")
        print("  def extract(auth_dump: dict) -> dict:")
        print("      '''")
        print("      Args:")
        print("          auth_dump: Dict with 'cookies', 'localStorage', 'sessionStorage'")
        print("      Returns:")
        print("          Dict of HTTP headers to use for authenticated requests")
        print("      '''")
        print("      pass")
        print("")
        print("  def determine_base_url(provided_url: str, auth_dump: dict, network_capture: list[dict]) -> str:")
        print("      '''")
        print("      Args:")
        print("          provided_url: Account login URL from backend")
        print("          auth_dump: Dict with browser auth state")
        print("          network_capture: List of captured authenticated requests")
        print("      Returns:")
        print("          Internal API base URL as http(s) string")
        print("      '''")
        print("      return provided_url")
        sys.exit(1)
    
    platform_name = sys.argv[1]
    publish_extractor(platform_name)


if __name__ == "__main__":
    main()








