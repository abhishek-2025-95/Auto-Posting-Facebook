import time
from datetime import datetime
from typing import List, Optional

from .calendar import CalendarItem, run_due_items
from .facebook_poster import FacebookPoster


def run_scheduler(
    poster: FacebookPoster,
    items: List[CalendarItem],
    *,
    interval_seconds: int = 60,
    dry_run: bool = False,
) -> None:
    remaining = list(items)
    while remaining:
        now = datetime.now()
        due = [i for i in remaining if i.when <= now]
        if due:
            run_due_items(poster, due, now=now, dry_run=dry_run)
            # remove due items
            remaining = [i for i in remaining if i.when > now]
        time.sleep(max(5, min(interval_seconds, 300)))



