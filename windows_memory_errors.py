"""
Windows-specific hints when heavy ML loads fail with low virtual memory / commit limit.

Error 1455 ("The paging file is too small for this operation to complete") often appears
while opening or loading Z-Image-Turbo safetensors shards — not fixable in Python alone.
"""

from __future__ import annotations

import os


def is_windows_paging_file_error(exc: BaseException) -> bool:
    if os.name != "nt":
        return False
    msg = str(exc).lower()
    if "paging file" in msg or "1455" in msg:
        return True
    if getattr(exc, "winerror", None) == 1455:
        return True
    return False


def print_windows_paging_file_help() -> None:
    print(
        "\n*** Windows: paging file / commit limit too small (often error 1455) ***\n"
        "Z-Image loads multi-GB weights; Windows needs enough RAM + page file *backing*.\n"
        "\nRecommended fix:\n"
        "  1. Settings -> System -> About -> Advanced system settings\n"
        "  2. Performance -> Settings -> Advanced -> Virtual memory -> Change\n"
        "  3. Uncheck 'Automatically manage', select system drive, Custom size:\n"
        "       Initial size (MB): 32768   Maximum (MB): 65536  (or higher if needed)\n"
        "  4. OK -> reboot. Close heavy apps (browsers, games) before generating.\n"
        "\nOptional (may lower peak RAM during load; less stable on some PCs):\n"
        "  In the same CMD window before Python:\n"
        "    set IMGEN_SAFE_SAFETENSORS_MODE=native\n"
        "  (Uses diffusers default safetensors load instead of per-tensor clone on Windows.)\n"
        "\nSee IMAGE_GEN_TROUBLESHOOTING.md -> 'Paging file too small (1455)'.\n"
    )
