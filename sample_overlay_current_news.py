"""
Generate a sample image with the minimal overlay using a current-news headline.
Creates a placeholder 4:5 image, applies Breaking News (top-left) + headline bar (bottom 30%) + AI label (bottom-right).
Output: sample_overlay_preview.jpg in this folder.
"""
import os
import sys

# Ensure project root is on path
_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

def main():
    from PIL import Image
    from minimal_overlay import apply_minimal_breaking_overlay

    # Current news headline (Mar 5, 2025) - max 15 words, grammatical
    headline = "Supreme Court rejects Trump's request to keep billions in foreign aid frozen"
    # 4:5 portrait (e.g. 720x900)
    width, height = 720, 900
    img = Image.new("RGB", (width, height))
    # Simple gradient background (dark blue-grey to darker) so overlay stands out
    for y in range(height):
        r = int(28 + (y / height) * 10)
        g = int(32 + (y / height) * 8)
        b = int(48 + (y / height) * 12)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    # Slight vignette-style darkening at edges (optional)
    cx, cy = width / 2, height / 2
    out = img.load()
    for y in range(height):
        for x in range(width):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / max(cx, cy)
            f = 1.0 - 0.15 * (d ** 1.5)
            c = out[x, y]
            out[x, y] = (int(c[0] * f), int(c[1] * f), int(c[2] * f))

    out_path = os.path.join(_BASE, "sample_overlay_preview.jpg")
    img.save(out_path, quality=95)
    # Overlay draws Breaking News, logo, headline box, source, and AI label in one pass
    if apply_minimal_breaking_overlay(out_path, headline=headline, source="Reuters"):
        print("Applied minimal overlay (Breaking News + headline box + logo + source + AI label).")
    else:
        print("Overlay did not apply; check errors above.")
    # AI label is already drawn by minimal_overlay; skip add_ai_generated_label to avoid duplicate
    print(f"Sample saved: {out_path}")
    return out_path

if __name__ == "__main__":
    main()
