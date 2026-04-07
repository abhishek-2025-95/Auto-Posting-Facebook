#!/usr/bin/env python3
"""
Multi-agent worker: run one full image cycle for a single sector (page + theme).
Used by orchestrator to run multiple pages with different themes in parallel.
"""
from __future__ import print_function
import sys
import os
import gc
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)


def _sector_slug(sector_name):
    """Safe filename slug from sector name (e.g. 'Real Estate' -> 'real_estate')."""
    s = (sector_name or "page").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "_", s).strip("_") or "page"
    return s[:32]


def run_one_cycle(sector_config):
    """
    Run one image cycle for a single sector: fetch news -> caption (persona/theme) -> image -> post.
    sector_config: dict with sector, theme, page_id, token, and optional system_prompt.
    Returns (sector_name, success: bool) or raises.
    """
    sector = sector_config.get("sector") or "Unknown"
    theme = sector_config.get("theme") or ""
    page_id = sector_config.get("page_id")
    token = sector_config.get("token")
    system_prompt = sector_config.get("system_prompt") or "You are a senior US news editor writing for Facebook."
    tone = sector_config.get("tone")
    hashtag_focus = sector_config.get("hashtag_focus")
    visual_style = sector_config.get("visual_style")
    if not visual_style:
        try:
            from config import get_default_visual_style_for_image_prompt

            visual_style = get_default_visual_style_for_image_prompt()
        except ImportError:
            pass

    sample_image_only = os.environ.get("SAMPLE_IMAGE_ONLY", "").strip().lower() in ("1", "true", "yes")
    if not sample_image_only and (not page_id or not token):
        print(f"[{sector}] Skipping: page_id and token are required in sector config.")
        return (sector, False)

    slug = _sector_slug(sector)
    output_path = os.path.join(_BASE, f"post_image_{slug}.jpg")

    print("\n" + "=" * 60)
    print(f"[{sector}] CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Theme: {theme[:50] or 'general'}" + (" [SAMPLE IMAGE ONLY - no post]" if sample_image_only else ""))
    print("=" * 60)

    try:
        os.chdir(_BASE)

        from enhanced_news_diversity import pick_freshest_postable_article, save_posted_article, is_article_posted
        from news_fetcher import select_viral_topic, get_news_bihar
        from content_generator import (
            generate_facebook_caption,
            generate_image_prompt_with_gemini,
            generate_post_image_fallback,
        )
        from facebook_api import post_to_facebook_page, test_facebook_connection

        if not sample_image_only:
            if not test_facebook_connection(page_id=page_id, page_access_token=token):
                print(f"[{sector}] Facebook connection failed for page_id={page_id}.")
                return (sector, False)

        # Step 1: Get news — Bihar Pulse uses ONLY Bihar news; no other news on this page.
        only_theme_news = sector_config.get("only_theme_news") is True
        is_bihar_pulse = "bihar" in (sector or "").lower() and "pulse" in (sector or "").lower()

        if only_theme_news or is_bihar_pulse:
            article_list = get_news_bihar()
            if article_list:
                fresh_list = [a for a in article_list if not is_article_posted(a)]
                viral_article = select_viral_topic(fresh_list) if fresh_list else None
            else:
                viral_article = None
            if not viral_article:
                print(f"[{sector}] No Bihar news found this cycle. Skipping — only Bihar news are posted on this page.")
                return (sector, False)
        else:
            viral_article = pick_freshest_postable_article()
            if not viral_article:
                print(f"[{sector}] No fresh articles. Skipping cycle.")
                return (sector, False)

        print(f"[{sector}] Selected: {viral_article.get('title', '')[:60]}...")

        # Step 2: Caption + image prompt in parallel (with persona, theme, tone, hashtag_focus, visual_style)
        with ThreadPoolExecutor(max_workers=2) as executor:
            f_caption = executor.submit(
                generate_facebook_caption,
                viral_article,
                system_prompt=system_prompt,
                topic_theme=theme,
                tone=tone,
                hashtag_focus=hashtag_focus,
            )
            f_prompt = executor.submit(
                generate_image_prompt_with_gemini,
                viral_article,
                system_prompt=system_prompt,
                topic_theme=theme,
                visual_style=visual_style,
            )
            caption = f_caption.result()
            image_prompt = f_prompt.result()

        if not caption:
            print(f"[{sector}] No caption generated, skipping.")
            return (sector, False)

        # Step 3: Generate image to sector-specific path
        image_path = generate_post_image_fallback(
            viral_article,
            image_prompt=image_prompt,
            output_path=output_path,
            system_prompt=system_prompt,
            topic_theme=theme,
            visual_style=visual_style,
        )
        image_path = os.path.abspath(image_path) if image_path else None
        if not image_path or not os.path.exists(image_path):
            print(f"[{sector}] Image generation failed.")
            return (sector, False)
        print(f"[{sector}] Image saved: {image_path}")

        if sample_image_only:
            import shutil
            preview_path = os.path.join(_BASE, "approval_preview.jpg")
            try:
                shutil.copy2(image_path, preview_path)
                print(f"[{sector}] Sample image copied to: {preview_path}")
            except Exception as e:
                print(f"[{sector}] Could not copy to preview: {e}")
            return (sector, True)

        # Approval gate (design_config)
        try:
            from design_config import APPROVE_BEFORE_POST
        except ImportError:
            APPROVE_BEFORE_POST = False
        if APPROVE_BEFORE_POST:
            print(f"[{sector}] PREVIEW ONLY (APPROVE_BEFORE_POST=True). Not posting.")
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception:
                pass
            return (sector, False)

        # Append news link at the end of the caption
        news_url = (viral_article.get("url") or viral_article.get("link") or "").strip()
        if news_url:
            caption = (caption or "").rstrip() + "\n\n" + news_url

        # Step 4: Post to this sector's page
        success = post_to_facebook_page(
            caption,
            image_path,
            ai_label_already_applied=True,
            page_id=page_id,
            page_access_token=token,
        )

        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass

        if success:
            save_posted_article(viral_article)
            print(f"[{sector}] POST SUCCESSFUL!")
        else:
            print(f"[{sector}] POST FAILED!")

        gc.collect()
        return (sector, success)

    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print(f"[{sector}] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return (sector, False)


if __name__ == "__main__":
    # Single-sector test: pass path to a one-item JSON or use env
    import json
    path = os.environ.get("SECTOR_CONFIG_JSON")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            configs = json.load(f)
        cfg = configs[0] if isinstance(configs, list) else configs
        name, ok = run_one_cycle(cfg)
        sys.exit(0 if ok else 1)
    print("Usage: set SECTOR_CONFIG_JSON to a JSON file with one sector config, or use orchestrator.py")
    sys.exit(2)
