#!/usr/bin/env python3
"""
Create ``cursor_video_work_treasury_auctions/`` with article.json, eight 1920×1080 scene PNGs
(one per ~10s of explainer audio), and CURSOR_IMAGE_PROMPTS_PASTE.txt for higher-quality swaps.

Run from project root:
  python scripts/build_treasury_auction_explainer_pack.py
  python scripts/build_treasury_auction_explainer_pack.py --render
  python scripts/build_treasury_auction_explainer_pack.py --full

After ``--render`` / ``--full``, if ``breaking_thumbnail_v2.png`` or ``breaking_news_thumbnail.png`` exists in the pack folder,
a branded still (breaking pill + AI label + logo) is prepended (~2.5s) to the output MP4 unless ``--no-intro-thumb``.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

WORKDIR = os.path.join(_ROOT, "cursor_video_work_treasury_auctions")

# One image per ~10s of narration (8 scenes ≈ 80s). Each entry maps to one sentence of ``NARRATION``.
SCENE_PACK: list[dict[str, str]] = [
    {
        "title": "1 — Weakest demand in years",
        "beat": "Markets focus on Treasury auctions seeing some of the weakest bidder demand in years.",
        "prompt": (
            "16:9 landscape cinematic news explainer. Visual concept: U.S. Treasury auction stress—sparse or hesitant "
            "bidders metaphor (few raised paddles, thin crowd), Treasury building or bond paperwork in background, "
            "muted red alert accents suggesting concern. Photoreal broadcast documentary. On-image optional short "
            "generic label only: 'Auction demand' — no fake statistics, no stock tickers, no corporate logos. "
            "Must communicate: Treasury sales are struggling to attract strong interest."
        ),
    },
    {
        "title": "2 — How cash is raised",
        "beat": "Washington funds the government by auctioning bills, notes, and bonds to investors on a schedule.",
        "prompt": (
            "16:9 landscape clean editorial infographic. Step diagram: U.S. Treasury at center selling three layers "
            "labeled only as generic words 'Bills' 'Notes' 'Bonds' (no fine print). Arrows from Treasury to investors "
            "and institutions exchanging cash for securities. Scheduled calendar motif. Flat modern navy, white, gold. "
            "Educational explainer style like NYT or Economist. Must teach: scheduled Treasury auctions raise cash."
        ),
    },
    {
        "title": "3 — Poor auction → higher yields → ripple",
        "beat": "Weak auctions can force higher yields to place debt; that ripples through the whole interest-rate world.",
        "prompt": (
            "16:9 landscape abstract finance visualization. Left: weakening auction hammer or fading bid volume; "
            "center: Treasury coupon edge or yield arrow bending upward; right: concentric ripples washing over "
            "abstract icons for mortgage, corporate loan, and money-market (generic silhouettes). Cool teal and amber. "
            "No readable percentage numbers. Must show causal chain: weak demand → higher yields → broader rate impact."
        ),
    },
    {
        "title": "4 — War fear → safety & duration",
        "beat": "Geopolitical stress pushes investors toward safety and makes them pickier about duration and credit risk.",
        "prompt": (
            "16:9 landscape split educational illustration. Left: globe Middle East region, serious diplomatic tone, "
            "no weapons or gore. Right: investor choosing between long-dated risky paper versus short safe Treasury "
            "stack with protective glow. Middle ground: hourglass or timeline hinting 'duration'. "
            "Must explain: fear shifts portfolios toward quality and careful maturity choices."
        ),
    },
    {
        "title": "5 — Funding cost pass-through",
        "beat": "If government borrowing costs rise, mortgages, corporate credit, and deficit financing all feel it.",
        "prompt": (
            "16:9 landscape tri-panel explainer graphic. Panel A: single-family home + subtle mortgage deed; "
            "Panel B: office towers + generic corporate bond; Panel C: Capitol or ledger stack symbolizing public debt. "
            "Single upward cost arrow linking all three to a Treasury rate pillar. Neutral documentary palette. "
            "Must show: Treasury yields transmit to housing, business borrowing, and fiscal bills."
        ),
    },
    {
        "title": "6 — Risk-free rate repricing",
        "beat": "Equities, credit spreads, and the dollar move as traders reprice the risk-free rate and liquidity.",
        "prompt": (
            "16:9 landscape dark professional finance montage. Three zones: abstract equity price path (no company names), "
            "two diverging lines suggesting widening credit spreads, stylized dollar globe watermark. "
            "Small caption space with only the words 'Risk-free rate' if text is used. Terminal aesthetic. "
            "Must convey: stocks, spreads, FX react when Treasury benchmarks shift."
        ),
    },
    {
        "title": "7 — Oil, inflation, fiscal pressure",
        "beat": "Energy shocks add inflation complexity while big borrowing needs keep policymakers vigilant.",
        "prompt": (
            "16:9 landscape cinematic blend. Oil pumpjack silhouette at sunset merging into dual stress visuals: "
            "abstract rising cost thermometer (no CPI digits) and heavy Treasury issuance paperwork stack with "
            "small central-bank dome silhouette in distance. Serious macro tone. "
            "Must pair: commodity inflation risk + heavy Treasury supply + policy watchfulness."
        ),
    },
    {
        "title": "8 — What to watch next",
        "beat": "Next catalysts: Treasury auctions, yield moves, Fed signals, war and oil headlines—volatility until clarity.",
        "prompt": (
            "16:9 landscape forward-looking news checklist graphic. Soft background: horizon at dawn. Foreground: "
            "five simple icons with tiny generic labels only—Auction, Yields, Fed, Oil, Headlines. Optional volatility "
            "lightning subtle in sky. Premium broadcast outro. Must read as viewer takeaway / roadmap for what matters next."
        ),
    },
]


# Kokoro-friendly: one continuous script (~80s spoken at moderate pace).
NARRATION = """ \
Markets are focused on a tough stretch for U.S. Treasury auctions, with coverage pointing to some of the weakest demand in years. \
That matters because Washington raises cash by selling bills, notes, and bonds to investors through scheduled auctions. \
When those auctions go poorly, the government may have to pay higher yields to clear the debt, and that can ripple through the whole rate complex. \
Geopolitical stress around the Iran conflict is part of the backdrop, pushing investors toward safety and making them more selective about duration and risk. \
If funding costs drift higher, mortgages, corporate borrowing, and the cost of carrying large deficits can all feel the pressure. \
Stocks, credit spreads, and the dollar often react as traders repricing the so-called risk-free rate and liquidity expectations. \
Energy shocks can complicate inflation at the same time fiscal needs stay large, keeping central bankers and risk managers on alert. \
Watch the next few auctions, moves in yields, Fed guidance, and headlines on war and oil—that bundle will likely drive volatility until uncertainty fades. \
""".replace(
    "  ", " "
).strip()


def _try_load_font(size: int):
    try:
        from PIL import ImageFont

        for path in (
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ):
            if os.path.isfile(path):
                return ImageFont.truetype(path, size=size)
    except (OSError, ImportError):
        pass
    try:
        from PIL import ImageFont

        return ImageFont.load_default()
    except ImportError:
        return None


def _wrap_words(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        trial = (" ".join(cur + [w])) if cur else w
        if len(trial) <= max_chars:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines if lines else [text[:max_chars]]


def write_scene_png(
    out_path: str,
    scene_index: int,
    title: str,
    bottom_caption: str,
    width: int = 1920,
    height: int = 1080,
) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height))
    px = img.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(12 + t * 28)
        g = int(18 + t * 32)
        b = int(40 + t * 70)
        for x in range(width):
            px[x, y] = (r, g, b)
    dr = ImageDraw.Draw(img)
    font_lg = _try_load_font(44)
    font_sm = _try_load_font(28)
    gold = (212, 175, 55)
    dr.rectangle([0, 0, width, 6], fill=gold)
    title_lines = _wrap_words(title.replace("—", "-"), 42)
    y0 = 72
    for line in title_lines:
        dr.text((80, y0), line, fill=(245, 245, 250), font=font_lg)
        y0 += 52
    dr.text((80, y0 + 8), f"Scene {scene_index + 1} of 8  ~10s", fill=(180, 185, 200), font=font_sm)
    cap_lines = _wrap_words(bottom_caption, 52)
    yb = height - 40 - len(cap_lines) * 34
    for line in cap_lines:
        dr.text((80, yb), line, fill=(210, 215, 230), font=font_sm)
        yb += 34
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def write_article_json(path: str) -> None:
    article = {
        "title": "Treasury auctions under strain as geopolitical fear runs high",
        "headline": "Treasury auctions under strain as geopolitical fear runs high",
        "description": "U.S. Treasury sales are drawing scrutiny as demand softens while markets navigate war-related uncertainty and rate implications.",
        "summary": "U.S. Treasury sales are drawing scrutiny as demand softens while markets navigate war-related uncertainty and rate implications.",
        "subtitle_text": NARRATION,
        "url": "https://www.marketwatch.com/story/u-s-endures-weakest-treasury-auctions-in-over-3-years-as-anxiety-over-iran-war-grows-fb9a20a8?mod=mw_rss_topstories",
        "source": "MarketWatch",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)


def write_cursor_paste(path: str) -> None:
    lines = [
        "Each image must teach ONE beat from article.json narration (~10s of audio per still). Save as scene0.png … scene7.png.",
        "Style: consistent 16:9 cinematic finance explainer; no fake statistics; no corporate logos; minimal generic labels only.",
        "",
    ]
    for i, scene in enumerate(SCENE_PACK):
        lines.append(f"=== scene{i}.png — {scene['title']} ===")
        lines.append(f"News beat (must match voiceover): {scene['beat']}")
        lines.append("")
        lines.append(scene["prompt"])
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _prepend_branded_thumbnail_intro(
    workdir: str,
    main_mp4: str,
    *,
    intro_seconds: float,
    skip: bool,
) -> None:
    if skip or not main_mp4 or not os.path.isfile(main_mp4):
        return
    from video_branding import composite_branding_on_image, prepend_image_intro_to_video

    thumb_src = None
    for name in ("breaking_thumbnail_v2.png", "breaking_news_thumbnail.png"):
        p = os.path.join(workdir, name)
        if os.path.isfile(p):
            thumb_src = p
            break
    if not thumb_src:
        print(
            "Intro thumb: add breaking_thumbnail_v2.png or breaking_news_thumbnail.png to the pack folder; skipped."
        )
        return
    branded = os.path.join(workdir, "thumbnail_branded_for_intro.png")
    if not composite_branding_on_image(thumb_src, branded, show_breaking_label=True):
        return
    tmp_out = os.path.join(workdir, "_concat_intro_tmp.mp4")
    try:
        if os.path.isfile(tmp_out):
            os.unlink(tmp_out)
    except OSError:
        pass
    done = prepend_image_intro_to_video(
        branded,
        main_mp4,
        tmp_out,
        intro_seconds=float(intro_seconds),
    )
    if done and os.path.isfile(tmp_out):
        os.replace(tmp_out, main_mp4)
        print(f"Prepended branded thumbnail ({intro_seconds}s) -> {main_mp4}")
    else:
        try:
            if os.path.isfile(tmp_out):
                os.unlink(tmp_out)
        except OSError:
            pass


def main() -> int:
    p = argparse.ArgumentParser(description="Build Treasury-auction explainer pack (8 scenes × ~10s).")
    p.add_argument(
        "--render",
        action="store_true",
        help="Run stitched MP4 (no premium) after building assets",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="Run full pipeline: Kokoro + Whisper + pycaps (slow; requires optional deps)",
    )
    p.add_argument(
        "--rewrite-placeholders",
        action="store_true",
        help="Overwrite scene0–7.png with gradient placeholders. Default: keep existing files so AI/Cursor art is not wiped before render.",
    )
    p.add_argument(
        "--no-branding",
        action="store_true",
        help="Skip breaking-news banner, AI-generated label, and logo overlay (default: branding ON).",
    )
    p.add_argument(
        "--no-intro-thumb",
        action="store_true",
        help="Do not prepend a branded still (breaking_thumbnail_v2.png / breaking_news_thumbnail.png) at the start.",
    )
    p.add_argument(
        "--intro-seconds",
        type=float,
        default=2.5,
        help="Duration of the branded thumbnail intro (default 2.5).",
    )
    args = p.parse_args()

    os.makedirs(WORKDIR, exist_ok=True)
    write_article_json(os.path.join(WORKDIR, "article.json"))
    write_cursor_paste(os.path.join(WORKDIR, "CURSOR_IMAGE_PROMPTS_PASTE.txt"))

    paths: list[str] = []
    for i, scene in enumerate(SCENE_PACK):
        title = scene["title"]
        cap = scene["beat"]
        outp = os.path.join(WORKDIR, f"scene{i}.png")
        if args.rewrite_placeholders or not os.path.isfile(outp):
            write_scene_png(outp, i, title, cap)
            print(f"Wrote {outp}")
        else:
            print(f"Kept existing {outp}")
        paths.append(outp)

    print(f"\nPack root: {WORKDIR}")
    print("Render silent stitched 80s clip (AI label + bright logo by default; add --breaking-label for BREAKING pill):")
    print(
        f'  python scripts\\render_manual_cursor_video.py render '
        f'--images {" ".join(os.path.join("cursor_video_work_treasury_auctions", f"scene{i}.png") for i in range(8))} '
        f'--output cursor_video_work_treasury_auctions\\stitched_80s.mp4 --article cursor_video_work_treasury_auctions\\article.json '
        f'--no-subtitles --duration 80'
    )
    print("  Add --no-branding on that command to skip overlays.")
    print("Premium + pycaps: same --images, then:")
    print(
        r'  --output cursor_video_work_treasury_auctions\final_premium_pycaps.mp4 '
        r'--pycaps-kinetic-subtitles --no-subtitles --duration 80'
    )

    if args.render:
        out_mp4 = os.path.join(WORKDIR, "stitched_80s.mp4")
        cmd = [
            sys.executable,
            os.path.join(_ROOT, "scripts", "render_manual_cursor_video.py"),
            "render",
            "--images",
            *paths,
            "--output",
            out_mp4,
            "--article",
            os.path.join(WORKDIR, "article.json"),
            "--no-subtitles",
            "--duration",
            "80",
        ]
        if args.no_branding:
            cmd.append("--no-branding")
        print("\nRunning:", " ".join(cmd))
        r = subprocess.run(cmd, cwd=_ROOT)
        if r.returncode == 0:
            _prepend_branded_thumbnail_intro(
                WORKDIR,
                out_mp4,
                intro_seconds=float(args.intro_seconds),
                skip=bool(args.no_intro_thumb),
            )
        return int(r.returncode)

    if args.full:
        out_mp4 = os.path.join(WORKDIR, "final_premium_pycaps.mp4")
        cmd = [
            sys.executable,
            os.path.join(_ROOT, "scripts", "render_manual_cursor_video.py"),
            "render",
            "--images",
            *paths,
            "--output",
            out_mp4,
            "--article",
            os.path.join(WORKDIR, "article.json"),
            "--pycaps-kinetic-subtitles",
            "--no-subtitles",
            "--duration",
            "80",
        ]
        if args.no_branding:
            cmd.append("--no-branding")
        print("\nRunning (long):", " ".join(cmd))
        r = subprocess.run(cmd, cwd=_ROOT)
        if r.returncode == 0:
            _prepend_branded_thumbnail_intro(
                WORKDIR,
                out_mp4,
                intro_seconds=float(args.intro_seconds),
                skip=bool(args.no_intro_thumb),
            )
        return int(r.returncode)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
