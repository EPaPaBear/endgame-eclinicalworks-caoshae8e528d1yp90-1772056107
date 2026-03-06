#!/usr/bin/env python3
"""
Publish Login Script Tool (Reverse Engineering Flow)

Uploads the login script to the backend.
The login script authenticates via HTTP and returns headers.

Usage:
    python tools/publish_login_script.py <platform_name>

Required files:
    auth/{platform_name}_login.py  - Login script with login(username, password) function
"""

import os
import sys
import json
import requests
import subprocess


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
AGENT_SECRET = os.environ.get("AGENT_CALLBACK_SECRET", "")


def get_ids_from_env() -> tuple[str | None, str | None]:
    """
    Get platform_id and account_id from environment variables (set by backend).
    
    Returns:
        Tuple of (platform_id, account_id) or (None, None) if not set
    """
    platform_id = os.environ.get("PLATFORM_ID")
    account_id = os.environ.get("ACCOUNT_ID")
    
    if platform_id:
        print(f"[DEBUG] PLATFORM_ID from env: {platform_id}")
    if account_id:
        print(f"[DEBUG] ACCOUNT_ID from env: {account_id}")
    
    return platform_id, account_id


def get_ids_from_branch() -> tuple[str | None, str | None]:
    """
    Extract platform_id and account_id from git branch name (legacy fallback).
    Branch format: endgame/re-{platform_id}-{account_id} or agent/login/{platform_id}-{account_id}
    
    Returns:
        Tuple of (platform_id, account_id) or (None, None) if extraction fails
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = result.stdout.strip()
        print(f"[DEBUG] Current branch: {branch}")
        
        # Try different branch formats
        rest = None
        if branch.startswith("agent/login/"):
            rest = branch.replace("agent/login/", "")
        elif branch.startswith("endgame/re-"):
            rest = branch.replace("endgame/re-", "")
        
        if rest:
            # Format: {platform_id}-{account_id}
            # Both IDs are UUIDs (36 chars each)
            parts = rest.split("-")
            
            # A UUID has 5 parts separated by hyphens
            # So platform_id is parts[0:5] and account_id is parts[5:10]
            if len(parts) >= 10:
                platform_id = "-".join(parts[0:5])
                account_id = "-".join(parts[5:10])
                print(f"[DEBUG] Extracted platform_id: {platform_id}")
                print(f"[DEBUG] Extracted account_id: {account_id}")
                return platform_id, account_id
            else:
                print(f"[ERROR] Could not parse IDs from branch '{branch}'")
                return None, None
        else:
            print(f"[DEBUG] Branch '{branch}' does not match expected patterns")
            return None, None
    except Exception as e:
        print(f"[ERROR] Could not get branch name: {e}")
        return None, None


def load_login_script(platform_name: str) -> str:
    """Load login script from auth/{platform_name}/{platform_name}_login.py or auth/{platform_name}_login.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Primary: auth/{platform}/{platform}_login.py (new pipeline)
    login_script_path = os.path.join(script_dir, "..", "auth", platform_name, f"{platform_name}_login.py")
    login_script_path = os.path.normpath(login_script_path)

    # Fallback: auth/{platform}_login.py (legacy flat path)
    if not os.path.exists(login_script_path):
        login_script_path = os.path.join(script_dir, "..", "auth", f"{platform_name}_login.py")
        login_script_path = os.path.normpath(login_script_path)

    print(f"[DEBUG] Looking for login script at: {login_script_path}")

    if not os.path.exists(login_script_path):
        print(f"[ERROR] Login script not found")
        print(f"[ERROR] Searched: auth/{platform_name}/{platform_name}_login.py and auth/{platform_name}_login.py")
        sys.exit(1)
    
    with open(login_script_path) as f:
        code = f.read()
    
    print(f"[DEBUG] Loaded login script: {len(code)} bytes, {len(code.splitlines())} lines")
    return code


