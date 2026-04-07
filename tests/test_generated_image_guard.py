"""Regression tests for generated-image safety checks.

Run: python tests/test_generated_image_guard.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import content_generator as cg  # noqa: E402


def _load_imgen_generate_image_module():
    imgen_path = os.path.abspath(
        os.path.join(_ROOT, "..", "imgen feb", "generate_image.py")
    )
    sys.path.insert(0, os.path.dirname(imgen_path))
    spec = importlib.util.spec_from_file_location("imgen_generate_image", imgen_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_windows_imgen_defaults_to_float16():
    imgen = _load_imgen_generate_image_module()
    old = os.environ.get("IMGEN_FEB_WINDOWS_BFLOAT16")
    if old is None:
        os.environ.pop("IMGEN_FEB_WINDOWS_BFLOAT16", None)
    else:
        os.environ["IMGEN_FEB_WINDOWS_BFLOAT16"] = old
    try:
        dtype = imgen._select_windows_cuda_dtype(imgen.torch)
        assert dtype == imgen.torch.float16
        os.environ["IMGEN_FEB_WINDOWS_BFLOAT16"] = "1"
        dtype = imgen._select_windows_cuda_dtype(imgen.torch)
        assert dtype == imgen.torch.bfloat16
    finally:
        if old is None:
            os.environ.pop("IMGEN_FEB_WINDOWS_BFLOAT16", None)
        else:
            os.environ["IMGEN_FEB_WINDOWS_BFLOAT16"] = old


def test_blank_image_detector_flags_black_image():
    with tempfile.TemporaryDirectory() as td:
        black_path = os.path.join(td, "black.jpg")
        ok_path = os.path.join(td, "ok.jpg")
        Image.new("RGB", (64, 64), (0, 0, 0)).save(black_path)
        Image.new("RGB", (64, 64), (120, 140, 180)).save(ok_path)
        assert cg._is_probably_blank_generated_image(black_path) is True
        assert cg._is_probably_blank_generated_image(ok_path) is False


def test_create_fallback_image_permanently_disabled():
    assert cg.create_fallback_image({"title": "Test"}) is None
    assert cg.create_fallback_image("prompt text") is None


def main() -> int:
    test_windows_imgen_defaults_to_float16()
    test_blank_image_detector_flags_black_image()
    test_create_fallback_image_permanently_disabled()
    print("test_generated_image_guard: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
