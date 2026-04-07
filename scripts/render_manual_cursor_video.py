#!/usr/bin/env python3
"""
Operator CLI: manual Cursor video flow — prompt pack from an article, or final MP4 from scene images (min 10).
Run from repo root (or any cwd); imports are resolved via project parent directory.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from manual_cursor_video_flow import (  # noqa: E402
    MIN_VIDEO_SCENES,
    build_cursor_prompt_pack,
    build_final_manual_cursor_video,
    build_manual_video_story_arc,
    build_render_plan,
    write_cursor_operator_bundle,
)


def _resolve_article_json_path(user_path: str) -> str:
    """Resolve --article to an existing file (cwd, project root, or common pack folders)."""
    p = (user_path or "").strip()
    if not p:
        raise SystemExit("Empty --article path.")
    tried: list[str] = []
    candidates: list[str] = [os.path.abspath(p)]
    if not os.path.isabs(p):
        candidates.append(os.path.normpath(os.path.join(_ROOT, p)))
    base = os.path.basename(p.replace("\\", "/"))
    if base == "article.json" or p in ("article.json", "./article.json"):
        for sub in (
            "cursor_video_work",
            "cursor_video_work_micron_mw",
            "cursor_video_work_dhs_shutdown",
            "cursor_video_work_treasury_auctions",
        ):
            candidates.append(os.path.join(_ROOT, sub, "article.json"))
    seen: set[str] = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        tried.append(c)
        if os.path.isfile(c):
            return c
    raise SystemExit(
        "Article JSON not found. Tried:\n  "
        + "\n  ".join(tried)
        + "\n\nPass the full path, e.g.\n"
        + f'  --article "{os.path.join(_ROOT, "cursor_video_work", "article.json")}"\n'
        "or generate a pack: python scripts\\render_manual_cursor_video.py fetch-us-uk-pack"
    )


def _resolve_scene_image_paths(paths: list[str]) -> list[str]:
    """
    Resolve each scene image: cwd, then project-relative path, then common pack folders
    (cursor_video_work, cursor_video_work_micron_mw) by filename.
    """
    out: list[str] = []
    pack_dirs = (
        "cursor_video_work",
        "cursor_video_work_micron_mw",
        "cursor_video_work_dhs_shutdown",
        "cursor_video_work_treasury_auctions",
    )
    for p in paths:
        raw = (p or "").strip()
        if not raw:
            raise SystemExit("Empty path in --images.")
        candidates: list[str] = [os.path.abspath(raw)]
        if not os.path.isabs(raw):
            candidates.append(os.path.normpath(os.path.join(_ROOT, raw)))
            base = os.path.basename(raw.replace("\\", "/"))
            for sub in pack_dirs:
                candidates.append(os.path.join(_ROOT, sub, base))
        seen: set[str] = set()
        resolved: str | None = None
        tried: list[str] = []
        for c in candidates:
            if c in seen:
                continue
            seen.add(c)
            tried.append(c)
            if os.path.isfile(c):
                resolved = c
                break
        if resolved is None:
            raise SystemExit(
                f"Image not found: {raw}\nTried:\n  " + "\n  ".join(tried)
            )
        out.append(resolved)
    return out


def _load_article(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"Article JSON must be an object, got {type(data).__name__}")
    return data


def _maybe_enrich_article_with_research(article: dict, enabled: bool) -> dict:
    if not enabled:
        return article
    try:
        from config import NEWS_RESEARCH_TIMEOUT
        from news_research_brief import enrich_article_with_research

        return enrich_article_with_research(article, timeout=float(NEWS_RESEARCH_TIMEOUT))
    except Exception as ex:
        print(f"[research] skipped: {ex}", file=sys.stderr)
        return article


def cmd_prompts(args: argparse.Namespace) -> int:
    if args.article:
        article = _load_article(_resolve_article_json_path(args.article))
    else:
        article = {
            "title": args.title or "",
            "summary": args.summary or "",
            "description": args.description or "",
            "headline": args.headline or "",
        }
    article = _maybe_enrich_article_with_research(article, bool(getattr(args, "research", False)))
    plan = build_render_plan(
        article,
        use_ideal_narration_policy=bool(getattr(args, "ideal_narration_policy", True)),
    )
    story = plan["story_pack"]
    prompts = build_cursor_prompt_pack(story)
    payload = {
        "render_plan": {k: v for k, v in plan.items() if k != "story_pack"},
        "story_pack": story,
        "cursor_prompts": prompts,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote prompt pack: {os.path.abspath(args.out)}")
    else:
        print(text)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    images = list(args.images)
    if len(images) < 1:
        raise SystemExit("At least one --images path is required.")
    images = _resolve_scene_image_paths(images)

    subtitle_text: str
    headline: str | None = args.headline
    if args.article:
        article = _load_article(_resolve_article_json_path(args.article))
        story = build_manual_video_story_arc(
            article,
            use_ideal_narration_policy=bool(getattr(args, "ideal_narration_policy", True)),
        )
        subtitle_text = args.subtitle_text or str(story.get("subtitle_text") or "")
        if headline is None:
            st = str(story.get("subtitle_text") or "")
            head_from_sub = st.split("\n\n", 1)[0].split(" — ", 1)[0].strip()
            headline = (
                article.get("title")
                or article.get("headline")
                or (head_from_sub if head_from_sub else None)
            )
            headline = str(headline).strip() or None
    else:
        if not args.subtitle_text:
            raise SystemExit("Provide --subtitle-text or --article for on-screen summary text.")
        subtitle_text = args.subtitle_text

    out = os.path.abspath(args.output)
    # Default: Kokoro + Whisper + pycaps kinetic captions; no static MoviePy paragraph (opt-in via --static-full-summary-subtitles).
    static_full_summary = bool(getattr(args, "static_full_summary_subtitles", False))
    if getattr(args, "no_subtitles", False):
        static_full_summary = False

    thumb_intro = str(getattr(args, "thumbnail_intro", "") or "").strip()

    result = build_final_manual_cursor_video(
        images,
        output_path=out,
        subtitle_text=subtitle_text,
        headline=headline,
        subtitles=static_full_summary,
        branding=not args.no_branding,
        premium_voice_subtitles=bool(args.premium_voice_subtitles),
        pycaps_kinetic_subtitles=bool(args.pycaps_kinetic_subtitles),
        pycaps_template=str(getattr(args, "pycaps_template", "dynamic-neon-pop") or "dynamic-neon-pop"),
        pycaps_video_quality=str(
            getattr(args, "pycaps_video_quality", "very_high") or "very_high"
        ),
        pycaps_layout_align=str(getattr(args, "pycaps_layout_align", "bottom") or "bottom"),
        pycaps_layout_offset=float(getattr(args, "pycaps_layout_offset", 0.0)),
        pycaps_preview=bool(getattr(args, "pycaps_preview", False)),
        kokoro_voice=getattr(args, "kokoro_voice", None) or None,
        whisper_model=getattr(args, "whisper_model", None) or None,
        kokoro_speed=float(getattr(args, "kokoro_speed", 1.0)),
        effect=args.effect,
        fps=args.fps,
        width=args.width,
        height=args.height,
        video_duration_seconds=getattr(args, "duration", None),
        branding_breaking_label=bool(getattr(args, "breaking_label", False)),
        thumbnail_intro_path=thumb_intro if thumb_intro else None,
        thumbnail_intro_seconds=float(getattr(args, "thumbnail_intro_seconds", 1.75)),
    )
    if not result:
        print("Render failed.", file=sys.stderr)
        return 1
    print(f"Final video: {result}")
    return 0


def cmd_story_only(args: argparse.Namespace) -> int:
    """Print only the story pack JSON (no Cursor prompts)."""
    article = _load_article(_resolve_article_json_path(args.article))
    story = build_manual_video_story_arc(
        article,
        use_ideal_narration_policy=bool(getattr(args, "ideal_narration_policy", True)),
    )
    print(json.dumps(story, indent=2, ensure_ascii=False))
    return 0


def _article_for_pack(article: dict) -> dict:
    d = {
        "title": article.get("title") or article.get("headline") or "",
        "summary": article.get("description") or article.get("summary") or "",
        "description": article.get("description") or "",
        "url": article.get("url") or article.get("link") or "",
        "source": article.get("source") or "",
    }
    for k in ("key_stats", "key_metrics", "stats"):
        if article.get(k) is not None:
            d[k] = article[k]
    return d


def cmd_fetch_us_uk_pack(args: argparse.Namespace) -> int:
    """Latest fresh US/UK financial story from the same pool as the main app → JSON + Cursor-only readme."""
    from enhanced_news_diversity import get_fresh_viral_news_us_uk

    raw = get_fresh_viral_news_us_uk()
    if not raw:
        print("No US/UK viral article available (check NEWS_API_KEY and posted_articles).", file=sys.stderr)
        return 1
    article = _article_for_pack(raw)
    article = _maybe_enrich_article_with_research(article, bool(getattr(args, "research", True)))
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    article_path = os.path.join(out_dir, "article.json")
    with open(article_path, "w", encoding="utf-8") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)

    pack_path, paste_path, readme_path, _story, _prompts = write_cursor_operator_bundle(
        out_dir,
        article,
        use_ideal_narration_policy=bool(getattr(args, "ideal_narration_policy", True)),
    )

    print(f"Wrote: {pack_path}")
    print(f"Wrote: {paste_path}")
    print(f"Wrote: {article_path}")
    print(f"Wrote: {readme_path}")
    print(f"\nHeadline: {article.get('title', '')[:80]}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Manual Cursor video: export prompt pack or render branded MP4 from scene images (story packs use a "
            f"minimum of {MIN_VIDEO_SCENES} scenes). Without --duration: non-premium stitch uses 18s for 5 images "
            "else max(18s, ~3.6s×N); with default Kokoro+pycaps, stitch length follows natural narration unless "
            "--duration is set (VO time-stretch)."
        )
    )
    sub = p.add_subparsers(dest="command", required=True)

    pp = sub.add_parser("prompts", help="Build story pack + Cursor image prompts (JSON, min scenes per policy).")
    pp.add_argument("--article", help="Path to JSON article: title, summary/description, etc.")
    pp.add_argument("--title", default="", help="If no --article: headline text")
    pp.add_argument("--summary", default="", help="If no --article: summary body")
    pp.add_argument("--description", default="", help="If no --article: alias for summary")
    pp.add_argument("--headline", default="", help="If no --article: alias for title")
    pp.add_argument("-o", "--out", help="Write JSON to this path instead of stdout")
    pp.add_argument(
        "--research",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fetch Wikipedia + web snippets to enrich teaching points and image prompts (default: off).",
    )
    pp.add_argument(
        "--ideal-narration-policy",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Per-story ideal VO length + optional narration expansion for scene count (default: on).",
    )
    pp.set_defaults(func=cmd_prompts)

    pr = sub.add_parser(
        "render",
        help="Stitch scene images into final MP4: default Kokoro + pycaps kinetic + branding; static paragraph opt-in.",
    )
    pr.add_argument(
        "--images",
        nargs="+",
        metavar="PATH",
        required=True,
        help=(
            "Scene images in order (expect ≥10 for default story packs). Non-premium: 18s if 5 images else "
            "max(18s,~3.6s×N) unless --duration. Premium: omit --duration to match narration; pass --duration to "
            "fix length and time-stretch VO. Premium also requires enough images for narration length (≥1 per 10s)."
        ),
    )
    pr.add_argument(
        "--duration",
        type=float,
        default=None,
        help=(
            "Total stitched length (seconds). Non-premium default: 18 if 5 images else max(18, 3.6×N). "
            "Premium (Kokoro): omit to use natural narration length; set to force that duration and fit audio."
        ),
    )
    pr.add_argument("--output", "-o", required=True, help="Output MP4 path")
    pr.add_argument("--article", help="Article JSON for subtitle_text and headline (optional if --subtitle-text set)")
    pr.add_argument("--subtitle-text", default="", help="Full on-screen summary (title + summary); overrides article pack if set with --article")
    pr.add_argument("--headline", default=None, help="Lower-third headline for branding (default from article title)")
    pr.add_argument(
        "--static-full-summary-subtitles",
        action="store_true",
        help="Burn the static full-summary paragraph (MoviePy). Default is off; kinetic pycaps + narration carry the text.",
    )
    pr.add_argument(
        "--no-subtitles",
        action="store_true",
        help="Force-disable static full-summary burn-in (overrides --static-full-summary-subtitles). Default already skips static subs.",
    )
    pr.add_argument("--no-branding", action="store_true", help="Skip branding overlay (AI label + logo)")
    pr.add_argument(
        "--breaking-label",
        action="store_true",
        help="With branding: show top-left BREAKING NEWS pill (default: off)",
    )
    pr.add_argument(
        "--premium-voice-subtitles",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Kokoro TTS + Whisper timings (default: on). Use --no-premium-voice-subtitles to disable.",
    )
    pr.add_argument(
        "--pycaps-kinetic-subtitles",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Kinetic CSS captions via pycaps (default: on). Use --no-pycaps-kinetic-subtitles for MoviePy timed captions only.",
    )
    pr.add_argument(
        "--pycaps-template",
        default="dynamic-neon-pop",
        help=(
            "Kinetic subtitle preset. Default dynamic-neon-pop (bundled CSS + PopIn per word). "
            "Other values use pycaps built-ins: word-focus, hype, vibrant, explosive, ..."
        ),
    )
    pr.add_argument(
        "--pycaps-video-quality",
        default="very_high",
        choices=("low", "middle", "high", "very_high"),
        help="pycaps output encode quality (default very_high).",
    )
    pr.add_argument(
        "--pycaps-layout-align",
        default="bottom",
        choices=("bottom", "center", "top"),
        help="Vertical caption alignment for pycaps (default bottom).",
    )
    pr.add_argument(
        "--pycaps-layout-offset",
        type=float,
        default=0.0,
        help=(
            "pycaps vertical offset for bottom align: added to an internal 0.95 factor. "
            "Positive values push captions down and can clip them off-screen; 0 is safe; "
            "small negative values (e.g. -0.05) move them up."
        ),
    )
    pr.add_argument(
        "--pycaps-preview",
        action="store_true",
        help="Fast low-quality pycaps preview (not for final delivery).",
    )
    pr.add_argument("--kokoro-voice", default="", help="Kokoro voice id (default: KOKORO_VOICE env or af_bella)")
    pr.add_argument("--whisper-model", default="", help="Whisper model size (default: WHISPER_MODEL env or small)")
    pr.add_argument("--kokoro-speed", type=float, default=1.0, help="Kokoro speed multiplier (default 1.0)")
    pr.add_argument(
        "--thumbnail-intro",
        default="",
        metavar="PNG",
        help="Prepend this PNG as the opening still (e.g. thumbnail_engagement.png). Omit to skip.",
    )
    pr.add_argument(
        "--thumbnail-intro-seconds",
        type=float,
        default=1.75,
        help="Duration of the opening still in seconds (default 1.75).",
    )
    pr.add_argument(
        "--effect",
        default="static",
        choices=("zoom", "zoom_out", "static"),
        help="Per-scene motion: static (default), zoom, or zoom_out (Ken Burns via ffmpeg zoompan).",
    )
    pr.add_argument("--fps", type=int, default=30)
    pr.add_argument("--width", type=int, default=1920, help="Output width (default 1920, cinematic 16:9)")
    pr.add_argument("--height", type=int, default=1080, help="Output height (default 1080)")
    pr.add_argument(
        "--ideal-narration-policy",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Build subtitle_text from article with ideal-length policy when using --article (default: on).",
    )
    pr.set_defaults(func=cmd_render)

    ps = sub.add_parser("story", help="Print story pack JSON only from --article.")
    ps.add_argument("--article", required=True)
    ps.add_argument(
        "--ideal-narration-policy",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Per-story ideal VO length + optional narration expansion (default: on).",
    )
    ps.set_defaults(func=cmd_story_only)

    pf = sub.add_parser(
        "fetch-us-uk-pack",
        help="Pick latest fresh US/UK financial article (news pipeline) and write article.json + cursor_video_pack.json for Cursor images only.",
    )
    pf.add_argument(
        "--out-dir",
        default="cursor_video_work",
        help="Directory to create (default: ./cursor_video_work)",
    )
    pf.add_argument(
        "--research",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fetch Wikipedia + web snippets for richer Cursor prompts (default: on). Use --no-research to skip.",
    )
    pf.add_argument(
        "--ideal-narration-policy",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Per-story ideal VO length + optional narration expansion for scene count (default: on).",
    )
    pf.set_defaults(func=cmd_fetch_us_uk_pack)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
