#!/usr/bin/env python3
"""
Post one image now, then run the image workflow continuously.

Default schedule (config): US/Eastern windows 7–9am, 12–1pm, 7–10pm; max POSTS_PER_DAY (10)/ET day;
evenly spaced slot times inside each window (3+2+5 for 10). Flood disabled by default (POSTING_SCHEDULE_SLOTS_ONLY).
Disable all guards: ENABLE_US_ET_POSTING_WINDOWS=0 in .env.

Each cycle: fetch news -> caption -> generate video -> post to Facebook.
Cooldown between attempts: CONTINUOUS_POST_COOLDOWN_SECONDS. Press Ctrl+C to stop.

Five-scene 18s Cursor videos: use ``scripts/render_manual_cursor_video.py fetch-us-uk-pack`` (Cursor image tool only),
then ``render`` with your five exports — not handled inside this loop.

Fully automated premium pipeline (local images + Kokoro + pycaps + post): ``python scripts/auto_news_cursor_video_post.py``
(see script docstring; uses ``generate_post_image_fallback``, not Cursor UI).
"""
from __future__ import print_function
import sys
import time
import warnings
import atexit

# Quiet noisy HF/transformers FutureWarnings on import (does not hide real tracebacks)
warnings.filterwarnings(
    "ignore",
    message=".*allow_in_graph.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*nonstrict_trace.*",
    category=FutureWarning,
)

import traceback
import gc
from datetime import datetime
import os

# Hugging Face: AUTO enables both torch + TensorFlow; TF pulls protobuf 5+ and breaks with protobuf 3.x + diffusers stub.
# Image gen is PyTorch-only — set before any import of transformers (via content_generator).
os.environ.setdefault("USE_TORCH", "1")
os.environ.setdefault("USE_TF", "0")

# Unbuffered output so logs and errors appear immediately (especially during pipeline load)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass
else:
    try:
        sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 1)
        sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 1)
    except Exception:
        pass

# Ensure project root on path
_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

import protobuf_runtime_shim  # noqa: F401 — before any google.cloud / pb2 (system Python + protobuf 5+)

from enhanced_news_diversity import (
    is_article_posted,
    is_duplicate_on_facebook,
    pick_freshest_postable_article,
    save_posted_article,
)
from content_generator import generate_facebook_caption, generate_post_video
from facebook_api import post_to_facebook_page, post_comment_on_post, test_facebook_connection
def _memory_cleanup():
    """Aggressive cleanup so continuous cycles don't accumulate GPU/CPU memory."""
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

try:
    from config import (
        CONTINUOUS_POST_COOLDOWN_SECONDS,
        CHECK_FACEBOOK_FOR_DUPLICATES,
        FACEBOOK_DUPLICATE_CHECK_LIMIT,
        FACEBOOK_DUPLICATE_SIMILARITY,
        RUN_CAPTION_PROMPT_SEQUENTIAL,
        TOPIC_THEME,
        ENABLE_US_ET_POSTING_WINDOWS,
        POSTS_PER_DAY,
    )
except ImportError:
    CONTINUOUS_POST_COOLDOWN_SECONDS = 30
    CHECK_FACEBOOK_FOR_DUPLICATES = True
    FACEBOOK_DUPLICATE_CHECK_LIMIT = 50
    FACEBOOK_DUPLICATE_SIMILARITY = 0.65
    RUN_CAPTION_PROMPT_SEQUENTIAL = True
    TOPIC_THEME = None
    ENABLE_US_ET_POSTING_WINDOWS = False
    POSTS_PER_DAY = 10

# When True, pipeline still runs (news -> caption -> image -> overlay) but skips posting to Facebook
SKIP_FACEBOOK_POST = False
_LOCK_PATH = os.path.join(_BASE, ".run_continuous_posts.lock")


def _pid_is_alive(pid):
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


