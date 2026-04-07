"""
Expert Agent: dynamic theming, typography hierarchy, compositing depth, and Prompt-to-JSON design schema.
When USE_DESIGN_AGENT is True, per-post design is driven by image analysis + optional LLM schema.
"""
import json
import os
import random

# Golden ratio for visual hierarchy (Line 1 = 1.618 * Line 2)
GOLDEN_RATIO = 1.618

# Default schema when LLM is unavailable
DEFAULT_SCHEMA = {
    "mood": "Urgent",
    "primary_color": "#D32F2F",
    "accent_color": "#1976D2",
    "headline_scale": 1.618,
    "letter_spacing": -0.04,
    "vignette_intensity": 0.3,
    "font_weight": "black",
    "shadow_tint": "warm",
    "bar_texture_opacity": 0.05,
}


def _kmeans_dominant_colors(img, n_colors=5, sample_size=2000, max_iters=10):
    """K-Means on sampled pixels; returns list of (R,G,B) cluster centers, sorted by cluster size (dominant first).
    Resizes image first to cap memory (avoids building a huge pixel list for 768x960+ images)."""
    from PIL import Image
    w, h = img.size
    img = img.convert("RGB")
    # Downsample so getdata() returns at most ~sample_size pixels (saves memory on large images)
    total = w * h
    if total > sample_size * 2:
        scale = (sample_size / total) ** 0.5
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        img = img.resize((new_w, new_h), Image.Resampling.BOX)
    pixels = list(img.getdata())
    if len(pixels) > sample_size:
        pixels = random.sample(pixels, sample_size)
    if not pixels:
        return [(220, 45, 60), (50, 90, 220)]
    # Initialize centers from random pixels
    centers = [list(pixels[i]) for i in random.sample(range(len(pixels)), min(n_colors, len(pixels)))]
    for _ in range(max_iters):
        clusters = [[] for _ in centers]
        for p in pixels:
            r, g, b = p[0], p[1], p[2]
            best = min(range(len(centers)), key=lambda i: (r - centers[i][0]) ** 2 + (g - centers[i][1]) ** 2 + (b - centers[i][2]) ** 2)
            clusters[best].append(p)
        new_centers = []
        for i, cluster in enumerate(clusters):
            if cluster:
                new_centers.append([
                    int(sum(c[0] for c in cluster) / len(cluster)),
                    int(sum(c[1] for c in cluster) / len(cluster)),
                    int(sum(c[2] for c in cluster) / len(cluster)),
                ])
            else:
                new_centers.append(centers[i])
        centers = new_centers
    # Sort by cluster size (largest first)
    sizes = [len(c) for c in clusters]
    order = sorted(range(len(centers)), key=lambda i: -sizes[i])
    return [tuple(centers[i]) for i in order]


def _hex_to_rgb(hex_str):
    h = (hex_str or "").strip().lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return (210, 50, 47)


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(min(255, max(0, int(rgb[0]))), min(255, max(0, int(rgb[1]))), min(255, max(0, int(rgb[2]))))


def color_theory_agent(image_path):
    """
    Analyze base image dominant colors; return badge and shadow palette that match the scene.
    E.g. dark ocean → signal red with blue undertone.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        dominant = _kmeans_dominant_colors(img, n_colors=5, sample_size=2000)
        if not dominant:
            return None
        # Dominant = first (largest cluster); use it to tint badge
        acc = dominant[0]
        # Signal red (D32F2F) with a touch of dominant for harmony (e.g. blue undertone)
        signal_red = (211, 47, 47)
        blend = 0.15
        red_tinted = (
            int(signal_red[0] * (1 - blend) + acc[0] * blend),
            int(signal_red[1] * (1 - blend) + acc[1] * blend),
            int(signal_red[2] * (1 - blend) + acc[2] * blend),
        )
        # Blue half: shift toward dominant
        signal_blue = (25, 118, 210)
        blue_tinted = (
            int(signal_blue[0] * (1 - blend) + acc[0] * blend),
            int(signal_blue[1] * (1 - blend) + acc[1] * blend),
            int(signal_blue[2] * (1 - blend) + acc[2] * blend),
        )
        # Darker variants for gradient bottom
        red_bottom = (int(red_tinted[0] * 0.75), int(red_tinted[1] * 0.4), int(red_tinted[2] * 0.4))
        blue_bottom = (int(blue_tinted[0] * 0.4), int(blue_tinted[1] * 0.5), int(blue_tinted[2] * 0.75))
        return {
            "badge_red_top": red_tinted,
            "badge_red_bottom": red_bottom,
            "badge_blue_top": blue_tinted,
            "badge_blue_bottom": blue_bottom,
            "accent_rgb": acc,
        }
    except Exception as e:
        print(f"Color theory agent failed: {e}")
        return None


def typography_agent():
    """Return typography params: golden ratio scale (line1 = 1.618 * line2), tracking as fraction of em (-0.05 = -5%)."""
    return {
        "headline_scale_ratio": GOLDEN_RATIO,
        "tracking_em": -0.04,
    }


def get_design_schema_from_llm(article):
    """
    Prompt-to-JSON: ask Ollama or Gemini for a Design Schema (mood, primary_color, headline_scale, etc.).
    Returns dict or None; design_agent will merge with defaults.
    Uses Ollama when available; Gemini only when GOOGLE_API_KEY/GEMINI_API_KEY is set (no API key = skip Gemini, no error).
    """
    title = (article.get("title") or "")[:200]
    desc = (article.get("description") or article.get("summary") or "")[:300]
    prompt = f"""You are a broadcast graphics designer. Given this news item, output a JSON design schema only (no markdown, no explanation).
