#!/usr/bin/env python3
"""
Prepare + finish one image post when IMAGE_GENERATION_MODE=cursor_only.

  python scripts/agent_post_one_cursor.py prepare   # fetch news, write prompt; exit 2 if inbound missing
  python scripts/agent_post_one_cursor.py finish    # consume inbound, overlay, post to Facebook
  python scripts/agent_post_one_cursor.py finish --no-post   # same, but never call Facebook

  # Or: SKIP_FACEBOOK_POST=1 or DRY_RUN=1 in the environment (applies to prepare + finish).

Set env before imports in your shell, or rely on defaults below (cursor_only + no ET wait).
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_BASE)
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

os.environ.setdefault("IMAGE_GENERATION_MODE", "cursor_only")
os.environ.setdefault("ENABLE_US_ET_POSTING_WINDOWS", "0")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_STATE = os.path.join(_BASE, "._agent_onepost_state.json")


def _skip_facebook_from_env() -> bool:
    for key in ("SKIP_FACEBOOK_POST", "DRY_RUN"):
        v = (os.environ.get(key) or "").strip().lower()
        if v in ("1", "true", "yes"):
            return True
    return False


def _memory_cleanup():
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()


def _pick_article():
    import protobuf_runtime_shim  # noqa: F401
    from enhanced_news_diversity import pick_freshest_postable_article

    return pick_freshest_postable_article()


def _caption_and_prompt(viral_article):
    from config import RUN_CAPTION_PROMPT_SEQUENTIAL, TOPIC_THEME
    from content_generator import generate_facebook_caption, generate_image_prompt_with_gemini

    if RUN_CAPTION_PROMPT_SEQUENTIAL:
        caption = generate_facebook_caption(viral_article, topic_theme=TOPIC_THEME)
        image_prompt = generate_image_prompt_with_gemini(viral_article)
    else:
        with ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(generate_facebook_caption, viral_article, None, TOPIC_THEME)
            f2 = ex.submit(generate_image_prompt_with_gemini, viral_article)
            caption = f1.result()
            image_prompt = f2.result()
    return caption, image_prompt


def _duplicate_ok(caption, viral_article, *, skip_facebook: bool) -> bool:
    from config import (
        CHECK_FACEBOOK_FOR_DUPLICATES,
        FACEBOOK_DUPLICATE_CHECK_LIMIT,
        FACEBOOK_DUPLICATE_SIMILARITY,
    )
    from enhanced_news_diversity import is_duplicate_on_facebook, save_posted_article

    if skip_facebook:
        return True
    if not CHECK_FACEBOOK_FOR_DUPLICATES or not caption:
        return True
    if is_duplicate_on_facebook(
        caption,
        limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
        similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
    ):
        print("Duplicate caption vs recent Page posts. Skipping.")
        save_posted_article(viral_article)
        return False
    hl = (viral_article.get("title") or "").strip()
    if hl and is_duplicate_on_facebook(
        hl,
        limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
        similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
    ):
        print("Duplicate headline vs recent Page posts. Skipping.")
        save_posted_article(viral_article)
        return False
    return True


def _finalize_caption(caption, viral_article) -> str:
    news_url = (viral_article.get("url") or viral_article.get("link") or "").strip()
    try:
        from config import ENABLE_FIRST_COMMENT, NEWS_LINK_IN_FIRST_COMMENT, SHOW_FIRST_COMMENT_LINK_HINT
    except ImportError:
        NEWS_LINK_IN_FIRST_COMMENT = False
        SHOW_FIRST_COMMENT_LINK_HINT = True
        ENABLE_FIRST_COMMENT = True
    if news_url:
        if NEWS_LINK_IN_FIRST_COMMENT and ENABLE_FIRST_COMMENT and SHOW_FIRST_COMMENT_LINK_HINT:
            caption = (caption or "").rstrip() + "\n\n📎 Full story link in our first comment 👇"
        elif NEWS_LINK_IN_FIRST_COMMENT and not ENABLE_FIRST_COMMENT:
            caption = (caption or "").rstrip() + "\n\n" + news_url
        elif not NEWS_LINK_IN_FIRST_COMMENT:
            caption = (caption or "").rstrip() + "\n\n" + news_url
    return caption


def _post_photo(caption, image_path, viral_article, *, skip_facebook: bool) -> bool:
    if skip_facebook:
        print("\n--- Caption (not posted) ---\n")
        print(caption or "")
        print(f"\nImage file (kept on disk): {image_path}")
        print("SKIP_FACEBOOK_POST / --no-post: skipping Facebook API.")
        return True

    from facebook_api import post_comment_on_post, post_to_facebook_page

    result = post_to_facebook_page(caption, image_path, ai_label_already_applied=True)
    success = bool(result)
    post_id = result if success and isinstance(result, str) else None
    news_url = (viral_article.get("url") or viral_article.get("link") or "").strip()
    if success and post_id:
        try:
            from config import (
                ENABLE_FIRST_COMMENT,
                FACEBOOK_ACCESS_TOKEN,
                FACEBOOK_PAGE_ID,
                FIRST_COMMENT_TEMPLATES,
                NEWS_LINK_IN_FIRST_COMMENT,
            )
            import random

            if ENABLE_FIRST_COMMENT and FIRST_COMMENT_TEMPLATES:
                intro = random.choice(FIRST_COMMENT_TEMPLATES)
                if news_url and NEWS_LINK_IN_FIRST_COMMENT:
                    first_comment = intro.rstrip() + "\n\n" + news_url
                else:
                    first_comment = intro
                post_comment_on_post(
                    post_id,
                    first_comment,
                    page_id=FACEBOOK_PAGE_ID,
                    page_access_token=FACEBOOK_ACCESS_TOKEN,
                )
        except Exception as e:
            print(f"First comment: {e}")
    try:
        if image_path and os.path.isfile(image_path):
            os.remove(image_path)
            print(f"Cleaned up: {image_path}")
    except OSError:
        pass
    if success:
        from enhanced_news_diversity import save_posted_article

        save_posted_article(viral_article)
        print("\nIMAGE POST SUCCESSFUL!")
    return success


def cmd_prepare(*, skip_facebook: bool) -> int:
    import protobuf_runtime_shim  # noqa: F401
    from content_generator import generate_post_image_fallback

    print("=== PREPARE (cursor_only) ===", flush=True)
    viral_article = _pick_article()
    if not viral_article:
        print("No fresh articles.")
        _memory_cleanup()
        return 1

    print(f"Selected: {viral_article.get('title', '')[:70]}...", flush=True)
    caption, image_prompt = _caption_and_prompt(viral_article)
    if not caption:
        print("No caption generated.")
        _memory_cleanup()
        return 1
    if not _duplicate_ok(caption, viral_article, skip_facebook=skip_facebook):
        _memory_cleanup()
        return 1

    try:
        from design_config import APPROVE_BEFORE_POST, PREVIEW_IMAGE_PATH
    except ImportError:
        APPROVE_BEFORE_POST = False
        PREVIEW_IMAGE_PATH = os.path.join(_BASE, "approval_preview.jpg")

    with open(_STATE, "w", encoding="utf-8") as f:
        json.dump(
            {"article": viral_article, "caption": caption, "image_prompt": image_prompt},
            f,
            indent=2,
            default=str,
        )
    print(f"Saved state: {_STATE}", flush=True)

    if APPROVE_BEFORE_POST:
        print("APPROVE_BEFORE_POST is True — not generating/posting in finish without your approval flow.")
        _memory_cleanup()
        return 1

    image_path = generate_post_image_fallback(viral_article, image_prompt=image_prompt)
    image_path = os.path.abspath(image_path) if image_path else None
    if image_path and os.path.isfile(image_path):
        caption = _finalize_caption(caption, viral_article)
        ok = _post_photo(caption, image_path, viral_article, skip_facebook=skip_facebook)
        _memory_cleanup()
        try:
            os.remove(_STATE)
        except OSError:
            pass
        return 0 if ok else 1

    print("\nInbound image missing. Generate with Cursor image tool, save to path in CURSOR_POST_IMAGE_PROMPT.txt", flush=True)
    print("Then run: python scripts/agent_post_one_cursor.py finish", flush=True)
    _memory_cleanup()
    return 2


def cmd_finish(*, skip_facebook: bool) -> int:
    import protobuf_runtime_shim  # noqa: F401
    from content_generator import generate_post_image_fallback

    print("=== FINISH (cursor_only) ===", flush=True)
    if not os.path.isfile(_STATE):
        print(f"Missing state file. Run prepare first: {_STATE}")
        return 1
    with open(_STATE, encoding="utf-8") as f:
        state = json.load(f)
    viral_article = state["article"]
    caption = state["caption"]
    image_prompt = state["image_prompt"]

    try:
        from design_config import APPROVE_BEFORE_POST
    except ImportError:
        APPROVE_BEFORE_POST = False
    if APPROVE_BEFORE_POST:
        print("APPROVE_BEFORE_POST is True — abort.")
        return 1

    image_path = generate_post_image_fallback(viral_article, image_prompt=image_prompt)
    image_path = os.path.abspath(image_path) if image_path else None
    if not image_path or not os.path.isfile(image_path):
        print("Image generation failed or file missing.")
        _memory_cleanup()
        return 1

    caption = _finalize_caption(caption, viral_article)
    if not skip_facebook:
        from facebook_api import test_facebook_connection

        if not test_facebook_connection():
            print("Facebook connection failed.")
            _memory_cleanup()
            return 1

    ok = _post_photo(caption, image_path, viral_article, skip_facebook=skip_facebook)
    try:
        os.remove(_STATE)
    except OSError:
        pass
    _memory_cleanup()
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("prepare", "finish"))
    ap.add_argument(
        "--no-post",
        action="store_true",
        help="Generate only: do not call Facebook (same as SKIP_FACEBOOK_POST=1 or DRY_RUN=1).",
    )
    args = ap.parse_args()
    skip_fb = bool(args.no_post) or _skip_facebook_from_env()
    try:
        if args.step == "prepare":
            return cmd_prepare(skip_facebook=skip_fb)
        return cmd_finish(skip_facebook=skip_fb)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
