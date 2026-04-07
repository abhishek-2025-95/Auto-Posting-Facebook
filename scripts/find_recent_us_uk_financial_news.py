#!/usr/bin/env python3
"""
Recent US/UK financial stories from reputed RSS (finance feeds) + optional Newsdata,
filtered by publish time. Wider pool than ``get_trending_news()`` (no breaking-headline shrink).

Usage (from project root):
  python scripts/find_recent_us_uk_financial_news.py
  python scripts/find_recent_us_uk_financial_news.py --hours 2 --limit 12
  python scripts/find_recent_us_uk_financial_news.py --require-breaking  # stricter, fewer hits
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _article_dt(article: dict) -> datetime | None:
    raw = article.get("publishedAt") or article.get("pubDate") or article.get("published_at") or ""
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    try:
        if raw.endswith("Z"):
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if len(raw) >= 19 and raw[10] in "T ":
            chunk = raw[:19].replace(" ", "T")
            dt = datetime.fromisoformat(chunk)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        pass
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _build_reputed_finance_pool() -> list[dict]:
    """Same outlets as the app RSS path; reputed + markets text filter (not breaking-headline gate)."""
    from news_fetcher import (
        _source_is_reputed_finance_outlet,
        article_matches_markets_us_europe,
    )
    from reputed_rss_fetcher import get_reputed_rss_news

    items: list[dict] = []
    items.extend(get_reputed_rss_news(finance_focus=True) or [])
    try:
        from news_fetcher import get_news_api_us_europe

        items.extend(get_news_api_us_europe() or [])
    except Exception:
        pass

    seen: set[str] = set()
    out: list[dict] = []
    for a in items:
        if not a.get("title") or not a.get("url"):
            continue
        if not _source_is_reputed_finance_outlet(a.get("source", "")):
            continue
        if not article_matches_markets_us_europe(a, geo_required=False):
            continue
        k = (a.get("title") or "")[:120].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(a)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Recent US/UK financial news (reputed pool, time-filtered).")
    p.add_argument("--hours", type=float, default=2.0, help="Max age in hours (default 2)")
    p.add_argument("--limit", type=int, default=15, help="Max rows to print")
    p.add_argument(
        "--relax-hours",
        type=float,
        default=8.0,
        help="If no hits in --hours, retry with this window (0 = disable)",
    )
    p.add_argument(
        "--require-breaking",
        action="store_true",
        help="Require breaking-style / market-moving headline heuristics (stricter)",
    )
    args = p.parse_args()

    from enhanced_news_diversity import _article_is_us_or_uk

    try:
        from news_fetcher import _headline_is_breaking_finance
    except ImportError:
        _headline_is_breaking_finance = None  # type: ignore

    pool = _build_reputed_finance_pool()

    def collect(hours: float) -> list[tuple[datetime, dict, bool]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows: list[tuple[datetime, dict, bool]] = []
        for a in pool:
            if not _article_is_us_or_uk(a):
                continue
            dt = _article_dt(a)
            if dt is None:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            if dt < cutoff:
                continue
            breaking = False
            if _headline_is_breaking_finance:
                breaking = _headline_is_breaking_finance(
                    a.get("title") or "", a.get("description") or ""
                )
            if args.require_breaking and not breaking:
                continue
            rows.append((dt, a, breaking))
        rows.sort(key=lambda x: (x[2], x[0]), reverse=True)
        return rows

    hits = collect(args.hours)
    used_window = args.hours
    if not hits and args.relax_hours > args.hours:
        print(f"No items in last {args.hours}h; retrying last {args.relax_hours}h...\n")
        hits = collect(args.relax_hours)
        used_window = args.relax_hours

    if not hits:
        print(
            f"No matching articles (reputed finance pool: {len(pool)} items, "
            f"US/UK + time window {used_window}h"
            f"{' + breaking filter' if args.require_breaking else ''})."
        )
        return 1

    print(
        f"Reputed US/UK financial — newest first "
        f"(within ~{used_window}h; breaking-style rows marked [MARKET-MOVING])\n"
    )
    for i, (dt, a, brk) in enumerate(hits[: args.limit], 1):
        age_m = (datetime.now(timezone.utc) - dt).total_seconds() / 60.0
        tag = "[MARKET-MOVING] " if brk else ""
        print(f"{i}. {tag}[{dt.strftime('%Y-%m-%d %H:%M')} UTC] (~{age_m:.0f} min ago)")
        print(f"   {a.get('title', '')}")
        print(f"   {a.get('source', '')} | {a.get('url', '')}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
