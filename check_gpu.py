#!/usr/bin/env python3
"""Quick check: does this Python see NVIDIA CUDA? Run from project folder with the same venv as the pipeline."""
from __future__ import print_function
import sys

def main():
    try:
        import torch
    except ImportError:
        print("torch is not installed in this environment.")
        sys.exit(1)
    print("Python:", sys.executable)
    print("torch:", getattr(torch, "__version__", "?"))
    print("torch.cuda.is_available():", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("device 0:", torch.cuda.get_device_name(0))
        print("capability:", torch.cuda.get_device_capability(0))
        try:
            print("CUDA (torch):", torch.version.cuda)
        except Exception:
            pass
        try:
            major, minor = torch.cuda.get_device_capability(0)
            if major > 9 or (major == 9 and minor > 0):
                print(
                    "\nNote (RTX 50 / Blackwell): capability %s.%s — run kernel smoke test below."
                    % (major, minor)
                )
                print("  If smoke fails: install_nightly_torch_venv.bat (same .venv as run_continuous_posts).")
        except Exception:
            pass
        # Blackwell (sm_120): is_available() can be True while ops fail with "no kernel image" — smoke test.
        try:
            t = torch.tensor([1.0], device="cuda")
            t2 = t + 1.0
            _ = float(t2[0].item())
            print("\nCUDA kernel smoke test: OK (this build can run ops on your GPU).")
        except RuntimeError as ex:
            msg = str(ex).lower()
            print("\n*** CUDA kernel smoke test FAILED ***")
            print(ex)
            if "no kernel image" in msg:
                print(
                    "\nPyTorch in THIS environment has no kernels for your GPU arch (e.g. RTX 50 / sm_120).\n"
                    "Common mistake: nightly torch installed for system Python, but you run the pipeline with .venv.\n\n"
                    "Fix — from the project folder:\n"
                    "  install_nightly_torch_venv.bat\n"
                    "or:\n"
                    r'  .venv\Scripts\python.exe -m pip install --upgrade --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128'
                    "\nThen:  .venv\\Scripts\\python.exe check_gpu.py"
                )
            else:
                print("\nGPU op failed — update GPU driver / PyTorch CUDA build, or run with IMGEN_FEB_DEVICE=cpu.")
            sys.exit(3)
        print("\nOK — use IMGEN_FEB_DEVICE=cuda and IMGEN_FEB_USE_CPU_OFFLOAD=True for GPU+CPU offload.")
    else:
        print("\nCUDA not available — you likely installed the CPU-only PyTorch wheel.")
        print("Fix (Windows, in this venv):")
        print('  pip uninstall torch torchvision -y')
        print('  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124')
        sys.exit(2)

if __name__ == "__main__":
    main()
