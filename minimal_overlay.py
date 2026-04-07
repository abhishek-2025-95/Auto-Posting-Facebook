"""
Minimal overlay: "Breaking News" label top-left + headline box at bottom 30% of image.
No badge or circular inset. AI label is added separately (bottom-right).
Sizing and position scale with image size and aspect ratio.
Headline: grammatically correct, max 15 words (caller should pass shortened text).
"""
import os
import re

# Ensure this package dir is on path so design_config loads the same locally and on RunPod
_OVERLAY_DIR = os.path.dirname(os.path.abspath(__file__))
if _OVERLAY_DIR not in __import__("sys").path:
    __import__("sys").path.insert(0, _OVERLAY_DIR)

try:
    from design_config import (
        SPATIAL_BASE_UNIT,
        OVERLAY_SAVE_QUALITY,
        BREAKING_LABEL_TEXT,
        BREAKING_LABEL_FONT_PATH,
        BREAKING_LABEL_HEIGHT_RATIO,
        BREAKING_LABEL_MARGIN_RATIO,
        BREAKING_LABEL_PAD_X_RATIO,
        BREAKING_LABEL_PAD_Y_RATIO,
        BREAKING_LABEL_BG_RED,
        BREAKING_LABEL_BG_BLUE,
        BREAKING_LABEL_TEXT_COLOR,
        BREAKING_LABEL_TOP_BORDER,
        BREAKING_LABEL_RADIUS,
        BREAKING_LABEL_X_SHIFT,
        BREAKING_LABEL_Y_SHIFT,
        SHOW_BREAKING_LABEL,
        MINIMAL_HEADLINE_BAR_HEIGHT_RATIO,
        MINIMAL_HEADLINE_FILL_WIDTH_RATIO,
        MINIMAL_HEADLINE_BAR_TOP_BORDER,
        MINIMAL_HEADLINE_BAR_TOP_BORDER_COLOR,
        MINIMAL_HEADLINE_INNER_PADDING_RATIO,
        MINIMAL_HEADLINE_FONT_SIZE_MIN_RATIO,
        MINIMAL_HEADLINE_FONT_SIZE_MAX_RATIO,
        MINIMAL_HEADLINE_COLOR,
        MINIMAL_HEADLINE_COLORS,
        MINIMAL_HEADLINE_MAX_WORDS_IN_BOX,
        MINIMAL_HEADLINE_SHADOW,
        MINIMAL_HEADLINE_SHADOW_OFFSET,
        MINIMAL_HEADLINE_SHADOW_OFFSETS,
        MINIMAL_HEADLINE_STROKE,
        MINIMAL_HEADLINE_STROKE_WIDTH,
        MINIMAL_HEADLINE_STROKE_COLOR,
        MINIMAL_HEADLINE_ALL_CAPS,
        MINIMAL_HEADLINE_WRAP_TWO_LINES,
        MINIMAL_HEADLINE_WRAP_WORD_THRESHOLD,
        MINIMAL_HEADLINE_MIN_FONT_SIZE,
        USE_CONTRAST_HEADLINE_COLOR,
        SAFE_ZONE_INSET_RATIO,
        USE_HEADLINE_BOX,
        BAR_COLOR_BOTTOM,
    )
except ImportError:
    SPATIAL_BASE_UNIT = 8
    OVERLAY_SAVE_QUALITY = 95
    BREAKING_LABEL_TEXT = "BREAKING NEWS"
    BREAKING_LABEL_FONT_PATH = None
    BREAKING_LABEL_HEIGHT_RATIO = 0.072
    BREAKING_LABEL_MARGIN_RATIO = 0.045
    BREAKING_LABEL_PAD_X_RATIO = 0.55
    BREAKING_LABEL_PAD_Y_RATIO = 0.36
    BREAKING_LABEL_BG_RED = (200, 40, 50)
    BREAKING_LABEL_BG_BLUE = (40, 70, 200)
    BREAKING_LABEL_TEXT_COLOR = (255, 255, 255)
    BREAKING_LABEL_TOP_BORDER = True
    BREAKING_LABEL_RADIUS = 4
    BREAKING_LABEL_X_SHIFT = 0
    BREAKING_LABEL_Y_SHIFT = 0
    SHOW_BREAKING_LABEL = True
    MINIMAL_HEADLINE_BAR_HEIGHT_RATIO = 0.60   # 100% larger fallback when design_config missing
    MINIMAL_HEADLINE_FILL_WIDTH_RATIO = 0.88
    MINIMAL_HEADLINE_BAR_TOP_BORDER = True
    MINIMAL_HEADLINE_BAR_TOP_BORDER_COLOR = (80, 80, 90)
    MINIMAL_HEADLINE_INNER_PADDING_RATIO = 0.15
    MINIMAL_HEADLINE_FONT_SIZE_MIN_RATIO = 0.84   # 100% larger fallback
    MINIMAL_HEADLINE_FONT_SIZE_MAX_RATIO = 1.0    # 100% larger (capped in use)
    MINIMAL_HEADLINE_COLOR = (255, 255, 255)
    MINIMAL_HEADLINE_SHADOW = True
    MINIMAL_HEADLINE_SHADOW_OFFSET = (1, 1)
    MINIMAL_HEADLINE_SHADOW_OFFSETS = [(2, 2), (3, 3)]
    MINIMAL_HEADLINE_STROKE = True
    MINIMAL_HEADLINE_STROKE_WIDTH = 4   # 100% larger fallback
    MINIMAL_HEADLINE_STROKE_COLOR = (0, 0, 0)
    MINIMAL_HEADLINE_ALL_CAPS = False
    MINIMAL_HEADLINE_WRAP_TWO_LINES = True
    MINIMAL_HEADLINE_WRAP_WORD_THRESHOLD = 7
    MINIMAL_HEADLINE_MIN_FONT_SIZE = 42   # 100% larger fallback
    USE_CONTRAST_HEADLINE_COLOR = True
    SAFE_ZONE_INSET_RATIO = 0.05
    USE_HEADLINE_BOX = True    # default ON so headline box shows when design_config fails to load
    BAR_COLOR_BOTTOM = (0, 0, 0)
    MINIMAL_HEADLINE_COLORS = [(0, 255, 255), (255, 255, 255), (255, 255, 0)]
    MINIMAL_HEADLINE_MAX_WORDS_IN_BOX = 10


