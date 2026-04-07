"""IST (Asia/Kolkata) schedule: same local clock windows as ET mode. Run: python tests/test_posting_schedule_ist.py"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Must be set before config + posting_schedule import
os.environ["POSTING_SCHEDULE_TIMEZONE"] = "IST"

from datetime import date, datetime  # noqa: E402

from zoneinfo import ZoneInfo  # noqa: E402

import posting_schedule as ps  # noqa: E402


def main() -> int:
    tz = ps._get_schedule_tz()
    assert getattr(tz, "key", None) == "Asia/Kolkata"
    t = datetime(2026, 6, 15, 7, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert ps.is_within_us_et_window(t) is True
    d = date(2026, 6, 15)
    slots = ps.daily_slot_times_et(d, 10)
    assert (slots[0].hour, slots[0].minute) == (7, 30)
    assert ps.schedule_short_tz_label() == "IST"
    print("posting_schedule IST tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
