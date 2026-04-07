#!/usr/bin/env python3
"""
Run the same full workflow (news -> caption -> image -> overlay -> post) for an
India-focused Facebook page. Uses .env for shared keys and .env.india for page-specific
settings (India page credentials, India news, topic theme).

Setup:
  1. Copy .env.india.example to .env.india and fill in your India page credentials.
  2. Keep .env with NEWS_API_KEY, GEMINI_API_KEY, Ollama, etc. (shared).
  3. Run: python run_india_page.py

To run both pages: run run_continuous_posts.py in one terminal (main page) and
run_india_page.py in another (India page), or use two machines/RunPods.
"""
from pathlib import Path
import os
import sys

# Load env files BEFORE any project imports so config sees India overrides
_root = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
    _india_env = _root / ".env.india"
    if _india_env.exists():
        load_dotenv(_india_env)
        print(f"[India page] Loaded {_india_env.name}")
    else:
        print(f"[India page] Warning: .env.india not found. Copy .env.india.example to .env.india and set PAGE_ID, PAGE_ACCESS_TOKEN, NEWS_COUNTRIES=in")
except ImportError:
    pass

# Ensure project root on path
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
os.chdir(_root)

from run_continuous_posts import main

if __name__ == "__main__":
    sys.exit(main() or 0)
