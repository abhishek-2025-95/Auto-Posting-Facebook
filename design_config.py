# design_config.py - Expert-grade design options for image posts (open-source stack)
# Typography, compositing, anti-aliasing, color grading, and dimensionality.

import os

# Optional: align headline/badge with institutional image mode (navy/slate + accent from config)
try:
    from config import IMAGE_VISUAL_MODE, INSTITUTIONAL_ACCENT_HEX
except ImportError:
    IMAGE_VISUAL_MODE = "classic"
    INSTITUTIONAL_ACCENT_HEX = "#00B8D4"


def _institutional_accent_rgb():
    h = (INSTITUTIONAL_ACCENT_HEX or "#00B8D4").lstrip("#")
    if len(h) == 6:
        try:
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return (0, 184, 212)

# --- Fonts (Noto Sans family: Black, Bold, Regular for variable weights) ---
_BASE = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(_BASE, "fonts")
# Per-line weight: "black" | "bold" | "regular" (fallback to bold if font missing)
HEADLINE_FONT_WEIGHTS = ("black", "bold", "regular")
HEADLINE_FONT_PATH = None
BADGE_FONT_PATH = None
AI_LABEL_FONT_PATH = None

# --- Spatial system (professional layout) ---
# 8px grid: all spacing/padding snap to multiples of BASE_UNIT. No arbitrary pixels.
SPATIAL_BASE_UNIT = 8
# Universal margin as fraction of canvas width (e.g. 5%)
MARGIN_RATIO = 0.05

# --- Sensational overlay: strict layout zones ---
# Top 70%: main image + badge + circular inset. Bottom 30%: solid black bar only (no overlays cross boundary).
BAR_HEIGHT_RATIO = 0.30
BAR_GRADIENT = False   # Solid black rectangle (hard geometric box for readability)
BAR_COLOR_TOP = (0, 0, 0)
BAR_COLOR_BOTTOM = (0, 0, 0)

# Headline: dynamic bounding box (shrink font until fits), anchor="mm", X = image_width/2
HEADLINE_MAX_LINES = 2
HEADLINE_MAX_CHARS_PER_LINE = 42
HEADLINE_LINE_SPACING = 0.5
HEADLINE_FILL_WIDTH_RATIO = 0.90   # Max 90% of image width before shrinking font
HEADLINE_TRACKING = 1
HEADLINE_ALL_CAPS = True   # Force .upper() like reference (Cyan / White / Yellow)
HEADLINE_COLORS = [(0, 255, 255), (255, 255, 255), (255, 255, 0)]   # Cyan, White, Yellow (high contrast)
HEADLINE_SHADOW = True
HEADLINE_SHADOW_OFFSET = (2, 2)
HEADLINE_SHADOW_COLOR = (0, 0, 0)

# Badge: skew (forward momentum) + micro-gradients
BADGE_HEIGHT_RATIO = 0.055
BADGE_WIDTH_RATIO = 0.20
BADGE_SKEW_DEGREES = 12   # 10–15° forward tilt
BADGE_GRADIENT = True
# Red half: (top, bottom) RGB; blue half: (top, bottom)
BADGE_RED_TOP = (220, 45, 60)
BADGE_RED_BOTTOM = (165, 20, 35)
BADGE_BLUE_TOP = (50, 90, 220)
BADGE_BLUE_BOTTOM = (20, 45, 175)
BADGE_TEXT_COLOR = (255, 255, 255)
BADGE_HIGHLIGHT_LINE = True

# Circular inset: supersampling + inner glow (professional, not debug-style)
INSET_SUPERSAMPLE = 4   # 3 or 4: draw at Nx resolution then downscale with LANCZOS
INSET_BORDER_COLOR = (200, 200, 210)   # Subtle light border (was bright blue; avoids “selection highlight” look)
INSET_BORDER_WIDTH = 2
INSET_GLOW_BLUR_RADIUS = 2   # Soft edge (reduced from 3)
INSET_SHADOW = True

