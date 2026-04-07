"""Regression: modern headline box must wrap to the same width budget used when drawing (glyph + stroke + shadow)."""
from __future__ import annotations

from PIL import Image, ImageDraw


def test_fit_column_matches_multicolor_line_measure():
    from design_utils import (
        fit_text_in_box,
        line_width_multicolor_drawing,
        shrink_width_for_stroke_shadow,
    )

    headline = (
        "South Korea's Kospi leads losses in Asia as Iran war worries keep investors on edge"
    )
    max_text_width = 920
    shadow = (1, 1, 0)
    stroke_est = 1
    fit_col = shrink_width_for_stroke_shadow(max_text_width, stroke_est, shadow)
    fit_col = max(80, int(fit_col))

    tmp = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(tmp)
    font, lines, _tw, _th = fit_text_in_box(
        headline,
        fit_col,
        500,
        min_size=9,
        max_size=120,
        weight="black",
        font_path=None,
        line_spacing_ratio=1.18,
        draw=draw,
        max_lines=5,
    )
    assert lines
    slack = 3
    for line in lines:
        lw = line_width_multicolor_drawing(font, line, draw, space_w=None)
        assert lw <= fit_col + slack, f"line wider than fit column: lw={lw} fit_col={fit_col} {line=!r}"
