"""Print ET schedule status: posts today vs slots passed (missed / catch-up). Run from project root."""
from __future__ import annotations

import os
import sys

# Project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import config
import posting_schedule as ps


def main() -> None:
    n = config.POSTS_PER_DAY
    dt = ps.now_et()
    d = dt.date()
    slots = ps.daily_slot_times_et(d, n)
    date_et, count = ps.load_daily_count()
    due = sum(1 for t in slots if t <= dt)
    backlog = max(0, due - count)
    remaining_cap = max(0, n - count)

    lab = ps.schedule_short_tz_label()
    print(f"Now ({lab}): {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"State file: date_et={date_et!r}, posts_count={count}")
    print(f"POSTS_PER_DAY: {n}")
    print(f"Slot times passed by now: {due} / {len(slots)}")
    print(f"Posts recorded for that ET day: {count}")
    print(f"Behind slot clock (catch-up owed): {backlog}")
    print(f"Room left under daily cap today: {remaining_cap}")
    if backlog > 0:
        print("=> YES — fewer posts than slots that have already passed in ET; next run should not wait for a window.")
    else:
        print("=> NO backlog vs passed slots - not behind the ET slot clock (may be waiting for next slot).")
    print(f"--- All slot times today ({lab}) ---")
    for i, t in enumerate(slots, 1):
        mark = "<= now" if t <= dt else "future"
        print(f"  #{i:2d}  {t.strftime('%H:%M')}  {mark}")


if __name__ == "__main__":
    main()
