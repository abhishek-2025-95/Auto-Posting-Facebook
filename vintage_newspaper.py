#!/usr/bin/env python3
"""
Vintage Newspaper (Flodia-style) overlay for Facebook "Human Interest" and long-form news.
2026 strategy: paper textures, serif typography, sepia/monochrome, mixed-media elements.
High-contrast headlines help Meta's AI categorize posts for history/journalism/storytelling.
"""

import os
import random


def _sepia(img):
    """Apply sepia tone for vintage press feel."""
    from PIL import Image
    width, height = img.size
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y][:3]
            tr = min(255, int(0.393 * r + 0.769 * g + 0.189 * b))
            tg = min(255, int(0.349 * r + 0.686 * g + 0.168 * b))
            tb = min(255, int(0.272 * r + 0.534 * g + 0.131 * b))
            pixels[x, y] = (tr, tg, tb)
    return img


def _paper_texture(img, amount=10, step=2):
    """Add subtle paper grain (noise) overlay. Uses PIL only; step=2 skips pixels for speed."""
    from PIL import Image
    pixels = img.load()
    w, h = img.size
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = pixels[x, y][:3]
            n = random.randint(-amount, amount)
            pixels[x, y] = (
                max(0, min(255, r + n)),
                max(0, min(255, g + n)),
                max(0, min(255, b + n)),
            )
    return img


def _serif_font(size):
    """Serif font: Times, Georgia, Courier, then Arial, then default."""
    from PIL import ImageFont
    # Try Windows-style font names and generic
    for name in (
        "times.ttf", "timesbd.ttf", "georgia.ttf", "cour.ttf",
        "Times New Roman", "Georgia", "Courier New", "arial.ttf",
    ):
        try:
            if "." in name:
                return ImageFont.truetype(name, size)
            return ImageFont.truetype(f"{name}.ttf", size)
        except (OSError, Exception):
            continue
    return ImageFont.load_default()


def _headline_layer(img, headline, font_size_ratio=0.08):
    """
    Draw high-contrast headline (for Meta AI readability and Flodia style).
    Uses a dark bar with white serif text or vice versa.
    """
    from PIL import Image, ImageDraw, ImageFont
    w, h = img.size
    font_size = max(24, int(min(w, h) * font_size_ratio))
    font = _serif_font(font_size)
    draw = ImageDraw.Draw(img)
    # Word-wrap headline (max ~40 chars per line for readability)
    words = headline.split()
    lines = []
    current = []
    for word in words:
        current.append(word)
        if len(" ".join(current)) > 40:
            if len(current) > 1:
                current.pop()
                lines.append(" ".join(current))
                current = [word]
            else:
                lines.append(word)
                current = []
    if current:
        lines.append(" ".join(current))
    lines = lines[:3]  # max 3 lines
    # Measure total text block
    line_heights = []
    max_w = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
        max_w = max(max_w, bbox[2] - bbox[0])
    total_h = sum(line_heights) + (len(lines) - 1) * 4
    pad = max(12, min(w, h) // 40)
    bar_h = total_h + pad * 2
    bar_y = pad  # top strip
    # Dark bar for high contrast (Meta AI + vintage)
    draw.rectangle([0, 0, w, bar_y + bar_h], fill=(30, 28, 26), outline=(80, 70, 60))
    y_off = bar_y + pad
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, y_off), line, fill=(250, 248, 240), font=font)
        y_off += line_heights[i] + 4
    return img


def _coffee_stain(img, opacity=0.12):
    """Subtle oval 'stain' for tactile mixed-media feel."""
    from PIL import Image, ImageDraw
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # One or two soft ovals
    cx, cy = w // 4, h - h // 4
    rx, ry = w // 6, h // 8
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(40, 30, 20, int(255 * opacity)))
    cx2, cy2 = w - w // 5, h // 5
    rx2, ry2 = w // 10, h // 12
    draw.ellipse([cx2 - rx2, cy2 - ry2, cx2 + rx2, cy2 + ry2], fill=(50, 35, 25, int(255 * opacity * 0.7)))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


def _tape_corners(img, opacity=0.35):
    """Subtle tape-like strips at corners (mixed media)."""
    from PIL import Image, ImageDraw
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    strip_w = max(20, w // 25)
    strip_l = max(60, w // 8)
    # Top-left tape
    draw.polygon(
        [(0, 0), (strip_l, 0), (strip_l + strip_w, strip_w), (strip_w, strip_w)],
        fill=(240, 230, 210, int(255 * opacity)),
        outline=(200, 190, 170, int(255 * opacity)),
    )
    # Bottom-right tape
    draw.polygon(
        [(w - strip_l - strip_w, h - strip_w), (w - strip_w, h - strip_w), (w, h), (w - strip_l, h)],
        fill=(240, 230, 210, int(255 * opacity)),
        outline=(200, 190, 170, int(255 * opacity)),
    )
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


def apply_vintage_newspaper(image_path, headline=None, paper_texture=True, sepia=True, headline_bar=True, coffee_stain=True, tape_corners=True):
    """
    Apply Flodia-style vintage newspaper overlay to an image (in place).
    Use for Human Interest, long-form, "On This Day", and myth-busting posts.

    Args:
        image_path: Path to the image file (modified in place).
        headline: Main headline text (high-contrast serif). If None, no headline bar is drawn.
        paper_texture: Add subtle paper grain.
        sepia: Apply sepia filter.
        headline_bar: Draw dark bar with headline at top (good for Meta AI + vintage).
        coffee_stain: Add subtle stain elements.
        tape_corners: Add subtle tape at corners.
    """
    if not image_path or not os.path.exists(image_path):
        return False
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        if sepia:
            img = _sepia(img)
        if paper_texture:
            img = _paper_texture(img)
        if headline_bar and headline and headline.strip():
            img = _headline_layer(img, headline.strip()[:120])
        if coffee_stain:
            img = _coffee_stain(img)
        if tape_corners:
            img = _tape_corners(img)
        img.save(image_path, quality=92)
        return True
    except Exception as e:
        print(f"Vintage newspaper overlay failed: {e}")
        return False
