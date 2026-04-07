"""
RTX 50 / Blackwell (compute capability 9.x+) — detect GPU and print one-line setup hints.
Used by run_continuous_posts.py at startup (after config / .env load).

imgen feb uses torch_cuda_compat (real kernel probe) for sm_91+; IMGEN_SKIP_GPU_CAPABILITY_CHECK
does not bypass that probe.
"""
from __future__ import annotations

def is_new_arch_gpu() -> bool:
    """True if CUDA device 0 is sm_90+ (Hopper 9.1+, Ada 10.x, Blackwell 12.x, etc.)."""
    try:
        import torch
    except ImportError:
        return False
    if not torch.cuda.is_available():
        return False
    try:
        major, minor = torch.cuda.get_device_capability(0)
    except Exception:
        return False
    return bool(major > 9 or (major == 9 and minor > 0))


def _cuda_kernel_probe_ok(torch) -> bool:
    """True if a tiny matmul runs on GPU 0 (catches 'no kernel image' wheels)."""
    try:
        with torch.cuda.device(0):
            x = torch.randn(32, 32, device="cuda", dtype=torch.float16)
            y = torch.matmul(x, x)
            torch.cuda.synchronize()
            del y, x
        return True
    except Exception:
        return False


def print_startup_banner() -> None:
    """Call after dotenv/config so IMGEN_* env vars are set."""
    import os

    try:
        import torch
    except ImportError:
        print("  PyTorch: not installed — image gen will fail until you: pip install -r requirements.txt", flush=True)
        return
    if not torch.cuda.is_available():
        return
    if os.name == "nt" and os.environ.get("IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE", "").strip().lower() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        print(
            "  Windows: full-GPU-first (STRATEGY 1) disabled unless IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE=1; "
            "config overrides risky .env flags.",
            flush=True,
        )
    try:
        major, minor = torch.cuda.get_device_capability(0)
        name = torch.cuda.get_device_name(0)
    except Exception:
        return
    if not (major > 9 or (major == 9 and minor > 0)):
        return

    if _cuda_kernel_probe_ok(torch):
        print(
            f"  GPU: {name} (capability {major}.{minor}) — CUDA kernel probe OK (imgen_feb can use GPU).",
            flush=True,
        )
        return

    print(
        f"  [!] {name} (capability {major}.{minor}) — PyTorch in this Python cannot run CUDA kernels on this GPU.",
        flush=True,
    )
    print(
        "      Fix:  install_nightly_torch_venv.bat   then   .venv\\Scripts\\python.exe check_gpu.py",
        flush=True,
    )
    print(
        "      (IMGEN_SKIP_GPU_CAPABILITY_CHECK does not bypass the probe — you need a nightly build with sm_120.)",
        flush=True,
    )
