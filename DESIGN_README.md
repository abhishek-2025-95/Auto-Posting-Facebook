# Expert-grade image design (open-source)

Config-driven design with **anti-aliasing**, **variable typography**, **dimensionality**, and **color grading** so output approaches human designer quality.

## What’s included

- **design_config.py** – Typography (weights, tracking, fill-width), badge (skew, gradients), inset (supersample, glow), color grading (contrast, saturation, vignette), sharpen.
- **design_utils.py** – Noto Sans family (Black/Bold/Regular), gradient rects, text with tracking, dynamic font scaling, vignette, color grade.
- **fonts/** – Noto Sans Black, Bold, Regular (auto-download on first use). See `fonts/README.md`.
- **Sensational overlay** – Color grade + vignette → gradient bar → variable-weight headline (dynamic scale, tracking) → sheared gradient badge → supersampled circular inset with inner glow.
- **AI label** – Semi-transparent background, optional sharpen on save.

## Anti-aliasing & compositing

- **Circular inset:** Drawn at 3× or 4× resolution (config: `INSET_SUPERSAMPLE`), then downscaled with LANCZOS for smooth edges.
- **Inner glow:** Optional Gaussian blur on the border stroke (`INSET_GLOW_BLUR_RADIUS`) so the inset blends into the frame instead of a hard sticker.

## Typography

- **Variable weights:** `HEADLINE_FONT_WEIGHTS` = (`"black"`, `"bold"`, `"regular"`) for line 1, 2, 3 (hook / secondary / reading).
- **Tracking:** `HEADLINE_TRACKING` (e.g. 1–2 px tighter) for punchy headlines.
- **Dynamic scaling:** Font size is chosen so the longest line fits `HEADLINE_FILL_WIDTH_RATIO` of the canvas (e.g. 0.90) for maximum impact.

## Badge (dimensionality)

- **Shear:** `BADGE_SKEW_DEGREES` (e.g. 12°) for a forward tilt.
- **Micro-gradients:** `BADGE_GRADIENT` with `BADGE_RED_TOP`/`BADGE_RED_BOTTOM` and `BADGE_BLUE_TOP`/`BADGE_BLUE_BOTTOM` for depth.

## Color grading (pre-process)

- **Contrast / saturation:** `PRE_CONTRAST` (e.g. 1.15), `PRE_SATURATION` (e.g. 1.08) applied before overlays.
- **Vignette:** `VIGNETTE_STRENGTH` (e.g. 0.25) for subtle edge darkening and focus on center.

## Quick reference in `design_config.py`

| Option | Effect |
|--------|--------|
| `HEADLINE_FONT_WEIGHTS` | `("black", "bold", "regular")` per line |
| `HEADLINE_FILL_WIDTH_RATIO` | 0.85–0.95 for edge-to-edge text |
| `HEADLINE_TRACKING` | Tighter letter-spacing (px) |
| `BADGE_SKEW_DEGREES` | 10–15 for forward tilt |
| `BADGE_GRADIENT` | Use TOP/BOTTOM gradient colors |
| `INSET_SUPERSAMPLE` | 3 or 4 for smooth circle |
| `INSET_GLOW_BLUR_RADIUS` | 2 for soft border blend |
| `PRE_CONTRAST` / `PRE_SATURATION` | Pop before overlays |
| `VIGNETTE_STRENGTH` | 0.2–0.35 subtle |

## Expert Design Agent (design_agent.py)

When **USE_DESIGN_AGENT = True** in `design_config.py`, each post gets:

1. **Color Theory Agent** – K-Means on the base image to find dominant colors; badge red/blue are tinted to match the scene (e.g. dark ocean → signal red with blue undertone).
2. **Typography Agent** – Line 1 font size = **1.618 ×** Line 2 (golden ratio); tracking from schema or **-4%** em for tight, urgent headlines.
3. **Compositing Agent** – **Colored glow** instead of flat black shadow (e.g. dark orange-brown for warm text); **5% noise texture** on the gradient bar for broadcast-style depth.
4. **Prompt-to-JSON** – Optional: article is sent to Gemini or Ollama; the model returns a design schema (mood, primary_color, letter_spacing, vignette_intensity, font_weight, shadow_tint, bar_texture_opacity). The overlay uses this to override config for that post.

Set **USE_DESIGN_AGENT_LLM_SCHEMA = False** to skip the LLM call and use only K-Means + golden ratio + defaults.

The **minimal overlay** (top-left "Breaking News" + bottom headline box) also uses this agent when **USE_DESIGN_AGENT = True**: bar gets a subtle dark tint from the primary color, optional bar texture, headline uses schema font weight and shadow tint (warm/cool), and headline color can follow a bright primary for an engaging look. Content is kept inside the box (font size and width capped).

## Spatial system and optical centering

- **8px grid:** All spacing and padding snap to `SPATIAL_BASE_UNIT` (default 8). No arbitrary pixel values.
- **Universal margin:** `MARGIN_RATIO` (e.g. 5% of canvas width) defines the outer margin; badge and inset use this.
- **anchor="mm":** Headline and badge text use Pillow’s middle-middle anchor so (x, y) is the true geometric center. Avoids ascenders/descenders (y, g) throwing off centering.
- **Tracking:** Letter-by-letter drawing with `font.getlength(letter)` and a negative tracking value (e.g. -0.05em) for tight, urgent headlines. Total width uses `get_text_width_with_tracking()` for correct horizontal centering.
- **Dynamic font size:** `dynamic_font_size_for_line()` finds the largest size so the line fits the target width (e.g. 90% of canvas). Visual hierarchy: line 1 ≈ 1.618 × line 2 (golden ratio).

## RunPod vs local: consistent format and headline

To keep RunPod-generated posts looking like local ones:

1. **design_config.py** – Deploy it with the project. `minimal_overlay` adds the project dir to `sys.path` so `design_config` loads the same on RunPod. If it fails to load, the overlay falls back to **modern** style (not minimal) and default ratios.
2. **Headline box size** – In `design_config.py`, **MODERN_HEADLINE_MAX_BOX_HEIGHT_RATIO** (default **0.50**) and **MODERN_HEADLINE_MIN_BOX_TOP_RATIO** (default **0.52**) control how large the lower-third box and headline font are. Increase the first (e.g. 0.52) for a larger headline; keep both so the box stays in the lower half of the image.
3. **Fonts** – Noto Sans is auto-downloaded into **fonts/** on first use. For identical typography on RunPod (no CDN dependency), copy your local **fonts/** (Noto Sans Black/Bold/Regular `.ttf`) into the project and include **fonts/** in your RunPod deploy so the same font files are used.

## Stack

- **Pillow (PIL)** – Drawing, gradients, transform, blur, enhance.
- **Noto Sans** (SIL OFL) – Black, Bold, Regular.
- No paid or proprietary assets.
