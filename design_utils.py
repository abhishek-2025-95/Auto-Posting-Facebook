"""
Expert-grade design utilities: fonts (variable weights), gradients, tracking, vignette, anti-aliasing.
Uses Pillow only; optional Noto Sans family (Black, Bold, Regular) from fonts/.

Inspiration: contrast-based text color and fit-text-in-box ideas from caption-forge
(https://github.com/KvaytG/caption-forge) — automatically pick text color for legibility on any background.
Hex colors and proportional stroke / alignment shifts inspired by ComfyUI-TextOverlay
(https://github.com/Munkyfoot/ComfyUI-TextOverlay).
"""
import os


def hex_to_rgb(hex_str):
    """
    Convert hex color to (R, G, B). Accepts '#RRGGBB' or '#RGB' (3-char expands to 6).
    Returns (255, 255, 255) if invalid. Useful for config colors (e.g. "#FFFFFF").
    """
    h = (hex_str or "").strip().lstrip("#")
    if not h:
        return (255, 255, 255)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return (255, 255, 255)
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return (255, 255, 255)


def resolve_color(color):
    """
    Return (R, G, B) from either a hex string ('#FFFFFF') or a tuple/list (255, 255, 255).
    Lets config use hex or RGB interchangeably.
    """
    if color is None:
        return (255, 255, 255)
    if isinstance(color, str) and color.strip().startswith("#"):
        return hex_to_rgb(color)
    if isinstance(color, (list, tuple)) and len(color) >= 3:
        return (int(color[0]), int(color[1]), int(color[2]))
    return (255, 255, 255)

# notofonts/noto-fonts (static hinted TTF) works for auto-download; jsDelivr can 403 in some environments.
NOTOFONTS_RAW = "https://raw.githubusercontent.com/notofonts/noto-fonts/main/hinted/ttf/NotoSans"
NOTO_SANS_URLS = {
    "black": f"{NOTOFONTS_RAW}/NotoSans-Black.ttf",
    "bold": f"{NOTOFONTS_RAW}/NotoSans-Bold.ttf",
    "regular": f"{NOTOFONTS_RAW}/NotoSans-Regular.ttf",
}
_noto_download_warned = set()  # print download failure only once per weight per process


def get_pro_font(size, bold=True, font_path=None):
    """Load a professional font: config path > fonts/NotoSans-Bold.ttf > Segoe UI > Arial > default."""
    return get_font_by_weight(size, "bold" if bold else "regular", font_path)


