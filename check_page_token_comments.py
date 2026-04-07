#!/usr/bin/env python3
"""
Check whether your Page access token can reach the Graph API and which scopes are granted.
Commenting as the Page usually requires pages_manage_engagement (plus pages_manage_posts to publish).

Usage (from project folder, with .env):
  python check_page_token_comments.py

Requires in .env:
  PAGE_ID, PAGE_ACCESS_TOKEN (or FACEBOOK_*)
Optional for scope details:
  FACEBOOK_APP_ID, FACEBOOK_APP_SECRET
"""
from __future__ import print_function

import os
import sys

_BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(_BASE)
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

import config  # noqa: E402 — loads .env

from config import FACEBOOK_ACCESS_TOKEN  # noqa: E402
from facebook_api import (  # noqa: E402
    debug_access_token,
    summarize_token_for_page_comments,
    test_facebook_connection,
)


def main():
    print("=== 1) Page read test (PAGE_ID + token) ===\n")
    ok = test_facebook_connection()
    print()
    print("=== 2) Token debug (scopes) ===\n")
    if not (config.FACEBOOK_APP_ID and config.FACEBOOK_APP_SECRET):
        print("Add FACEBOOK_APP_ID and FACEBOOK_APP_SECRET to .env to see granted scopes.")
        print("(Meta: App -> Settings -> Basic)\n")
    data = debug_access_token(input_token=FACEBOOK_ACCESS_TOKEN)
    summarize_token_for_page_comments(data)
    print()
    if not ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
