#!/usr/bin/env python3
"""
Retry run_continuous_posts.run_image_cycle until it succeeds or max attempts.
Use when Step 2b skips: "Duplicate on Facebook" — the news pool and captions change over time.

Run from project root:
  python scripts/wait_for_video_cycle.py --interval 300 --max-attempts 48
"""
from __future__ import annotations

import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.chdir(_ROOT)


def main() -> int:
    p = argparse.ArgumentParser(description="Poll until a video cycle posts (or cap attempts).")
    p.add_argument("--interval", type=int, default=300, help="Seconds between attempts (default 300).")
    p.add_argument("--max-attempts", type=int, default=0, help="Stop after N tries (0 = unlimited).")
    args = p.parse_args()

    import run_continuous_posts as r

    attempt = 0
    while True:
        attempt += 1
        if args.max_attempts and attempt > args.max_attempts:
            print(f"Stopped after {args.max_attempts} attempts without success.", flush=True)
            return 1
        print(f"\n{'=' * 60}\nAttempt {attempt} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'=' * 60}", flush=True)
        try:
            ok = r.run_image_cycle()
            if ok:
                print("Cycle completed successfully.", flush=True)
                return 0
        except KeyboardInterrupt:
            print("Stopped by user.", flush=True)
            return 130
        except Exception as e:
            print(f"Cycle error: {e}", flush=True)
        print(f"Waiting {args.interval}s before next attempt...", flush=True)
        time.sleep(max(30, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
