"""
Strict image pipeline startup for run_continuous_posts.py.

When STRICT_IMAGE_GEN=1 (set by run_local.cmd / external helper, or .env):
  - Require CUDA + kernel smoke test when IMGEN_FEB_DEVICE=cuda and CPU fallback is disallowed
  - Optionally warm-load Z-Image once (IMAGE_GEN_WARM_LOAD, default on with strict)
  - Surface Windows paging-file hints on OSError 1455

Set STRICT_IMAGE_GEN=0 or IMAGE_GEN_WARM_LOAD=0 in .env to skip parts for debugging.
"""
from __future__ import annotations

import os
import sys
import tempfile


def _cuda_kernel_smoke_ok() -> bool:
    try:
        import torch

        if not torch.cuda.is_available():
            return False
        with torch.cuda.device(0):
            x = torch.randn(32, 32, device="cuda", dtype=torch.float16)
            y = torch.matmul(x, x)
            torch.cuda.synchronize()
            del y, x
        return True
    except Exception:
        return False


def run_image_gen_preflight_or_exit() -> None:
    try:
        from config import (
            IMAGE_GEN_WARM_LOAD,
            IMGEN_ALLOW_CPU_FALLBACK,
            IMGEN_FEB_DEVICE,
            STRICT_IMAGE_GEN,
            USE_IMGEN_FEB,
            Z_IMAGE_TURBO_MODEL,
        )
    except ImportError:
        return

    if not STRICT_IMAGE_GEN:
        return

    print("\n[PREFLIGHT] Strict image mode: checks + pinned loader env (see config.py).", flush=True)

    if not USE_IMGEN_FEB:
        print("[PREFLIGHT] ERROR: USE_IMGEN_FEB is false; nothing to preflight.", flush=True)
        raise SystemExit(2)

    dev = (IMGEN_FEB_DEVICE or "cuda").strip().lower()
    if dev != "cuda":
        print(
            f"[PREFLIGHT] ERROR: IMGEN_FEB_DEVICE={dev!r} but strict mode expects cuda for reliability. "
            "Set IMGEN_FEB_DEVICE=cuda or STRICT_IMAGE_GEN=0.",
            flush=True,
        )
        raise SystemExit(2)

    try:
        import torch
    except ImportError:
        print("[PREFLIGHT] ERROR: torch not installed.", flush=True)
        raise SystemExit(2)

    if not torch.cuda.is_available():
        print(
            "[PREFLIGHT] ERROR: torch.cuda.is_available() is False. Install CUDA PyTorch in this venv.\n"
            "  .venv\\Scripts\\python.exe check_gpu.py",
            flush=True,
        )
        raise SystemExit(2)

    if not IMGEN_ALLOW_CPU_FALLBACK:
        if not _cuda_kernel_smoke_ok():
            print(
                "[PREFLIGHT] ERROR: CUDA kernel smoke test failed (e.g. no kernel image for RTX 50 / sm_120).\n"
                "  install_nightly_torch_venv.bat\n"
                "  .venv\\Scripts\\python.exe check_gpu.py",
                flush=True,
            )
            raise SystemExit(2)
        print("[PREFLIGHT] CUDA kernel smoke test: OK", flush=True)
    else:
        print("[PREFLIGHT] IMGEN_ALLOW_CPU_FALLBACK=true — skipping kernel smoke gate.", flush=True)

    if not IMAGE_GEN_WARM_LOAD:
        print("[PREFLIGHT] IMAGE_GEN_WARM_LOAD=0 — skipping model warm load.", flush=True)
        return

    os.environ["IMGEN_DEVICE"] = "cuda"
    out = None
    try:
        fd, out = tempfile.mkstemp(suffix=".jpg", prefix="zimg_preflight_")
        os.close(fd)
        import imgen_feb

        prompt = "minimal abstract soft gradient, no text, no people, neutral tones"
        print("[PREFLIGHT] Warm-loading Z-Image (one tiny image; pipeline stays cached)...", flush=True)
        result = imgen_feb.generate_image(
            prompt=prompt,
            output_path=out,
            height=512,
            width=512,
            num_inference_steps=2,
            device="cuda",
            use_cpu_offload_from_start=None,
            clear_pipeline_after_generate=False,
            model_id=(Z_IMAGE_TURBO_MODEL or "Tongyi-MAI/Z-Image-Turbo").strip(),
        )
        if result is None and not (out and os.path.isfile(out) and os.path.getsize(out) > 0):
            print("[PREFLIGHT] ERROR: Z-Image warm load produced no output file.", flush=True)
            raise SystemExit(3)
        print(f"[PREFLIGHT] Warm load OK (saved {out!r}).", flush=True)
    except OSError as e:
        try:
            from windows_memory_errors import (
                is_windows_paging_file_error,
                print_windows_paging_file_help,
            )

            if is_windows_paging_file_error(e):
                print_windows_paging_file_help()
        except ImportError:
            pass
        print(f"[PREFLIGHT] ERROR: {e}", flush=True)
        raise SystemExit(3) from e
    except SystemExit:
        raise
    except Exception as e:
        print(f"[PREFLIGHT] ERROR during warm load: {e}", flush=True)
        import traceback

        traceback.print_exc()
        raise SystemExit(3) from e
    finally:
        if out and os.path.isfile(out):
            try:
                os.remove(out)
            except OSError:
                pass
