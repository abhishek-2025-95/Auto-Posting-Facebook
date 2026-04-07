"""
**Your PC (local):** Z-Image-Turbo via Hugging Face **diffusers** — runs entirely on your machine.
Used when the built-in path is chosen before `imgen_feb`, or when `imgen_feb` is not installed.

**Why the file is still named `runpod_image.py`:** legacy. The same file also runs **inside a RunPod
GPU pod** when `RUNPOD=1`. Local Windows posting is **not** using RunPod unless you set a remote URL.

**Env vars:** prefer **`IMGEN_LOCAL_ZIMAGE_*`** for tuning this path; older **`IMGEN_RUNPOD_*`** names
still work as aliases.

Requires diffusers with Z-Image support. Default model: Tongyi-MAI/Z-Image-Turbo (public).
Pipeline is cached unless ``clear_pipeline_after_generate=True``.
"""
import protobuf_runtime_shim  # noqa: F401 — Domain + ValidateProtobufRuntimeVersion for protobuf 5+

# Before diffusers: ensure transformers exposes PreTrainedModel, AutoImageProcessor, etc.
try:
    import transformers_shim  # noqa: F401
except Exception:
    pass

import os
import gc
import sys
from contextlib import contextmanager


def _env_pick(*keys: str, default: str = "") -> str:
    """First non-empty env among keys (supports IMGEN_LOCAL_ZIMAGE_* aliases for legacy IMGEN_RUNPOD_*)."""
    for k in keys:
        v = os.environ.get(k)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return default

# Must run before diffusers loads .safetensors (built-in path does not import imgen_feb patches).
if os.name == "nt":
    try:
        import windows_zimage_safetensors_patch as _wzsp

        _wzsp.apply_patches()
    except Exception as _wz_err:
        print(f"[WARN] windows_zimage_safetensors_patch failed: {_wz_err}", flush=True)


def _windows_big_pipeline_load_kwargs(device: str) -> dict:
    """
    After safetensors shards finish, diffusers still assembles sub-models; peak RAM can
    native-crash on Windows. Use disk-backed state dict offload + disable mmap.
    """
    if sys.platform != "win32" or device != "cuda":
        return {}
    if _env_pick(
        "IMGEN_LOCAL_ZIMAGE_DISABLE_OFFLOAD_STATE_DICT",
        "IMGEN_RUNPOD_DISABLE_OFFLOAD_STATE_DICT",
    ).lower() in ("1", "true", "yes", "on"):
        return {"disable_mmap": True}
    base = os.path.dirname(os.path.abspath(__file__))
    off = os.path.join(base, ".hf_offload_tmp")
    try:
        os.makedirs(off, exist_ok=True)
    except OSError:
        print(f"[WARN] Could not create offload folder {off!r}; load may use more RAM.", flush=True)
        return {"disable_mmap": True}
    _lcm = _env_pick(
        "IMGEN_LOCAL_ZIMAGE_LOW_CPU_MEM",
        "IMGEN_RUNPOD_WINDOWS_LOW_CPU_MEM",
        default="1",
    ).lower()
    _low = _lcm not in ("0", "false", "no", "off")
    print(
        f"[INFO] Windows load helpers: offload_state_dict=1 offload_folder={off!r} "
        f"disable_mmap=1 low_cpu_mem_usage={_low} "
        f"(IMGEN_LOCAL_ZIMAGE_LOW_CPU_MEM=0 or IMGEN_RUNPOD_WINDOWS_LOW_CPU_MEM=0 to disable meta init).",
        flush=True,
    )
    return {
        "offload_state_dict": True,
        "offload_folder": off,
        "disable_mmap": True,
        "low_cpu_mem_usage": _low,
    }


@contextmanager
def _windows_limit_model_load_threads():
    """Cap OpenMP/BLAS threads during huge from_pretrained on Windows (reduces native exits)."""
    if sys.platform != "win32":
        yield
        return
    try:
        cap = int(os.environ.get("IMGEN_WIN_MODEL_LOAD_OMP_THREADS", "4"))
    except ValueError:
        cap = 4
    cap = max(1, min(16, cap))
    _keys = (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    )
    _saved = {k: os.environ.get(k) for k in _keys}
    for k in _keys:
        os.environ[k] = str(cap)
    import torch
    _pt, _pio = None, None
    try:
        _pt = torch.get_num_threads()
        torch.set_num_threads(cap)
        try:
            _pio = torch.get_num_interop_threads()
            torch.set_num_interop_threads(1)
        except RuntimeError:
            _pio = None
    except Exception:
        pass
    try:
        yield
    finally:
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            if _pt is not None:
                torch.set_num_threads(_pt)
            if _pio is not None:
                torch.set_num_interop_threads(_pio)
        except Exception:
            pass

