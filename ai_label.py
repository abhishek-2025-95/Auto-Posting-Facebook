"""
Mandatory "AI Generated" compliance label for all image posts.
Professional-grade: configurable font, semi-transparent background, optional outline.
"""
import os

try:
    from design_config import (
        AI_LABEL_TEXT, AI_LABEL_BG_COLOR, AI_LABEL_BG_ALPHA, AI_LABEL_TEXT_COLOR,
        AI_LABEL_OUTLINE, AI_LABEL_OUTLINE_COLOR, AI_LABEL_OUTLINE_WIDTH,
        AI_LABEL_MARGIN_RATIO, AI_LABEL_PAD_X_RATIO, AI_LABEL_PAD_Y_RATIO,
        AI_LABEL_FONT_SIZE_RATIO, AI_LABEL_RADIUS, AI_LABEL_FONT_PATH,
        AI_LABEL_NO_BOX,
    )
except ImportError:
    AI_LABEL_TEXT = "AI Generated"
    AI_LABEL_BG_COLOR = (0, 0, 0)
    AI_LABEL_BG_ALPHA = 0.90
    AI_LABEL_TEXT_COLOR = (255, 255, 255)
    AI_LABEL_OUTLINE = True
    AI_LABEL_OUTLINE_COLOR = (255, 255, 255)
    AI_LABEL_OUTLINE_WIDTH = 1
    AI_LABEL_MARGIN_RATIO = 0.028
    AI_LABEL_PAD_X_RATIO = 0.50
    AI_LABEL_PAD_Y_RATIO = 0.35
    AI_LABEL_FONT_SIZE_RATIO = 0.042
    AI_LABEL_RADIUS = 4
    AI_LABEL_FONT_PATH = None
    AI_LABEL_NO_BOX = False

try:
    from design_config import OVERLAY_SAVE_QUALITY
except ImportError:
    OVERLAY_SAVE_QUALITY = 95


def _draw_ai_label_on_image(img):
    """
    Draw 'AI Generated' label on an already-opened PIL Image. Returns the image (same or new
    if alpha composite was used). Memory-efficient when called from overlay so we don't open the file again.
    """
    from PIL import Image, ImageDraw
    from design_utils import get_pro_font

    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    short_side = min(w, h)
    margin = max(3, int(short_side * AI_LABEL_MARGIN_RATIO))
    font_size = max(6, min(18, int(short_side * AI_LABEL_FONT_SIZE_RATIO)))
    font = get_pro_font(font_size, bold=True, font_path=AI_LABEL_FONT_PATH)
    bbox = draw.textbbox((0, 0), AI_LABEL_TEXT, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    no_box = False
    try:
        from design_config import AI_LABEL_NO_BOX as _no_box
        no_box = _no_box
    except ImportError:
        pass
    if no_box:
        x = w - margin
        y = h - margin
        try:
            draw.text((x, y), AI_LABEL_TEXT, fill=AI_LABEL_TEXT_COLOR, font=font, anchor="rb")
        except TypeError:
            draw.text((x - tw, y - th), AI_LABEL_TEXT, fill=AI_LABEL_TEXT_COLOR, font=font)
    else:
        pad_x = max(6, int(font_size * AI_LABEL_PAD_X_RATIO))
        pad_y = max(4, int(font_size * AI_LABEL_PAD_Y_RATIO))
        box_w = tw + pad_x * 2
        box_h = th + pad_y * 2
        x0 = w - margin - box_w
        y0 = h - margin - box_h
        x1 = w - margin
        y1 = h - margin
        x = x0 + pad_x
        y = y0 + pad_y
        outline_color = (AI_LABEL_OUTLINE_COLOR if AI_LABEL_OUTLINE else None)
        outline_width = AI_LABEL_OUTLINE_WIDTH if AI_LABEL_OUTLINE else 0
        radius = max(0, AI_LABEL_RADIUS)

        def _draw_rect(d, x0_, y0_, x1_, y1_, fill, outline, width=1):
            if radius and hasattr(d, "rounded_rectangle"):
                d.rounded_rectangle([x0_, y0_, x1_, y1_], radius=radius, fill=fill, outline=outline, width=width)
            else:
                d.rectangle([x0_, y0_, x1_, y1_], fill=fill, outline=outline, width=width)

        if AI_LABEL_BG_ALPHA >= 1.0:
            _draw_rect(draw, x0, y0, x1, y1, AI_LABEL_BG_COLOR, outline_color, outline_width)
        else:
            img_rgba = img.convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            alpha = int(255 * AI_LABEL_BG_ALPHA)
            oc = (*(AI_LABEL_OUTLINE_COLOR if AI_LABEL_OUTLINE else (0, 0, 0)), 220) if outline_color else None
            _draw_rect(odraw, x0, y0, x1, y1, (*AI_LABEL_BG_COLOR, alpha), oc, outline_width)
            img = Image.alpha_composite(img_rgba, overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

        try:
            draw.text((x0 + box_w // 2, y0 + box_h // 2), AI_LABEL_TEXT, fill=AI_LABEL_TEXT_COLOR, font=font, anchor="mm")
        except TypeError:
            draw.text((x, y), AI_LABEL_TEXT, fill=AI_LABEL_TEXT_COLOR, font=font)
    return img


def add_ai_generated_label(image_path):
    """
    Add an 'AI Generated' compliance label (extreme bottom-right) by path.
    When AI_LABEL_NO_BOX: text only, no background. For pipeline: overlay can use _draw_ai_label_on_image(img) then save once.
    """
    if not image_path or not os.path.exists(image_path):
        return
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        img = _draw_ai_label_on_image(img)
        try:
            from design_config import POST_SHARPEN, SHARPEN_FACTOR
        except ImportError:
            POST_SHARPEN = True
            SHARPEN_FACTOR = 1.2
        if POST_SHARPEN and SHARPEN_FACTOR and SHARPEN_FACTOR != 1.0:
            from PIL import ImageEnhance
            img = ImageEnhance.Sharpness(img).enhance(SHARPEN_FACTOR)
        img.save(image_path, quality=OVERLAY_SAVE_QUALITY)
    except Exception as e:
        print(f"Could not add AI label: {e}")
