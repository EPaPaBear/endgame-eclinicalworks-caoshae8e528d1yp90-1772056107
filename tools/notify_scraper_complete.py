#!/usr/bin/env python3
"""
Tool for the scraper agent to notify the server when scraping is complete.

Usage:
    python3 tools/notify_scraper_complete.py [--failed] [--message "optional message"] [--files-scraped 42]
"""

import os
import sys
import subprocess
import argparse
import requests

# Backend URL - use ngrok in dev, production URL in prod
BACKEND_URL = os.environ.get("BACKEND_URL", "https://7a1a6dcf06c9.ngrok-free.app")
AGENT_SECRET = os.environ.get("AGENT_CALLBACK_SECRET", "")


def get_platform_id_from_env() -> str | None:
    """Get platform_id from environment variable (set by backend)."""
    platform_id = os.environ.get("PLATFORM_ID")
    if platform_id:
        print(f"[DEBUG] PLATFORM_ID from env: {platform_id}")
    return platform_id


def get_platform_id_from_branch() -> str | None:
    """
    Extract platform_id from git branch name (legacy fallback).
    
    Supports:
    - agent/scraper/{platform_id}
    - endgame/re-{platform_id}-{account_id}
    - endgame/{session_id} (requires API lookup)
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()
        print(f"[DEBUG] Current branch: {branch}")
        
        # New format: agent/scraper/{platform_id}
        if branch.startswith("agent/scraper/"):
            platform_id = branch.replace("agent/scraper/", "")
            print(f"[DEBUG] Extracted platform_id: {platform_id}")
            return platform_id
        
        # Legacy format: endgame/re-{platform_id}-{account_id}
        if branch.startswith("endgame/re-"):
            rest = branch.replace("endgame/re-", "")
            parts = rest.split("-")
            
            # A UUID has 5 parts separated by hyphens
            if len(parts) >= 5:
                platform_id = "-".join(parts[0:5])
                print(f"[DEBUG] Extracted platform_id: {platform_id}")
                return platform_id
        
        # Legacy format: endgame/{session_id}
        elif branch.startswith("endgame/"):
            session_id = branch.replace("endgame/", "")
            print(f"[DEBUG] Session ID: {session_id}")
            
            # Try to get platform_id from backend
            try:
                resp = requests.get(
                    f"{BACKEND_URL}/chat/sessions/{session_id}",
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    platform_id = data.get("platform_id")
                    if platform_id:
                        print(f"[DEBUG] Platform ID from session: {platform_id}")
                        return platform_id
            except Exception as e:
                print(f"[WARN] Could not fetch session: {e}")
            
            # Fallback: check if there's a .platform_id file
            platform_file = os.path.join(os.path.dirname(__file__), "..", ".platform_id")
            if os.path.exists(platform_file):
                with open(platform_file) as f:
                    platform_id = f.read().strip()
                    print(f"[DEBUG] Platform ID from file: {platform_id}")
                    return platform_id
        
        print(f"[DEBUG] Could not extract platform_id from branch: {branch}")
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Git command failed: {e}")
        return None


def notify_complete(platform_id: str, failed: bool = False, message: str | None = None, files_scraped: int | None = None):
    """Send completion notification to backend."""
    
    payload = {
        "platform_id": platform_id,
        "status": "failed" if failed else "success",
    }
    
    if message:
        payload["message"] = message
    
    if files_scraped is not None:
        payload["files_scraped"] = files_scraped
    
    url = f"{BACKEND_URL}/webhook/scraper-complete"
    
    print("=" * 50)
    print(f"Notifying server: Scraper {'FAILED' if failed else 'COMPLETE'}")
    print("=" * 50)
    print(f"[INFO] URL: {url}")
    print(f"[INFO] Platform ID: {platform_id}")
    print(f"[INFO] Status: {payload['status']}")
    if message:
        print(f"[INFO] Message: {message}")
    if files_scraped:
        print(f"[INFO] Files scraped: {files_scraped}")
    print("-" * 50)
    
    try:
        headers = {"X-Agent-Secret": AGENT_SECRET} if AGENT_SECRET else {}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            print("=" * 50)
            print("[SUCCESS] Server notified!")
            print(f"  Platform status: {result.get('platform_status', 'unknown')}")
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
    parser = argparse.ArgumentParser(description="Notify server that scraping is complete")
    parser.add_argument("--failed", action="store_true", help="Mark scraping as failed")
    parser.add_argument("--message", type=str, help="Optional message about the result")
    parser.add_argument("--files-scraped", type=int, help="Number of files scraped")
    parser.add_argument("--platform-id", type=str, help="Platform ID (auto-detected from branch if not provided)")
    
    args = parser.parse_args()
    
    # Get platform_id (priority: args > env > branch)
    platform_id = args.platform_id or get_platform_id_from_env() or get_platform_id_from_branch()
    
    if not platform_id:
        print("[ERROR] Could not determine platform_id")
        print("[ERROR] Either provide --platform-id or ensure you're on the correct git branch")
        sys.exit(1)
    
    notify_complete(
        platform_id=platform_id,
        failed=args.failed,
        message=args.message,
        files_scraped=args.files_scraped
    )


if __name__ == "__main__":
    main()



