#!/usr/bin/env python3
"""
Multi-agent orchestrator: run one image cycle for multiple pages/themes in parallel.
Loads sector config from sectors.json; each sector runs in its own process (different page + theme).
Use --page 1 to run only the first sector (focus on page 1).
"""
from __future__ import print_function
import os
import sys
import json
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

CONFIG_JSON = os.path.join(_BASE, "config.json")
SECTORS_JSON = os.path.join(_BASE, "sectors.json")


def load_sectors(path=None):
    """Load sector configs from JSON. Tries config.json then sectors.json (plan: config.json or sectors.json)."""
    if path and os.path.exists(path):
        p = path
    elif os.path.exists(CONFIG_JSON):
        p = CONFIG_JSON
    elif os.path.exists(SECTORS_JSON):
        p = SECTORS_JSON
    else:
        p = None
    if not p or not os.path.exists(p):
        print("No config.json or sectors.json found. Copy config.example.json or sectors.example.json and add your pages/tokens.")
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    # Filter out entries without token/page_id so we don't crash
    return [c for c in data if c.get("page_id") and c.get("token")]


def run_one_cycle_standalone(sector_config):
    """
    Entry point for ProcessPoolExecutor: must be a top-level function for pickling.
    Runs worker_cycle.run_one_cycle in the worker process.
    """
    from worker_cycle import run_one_cycle
    return run_one_cycle(sector_config)


def main():
    parser = argparse.ArgumentParser(description="Run one image cycle per sector (page). Use --page 1 to run only the first sector.")
    parser.add_argument("--page", type=int, default=None, metavar="N", help="Run only sector N (1-based; e.g. --page 1 for first page). Omit to run all.")
    parser.add_argument("--config", type=str, default=None, help="Path to config.json or sectors.json (default: auto-detect)")
    args = parser.parse_args()

    os.chdir(_BASE)
    sectors = load_sectors(args.config)
    if not sectors:
        print("No sectors to run. Exiting.")
        return 1

    if args.page is not None:
        idx = args.page - 1  # 1-based
        if idx < 0 or idx >= len(sectors):
            print(f"Invalid --page {args.page}. Valid range: 1 to {len(sectors)}.")
            return 1
        sectors = [sectors[idx]]
        print("=" * 60)
        print(f"PAGE 1 ONLY — Running single sector: {sectors[0].get('sector')}")
        print("=" * 60)
    else:
        print("=" * 60)
        print("MULTI-AGENT ORCHESTRATOR — One cycle per page/theme in parallel")
        print("=" * 60)
        print(f"  Sectors: {[s.get('sector') for s in sectors]}")
        print("=" * 60)

    results = []
    max_workers = min(len(sectors), 4)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_sector = {executor.submit(run_one_cycle_standalone, cfg): cfg.get("sector") for cfg in sectors}
        for future in as_completed(future_to_sector):
            sector_name = future_to_sector[future]
            try:
                name, success = future.result()
                results.append((name, success))
                print(f"  Done: {name} -> {'OK' if success else 'FAIL'}")
            except Exception as e:
                print(f"  Done: {sector_name} -> ERROR: {e}")
                results.append((sector_name, False))

    print("\n" + "=" * 60)
    print("ORCHESTRATOR FINISHED")
    for name, ok in results:
        print(f"  {name}: {'SUCCESS' if ok else 'FAILED'}")
    print("=" * 60)
    return 0 if all(r[1] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
