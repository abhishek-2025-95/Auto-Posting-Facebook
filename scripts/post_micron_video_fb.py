#!/usr/bin/env python3
"""Post Micron explainer FINAL_VIDEO.mp4 + FACEBOOK_CAPTION.txt to the configured Facebook Page."""
from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_PACK = os.path.join(_ROOT, "cursor_video_work_micron_mw")
_DEFAULT_VIDEO = os.path.join(_PACK, "FINAL_VIDEO.mp4")
_DEFAULT_CAPTION = os.path.join(_PACK, "FACEBOOK_CAPTION.txt")


def main() -> int:
    p = argparse.ArgumentParser(description="Post Micron Cursor video + caption to Facebook Page (.env).")
    p.add_argument("--video", default=_DEFAULT_VIDEO, help="Path to MP4")
    p.add_argument("--caption-file", default=_DEFAULT_CAPTION, help="UTF-8 text file (full post body + hashtags)")
    args = p.parse_args()
    video = os.path.abspath(args.video)
    cap_path = os.path.abspath(args.caption_file)

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
        return 1
    if not os.path.isfile(cap_path):
        print(f"Caption file not found: {cap_path}", file=sys.stderr)
        return 1
    caption = open(cap_path, encoding="utf-8").read().strip()
    if not caption:
        print("Caption file is empty.", file=sys.stderr)
        return 1
    ok = post_to_facebook_page(caption, video, ai_label_already_applied=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
