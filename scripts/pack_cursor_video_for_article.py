#!/usr/bin/env python3
"""Write cursor_video_pack + paste file for a fixed article dict (no network)."""
from __future__ import annotations

import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.chdir(_ROOT)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()

    import importlib.util

    from manual_cursor_video_flow import build_cursor_prompt_pack, build_render_plan

    article = {
        "title": "Micron's stock falls into a bear market — and it's now the cheapest in the S&P 500",
        "summary": (
            "Micron Technology has slid into bear-market territory off its highs as traders weigh the memory cycle, "
            "valuation versus S&P 500 peers, and earnings expectations. Coverage highlights the stock screening cheaper "
            "on forward metrics than many large-cap index names in the semiconductor space."
        ),
        "description": (
            "Micron Technology has slid into bear-market territory off its highs as traders weigh the memory cycle, "
            "valuation versus S&P 500 peers, and earnings expectations. Coverage highlights the stock screening cheaper "
            "on forward metrics than many large-cap index names in the semiconductor space."
        ),
        "url": (
            "https://www.marketwatch.com/story/microns-stock-falls-into-a-bear-market-"
            "and-its-now-the-cheapest-in-the-s-p-500-f90d9114"
        ),
        "source": "MarketWatch",
    }

    spec = importlib.util.spec_from_file_location(
        "_rmv", os.path.join(_ROOT, "scripts", "render_manual_cursor_video.py")
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    article_path = os.path.join(out_dir, "article.json")
    with open(article_path, "w", encoding="utf-8") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)

    plan = build_render_plan(article)
    story = plan["story_pack"]
    prompts = build_cursor_prompt_pack(story)
    payload = {
        "article": article,
        "render_plan": {k: v for k, v in plan.items() if k != "story_pack"},
        "story_pack": story,
        "cursor_prompts": prompts,
        "images_policy": "cursor_image_tool_only",
    }
    pack_path = os.path.join(out_dir, "cursor_video_pack.json")
    with open(pack_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    paste_path = mod._write_cursor_image_paste_file(out_dir, prompts, article)
    readme_path = os.path.join(out_dir, "CURSOR_IMAGES_README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "Micron / MarketWatch story — Cursor image tool only.\n"
            "Open CURSOR_IMAGE_PROMPTS_PASTE.txt; generate 5 images in Cursor; save scene0.png … scene4.png here.\n\n"
            "Then:\n"
            f'  python scripts/render_manual_cursor_video.py render '
            f'--images "{out_dir}/scene0.png" "{out_dir}/scene1.png" "{out_dir}/scene2.png" '
            f'"{out_dir}/scene3.png" "{out_dir}/scene4.png" '
            f'--output "{out_dir}/final.mp4" --article "{article_path}"\n'
        )

    print("Wrote:", pack_path)
    print("Wrote:", paste_path)
    print("Wrote:", article_path)
    print("Wrote:", readme_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
