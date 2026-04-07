"""
Windows safetensors / diffusers load hardening for Z-Image (same strategy as imgen feb generate_image.py).

The local diffusers module (`runpod_image.py`) loads diffusers without importing imgen_feb — those patches never ran, which often
produces a silent native exit right after "Loading checkpoint shards: 100%".

Call apply_patches() once before any diffusers.from_pretrained that loads .safetensors on Windows.
"""
from __future__ import annotations

import os
from typing import Optional

_PATCHED = False


def _windows_load_safetensors_cloned(checkpoint_file, map_location="cpu"):
    from safetensors import safe_open

    out = {}
    with safe_open(checkpoint_file, framework="pt", device="cpu") as f:
        for key in f.offset_keys():
            t = f.get_tensor(key)
            out[key] = t.clone().contiguous()
            del t
    if map_location is not None and str(map_location) not in ("cpu", "meta"):
        out = {k: v.to(map_location) for k, v in out.items()}
    return out


def _patch_safetensors_load_file_windows() -> None:
    if os.name != "nt":
        return
    _on = (os.environ.get("IMGEN_PATCH_SAFETENSORS_LOAD_FILE", "1") or "1").strip().lower()
    if _on in ("0", "false", "no", "off"):
        return
    mode = (os.environ.get("IMGEN_SAFE_SAFETENSORS_MODE") or "clone").strip().lower()
    if mode in ("native", "off", "none", "0", "false"):
        return
    try:
        import safetensors.torch as _st

        if getattr(_st, "_imgen_load_file_patch", False) or getattr(_st, "_apfb_load_file_patch", False):
            return
        _orig = _st.load_file

        def _safe_load_file(filename, device="cpu"):
            if mode in ("clone", "cloned"):
                return _windows_load_safetensors_cloned(filename, map_location=device)
            return _orig(filename, device=device)

        _st.load_file = _safe_load_file
        _st._apfb_load_file_patch = True
    except Exception:
        pass


def _apply_windows_safetensors_mmap_fix(for_cpu_pipeline: Optional[bool] = None) -> None:
    if os.name != "nt":
        return
    if for_cpu_pipeline is False:
        return
    if for_cpu_pipeline is None:
        _dev = (os.environ.get("IMGEN_DEVICE") or "").strip().lower()
        if _dev == "cuda":
            _force_safe = os.environ.get("IMGEN_FORCE_SAFE_SAFETENSORS", "1").strip().lower()
            if _force_safe not in ("1", "true", "yes", "on", ""):
                return
    raw = os.environ.get("IMGEN_DISABLE_SAFETENSORS_MMAP", "1").strip().lower()
    if raw in ("0", "false", "no"):
        return

    try:
        import diffusers.models.model_loading_utils as _diff_mlu

        _dd_done = getattr(_diff_mlu, "_imgen_mmap_patch", False) or getattr(_diff_mlu, "_apfb_mmap_patch", False)
        if not _dd_done:
            _orig_dd = _diff_mlu.load_state_dict

            def _load_state_dict_dd(checkpoint_file, dduf_entries=None, disable_mmap=False, map_location="cpu"):
                if not isinstance(checkpoint_file, dict):
                    try:
                        ext = os.path.basename(str(checkpoint_file)).rsplit(".", 1)[-1]
                    except Exception:
                        ext = ""
                    if ext == "safetensors" and not dduf_entries:
                        if map_location == "meta":
                            return _orig_dd(
                                checkpoint_file,
                                dduf_entries=dduf_entries,
                                disable_mmap=False,
                                map_location=map_location,
                            )
                        _safem = os.environ.get("IMGEN_SAFE_SAFETENSORS_MODE")
                        mode = (
                            _safem.strip().lower()
                            if _safem and str(_safem).strip()
                            else "clone"
                        )
                        if mode in ("clone", "cloned"):
                            try:
                                return _windows_load_safetensors_cloned(checkpoint_file, map_location=map_location)
                            except OSError as _e:
                                _msg = str(_e).lower()
                                if os.name == "nt" and ("1455" in _msg or "paging file" in _msg):
                                    print(
                                        "[WARN] safetensors clone load hit Windows error 1455; "
                                        "retrying with native loader for this shard.",
                                        flush=True,
                                    )
                                    return _orig_dd(
                                        checkpoint_file,
                                        dduf_entries=dduf_entries,
                                        disable_mmap=False,
                                        map_location=map_location,
                                    )
                                raise
                        if mode in ("native", "off", "none", "0", "false"):
                            return _orig_dd(
                                checkpoint_file,
                                dduf_entries=dduf_entries,
                                disable_mmap=disable_mmap,
                                map_location=map_location,
                            )
                        if mode in ("disable_mmap",):
                            return _orig_dd(
                                checkpoint_file,
                                dduf_entries=dduf_entries,
                                disable_mmap=True,
                                map_location=map_location,
                            )
                        return _windows_load_safetensors_cloned(checkpoint_file, map_location=map_location)
                return _orig_dd(
                    checkpoint_file,
                    dduf_entries=dduf_entries,
                    disable_mmap=disable_mmap,
                    map_location=map_location,
                )

            _diff_mlu.load_state_dict = _load_state_dict_dd
            _diff_mlu._apfb_mmap_patch = True
    except Exception:
        pass

    try:
        import transformers.modeling_utils as _tf_mu

        _tf_done = getattr(_tf_mu, "_imgen_mmap_patch", False) or getattr(_tf_mu, "_apfb_mmap_patch", False)
        if not _tf_done:
            _orig_tf = _tf_mu.load_state_dict

            def _load_state_dict_tf(checkpoint_file, is_quantized=False, map_location="cpu", weights_only=True, **kwargs):
                cs = str(checkpoint_file)
                if cs.endswith(".safetensors") and map_location != "meta":
                    return _windows_load_safetensors_cloned(checkpoint_file, map_location=map_location)
                try:
                    return _orig_tf(
                        checkpoint_file,
                        is_quantized=is_quantized,
                        map_location=map_location,
                        weights_only=weights_only,
                        **kwargs,
                    )
                except TypeError:
                    return _orig_tf(checkpoint_file, map_location=map_location, weights_only=weights_only)

            _tf_mu.load_state_dict = _load_state_dict_tf
            _tf_mu._apfb_mmap_patch = True
    except Exception:
        pass


def apply_patches() -> None:
    """Idempotent; safe to call multiple times."""
    global _PATCHED
    if _PATCHED or os.name != "nt":
        return
    _apply_windows_safetensors_mmap_fix(for_cpu_pipeline=None)
    _patch_safetensors_load_file_windows()
    _PATCHED = True
    if os.environ.get("IMGEN_DISABLE_SAFETENSORS_MMAP", "1").strip().lower() not in ("0", "false", "no"):
        print(
            "[INFO] Windows safetensors: diffusers/transformers use clone loader (windows_zimage_safetensors_patch).",
            flush=True,
        )
