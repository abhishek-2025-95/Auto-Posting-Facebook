"""
Sensational Breaking News overlay: expert-grade design.
Color grading + vignette → gradient bar → variable-weight headline (tracking, dynamic scale) →
sheared badge with micro-gradients → supersampled circular inset with inner glow.
"""
import os
import math

try:
    from design_config import (
        SPATIAL_BASE_UNIT, MARGIN_RATIO,
        BAR_HEIGHT_RATIO, BAR_GRADIENT, BAR_COLOR_TOP, BAR_COLOR_BOTTOM,
        HEADLINE_MAX_LINES, HEADLINE_MAX_CHARS_PER_LINE, HEADLINE_LINE_SPACING,
        HEADLINE_COLORS, HEADLINE_SHADOW, HEADLINE_SHADOW_OFFSET, HEADLINE_SHADOW_COLOR,
        HEADLINE_FILL_WIDTH_RATIO, HEADLINE_TRACKING, HEADLINE_FONT_WEIGHTS, HEADLINE_ALL_CAPS,
        BADGE_HEIGHT_RATIO, BADGE_WIDTH_RATIO, BADGE_SKEW_DEGREES, BADGE_GRADIENT,
        BADGE_RED_TOP, BADGE_RED_BOTTOM, BADGE_BLUE_TOP, BADGE_BLUE_BOTTOM,
        BADGE_TEXT_COLOR, BADGE_HIGHLIGHT_LINE,
        INSET_SUPERSAMPLE, INSET_BORDER_COLOR, INSET_BORDER_WIDTH, INSET_GLOW_BLUR_RADIUS, INSET_SHADOW,
        PRE_CONTRAST, PRE_SATURATION, VIGNETTE_STRENGTH, VIGNETTE_POWER,
        HEADLINE_FONT_PATH, BADGE_FONT_PATH, OVERLAY_SAVE_QUALITY,
    )
except ImportError:
    SPATIAL_BASE_UNIT = 8
    MARGIN_RATIO = 0.05
    BAR_HEIGHT_RATIO = 1 / 3
    BAR_GRADIENT = True
    BAR_COLOR_TOP = (28, 28, 32)
    BAR_COLOR_BOTTOM = (0, 0, 0)
    HEADLINE_MAX_LINES = 2
    HEADLINE_MAX_CHARS_PER_LINE = 42
    HEADLINE_LINE_SPACING = 0.5
    HEADLINE_FILL_WIDTH_RATIO = 0.90
    HEADLINE_TRACKING = 1
    HEADLINE_FONT_WEIGHTS = ("black", "bold", "regular")
    HEADLINE_ALL_CAPS = True
    HEADLINE_COLORS = [(0, 255, 255), (255, 255, 255), (255, 255, 0)]
    HEADLINE_SHADOW = True
    HEADLINE_SHADOW_OFFSET = (2, 2)
    HEADLINE_SHADOW_COLOR = (0, 0, 0)
    BADGE_HEIGHT_RATIO = 0.055
    BADGE_WIDTH_RATIO = 0.20
    BADGE_SKEW_DEGREES = 12
    BADGE_GRADIENT = True
    BADGE_RED_TOP = (220, 45, 60)
    BADGE_RED_BOTTOM = (165, 20, 35)
    BADGE_BLUE_TOP = (50, 90, 220)
    BADGE_BLUE_BOTTOM = (20, 45, 175)
    BADGE_TEXT_COLOR = (255, 255, 255)
    BADGE_HIGHLIGHT_LINE = True
    INSET_SUPERSAMPLE = 4
    INSET_BORDER_COLOR = (200, 200, 210)
    INSET_BORDER_WIDTH = 2
    INSET_GLOW_BLUR_RADIUS = 2
    INSET_SHADOW = True
    PRE_CONTRAST = 1.15
    PRE_SATURATION = 1.08
    VIGNETTE_STRENGTH = 0.28
    VIGNETTE_POWER = 2
    HEADLINE_FONT_PATH = BADGE_FONT_PATH = None
    OVERLAY_SAVE_QUALITY = 95


