"""Unit checks for posting_schedule (US/ET windows + daily cap logic). Run: python tests/test_posting_schedule.py"""
from __future__ import annotations

import sys
from datetime import date, datetime

# Project root on path
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from zoneinfo import ZoneInfo

import posting_schedule as ps


def _et(y, mo, d, h, mi, s=0):
    return datetime(y, mo, d, h, mi, s, tzinfo=ZoneInfo("America/New_York"))


def test_window_edges():
    # Morning 7:00–9:00 exclusive end
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 6, 59, 59)) is False
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 7, 0, 0)) is True
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 8, 59, 59)) is True
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 9, 0, 0)) is False
    # Lunch
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 12, 0, 0)) is True
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 12, 59, 59)) is True
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 13, 0, 0)) is False
    # Evening 19:00–22:00 exclusive
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 18, 59, 59)) is False
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 19, 0, 0)) is True
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 21, 59, 59)) is True
    assert ps.is_within_us_et_window(_et(2026, 6, 15, 22, 0, 0)) is False


def test_next_window_start():
    # 10:30 ET -> next is noon same day
    t = _et(2026, 1, 5, 10, 30, 0)
    n = ps.next_window_start(t)
    assert n == _et(2026, 1, 5, 12, 0, 0)
    # 22:30 ET -> next day 7:00
    t2 = _et(2026, 1, 5, 22, 30, 0)
    n2 = ps.next_window_start(t2)
    assert n2 == _et(2026, 1, 6, 7, 0, 0)


def test_seconds_until_can_post_returns_float():
    w = ps.seconds_until_can_post(10)
    assert isinstance(w, float)
    assert w >= 0.0


def test_allocate_ten_posts():
    assert ps._allocate_posts_across_windows(10) == [3, 2, 5]


def _hm(t):
    return (t.hour, t.minute)


def test_daily_slots_ten_posts():
    """3 morning + 2 lunch + 5 evening, evenly spaced inside each window."""
    d = date(2026, 6, 15)
    slots = ps.daily_slot_times_et(d, 10)
    assert len(slots) == 10
    assert _hm(slots[0]) == (7, 30) and _hm(slots[1]) == (8, 0) and _hm(slots[2]) == (8, 30)
    assert _hm(slots[3]) == (12, 20) and _hm(slots[4]) == (12, 40)
    assert _hm(slots[5]) == (19, 30) and _hm(slots[6]) == (20, 0) and _hm(slots[7]) == (20, 30)
    assert _hm(slots[8]) == (21, 0) and _hm(slots[9]) == (21, 30)


def main():
    test_window_edges()
    test_next_window_start()
    test_seconds_until_can_post_returns_float()
    test_allocate_ten_posts()
    test_daily_slots_ten_posts()
    lines = ps.schedule_summary_lines(10)
    assert len(lines) >= 3
    print("posting_schedule tests: OK")
    print(lines[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
