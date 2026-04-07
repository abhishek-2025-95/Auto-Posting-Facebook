#!/usr/bin/env python3
"""Print the next scheduled post time (IST). Run from project folder."""
import schedule
from datetime import datetime
from monetization_optimized_schedule import get_optimal_posting_times

def run_image_cycle():
    pass  # dummy for schedule

# Setup same schedule as test_image_post_then_schedule
for time_str in get_optimal_posting_times().keys():
    schedule.every().day.at(time_str).do(run_image_cycle)
schedule.every(144).minutes.do(run_image_cycle)

next_times = sorted(t for j in schedule.get_jobs() for t in (j.next_run,) if t)
now = datetime.now()
next_run = min((t for t in next_times if t >= now), default=None) if next_times else None

if next_run:
    print("Next post (IST):", next_run.strftime("%Y-%m-%d %H:%M:%S"))
else:
    print("No schedule loaded.")
