#!/usr/bin/env python3
"""Run a single post cycle and exit. Use for cron/scheduled runs (e.g. on RunPod).
On RunPod, set RUNPOD=1 before running (e.g. RUNPOD=1 python run_one_cycle.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from run_continuous_posts import run_image_cycle, _memory_cleanup

if __name__ == "__main__":
    ok = run_image_cycle()
    _memory_cleanup()
    if ok:
        try:
            from config import ENABLE_US_ET_POSTING_WINDOWS

            if ENABLE_US_ET_POSTING_WINDOWS:
                from posting_schedule import record_successful_post

                record_successful_post()
                print("Recorded successful post in posting schedule state.", flush=True)
        except Exception as e:
            print(f"[SCHEDULE] Could not record post ({e}).", flush=True)
    print("Single cycle done.")
