#!/usr/bin/env python3
"""
One-shot setup for NVIDIA Blackwell / RTX 50-series (sm_100+) with this project:

  1) pip install --pre torch torchvision torchaudio from PyTorch nightly cu128 index
  2) Append Blackwell + speed keys to .env (if missing): SKIP_GPU_CHECK, inference steps=6, offload-stable flags, etc.

Run from project root:
  python scripts\\setup_blackwell_gpu.py

Or double-click: setup_blackwell_gpu.bat
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

NIGHTLY_INDEX = "https://download.pytorch.org/whl/nightly/cu128"

# Keys imgen_feb + transformers_shim + speed (config.py also setdefaults these if missing)
_ENV_DEFAULTS = [
    ("IMGEN_FEB_DEVICE", "cuda"),
    ("IMGEN_SKIP_GPU_CAPABILITY_CHECK", "1"),
    ("USE_TORCH", "1"),
    ("USE_TF", "0"),
    # Offload-first on Windows: full-GPU first often native-crashes on ~12GB VRAM after shard load.
    ("IMGEN_TRY_DIRECT_GPU_FIRST", "0"),
    ("IMGEN_ALLOW_WINDOWS_DIRECT_GPU", "0"),
    ("IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE", "false"),
    ("IMGEN_FEB_INFERENCE_STEPS", "6"),
]


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _venv_python(root: str) -> str | None:
    if os.name == "nt":
        p = os.path.join(root, ".venv", "Scripts", "python.exe")
        return p if os.path.isfile(p) else None
    p = os.path.join(root, ".venv", "bin", "python")
    return p if os.path.isfile(p) else None


def _pick_python(root: str, use_current: bool) -> str:
    """Install wheels into project .venv when it exists (fixes 'no kernel image' when system torch works but .venv torch is old)."""
    if use_current:
        return sys.executable
    v = _venv_python(root)
    if v:
        cur = os.path.normcase(os.path.abspath(sys.executable))
        tgt = os.path.normcase(os.path.abspath(v))
        if cur != tgt:
            print(
                f"[INFO] Project has .venv — installing PyTorch into:\n       {v}\n"
                f"       (You ran this script with a different Python; the pipeline usually uses .venv.)",
                flush=True,
            )
        return v
    return sys.executable


def _has_env_key(content: str, key: str) -> bool:
    """True if .env assigns this key (non-comment line)."""
    return bool(re.search(r"^\s*" + re.escape(key) + r"\s*=", content, re.MULTILINE))


def _append_env_keys(env_path: str, pairs: list[tuple[str, str]], banner: str) -> bool:
    """Append only missing keys. Return True if file was modified."""
    existing = ""
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8", errors="replace") as f:
            existing = f.read()
    to_add = [(k, v) for k, v in pairs if not _has_env_key(existing, k)]
    if not to_add:
        return False
    mode = "a" if os.path.isfile(env_path) else "w"
    with open(env_path, mode, encoding="utf-8", newline="\n") as f:
        if mode == "a" and existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(banner)
        for k, v in to_add:
            f.write(f"{k}={v}\n")
    print(f"[OK] Added {len(to_add)} line(s) to {env_path}.", flush=True)
    return True


def _pip_install_nightly(py: str, dry_run: bool) -> None:
    cmd = [
        py,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--pre",
        "torch",
        "torchvision",
        "torchaudio",
        "--index-url",
        NIGHTLY_INDEX,
    ]
    if dry_run:
        print("[DRY-RUN] would run:", " ".join(cmd), flush=True)
        return
    print("[RUN]", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def _verify_import(py: str, dry_run: bool) -> None:
    if dry_run:
        return
    code = (
        "import torch; "
        "print('torch', torch.__version__); "
        "print('cuda', torch.cuda.is_available()); "
        "print('cap', torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None); "
        "_c=torch.cuda.is_available(); "
        "assert not _c or float((torch.tensor([1.],device='cuda')+1)[0])==2.0; "
        "print('CUDA kernel smoke: OK' if _c else 'CUDA kernel smoke: skipped')"
    )
    subprocess.check_call([py, "-c", code])


def main() -> int:
    ap = argparse.ArgumentParser(description="Install nightly PyTorch (cu128) + .env for RTX 50 / Blackwell.")
    ap.add_argument("--skip-pip", action="store_true", help="Only update .env, do not run pip.")
    ap.add_argument("--dry-run", action="store_true", help="Print actions only.")
    ap.add_argument(
        "--speed",
        action="store_true",
        help="(No-op: speed keys are always appended with Blackwell keys.)",
    )
    ap.add_argument(
        "--use-current-python",
        action="store_true",
        help="Install into the interpreter running this script only (default: use .venv if the folder exists).",
    )
    args = ap.parse_args()

    root = _project_root()
    os.chdir(root)
    env_path = os.path.join(root, ".env")
    py = _pick_python(root, args.use_current_python)

    print("Project:", root, flush=True)
    print("Python used for pip:", py, flush=True)

    if not args.skip_pip:
        try:
            _pip_install_nightly(py, args.dry_run)
        except subprocess.CalledProcessError as e:
            print("[ERROR] pip install failed:", e, flush=True)
            return 1
    else:
        print("[SKIP] pip (--skip-pip)", flush=True)

    if not args.dry_run:
        added = _append_env_keys(
            env_path,
            _ENV_DEFAULTS,
            "# --- Blackwell / RTX 50 (scripts/setup_blackwell_gpu.py) ---\n",
        )
        if not added:
            print(f"[OK] {env_path} already has Blackwell + speed keys.", flush=True)
        if args.speed:
            print("[INFO] --speed is optional; speed vars are included in the Blackwell bundle.", flush=True)
    else:
        print("[DRY-RUN] would append Blackwell + speed block to", env_path, flush=True)

    print("\nNext:", flush=True)
    print("  1) Restart the terminal (or IDE) so the new torch is picked up.", flush=True)
    print("  2) python check_gpu.py", flush=True)
    print("  3) python run_continuous_posts.py", flush=True)
    print("\nIf you see 'no kernel image' on CUDA, try a newer nightly or cu129 index from https://pytorch.org/get-started/locally/", flush=True)

    if not args.skip_pip and not args.dry_run:
        try:
            _verify_import(py, False)
        except subprocess.CalledProcessError:
            print("[WARN] Post-install verify failed — check torch manually.", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
