"""
Ensure Hugging Face `transformers` exposes symbols at package top level that `diffusers`
imports via `from transformers import X`.

Some broken, partial, or oddly configured installs omit these from `transformers.__init__`,
which causes: cannot import name 'AutoImageProcessor' / 'PreTrainedModel' from 'transformers'.

Import this module once before importing diffusers (e.g. at startup of content_generator,
runpod_image, imgen feb generate_image).

The proper fix is still: pip install --force-reinstall "transformers>=4.52.0"
in the same Python you use to run the pipeline.
"""
from __future__ import annotations

import os

# If both USE_TORCH and USE_TF are AUTO, transformers treats TensorFlow as available and
# image_transforms imports tensorflow → TF 2.20+ needs protobuf>=5.28 (runtime_version).
# This pipeline only needs PyTorch for Z-Image; protobuf 3.20.x is fine when TF is not loaded.
os.environ.setdefault("USE_TORCH", "1")
os.environ.setdefault("USE_TF", "0")


def _patch_one(tf, name: str, modname: str, attr: str) -> None:
    if hasattr(tf, name):
        return
    try:
        m = __import__(modname, fromlist=[attr])
        setattr(tf, name, getattr(m, attr))
    except Exception:
        pass


def apply_transformers_shim() -> None:
    try:
        import transformers as tf
    except Exception:
        return

    _patch_one(tf, "AutoImageProcessor", "transformers.models.auto.image_processing_auto", "AutoImageProcessor")
    _patch_one(tf, "PreTrainedModel", "transformers.modeling_utils", "PreTrainedModel")
    _patch_one(tf, "AutoTokenizer", "transformers.models.auto.tokenization_auto", "AutoTokenizer")
    _patch_one(tf, "AutoModel", "transformers.models.auto.modeling_auto", "AutoModel")


apply_transformers_shim()