# Color grading (applied to base image before overlays)
PRE_CONTRAST = 1.15    # 1.0 = none; 1.1–1.2 pop
PRE_SATURATION = 1.08  # slight vibrancy bump
VIGNETTE_STRENGTH = 0.28   # 0 = off; 0.25–0.35 subtle darkening at edges
VIGNETTE_POWER = 2   # 1 = linear; 2 = smoother, more natural falloff

# Output quality
OVERLAY_SAVE_QUALITY = 95
POST_SHARPEN = True
SHARPEN_FACTOR = 1.2

# --- Minimal Breaking News (top-left label + bottom 30% headline bar when USE_MINIMAL_BREAKING_OVERLAY) ---
# Multi-layer composition (in draw order): base image → bottom-third gradient → headline bar →
# Breaking News label + headline text → Unseen Economy logo → source text → AI label → branding logo.
# Safe zone: content kept inside (SAFE_ZONE_INSET_RATIO * width/height) from edges to avoid crop on all devices.
SAFE_ZONE_INSET_RATIO = 0.05   # min 5% inset from each edge for text/logo (professional layout)
# ULTRA_MINIMAL_IMAGE_OVERLAY=0|false turns the bottom headline bar back on.
# Default on: story is carried by Z-Image + caption; overlay = Breaking label + logo + source + AI tag only.
# Exception: IMAGE_GENERATION_MODE=cursor_only + CURSOR_USE_PIL_HEADLINE_OVERLAY=true still draws the PIL headline box
# (see minimal_overlay) when the base image is scene-only. Default is Cursor-painted headline (see config.py).
_ultra_raw = os.environ.get("ULTRA_MINIMAL_IMAGE_OVERLAY", "1").strip().lower()
_ultra_on = _ultra_raw not in ("0", "false", "no", "off")
USE_HEADLINE_BOX = not _ultra_on
# Headline box style: "modern" = lower-third + left accent; "frosted" = glassmorphism (no accent); "minimal" = full-width bar (legacy)
HEADLINE_BOX_STYLE = "modern"
# --- Frosted Glass headline box (Apple / premium tech: dark semi-transparent + thin white edge, no left accent) ---
FROSTED_BOX_RGBA = (15, 20, 30, 160)           # very dark, semi-transparent (background bleeds through)
FROSTED_BOX_RADIUS = 14                         # deep rounded corners (was 24; 40% smaller with box)
FROSTED_BOX_OUTLINE_RGBA = (255, 255, 255, 80)  # delicate 1px "glass edge"
FROSTED_BOX_OUTLINE_WIDTH = 1
# --- Modern headline box: efficient space use, headline always complete, professional spacing ---
# Scaled down ~40% (smaller box + smaller typography), while keeping the fitting logic able to wrap.
MODERN_HEADLINE_MAX_BOX_HEIGHT_RATIO = 0.48   # 0.80 * 0.60
MODERN_HEADLINE_MIN_BOX_TOP_RATIO = 0.35     # keep within overlay clamp
MODERN_HEADLINE_MARGIN_RATIO = 0.05       # 5% from bottom, left, right
MODERN_HEADLINE_BORDER_RADIUS = 20       # px (~32 * 0.60)
MODERN_HEADLINE_BG_RGBA = (15, 25, 72, 0.95)  # dark navy blue, 95% opacity
MODERN_HEADLINE_BLUR_RADIUS = 14        # backdrop blur (~24 * 0.60)
MODERN_HEADLINE_ACCENT_LEFT = (255, 255, 0)   # bright yellow for first 3 words (and left bar)
MODERN_HEADLINE_ACCENT_WIDTH = 10       # px (~16 * 0.60)
# Horizontal padding (left/right): tighter so headline uses full width; vertical can be slightly larger for balance
MODERN_HEADLINE_PADDING_PX = 38         # fallback when H/V not set (~64 * 0.60)
MODERN_HEADLINE_PADDING_HORIZONTAL_PX = 29   # left & right (~48 * 0.60)
MODERN_HEADLINE_PADDING_VERTICAL_PX = 34    # top & bottom (~56 * 0.60)
MODERN_HEADLINE_TEXT_INSET_LEFT = 8    # minimal gap between accent bar and text (~14 * 0.60)
MODERN_HEADLINE_MAX_WIDTH_PX = 2000    # use full box width for text
MODERN_HEADLINE_LINE_HEIGHT_RATIO = 1.18  # professional line spacing (tighter after scaling down)
MODERN_HEADLINE_HIGHLIGHT_WORDS = 3    # first N words in accent (used when HIGHLIGHT_WORDS_LIST is empty)
MODERN_HEADLINE_HIGHLIGHT_WORDS_LIST = []
MODERN_HEADLINE_WHITE_RGB = (255, 255, 255)   # bright white for rest of headline
MODERN_HEADLINE_TOP_BORDER = False
MODERN_HEADLINE_TOP_BORDER_COLOR = (255, 200, 50)
MODERN_HEADLINE_TEXT_SHADOW = (1, 1, 0)
MODERN_HEADLINE_STROKE_WIDTH = 1
MODERN_HEADLINE_STROKE_RATIO = 0
MODERN_HEADLINE_STROKE_FILL = (0, 0, 0)
MODERN_HEADLINE_FONT_WEIGHT = "black"
MODERN_HEADLINE_FONT_PATH = None
MODERN_HEADLINE_MAX_WORDS = 25           # full headline (complete sentence); font scales to fit
MODERN_HEADLINE_MAX_LINES = 5            # keep enough wrap room so the headline stays complete
USE_MINIMAL_BREAKING_OVERLAY = True   # Top-left "Breaking News" + bottom 30% headline box + AI label bottom-right
SHOW_BREAKING_LABEL = True            # True = show "Breaking News" label top-left; False = only main headline in box
BREAKING_LABEL_TEXT = "BREAKING NEWS"
BREAKING_LABEL_FONT_PATH = None
BREAKING_LABEL_HEIGHT_RATIO = 0.0504  # label height as fraction of min(w,h); 30% smaller than 0.072 (0.072 * 0.7)
BREAKING_LABEL_MARGIN_RATIO = 0.045   # inset from top/left
BREAKING_LABEL_PAD_X_RATIO = 0.55     # horizontal padding as fraction of label height (generous for pro look)
BREAKING_LABEL_PAD_Y_RATIO = 0.36     # vertical padding as fraction of label height
BREAKING_LABEL_X_SHIFT = 0            # pixels to nudge label right (negative = left); ComfyUI-TextOverlay–style fine-tuning
BREAKING_LABEL_Y_SHIFT = 0            # pixels to nudge label down (negative = up)
# Breaking News label: vivid red/blue for a lively, eye-catching look; TEXT_COLOR can be hex (e.g. "#FFFFFF") or (R,G,B)
BREAKING_LABEL_BG_RED = (220, 30, 45)
BREAKING_LABEL_BG_BLUE = (30, 90, 220)
BREAKING_LABEL_TEXT_COLOR = (255, 255, 255)  # or "#FFFFFF"
BREAKING_LABEL_TOP_BORDER = True     # 1px light line on top edge
BREAKING_LABEL_RADIUS = 4             # rounded corners (0 = square); Pillow 8.2+
# Bottom headline box: scaled down ~40% (smaller bar + typography)
MINIMAL_HEADLINE_BAR_HEIGHT_RATIO = 0.34   # 0.56 * 0.60
MINIMAL_HEADLINE_MAX_WORDS = 22   # full headline (complete sentence)
MINIMAL_HEADLINE_MAX_WORDS_IN_BOX = 22   # max words in bar so headline is complete
MINIMAL_HEADLINE_FILL_WIDTH_RATIO = 0.78   # keep width usage; font shrinks so it still fits
MINIMAL_HEADLINE_BAR_TOP_BORDER = True
MINIMAL_HEADLINE_BAR_TOP_BORDER_COLOR = (255, 255, 255)
MINIMAL_HEADLINE_INNER_PADDING_RATIO = 0.12 # 0.20 * 0.60
# Professional readability: 100% larger min font size
MINIMAL_HEADLINE_MIN_FONT_SIZE = 25         # 42 * 0.60
# Uniform font size in headline box (one size for all lines/headlines)
MINIMAL_HEADLINE_UNIFORM_SIZE = True         # same font size for all news text in the box
MINIMAL_HEADLINE_FONT_SIZE_RATIO = 0.50     # 0.84 * 0.60
MINIMAL_HEADLINE_FONT_SIZE_MIN_RATIO = 0.50 # keep consistent scaling when computing font range
MINIMAL_HEADLINE_FONT_SIZE_MAX_RATIO = 0.60 # 1.0 * 0.60
MINIMAL_HEADLINE_COLOR = (255, 255, 255)
# When True, headline color is chosen from bar region contrast (black/white) for legibility on any bar (CreatiPoster-style).
USE_CONTRAST_HEADLINE_COLOR = True   # auto-pick headline color from bar region for legibility; False uses design_agent or MINIMAL_HEADLINE_COLOR
# News box: white text with yellow to highlight (cycled per word)
MINIMAL_HEADLINE_COLORS = [(255, 255, 255), (255, 255, 0)]   # white, yellow highlight
MINIMAL_HEADLINE_SHADOW = True
MINIMAL_HEADLINE_SHADOW_OFFSET = (3, 3)      # strong drop-shadow so text pops on any background
MINIMAL_HEADLINE_SHADOW_OFFSETS = [(2, 2), (3, 3)]  # multiple layers for bolder shadow (used if set)
MINIMAL_HEADLINE_STROKE = True               # crisp outline for professional, high-quality text
MINIMAL_HEADLINE_STROKE_WIDTH = 6            # 10 * 0.60 for sharper, more defined edges
MINIMAL_HEADLINE_STROKE_COLOR = (0, 0, 0)
MINIMAL_HEADLINE_FONT_PATH = None            # set to path of .ttf for custom professional font (e.g. Noto Sans in fonts/)
# Bottom bar: gradient fading into image (camouflage effect)
MINIMAL_HEADLINE_BAR_RED_GRADIENT = False  # False = use image-blend gradient below
MINIMAL_HEADLINE_BAR_RED_TOP = (150, 28, 35)
MINIMAL_HEADLINE_BAR_RED_BOTTOM = (85, 12, 18)
# Gradient from image (sample above bar) to dark bar: fades away to camouflage with image
MINIMAL_HEADLINE_BAR_GRADIENT = True
MINIMAL_HEADLINE_BAR_GRADIENT_SAMPLE_HEIGHT = 40   # pixels above bar to sample (larger = smoother fade)
MINIMAL_HEADLINE_BAR_CAMOUFLAGE_BLEND = 0.78      # top of bar: 78% image color, 22% bar (strong fade-in)
MINIMAL_HEADLINE_FONT_WEIGHT = "black"      # black weight for sharper, bolder headline text
MINIMAL_HEADLINE_ALL_CAPS = False
# Wrap long headlines to 2 lines so text stays in viewport (no overflow); like overflow-wrap: break-word
MINIMAL_HEADLINE_WRAP_TWO_LINES = True
MINIMAL_HEADLINE_WRAP_WORD_THRESHOLD = 7   # if words > this, use 2 lines

