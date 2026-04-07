#!/usr/bin/env python3
"""
End-to-end automation: fetch fresh news → (you add Cursor-chat images) → Kokoro + Whisper + pycaps
→ branded MP4 + engagement thumbnail intro → Facebook caption → Page video post.

Scene stills are **only** from the **Cursor image tool in chat** — no local diffusion, no fallback.
Each run writes ``CURSOR_IMAGE_PROMPTS_PASTE.txt`` under the work folder. Generate each scene in chat,
save ``scene0.png`` … into that folder, then re-run this script in the same work dir or use
``scripts/render_manual_cursor_video.py render``.

Requires: ffmpeg, Kokoro, Whisper, pycaps; .env PAGE_ID + PAGE_ACCESS_TOKEN, NEWS_API_KEY.

Usage:
  python scripts/auto_news_cursor_video_post.py              # one cycle
  python scripts/auto_news_cursor_video_post.py --loop       # repeat forever (cooldown from config)
  python scripts/auto_news_cursor_video_post.py --dry-run    # fetch + render, no Facebook
"""
from __future__ import annotations

import argparse
import atexit
import gc
import json
import os
import sys
import time
import traceback
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.chdir(_ROOT)

_LOCK_PATH = os.path.join(_ROOT, ".auto_news_cursor_video_post.lock")


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


def _release_lock() -> None:
    try:
        if os.path.exists(_LOCK_PATH):
            with open(_LOCK_PATH, "r", encoding="utf-8") as f:
                owner = int((f.read() or "0").strip())
            if owner == os.getpid():
                os.remove(_LOCK_PATH)
    except Exception:
        pass


