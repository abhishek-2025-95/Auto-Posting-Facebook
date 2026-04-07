# Faster image generation (local GPU)

**Defaults (Mar 2026):** `config.py` sets **`IMGEN_TRY_DIRECT_GPU_FIRST=0`** for **`IMGEN_FEB_DEVICE=cuda`**. **On Windows + CUDA**, `config.py` **overwrites** `.env` so **`IMGEN_TRY_DIRECT_GPU_FIRST=0`**, **`IMGEN_ALLOW_WINDOWS_DIRECT_GPU=0`**, and **`IMGEN_FORCE_CPU_OFFLOAD=1`** unless **`IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE=1`** (so old `.env` lines cannot bring back STRATEGY‑1 crashes). **`imgen feb`** also skips full-GPU if VRAM **&lt; 16 GB** on Windows. To skip forced offload while staying “safe” from TRY_DIRECT: **`IMGEN_WIN_SKIP_FORCE_CPU_OFFLOAD=1`**. **`IMGEN_WIN_MODEL_LOAD_OMP_THREADS`** (default **4**) caps threads during `from_pretrained` on Windows. **`expandable_segments`** in **`PYTORCH_CUDA_ALLOC_CONF`** is stripped on Windows (unsupported). **Local diffusers** (`runpod_image.py`, legacy filename) runs **before** `imgen_feb` by default — set **`IMGEN_PREFER_LOCAL_DIFFUSERS_FIRST=0`** to skip it, or use legacy **`IMGEN_PREFER_RUNPOD_IMAGE_LOCAL=0`**. This is **your PC**, not RunPod, unless you use a remote image URL.

Your **RTX 5070 (~12 GB VRAM)** + **32 GB RAM** should use **model CPU offload** (GPU runs active layers) — full-GPU Z-Image-Turbo often **crashes** before OOM handling.

## What was slowing you down

1. **Model CPU offload (default on 12 GB)**  
   Weights stream **CPU↔GPU** — slower than full-GPU, but **full-GPU on ~12 GB** frequently **hard-exits** Windows after checkpoint load. Use offload unless you have **16+ GB VRAM** and accept experimentation (`IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE=1`).

2. **First load**  
   First run downloads weights and builds CUDA contexts — expect **minutes once**.

3. **Later runs**  
   With **`IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE=false`** (default on **CUDA**), the model **stays in VRAM** — cycle 2+ should be **much** faster than cycle 1.

4. **Ollama + news + Facebook**  
   Those steps are **network / LLM** bound — they will not use all **16 threads**.

## `.env` (optional — many speed settings are automatic)

`setup_blackwell_gpu.py` appends a stable bundle: **`IMGEN_TRY_DIRECT_GPU_FIRST=0`**, **`IMGEN_ALLOW_WINDOWS_DIRECT_GPU=0`**, plus Blackwell skip-check and step count.

**If the process vanishes after “Loading checkpoint shards”:** you were on **full-GPU** — remove `IMGEN_TRY_DIRECT_GPU_FIRST=1` from `.env` or rely on the automatic **VRAM &lt; 16 GB** skip on Windows. **`IMGEN_FORCE_CPU_OFFLOAD=1`** forces offload always.

## Tunables (imgen feb)

| Variable | Effect |
|----------|--------|
| `IMGEN_TRY_DIRECT_GPU_FIRST=1` | Full-GPU load first (Windows: needs **`IMGEN_ALLOW_WINDOWS_DIRECT_GPU=1`** and VRAM ≥ **`IMGEN_WINDOWS_DIRECT_GPU_MIN_VRAM_GB`**, default 16) |
| `IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE=1` | Bypass VRAM floor (may crash on 12 GB) |
| `IMGEN_OFFLOAD_VRAM_THRESHOLD_GB` | Auto mode: offload if `VRAM <` this (default **14**) |
| `IMGEN_FEB_USE_CPU_OFFLOAD` | `false` = **always** full-GPU (risk OOM); `true` = **auto** (`None` passed to imgen) |
| `IMGEN_FORCE_CPU_OFFLOAD=1` | Always offload (safest, slowest) |
| `IMGEN_FEB_INFERENCE_STEPS` | Lower = faster, less refinement (Turbo often **6–8**) |
| `IMGEN_FEB_SIZE` | Lower resolution = faster (default **1024** width on GPU) |

## Windows / Triton / xformers

**Triton** is often missing on Windows — you may see **warnings**; inference still runs. **FutureWarning** spam from **torch 2.12 dev** + diffusers is harmless.

```cmd
set PYTHONWARNINGS=ignore::FutureWarning
```

---

After changing `.env`, **restart** `run_continuous_posts.py`.
