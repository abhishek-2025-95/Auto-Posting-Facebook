"""Cursor prompt geometry hints scale with headline length."""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import content_generator as cg


def test_geometry_block_includes_inset_and_wrap_hints():
    short = cg._cursor_headline_geometry_block("Oil rises on Mideast tensions")
    long = cg._cursor_headline_geometry_block(
        "South Korea's Kospi leads losses in Asia as Iran war worries keep investors on edge"
    )
    assert "SAFE ZONE" in short and "%" in short
    assert "LEFT PADDING" in short and "RIGHT PADDING" in short
    assert "WRAP" in long and "lines" in long.lower()
    assert "VERIFY" in long


def test_mandatory_suffix_contains_geometry():
    art = {"title": "Test headline for geometry block"}
    s = cg._cursor_tool_mandatory_headline_suffix(art)
    assert "SAFE ZONE" in s
    assert "Test headline for geometry block" in s
