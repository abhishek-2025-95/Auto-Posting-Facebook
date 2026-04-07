#!/usr/bin/env python3
"""
RunPod bootstrap: ensure cwd and .env, set RUNPOD=1, run continuous pipeline.
Captures crashes to runpod_crash.log. Run from project root: nohup python start_runpod.py >> runpod.log 2>&1 &
"""
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Run from project root (script directory)
SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Write to log immediately so we know the process started (before any heavy imports)
_log = SCRIPT_DIR / "runpod.log"
try:
    with open(_log, "a", encoding="utf-8") as f:
        f.write(f"[start_runpod] started at {datetime.utcnow().isoformat()}Z cwd={SCRIPT_DIR}\n")
except Exception:
    pass

# Load .env from project root before any other project imports
_env_file = SCRIPT_DIR / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass
# Gemini SDK looks for GOOGLE_API_KEY; set from GEMINI_API_KEY so it works before any genai import
_gemini = os.environ.get("GEMINI_API_KEY", "").strip()
if _gemini and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _gemini
os.environ["RUNPOD"] = "1"

def main():
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(line_buffering=True)
            sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass
    print(f"[start_runpod] cwd={os.getcwd()}, RUNPOD=1", flush=True)
    crash_log = SCRIPT_DIR / "runpod_crash.log"
    try:
        from run_continuous_posts import main as run_main
        return run_main()
    except Exception as e:
        msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        try:
            with open(crash_log, "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        print(msg, flush=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
