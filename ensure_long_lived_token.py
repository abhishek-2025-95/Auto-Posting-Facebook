#!/usr/bin/env python3
"""
Exchange your current Page (or User) token for a long-lived Page access token.

- Short-lived tokens (e.g. Graph API Explorer) expire in ~1–2 hours.
- After exchange: Page access tokens from a long-lived user token typically have **no expiry**
  in normal use (until you revoke the app, change password, or Meta invalidates them).
- Requires: FACEBOOK_APP_ID + FACEBOOK_APP_SECRET (Meta → App → Settings → Basic).

Usage:
  python ensure_long_lived_token.py              # prints new token (copy into .env)
  python ensure_long_lived_token.py --write-env  # updates PAGE_ACCESS_TOKEN in .env

Re-run every ~60 days if you use a user token flow, or use a Meta **System User** token
for Business-managed apps if you need stricter “always on” automation.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parent
_GRAPH = "v21.0"


def _load_dotenv():
    try:
        from dotenv import load_dotenv
        load_dotenv(_ROOT / ".env")
    except ImportError:
        pass


def _write_env_page_token(page_token: str, page_id: str) -> bool:
    """Replace PAGE_ACCESS_TOKEN (and PAGE_ID if present) in .env; backup .env.bak once."""
    env_path = _ROOT / ".env"
    if not env_path.is_file():
        print(f"ERROR: No {env_path} - create .env first.")
        return False
    raw = env_path.read_text(encoding="utf-8")
    bak = _ROOT / ".env.bak"
    if not bak.is_file():
        bak.write_text(raw, encoding="utf-8")
        print(f"Backup saved: {bak}")

    def repl_token(m):
        return f"PAGE_ACCESS_TOKEN={page_token}"

    def repl_id(m):
        return f"PAGE_ID={page_id}"

    out, n_tok = re.subn(r"^PAGE_ACCESS_TOKEN=.*$", repl_token, raw, flags=re.MULTILINE)
    if n_tok == 0:
        out = f"PAGE_ACCESS_TOKEN={page_token}\n" + out
    out, n_id = re.subn(r"^PAGE_ID=.*$", repl_id, out, flags=re.MULTILINE)
    if n_id == 0:
        out = f"PAGE_ID={page_id}\n" + out

    env_path.write_text(out, encoding="utf-8")
    print(f"Updated {env_path} with long-lived PAGE_ACCESS_TOKEN (and PAGE_ID).")
    return True


def _debug_expiry(page_token: str, app_id: str, app_secret: str) -> None:
    app_access = f"{app_id}|{app_secret}"
    url = f"https://graph.facebook.com/{_GRAPH}/debug_token"
    try:
        r = requests.get(
            url,
            params={"input_token": page_token, "access_token": app_access},
            timeout=20,
        )
        if not r.ok:
            print(f"(Could not read token expiry: {r.status_code})")
            return
        data = r.json().get("data") or {}
        exp = data.get("expires_at")
        is_valid = data.get("is_valid")
        if exp == 0 or exp is None:
            print("debug_token: Page token shows no short expiry (good for automation).")
        else:
            print(f"debug_token: expires_at={exp} (Unix). Valid={is_valid}")
    except Exception as e:
        print(f"(debug_token skipped: {e})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Exchange for long-lived Facebook Page access token")
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Write new PAGE_ACCESS_TOKEN into .env (keeps .env.bak first time)",
    )
    args = parser.parse_args()

    os.chdir(_ROOT)
    _load_dotenv()

    token = (os.environ.get("FACEBOOK_ACCESS_TOKEN") or os.environ.get("PAGE_ACCESS_TOKEN") or "").strip()
    page_id = (os.environ.get("FACEBOOK_PAGE_ID") or os.environ.get("PAGE_ID") or "").strip()
    app_id = os.environ.get("FACEBOOK_APP_ID", "").strip()
    app_secret = os.environ.get("FACEBOOK_APP_SECRET", "").strip()

    print("=" * 60)
    print("Long-lived Facebook Page access token")
    print("=" * 60)

    if not token:
        print("ERROR: Set PAGE_ACCESS_TOKEN=... in .env (current short- or long-lived token to exchange).")
        return 1
    if not page_id:
        print("ERROR: Set PAGE_ID=... in .env")
        return 1

    if not app_id or not app_secret:
        print("You need FACEBOOK_APP_ID and FACEBOOK_APP_SECRET.")
        print("  Meta: https://developers.facebook.com/apps/ → Your App → Settings → Basic")
        print("  Add to .env:")
        print("    FACEBOOK_APP_ID=...")
        print("    FACEBOOK_APP_SECRET=...")
        if sys.stdin.isatty():
            if not app_id:
                app_id = input("App ID (or Enter to abort): ").strip()
            if not app_secret:
                app_secret = input("App Secret (or Enter to abort): ").strip()
        if not app_id or not app_secret:
            return 1

    print("\nStep 1/2: Exchanging for long-lived user token...")
    url = f"https://graph.facebook.com/{_GRAPH}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token,
    }
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        print(f"ERROR: Exchange failed: {r.status_code}")
        print(r.text[:800])
        print("\nTip: Token may already be long-lived, or not a user/Page token this endpoint accepts.")
        print("      Get a fresh User token from Graph API Explorer with pages_show_list,")
        print("      pages_manage_posts, pages_manage_engagement, then run again.")
        return 1
    data = r.json()
    long_lived_user = data.get("access_token")
    expires_in = data.get("expires_in", 0)
    if not long_lived_user:
        print("ERROR: No access_token in exchange response.")
        return 1
    print(f"  OK (user token expires_in: {expires_in}s (~{expires_in // 86400} days)")

    print("\nStep 2/2: Getting long-lived Page access token...")
    url = f"https://graph.facebook.com/{_GRAPH}/{page_id}"
    r = requests.get(url, params={"fields": "access_token", "access_token": long_lived_user}, timeout=30)
    if r.status_code != 200:
        print(f"ERROR: Page token request failed: {r.status_code}")
        print(r.text[:800])
        return 1
    page_token = r.json().get("access_token")
    if not page_token:
        print("ERROR: No page access_token - check PAGE_ID matches the Page for this app.")
        return 1
    print("  OK - Page token retrieved.")

    print("\n" + "=" * 60)
    print("SUCCESS - use this as PAGE_ACCESS_TOKEN")
    print("=" * 60)
    print(f"PAGE_ACCESS_TOKEN={page_token}")
    print(f"PAGE_ID={page_id}")
    print("=" * 60)

    _debug_expiry(page_token, app_id, app_secret)

    if args.write_env:
        if _write_env_page_token(page_token, page_id):
            print("\nDone. Your .env now has the long-lived Page token.")
    else:
        print("\nTo update .env automatically: python ensure_long_lived_token.py --write-env")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