def _headline_to_lines(headline, caption=None, max_lines=None, max_chars_per_line=None):
    max_lines = max_lines or HEADLINE_MAX_LINES
    max_chars_per_line = max_chars_per_line or HEADLINE_MAX_CHARS_PER_LINE
    headline = (headline or "").strip()[:200]
    lines = []
    if headline:
        words = headline.split()
        current = []
        for word in words:
            current.append(word)
            s = " ".join(current)
            if len(s) >= max_chars_per_line and len(lines) < max_lines:
                lines.append(s)
                current = []
        if current:
            lines.append(" ".join(current))
    lines = lines[:max_lines]
    if caption:
        cap = (caption or "").strip()[:70]
        if cap and cap.lower() not in (headline[:80].lower() if headline else ""):
            if len(lines) < 3:
                lines.append(cap)
    return lines[:3]


def apply_sensational_overlay(image_path, headline_text, caption=None, design_context=None, inset_image=None):
    """
    Strict 70/30 zones. Top 70%: main image + badge + circular inset. Bottom 30%: solid black bar + headline only.
    Headline: dynamic font scaling (getlength loop), anchor='mm' at image_width/2, ALL CAPS, alternating Cyan/White/Yellow.
    inset_image: optional path or PIL Image for circular inset; if None, crop from main image.
    """
    if not image_path or not os.path.exists(image_path):
        return False
    ctx = design_context or {}
    try:
        from PIL import Image, ImageDraw, ImageFilter
        from design_utils import (
            get_font_by_weight, draw_gradient_rect, apply_vignette, apply_color_grade, ensure_noto_font,
            apply_bar_texture, grid_snap, draw_centered_scaled_text,
        )
        img = Image.open(image_path).convert("RGB")
        w, h = img.size

        vignette_strength = float(ctx.get("vignette_intensity", VIGNETTE_STRENGTH))
        bar_texture_opacity = float(ctx.get("bar_texture_opacity", 0))

        # --- Color grading (before any overlays) ---
        if PRE_CONTRAST != 1.0 or PRE_SATURATION != 1.0:
            img = apply_color_grade(img, PRE_CONTRAST, PRE_SATURATION)
        if vignette_strength > 0:
            apply_vignette(img, vignette_strength, VIGNETTE_POWER)

        # Copy for inset crop (inset must show scene, not the bar we're about to draw)
        img_for_inset = img.copy()

        draw = ImageDraw.Draw(img)
        base_unit = max(1, int(SPATIAL_BASE_UNIT))
        margin_ratio = float(MARGIN_RATIO)
        margin = grid_snap(int(w * margin_ratio), base_unit)
        margin = max(base_unit, margin)

        bar_height = max(grid_snap(int(h * BAR_HEIGHT_RATIO), base_unit), base_unit)
        bar_y0 = h - bar_height

        if BAR_GRADIENT:
            draw_gradient_rect(draw, 0, bar_y0, w, h, BAR_COLOR_TOP, BAR_COLOR_BOTTOM, vertical=True)
        else:
            draw.rectangle([0, bar_y0, w, h], fill=BAR_COLOR_BOTTOM)
        if bar_texture_opacity > 0:
            apply_bar_texture(img, bar_y0, bar_height, w, bar_texture_opacity)

        # --- Headline: dynamic bounding box loop + anchor="mm" at image_width/2 (no overflow) ---
        lines = _headline_to_lines(headline_text, caption)
        if not lines:
            lines = ["Breaking News"]
        for wt in ("black", "bold", "regular"):
            ensure_noto_font(wt)
        # Line centers: evenly spaced in bottom 30% bar; no overlap with top zone
        n_lines = len(lines)
        spacing = bar_height // max(1, n_lines)
        line_center_ys = [bar_y0 + spacing // 2 + i * spacing for i in range(n_lines)]
        force_upper = bool(HEADLINE_ALL_CAPS)
        for i, line in enumerate(lines):
            if not line:
                continue
            color = HEADLINE_COLORS[min(i, len(HEADLINE_COLORS) - 1)]
            weight = (HEADLINE_FONT_WEIGHTS[min(i, len(HEADLINE_FONT_WEIGHTS) - 1)] if hasattr(HEADLINE_FONT_WEIGHTS, "__iter__") and not isinstance(HEADLINE_FONT_WEIGHTS, str) else "bold")
            draw_centered_scaled_text(
                draw, line, w, line_center_ys[i],
                max_width_ratio=HEADLINE_FILL_WIDTH_RATIO,
                color=color,
                font_path=HEADLINE_FONT_PATH,
                weight=weight,
                min_size=10,
                max_size=min(w, bar_height) // 2,
                shadow_offset=HEADLINE_SHADOW_OFFSET if HEADLINE_SHADOW else None,
                shadow_color=HEADLINE_SHADOW_COLOR,
                force_upper=force_upper,
            )

        # --- Badge: context-aware colors from Color Theory Agent or schema ---
        badge_red_top = ctx.get("badge_red_top") or BADGE_RED_TOP
        badge_red_bottom = ctx.get("badge_red_bottom") or BADGE_RED_BOTTOM
        badge_blue_top = ctx.get("badge_blue_top") or BADGE_BLUE_TOP
        badge_blue_bottom = ctx.get("badge_blue_bottom") or BADGE_BLUE_BOTTOM
        badge_h = grid_snap(max(28, min(int(h * BADGE_HEIGHT_RATIO), 48)), base_unit)
        badge_w = grid_snap(max(120, min(int(w * BADGE_WIDTH_RATIO), 200)), base_unit)
        badge_x = margin
        # Clear space above bar: badge sits above with consistent margin (no overlap with bar edge)
        badge_y = grid_snap(bar_y0 - badge_h - max(margin, base_unit * 2), base_unit)
        if badge_y < base_unit:
            badge_y = max(base_unit, bar_y0 - badge_h - base_unit)
        skew_rad = math.radians(BADGE_SKEW_DEGREES) if BADGE_SKEW_DEGREES else 0
        k = math.tan(skew_rad) if skew_rad else 0
        extra_h = int(abs(k) * badge_w) + 12
        src_h = badge_h + extra_h
        badge_canvas = Image.new("RGB", (badge_w, src_h), (0, 0, 0))
        bdraw = ImageDraw.Draw(badge_canvas)
        split = int(badge_w * 0.55)
        if BADGE_GRADIENT:
            draw_gradient_rect(bdraw, 0, 0, split, src_h, badge_red_top, badge_red_bottom, vertical=True)
            draw_gradient_rect(bdraw, split, 0, badge_w, src_h, badge_blue_top, badge_blue_bottom, vertical=True)
        else:
            bdraw.rectangle([0, 0, split, src_h], fill=badge_red_top)
            bdraw.rectangle([split, 0, badge_w, src_h], fill=badge_blue_top)
        if k:
            # Vertical shear: output (x,y) samples from (x, y + k*x). Output size (badge_w, badge_h).
            aff = getattr(Image, "Transform", Image)
            aff = getattr(aff, "AFFINE", Image.AFFINE)
            badge_canvas = badge_canvas.transform((badge_w, badge_h), aff, (1, 0, 0, k, 1, 0), Image.Resampling.BICUBIC)
        img.paste(badge_canvas, (int(badge_x), int(badge_y)))
        if BADGE_HIGHLIGHT_LINE:
            draw.line([(int(badge_x), int(badge_y)), (int(badge_x + badge_w), int(badge_y))], fill=(255, 255, 255), width=1)
        badge_font = get_font_by_weight(max(12, badge_h - 10), "bold", BADGE_FONT_PATH)
        badge_cx = int(badge_x) + badge_w // 2
        badge_cy = int(badge_y) + badge_h // 2
        try:
            draw.text((badge_cx, badge_cy), "BREAKING NEWS", fill=BADGE_TEXT_COLOR, font=badge_font, anchor="mm")
        except TypeError:
            draw.text((int(badge_x) + 12, int(badge_y) + (badge_h - 14) // 2), "BREAKING NEWS", fill=BADGE_TEXT_COLOR, font=badge_font)

        # --- Circular inset: entirely in top 70% (no overlap with bar). 3x draw + thick stroke, LANCZOS downscale. ---
        circle_radius = grid_snap(min(int(w * 0.18), int(bar_y0 * 0.35), 150), base_unit)
        cx = w - circle_radius - max(margin, grid_snap(int(w * 0.035), base_unit))
        # Inset center in top zone: bottom of circle sits just above bar (no overlap)
        cy = bar_y0 - circle_radius - max(margin, base_unit)
        cy = max(cy, circle_radius + margin)

        # Source for inset: optional inset_image (path or PIL Image) or crop from main (scene only, not bar)
        if inset_image is not None:
            if hasattr(inset_image, "crop"):
                src_img = inset_image.convert("RGB") if inset_image.mode != "RGB" else inset_image
            elif isinstance(inset_image, str) and os.path.exists(inset_image):
                src_img = Image.open(inset_image).convert("RGB")
            else:
                src_img = img_for_inset
        else:
            src_img = img_for_inset
        crop_x0 = max(0, w - circle_radius * 2 - 24)
        crop_y0 = max(0, int(h * 0.08))
        crop_box = (crop_x0, crop_y0, min(src_img.size[0], crop_x0 + circle_radius * 2), min(src_img.size[1], crop_y0 + circle_radius * 2))
        cropped = src_img.crop(crop_box) if src_img.size[0] >= crop_box[2] and src_img.size[1] >= crop_box[3] else src_img.resize((circle_radius * 2, circle_radius * 2), Image.Resampling.LANCZOS)
        if cropped.size[0] != circle_radius * 2 or cropped.size[1] != circle_radius * 2:
            cropped = cropped.resize((circle_radius * 2, circle_radius * 2), Image.Resampling.LANCZOS)

        # Draw at 3x size + 15px stroke, then downsample LANCZOS for buttery smooth edges
        inset_scale = 3
        stroke_px = 15
        big_radius = circle_radius * inset_scale
        big_size = big_radius * 2 + stroke_px * 4
        cropped_big = cropped.resize((big_radius * 2, big_radius * 2), Image.Resampling.LANCZOS)
        # Mask must match source size for paste(); use mask same size as cropped_big
        crop_size = big_radius * 2
        mask_crop = Image.new("L", (crop_size, crop_size), 0)
        mdraw_crop = ImageDraw.Draw(mask_crop)
        mdraw_crop.ellipse((0, 0, crop_size - 1, crop_size - 1), fill=255)
        composite_big = Image.new("RGB", (big_size, big_size), (0, 0, 0))
        composite_big.paste(cropped_big, (stroke_px * 2, stroke_px * 2), mask_crop)
        gc = big_size // 2
        # Thick stroke at 3x (15px at output ≈ 5px equivalent)
        for t in range(stroke_px, 0, -1):
            bdraw = ImageDraw.Draw(composite_big)
            bdraw.ellipse((gc - big_radius - t, gc - big_radius - t, gc + big_radius + t, gc + big_radius + t), outline=INSET_BORDER_COLOR, width=2)
        inset_final = composite_big.resize((circle_radius * 2, circle_radius * 2), Image.Resampling.LANCZOS)
        paste_x = cx - circle_radius
        paste_y = cy - circle_radius
        img.paste(inset_final, (paste_x, paste_y))

        # Optional shadow ring on main canvas (subtle)
        if INSET_SHADOW:
            for offset in range(4, 0, -1):
                r = circle_radius + offset
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(20, 20, 30), width=1)
        for offset in range(2, 0, -1):
            r = circle_radius + offset
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INSET_BORDER_COLOR, width=1)

        img.save(image_path, quality=OVERLAY_SAVE_QUALITY)
        return True
    except Exception as e:
        print(f"Sensational overlay failed: {e}")
        import traceback
        traceback.print_exc()
        return False