# Cached pipeline: reused across generate_image() calls so the model is loaded only once.
_cached_pipeline = None
_cached_device = None
_cached_offload = None  # tuple (use_cpu_offload: bool, sequential_offload: bool)

def _model_id():
    from config import Z_IMAGE_TURBO_MODEL
    return (Z_IMAGE_TURBO_MODEL or "Tongyi-MAI/Z-Image-Turbo").strip()

def _get_pipeline(device, use_cpu_offload_from_start):
    """Return cached pipeline or create, configure, and cache it."""
    global _cached_pipeline, _cached_device, _cached_offload
    _seq_env = os.environ.get("IMGEN_SEQUENTIAL_CPU_OFFLOAD", "").strip().lower() in ("1", "true", "yes")
    _offload_key = (
        use_cpu_offload_from_start,
        _seq_env if (device == "cuda" and use_cpu_offload_from_start) else False,
    )
    if _cached_pipeline is not None and _cached_device == device and _cached_offload == _offload_key:
        return _cached_pipeline
    # Clear stale cache if device/offload changed
    if _cached_pipeline is not None:
        try:
            del _cached_pipeline
        except Exception:
            pass
        _cached_pipeline = None
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    import torch
    model_id = _model_id()
    _win = sys.platform == "win32"
    # CPU: float32 + optional low_cpu_mem saves RAM spikes
    _dtype = torch.float32 if device == "cpu" else torch.bfloat16
    if device == "cuda" and _win:
        # bf16 during large weight materialization has native-crashed on some Windows + RTX 50 stacks; fp16 is safer.
        _use_bf16 = _env_pick(
            "IMGEN_LOCAL_ZIMAGE_BF16",
            "IMGEN_RUNPOD_WINDOWS_BFLOAT16",
            default="0",
        ).lower() in ("1", "true", "yes", "on")
        if not _use_bf16:
            _dtype = torch.float16
            print(
                "[INFO] Windows CUDA: load dtype=float16 "
                "(IMGEN_LOCAL_ZIMAGE_BF16=1 or IMGEN_RUNPOD_WINDOWS_BFLOAT16=1 for bfloat16).",
                flush=True,
            )
    _low_mem = device == "cpu" and _env_pick(
        "IMGEN_LOCAL_ZIMAGE_LOW_CPU_MEM_LOAD",
        "RUNPOD_LOW_CPU_MEM",
    ).lower() in ("1", "true", "yes")
    if device == "cpu" and os.name == "nt":
        _low_mem = False  # Windows: meta-init can AV; match imgen_feb default unless explicitly enabled
    _low_for_pretrained = _low_mem
    _win_load_extras = _windows_big_pipeline_load_kwargs(device)

    if _win:
        print(
            "[INFO] Z-Image load: capping CPU threads during weight load (IMGEN_WIN_MODEL_LOAD_OMP_THREADS)…",
            flush=True,
        )

    if _win:
        # ZImagePipeline import / graph has native-exited on some Windows builds before tqdm even runs.
        print("[INFO] Windows: loading via DiffusionPipeline + trust_remote_code (skipping ZImagePipeline).", flush=True)
        from diffusers import DiffusionPipeline

        with _windows_limit_model_load_threads():
            print(f"[INFO] from_pretrained({model_id!r}) …", flush=True)
            _fp_kw = {
                "torch_dtype": _dtype,
                "use_safetensors": True,
                "trust_remote_code": True,
                "low_cpu_mem_usage": _low_for_pretrained,
            }
            _fp_kw.update(_win_load_extras)
            # accelerate enable_sequential_cpu_offload / enable_model_cpu_offload walks state_dict and
            # calls .to("cpu"); meta tensors from low_cpu_mem_usage=True cause:
            # NotImplementedError: Cannot copy out of meta tensor; no data!
            if device == "cuda" and use_cpu_offload_from_start and _fp_kw.get("low_cpu_mem_usage"):
                print(
                    "[INFO] low_cpu_mem_usage=False for CUDA+CPU offload (meta init is incompatible with sequential offload).",
                    flush=True,
                )
                _fp_kw["low_cpu_mem_usage"] = False
            pipe = DiffusionPipeline.from_pretrained(model_id, **_fp_kw)
    else:
        try:
            from diffusers import ZImagePipeline

            with _windows_limit_model_load_threads():
                pipe = ZImagePipeline.from_pretrained(
                    model_id,
                    torch_dtype=_dtype,
                    use_safetensors=True,
                    low_cpu_mem_usage=_low_for_pretrained,
                )
        except (ImportError, AttributeError):
            from diffusers import DiffusionPipeline

            with _windows_limit_model_load_threads():
                pipe = DiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=_dtype,
                    use_safetensors=True,
                    trust_remote_code=True,
                    low_cpu_mem_usage=_low_for_pretrained,
                )

    print("[INFO] Z-Image pipeline weights loaded; configuring device/offload…", flush=True)

    if device == "cuda":
        if use_cpu_offload_from_start:
            if _seq_env and hasattr(pipe, "enable_sequential_cpu_offload"):
                pipe.enable_sequential_cpu_offload()
            elif hasattr(pipe, "enable_model_cpu_offload"):
                pipe.enable_model_cpu_offload()
        else:
            pipe = pipe.to(device)
        # Lower activation memory during denoise (matches imgen_feb-style tuning)
        try:
            if hasattr(pipe, "enable_vae_slicing"):
                pipe.enable_vae_slicing()
            if hasattr(pipe, "enable_attention_slicing"):
                pipe.enable_attention_slicing("max")
        except Exception:
            pass
    else:
        pipe = pipe.to(device)

    _cached_pipeline = pipe
    _cached_device = device
    _cached_offload = _offload_key
    return pipe