def _acquire_single_instance_lock():
    if os.path.exists(_LOCK_PATH):
        try:
            with open(_LOCK_PATH, "r", encoding="utf-8") as f:
                existing_pid = int((f.read() or "0").strip())
        except Exception:
            existing_pid = 0
        if _pid_is_alive(existing_pid):
            print(
                f"[LOCK] Another run_continuous_posts.py is already running (PID {existing_pid}). "
                "Exiting this duplicate instance.",
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


def run_image_cycle():
    """
    One cycle: fetch news -> caption -> generate branded video -> post to Facebook.
    """
    print("\n" + "=" * 60)
    print(f"VIDEO CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Step 1: Get fresh viral news
        print("\nStep 1: Fetching viral news...")
        viral_article = pick_freshest_postable_article()
        if not viral_article:
            print("No fresh articles. Skipping this cycle.")
            _memory_cleanup()
            return False

        print(f"Selected: {viral_article.get('title', '')[:60]}...")

        # Step 2: Caption generation
        print("\nStep 2: Generating caption...")
        caption = generate_facebook_caption(viral_article, topic_theme=TOPIC_THEME)
        if not caption:
            print("No caption generated, skipping")
            _memory_cleanup()
            return False

        # Step 2b: Check Facebook recent posts to avoid duplicate (same/similar news already posted)
        if SKIP_FACEBOOK_POST:
            print("\nStep 2b: Skipping duplicate check (Facebook not configured).")
        elif not CHECK_FACEBOOK_FOR_DUPLICATES:
            print("\nStep 2b: Facebook duplicate check is OFF (set CHECK_FACEBOOK_FOR_DUPLICATES = True in config.py to enable).")
        elif caption:
            print("\nStep 2b: Checking Facebook for duplicate posts (caption + headline)...")
            if is_duplicate_on_facebook(
                caption,
                limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
                similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
            ):
                print("\nDuplicate on Facebook: caption too similar to a recent post. Skipping this article.")
                save_posted_article(viral_article)  # so we don't retry the same story next cycle
                _memory_cleanup()
                return False
            headline_for_check = (viral_article.get("title") or "").strip()
            if headline_for_check and is_duplicate_on_facebook(
                headline_for_check,
                limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
                similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
            ):
                print("\nDuplicate on Facebook: headline too similar to a recent post. Skipping this article.")
                save_posted_article(viral_article)
                _memory_cleanup()
                return False
            print("Step 2b: No duplicate found; continuing to post.")

        # Step 3: Generate branded video
        print("\nStep 3: Generating branded video...")
        video_path = generate_post_video(viral_article)
        video_path = os.path.abspath(video_path) if video_path else None
        if not video_path or not os.path.exists(video_path):
            print("Video generation/branding failed or file missing, skipping cycle.")
            print(f"  Expected path: {os.path.join(_BASE, 'post_video_branded.mp4')}")
            _memory_cleanup()
            return False
        print(f"Video saved: {video_path}")

        # Approval gate (design_config.APPROVE_BEFORE_POST)
        try:
            from design_config import APPROVE_BEFORE_POST, PREVIEW_IMAGE_PATH
        except ImportError:
            APPROVE_BEFORE_POST = False
            PREVIEW_IMAGE_PATH = os.path.join(_BASE, "approval_preview.jpg")
        if APPROVE_BEFORE_POST:
            import shutil
            preview_video_path = os.path.splitext(PREVIEW_IMAGE_PATH)[0] + ".mp4"
            shutil.copy2(video_path, preview_video_path)
            print("\n" + "=" * 60)
            print("PREVIEW ONLY (no post). Set APPROVE_BEFORE_POST = False in design_config.py to post.")
            print(f"  Preview: {preview_video_path}")
            print("=" * 60)
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                pass
            return False

        # News link: in first Page comment (reach) or in main caption — see config NEWS_LINK_IN_FIRST_COMMENT
        news_url = (viral_article.get("url") or viral_article.get("link") or "").strip()
        try:
            from config import NEWS_LINK_IN_FIRST_COMMENT, SHOW_FIRST_COMMENT_LINK_HINT, ENABLE_FIRST_COMMENT
        except ImportError:
            NEWS_LINK_IN_FIRST_COMMENT = False
            SHOW_FIRST_COMMENT_LINK_HINT = True
            ENABLE_FIRST_COMMENT = True
        if news_url:
            if NEWS_LINK_IN_FIRST_COMMENT and ENABLE_FIRST_COMMENT:
                if SHOW_FIRST_COMMENT_LINK_HINT:
                    caption = (caption or "").rstrip() + "\n\n📎 Full story link in our first comment 👇"
            elif NEWS_LINK_IN_FIRST_COMMENT and not ENABLE_FIRST_COMMENT:
                # First comment disabled — keep URL on the main post
                caption = (caption or "").rstrip() + "\n\n" + news_url
            elif not NEWS_LINK_IN_FIRST_COMMENT:
                caption = (caption or "").rstrip() + "\n\n" + news_url

        # Step 4: Post to Facebook
        if SKIP_FACEBOOK_POST:
            print("\nStep 4: Skipping Facebook post (no valid token; add PAGE_ID and PAGE_ACCESS_TOKEN to .env to post).")
            success = False
            post_id = None
        else:
            print("\nStep 4: Posting to Facebook...")
            result = post_to_facebook_page(caption, video_path)
            success = bool(result)
            post_id = result if success and isinstance(result, str) else None

        # Step 4b: First comment as the Page (e.g. The Unseen Economy) — engagement + optional article URL
        if success and post_id:
            try:
                from config import (
                    ENABLE_FIRST_COMMENT,
                    FIRST_COMMENT_TEMPLATES,
                    FACEBOOK_PAGE_ID,
                    FACEBOOK_ACCESS_TOKEN,
                    NEWS_LINK_IN_FIRST_COMMENT,
                )
                import random
                if not ENABLE_FIRST_COMMENT:
                    print("Step 4b: First comment skipped (ENABLE_FIRST_COMMENT is false).")
                elif not FIRST_COMMENT_TEMPLATES:
                    print("Step 4b: First comment skipped (no FIRST_COMMENT_TEMPLATES).")
                else:
                    intro = random.choice(FIRST_COMMENT_TEMPLATES)
                    if news_url and NEWS_LINK_IN_FIRST_COMMENT:
                        first_comment = intro.rstrip() + "\n\n" + news_url
                    else:
                        first_comment = intro
                    if post_comment_on_post(post_id, first_comment, page_id=FACEBOOK_PAGE_ID, page_access_token=FACEBOOK_ACCESS_TOKEN):
                        print("Step 4b: First comment posted as Page (with link in comment when configured).")
                    else:
                        print("Step 4b: First comment failed (check logs above — may need pages_manage_engagement).")
            except Exception as e:
                print(f"Step 4b: First comment error: {e}")
        elif success and not post_id:
            print("Step 4b: First comment skipped (no post_id returned from Facebook).")

        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"Cleaned up: {video_path}")
        except Exception:
            pass

        if success:
            print("\nPOST SUCCESSFUL!")
            save_posted_article(viral_article)
        else:
            print("\nPOST FAILED!")
        # Aggressive memory cleanup so next cycle runs without GPU/CUDA/VRAM buildup
        _memory_cleanup()
        return success

    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print(f"\nERROR in cycle: {e}")
        traceback.print_exc()
        _memory_cleanup()
        return False


def main():
    if not _acquire_single_instance_lock():
        return 0
    # Run from project folder so generated image path and imports are consistent
    os.chdir(_BASE)
    try:
        from config import PIPELINE_BUILD_ID
        print(f"  Pipeline build: {PIPELINE_BUILD_ID}", flush=True)
    except ImportError:
        pass
    print("=" * 60)
    print("CONTINUOUS VIDEO POSTING")
    print("  Post one now, then next cycle after each finish (see US/ET schedule line below).")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)
    print(f"  Project folder: {_BASE}")
    print("  Generated video: post_video_branded.mp4 in project folder (full path printed after generation).")
    if ENABLE_US_ET_POSTING_WINDOWS:
        try:
            from posting_schedule import schedule_summary_lines
            for line in schedule_summary_lines(POSTS_PER_DAY):
                print(line, flush=True)
        except Exception as e:
            print(f"  [SCHEDULE] Could not load US/ET schedule ({e}). Install: pip install tzdata", flush=True)
            print("  Set ENABLE_US_ET_POSTING_WINDOWS=0 in .env to run without this guard.", flush=True)
    else:
        print("  Schedule: 24/7 (set ENABLE_US_ET_POSTING_WINDOWS=1 for US ET windows + daily cap).", flush=True)
    print("=" * 60)

    print("  Video mode: Veo 3 render -> branded MP4 overlay -> Facebook video post.")

    # Retry Facebook check (transient network/API can fail on first try)
    global SKIP_FACEBOOK_POST
    for attempt in range(1, 4):
        if test_facebook_connection():
            break
        if attempt < 3:
            print(f"Facebook check failed (attempt {attempt}/3). Retrying in 5s...", flush=True)
            time.sleep(5)
    else:
        print("Facebook connection failed after 3 attempts. Pipeline will run in preview mode (no post).", flush=True)
        print("  Add PAGE_ID and PAGE_ACCESS_TOKEN to .env and restart to post to Facebook.", flush=True)
        SKIP_FACEBOOK_POST = True

    try:
        from design_config import APPROVE_BEFORE_POST
        if APPROVE_BEFORE_POST:
            print("\nNOTE: APPROVE_BEFORE_POST is True in design_config.py - preview only, no Facebook post.")
            print("      Set APPROVE_BEFORE_POST = False to post to Facebook.\n")
    except ImportError:
        pass

    def _wait_schedule_if_enabled():
        if not ENABLE_US_ET_POSTING_WINDOWS:
            return
        try:
            from posting_schedule import wait_until_allowed_post_slot
            wait_until_allowed_post_slot(POSTS_PER_DAY)
        except Exception as e:
            print(f"[SCHEDULE] Wait skipped ({e}). Try: pip install tzdata", flush=True)

    def _record_post_if_enabled(ok):
        if ok and ENABLE_US_ET_POSTING_WINDOWS:
            try:
                from posting_schedule import record_successful_post
                record_successful_post()
            except Exception:
                pass

    # --- Post one now (respects US/ET windows + daily cap when enabled) ---
    print("\n>>> Posting ONE now...")
    _wait_schedule_if_enabled()
    _ok = run_image_cycle()
    _record_post_if_enabled(_ok)

    # --- Then run continuously: next cycle starts after previous finishes ---
    print(f"\n>>> Starting continuous cycle (cooldown {CONTINUOUS_POST_COOLDOWN_SECONDS}s between cycles).\n")
    cycle_count = 1
    try:
        while True:
            cycle_count += 1
            _wait_schedule_if_enabled()
            _ok = run_image_cycle()
            _record_post_if_enabled(_ok)
            _memory_cleanup()
            if CONTINUOUS_POST_COOLDOWN_SECONDS > 0:
                print(f"\nCooldown {CONTINUOUS_POST_COOLDOWN_SECONDS}s before next cycle...")
                time.sleep(CONTINUOUS_POST_COOLDOWN_SECONDS)
    except KeyboardInterrupt:
        print("\n\nStopped by user (Ctrl+C).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, SystemExit) as e:
        raise
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