Keys: mood (e.g. Urgent/Military/Calm), primary_color (hex e.g. #D32F2F), accent_color (hex), headline_scale (number, e.g. 1.4), letter_spacing (number between -0.05 and 0, e.g. -0.04), vignette_intensity (0.2-0.4), font_weight (black or bold), shadow_tint (warm or cool), bar_texture_opacity (0.03-0.08).

News:
Title: {title}
Description: {desc}

Output only valid JSON with those keys."""

    def _parse_json_response(text):
        if not text:
            return None
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    # 1) Try Ollama first when enabled (or when no Gemini key, so RunPod can use Ollama-only)
    try:
        from config import USE_OLLAMA, GEMINI_API_KEY
        has_gemini_key = bool(os.environ.get("GOOGLE_API_KEY") or (GEMINI_API_KEY and str(GEMINI_API_KEY).strip()))
        try_ollama = USE_OLLAMA or not has_gemini_key
        if try_ollama:
            try:
                from ollama_client import ollama_available, ollama_generate_text
                if ollama_available():
                    out = ollama_generate_text(prompt, model=None)
                    if out:
                        schema = _parse_json_response(out)
                        if schema:
                            return schema
            except ImportError:
                pass
    except Exception:
        pass

    # 2) Use Gemini only when API key is set (avoids "No API_KEY or ADC found" when key is missing)
    try:
        from config import GEMINI_API_KEY
        api_key = (os.environ.get("GOOGLE_API_KEY") or GEMINI_API_KEY or "").strip()
        if not api_key:
            return None
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        if resp and resp.text:
            schema = _parse_json_response(resp.text)
            if schema:
                return schema
    except Exception as e:
        print(f"Design schema LLM failed: {e}")
    return None


def shadow_tint_for_text_color(rgb, tint="warm"):
    """Colored glow: dark orange-brown for warm/yellow text; dark blue-gray for cool. Returns (R,G,B)."""
    if tint == "cool":
        return (30, 40, 70)
    return (60, 35, 20)


def get_design_context(image_path, article, use_llm_schema=True, use_color_agent=True):
    """
    Run all agents and return a single design_context dict for this post.
    Overrides to apply: badge colors, headline scale ratio, tracking, vignette, font weight, shadow color/blur, bar texture.
    """
    ctx = {}
    if use_color_agent:
        palette = color_theory_agent(image_path)
        if palette:
            ctx["badge_red_top"] = palette["badge_red_top"]
            ctx["badge_red_bottom"] = palette["badge_red_bottom"]
            ctx["badge_blue_top"] = palette["badge_blue_top"]
            ctx["badge_blue_bottom"] = palette["badge_blue_bottom"]
    typo = typography_agent()
    ctx.setdefault("headline_scale_ratio", typo["headline_scale_ratio"])
    ctx.setdefault("tracking_em", typo["tracking_em"])
    if use_llm_schema:
        schema = get_design_schema_from_llm(article)
        if schema:
            ctx["mood"] = schema.get("mood", "Urgent")
            if schema.get("primary_color"):
                ctx["primary_color_rgb"] = _hex_to_rgb(schema["primary_color"])
            ctx["headline_scale"] = float(schema.get("headline_scale", 1.618))
            ctx["letter_spacing"] = float(schema.get("letter_spacing", -0.04))
            ctx["vignette_intensity"] = float(schema.get("vignette_intensity", 0.3))
            ctx["font_weight"] = (schema.get("font_weight") or "black").lower()
            ctx["shadow_tint"] = schema.get("shadow_tint") or "warm"
            ctx["bar_texture_opacity"] = float(schema.get("bar_texture_opacity", 0.05))
    if "headline_scale" not in ctx:
        ctx["headline_scale"] = ctx.get("headline_scale_ratio", GOLDEN_RATIO)
    if "letter_spacing" not in ctx:
        ctx["letter_spacing"] = ctx.get("tracking_em", -0.04)
    if "vignette_intensity" not in ctx:
        ctx["vignette_intensity"] = 0.3
    if "font_weight" not in ctx:
        ctx["font_weight"] = "black"
    if "shadow_tint" not in ctx:
        ctx["shadow_tint"] = "warm"
    if "bar_texture_opacity" not in ctx:
        ctx["bar_texture_opacity"] = 0.05
    return ctx
