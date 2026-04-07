#!/usr/bin/env python3
"""
Verify config.py clamps dangerous Windows CUDA flags (even if .env sets TRY_DIRECT=1).
Run from project root: .venv\\Scripts\\python.exe scripts\\verify_windows_stability.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if sys.platform != "win32":
        print("verify_windows_stability: skip (not Windows)")
        return 0

    py = root / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        print("verify_windows_stability: skip (.venv not found)")
        return 0

    # Fresh process so `import config` applies the same as the real app
    code = r"""
import os
os.environ.pop("IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE", None)
os.environ["IMGEN_TRY_DIRECT_GPU_FIRST"] = "1"
os.environ["IMGEN_ALLOW_WINDOWS_DIRECT_GPU"] = "1"
os.environ["IMGEN_FEB_DEVICE"] = "cuda"
import config  # noqa: F401
assert os.environ.get("IMGEN_TRY_DIRECT_GPU_FIRST") == "0", os.environ.get("IMGEN_TRY_DIRECT_GPU_FIRST")
assert os.environ.get("IMGEN_ALLOW_WINDOWS_DIRECT_GPU") == "0", os.environ.get("IMGEN_ALLOW_WINDOWS_DIRECT_GPU")
assert os.environ.get("IMGEN_FORCE_CPU_OFFLOAD") == "1", os.environ.get("IMGEN_FORCE_CPU_OFFLOAD")
print("verify_windows_stability: OK (bad .env flags clamped)")
"""
    try:
        subprocess.run(
            [str(py), "-c", code],
            cwd=str(root),
            check=True,
        )
    except subprocess.CalledProcessError:
        return 1

    # UNSAFE=1 must preserve user intent (set before import so dotenv does not override)
    code_unsafe = r"""
import os
os.environ["IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE"] = "1"
os.environ["IMGEN_TRY_DIRECT_GPU_FIRST"] = "1"
os.environ["IMGEN_ALLOW_WINDOWS_DIRECT_GPU"] = "1"
os.environ["IMGEN_FORCE_CPU_OFFLOAD"] = "0"
os.environ["IMGEN_FEB_DEVICE"] = "cuda"
import config  # noqa: F401
assert os.environ.get("IMGEN_TRY_DIRECT_GPU_FIRST") == "1"
assert os.environ.get("IMGEN_ALLOW_WINDOWS_DIRECT_GPU") == "1"
print("verify_windows_stability: OK (UNSAFE preserves TRY_DIRECT)")
"""
    try:
        subprocess.run(
            [str(py), "-c", code_unsafe],
            cwd=str(root),
            check=True,
        )
    except subprocess.CalledProcessError:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
