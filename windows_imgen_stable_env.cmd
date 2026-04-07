@echo off
REM Shared stable env for Z-Image on Windows (~12GB VRAM, RTX 40/50).
REM Usage (from project root):  call "%~dp0windows_imgen_stable_env.cmd"
REM config.py also clamps TRY_DIRECT / ALLOW_WINDOWS unless IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE=1
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
set IMGEN_FEB_DEVICE=cuda
set IMGEN_ALLOW_CPU_FALLBACK=false
set ALLOW_FALLBACK_POST_IMAGE=false
set STRICT_IMAGE_GEN=1
set IMAGE_GEN_WARM_LOAD=0
set IMGEN_SAFE_SAFETENSORS_MODE=clone
set IMGEN_DISABLE_SAFETENSORS_MMAP=1
set HF_DEACTIVATE_ASYNC_LOAD=1
set IMGEN_FEB_SIZE=768
REM Prefer local Hugging Face diffusers (runpod_image.py) before imgen_feb. Alias: IMGEN_PREFER_LOCAL_DIFFUSERS_FIRST=1
set IMGEN_PREFER_RUNPOD_IMAGE_LOCAL=1
set IMGEN_TRY_DIRECT_GPU_FIRST=0
set IMGEN_FORCE_CPU_OFFLOAD=1
REM Lower peak VRAM when attaching offload (slower): model runs submodules one-by-one on GPU
set IMGEN_SEQUENTIAL_CPU_OFFLOAD=1
REM Breaking News + headline box on the image (default in config.py is ON — do not force OFF here or posts look “plain”)
set USE_SENSATIONAL_BREAKING_TEMPLATE=1
set USE_MINIMAL_BREAKING_OVERLAY=1
