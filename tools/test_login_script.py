#!/usr/bin/env python3
"""
Test Login Script Tool

Runs a login script exactly as production would - with fetch_2fa_code injected.
This allows the agent to verify the script works before publishing.

Usage:
    python tools/test_login_script.py <platform_name> <username> <password>

Required files:
    auth/{platform_name}_login.py  - Login script with login(username, password) function
"""

import os
import sys
import json

# Import shared 2FA function
from tools.twofa import fetch_2fa_code


def load_login_script(platform_name: str) -> str:
    """Load login script from auth/{platform_name}/{platform_name}_login.py or auth/{platform_name}_login.py"""
    base = os.path.join(os.path.dirname(__file__), "..")
    possible_paths = [
        # New pipeline: auth/{platform}/{platform}_login.py
        os.path.join(base, "auth", platform_name, f"{platform_name}_login.py"),
        os.path.join("/workspace/repo", "auth", platform_name, f"{platform_name}_login.py"),
        # Legacy flat: auth/{platform}_login.py
        os.path.join(base, "auth", f"{platform_name}_login.py"),
        os.path.join("/workspace/repo", "auth", f"{platform_name}_login.py"),
    ]

    for path in possible_paths:
        path = os.path.normpath(path)
        if os.path.exists(path):
            print(f"[DEBUG] Found login script at: {path}")
            with open(path) as f:
                return f.read()

    print(f"[ERROR] Login script not found. Searched:")
    for path in possible_paths:
        print(f"  - {os.path.normpath(path)}")
    sys.exit(1)


def test_login_script(platform_name: str, username: str, password: str) -> dict:
    """
    Test a login script exactly as production would.

    1. Loads the script from auth/{platform_name}_login.py
    2. Injects fetch_2fa_code into namespace
    3. Runs login(username, password)
    4. Returns the headers
    """
    print("=" * 50)
    print(f"Testing Login Script: {platform_name}")
    print("=" * 50)

    # 1. Load script
    code = load_login_script(platform_name)
    print(f"[DEBUG] Loaded script: {len(code)} bytes")

    # 2. Create namespace with fetch_2fa_code injected
    namespace = {
        '__builtins__': __builtins__,
        'fetch_2fa_code': fetch_2fa_code,
    }

    # 3. Execute script to load the login function
    print("[DEBUG] Loading script into namespace...")
    try:
        exec(code, namespace)
    except Exception as e:
        print(f"[ERROR] Script execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 4. Verify login function exists
    if 'login' not in namespace or not callable(namespace['login']):
        print("[ERROR] Script does not define a 'login' function")
        sys.exit(1)

    # 5. Run login
    print("-" * 50)
    print(f"[INFO] Running login({username[:3]}***, ***)")
    print("-" * 50)

    try:
        headers = namespace['login'](username, password)
    except Exception as e:
        print(f"[ERROR] login() failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 6. Validate result
    if not isinstance(headers, dict):
        print(f"[ERROR] login() returned {type(headers).__name__}, expected dict")
        sys.exit(1)

    if not headers:
        print("[ERROR] login() returned empty headers")
        sys.exit(1)

    # 7. Success
    print("=" * 50)
    print("[SUCCESS] Login script works!")
    print(f"[INFO] Headers returned: {len(headers)}")
    print("-" * 50)
    for key in list(headers.keys())[:5]:
        value = str(headers[key])
        if len(value) > 50:
            value = value[:50] + "..."
        print(f"  {key}: {value}")
    if len(headers) > 5:
        print(f"  ... and {len(headers) - 5} more")
    print("=" * 50)

    return headers


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/test_login_script.py <platform_name> [username] [password]")
        print("")
        print("Credentials can be passed as:")
        print("  1. CLI args:  python tools/test_login_script.py healthie user@example.com mypassword")
        print("  2. Env vars:  LOGIN_USERNAME / LOGIN_PASSWORD")
        print("  3. Stdin JSON: echo '{\"username\":\"u\",\"password\":\"p\"}' | python tools/test_login_script.py healthie --stdin")
        print("")
        print("Required files:")
        print("  auth/{platform_name}_login.py  - Login script")
        sys.exit(1)

    platform_name = sys.argv[1]

    # Priority: --stdin > CLI args > env vars
    if "--stdin" in sys.argv:
        import select
        data = json.loads(sys.stdin.read())
        username = data["username"]
        password = data["password"]
    elif len(sys.argv) >= 4:
        username = sys.argv[2]
        password = sys.argv[3]
    else:
        username = os.environ.get("LOGIN_USERNAME", "")
        password = os.environ.get("LOGIN_PASSWORD", "")
        if not username or not password:
            print("[ERROR] No credentials provided. Use CLI args, env vars, or --stdin.")
            sys.exit(1)

    test_login_script(platform_name, username, password)


if __name__ == "__main__":
    main()