def _grid_snap(px, base=8):
    b = max(1, int(base))
    return (int(px) // b) * b


def _dedupe_headline_text(text):
    """Remove consecutive duplicate sentences or phrases so headline is not repeated (e.g. from upstream glitches)."""
    if not text or not text.strip():
        return text
    # Split on sentence boundaries (., !, ?) and strip
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return text.strip()
    deduped = []
    for p in parts:
        if deduped and deduped[-1].lower() == p.lower():
            continue
        deduped.append(p)
    return " ".join(deduped)


def _wrap_headline_two_lines(text, max_chars_per_line=42):
    """Wrap headline into at most 2 lines at word boundary so each line stays under max_chars_per_line."""
    words = (text or "").strip().split()
    if not words:
        return ["Breaking News"]
    if len(words) == 1:
        return [words[0]]
    line1, line2 = [], []
    for word in words:
        cand = line1 + [word]
        s = " ".join(cand)
        if len(s) <= max_chars_per_line:
            line1.append(word)
        else:
            break
    line2 = words[len(line1):]
    s1 = " ".join(line1) if line1 else ""
    s2 = " ".join(line2) if line2 else ""
    if not s1:
        line1, line2 = words[:1], words[1:]
        s1, s2 = " ".join(line1), " ".join(line2)
    return [s1, s2] if s2 else [s1]


def _truncate_line_to_fit(draw, line, font_size, max_width_px, font_path, weight, stroke_width=0):
    """Return text that fits in max_width_px so nothing is drawn outside the box (no 're-elec' cut-off)."""
    if not line or max_width_px <= 0:
        return line
    from design_utils import get_font_by_weight
    font = get_font_by_weight(font_size, weight, font_path)
    try:
        w = int(font.getlength(line))
    except (AttributeError, TypeError):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
    extra = 2 * (stroke_width or 0)
    if w + extra <= max_width_px:
        return line
    words = line.split()
    suffix = "\u2026"  # ellipsis
    for i in range(len(words), 0, -1):
        candidate = " ".join(words[:i]) + suffix
        try:
            w = int(font.getlength(candidate))
        except (AttributeError, TypeError):
            bbox = draw.textbbox((0, 0), candidate, font=font)
            w = bbox[2] - bbox[0]
        if w + extra <= max_width_px:
            return candidate
    return (words[0][:12] + suffix) if words else suffix


# Country code -> full name for image prompt (country-specific thematic)
COUNTRY_CODE_TO_NAME = {
    "us": "United States", "gb": "United Kingdom", "in": "India", "cn": "China", "ru": "Russia",
    "fr": "France", "de": "Germany", "jp": "Japan", "br": "Brazil", "qa": "Qatar",
    "au": "Australia", "ca": "Canada", "kr": "South Korea", "it": "Italy", "es": "Spain",
}

# Common news source names -> ISO 3166-1 alpha-2
_SOURCE_TO_COUNTRY = {
    "bbc": "gb", "bbc news": "gb", "cnn": "us", "reuters": "gb", "ap": "us", "associated press": "us",
    "al jazeera": "qa", "npr": "us", "nytimes": "us", "new york times": "us", "guardian": "gb",
    "washington post": "us", "usa today": "us", "fox news": "us", "nbc": "us", "abc": "us", "cbs": "us",
    "bloomberg": "us", "wsj": "us", "wall street journal": "us", "the hill": "us", "politico": "us",
    "axios": "us", "nbc news": "us", "abc news": "us", "cbs news": "us", "msnbc": "us",
    "dw": "de", "france 24": "fr", "rt": "ru", "xinhua": "cn", "global times": "cn", "india today": "in",
}


def get_country_code_for_article(article):
    """Return ISO 3166-1 alpha-2 country code from article country/countryCode/source."""
    if not article:
        return None
    code = (article.get("countryCode") or article.get("country") or "").strip().lower()
    if len(code) == 2:
        return code
    source = (article.get("source") or "").strip().lower()
    if source:
        return _SOURCE_TO_COUNTRY.get(source) or _SOURCE_TO_COUNTRY.get(source.replace(" ", ""))
    return None


def get_country_name_for_prompt(country_code):
    """Return full country name for image prompt thematic (e.g. 'us' -> 'United States')."""
    if not country_code or len(country_code) != 2:
        return None
    return COUNTRY_CODE_TO_NAME.get(str(country_code).lower())


def _draw_subtle_flag(img, country_code, w, h):
    """Paste a very subtle source-country flag in the theme (top-right). country_code: ISO 3166-1 alpha-2 (e.g. 'us', 'gb'). Returns img (RGB)."""
    if not country_code or len(country_code) != 2:
        return img
    try:
        import urllib.request
        from PIL import Image
        code = str(country_code).lower()[:2]
        url = f"https://flagcdn.com/w40/{code}.png"
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"_flag_{code}.png")
        if not os.path.exists(path):
            urllib.request.urlretrieve(url, path)
        flag = Image.open(path).convert("RGBA")
        flag = flag.resize((24, 16), Image.Resampling.LANCZOS)
        out = flag.load()
        for py in range(flag.size[1]):
            for px in range(flag.size[0]):
                r, g, b, a = out[px, py]
                out[px, py] = (r, g, b, int(a * 0.20))
        margin = max(8, int(min(w, h) * 0.022))
        x0 = w - margin - 24
        y0 = margin
        img_rgba = img.convert("RGBA")
        img_rgba.paste(flag, (x0, y0), flag)
        return img_rgba.convert("RGB")
    except Exception:
        return img


def _bar_color_from_context(ctx):
    """Design agent: subtle dark bar tint from primary color for a professional, branded look."""
    primary = ctx.get("primary_color_rgb")
    if not primary or len(primary) != 3:
        return None
    # Very dark tint: ~10% primary + 90% black so bar stays readable
    blend = 0.10
    return (
        int(primary[0] * blend),
        int(primary[1] * blend),
        int(primary[2] * blend),
    )


def _headline_color_from_context(ctx):
    """Design agent: headline color – white for readability, or primary if bright (engaging)."""
    primary = ctx.get("primary_color_rgb")
    if not primary or len(primary) != 3:
        return None
    luminance = (primary[0] * 0.299 + primary[1] * 0.587 + primary[2] * 0.114)
    if luminance >= 200:
        return tuple(min(255, max(0, int(c))) for c in primary)
    return None


