"""Empty overlay headline skips PIL headline layer (Cursor in-image typography)."""
from __future__ import annotations

import os
import sys
import tempfile

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def test_apply_minimal_overlay_empty_headline_still_ok():
    from minimal_overlay import apply_minimal_breaking_overlay

    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "x.png")
        Image.new("RGB", (256, 320), (30, 30, 50)).save(path)
        assert apply_minimal_breaking_overlay(path, headline="", source="Test Source") is True
