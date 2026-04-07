#!/usr/bin/env python3
"""
High-contrast social thumbnails: default “engagement” (gold bar + warm glow) or
``breaking`` (full-width red banner + lower-third panel + ticker).

Run from repo root:
  python scripts/generate_engagement_thumbnail.py --work-dir cursor_video_work_micron_mw
  python scripts/generate_engagement_thumbnail.py --work-dir cursor_video_work --style breaking
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _load_article(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


# (keyword group, short label) — first matches become the hook strip (broadcast style).
_HOOK_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("plastic", "petrochemical", "polymer", "olefin", "resin"), "PETROCHEM"),
    (("hormuz", "strait", "iran", "tanker", "red sea"), "HORMUZ RISK"),
    (("inflation", "consumer price", "cpi", "prices"), "INFLATION WATCH"),
    (("oil", "crude", "brent", "wti", "opec"), "OIL MARKETS"),
    (("fed", "rates", "powell", "central bank", "ecb"), "RATES & POLICY"),
    (("china", "yuan", "beijing", "tariff"), "CHINA MACRO"),
    (("nvidia", "chip", "semiconductor", "memory"), "CHIPS"),
    (("bank", "credit", "default", "debt"), "CREDIT WATCH"),
    (("earnings", "guidance", "revenue"), "EARNINGS"),
)


def _derive_hook_strip(article: dict) -> str:
    blob = (
        f"{article.get('title', '')} {article.get('summary', '')} "
        f"{article.get('description', '')}"
    ).lower()
    tags: list[str] = []
    seen: set[str] = set()
    for keys, label in _HOOK_RULES:
        if any(k in blob for k in keys) and label not in seen:
            tags.append(label)
            seen.add(label)
    if len(tags) >= 2:
        return "  •  ".join(tags[:3])
    if len(tags) == 1:
        return f"{tags[0]}  •  GLOBAL MARKETS  •  WHAT IT MEANS"
    title = (article.get("title") or article.get("headline") or "Markets").upper()
    words = re.findall(r"[A-Za-z]{4,}", title)[:4]
    if len(words) >= 3:
        return "  •  ".join(words[:3])
    return "MACRO  •  MARKETS  •  THE BOTTOM LINE"


def _composite_warm_atmosphere(rgba: "Image.Image", width: int, height: int) -> "Image.Image":
    """Top warm wash + soft spotlight over the lower headline zone (modifies compositing only)."""
    from PIL import Image, ImageDraw

    out = rgba.copy()
    wash = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    y_top = max(1, int(height * 0.14))
    for y in range(y_top):
        t = 1.0 - (y / y_top)
        a = int(42 * t)
        wd.line([(0, y), (width, y)], fill=(255, 195, 110, a), width=1)
    out = Image.alpha_composite(out, wash)

    spot = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spot)
    cx, cy = width // 2, int(height * 0.62)
    rx, ry = int(width * 0.52), int(height * 0.38)
    for i, alpha in enumerate((38, 22, 10)):
        s = 1.0 - i * 0.11
        bx0 = int(cx - rx * s)
        bx1 = int(cx + rx * s)
        by0 = int(cy - ry * s)
        by1 = int(cy + ry * s)
        sd.ellipse([bx0, by0, bx1, by1], fill=(255, 155, 70, alpha))
    return Image.alpha_composite(out, spot)


def _draw_gradient_gold_bar(draw: "ImageDraw.ImageDraw", bar_w: int, height: int) -> None:
    y0 = int(height * 0.30)
    y1 = height - int(height * 0.09)
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0))
        r = 255
        g = int(200 + 55 * (1.0 - t))
        b = int(45 + 90 * t)
        draw.rectangle([0, y, bar_w, y + 1], fill=(r, g, b, 255))
    draw.line([(bar_w - 1, y0), (bar_w - 1, y1)], fill=(0, 0, 0, 140), width=2)


def _draw_text_stroke_center(
    draw,
    xy: tuple[int, int],
    text: str,
    font,
    fill: tuple[int, int, int, int],
    stroke_w: int,
    stroke_fill: tuple[int, int, int, int],
) -> None:
    x, y = xy
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=stroke_fill, anchor="mm")


def generate_engagement_thumbnail(
    scene_image: str,
    article: dict,
    output_path: str,
    *,
    width: int = 1920,
    height: int = 1080,
    branding_breaking: bool = True,
) -> str | None:
    from PIL import Image, ImageDraw, ImageEnhance, ImageOps

    from design_utils import apply_bottom_third_black_gradient, apply_vignette, get_font_by_weight
    from video_branding import _build_overlay_frame

    if not os.path.isfile(scene_image):
        print(f"Scene image not found: {scene_image}")
        return None
    title = (article.get("title") or article.get("headline") or "Breaking").strip()
    source = (article.get("source") or "").strip()

    base = Image.open(scene_image).convert("RGB")
    base = ImageOps.fit(base, (width, height), method=Image.Resampling.LANCZOS)
    base = ImageEnhance.Contrast(base).enhance(1.16)
    base = ImageEnhance.Color(base).enhance(1.14)
    base = ImageEnhance.Brightness(base).enhance(1.02)
    apply_vignette(base, strength=0.31, power=2)
    apply_bottom_third_black_gradient(base, alpha_max=0.84)

    rgba = base.convert("RGBA")
    rgba = _composite_warm_atmosphere(rgba, width, height)

    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    bar_w = max(12, width // 140)
    _draw_gradient_gold_bar(draw, bar_w, height)

    hook = _derive_hook_strip(article)

    sub_font = get_font_by_weight(max(28, height // 38), "bold")
    hook_y = height - int(height * 0.192)
    _draw_text_stroke_center(
        draw,
        (width // 2 + bar_w // 2, hook_y),
        hook,
        sub_font,
        (255, 248, 220, 255),
        3,
        (0, 0, 0, 255),
    )
    # Accent rule under hook
    rule_margin = int(width * 0.12)
    rule_y = hook_y + int(height * 0.038)
    draw.line(
        [(rule_margin, rule_y), (width - rule_margin, rule_y)],
        fill=(255, 210, 100, 220),
        width=max(2, height // 540),
    )

    # Main headline — 2–3 lines, large
    wrap_w = 38 if width >= 1800 else 32
    lines = textwrap.wrap(title, width=wrap_w)[:3]
    line_sizes = [max(52, height // 20), max(48, height // 22), max(44, height // 24)]
    font_main = get_font_by_weight(line_sizes[0], "black")
    font_mid = get_font_by_weight(line_sizes[1], "black") if len(lines) > 1 else font_main
    font_small = get_font_by_weight(line_sizes[2], "bold") if len(lines) > 2 else font_mid
    fonts = [font_main, font_mid, font_small]

    total_h = 0
    line_heights: list[int] = []
    for i, line in enumerate(lines):
        f = fonts[min(i, len(fonts) - 1)]
        bbox = draw.textbbox((0, 0), line, font=f)
        lh = bbox[3] - bbox[1] + 18
        line_heights.append(lh)
        total_h += lh
    y_cursor = height - int(height * 0.54) - total_h // 2
    for i, line in enumerate(lines):
        f = fonts[min(i, len(fonts) - 1)]
        cy = y_cursor + line_heights[i] // 2
        stroke = max(5, height // 260) if i == 0 else max(4, height // 300)
        _draw_text_stroke_center(
            draw,
            (width // 2 + bar_w // 2, cy),
            line,
            f,
            (255, 255, 255, 255),
            stroke,
            (0, 0, 0, 255),
        )
        y_cursor += line_heights[i]

    # CTA micro-line
    cta_font = get_font_by_weight(max(22, height // 48), "bold")
    _draw_text_stroke_center(
        draw,
        (width // 2, height - int(height * 0.065)),
        "WATCH THE FULL BREAKDOWN →",
        cta_font,
        (240, 245, 255, 255),
        2,
        (0, 0, 0, 200),
    )

    if source:
        src_font = get_font_by_weight(max(20, height // 52), "regular")
        draw.text(
            (width - 24, height - 28),
            source.upper(),
            font=src_font,
            fill=(200, 205, 220, 230),
            anchor="rb",
        )

    composed = Image.alpha_composite(rgba, layer)
    brand = _build_overlay_frame(
        width,
        height,
        headline=None,
        show_headline_lower_third=False,
        show_breaking_label=branding_breaking,
    )
    composed = Image.alpha_composite(composed, brand)

    out_abs = os.path.abspath(output_path)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)
    composed.convert("RGB").save(out_abs, "PNG", optimize=True)
    try:
        from design_utils import apply_post_process

        apply_post_process(out_abs)
    except Exception:
        pass
    print(f"Engagement thumbnail: {out_abs}")
    return out_abs


def generate_breaking_news_thumbnail(
    scene_image: str,
    article: dict,
    output_path: str,
    *,
    width: int = 1920,
    height: int = 1080,
    branding_breaking_pill: bool = False,
) -> str | None:
    """
    Alternate “broadcast breaking” look: crimson top band, desaturated frame, navy lower third,
    red spine + left-aligned headline, ticker strip. Visually distinct from ``generate_engagement_thumbnail``.
    """
    from PIL import Image, ImageDraw, ImageEnhance, ImageOps

    from design_utils import apply_vignette, get_font_by_weight
    from video_branding import _build_overlay_frame

    if not os.path.isfile(scene_image):
        print(f"Scene image not found: {scene_image}")
        return None
    title = (article.get("title") or article.get("headline") or "Breaking development").strip()
    source = (article.get("source") or "").strip()
    hook = _derive_hook_strip(article)

    base = Image.open(scene_image).convert("RGB")
    base = ImageOps.fit(base, (width, height), method=Image.Resampling.LANCZOS)
    base = ImageEnhance.Color(base).enhance(0.88)
    base = ImageEnhance.Contrast(base).enhance(1.12)
    base = ImageEnhance.Brightness(base).enhance(0.97)
    apply_vignette(base, strength=0.36, power=2)

    rgba = base.convert("RGBA")
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    band_h = max(72, int(height * 0.13))
    for y in range(band_h):
        t = y / max(1, band_h)
        r = int(175 + 80 * (1.0 - t))
        g = int(8 + 22 * (1.0 - t))
        b = int(18 + 25 * (1.0 - t))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    # Subtle highlight line under band
    draw.line([(0, band_h), (width, band_h)], fill=(255, 80, 80, 255), width=max(2, height // 540))

    live_r = max(8, height // 120)
    lx, ly = int(width * 0.045), band_h // 2
    draw.ellipse(
        [lx - live_r, ly - live_r, lx + live_r, ly + live_r],
        fill=(255, 60, 60, 255),
        outline=(255, 255, 255, 200),
        width=2,
    )
    live_font = get_font_by_weight(max(14, band_h // 5), "bold")
    draw.text((lx + live_r + 14, ly), "LIVE", fill=(255, 255, 255, 255), font=live_font, anchor="lm")

    banner_font = get_font_by_weight(max(28, int(band_h * 0.46)), "black")
    draw.text(
        (width // 2 + int(width * 0.04), band_h // 2),
        "BREAKING NEWS",
        font=banner_font,
        fill=(255, 255, 255, 255),
        anchor="mm",
        stroke_width=max(2, height // 400),
        stroke_fill=(0, 0, 0, 255),
    )

    panel_top = height - int(height * 0.38)
    draw.rectangle([0, panel_top, width, height], fill=(12, 16, 38, 242))
    spine_w = max(10, width // 100)
    draw.rectangle([0, panel_top, spine_w, height], fill=(218, 32, 56, 255))

    margin_x = spine_w + int(width * 0.042)
    lines = textwrap.wrap(title, width=40)[:4]
    if not lines:
        lines = [(title or "Breaking")[:180]]
    sizes = [max(46, height // 22), max(40, height // 26), max(36, height // 30), max(32, height // 34)]
    fonts = [get_font_by_weight(sizes[min(i, 3)], "black") for i in range(len(lines))]

    y_text = panel_top + int(height * 0.055)
    for i, line in enumerate(lines):
        f = fonts[i]
        bbox = draw.textbbox((0, 0), line, font=f)
        lh = bbox[3] - bbox[1] + 10
        cy = y_text + lh // 2
        draw.text(
            (margin_x, cy),
            line,
            font=f,
            fill=(255, 255, 255, 255),
            anchor="lm",
            stroke_width=max(3, height // 300),
            stroke_fill=(0, 0, 0, 255),
        )
        y_text += lh

    ticker_h = max(40, int(height * 0.052))
    ty0 = height - ticker_h
    draw.rectangle([0, ty0, width, height], fill=(28, 8, 12, 250))
    draw.line([(0, ty0), (width, ty0)], fill=(255, 215, 80, 255), width=2)
    tick_font = get_font_by_weight(max(17, height // 56), "bold")
    ticker_text = f"●  {hook}  ●  FULL STORY IN VIDEO"
    draw.text(
        (width // 2, ty0 + ticker_h // 2),
        ticker_text,
        font=tick_font,
        fill=(255, 245, 230, 255),
        anchor="mm",
        stroke_width=1,
        stroke_fill=(0, 0, 0, 255),
    )

    if source:
        src_font = get_font_by_weight(max(18, height // 58), "bold")
        draw.text(
            (width - 20, band_h + 12),
            source.upper(),
            font=src_font,
            fill=(255, 200, 200, 255),
            anchor="rt",
        )

    composed = Image.alpha_composite(rgba, layer)
    brand = _build_overlay_frame(
        width,
        height,
        headline=None,
        show_headline_lower_third=False,
        show_breaking_label=branding_breaking_pill,
    )
    composed = Image.alpha_composite(composed, brand)

    out_abs = os.path.abspath(output_path)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)
    composed.convert("RGB").save(out_abs, "PNG", optimize=True)
    try:
        from design_utils import apply_post_process

        apply_post_process(out_abs)
    except Exception:
        pass
    print(f"Breaking-news thumbnail: {out_abs}")
    return out_abs


def main() -> int:
    p = argparse.ArgumentParser(description="Generate a high-contrast video thumbnail for social feeds.")
    p.add_argument(
        "--work-dir",
        default="",
        help="Folder with article.json and scene0.png (default scene image).",
    )
    p.add_argument("--scene", default="", help="Override scene image path.")
    p.add_argument("--article", default="", help="Override article JSON path.")
    p.add_argument("-o", "--output", default="", help="Output PNG path.")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument(
        "--no-breaking-pill",
        action="store_true",
        help="Hide BREAKING NEWS pill (branding overlay).",
    )
    p.add_argument(
        "--style",
        choices=("engagement", "breaking"),
        default="engagement",
        help="Thumbnail layout: gold-bar engagement (default) or full breaking-news broadcast frame.",
    )
    args = p.parse_args()

    wd = (args.work_dir or "").strip()
    if wd and not os.path.isabs(wd):
        wd = os.path.join(_ROOT, wd)
    if not wd or not os.path.isdir(wd):
        print("Provide --work-dir pointing to a pack folder (article.json + scene0.png).", file=sys.stderr)
        return 1

    article_path = args.article.strip() or os.path.join(wd, "article.json")
    scene = args.scene.strip() or os.path.join(wd, "scene0.png")
    if not os.path.isfile(scene):
        for name in ("scene0.jpg", "scene1.png"):
            alt = os.path.join(wd, name)
            if os.path.isfile(alt):
                scene = alt
                break
    default_name = (
        "thumbnail_engagement.png" if args.style == "engagement" else "thumbnail_breaking_news.png"
    )
    out = args.output.strip() or os.path.join(wd, default_name)

    if not os.path.isfile(article_path):
        print(f"Missing article: {article_path}", file=sys.stderr)
        return 1

    art = _load_article(article_path)
    if args.style == "breaking":
        done = generate_breaking_news_thumbnail(
            scene,
            art,
            out,
            width=args.width,
            height=args.height,
            branding_breaking_pill=False,
        )
    else:
        done = generate_engagement_thumbnail(
            scene,
            art,
            out,
            width=args.width,
            height=args.height,
            branding_breaking=not args.no_breaking_pill,
        )
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