def validate_login_script(code: str) -> bool:
    """
    Validate that the login script has the required login() function.
    """
    print("[DEBUG] Validating login script...")
    
    namespace = {'__builtins__': __builtins__}
    
    try:
        exec(code, namespace)
    except Exception as e:
        print(f"[ERROR] Failed to execute login script: {e}")
        return False
    
    if 'login' not in namespace or not callable(namespace['login']):
        print("[ERROR] Login script missing required login(username, password) function")
        print("[ERROR] Your script must define:")
        print("    def login(username: str, password: str) -> dict:")
        print('        """Authenticate and return headers."""')
        print("        # ... your login logic ...")
        print("        return {'Cookie': '...', 'Authorization': '...'}")
        return False
    
    print("[DEBUG] Login script validation passed!")
    return True


def test_login_script_syntax(code: str) -> bool:
    """
    Test that the login script can be imported and has correct signature.
    Does NOT actually run the login (that would require credentials).
    """
    print("[DEBUG] Testing login script syntax...")
    
    namespace = {'__builtins__': __builtins__}
    
    try:
        exec(code, namespace)
        
        # Check function signature
        import inspect
        login_func = namespace['login']
        sig = inspect.signature(login_func)
        params = list(sig.parameters.keys())
        
        # Should have at least username and password
        if len(params) < 2:
            print(f"[WARNING] login() has {len(params)} parameters, expected at least 2 (username, password)")
        else:
            print(f"[DEBUG] login() signature: ({', '.join(params)})")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Syntax test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def publish_login_script(platform_name: str, platform_id: str = None, account_id: str = None):
    """Publish the login script to the backend."""
    print("=" * 50)
    print(f"Publishing Login Script: {platform_name}")
    print("=" * 50)
    
    # 1. Get platform_id and account_id (priority: args > env > branch)
    if not platform_id or not account_id:
        env_platform_id, env_account_id = get_ids_from_env()
        platform_id = platform_id or env_platform_id
        account_id = account_id or env_account_id
    
    if not platform_id or not account_id:
        branch_platform_id, branch_account_id = get_ids_from_branch()
        platform_id = platform_id or branch_platform_id
        account_id = account_id or branch_account_id
    
    if not platform_id:
        print("[ERROR] Could not determine platform_id")
        print("[ERROR] Either pass --platform-id or be on a branch named 'endgame/re-{platform_id}-{account_id}'")
        sys.exit(1)
    
    # 2. Load login script
    code = load_login_script(platform_name)
    
    # 3. Validate login script
    if not validate_login_script(code):
        sys.exit(1)
    
    # 4. Test syntax (does not run login)
    if not test_login_script_syntax(code):
        sys.exit(1)
    
    # 5. Send to backend
    payload = {
        "platform_id": platform_id,
        "login_script_code": code,
        "platform_name": platform_name,
    }
    if account_id:
        payload["account_id"] = account_id
    
    url = f"{BACKEND_URL}/webhook/login-script"
    
    print("-" * 50)
    print(f"[INFO] Sending to: {url}")
    print(f"[INFO] Platform ID: {platform_id}")
    if account_id:
        print(f"[INFO] Account ID: {account_id}")
    print(f"[INFO] Code size: {len(code)} bytes")
    print("-" * 50)
    
    try:
        headers = {"X-Agent-Secret": AGENT_SECRET} if AGENT_SECRET else {}
        resp = requests.post(url, json=payload, headers=headers, timeout=120)  # Longer timeout for login test
        
        if resp.status_code == 200:
            result = resp.json()
            print("=" * 50)
            print("[SUCCESS] Login script published!")
            print(f"  Status: {result.get('status', 'unknown')}")
            if result.get('headers_valid'):
                print("  Headers validated: YES")
            else:
                print("  Headers validated: NO (but script saved)")
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
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Publish login script to the backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Required files:
  auth/{platform_name}_login.py  - Login script with login(username, password) function

The login script should define:
  def login(username: str, password: str) -> dict:
      '''
      Authenticate to the platform and return headers.
      
      Args:
          username: The username or email
          password: The password
      Returns:
          Dict of HTTP headers to use for authenticated requests
      '''
      pass
"""
    )
    parser.add_argument("platform_name", help="Name of the platform (e.g., 'healthie')")
    parser.add_argument("--platform-id", help="Platform ID (UUID). If not provided, extracted from git branch.")
    parser.add_argument("--account-id", help="Account ID (UUID). If not provided, extracted from git branch.")
    
    args = parser.parse_args()
    
    publish_login_script(args.platform_name, args.platform_id, args.account_id)


if __name__ == "__main__":
    main()