# --- AI label (extreme bottom-right, text only, no box, white, 100% larger) ---
AI_LABEL_TEXT = "AI Generated"
AI_LABEL_NO_BOX = True         # no background or outline; text only
AI_LABEL_BG_COLOR = (0, 0, 0)
AI_LABEL_BG_ALPHA = 0.90
AI_LABEL_TEXT_COLOR = (255, 255, 255)   # white
AI_LABEL_OUTLINE = False
AI_LABEL_OUTLINE_COLOR = (255, 255, 255)
AI_LABEL_OUTLINE_WIDTH = 0
AI_LABEL_MARGIN_RATIO = 0.006   # minimal margin for extreme bottom-right
AI_LABEL_PAD_X_RATIO = 0.50
AI_LABEL_PAD_Y_RATIO = 0.35
AI_LABEL_FONT_SIZE_RATIO = 0.014   # 50% smaller than previous (was 0.028)
AI_LABEL_RADIUS = 4
AI_LABEL_PAD_RATIO = 0.012

# --- Branding logo (transparent PNG, top-right, on top of all elements) ---
# Pasted last so it sits above all other overlays. Fixed 50px from top-right; max width 150px, aspect ratio preserved.
BRANDING_LOGO_PATH = os.path.join(_BASE, "assets", "brand_logo.png")
BRANDING_LOGO_INSET_PX = 50      # pixels from top and from right edge
BRANDING_LOGO_MAX_WIDTH_PX = 150 # scale logo so width <= this; height scales to keep aspect ratio