def clear_cached_pipeline():
    """Free the cached pipeline and GPU memory. Next generate_image() will load again."""
    global _cached_pipeline, _cached_device, _cached_offload
    if _cached_pipeline is not None:
        try:
            del _cached_pipeline
        except Exception:
            pass
        _cached_pipeline = None
        _cached_device = None
        _cached_offload = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

# Negative prompt to push the model away from drawing any text (headline appears only in overlay box)
_NEGATIVE_PROMPT_TEXT = "text, words, letters, headline, title, writing, caption, typography, sign, watermark, label, text overlay, magazine cover, magazine headline, yellow text, large text on image, bold text overlay, newspaper headline style"

def generate_image(
    prompt,
    output_path="post_image.jpg",
    height=None,
    width=None,
    num_inference_steps=9,
    guidance_scale=3.5,
    device=None,
    use_cpu_offload_from_start=True,
    clear_pipeline_after_generate=False,
    negative_prompt=None,
    **_kwargs
):
    """Generate image with Z-Image-Turbo via diffusers (ZImagePipeline or DiffusionPipeline). Returns output_path on success else None.
    Pipeline is reused across calls unless clear_pipeline_after_generate=True.
    negative_prompt: used with guidance_scale to suppress text in the image (default: no text/headline)."""
    import torch
    try:
        from diffusers.utils import logging as _dl
        _dl.disable_progress_bar()
    except Exception:
        pass

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    if width is None or height is None:
        try:
            from config import get_post_image_dimensions_45

            width, height = get_post_image_dimensions_45()
        except Exception:
            width, height = 768, 960
    prompt = (prompt or "").strip()
    try:
        from config import IMAGE_VISUAL_MODE
    except ImportError:
        IMAGE_VISUAL_MODE = "classic"
    # Classic mode: vivid suffix. Institutional mode: caller already appends navy/slate suffix — do not fight it.
    if IMAGE_VISUAL_MODE != "institutional":
        if prompt and "vivid" not in prompt.lower():
            prompt = prompt + " Vivid, saturated colors; lively and eye-catching palette."
    # Prevent model from drawing headline/text — only one headline, inside the overlay box
    _no_text = " Do not draw or render any text, words, headlines, titles, magazine headlines, or letters anywhere in the image. No magazine-style text. Visual scene and objects only. The headline is added separately."
    if prompt and _no_text.strip().lower() not in prompt.lower():
        prompt = prompt + _no_text

    neg = negative_prompt if negative_prompt is not None else _NEGATIVE_PROMPT_TEXT
    # guidance_scale > 0 needed for negative_prompt to take effect
    use_guidance = guidance_scale if guidance_scale is not None and float(guidance_scale) > 0 else 3.5

    pipe = None
    try:
        pipe = _get_pipeline(device, use_cpu_offload_from_start if device == "cuda" else False)
        call_kw = dict(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=num_inference_steps,
            guidance_scale=use_guidance,
            negative_prompt=neg,
        )
        try:
            image = pipe(**call_kw).images[0]
        except TypeError:
            # Pipeline may not support negative_prompt; retry without it
            call_kw.pop("negative_prompt", None)
            image = pipe(**call_kw).images[0]
        image.save(output_path)

        if clear_pipeline_after_generate:
            clear_cached_pipeline()
        return output_path
    except Exception as e:
        import traceback
        print(f"Local Z-Image (diffusers / runpod_image.py) error: {e}")
        traceback.print_exc()
        try:
            from windows_memory_errors import (
                is_windows_paging_file_error,
                print_windows_paging_file_help,
            )

            if is_windows_paging_file_error(e):
                print_windows_paging_file_help()
        except ImportError:
            pass
        clear_cached_pipeline()
        return None
