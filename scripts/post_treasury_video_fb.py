#!/usr/bin/env python3
"""One-shot: post Treasury explainer MP4 + Option A caption (with emojis) to the configured Facebook Page."""
from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_DEFAULT_VIDEO = os.path.join(
    _ROOT,
    "cursor_video_work_treasury_auctions",
    "final_premium_pycaps.mp4",
)

CAPTION = """Why are Treasury auctions suddenly in the spotlight—and why should you care if you're in the US *or* Europe? 🇺🇸 🇪🇺

Washington doesn't run on vibes: it funds the government partly through **scheduled auctions** of bills, notes, and bonds. 📜 When **demand looks thin**, markets start asking a hard question: **Will the U.S. need to pay higher yields to place that debt?** 📊

That matters everywhere:

• **US:** Yields feed into **mortgages**, **credit cards**, **corporate borrowing**, and the **cost of carrying large deficits**. 🏠 💳
• **EU / UK:** Global rates and **risk appetite** often move together. When the "risk-free" benchmark reprices, it ripples through **equities**, **credit spreads**, and **FX**—including how investors treat the **dollar** vs **euro / sterling**. 💶 📈

**Geopolitical stress** (headlines around conflict and uncertainty) can push money toward **safety**—but also make investors **pickier about duration and risk**, which shows up in auctions and volatility. ⚠️🛡️

**What we're watching next:** the **next Treasury auctions**, **moves in yields**, **Fed guidance**, and **energy / war headlines**. 👀 Until uncertainty fades, this bundle can drive **sharp, fast market moves**—not just "inside baseball" for bond traders.

**If you found this useful:** 💾 save it, share it with someone who's trying to understand *why* rates and markets move, and tell us in the comments—**are you more worried about inflation, recession, or geopolitical shock right now?** 💬

#Economy #Markets #Bonds #Treasury #Investing"""


def main() -> int:
    p = argparse.ArgumentParser(description="Post Treasury explainer video to Facebook Page (from .env tokens).")
    p.add_argument(
        "--video",
        default=_DEFAULT_VIDEO,
        help=f"Path to MP4 (default: {_DEFAULT_VIDEO})",
    )
    args = p.parse_args()
    video = os.path.abspath(args.video)

    from config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID
    from facebook_api import post_to_facebook_page

    if not FACEBOOK_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
        print(
            "Missing FACEBOOK_ACCESS_TOKEN / FACEBOOK_PAGE_ID (or PAGE_ACCESS_TOKEN / PAGE_ID) in .env.",
            file=sys.stderr,
        )
        return 1
    if not os.path.isfile(video):
        print(f"Video not found: {video}", file=sys.stderr)
        print("Render the pack first, or pass --video path\\to\\your.mp4", file=sys.stderr)
        return 1
    # Video already includes on-frame AI label + logo from branding pipeline
    ok = post_to_facebook_page(CAPTION, video, ai_label_already_applied=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