def _acquire_lock() -> bool:
    if os.path.exists(_LOCK_PATH):
        try:
            with open(_LOCK_PATH, "r", encoding="utf-8") as f:
                existing_pid = int((f.read() or "0").strip())
        except Exception:
            existing_pid = 0
        if _pid_is_alive(existing_pid):
            print(
                f"[LOCK] Another auto_news_cursor_video_post.py is running (PID {existing_pid}). Exiting.",
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


def _memory_cleanup() -> None:
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except Exception:
        pass
    gc.collect()


def _article_for_pipeline(raw: dict) -> dict:
    return {
        "title": (raw.get("title") or raw.get("headline") or "").strip(),
        "summary": (raw.get("summary") or raw.get("description") or "").strip(),
        "description": (raw.get("description") or raw.get("summary") or "").strip(),
        "url": (raw.get("url") or raw.get("link") or "").strip(),
        "source": (raw.get("source") or "").strip(),
    }


def _one_cycle(
    *,
    us_uk_only: bool,
    dry_run: bool,
    work_parent: str,
    intro_seconds: float,
) -> bool:
    from config import (
        CHECK_FACEBOOK_FOR_DUPLICATES,
        ENABLE_NEWS_SECONDARY_RESEARCH,
        FACEBOOK_ACCESS_TOKEN,
        FACEBOOK_DUPLICATE_CHECK_LIMIT,
        FACEBOOK_DUPLICATE_SIMILARITY,
        FACEBOOK_PAGE_ID,
        NEWS_RESEARCH_TIMEOUT,
        TOPIC_THEME,
    )
    from content_generator import generate_facebook_caption
    from enhanced_news_diversity import (
        get_fresh_viral_news,
        get_fresh_viral_news_us_uk,
        is_duplicate_on_facebook,
        save_posted_article,
    )
    from facebook_api import post_comment_on_post, post_to_facebook_page
    from manual_cursor_video_flow import (
        build_final_manual_cursor_video,
        build_manual_video_story_arc,
        load_cursor_tool_scene_paths_if_present,
        write_cursor_operator_bundle,
    )

    print("\n" + "=" * 60)
    print(f"AUTO CURSOR VIDEO CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print("\nStep 1: Fetching news...")
    fetcher = get_fresh_viral_news_us_uk if us_uk_only else get_fresh_viral_news
    raw = fetcher()
    if not raw:
        print("No fresh article. Stop.")
        _memory_cleanup()
        return False
    article = _article_for_pipeline(raw)
    if not article.get("title"):
        print("Article missing title. Stop.")
        _memory_cleanup()
        return False
    print(f"Selected: {article['title'][:72]}...")
    if ENABLE_NEWS_SECONDARY_RESEARCH:
        try:
            from news_research_brief import enrich_article_with_research

            article = enrich_article_with_research(article, timeout=float(NEWS_RESEARCH_TIMEOUT))
            rb = article.get("research_brief") or {}
            nbullets = len(rb.get("bullets") or [])
            src = ", ".join(rb.get("sources") or []) or "none"
            print(f"  Secondary research: {nbullets} context bullets ({src}).")
        except Exception as ex:
            print(f"  Secondary research skipped: {ex}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = os.path.join(os.path.abspath(work_parent), f"run_{stamp}")
    os.makedirs(work_dir, exist_ok=True)
    article_path = os.path.join(work_dir, "article.json")
    with open(article_path, "w", encoding="utf-8") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)
    print(f"Work dir: {work_dir}")

    print("\nStep 2: Generating Facebook caption...")
    caption = generate_facebook_caption(raw, topic_theme=TOPIC_THEME)
    if not caption:
        print("Caption failed. Stop.")
        _memory_cleanup()
        return False
    cap_path = os.path.join(work_dir, "FACEBOOK_CAPTION.txt")
    with open(cap_path, "w", encoding="utf-8") as f:
        f.write(caption)
    if not dry_run and FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID:
        if CHECK_FACEBOOK_FOR_DUPLICATES:
            print("\nStep 2b: Duplicate check (Facebook)...")
            if is_duplicate_on_facebook(
                caption,
                limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
                similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
            ):
                print("Caption too similar to a recent post. Skipping.")
                save_posted_article(raw)
                _memory_cleanup()
                return False
            hl = (article.get("title") or "").strip()
            if hl and is_duplicate_on_facebook(
                hl,
                limit=FACEBOOK_DUPLICATE_CHECK_LIMIT,
                similarity_threshold=FACEBOOK_DUPLICATE_SIMILARITY,
            ):
                print("Headline too similar to a recent post. Skipping.")
                save_posted_article(raw)
                _memory_cleanup()
                return False

    print("\nStep 2c: Video narration (lede + caption body + research, for Kokoro)...")
    try:
        from manual_cursor_video_flow import compose_video_narration_for_publish

        article["subtitle_text"] = compose_video_narration_for_publish(article, social_caption=caption)
        with open(article_path, "w", encoding="utf-8") as f:
            json.dump(article, f, indent=2, ensure_ascii=False)
    except Exception as ex:
        print(f"  Video narration compose skipped: {ex}")

    print("\nStep 3: Scene images (Cursor chat image tool only — no fallback)...")
    _pack, _paste, _readme, story, _prompts = write_cursor_operator_bundle(work_dir, article)
    print(
        f"  Story pack: ideal VO ~{story.get('ideal_narration_seconds')}s, "
        f"est. from script ~{story.get('estimated_narration_seconds')}s, "
        f"{story.get('scene_count')} scenes."
    )
    scene_n = int(story.get("scene_count") or 0)
    paths = load_cursor_tool_scene_paths_if_present(work_dir, scene_n)
    if not paths:
        art_json = os.path.join(work_dir, "article.json")
        out_mp4 = os.path.join(work_dir, "FINAL_VIDEO.mp4")
        print(
            f"  No scene images in {work_dir!r} (need scene0 … scene{scene_n - 1} as .png/.jpg).\n"
            "  Open CURSOR_IMAGE_PROMPTS_PASTE.txt and generate each block with the image tool **in Cursor chat**.\n"
            "  Save files into this folder, then re-run this script or:\n"
            f'    python scripts/render_manual_cursor_video.py render --images "{work_dir}\\scene0.png" ... '
            f'--output "{out_mp4}" --article "{art_json}"\n'
            "  (Full --images list in CURSOR_IMAGES_README.txt.)"
        )
        _memory_cleanup()
        return False
    print(f"Scenes: {len(paths)} files")

    print("\nStep 4: Engagement thumbnail PNG...")
    thumb_path = os.path.join(work_dir, "thumbnail_engagement.png")
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "gen_eng_thumb",
            os.path.join(_ROOT, "scripts", "generate_engagement_thumbnail.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        mod.generate_engagement_thumbnail(paths[0], article, thumb_path)
    except Exception as e:
        print(f"[Thumb] engagement overlay failed ({e}); continuing without intro still.")
        thumb_path = ""

    out_video = os.path.join(work_dir, "FINAL_VIDEO.mp4")
    story = build_manual_video_story_arc(article)
    sub = str(story.get("subtitle_text") or "")

    print("\nStep 5: Premium render (Kokoro + Whisper + pycaps + branding)...")
    vid = build_final_manual_cursor_video(
        paths,
        output_path=out_video,
        subtitle_text=sub,
        headline=(article.get("title") or None),
        subtitles=False,
        branding=True,
        premium_voice_subtitles=True,
        pycaps_kinetic_subtitles=True,
        thumbnail_intro_path=thumb_path if (thumb_path and os.path.isfile(thumb_path)) else None,
        thumbnail_intro_seconds=float(intro_seconds),
    )
    if not vid or not os.path.isfile(vid):
        print("Video render failed.")
        _memory_cleanup()
        return False
    print(f"Video: {vid}")

    if dry_run:
        print("\nDry-run: skipping Facebook (article NOT marked posted). Caption saved next to video.")
        _memory_cleanup()
        return True

    if not FACEBOOK_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
        print("\nMissing PAGE_ACCESS_TOKEN / PAGE_ID in .env — not posting.")
        _memory_cleanup()
        return False

    try:
        from config import (
            ENABLE_FIRST_COMMENT,
            FIRST_COMMENT_TEMPLATES,
            NEWS_LINK_IN_FIRST_COMMENT,
            SHOW_FIRST_COMMENT_LINK_HINT,
        )
    except ImportError:
        ENABLE_FIRST_COMMENT = True
        FIRST_COMMENT_TEMPLATES = ()
        NEWS_LINK_IN_FIRST_COMMENT = False
        SHOW_FIRST_COMMENT_LINK_HINT = True

    news_url = article.get("url") or ""
    post_caption = caption
    if news_url:
        if NEWS_LINK_IN_FIRST_COMMENT and ENABLE_FIRST_COMMENT and SHOW_FIRST_COMMENT_LINK_HINT:
            post_caption = post_caption.rstrip() + "\n\n📎 Full story link in our first comment 👇"
        elif not NEWS_LINK_IN_FIRST_COMMENT:
            post_caption = post_caption.rstrip() + "\n\n" + news_url

    print("\nStep 6: Posting video to Facebook Page...")
    result = post_to_facebook_page(post_caption, vid, ai_label_already_applied=True)
    success = bool(result)
    post_id = result if success and isinstance(result, str) else None

    if success and post_id and ENABLE_FIRST_COMMENT and FIRST_COMMENT_TEMPLATES:
        import random

        intro = random.choice(FIRST_COMMENT_TEMPLATES)
        if news_url and NEWS_LINK_IN_FIRST_COMMENT:
            fc = intro.rstrip() + "\n\n" + news_url
        else:
            fc = intro
        post_comment_on_post(post_id, fc, page_id=FACEBOOK_PAGE_ID, page_access_token=FACEBOOK_ACCESS_TOKEN)

    if success:
        print("\nPOST SUCCESSFUL.")
        save_posted_article(raw)
    else:
        print("\nPOST FAILED.")

    _memory_cleanup()
    return success


def main() -> int:
    p = argparse.ArgumentParser(description="Auto: news → multi-scene premium video → Facebook.")
    p.add_argument(
        "--loop",
        action="store_true",
        help="Run forever with cooldown between cycles (CONTINUOUS_POST_COOLDOWN_SECONDS).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch, render, save files; do not post to Facebook.",
    )
    p.add_argument(
        "--global-pool",
        action="store_true",
        help="Use get_fresh_viral_news (default: US/UK scoped).",
    )
    p.add_argument(
        "--work-parent",
        default=os.path.join(_ROOT, "cursor_video_work_auto_run"),
        help="Directory under which run_YYYYMMDD_HHMMSS folders are created.",
    )
    p.add_argument(
        "--intro-seconds",
        type=float,
        default=1.75,
        help="Thumbnail intro duration when engagement PNG exists.",
    )
    p.add_argument(
        "--respect-schedule",
        action="store_true",
        help="Wait for US/ET posting window when ENABLE_US_ET_POSTING_WINDOWS=1 in .env.",
    )
    args = p.parse_args()

    if not _acquire_lock():
        return 1

    try:
        from config import (
            CONTINUOUS_POST_COOLDOWN_SECONDS,
            ENABLE_US_ET_POSTING_WINDOWS,
            POSTS_PER_DAY,
        )
    except ImportError:
        CONTINUOUS_POST_COOLDOWN_SECONDS = 120
        ENABLE_US_ET_POSTING_WINDOWS = False
        POSTS_PER_DAY = 10

    def wait_schedule() -> None:
        if not args.respect_schedule or not ENABLE_US_ET_POSTING_WINDOWS:
            return
        try:
            from posting_schedule import wait_until_allowed_post_slot

            wait_until_allowed_post_slot(POSTS_PER_DAY)
        except Exception as e:
            print(f"[SCHEDULE] wait skipped: {e}", flush=True)

    def record_post(ok: bool) -> None:
        if ok and ENABLE_US_ET_POSTING_WINDOWS and args.respect_schedule:
            try:
                from posting_schedule import record_successful_post

                record_successful_post()
            except Exception:
                pass

    print("=" * 60)
    print("AUTO NEWS -> CURSOR-STYLE PREMIUM VIDEO -> FACEBOOK")
    print(f"  Image source: Cursor image tool (inbound file via generate_post_image_fallback)")
    print(f"  Work parent: {os.path.abspath(args.work_parent)}")
    print("=" * 60)

    wait_schedule()
    try:
        ok = _one_cycle(
            us_uk_only=not args.global_pool,
            dry_run=bool(args.dry_run),
            work_parent=args.work_parent,
            intro_seconds=float(args.intro_seconds),
        )
        record_post(ok)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        ok = False

    if not args.loop:
        return 0 if ok else 1

    print(f"\nLoop mode: cooldown {CONTINUOUS_POST_COOLDOWN_SECONDS}s between cycles (Ctrl+C to stop).\n")
    try:
        while True:
            if CONTINUOUS_POST_COOLDOWN_SECONDS > 0:
                time.sleep(CONTINUOUS_POST_COOLDOWN_SECONDS)
            wait_schedule()
            try:
                ok = _one_cycle(
                    us_uk_only=not args.global_pool,
                    dry_run=bool(args.dry_run),
                    work_parent=args.work_parent,
                    intro_seconds=float(args.intro_seconds),
                )
                record_post(ok)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"ERROR: {e}")
                traceback.print_exc()
            _memory_cleanup()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
