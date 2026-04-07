#!/usr/bin/env python3
"""
Facebook **image** posts: **Cursor chat image tool only** (locked in ``config.py`` — no Z-Image, no PIL/API placeholders).
Write prompt to ``CURSOR_POST_IMAGE_PROMPT.txt``, save PNG/JPEG to ``CURSOR_POST_IMAGE_INBOUND``.

Minimal overlay via ``ULTRA_MINIMAL_IMAGE_OVERLAY``; caption + news link.

Post **one** image on start (respects US/ET windows + daily cap when enabled), then loops like ``run_continuous_posts.py``.

  python run_continuous_image_posts.py
  python run_continuous_image_posts.py --once   # single post, exit

Requires: PAGE_ID, PAGE_ACCESS_TOKEN, NEWS flow, and the Cursor image tool to produce inbound stills.
"""
from __future__ import annotations

import atexit
import gc
import os
import sys
import time
import traceback
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

warnings.filterwarnings("ignore", message=".*allow_in_graph.*", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*nonstrict_trace.*", category=FutureWarning)

os.environ.setdefault("USE_TORCH", "1")
os.environ.setdefault("USE_TF", "0")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

import protobuf_runtime_shim  # noqa: F401

from enhanced_news_diversity import (
    is_duplicate_on_facebook,
    pick_freshest_postable_article,
    save_posted_article,
)
from content_generator import (
    generate_facebook_caption,
    generate_image_prompt_with_gemini,
    generate_post_image_fallback,
)
from facebook_api import post_comment_on_post, post_to_facebook_page, test_facebook_connection

try:
    from config import (
        CONTINUOUS_POST_COOLDOWN_SECONDS,
        CHECK_FACEBOOK_FOR_DUPLICATES,
        ENABLE_US_ET_POSTING_WINDOWS,
        FACEBOOK_DUPLICATE_CHECK_LIMIT,
        FACEBOOK_DUPLICATE_SIMILARITY,
        POSTS_PER_DAY,
        RUN_CAPTION_PROMPT_SEQUENTIAL,
        TOPIC_THEME,
    )
except ImportError:
    CONTINUOUS_POST_COOLDOWN_SECONDS = 30
    CHECK_FACEBOOK_FOR_DUPLICATES = True
    ENABLE_US_ET_POSTING_WINDOWS = False
    FACEBOOK_DUPLICATE_CHECK_LIMIT = 50
    FACEBOOK_DUPLICATE_SIMILARITY = 0.65
    POSTS_PER_DAY = 10
    RUN_CAPTION_PROMPT_SEQUENTIAL = True
    TOPIC_THEME = None

SKIP_FACEBOOK_POST = False
_LOCK_PATH = os.path.join(_BASE, ".run_continuous_image_posts.lock")


def _memory_cleanup():
    gc.collect()
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except Exception:
        pass
    gc.collect()


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    try:
        if os.name == "nt":
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _release_lock():
    try:
        if os.path.exists(_LOCK_PATH):
            with open(_LOCK_PATH, "r", encoding="utf-8") as f:
                owner = int((f.read() or "0").strip())
            if owner == os.getpid():
                os.remove(_LOCK_PATH)
    except Exception:
        pass


def _acquire_single_instance_lock() -> bool:
    if os.path.exists(_LOCK_PATH):
        try:
            with open(_LOCK_PATH, "r", encoding="utf-8") as f:
                existing_pid = int((f.read() or "0").strip())
        except Exception:
            existing_pid = 0
        if _pid_is_alive(existing_pid):
            print(
                f"[LOCK] Another run_continuous_image_posts.py is already running (PID {existing_pid}). Exiting.",
                flush=True,
            )
            return False
        try:
            os.remove(_LOCK_PATH)
        except Exception:
            pass
    with open(_LOCK_PATH, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    atexit.register(_release_lock)
    return True


def run_one_image_post_cycle() -> bool:
    print("\n" + "=" * 60)
    print(f"IMAGE POST CYCLE (Z-Image local) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        print("\nStep 1: Fetching viral news (reputed + age window; no stale fallback)...")
        viral_article = pick_freshest_postable_article()
        if not viral_article:
            print("No fresh articles. Skipping this cycle.")
            _memory_cleanup()
            return False

        print(f"Selected: {viral_article.get('title', '')[:70]}...")

        print("\nStep 2: Caption + image prompt...")
        if RUN_CAPTION_PROMPT_SEQUENTIAL:
            caption = generate_facebook_caption(viral_article, topic_theme=TOPIC_THEME)
            image_prompt = generate_image_prompt_with_gemini(viral_article)
        else:
            with ThreadPoolExecutor(max_workers=2) as ex:
                f1 = ex.submit(generate_facebook_caption, viral_article, None, TOPIC_THEME)
                f2 = ex.submit(generate_image_prompt_with_gemini, viral_article)
                caption = f1.result()
                image_prompt = f2.result()

        if not caption:
            print("No caption generated, skipping")
            _memory_cleanup()
            return False

        if SKIP_FACEBOOK_POST:
            print("\nStep 2b: Skipping duplicate check (Facebook not configured).")
        elif not CHECK_FACEBOOK_FOR_DUPLICATES:
            print("\nStep 2b: Duplicate check OFF.")
        elif caption:
            print("\nStep 2b: Checking Facebook for duplicates...")
            if is_duplicate_on_facebook(
                caption,
                limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
                similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
            ):
                print("Duplicate caption vs recent Page posts. Skipping.")
                save_posted_article(viral_article)
                _memory_cleanup()
                return False
            hl = (viral_article.get("title") or "").strip()
            if hl and is_duplicate_on_facebook(
                hl,
                limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
                similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
            ):
                print("Duplicate headline vs recent Page posts. Skipping.")
                save_posted_article(viral_article)
                _memory_cleanup()
                return False

        print("\nStep 3: Post image (Z-Image or Cursor inbound per config) + overlay...")
        image_path = generate_post_image_fallback(viral_article, image_prompt=image_prompt)
        image_path = os.path.abspath(image_path) if image_path else None
        if not image_path or not os.path.isfile(image_path):
            print("Image generation failed or file missing. Skipping.")
            _memory_cleanup()
            return False
        print(f"Image ready: {image_path}")

        try:
            from design_config import APPROVE_BEFORE_POST, PREVIEW_IMAGE_PATH
        except ImportError:
            APPROVE_BEFORE_POST = False
            PREVIEW_IMAGE_PATH = os.path.join(_BASE, "approval_preview.jpg")
        if APPROVE_BEFORE_POST:
            import shutil
            shutil.copy2(image_path, PREVIEW_IMAGE_PATH)
            print("\nAPPROVE_BEFORE_POST is True — preview only, no Facebook post.")
            print(f"  Preview: {PREVIEW_IMAGE_PATH}")
            _memory_cleanup()
            return False

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

        posted_to_facebook = False
        post_id = None
        if SKIP_FACEBOOK_POST:
            print("\nStep 4: Skipping Facebook post (SKIP_FACEBOOK_POST / DRY_RUN or no token).")
            print(f"  Image file: {image_path}")
        else:
            print("\nStep 4: Posting photo to Facebook...")
            result = post_to_facebook_page(caption, image_path, ai_label_already_applied=True)
            posted_to_facebook = bool(result)
            post_id = result if posted_to_facebook and isinstance(result, str) else None

        if posted_to_facebook and post_id:
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
            if posted_to_facebook and image_path and os.path.isfile(image_path):
                os.remove(image_path)
                print(f"Cleaned up: {image_path}")
        except OSError:
            pass

        if posted_to_facebook:
            print("\nIMAGE POST SUCCESSFUL!")
            save_posted_article(viral_article)
            _memory_cleanup()
            return True
        if SKIP_FACEBOOK_POST:
            print("\nGeneration complete (Facebook post skipped; image left on disk).")
            _memory_cleanup()
            return False
        print("\nPOST FAILED or skipped.")
        _memory_cleanup()
        return False

    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print(f"\nERROR in image cycle: {e}")
        traceback.print_exc()
        _memory_cleanup()
        return False


def main() -> int:
    global SKIP_FACEBOOK_POST
    post_once = "--once" in sys.argv or "-1" in sys.argv

    _env_skip = (os.environ.get("SKIP_FACEBOOK_POST") or os.environ.get("DRY_RUN") or "").strip().lower()
    if _env_skip in ("1", "true", "yes"):
        SKIP_FACEBOOK_POST = True

    if not _acquire_single_instance_lock():
        return 0
    os.chdir(_BASE)

    print("=" * 60)
    print("CONTINUOUS IMAGE POSTING (Cursor image tool + inbound file only — no scripted image fallbacks)")
    print("  Config: ULTRA_MINIMAL_IMAGE_OVERLAY, US/ET schedule")
    print("=" * 60)

    if ENABLE_US_ET_POSTING_WINDOWS:
        try:
            from posting_schedule import schedule_summary_lines
            for line in schedule_summary_lines(POSTS_PER_DAY):
                print(line, flush=True)
        except Exception as e:
            print(f"  [SCHEDULE] {e} — pip install tzdata", flush=True)

    if SKIP_FACEBOOK_POST:
        print("SKIP_FACEBOOK_POST or DRY_RUN is set — generate image only, no Facebook API.", flush=True)
    else:
        for attempt in range(1, 4):
            if test_facebook_connection():
                break
            if attempt < 3:
                print(f"Facebook check failed ({attempt}/3). Retrying in 5s...", flush=True)
                time.sleep(5)
        else:
            print("Facebook connection failed. Running without post (preview / gen only).", flush=True)
            SKIP_FACEBOOK_POST = True

    _schedule_first_cycle = True

    def _wait_schedule_if_enabled():
        nonlocal _schedule_first_cycle
        if not ENABLE_US_ET_POSTING_WINDOWS:
            return
        if _schedule_first_cycle:
            _schedule_first_cycle = False
            try:
                from config import SKIP_US_ET_WAIT_FIRST_IMAGE_POST as _skip_first
            except ImportError:
                _skip_first = False
            if _skip_first:
                print(
                    "[SCHEDULE] First cycle: SKIP_US_ET_WAIT_FIRST_IMAGE_POST — not waiting for ET slot (post now).",
                    flush=True,
                )
                return
        try:
            from posting_schedule import wait_until_allowed_post_slot
            wait_until_allowed_post_slot(POSTS_PER_DAY)
        except Exception as e:
            print(f"[SCHEDULE] Wait skipped ({e}).", flush=True)

    def _record_post_if_enabled(ok: bool):
        if ok and ENABLE_US_ET_POSTING_WINDOWS:
            try:
                from posting_schedule import record_successful_post
                record_successful_post()
            except Exception:
                pass

    print("\n>>> Posting ONE image now...", flush=True)
    _wait_schedule_if_enabled()
    _ok = run_one_image_post_cycle()
    _record_post_if_enabled(_ok)

    if post_once:
        print("\n>>> --once: exiting.", flush=True)
        return 0

    print(f"\n>>> Continuous image mode (cooldown {CONTINUOUS_POST_COOLDOWN_SECONDS}s). Ctrl+C to stop.\n", flush=True)
    try:
        while True:
            _wait_schedule_if_enabled()
            _ok = run_one_image_post_cycle()
            _record_post_if_enabled(_ok)
            _memory_cleanup()
            if CONTINUOUS_POST_COOLDOWN_SECONDS > 0:
                print(f"\nCooldown {CONTINUOUS_POST_COOLDOWN_SECONDS}s...\n", flush=True)
                time.sleep(float(CONTINUOUS_POST_COOLDOWN_SECONDS))
    except KeyboardInterrupt:
        print("\nStopped by user.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
