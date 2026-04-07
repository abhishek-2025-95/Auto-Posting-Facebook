"""Cursor inbound 4:5 normalization: headline_safe crop keeps LTR lower-third."""
from __future__ import annotations

import os
import sys

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import content_generator as cg


def test_headline_safe_wide_source_keeps_left_strip(monkeypatch):
    """Wide image: center crop would drop left pixels; headline_safe keeps x=0..new_w."""
    monkeypatch.setattr(cg, "get_post_image_dimensions_45", lambda: (80, 100))
    # 200x100 — 2:1 wide; crop to 4:5 window height 100 -> width 80
    im = Image.new("RGB", (200, 100))
    for x in range(200):
        for y in range(100):
            im.putpixel((x, y), (x % 256, 0, 0))
    out = cg._crop_resize_rgb_to_45_cursor_inbound(im, _crop_mode_override="headline_safe")
    assert out.size == (80, 100)
    assert out.getpixel((0, 50))[0] == 0


def test_headline_safe_tall_source_keeps_bottom(monkeypatch):
    """Tall image: keep bottom rows (lower-third headline region)."""
    monkeypatch.setattr(cg, "get_post_image_dimensions_45", lambda: (80, 100))
    im = Image.new("RGB", (80, 200))
    for y in range(200):
        for x in range(80):
            im.putpixel((x, y), (0, y % 256, 0))
    out = cg._crop_resize_rgb_to_45_cursor_inbound(im, _crop_mode_override="headline_safe")
    assert out.size == (80, 100)
    assert out.getpixel((40, 99))[1] == 199 % 256


def test_cover_fills_target_size(monkeypatch):
    """cover = full 4:5 output with no letterbox bands (all pixels from source crop)."""
    monkeypatch.setattr(cg, "get_post_image_dimensions_45", lambda: (40, 50))
    # Wide 2:1 — after cover scale, crop to 40x50 fills frame
    im = Image.new("RGB", (200, 100), (10, 20, 30))
    out = cg._crop_resize_rgb_to_45_cursor_inbound(im, _crop_mode_override="cover")
    assert out.size == (40, 50)
    # No uniform black bars: corners should match scene (not all four black)
    corners = [out.getpixel((0, 0)), out.getpixel((39, 0)), out.getpixel((0, 49)), out.getpixel((39, 49))]
    assert not all(c == (0, 0, 0) for c in corners)


def test_letterbox_pads_without_slicing_content(monkeypatch):
    monkeypatch.setattr(cg, "get_post_image_dimensions_45", lambda: (40, 50))
    im = Image.new("RGB", (100, 100), (200, 10, 10))
    out = cg._crop_resize_rgb_to_45_cursor_inbound(im, _crop_mode_override="letterbox")
    assert out.size == (40, 50)
    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((20, 25))[0] == 200
