#!/usr/bin/env python3
"""
Test script: Post ONE image now (news -> imgen_feb/Z-Image-Turbo -> Facebook),
then run the same schedule with image-based posts for testing the new image generation.
"""
from __future__ import print_function
import sys
import schedule
import time
import traceback
from datetime import datetime
import os

from concurrent.futures import ThreadPoolExecutor
from enhanced_news_diversity import pick_freshest_postable_article, save_posted_article
from content_generator import generate_facebook_caption, generate_post_image_fallback, generate_image_prompt_with_gemini
from facebook_api import post_to_facebook_page, test_facebook_connection
from monetization_optimized_schedule import get_optimal_posting_times


def run_image_cycle():
    """
    One cycle: fetch news -> caption -> generate image (imgen_feb) -> post to Facebook.
    Uses the new image generation model based on news links.
    """
    print("\n" + "="*60)
    print(f"IMAGE CYCLE (imgen_feb) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    try:
        # Step 1: Get fresh viral news
        print("\nStep 1: Fetching viral news...")
        viral_article = pick_freshest_postable_article()
        if not viral_article:
            print("No fresh articles (all recent stories already posted). Skipping this cycle.")
            return False

        print(f"Selected: {viral_article.get('title', '')[:60]}...")

        # Step 2: Caption + image prompt in parallel
        print("\nStep 2: Generating caption and image prompt in parallel...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            f_caption = executor.submit(generate_facebook_caption, viral_article)
            f_prompt = executor.submit(generate_image_prompt_with_gemini, viral_article)
            caption = f_caption.result()
            image_prompt = f_prompt.result()
        if not caption:
            print("No caption generated, skipping")
            return False

        # Step 3: Generate image (imgen_feb / Z-Image-Turbo)
        print("\nStep 3: Generating image...")
        image_path = generate_post_image_fallback(viral_article, image_prompt=image_prompt)
        if not image_path or not os.path.exists(image_path):
            print("Image generation failed, skipping")
            return False
        print(f"Image saved: {image_path}")

        # Approval gate: save preview and do NOT post until APPROVE_BEFORE_POST is False
        try:
            from design_config import APPROVE_BEFORE_POST, PREVIEW_IMAGE_PATH
        except ImportError:
            APPROVE_BEFORE_POST = False
            PREVIEW_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "approval_preview.jpg")
        if APPROVE_BEFORE_POST:
            import shutil
            shutil.copy2(image_path, PREVIEW_IMAGE_PATH)
            print("\n" + "="*60)
            print("PREVIEW ONLY (no post). Image saved for your approval:")
            print(f"  {PREVIEW_IMAGE_PATH}")
            print("Review the image. When satisfied, set APPROVE_BEFORE_POST = False in design_config.py")
            print("and run again to post to Facebook.")
            print("="*60)
            return False

        # Append news link at the end of the caption
        news_url = (viral_article.get("url") or viral_article.get("link") or "").strip()
        if news_url:
            caption = (caption or "").rstrip() + "\n\n" + news_url

        # Step 4: Post to Facebook (label already applied in overlay when using minimal)
        print("\nStep 4: Posting to Facebook...")
        success = post_to_facebook_page(caption, image_path, ai_label_already_applied=True)

        # Cleanup
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"Cleaned up: {image_path}")
        except Exception:
            pass

        if success:
            print("\nIMAGE POST SUCCESSFUL!")
            save_posted_article(viral_article)  # prevent duplicate posts
        else:
            print("\nPOST FAILED!")
        return success

    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"\nERROR in image cycle: {e}")
        traceback.print_exc()
        return False


def setup_schedule():
    """Use same times as monetization schedule, but run image cycle instead of video."""
    print("Setting up schedule (same times as monetization, image-based)...")
    optimal_times = get_optimal_posting_times()
    for time_str in optimal_times.keys():
        schedule.every().day.at(time_str).do(run_image_cycle)
        print(f"  Scheduled: {time_str} - {optimal_times[time_str]}")
    schedule.every(144).minutes.do(run_image_cycle)
    print("  Backup: every 144 minutes")


def show_next_runs_ist():
    """Print the next few scheduled run times (assumes system time is IST)."""
    next_times = []
    for job in schedule.get_jobs():
        if job.next_run:
            next_times.append(job.next_run)
    next_times.sort()
    # show next 5
    next_times = next_times[:5]
    if not next_times:
        print("\nNext post (IST): (no scheduled runs yet)")
        return
    print("\n" + "="*60)
    print("NEXT POSTS (IST)")
    print("="*60)
    for i, t in enumerate(next_times, 1):
        label = "Next" if i == 1 else f"Then"
        print(f"  {label}: {t.strftime('%Y-%m-%d %H:%M:%S')} IST")
    print("="*60)


def main():
    post_once = "--once" in sys.argv or "-1" in sys.argv
    if post_once:
        run_image_cycle.post_once = True

    print("="*60)
    print("TEST: Image generation (imgen_feb) + schedule")
    print("="*60)

    # Quick Facebook check
    if not test_facebook_connection():
        print("Facebook connection failed. Check config/token.")
        return

    # --- Post ONE now ---
    print("\n>>> Posting ONE image now (test run)...")
    run_image_cycle()

    if post_once:
        print("\n>>> Done (--once). Exiting.")
        return

    # --- Then run on schedule ---
    setup_schedule()
    show_next_runs_ist()
    print("\n>>> Schedule active. Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code:
            print("\n[Script exited with code %s]" % e.code, file=sys.stderr)
        raise
    except Exception as e:
        print("\n[FATAL] %s" % e, file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
