#!/usr/bin/env python3
"""
Publish Validation Script Tool

Uploads a validation script to the backend. The validation script defines
check(headers) -> bool and is used to verify auth headers are still valid
before falling back to a full re-login.

Usage:
    python tools/publish_validation_script.py <platform_name>

Required files:
    validation/{platform_name}_check.py  - Script with check(headers) function
"""

import os
import sys
import requests
import subprocess


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
AGENT_SECRET = os.environ.get("AGENT_CALLBACK_SECRET", "")


def get_platform_id() -> str | None:
    """Get platform_id from PLATFORM_ID env var or git branch name."""
    platform_id = os.environ.get("PLATFORM_ID")
    if platform_id:
        return platform_id

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = result.stdout.strip()

        # Try scraper branch patterns
        for prefix in ["agent/scraper/", "endgame/scraper-", "endgame/re-", "endgame/auth-"]:
            if branch.startswith(prefix):
                rest = branch[len(prefix):]
                # First UUID (platform_id) is 36 chars with hyphens
                parts = rest.split("-")
                if len(parts) >= 5:
                    return "-".join(parts[0:5])

        print(f"[WARNING] Could not extract platform_id from branch '{branch}'")
        return None
    except Exception as e:
        print(f"[ERROR] Could not get branch name: {e}")
        return None


def load_validation_script(platform_name: str) -> str:
    """Load validation script from validation/{platform_name}_check.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "..", "validation", f"{platform_name}_check.py")
    path = os.path.normpath(path)

    print(f"[DEBUG] Looking for validation script at: {path}")

    if not os.path.exists(path):
        print(f"[ERROR] Validation script not found: {path}")
        print(f"[ERROR] Create validation/{platform_name}_check.py with a check(headers) function")
        sys.exit(1)

    with open(path) as f:
        code = f.read()

    print(f"[DEBUG] Loaded validation script: {len(code)} bytes")
    return code


def validate_script(code: str) -> bool:
    """Validate that the script defines a callable check(headers) function."""
    namespace = {"__builtins__": __builtins__}
    try:
        exec(code, namespace)
    except Exception as e:
        print(f"[ERROR] Failed to parse validation script: {e}")
        return False

    if "check" not in namespace or not callable(namespace["check"]):
        print("[ERROR] Validation script must define: def check(headers: dict) -> bool")
        return False

    print("[DEBUG] Validation script OK")
    return True


def publish(platform_name: str):
    print("=" * 50)
    print(f"Publishing Validation Script: {platform_name}")
    print("=" * 50)

    platform_id = get_platform_id()
    if not platform_id:
        print("[ERROR] Could not determine platform_id")
        sys.exit(1)

    code = load_validation_script(platform_name)

    if not validate_script(code):
        sys.exit(1)

    payload = {
        "platform_id": platform_id,
        "validation_script_code": code,
    }

    url = f"{BACKEND_URL}/webhook/validation-script"

    print(f"[INFO] Sending to: {url}")
    print(f"[INFO] Platform ID: {platform_id}")

    try:
        headers = {"X-Agent-Secret": AGENT_SECRET} if AGENT_SECRET else {}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)

        if resp.status_code == 200:
            result = resp.json()
            print("[SUCCESS] Validation script published!")
            print(f"  S3 Key: {result.get('validation_script_s3_key')}")
        else:
            print(f"[ERROR] Server returned {resp.status_code}: {resp.text}")
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Could not connect to backend at {BACKEND_URL}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python publish_validation_script.py <platform_name>")
        print()
        print("Required files:")
        print("  validation/{platform_name}_check.py")
        print()
        print("The script must define:")
        print("  def check(headers: dict) -> bool:")
        print("      # Make a lightweight authenticated request")
        print("      # Return True if headers are valid, False if expired")
        sys.exit(1)

    publish(sys.argv[1])


if __name__ == "__main__":
    main()
