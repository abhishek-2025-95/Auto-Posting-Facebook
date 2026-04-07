"""IMAGE_GENERATION_MODE=cursor_only: inbound file only, no Z-Image."""
from __future__ import annotations

import os
import sys
import tempfile

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import config
import content_generator as cg


def test_cursor_only_uses_inbound_and_consumes(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CURSOR_USE_PIL_HEADLINE_OVERLAY", False)
    monkeypatch.setattr(cg, "IMAGE_GENERATION_MODE", "cursor_only")
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_CONSUME", True)
    monkeypatch.setattr(cg, "USE_SENSATIONAL_BREAKING_TEMPLATE", False)

    inbound = tmp_path / "in.png"
    Image.new("RGB", (80, 100), (50, 80, 120)).save(inbound)
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_INBOUND", str(inbound))

    prompt_file = tmp_path / "prompt.txt"
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_PROMPT_PATH", str(prompt_file))

    out_jpg = tmp_path / "out.jpg"
    article = {"title": "Headline", "summary": "Body", "url": "https://example.com/x"}

    r = cg.generate_post_image_fallback(article, image_prompt="A news photo", output_path=str(out_jpg))
    assert r == str(out_jpg)
    assert os.path.isfile(out_jpg)
    assert not os.path.isfile(inbound)
    assert prompt_file.is_file()
    text = prompt_file.read_text(encoding="utf-8")
    assert "Cursor chat IMAGE tool" in text
    assert "A news photo" in text
    assert "HEADLINE ON IMAGE" in text
    assert "Headline" in text  # exact title in mandatory headline block


def test_cursor_pil_overlay_writes_scene_only_prompt(tmp_path, monkeypatch):
    """Default PIL headline: operator prompt asks for scene only (no generator chyron)."""
    monkeypatch.setattr(config, "CURSOR_USE_PIL_HEADLINE_OVERLAY", True)
    monkeypatch.setattr(cg, "IMAGE_GENERATION_MODE", "cursor_only")
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_CONSUME", False)
    monkeypatch.setattr(cg, "USE_SENSATIONAL_BREAKING_TEMPLATE", False)

    inbound = tmp_path / "in.png"
    Image.new("RGB", (80, 100), (50, 80, 120)).save(inbound)
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_INBOUND", str(inbound))
    prompt_file = tmp_path / "prompt2.txt"
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_PROMPT_PATH", str(prompt_file))
    out_jpg = tmp_path / "out2.jpg"
    article = {"title": "Oil headline test", "summary": "Body", "url": "https://example.com/x"}
    r = cg.generate_post_image_fallback(article, image_prompt="A room", output_path=str(out_jpg))
    assert r == str(out_jpg)
    text = prompt_file.read_text(encoding="utf-8")
    assert "no on-image headline" in text or "Scene only" in text
    assert "HEADLINE ON IMAGE" not in text


def test_cursor_only_missing_inbound_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(cg, "IMAGE_GENERATION_MODE", "cursor_only")
    inbound = tmp_path / "missing.png"
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_INBOUND", str(inbound))
    monkeypatch.setattr(cg, "CURSOR_POST_IMAGE_PROMPT_PATH", str(tmp_path / "p.txt"))

    r = cg.generate_post_image_fallback({"title": "T"}, image_prompt="p", output_path=str(tmp_path / "o.jpg"))
    assert r is None