def apply_minimal_breaking_overlay(image_path, headline=None, design_context=None, country_code=None, source=None):
    """
    Draw overlay on the image. Layout (in draw order):
    - Headline box: lower third (when USE_HEADLINE_BOX and style modern/frosted/minimal); full headline up to 15 words.
    - Breaking News label: top-left (when SHOW_BREAKING_LABEL).
    - Logo: top-right (Unseen Economy image or text).
    - Source: bottom-left, "Source: <name>" (when source is non-empty).
    - AI Generated label: bottom-right (drawn by ai_label after this returns, or in same pass).

    headline: text for the PIL headline box/bar. If empty/None, no overlay headline is drawn (use when the base image
        already contains full headline typography, e.g. Cursor image tool).
    source: news source name for bottom-left; optional.
    """
    if not image_path:
        print("Minimal overlay: image path missing or file not found.")
        return False
    image_path = os.path.abspath(os.path.normpath(str(image_path)))
    if not os.path.isfile(image_path):
        print("Minimal overlay: image path missing or file not found.")
        return False
    ctx = design_context or {}
    try:
        from PIL import Image, ImageDraw
        from design_utils import (
            get_font_by_weight,
            draw_gradient_rect,
            draw_centered_scaled_text,
            draw_centered_scaled_text_multicolor,
            apply_bottom_third_black_gradient,
            get_contrast_text_color,
            wrap_text_to_width,
            fit_text_in_box,
            draw_left_aligned_headline,
            resolve_color,
            shrink_width_for_stroke_shadow,
        )
        try:
            from design_utils import apply_bar_texture
        except ImportError:
            apply_bar_texture = None

        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        draw = ImageDraw.Draw(img)
        base = max(1, int(SPATIAL_BASE_UNIT))
        short_side = min(w, h)
        margin = max(base, _grid_snap(short_side * BREAKING_LABEL_MARGIN_RATIO, base))
        label_h = max(28, _grid_snap(short_side * BREAKING_LABEL_HEIGHT_RATIO, base))  # min 28px so label is visible
        # Empty headline: skip PIL headline layer (in-image headline only — e.g. Cursor image tool).
        headline_for_overlay = (headline or "").strip()
        # ULTRA_MINIMAL_IMAGE_OVERLAY sets USE_HEADLINE_BOX=False (label+logo+source only). For cursor_only +
        # CURSOR_USE_PIL_HEADLINE_OVERLAY the base image has no chyron—we must still draw the headline box.
        try:
            from config import CURSOR_USE_PIL_HEADLINE_OVERLAY as _cfg_cursor_pil_hl
        except ImportError:
            _cfg_cursor_pil_hl = False  # match config default: Cursor paints headline
        try:
            from config import IMAGE_GENERATION_MODE as _igm_cfg
        except ImportError:
            _igm_cfg = ""
        _cursor_only_mode = (_igm_cfg or "").strip().lower() == "cursor_only"
        _force_headline_box = (
            bool(headline_for_overlay) and _cursor_only_mode and bool(_cfg_cursor_pil_hl)
        )
        _draw_headline_layer = bool(headline_for_overlay) and (USE_HEADLINE_BOX or _force_headline_box)
        if _force_headline_box and not USE_HEADLINE_BOX:
            print(
                "Minimal overlay: drawing PIL headline box (cursor_only + PIL headline; ULTRA_MINIMAL hides box otherwise)."
            )

        if _draw_headline_layer:
            try:
                from design_config import (
                    HEADLINE_BOX_STYLE,
                    FROSTED_BOX_RGBA,
                    FROSTED_BOX_RADIUS,
                    FROSTED_BOX_OUTLINE_RGBA,
                    FROSTED_BOX_OUTLINE_WIDTH,
                    MODERN_HEADLINE_MARGIN_RATIO,
                    MODERN_HEADLINE_BORDER_RADIUS,
                    MODERN_HEADLINE_BG_RGBA,
                    MODERN_HEADLINE_BLUR_RADIUS,
                    MODERN_HEADLINE_ACCENT_LEFT,
                    MODERN_HEADLINE_ACCENT_WIDTH,
                    MODERN_HEADLINE_PADDING_PX,
                    MODERN_HEADLINE_TEXT_INSET_LEFT,
                    MODERN_HEADLINE_MAX_WIDTH_PX,
                    MODERN_HEADLINE_LINE_HEIGHT_RATIO,
                    MODERN_HEADLINE_HIGHLIGHT_WORDS,
                    MODERN_HEADLINE_HIGHLIGHT_WORDS_LIST,
                    MODERN_HEADLINE_WHITE_RGB,
                    MODERN_HEADLINE_TOP_BORDER,
                    MODERN_HEADLINE_TOP_BORDER_COLOR,
                    MODERN_HEADLINE_TEXT_SHADOW,
                    MODERN_HEADLINE_STROKE_WIDTH,
                    MODERN_HEADLINE_STROKE_RATIO,
                    MODERN_HEADLINE_STROKE_FILL,
                    MODERN_HEADLINE_FONT_WEIGHT,
                    MODERN_HEADLINE_FONT_PATH,
                    MODERN_HEADLINE_MAX_WORDS,
                    MODERN_HEADLINE_MAX_LINES,
                )
                try:
                    from design_config import MODERN_HEADLINE_PADDING_HORIZONTAL_PX, MODERN_HEADLINE_PADDING_VERTICAL_PX
                    pad_h = MODERN_HEADLINE_PADDING_HORIZONTAL_PX
                    pad_v = MODERN_HEADLINE_PADDING_VERTICAL_PX
                except ImportError:
                    pad_h = pad_v = MODERN_HEADLINE_PADDING_PX
                try:
                    from design_config import MODERN_HEADLINE_MAX_BOX_HEIGHT_RATIO, MODERN_HEADLINE_MIN_BOX_TOP_RATIO
                except ImportError:
                    MODERN_HEADLINE_MAX_BOX_HEIGHT_RATIO = 0.50
                    MODERN_HEADLINE_MIN_BOX_TOP_RATIO = 0.52
            except ImportError:
                HEADLINE_BOX_STYLE = "modern"
                MODERN_HEADLINE_MAX_BOX_HEIGHT_RATIO = 0.50
                MODERN_HEADLINE_MIN_BOX_TOP_RATIO = 0.52
                MODERN_HEADLINE_STROKE_WIDTH = 1
                MODERN_HEADLINE_STROKE_RATIO = 0
                MODERN_HEADLINE_STROKE_FILL = (0, 0, 0)
                MODERN_HEADLINE_MARGIN_RATIO = 0.05
                MODERN_HEADLINE_BORDER_RADIUS = 12
                MODERN_HEADLINE_BG_RGBA = (15, 25, 72, 0.95)
                MODERN_HEADLINE_BLUR_RADIUS = 10
                MODERN_HEADLINE_ACCENT_LEFT = (255, 255, 0)
                MODERN_HEADLINE_ACCENT_WIDTH = 6
                MODERN_HEADLINE_PADDING_PX = 28
                MODERN_HEADLINE_TEXT_INSET_LEFT = 10
                pad_h = pad_v = MODERN_HEADLINE_PADDING_PX
                MODERN_HEADLINE_MAX_WIDTH_PX = 960
                MODERN_HEADLINE_LINE_HEIGHT_RATIO = 1.25
                MODERN_HEADLINE_HIGHLIGHT_WORDS = 3
                MODERN_HEADLINE_HIGHLIGHT_WORDS_LIST = []
                MODERN_HEADLINE_WHITE_RGB = (255, 255, 255)
                MODERN_HEADLINE_TOP_BORDER = False
                MODERN_HEADLINE_TOP_BORDER_COLOR = (255, 200, 50)
                MODERN_HEADLINE_TEXT_SHADOW = (1, 1, 0)
                MODERN_HEADLINE_FONT_WEIGHT = "black"
                MODERN_HEADLINE_FONT_PATH = None
                MODERN_HEADLINE_MAX_WORDS = 15
                MODERN_HEADLINE_MAX_LINES = 2
                FROSTED_BOX_RGBA = (15, 20, 30, 160)
                FROSTED_BOX_RADIUS = 14
                FROSTED_BOX_OUTLINE_RGBA = (255, 255, 255, 80)
                FROSTED_BOX_OUTLINE_WIDTH = 1

            if HEADLINE_BOX_STYLE in ("modern", "frosted"):
                # --- Modern lower-third headline box (5% margin, rounded, frosted, left accent) ---
                # Headline is from get_short_headline_for_overlay: one complete sentence, ≤15 words
                raw_headline = headline_for_overlay
                words = raw_headline.split() if raw_headline else []
                headline_text = _dedupe_headline_text(" ".join(words[:MODERN_HEADLINE_MAX_WORDS]).strip() if words else "Breaking News")
                margin_px = max(50, int(min(w, h) * MODERN_HEADLINE_MARGIN_RATIO))
                box_width = w - 2 * margin_px
                # Text area: use left/right space efficiently with horizontal padding; full width for headline
                text_inset_left = MODERN_HEADLINE_TEXT_INSET_LEFT if HEADLINE_BOX_STYLE == "modern" else 0
                max_text_width = box_width - 2 * pad_h - text_inset_left
                max_text_width = min(MODERN_HEADLINE_MAX_WIDTH_PX, max(120, max_text_width))
                # Use config box ratio (allow up to 0.82) so space is used efficiently
                max_box_ratio = max(0.40, min(0.82, float(MODERN_HEADLINE_MAX_BOX_HEIGHT_RATIO)))
                min_top_ratio = max(0.35, min(0.65, float(MODERN_HEADLINE_MIN_BOX_TOP_RATIO)))
                max_box_height = max(80, int(h * max_box_ratio) - margin_px)
                available_text_height = max_box_height - 2 * pad_v
                tmp_img = Image.new("RGB", (1, 1))
                tmp_draw = ImageDraw.Draw(tmp_img)
                max_lines = MODERN_HEADLINE_MAX_LINES if MODERN_HEADLINE_MAX_LINES is not None else 4
                # Fit width must match drawable width: draw uses text_x + shrink(min(stroke)) while we used to wrap
                # to raw max_text_width, so lines were wider than the margin and clipped both sides (modern box).
                sh_fit = MODERN_HEADLINE_TEXT_SHADOW
                shadow_fit = (sh_fit[0], sh_fit[1]) if len(sh_fit) >= 2 else (2, 2)
                stroke_est = int(MODERN_HEADLINE_STROKE_WIDTH or 0)
                try:
                    if MODERN_HEADLINE_STROKE_RATIO and float(MODERN_HEADLINE_STROKE_RATIO) > 0:
                        stroke_est = max(stroke_est, int(120 * float(MODERN_HEADLINE_STROKE_RATIO)))
                except (TypeError, ValueError):
                    pass
                fit_column_width = shrink_width_for_stroke_shadow(max_text_width, stroke_est, shadow_fit)
                fit_column_width = max(80, int(fit_column_width))
                # Scaled headline: allow font to shrink further so the full headline stays complete
                # even after we reduce the box size/spacing.
                font, lines, _tw, _th = fit_text_in_box(
                    headline_text, fit_column_width, available_text_height,
                    # Slightly lower min_size to avoid any ellipsis/truncation when box size is reduced.
                    min_size=9, max_size=120, weight=MODERN_HEADLINE_FONT_WEIGHT, font_path=MODERN_HEADLINE_FONT_PATH,
                    line_spacing_ratio=MODERN_HEADLINE_LINE_HEIGHT_RATIO, draw=tmp_draw, max_lines=max_lines,
                )
                if not lines:
                    lines = [headline_text or "Breaking News"]
                # Headline always complete: if fit still returned too many lines (hit min_size), show all lines
                # so we never cut text; only trim to max_lines if we must avoid overflow (rare)
                if len(lines) > max_lines:
                    lines = lines[:max_lines]
                    last = lines[-1]
                    last_with_ellipsis = (last.rstrip() + " \u2026") if not (last.rstrip().endswith("\u2026") or last.rstrip().endswith("...")) else last
                    lines[-1] = _truncate_line_to_fit(tmp_draw, last_with_ellipsis, getattr(font, "size", 24), fit_column_width, MODERN_HEADLINE_FONT_PATH, MODERN_HEADLINE_FONT_WEIGHT, stroke_width=MODERN_HEADLINE_STROKE_WIDTH or 0)
                # Actual stroke may exceed stroke_est when STROKE_RATIO scales with font size; refit so wrap matches draw.
                _fz0 = getattr(font, "size", 24)
                _sw0 = (
                    max(1, int(_fz0 * float(MODERN_HEADLINE_STROKE_RATIO)))
                    if MODERN_HEADLINE_STROKE_RATIO and float(MODERN_HEADLINE_STROKE_RATIO) > 0
                    else int(MODERN_HEADLINE_STROKE_WIDTH or 0)
                )
                _draw_w0 = shrink_width_for_stroke_shadow(max_text_width, _sw0, shadow_fit)
                if _draw_w0 + 2 < fit_column_width:
                    font, lines, _tw, _th = fit_text_in_box(
                        headline_text, max(80, int(_draw_w0)), available_text_height,
                        min_size=9, max_size=120, weight=MODERN_HEADLINE_FONT_WEIGHT, font_path=MODERN_HEADLINE_FONT_PATH,
                        line_spacing_ratio=MODERN_HEADLINE_LINE_HEIGHT_RATIO, draw=tmp_draw, max_lines=max_lines,
                    )
                    if not lines:
                        lines = [headline_text or "Breaking News"]
                    if len(lines) > max_lines:
                        lines = lines[:max_lines]
                        last = lines[-1]
                        last_with_ellipsis = (last.rstrip() + " \u2026") if not (last.rstrip().endswith("\u2026") or last.rstrip().endswith("...")) else last
                        lines[-1] = _truncate_line_to_fit(
                            tmp_draw, last_with_ellipsis, getattr(font, "size", 24), max(80, int(_draw_w0)),
                            MODERN_HEADLINE_FONT_PATH, MODERN_HEADLINE_FONT_WEIGHT, stroke_width=_sw0,
                        )
                try:
                    bbox_ay = tmp_draw.textbbox((0, 0), "Ay", font=font)
                    line_height_px = int((bbox_ay[3] - bbox_ay[1]) * MODERN_HEADLINE_LINE_HEIGHT_RATIO)
                except TypeError:
                    line_height_px = int(getattr(font, "size", 24) * MODERN_HEADLINE_LINE_HEIGHT_RATIO)
                # Use fit_text_in_box's total height when valid so spacing matches; else derive from lines
                total_text_h = int(_th) if _th and _th > 0 else (len(lines) * line_height_px)
                box_height = min(2 * pad_v + total_text_h, max_box_height)
                box_left = margin_px
                # Ensure box stays in lower portion: top at or below configured ratio (never on top of image).
                min_box_top = int(h * min_top_ratio)
                box_top = max(min_box_top, h - margin_px - box_height)
                box_right = w - margin_px
                box_bottom = h - margin_px
                # Vertical center of text block within box.
                # Do NOT force an extra minimum top padding here; when the box is reduced,
                # enforcing padding can waste space or risk clipping. Center is more efficient.
                text_block_top_in_box = max(0, (box_height - total_text_h) // 2)
                img_rgba = img.convert("RGBA")
                if MODERN_HEADLINE_BLUR_RADIUS and MODERN_HEADLINE_BLUR_RADIUS > 0:
                    from PIL import ImageFilter
                    crop = img_rgba.crop((box_left, box_top, box_right, box_bottom))
                    crop = crop.filter(ImageFilter.GaussianBlur(radius=MODERN_HEADLINE_BLUR_RADIUS))
                    img_rgba.paste(crop, (box_left, box_top))
                overlay = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
                odraw = ImageDraw.Draw(overlay)
                if HEADLINE_BOX_STYLE == "frosted":
                    # Frosted Glass: rounded_rectangle with fill + thin white outline only (no left accent)
                    fill_frosted = FROSTED_BOX_RGBA
                    if len(fill_frosted) == 4 and fill_frosted[3] <= 1.0:
                        fill_frosted = (fill_frosted[0], fill_frosted[1], fill_frosted[2], int(fill_frosted[3] * 255))
                    outline_frosted = FROSTED_BOX_OUTLINE_RGBA
                    if len(outline_frosted) == 4 and outline_frosted[3] <= 1.0:
                        outline_frosted = (outline_frosted[0], outline_frosted[1], outline_frosted[2], int(outline_frosted[3] * 255))
                    rad_f = max(0, min(FROSTED_BOX_RADIUS, box_height // 2, box_width // 2))
                    if hasattr(odraw, "rounded_rectangle"):
                        odraw.rounded_rectangle(
                            [0, 0, box_width - 1, box_height - 1],
                            radius=rad_f,
                            fill=fill_frosted,
                            outline=outline_frosted,
                            width=FROSTED_BOX_OUTLINE_WIDTH,
                        )
                    else:
                        odraw.rectangle([0, 0, box_width - 1, box_height - 1], fill=fill_frosted)
                else:
                    # Modern: rounded fill + yellow left accent
                    r, g, b, a = MODERN_HEADLINE_BG_RGBA
                    fill_rgba = (r, g, b, int(a * 255) if a <= 1.0 else int(a))
                    rad = max(0, min(MODERN_HEADLINE_BORDER_RADIUS, box_height // 2, box_width // 2))
                    if hasattr(odraw, "rounded_rectangle"):
                        odraw.rounded_rectangle([0, 0, box_width - 1, box_height - 1], radius=rad, fill=fill_rgba)
                    else:
                        odraw.rectangle([0, 0, box_width - 1, box_height - 1], fill=fill_rgba)
                    odraw.rectangle([0, 0, MODERN_HEADLINE_ACCENT_WIDTH - 1, box_height - 1], fill=(*MODERN_HEADLINE_ACCENT_LEFT, 255))
                img_rgba.paste(overlay, (box_left, box_top), overlay)
                draw_rgba = ImageDraw.Draw(img_rgba)
                if HEADLINE_BOX_STYLE == "modern" and MODERN_HEADLINE_TOP_BORDER:
                    top_color = MODERN_HEADLINE_TOP_BORDER_COLOR if isinstance(MODERN_HEADLINE_TOP_BORDER_COLOR, (tuple, list)) else (255, 200, 50)
                    draw_rgba.line([(box_left, box_top), (box_right, box_top)], fill=tuple(top_color)[:3], width=1)
                text_x = box_left + pad_h + (MODERN_HEADLINE_TEXT_INSET_LEFT if HEADLINE_BOX_STYLE == "modern" else 0)
                text_y = box_top + text_block_top_in_box
                sh = MODERN_HEADLINE_TEXT_SHADOW
                shadow_offset = (sh[0], sh[1]) if len(sh) >= 2 else (2, 2)
                font_size = getattr(font, "size", 24)
                stroke_w = (max(1, int(font_size * MODERN_HEADLINE_STROKE_RATIO)) if MODERN_HEADLINE_STROKE_RATIO and float(MODERN_HEADLINE_STROKE_RATIO) > 0 else MODERN_HEADLINE_STROKE_WIDTH)
                stroke_fill = resolve_color(MODERN_HEADLINE_STROKE_FILL)
                # Keep stroke + shadow inside the box (glyph metrics understate ink extent)
                text_right_bound = text_x + shrink_width_for_stroke_shadow(
                    max_text_width, stroke_w, shadow_offset
                )
                white_rgb = MODERN_HEADLINE_WHITE_RGB if hasattr(MODERN_HEADLINE_WHITE_RGB, '__len__') and len(MODERN_HEADLINE_WHITE_RGB) >= 3 else (255, 255, 255)
                draw_left_aligned_headline(
                    draw_rgba, text_x, text_y, lines, font,
                    accent_color=MODERN_HEADLINE_ACCENT_LEFT,
                    white_color=tuple(white_rgb)[:3],
                    highlight_first_n_words=MODERN_HEADLINE_HIGHLIGHT_WORDS,
                    highlight_words_list=MODERN_HEADLINE_HIGHLIGHT_WORDS_LIST,
                    line_height_ratio=MODERN_HEADLINE_LINE_HEIGHT_RATIO,
                    shadow_offset=shadow_offset,
                    shadow_color=(0, 0, 0),
                    stroke_width=stroke_w,
                    stroke_fill=tuple(stroke_fill),
                    max_x=text_right_bound,
                )
                img = img_rgba.convert("RGB")
                draw = ImageDraw.Draw(img)
            else:
                # --- Minimal: full-width bar + headline only (no gradient overlay on image) ---
                draw = ImageDraw.Draw(img)

                # --- Bottom headline box: full red gradient or optional image-blend ---
                bar_height = max(base, _grid_snap(int(h * MINIMAL_HEADLINE_BAR_HEIGHT_RATIO), base))
                bar_y0 = h - bar_height
                bar_fill = _bar_color_from_context(ctx) or BAR_COLOR_BOTTOM
                bar_top_color = ctx.get("minimal_bar_top_border_color") or MINIMAL_HEADLINE_BAR_TOP_BORDER_COLOR
                if MINIMAL_HEADLINE_BAR_TOP_BORDER:
                    draw.line([(0, bar_y0), (w, bar_y0)], fill=bar_top_color, width=1)
                # Red gradient bar (complete gradient red) or image-blend gradient or solid
                use_red_gradient = False
                red_top = (220, 50, 50)
                red_bottom = (140, 20, 25)
                try:
                    from design_config import MINIMAL_HEADLINE_BAR_RED_GRADIENT, MINIMAL_HEADLINE_BAR_RED_TOP, MINIMAL_HEADLINE_BAR_RED_BOTTOM
                    use_red_gradient = MINIMAL_HEADLINE_BAR_RED_GRADIENT
                    red_top = MINIMAL_HEADLINE_BAR_RED_TOP
                    red_bottom = MINIMAL_HEADLINE_BAR_RED_BOTTOM
                except ImportError:
                    pass
                if use_red_gradient:
                    draw_gradient_rect(draw, 0, bar_y0, w, h, red_top, red_bottom, vertical=True)
                else:
                    use_bar_gradient = False
                    sample_h = 25
                    try:
                        from design_config import MINIMAL_HEADLINE_BAR_GRADIENT, MINIMAL_HEADLINE_BAR_GRADIENT_SAMPLE_HEIGHT
                        use_bar_gradient = MINIMAL_HEADLINE_BAR_GRADIENT
                        sample_h = max(5, min(80, MINIMAL_HEADLINE_BAR_GRADIENT_SAMPLE_HEIGHT))
                    except ImportError:
                        pass
                    if use_bar_gradient:
                        y_start = max(0, bar_y0 - sample_h)
                        band = img.crop((0, y_start, w, bar_y0))
                        pixels = list(band.getdata())
                        if pixels:
                            r = sum(p[0] for p in pixels) // len(pixels)
                            g = sum(p[1] for p in pixels) // len(pixels)
                            b = sum(p[2] for p in pixels) // len(pixels)
                            try:
                                from design_config import MINIMAL_HEADLINE_BAR_CAMOUFLAGE_BLEND
                                blend = max(0.3, min(0.95, float(MINIMAL_HEADLINE_BAR_CAMOUFLAGE_BLEND)))
                            except ImportError:
                                blend = 0.78
                            # Top of bar: mostly image color so it fades/camouflages; bottom stays dark for text
                            color_top = (
                                int(r * blend + bar_fill[0] * (1 - blend)),
                                int(g * blend + bar_fill[1] * (1 - blend)),
                                int(b * blend + bar_fill[2] * (1 - blend)),
                            )
                            draw_gradient_rect(draw, 0, bar_y0, w, h, color_top, bar_fill, vertical=True)
                        else:
                            draw.rectangle([0, bar_y0, w, h], fill=bar_fill)
                    else:
                        draw.rectangle([0, bar_y0, w, h], fill=bar_fill)
                # Bar texture overlay removed; only headline box, Breaking News label, logo, source, AI label remain.

                inner_pad = int(bar_height * MINIMAL_HEADLINE_INNER_PADDING_RATIO)
                raw_headline = headline_for_overlay
                words = raw_headline.split() if raw_headline else []
                headline_text = " ".join(words[:MINIMAL_HEADLINE_MAX_WORDS_IN_BOX]).strip() if words else "Breaking News"
                headline_text = _dedupe_headline_text(headline_text)
                available_height = bar_height - 2 * inner_pad
                # Viewport: headline must stay strictly inside the bar (no overflow).
                use_uniform_size = False
                uniform_ratio = 0.44
                try:
                    from design_config import MINIMAL_HEADLINE_UNIFORM_SIZE, MINIMAL_HEADLINE_FONT_SIZE_RATIO
                    use_uniform_size = MINIMAL_HEADLINE_UNIFORM_SIZE
                    uniform_ratio = MINIMAL_HEADLINE_FONT_SIZE_RATIO
                except ImportError:
                    pass
                if use_uniform_size:
                    headline_font_size_uniform = max(12, min(int(bar_height * uniform_ratio), int(available_height * 0.85)))
                    max_fs = headline_font_size_uniform
                    min_fs = max(MINIMAL_HEADLINE_MIN_FONT_SIZE, 8, headline_font_size_uniform // 2)  # pro min size; allow shrink so full line fits
                else:
                    min_fs = max(MINIMAL_HEADLINE_MIN_FONT_SIZE, 8, int(bar_height * MINIMAL_HEADLINE_FONT_SIZE_MIN_RATIO))
                    max_fs = min(int(bar_height * MINIMAL_HEADLINE_FONT_SIZE_MAX_RATIO), w // 2)
                    max_fs = min(max_fs, int(available_height * 0.85))
                line_center_y = bar_y0 + bar_height // 2
                margin_px = max(20, int(w * SAFE_ZONE_INSET_RATIO))  # safe zone: text inside inset (pro layout)
                inner_w = max(0, w - 2 * margin_px)
                max_line_width_px = shrink_width_for_stroke_shadow(
                    inner_w,
                    MINIMAL_HEADLINE_STROKE_WIDTH if MINIMAL_HEADLINE_STROKE else 0,
                    MINIMAL_HEADLINE_SHADOW_OFFSETS if MINIMAL_HEADLINE_SHADOW else None,
                )
                fill_ratio_by_margin = max_line_width_px / w if w > 0 else 0.85

                try:
                    from design_config import MINIMAL_HEADLINE_FONT_WEIGHT
                    default_weight = (MINIMAL_HEADLINE_FONT_WEIGHT or "black").lower()
                except ImportError:
                    default_weight = "black"
                headline_weight = (ctx.get("font_weight") or default_weight).lower()
                if headline_weight not in ("black", "bold", "regular"):
                    headline_weight = "black"
                try:
                    from design_config import MINIMAL_HEADLINE_FONT_PATH
                    headline_font_path = MINIMAL_HEADLINE_FONT_PATH
                except ImportError:
                    headline_font_path = None
                try:
                    from design_agent import shadow_tint_for_text_color
                    shadow_tint = ctx.get("shadow_tint") or "warm"
                    shadow_color = shadow_tint_for_text_color((0, 0, 0), shadow_tint)
                except ImportError:
                    shadow_color = (0, 0, 0)
                colors = MINIMAL_HEADLINE_COLORS
                use_multicolor = isinstance(colors, (list, tuple)) and len(colors) > 1

                fill_ratio = min(0.85, MINIMAL_HEADLINE_FILL_WIDTH_RATIO, fill_ratio_by_margin)
                use_two_lines = (MINIMAL_HEADLINE_WRAP_TWO_LINES and len(words) > MINIMAL_HEADLINE_WRAP_WORD_THRESHOLD)
                if use_two_lines:
                    tmp_fit = Image.new("RGB", (1, 1))
                    tmp_draw_fit = ImageDraw.Draw(tmp_fit)
                    font_fit, lines, _tw_fit, _th_fit = fit_text_in_box(
                        headline_text,
                        max_line_width_px,
                        available_height,
                        min_size=min_fs,
                        max_size=max_fs,
                        weight=headline_weight,
                        font_path=headline_font_path,
                        line_spacing_ratio=1.12,
                        draw=tmp_draw_fit,
                        max_lines=3,
                    )
                    if not lines:
                        lines = [headline_text]
                    block_font_size = getattr(font_fit, "size", min_fs)
                    gap = max(4, block_font_size // 10)
                    try:
                        bbox_ay = tmp_draw_fit.textbbox((0, 0), "Ay", font=font_fit)
                        line_height = bbox_ay[3] - bbox_ay[1]
                    except TypeError:
                        line_height = int(block_font_size * 1.1)
                    n_lines = len(lines)
                    total_block_h = n_lines * line_height + (n_lines - 1) * gap
                    top_y = bar_y0 + inner_pad + max(0, (available_height - total_block_h) // 2)
                    y_positions = [
                        top_y + i * (line_height + gap) + line_height // 2
                        for i in range(n_lines)
                    ]
                    max_height_per_line = max(8, line_height + 4)
                    for line_text, y_pos in zip(lines, y_positions):
                        if not (line_text or "").strip():
                            continue
                        if use_multicolor:
                            draw_centered_scaled_text_multicolor(
                                draw, line_text, w, y_pos,
                                colors=list(colors),
                                max_width_ratio=fill_ratio,
                                max_width_px=max_line_width_px,
                                font_path=headline_font_path,
                                weight=headline_weight,
                                min_size=block_font_size,
                                max_size=block_font_size,
                                shadow_offset=MINIMAL_HEADLINE_SHADOW_OFFSETS if MINIMAL_HEADLINE_SHADOW else None,
                                shadow_color=shadow_color,
                                force_upper=MINIMAL_HEADLINE_ALL_CAPS,
                                stroke_width=MINIMAL_HEADLINE_STROKE_WIDTH if MINIMAL_HEADLINE_STROKE else 0,
                                stroke_fill=MINIMAL_HEADLINE_STROKE_COLOR,
                                max_height=max_height_per_line,
                            )
                        else:
                            headline_color = (get_contrast_text_color(img, (0, bar_y0, w, h)) if USE_CONTRAST_HEADLINE_COLOR
                                             else (_headline_color_from_context(ctx) or MINIMAL_HEADLINE_COLOR))
                            draw_centered_scaled_text(
                                draw, line_text, w, y_pos,
                                max_width_ratio=fill_ratio,
                                max_width_px=max_line_width_px,
                                color=headline_color,
                                font_path=headline_font_path,
                                weight=headline_weight,
                                min_size=block_font_size,
                                max_size=block_font_size,
                                shadow_offset=MINIMAL_HEADLINE_SHADOW_OFFSETS if MINIMAL_HEADLINE_SHADOW else None,
                                shadow_color=shadow_color,
                                force_upper=MINIMAL_HEADLINE_ALL_CAPS,
                                stroke_width=MINIMAL_HEADLINE_STROKE_WIDTH if MINIMAL_HEADLINE_STROKE else 0,
                                stroke_fill=MINIMAL_HEADLINE_STROKE_COLOR,
                                max_height=max_height_per_line,
                            )
                else:
                    headline_color = (get_contrast_text_color(img, (0, bar_y0, w, h)) if USE_CONTRAST_HEADLINE_COLOR
                                     else (_headline_color_from_context(ctx) or MINIMAL_HEADLINE_COLOR))
                if not use_two_lines and not use_multicolor:
                    draw_centered_scaled_text(
                        draw, headline_text, w, line_center_y,
                        max_width_ratio=fill_ratio,
                        max_width_px=max_line_width_px,
                        color=headline_color,
                        font_path=headline_font_path,
                        weight=headline_weight,
                        min_size=min_fs,
                        max_size=max_fs,
                        shadow_offset=MINIMAL_HEADLINE_SHADOW_OFFSETS if MINIMAL_HEADLINE_SHADOW else None,
                        shadow_color=shadow_color,
                        force_upper=MINIMAL_HEADLINE_ALL_CAPS,
                        stroke_width=MINIMAL_HEADLINE_STROKE_WIDTH if MINIMAL_HEADLINE_STROKE else 0,
                        stroke_fill=MINIMAL_HEADLINE_STROKE_COLOR,
                    )
                elif use_multicolor:
                    draw_centered_scaled_text_multicolor(
                        draw, headline_text, w, line_center_y,
                        colors=list(colors),
                        max_width_ratio=fill_ratio,
                        max_width_px=max_line_width_px,
                        font_path=headline_font_path,
                        weight=headline_weight,
                        min_size=min_fs,
                        max_size=max_fs,
                        shadow_offset=MINIMAL_HEADLINE_SHADOW_OFFSETS if MINIMAL_HEADLINE_SHADOW else None,
                        shadow_color=shadow_color,
                        force_upper=MINIMAL_HEADLINE_ALL_CAPS,
                        stroke_width=MINIMAL_HEADLINE_STROKE_WIDTH if MINIMAL_HEADLINE_STROKE else 0,
                        stroke_fill=MINIMAL_HEADLINE_STROKE_COLOR,
                        max_height=available_height,
                    )

        # --- Top-left "Breaking News" label (optional; when off, only the main headline in the box is shown) ---
        if SHOW_BREAKING_LABEL:
            draw = ImageDraw.Draw(img)
            pad_x = max(base, int(label_h * BREAKING_LABEL_PAD_X_RATIO))
            pad_y = max(base, int(label_h * BREAKING_LABEL_PAD_Y_RATIO))
            font_size = max(14, min(32, label_h - pad_y))
            font = get_font_by_weight(font_size, "bold", BREAKING_LABEL_FONT_PATH)
            text = BREAKING_LABEL_TEXT
            try:
                tw = int(font.getlength(text))
            except (AttributeError, TypeError):
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
            th = font_size + 4
            label_w = tw + pad_x * 2
            label_h_actual = max(label_h, th + pad_y * 2)
            x0 = margin + BREAKING_LABEL_X_SHIFT
            y0 = margin + BREAKING_LABEL_Y_SHIFT
            x1 = x0 + label_w
            y1 = y0 + label_h_actual
            mid = x0 + int(label_w * 0.55)
            try:
                draw_gradient_rect(draw, x0, y0, mid, y1, BREAKING_LABEL_BG_RED, (160, 30, 45), vertical=True)
                draw_gradient_rect(draw, mid, y0, x1, y1, (30, 55, 180), BREAKING_LABEL_BG_BLUE, vertical=True)
            except Exception:
                draw.rectangle([x0, y0, x1, y1], fill=BREAKING_LABEL_BG_RED)
            if BREAKING_LABEL_TOP_BORDER:
                draw.line([(x0, y0), (x1, y0)], fill=(255, 255, 255), width=1)
            tx = x0 + (label_w - tw) // 2
            ty = y0 + (label_h_actual - th) // 2
            text_color = resolve_color(BREAKING_LABEL_TEXT_COLOR)
            try:
                draw.text((tx, ty), text, fill=text_color, font=font, anchor="lt")
            except TypeError:
                draw.text((tx, ty), text, fill=text_color, font=font)

        # --- The Unseen Economy logo (small, top-right): image if available, else text ---
        try:
            from design_config import (
                UNSEEN_ECONOMY_LOGO_IMAGE_PATH,
                UNSEEN_ECONOMY_LOGO_MAX_HEIGHT_RATIO,
                UNSEEN_ECONOMY_LOGO_TEXT,
                UNSEEN_ECONOMY_LOGO_FONT_SIZE_RATIO,
                UNSEEN_ECONOMY_LOGO_COLOR,
                UNSEEN_ECONOMY_LOGO_BRIGHTNESS,
                UNSEEN_ECONOMY_LOGO_MARGIN_RATIO,
                UNSEEN_ECONOMY_LOGO_INSET_RATIO,
            )
        except ImportError:
            UNSEEN_ECONOMY_LOGO_IMAGE_PATH = None
            UNSEEN_ECONOMY_LOGO_MAX_HEIGHT_RATIO = 0.12
            UNSEEN_ECONOMY_LOGO_TEXT = "The Unseen Economy"
            UNSEEN_ECONOMY_LOGO_FONT_SIZE_RATIO = 0.026
            UNSEEN_ECONOMY_LOGO_COLOR = (255, 255, 255)
            UNSEEN_ECONOMY_LOGO_BRIGHTNESS = 1.4
            UNSEEN_ECONOMY_LOGO_MARGIN_RATIO = 0.025
            UNSEEN_ECONOMY_LOGO_INSET_RATIO = 0.006
        # Minimal inset: push logo to extreme top-right
        logo_inset = max(4, int(short_side * UNSEEN_ECONOMY_LOGO_INSET_RATIO))
        logo_top = logo_inset
        logo_placed = False
        if UNSEEN_ECONOMY_LOGO_IMAGE_PATH and os.path.exists(UNSEEN_ECONOMY_LOGO_IMAGE_PATH):
            try:
                logo_img = Image.open(UNSEEN_ECONOMY_LOGO_IMAGE_PATH).convert("RGBA")
                lw0, lh0 = logo_img.size
                max_logo_h = max(20, int(h * UNSEEN_ECONOMY_LOGO_MAX_HEIGHT_RATIO))
                scale = min(1.0, max_logo_h / lh0, (w - 2 * logo_inset) / lw0) if lh0 and lw0 else 1.0
                new_lw = max(1, int(lw0 * scale))
                new_lh = max(1, int(lh0 * scale))
                logo_img = logo_img.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
                # Make logo very bright (boost brightness before paste; keep alpha)
                try:
                    brightness = max(1.0, min(2.0, float(UNSEEN_ECONOMY_LOGO_BRIGHTNESS)))
                except (TypeError, ValueError, AttributeError):
                    brightness = 1.4
                if brightness > 1.0:
                    from PIL import ImageEnhance
                    r, g, b, a = logo_img.split()
                    rgb = Image.merge("RGB", (r, g, b))
                    rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
                    r2, g2, b2 = rgb.split()
                    logo_img = Image.merge("RGBA", (r2, g2, b2, a))
                logo_x = w - logo_inset - new_lw
                logo_y = logo_top
                img_rgba = img.convert("RGBA")
                img_rgba.paste(logo_img, (logo_x, logo_y), logo_img)
                img = img_rgba.convert("RGB")
                draw = ImageDraw.Draw(img)
                logo_placed = True
            except Exception:
                pass
        if not logo_placed:
            logo_fs = max(10, min(28, int(short_side * UNSEEN_ECONOMY_LOGO_FONT_SIZE_RATIO)))
            logo_font = get_font_by_weight(logo_fs, "regular", None)
            try:
                logo_w = int(logo_font.getlength(UNSEEN_ECONOMY_LOGO_TEXT))
            except (AttributeError, TypeError):
                bbox = draw.textbbox((0, 0), UNSEEN_ECONOMY_LOGO_TEXT, font=logo_font)
                logo_w = bbox[2] - bbox[0]
            logo_x = w - logo_inset - logo_w
            logo_y = logo_top
            try:
                draw.text((logo_x, logo_y), UNSEEN_ECONOMY_LOGO_TEXT, fill=UNSEEN_ECONOMY_LOGO_COLOR, font=logo_font, anchor="lt")
            except TypeError:
                draw.text((logo_x, logo_y), UNSEEN_ECONOMY_LOGO_TEXT, fill=UNSEEN_ECONOMY_LOGO_COLOR, font=logo_font)

        # Source of the news at extreme bottom-left (font size 80% of AI Generated label)
        if source and str(source).strip():
            try:
                from design_config import AI_LABEL_FONT_SIZE_RATIO, AI_LABEL_MARGIN_RATIO
            except ImportError:
                AI_LABEL_FONT_SIZE_RATIO = 0.014
                AI_LABEL_MARGIN_RATIO = 0.006
            source_margin = max(3, int(short_side * AI_LABEL_MARGIN_RATIO))
            ai_label_font_size = max(6, min(18, int(short_side * AI_LABEL_FONT_SIZE_RATIO)))
            source_font_size = max(5, min(14, int(ai_label_font_size * 0.8)))
            source_font = get_font_by_weight(source_font_size, "regular", None)
            source_text = ("Source: " + str(source).strip())[:60]
            try:
                draw.text((source_margin, h - source_margin), source_text, fill=(255, 255, 255), font=source_font, anchor="lb")
            except TypeError:
                bbox = draw.textbbox((0, 0), source_text, font=source_font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text((source_margin, h - source_margin - th), source_text, fill=(255, 255, 255), font=source_font)

        # AI label on same image (one file open; no separate add_ai_generated_label pass)
        try:
            from ai_label import _draw_ai_label_on_image
            img = _draw_ai_label_on_image(img)
        except Exception:
            pass

        img.save(image_path, quality=OVERLAY_SAVE_QUALITY)
        return True
    except Exception as e:
        print(f"Minimal overlay failed: {e}")
        import traceback
        traceback.print_exc()
        return False