# --- The Unseen Economy logo (small, top-right, extreme right) ---
# If UNSEEN_ECONOMY_LOGO_IMAGE_PATH is set and the file exists, the image is pasted (with alpha). Else text logo is drawn.
UNSEEN_ECONOMY_LOGO_IMAGE_PATH = os.path.join(_BASE, "assets", "unseen_economy_logo.png")
UNSEEN_ECONOMY_LOGO_TEXT = "The Unseen Economy"
UNSEEN_ECONOMY_LOGO_FONT_SIZE_RATIO = 0.026   # slightly larger so logo reads very bright
UNSEEN_ECONOMY_LOGO_COLOR = (255, 255, 255)   # very bright white
UNSEEN_ECONOMY_LOGO_BRIGHTNESS = 1.85         # video overlay: brighter logo on dark frames (max applied in code ~2.2)
UNSEEN_ECONOMY_LOGO_MARGIN_RATIO = 0.025
UNSEEN_ECONOMY_LOGO_INSET_RATIO = 0.006   # minimal inset: push logo to extreme top-right
UNSEEN_ECONOMY_LOGO_MAX_HEIGHT_RATIO = 0.12   # max logo height as fraction of image height (keeps aspect ratio)

# --- Expert Design Agent (dynamic theming per post) ---
USE_DESIGN_AGENT = True   # Color theory (K-Means), typography (golden ratio, tracking %), compositing (colored glow, bar texture), optional LLM schema
USE_DESIGN_AGENT_LLM_SCHEMA = True   # Prompt-to-JSON: ask Gemini/Ollama for mood, primary_color, letter_spacing, etc.