def get_font_by_weight(size, weight="bold", font_path=None):
    """Load font by weight: black | bold | regular. Falls back to bold then system."""
    from PIL import ImageFont
    base = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base, "fonts")
    weight = (weight or "bold").lower()
    if weight not in ("black", "bold", "regular"):
        weight = "bold"
    fname = f"NotoSans-{weight.capitalize()}.ttf"
    path = os.path.join(fonts_dir, fname)
    if font_path and os.path.isfile(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    if not os.path.isfile(path):
        ensure_noto_font(weight)
    for p in (path, os.path.join(fonts_dir, "NotoSans-Bold.ttf"), "C:\\Windows\\Fonts\\segoeuib.ttf",
              "C:\\Windows\\Fonts\\arialbd.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            if p and os.path.isfile(p):
                return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def ensure_noto_font(weight="bold"):
    """Download Noto Sans (black/bold/regular) into fonts/ if missing. Falls back to system fonts if download fails."""
    global _noto_download_warned
    base = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    weight = weight.lower() if weight else "bold"
    if weight not in NOTO_SANS_URLS:
        weight = "bold"
    fname = f"NotoSans-{weight.capitalize()}.ttf"
    path = os.path.join(fonts_dir, fname)
    if os.path.isfile(path):
        return path
    url = NOTO_SANS_URLS.get(weight, NOTO_SANS_URLS["bold"])
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Python)"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) > 10000:
            with open(path, "wb") as f:
                f.write(data)
            return path
    except Exception:
        pass
    if weight not in _noto_download_warned:
        _noto_download_warned.add(weight)
        print(f"Optional: Noto Sans {weight} not downloaded; using system font (Segoe UI/Arial).")
    return None




def grid_snap(px, base=8):
    """Snap value to spatial grid (e.g. 8px). Professional layout uses consistent units."""
    b = max(1, int(base))
    return (int(px) // b) * b


def get_contrast_text_color(pil_image, region=None):
    """
    Pick a high-contrast text color (black or near-black / white or near-white) from the image
    so text stays readable on any background. Optional region = (x0, y0, x1, y1) to sample only
    that area (e.g. the headline bar); if None, uses the whole image.

    Inspired by caption-forge (https://github.com/KvaytG/caption-forge): average color → contrast
    color with a push away from mid-gray for clearer legibility.
    """
    from PIL import Image
    if pil_image is None:
        return (255, 255, 255)
    img = pil_image.convert("RGB")
    if region is not None:
        x0, y0, x1, y1 = [int(x) for x in region]
        x0, x1 = max(0, x0), min(img.width, x1)
        y0, y1 = max(0, y0), min(img.height, y1)
        if x1 <= x0 or y1 <= y0:
            return (255, 255, 255)
        img = img.crop((x0, y0, x1, y1))
    pixels = list(img.getdata())
    if not pixels:
        return (255, 255, 255)
    n = len(pixels)
    r = sum(p[0] for p in pixels) / n
    g = sum(p[1] for p in pixels) / n
    b = sum(p[2] for p in pixels) / n
    avg = (r, g, b)
    # Contrast color: invert then push away from 128 for stronger black or white
    out = []
    for c in avg:
        inv = 255 - c
        if inv < 128:
            inv = max(0, inv - 40)
        else:
            inv = min(255, inv + 40)
        out.append(int(round(inv)))
    return tuple(out)


def get_text_width_with_tracking(draw, text, font, tracking_px):
    """Total width of text when drawn with given tracking (letter-by-letter). tracking_px < 0 = tight."""
    if not text:
        return 0
    total = 0
    for i, c in enumerate(text):
        if i > 0:
            total += tracking_px  # negative = subtract
        try:
            total += font.getlength(c)
        except (AttributeError, TypeError):
            bbox = draw.textbbox((0, 0), c, font=font)
            total += bbox[2] - bbox[0]
    return int(total)


def draw_gradient_rect(draw, x0, y0, x1, y1, color_top, color_bottom, vertical=True):
    """Fill rectangle with linear gradient (Pillow). color_* are (R,G,B)."""
    w = x1 - x0
    h = y1 - y0
    n = max(h if vertical else w, 1)
    for i in range(n):
        t = i / n
        c = tuple(int(color_top[j] + (color_bottom[j] - color_top[j]) * t) for j in range(3))
        if vertical:
            draw.line([(x0, y0 + i), (x1, y0 + i)], fill=c, width=1)
        else:
            draw.line([(x0 + i, y0), (x0 + i, y1)], fill=c, width=1)


def apply_bottom_third_black_gradient(img, alpha_max=0.6):
    """
    Apply a semi-transparent black gradient over the bottom third of the image
    (alpha 0 at top of that third to alpha_max at bottom) to improve text legibility.
    Modifies img in place; img must be RGB.
    """
    from PIL import Image
    if not img or img.mode != "RGB":
        return
    w, h = img.size
    y0 = h - (h // 3)  # bottom third
    if y0 >= h:
        return
    overlay = Image.new("RGB", (w, h), (0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    mask_px = mask.load()
    region_h = h - y0
    for y in range(y0, h):
        t = (y - y0) / region_h if region_h else 1.0
        alpha = int(255 * alpha_max * t)
        for x in range(w):
            mask_px[x, y] = alpha
    composited = Image.composite(overlay, img, mask)
    img.paste(composited, (0, 0))


def shrink_width_for_stroke_shadow(width_px, stroke_width=0, shadow_offset=None):
    """
    Reduce a nominal max line width so glyph + outline + horizontal drop-shadow
    stays inside the canvas (Pillow stroke draws outside the fill bbox).
    """
    try:
        w = float(width_px)
    except (TypeError, ValueError):
        return 40
    sw = int(stroke_width or 0)
    max_dx = 0
    if shadow_offset:
        offs = shadow_offset if isinstance(shadow_offset, list) else [shadow_offset]
        for off in offs:
            try:
                max_dx = max(max_dx, abs(int(off[0])))
            except (TypeError, ValueError, IndexError):
                pass
    # Each side: half stroke blob + shadow shift; +4px safety for subpixel/kerning
    return max(40, int(w - 2 * sw - 2 * max_dx - 4))


def _draw_shadow_layers(draw, shadow_offset, shadow_color, x, y, text, font, anchor="mm"):
    """Draw one or more shadow layers. shadow_offset can be (dx,dy) or [(dx,dy), ...] for strong drop-shadow."""
    if not shadow_offset:
        return
    offsets = shadow_offset if isinstance(shadow_offset, list) else [shadow_offset]
    kwargs = {} if anchor is None else {"anchor": anchor}
    for off in offsets:
        dx, dy = off[0], off[1]
        draw.text((x + dx, y + dy), text, fill=shadow_color, font=font, **kwargs)


def draw_text_with_shadow(draw, xy, text, font, fill, shadow_offset=(2, 2), shadow_color=(0, 0, 0), anchor=None):
    """Draw text with a simple offset shadow (drawn first). anchor='mm' for geometric center (Pillow 8+)."""
    x, y = xy
    sx, sy = shadow_offset
    kwargs = {} if anchor is None else {"anchor": anchor}
    draw.text((x + sx, y + sy), text, fill=shadow_color, font=font, **kwargs)
    draw.text((x, y), text, fill=fill, font=font, **kwargs)


def draw_text_with_stroke(draw, xy, text, font, fill, stroke_width=1, stroke_fill=(0, 0, 0), anchor=None):
    """
    Draw text with a thin outline (stroke) for readability on any background.
    Draws stroke first by offset copies, then fill on top. anchor e.g. 'mm' (Pillow 8+).
    """
    if not text:
        return
    kwargs = {} if anchor is None else {"anchor": anchor}
    sw = max(1, int(stroke_width))
    for dx in range(-sw, sw + 1):
        for dy in range(-sw, sw + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((xy[0] + dx, xy[1] + dy), text, fill=stroke_fill, font=font, **kwargs)
    draw.text(xy, text, fill=fill, font=font, **kwargs)


def draw_text_centered_mm(draw, cx, cy, text, font, fill, shadow_offset=None, shadow_color=(0, 0, 0)):
    """
    Draw text with anchor='mm' (middle-middle) so (cx, cy) is the true geometric center.
    Fixes ascenders/descenders throwing off centering. Pillow 8+. Falls back to bbox center if anchor unsupported.
    """
    try:
        kwargs = {"anchor": "mm"}
        if shadow_offset:
            draw.text((cx + shadow_offset[0], cy + shadow_offset[1]), text, fill=shadow_color, font=font, **kwargs)
        draw.text((cx, cy), text, fill=fill, font=font, **kwargs)
    except TypeError:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = cx - tw // 2, cy - th // 2
        if shadow_offset:
            draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, fill=shadow_color, font=font)
        draw.text((x, y), text, fill=fill, font=font)


def draw_text_with_tracking(draw, x, y, text, font, fill, tracking=0, shadow_offset=None, shadow_color=(0, 0, 0), anchor=None):
    """
    Draw text with custom letter-spacing (tracking). tracking in pixels; negative = tight/urgent.
    Uses font.getlength(letter) when available for accurate kerning. anchor: e.g. "mm" for middle-middle (Pillow 8+).
    """
    if not text:
        return
    sx, sy = (shadow_offset[0], shadow_offset[1]) if shadow_offset else (0, 0)
    cur_x = x
    kwargs = {} if anchor is None else {"anchor": anchor}
    for i, c in enumerate(text):
        if i > 0:
            cur_x += tracking  # tracking is negative for tight, so we add (e.g. -2)
        if shadow_offset:
            draw.text((cur_x + sx, y + sy), c, fill=shadow_color, font=font, **kwargs)
        draw.text((cur_x, y), c, fill=fill, font=font, **kwargs)
        try:
            cur_x += font.getlength(c)
        except (AttributeError, TypeError):
            bbox = draw.textbbox((0, 0), c, font=font)
            cur_x += bbox[2] - bbox[0]


def dynamic_font_size_for_line(draw, line, max_width, weight="bold", font_path=None, min_size=14, max_size=120):
    """
    Find font size so that line fits in max_width (e.g. 90% of canvas). Iterate until width matches target.
    Returns (font, width_used). Uses getbbox for measurement.
    """
    size = max_size
    font = get_font_by_weight(size, weight, font_path)
    try:
        w = int(font.getlength(line))
    except (AttributeError, TypeError):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
    while w > max_width and size > min_size:
        size = max(min_size, size - 2)
        font = get_font_by_weight(size, weight, font_path)
        try:
            w = int(font.getlength(line))
        except (AttributeError, TypeError):
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
    return font, w


def line_width_multicolor_drawing(font, line, draw=None, space_w=None):
    """
    Effective line width when words are drawn one-by-one (as in draw_centered_scaled_text_multicolor).
    Sum of per-word getlengths + spaces is often **wider** than getlength("whole line") because
    cross-word kerning is applied only on joined layout — per-word drawing misses that tightening,
    which is the main cause of horizontal clipping on multicolor headlines.
    """
    line = (line or "").strip()
    if not line:
        return 0
    words = line.split()
    if not words:
        return 0
    if space_w is None:
        try:
            space_w = int(font.getlength(" "))
        except (AttributeError, TypeError):
            space_w = max(1, int(getattr(font, "size", 12) or 12) // 2)
    sep = 0
    for wd in words:
        try:
            sep += int(font.getlength(wd))
        except (AttributeError, TypeError):
            if draw is not None:
                bbox = draw.textbbox((0, 0), wd, font=font)
                sep += bbox[2] - bbox[0]
            else:
                sep += len(wd) * max(2, space_w)
    if len(words) > 1:
        sep += (len(words) - 1) * space_w
    try:
        joined = int(font.getlength(line))
    except (AttributeError, TypeError):
        if draw is not None:
            bbox = draw.textbbox((0, 0), line, font=font)
            joined = bbox[2] - bbox[0]
        else:
            joined = sep
    return max(sep, joined)


def wrap_text_to_width(text, font, max_width_px, draw=None):
    """
    Word-wrap a string so each line fits within max_width_px when rendered with the given font.
    Uses conservative width: max(joined string, per-word-sum) so lines still fit when drawn
    word-by-word (multicolor). Returns list of lines.
    """
    if not text or max_width_px <= 0:
        return [text] if text else []
    words = text.strip().split()
    if not words:
        return []
    lines = []
    current = []
    try:
        space_w = int(font.getlength(" "))
    except (AttributeError, TypeError):
        space_w = max(1, int(font.size or 12) // 2) if hasattr(font, "size") else 8
    for word in words:
        candidate = current + [word]
        line_str = " ".join(candidate)
        w = line_width_multicolor_drawing(font, line_str, draw, space_w)
        if w <= max_width_px:
            current = candidate
        else:
            if current:
                lines.append(" ".join(current))
            try:
                word_w = int(font.getlength(word))
            except (AttributeError, TypeError):
                word_w = len(word) * space_w * 2
            if word_w > max_width_px:
                lines.append(word)
                current = []
            else:
                current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _text_block_size(draw, font, lines, line_spacing_ratio=1.2):
    """Return (total_width_px, total_height_px) for a block of lines rendered with font.
    Uses multiline_textbbox when available (Pillow 9.2+) for accurate height with spacing."""
    if not lines or not font:
        return 0, 0
    try:
        bbox = draw.textbbox((0, 0), "Ay", font=font)
        line_height = bbox[3] - bbox[1]
    except TypeError:
        line_height = getattr(font, "size", 12) * 1.25
    gap = max(2, int(line_height * (line_spacing_ratio - 1.0)))
    total_width = 0
    for line in lines:
        w = line_width_multicolor_drawing(font, line, draw, space_w=None)
        total_width = max(total_width, w)
    if len(lines) > 1 and hasattr(draw, "multiline_textbbox"):
        try:
            multi_bbox = draw.multiline_textbbox(
                (0, 0), "\n".join(lines), font=font, spacing=gap
            )
            total_height = multi_bbox[3] - multi_bbox[1]
            return total_width, total_height
        except (TypeError, Exception):
            pass
    total_height = len(lines) * line_height + (len(lines) - 1) * gap
    return total_width, total_height


def fit_text_in_box(text, box_width_px, box_height_px, min_size=8, max_size=120, weight="bold", font_path=None,
                    line_spacing_ratio=1.2, draw=None, max_lines=None):
    """
    Find a font size so that the wrapped text block fits inside the given bounding box (centered).
    Uses a loop to decrement font size until the entire block fits without overflowing.
    If max_lines is set (e.g. 2), keeps shrinking font until the wrapped text has at most that many lines.

    Returns:
        (font, lines, total_width_px, total_height_px)
        - font: PIL ImageFont to use for drawing
        - lines: list of wrapped lines at that font (at most max_lines if set)
        - total_width_px, total_height_px: rendered block dimensions (for centering in the box)

    If no size fits (e.g. too much text), returns the smallest size attempt (best effort).
    """
    from PIL import Image, ImageDraw
    if not text or box_width_px <= 0 or box_height_px <= 0:
        font = get_font_by_weight(min_size, weight, font_path)
        return font, [text.strip()] if text and text.strip() else [], 0, 0
    if draw is None:
        tmp = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(tmp)
    size = max_size
    font = get_font_by_weight(size, weight, font_path)
    lines = wrap_text_to_width(text, font, box_width_px, draw=draw)
    total_width, total_height = _text_block_size(draw, font, lines, line_spacing_ratio)
    def overflows():
        if total_height > box_height_px or total_width > box_width_px:
            return True
        if max_lines is not None and len(lines) > max_lines:
            return True
        return False
    while overflows() and size > min_size:
        size = max(min_size, size - 2)
        font = get_font_by_weight(size, weight, font_path)
        lines = wrap_text_to_width(text, font, box_width_px, draw=draw)
        total_width, total_height = _text_block_size(draw, font, lines, line_spacing_ratio)
    return font, lines, int(total_width), int(total_height)


def draw_left_aligned_headline(draw, x0, y0, lines, font, accent_color=(255, 215, 0), white_color=(255, 255, 255),
                               highlight_first_n_words=3, highlight_words_list=None, line_height_ratio=1.3,
                               shadow_offset=(2, 2), shadow_color=(0, 0, 0), stroke_width=0, stroke_fill=(0, 0, 0),
                               max_x=None):
    """
    Draw wrapped headline left-aligned. Word-by-word offset (typewriter) so spacing is exact.
    Text is constrained to the viewport: if max_x is set, any word that would go past max_x wraps to the next line
    (equivalent to overflow-wrap: break-word / white-space: normal so nothing bleeds off the right edge).
    Highlighting: if highlight_words_list is non-empty, any word matching it (case-insensitive) gets accent_color;
    otherwise first highlight_first_n_words get accent, rest white. line_height_ratio 1.3 = 130%.
    stroke_width/stroke_fill = thin black outline for legibility (Pillow 8.2+).
    """
    if not lines or not font:
        return
    try:
        bbox = draw.textbbox((0, 0), "Ay", font=font)
        line_height_px = int((bbox[3] - bbox[1]) * line_height_ratio)
    except TypeError:
        line_height_px = int(getattr(font, "size", 24) * line_height_ratio)
    try:
        space_w = int(font.getlength(" "))
    except (AttributeError, TypeError):
        space_w = max(1, getattr(font, "size", 24) // 2)
    stroke_kw = {}
    if stroke_width and stroke_width > 0 and stroke_fill is not None:
        stroke_kw = {"stroke_width": stroke_width, "stroke_fill": stroke_fill}
    use_smart_highlight = highlight_words_list and len(highlight_words_list) > 0
    highlight_set = {w.strip().upper() for w in highlight_words_list if w.strip()} if use_smart_highlight else set()
    word_index = 0
    line_index = 0
    y_pos = y0
    x = x0
    for i, line in enumerate(lines):
        if i > 0:
            line_index += 1
            y_pos = y0 + line_index * line_height_px
            x = x0
        words = line.split()
        for w in words:
            try:
                w_w = int(font.getlength(w))
            except (AttributeError, TypeError):
                bbox = draw.textbbox((0, 0), w, font=font)
                w_w = bbox[2] - bbox[0]
            # Viewport constraint: if this word would bleed past max_x, wrap to next line (overflow-wrap behavior)
            pad_r = 0
            if stroke_width:
                try:
                    pad_r = int(stroke_width)
                except (TypeError, ValueError):
                    pad_r = 0
            if shadow_offset:
                offs = shadow_offset if isinstance(shadow_offset, list) else [shadow_offset]
                for off in offs:
                    try:
                        pad_r = max(pad_r, abs(int(off[0])))
                    except (TypeError, ValueError, IndexError):
                        pass
            eff_max_x = max_x
            if eff_max_x is not None:
                eff_max_x = eff_max_x - pad_r
            if eff_max_x is not None and x + w_w > eff_max_x and x > x0:
                line_index += 1
                y_pos = y0 + line_index * line_height_px
                x = x0
            if use_smart_highlight:
                color = accent_color if (w.upper() in highlight_set) else white_color
            else:
                color = accent_color if word_index < highlight_first_n_words else white_color
            if shadow_offset:
                draw.text((x + shadow_offset[0], y_pos + shadow_offset[1]), w, fill=shadow_color, font=font, **stroke_kw)
            draw.text((x, y_pos), w, fill=color, font=font, **stroke_kw)
            x += w_w + space_w
            word_index += 1
    return


def draw_centered_wrapped_text(draw, text, image_width, y_center, font, max_width_px=900,
                               color=(255, 255, 255), stroke_width=0, stroke_fill=(0, 0, 0),
                               shadow_offset=None, shadow_color=(0, 0, 0), line_spacing_ratio=1.2):
    """
    Word-wrap text to max_width_px, then draw the multi-line block center-aligned on the image.
    y_center is the vertical center of the whole block. Uses font.getlength() for wrap calculation.
    """
    if not text or not font:
        return
    lines = wrap_text_to_width(text, font, max_width_px, draw=draw)
    if not lines:
        return
    try:
        space_w = int(font.getlength(" "))
    except (AttributeError, TypeError):
        space_w = max(1, getattr(font, "size", 12) // 2)
    bbox = draw.textbbox((0, 0), "Ay", font=font)
    line_height = bbox[3] - bbox[1]
    gap = max(2, int(line_height * (line_spacing_ratio - 1.0)))
    total_height = len(lines) * line_height + (len(lines) - 1) * gap
    y_start = y_center - total_height / 2.0 + line_height / 2.0
    cx = image_width / 2.0
    kwargs = {"anchor": "mm", "font": font}
    for i, line in enumerate(lines):
        y_pos = y_start + i * (line_height + gap)
        xy = (cx, y_pos)
        if shadow_offset:
            draw.text((cx + shadow_offset[0], y_pos + shadow_offset[1]), line, fill=shadow_color, **kwargs)
        if stroke_width and stroke_width > 0:
            draw_text_with_stroke(draw, xy, line, font, color, stroke_width=stroke_width, stroke_fill=stroke_fill, anchor="mm")
        else:
            draw.text(xy, line, fill=color, **kwargs)


def draw_centered_scaled_text(draw, text, image_width, y_position, max_width_ratio=0.9, color=(255, 255, 255),
                              font_path=None, weight="bold", min_size=10, max_size=100, shadow_offset=None,
                              shadow_color=(0, 0, 0), force_upper=True, stroke_width=0, stroke_fill=(0, 0, 0),
                              max_height=None, max_width_px=None):
    """
    Dynamic font size: fit width (and max_width_px so text stays inside image) and optionally max_height.
    Draw at (image_width/2, y_position) with anchor="mm". Ensures text never goes out of image.
    """
    if not text:
        return
    display_text = text.upper() if force_upper else text
    # When max_width_px is set, callers (e.g. minimal overlay) already baked in margins + stroke/shadow
    # halo — use it as-is. Do not also apply max_width_ratio (would clip vs fit_text_in_box) or shrink twice.
    if max_width_px is not None and max_width_px > 0:
        max_width = min(float(max_width_px), float(image_width))
    else:
        max_width = shrink_width_for_stroke_shadow(
            image_width * max_width_ratio, stroke_width, shadow_offset
        )
    font_size = max_size
    font = get_font_by_weight(font_size, weight, font_path)
    try:
        w = int(font.getlength(display_text))
    except (AttributeError, TypeError):
        bbox = draw.textbbox((0, 0), display_text, font=font)
        w = bbox[2] - bbox[0]
    while w > max_width and font_size > min_size:
        font_size -= 2
        font = get_font_by_weight(font_size, weight, font_path)
        try:
            w = int(font.getlength(display_text))
        except (AttributeError, TypeError):
            bbox = draw.textbbox((0, 0), display_text, font=font)
            w = bbox[2] - bbox[0]
    if max_height is not None and max_height > 0:
        bbox = draw.textbbox((0, 0), display_text, font=font)
        th = bbox[3] - bbox[1]
        extra = (2 * stroke_width) if stroke_width else 0
        while (th + extra) > max_height and font_size > min_size:
            font_size -= 2
            font = get_font_by_weight(font_size, weight, font_path)
            bbox = draw.textbbox((0, 0), display_text, font=font)
            th = bbox[3] - bbox[1]
    cx = image_width / 2
    xy = (cx, y_position)
    kwargs = {"anchor": "mm"}
    _draw_shadow_layers(draw, shadow_offset, shadow_color, cx, y_position, display_text, font, **kwargs)
    try:
        if stroke_width and stroke_width > 0:
            draw_text_with_stroke(draw, xy, display_text, font, color, stroke_width=stroke_width, stroke_fill=stroke_fill, anchor="mm")
        else:
            draw.text(xy, display_text, fill=color, font=font, **kwargs)
    except TypeError:
        bbox = draw.textbbox((0, 0), display_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = cx - tw // 2, y_position - th // 2
        xy = (x, y)
        _draw_shadow_layers(draw, shadow_offset, shadow_color, x, y, display_text, font, anchor=None)
        if stroke_width and stroke_width > 0:
            draw_text_with_stroke(draw, xy, display_text, font, color, stroke_width=stroke_width, stroke_fill=stroke_fill, anchor=None)
        else:
            draw.text(xy, display_text, fill=color, font=font)


def draw_centered_scaled_text_multicolor(draw, text, image_width, y_position, colors, max_width_ratio=0.72,
                                         font_path=None, weight="bold", min_size=10, max_size=80, shadow_offset=None,
                                         shadow_color=(0, 0, 0), force_upper=False, stroke_width=0, stroke_fill=(0, 0, 0),
                                         max_height=None, max_width_px=None):
    """
    Draw headline with multiple colours (one per word, cycling). Scales to fit width and max_height so text stays inside image.
    """
    if not text or not colors:
        return
    display_text = text.upper() if force_upper else text
    words = display_text.split()
    if not words:
        return
    full = " ".join(words)
    if max_width_px is not None and max_width_px > 0:
        max_width = min(float(max_width_px), float(image_width))
    else:
        max_width = shrink_width_for_stroke_shadow(
            image_width * max_width_ratio, stroke_width, shadow_offset
        )
    # Small slack so stroke / subpixel rounding never kisses the edge
    max_width = max(40, int(max_width) - 2)
    sw_line = int(stroke_width or 0)
    font_size = max_size
    font = get_font_by_weight(font_size, weight, font_path)
    line_total_m = line_width_multicolor_drawing(font, full, draw, space_w=None)
    while line_total_m + 2 * sw_line > max_width and font_size > min_size:
        font_size -= 2
        font = get_font_by_weight(font_size, weight, font_path)
        line_total_m = line_width_multicolor_drawing(font, full, draw, space_w=None)
    if max_height is not None and max_height > 0:
        bbox = draw.textbbox((0, 0), full, font=font)
        th = bbox[3] - bbox[1]
        extra = (2 * stroke_width) if stroke_width else 0
        while (th + extra) > max_height and font_size > min_size:
            font_size -= 2
            font = get_font_by_weight(font_size, weight, font_path)
            bbox = draw.textbbox((0, 0), full, font=font)
            th = bbox[3] - bbox[1]
        line_total_m = line_width_multicolor_drawing(font, full, draw, space_w=None)
        while line_total_m + 2 * sw_line > max_width and font_size > min_size:
            font_size -= 2
            font = get_font_by_weight(font_size, weight, font_path)
            line_total_m = line_width_multicolor_drawing(font, full, draw, space_w=None)
    sw = int(stroke_width or 0)
    max_dx = 0
    if shadow_offset:
        _offs = shadow_offset if isinstance(shadow_offset, list) else [shadow_offset]
        for off in _offs:
            try:
                max_dx = max(max_dx, abs(int(off[0])))
            except (TypeError, ValueError, IndexError):
                pass
    margin_safe = max(12, sw + max_dx + 8)
    # Safety: per-word sum + outline extent must stay within budget
    line_total = 0
    while font_size > min_size:
        try:
            space_w = int(font.getlength(" "))
        except (AttributeError, TypeError):
            space_w = font_size // 2
        word_widths = []
        for word in words:
            try:
                w = int(font.getlength(word))
            except (AttributeError, TypeError):
                bbox = draw.textbbox((0, 0), word, font=font)
                w = bbox[2] - bbox[0]
            word_widths.append(w)
        line_total = line_width_multicolor_drawing(font, full, draw, space_w)
        if line_total + 2 * sw <= max_width:
            break
        font_size -= 2
        font = get_font_by_weight(font_size, weight, font_path)
    try:
        space_w = int(font.getlength(" "))
    except (AttributeError, TypeError):
        space_w = font_size // 2
    word_widths = []
    for word in words:
        try:
            w = int(font.getlength(word))
        except (AttributeError, TypeError):
            bbox = draw.textbbox((0, 0), word, font=font)
            w = bbox[2] - bbox[0]
        word_widths.append(w)
    line_total = line_width_multicolor_drawing(font, full, draw, space_w)
    start_x = (image_width - line_total) / 2
    start_x = max(margin_safe, min(image_width - margin_safe - line_total, start_x))
    cx = float(start_x)
    for i, word in enumerate(words):
        color = colors[i % len(colors)]
        x = int(round(cx + word_widths[i] / 2.0))
        xy = (x, y_position)
        try:
            _draw_shadow_layers(draw, shadow_offset, shadow_color, x, y_position, word, font, anchor="mm")
            if stroke_width and stroke_width > 0:
                draw_text_with_stroke(draw, xy, word, font, color, stroke_width=stroke_width, stroke_fill=stroke_fill, anchor="mm")
            else:
                draw.text(xy, word, fill=color, font=font, anchor="mm")
        except TypeError:
            bbox = draw.textbbox((0, 0), word, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x_lt = int(round(cx))
            y_lt = y_position - th // 2
            _draw_shadow_layers(draw, shadow_offset, shadow_color, x_lt, y_lt, word, font, anchor=None)
            if stroke_width and stroke_width > 0:
                draw_text_with_stroke(draw, (x_lt + tw // 2, y_position), word, font, color, stroke_width=stroke_width, stroke_fill=stroke_fill, anchor=None)
            else:
                draw.text((x_lt, y_lt), word, fill=color, font=font)
        cx += float(word_widths[i] + space_w)


def apply_vignette(img, strength=0.25, power=2):
    """Subtle dark vignette: draws eye to center. strength 0.25–0.35; power 2 = smoother falloff. Modifies img in place (RGB)."""
    import math
    if not img or strength <= 0:
        return
    w, h = img.size
    cx, cy = w / 2.0, h / 2.0
    max_r = math.sqrt(cx * cx + cy * cy)
    if max_r <= 0:
        return
    out = img.load()
    power = max(1, power)
    for py in range(h):
        for px in range(w):
            r = math.sqrt((px - cx) ** 2 + (py - cy) ** 2) / max_r
            r = r ** power
            factor = 1.0 - strength * r
            c = out[px, py]
            out[px, py] = (int(c[0] * factor), int(c[1] * factor), int(c[2] * factor))
    return


def apply_color_grade(img, contrast=1.0, saturation=1.0):
    """Apply contrast and saturation (ImageEnhance). Returns new image."""
    from PIL import ImageEnhance
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if saturation != 1.0:
        img = ImageEnhance.Color(img).enhance(saturation)
    return img


def draw_text_with_colored_glow(draw, img, x, y, text, font, fill, shadow_rgb, blur_radius=4):
    """
    Draw text with a colored, blurred glow (no hard black shadow). Draws glow on a temp layer, blurs, composites, then text.
    img is the PIL Image (for size/paste); draw is ImageDraw.Draw(img).
    """
    from PIL import Image, ImageDraw, ImageFilter
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = max(blur_radius * 3, 8)
    layer = Image.new("RGBA", (int(tw + pad * 2), int(th + pad * 2)), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    ldraw.text((pad - bbox[0], pad - bbox[1]), text, fill=(*shadow_rgb, 200), font=font)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    img.paste(layer, (int(x) - pad + bbox[0], int(y) - pad + bbox[1]), layer)
    draw.text((x, y), text, fill=fill, font=font)


def apply_bar_texture(img, bar_y0, bar_height, w, opacity=0.05):
    """
    Add subtle noise texture over the bar region (broadcast-style depth). Modifies img in place (RGB).
    opacity 0.03–0.08 typical.
    """
    import random
    from PIL import Image
    if opacity <= 0:
        return
    out = img.load()
    for py in range(bar_y0, min(bar_y0 + bar_height, img.size[1])):
        for px in range(w):
            n = random.randint(0, 255)
            c = out[px, py]
            out[px, py] = (
                int(c[0] * (1 - opacity) + n * opacity),
                int(c[1] * (1 - opacity) + n * opacity),
                int(c[2] * (1 - opacity) + n * opacity),
            )
    return


def apply_post_process(image_path):
    """Optional light sharpen and save (professional crisp). Uses design_config POST_SHARPEN, SHARPEN_FACTOR, OVERLAY_SAVE_QUALITY."""
    if not image_path or not os.path.exists(image_path):
        return
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        try:
            from design_config import POST_SHARPEN, SHARPEN_FACTOR, OVERLAY_SAVE_QUALITY
        except ImportError:
            POST_SHARPEN = False
            SHARPEN_FACTOR = 1.2
            OVERLAY_SAVE_QUALITY = 95
        img = Image.open(image_path).convert("RGB")
        if POST_SHARPEN and SHARPEN_FACTOR and SHARPEN_FACTOR != 1.0:
            sharpener = ImageEnhance.Sharpness(img)
            img = sharpener.enhance(SHARPEN_FACTOR)
        img.save(image_path, quality=OVERLAY_SAVE_QUALITY)
    except Exception as e:
        print(f"Post-process (sharpen) skipped: {e}")
