"""Regression test for Windows local diffusers offload load flags.

Run: python tests/test_runpod_image_offload.py
"""
from __future__ import annotations

import os
import sys
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import runpod_image  # noqa: E402


class _FakePipe:
    last_kwargs = None

    @classmethod
    def from_pretrained(cls, _model_id, **kwargs):
        cls.last_kwargs = dict(kwargs)
        return cls()

    def enable_sequential_cpu_offload(self):
        self.sequential = True

    def enable_model_cpu_offload(self):
        self.model = True

    def enable_vae_slicing(self):
        return None

    def enable_attention_slicing(self, *_args):
        return None


def test_cuda_cpu_offload_disables_meta_init_on_windows():
    old_env = {k: os.environ.get(k) for k in ("IMGEN_LOCAL_ZIMAGE_LOW_CPU_MEM", "IMGEN_SEQUENTIAL_CPU_OFFLOAD")}
    old_diffusers = sys.modules.get("diffusers")
    fake_diffusers = types.ModuleType("diffusers")
    fake_diffusers.DiffusionPipeline = _FakePipe
    sys.modules["diffusers"] = fake_diffusers

    runpod_image.clear_cached_pipeline()
    os.environ["IMGEN_LOCAL_ZIMAGE_LOW_CPU_MEM"] = "1"
    os.environ["IMGEN_SEQUENTIAL_CPU_OFFLOAD"] = "1"

    try:
        runpod_image._get_pipeline("cuda", True)
        assert _FakePipe.last_kwargs is not None
        assert _FakePipe.last_kwargs["low_cpu_mem_usage"] is False
    finally:
        runpod_image.clear_cached_pipeline()
        if old_diffusers is None:
            sys.modules.pop("diffusers", None)
        else:
            sys.modules["diffusers"] = old_diffusers
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main() -> int:
    test_cuda_cpu_offload_disables_meta_init_on_windows()
    print("test_runpod_image_offload: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