# --- Approval before post (no post until you approve) ---
APPROVE_BEFORE_POST = False  # If True: save preview only, no Facebook post. Set False to post (24x7 runner is post-ready).
PREVIEW_IMAGE_PATH = os.path.join(_BASE, "approval_preview.jpg")

# --- Institutional visual mode: cooler headline bar + badge (matches IMAGE_VISUAL_MODE=institutional) ---
if IMAGE_VISUAL_MODE == "institutional":
    _iar = _institutional_accent_rgb()
    MODERN_HEADLINE_BG_RGBA = (12, 18, 38, 0.95)
    MODERN_HEADLINE_ACCENT_LEFT = _iar
    MODERN_HEADLINE_WHITE_RGB = (245, 248, 255)
    MINIMAL_HEADLINE_COLORS = [(245, 248, 255), _iar]
    HEADLINE_COLORS = [_iar, (255, 255, 255), (180, 195, 220)]
    BREAKING_LABEL_BG_RED = (45, 55, 85)
    BREAKING_LABEL_BG_BLUE = (28, 42, 72)
    BADGE_RED_TOP = (55, 65, 95)
    BADGE_RED_BOTTOM = (40, 48, 75)
    BADGE_BLUE_TOP = (35, 55, 95)
    BADGE_BLUE_BOTTOM = (22, 38, 68)
