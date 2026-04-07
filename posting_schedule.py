"""
Posting windows + daily post cap for run_continuous_posts.

Default: **US Eastern** (`America/New_York` — **EST/EDT** handled automatically). Windows: 07:00–09:00, 12:00–13:00, 19:00–22:00 in that zone.

Optional: set **POSTING_SCHEDULE_TIMEZONE** in `.env` only if you need another zone (e.g. `IST` for India-local hours; US audience → leave unset or use `EST` / `America/New_York`).

Default: up to POSTS_PER_DAY attempts are spread with **evenly spaced slot times** inside each
window; counts per window follow window length (largest remainder). Example for 10 posts: 3 morning,
2 lunch, 5 evening (~7:30/8:00/8:30, 12:20/12:40, 7:30–9:30 PM local).

Default: **slot times only** (config POSTING_SCHEDULE_SLOTS_ONLY=true). Flood env vars are ignored unless you set POSTING_SCHEDULE_SLOTS_ONLY=0.

If posts are **missed** (fewer posts than slot times that have already passed), the next attempt is **immediate** — no waiting for a posting window to open.

POSTING_SCHEDULE_FLOOD_WINDOWS (only if SLOTS_ONLY=0):
  unset / 0 / false — evenly spaced slots in every window
  1 / true / all — flood (any time) in all windows
  morning / am — flood only 7:00–9:00 local for the **morning share** of posts; lunch & evening use slot times

Requires: Python 3.9+ zoneinfo; on Windows install `tzdata` if timezones fail.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore

import config as _config

_STATE_FILENAME = "posting_schedule_state.json"

# (start_h, start_m, end_h, end_m) — end is exclusive (e.g. 9,0 = through 08:59:59)
_ET_WINDOWS = (
    (7, 0, 9, 0),
    (12, 0, 13, 0),
    (19, 0, 22, 0),
)


def _state_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), _STATE_FILENAME)


def _get_schedule_tz():
    if ZoneInfo is None:
        raise RuntimeError("zoneinfo not available; use Python 3.9+ and pip install tzdata on Windows")
    name = getattr(_config, "POSTING_SCHEDULE_TIMEZONE", "America/New_York")
    try:
        return ZoneInfo(name)
    except Exception as e:
        raise RuntimeError(
            f"Invalid POSTING_SCHEDULE_TIMEZONE={name!r} (check .env). Original error: {e}"
        ) from e


def schedule_short_tz_label() -> str:
    """Short label for logs (ET, IST, …)."""
    z = getattr(_config, "POSTING_SCHEDULE_TIMEZONE", "America/New_York")
    if z == "America/New_York":
        return "ET"
    if z == "Asia/Kolkata":
        return "IST"
    return z.split("/")[-1].replace("_", " ")


def now_et() -> datetime:
    """Current time in the configured posting timezone (name kept for backward compatibility)."""
    return datetime.now(tz=_get_schedule_tz())


def _flood_mode() -> str:
    """none | all | morning — flood is ignored when config POSTING_SCHEDULE_SLOTS_ONLY is True (default)."""
    if getattr(_config, "POSTING_SCHEDULE_SLOTS_ONLY", True):
        return "none"
    v = os.environ.get("POSTING_SCHEDULE_FLOOD_WINDOWS", "").strip().lower()
    if v in ("1", "true", "yes", "on", "all"):
        return "all"
    if v in ("morning", "am", "7-9"):
        return "morning"
    return "none"


def _schedule_uses_slots() -> bool:
    """True only when every window uses slot timing (no flood at all)."""
    return _flood_mode() == "none"


def _is_morning_schedule_window(dt_local: datetime) -> bool:
    h, m, s = dt_local.hour, dt_local.minute, dt_local.second
    return _seconds_in_window(_ET_WINDOWS[0], h, m, s)


def _is_morning_et_window(dt_et: datetime) -> bool:
    """Deprecated name; same as _is_morning_schedule_window."""
    return _is_morning_schedule_window(dt_et)


def _morning_start_local(d: date) -> datetime:
    return _window_start_datetime(d, _ET_WINDOWS[0])


def _morning_start_et(d: date) -> datetime:
    return _morning_start_local(d)


def _seconds_in_window(w, h: int, m: int, s: int) -> bool:
    sh, sm, eh, em = w
    cur = h * 3600 + m * 60 + s
    start = sh * 3600 + sm * 60
    end = eh * 3600 + em * 60
    return start <= cur < end


def is_within_us_et_window(dt_et: datetime | None = None) -> bool:
    """True if local time (in POSTING_SCHEDULE_TIMEZONE) is inside a posting window."""
    dt = dt_et or now_et()
    h, m, s = dt.hour, dt.minute, dt.second
    return any(_seconds_in_window(w, h, m, s) for w in _ET_WINDOWS)


def _window_start_datetime(d: date, w) -> datetime:
    sh, sm, _, _ = w
    tz = _get_schedule_tz()
    return datetime(d.year, d.month, d.day, sh, sm, 0, tzinfo=tz)


def next_window_start(from_dt: datetime) -> datetime:
    """Earliest datetime >= from_dt when a posting window opens (may equal from_dt if already at an open edge)."""
    tz = from_dt.tzinfo or _get_schedule_tz()
    if from_dt.tzinfo is None:
        from_dt = from_dt.replace(tzinfo=tz)
    d = from_dt.date()
    for _ in range(8):
        for w in _ET_WINDOWS:
            start = _window_start_datetime(d, w)
            if start >= from_dt:
                return start
        d = d + timedelta(days=1)
    return _window_start_datetime(from_dt.date() + timedelta(days=1), _ET_WINDOWS[0])


def _window_duration_seconds(w) -> float:
    sh, sm, eh, em = w
    return float((eh * 60 + em) - (sh * 60 + sm)) * 60.0


def _allocate_posts_across_windows(n_posts: int) -> list[int]:
    """Largest-remainder allocation by window length (minutes)."""
    durs = [_window_duration_seconds(w) / 60.0 for w in _ET_WINDOWS]
    total = sum(durs)
    if n_posts <= 0:
        return [0] * len(_ET_WINDOWS)
    exact = [n_posts * d / total for d in durs]
    counts = [int(x) for x in exact]
    rem = n_posts - sum(counts)
    order = sorted(range(len(_ET_WINDOWS)), key=lambda i: exact[i] - counts[i], reverse=True)
    for k in range(rem):
        counts[order[k]] += 1
    return counts


def _evenly_spaced_slots(day: date, w, n: int) -> list[datetime]:
    """n times strictly between window start and end (same spacing as (i+1)/(n+1))."""
    if n <= 0:
        return []
    sh, sm, eh, em = w
    tz = _get_schedule_tz()
    start = datetime(day.year, day.month, day.day, sh, sm, 0, tzinfo=tz)
    end = datetime(day.year, day.month, day.day, eh, em, 0, tzinfo=tz)
    span = (end - start).total_seconds()
    out = []
    for i in range(n):
        off = (i + 1) / (n + 1) * span
        out.append(start + timedelta(seconds=off))
    return out


def daily_slot_times_et(day: date, posts_per_day_limit: int) -> list[datetime]:
    """
    All target slot datetimes for this schedule-local calendar day, sorted chronologically.
    posts_per_day_limit is split across windows by length; each window's posts are evenly spaced inside it.
    (Function name kept for backward compatibility.)
    """
    alloc = _allocate_posts_across_windows(posts_per_day_limit)
    slots: list[datetime] = []
    for w, n in zip(_ET_WINDOWS, alloc):
        slots.extend(_evenly_spaced_slots(day, w, n))
    slots.sort()
    return slots


def format_daily_slot_table(day: date, posts_per_day_limit: int) -> list[str]:
    """Human-readable lines for docs / startup (schedule local time)."""
    lab = schedule_short_tz_label()
    alloc = _allocate_posts_across_windows(posts_per_day_limit)
    lines = [
        f"  Slot plan: {alloc[0]} morning, {alloc[1]} lunch, {alloc[2]} evening "
        f"(total {posts_per_day_limit}, proportional to window length).",
    ]
    slots = daily_slot_times_et(day, posts_per_day_limit)
    for i, t in enumerate(slots, start=1):
        lines.append(f"    #{i:2d}  {t.strftime('%Y-%m-%d %H:%M')} {lab}")
    return lines


def load_daily_count() -> tuple[str, int]:
    """Return (date_et_iso, successful_posts_that_day)."""
    path = _state_path()
    today = now_et().date().isoformat()
    if not os.path.isfile(path):
        return today, 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        d = str(data.get("date_et", ""))
        c = int(data.get("posts_count", 0))
        if d != today:
            return today, 0
        return today, c
    except Exception:
        return today, 0


def record_successful_post() -> None:
    """Call after a Facebook post succeeded (counts toward daily cap)."""
    path = _state_path()
    today = now_et().date().isoformat()
    cur = 0
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if str(data.get("date_et")) == today:
                cur = int(data.get("posts_count", 0))
        except Exception:
            pass
    new_count = cur + 1
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"date_et": today, "posts_count": new_count}, f, indent=0)
    except Exception as e:
        print(f"[WARN] Could not save posting_schedule_state.json: {e}", flush=True)


def _seconds_until_can_post_flood_windows(posts_per_day_limit: int) -> float:
    """Original behavior: post anytime inside a window until cap."""
    dt = now_et()
    _, count = load_daily_count()
    in_win = is_within_us_et_window(dt)
    tz = dt.tzinfo

    if in_win and count < posts_per_day_limit:
        return 0.0

    if count >= posts_per_day_limit:
        tomorrow = dt.date() + timedelta(days=1)
        next_open = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7, 0, 0, tzinfo=tz)
        return max(1.0, (next_open - dt).total_seconds())

    nxt = next_window_start(dt)
    return max(1.0, (nxt - dt).total_seconds())


def _seconds_until_can_post_slots_core(dt: datetime, count: int, posts_per_day_limit: int) -> float:
    """Slot timing for lunch/evening (and full day when mode=none)."""
    tz = dt.tzinfo

    if count >= posts_per_day_limit:
        tomorrow = dt.date() + timedelta(days=1)
        slots_tmr = daily_slot_times_et(tomorrow, posts_per_day_limit)
        if not slots_tmr:
            next_open = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7, 0, 0, tzinfo=tz)
            return max(1.0, (next_open - dt).total_seconds())
        first = slots_tmr[0]
        return max(1.0, (first - dt).total_seconds())

    slots_today = daily_slot_times_et(dt.date(), posts_per_day_limit)
    if not slots_today or count >= len(slots_today):
        tomorrow = dt.date() + timedelta(days=1)
        slots_tmr = daily_slot_times_et(tomorrow, posts_per_day_limit)
        target = slots_tmr[0] if slots_tmr else datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7, 0, 0, tzinfo=tz)
        return max(1.0, (target - dt).total_seconds())

    required = slots_today[count]

    # Catch-up: do NOT wait for a posting window. If fewer posts than slot times
    # already passed today, post as soon as possible (even outside 7–9 / 12–1 / 7–10 ET).
    due_now = sum(1 for t in slots_today if t <= dt)
    if count < due_now:
        return 0.0

    # On track: wait until the next slot timestamp (may be outside a window until then).
    if dt < required:
        return max(1.0, (required - dt).total_seconds())

    # At/after scheduled slot for this post index — go now (no window gate).
    return 0.0


def seconds_until_can_post(posts_per_day_limit: int) -> float:
    """
    Seconds to sleep before we should attempt another cycle (0 = can try now).
    Slot mode: post #k at/after slot times. Flood all: any time in window.
    Morning flood: 7:00–9:00 local only for the **first N** posts (N = morning allocation, e.g. 3/10); post N+1 onward uses normal slot times (lunch/evening).
    """
    dt = now_et()
    _, count = load_daily_count()
    mode = _flood_mode()

    if mode == "all":
        return _seconds_until_can_post_flood_windows(posts_per_day_limit)

    if mode == "morning":
        if count >= posts_per_day_limit:
            tomorrow = dt.date() + timedelta(days=1)
            tz = dt.tzinfo
            next_open = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7, 0, 0, tzinfo=tz)
            return max(1.0, (next_open - dt).total_seconds())
        alloc = _allocate_posts_across_windows(posts_per_day_limit)
        morning_quota = int(alloc[0]) if alloc else 0
        # Flood only while count < morning_quota AND inside 7:00–9:00; then slot discipline for the rest.
        if morning_quota > 0 and count < morning_quota and _is_morning_schedule_window(dt):
            return 0.0
        ms = _morning_start_local(dt.date())
        if morning_quota > 0 and count < morning_quota and dt < ms:
            return max(1.0, (ms - dt).total_seconds())
        return _seconds_until_can_post_slots_core(dt, count, posts_per_day_limit)

    return _seconds_until_can_post_slots_core(dt, count, posts_per_day_limit)


def wait_until_allowed_post_slot(posts_per_day_limit: int, chunk_seconds: int = 60) -> None:
    """
    Block until allowed to attempt a post (slot times + daily cap; missed posts = no window wait).
    Sleeps in chunks for Ctrl+C.
    """
    lab = schedule_short_tz_label()
    win_desc = f"7-9am, 12-1pm, 7-10pm {lab}"
    announced = False
    while True:
        wait = seconds_until_can_post(posts_per_day_limit)
        if wait <= 0:
            return
        dt = now_et()
        _, cnt = load_daily_count()
        if not announced:
            if cnt >= posts_per_day_limit:
                print(
                    f"\n[SCHEDULE] Daily cap reached ({cnt}/{posts_per_day_limit} posts, {lab} date {dt.date().isoformat()}). "
                    f"Next window (~{int(wait // 60)} min). Ctrl+C to stop.",
                    flush=True,
                )
            elif _flood_mode() == "morning" and cnt < posts_per_day_limit:
                ms = _morning_start_local(dt.date())
                if dt < ms:
                    print(
                        f"\n[SCHEDULE] Morning flood mode: waiting for 7:00 AM {lab} (now {dt.strftime('%H:%M:%S')} {lab}). "
                        f"Ctrl+C to stop.",
                        flush=True,
                    )
                else:
                    slots = daily_slot_times_et(dt.date(), posts_per_day_limit)
                    need = slots[cnt] if cnt < len(slots) else None
                    if need and dt < need:
                        print(
                            f"\n[SCHEDULE] Waiting for post #{cnt + 1} slot at {need.strftime('%H:%M')} {lab} "
                            f"(now {dt.strftime('%H:%M:%S')}). Ctrl+C to stop.",
                            flush=True,
                        )
                    else:
                        nxt = next_window_start(dt)
                        print(
                            f"\n[SCHEDULE] Outside posting windows ({win_desc}). "
                            f"Now {lab}: {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}. Next open: {nxt.strftime('%Y-%m-%d %H:%M %Z')}.",
                            flush=True,
                        )
            elif _schedule_uses_slots() and cnt < posts_per_day_limit:
                slots = daily_slot_times_et(dt.date(), posts_per_day_limit)
                need = slots[cnt] if cnt < len(slots) else None
                if need and dt < need:
                    print(
                        f"\n[SCHEDULE] Waiting for post #{cnt + 1} slot at {need.strftime('%H:%M')} {lab} "
                        f"(now {dt.strftime('%H:%M:%S')}). Ctrl+C to stop.",
                        flush=True,
                    )
                else:
                    nxt = next_window_start(dt)
                    print(
                        f"\n[SCHEDULE] Outside posting windows ({win_desc}). "
                        f"Now {lab}: {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}. Next open: {nxt.strftime('%Y-%m-%d %H:%M %Z')}.",
                        flush=True,
                    )
            else:
                nxt = next_window_start(dt)
                print(
                    f"\n[SCHEDULE] Outside posting windows ({win_desc}). "
                    f"Now {lab}: {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}. Next open: {nxt.strftime('%Y-%m-%d %H:%M %Z')}.",
                    flush=True,
                )
            announced = True
        sleep_t = min(max(1, int(wait)), chunk_seconds)
        time.sleep(sleep_t)


def schedule_summary_lines(posts_per_day_limit: int) -> list[str]:
    dt = now_et()
    lab = schedule_short_tz_label()
    tz_name = getattr(_config, "POSTING_SCHEDULE_TIMEZONE", "America/New_York")
    _, cnt = load_daily_count()
    fm = _flood_mode()
    if fm == "all":
        mode = "flood all windows (POSTING_SCHEDULE_FLOOD_WINDOWS=1)"
    elif fm == "morning":
        aq = _allocate_posts_across_windows(posts_per_day_limit)[0]
        mode = (
            f"morning flood 7-9 {lab} for first {aq} posts, then slots "
            f"(POSTING_SCHEDULE_FLOOD_WINDOWS=morning)"
        )
    else:
        mode = "slots + immediate catch-up when behind (ignores windows)"
    lines = [
        f"  Schedule: {tz_name} ({lab}) - 7:00-9:00, 12:00-13:00, 19:00-22:00 local | max {posts_per_day_limit}/day | mode: {mode}.",
        f"  Now {lab}: {dt.strftime('%Y-%m-%d %H:%M:%S')} | In window: {is_within_us_et_window(dt)} | Posts today ({lab}): {cnt}/{posts_per_day_limit}",
    ]
    if fm != "all":
        alloc = _allocate_posts_across_windows(posts_per_day_limit)
        lines.append(
            f"  Posts per window today: morning {alloc[0]}, lunch {alloc[1]}, evening {alloc[2]} (by window length)."
        )
        slots = daily_slot_times_et(dt.date(), posts_per_day_limit)
        if slots:
            preview = ", ".join(t.strftime("%H:%M") for t in slots[:6])
            if len(slots) > 6:
                preview += ", ..."
            if fm == "morning":
                lines.append(f"  Slot times apply after 9:00 AM {lab} (lunch/evening); morning 7-9 is flood: {preview}")
            else:
                lines.append(f"  Today's slot times ({lab}): {preview}")
    return lines
