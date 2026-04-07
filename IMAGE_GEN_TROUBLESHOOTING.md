# Why image generation errors keep recurring

You're using **system Python** (e.g. `C:\Users\user\AppData\Local\Programs\Python\Python311`) with many packages installed (TensorFlow, growwapi, grpcio, etc.). Those packages depend on **different versions** of the same libraries (e.g. protobuf 5.x, older transformers). When you run the pipeline:

1. **protobuf** – TensorFlow/grpcio want protobuf 5.x; diffusers’ dependency chain expects 3.x and uses `runtime_version`, which was removed in 4+.  
2. **transformers** – Something in your env can leave `transformers` in a state where `AutoImageProcessor` / `PreTrainedModel` aren’t at the top level, so diffusers’ `from transformers import …` fails.

So the **same kind** of error (missing attribute/import) can **recur with different names** (runtime_version, AutoImageProcessor, etc.) because of **version clashes** in one global environment.

### "cannot import name 'message' or 'descriptor' from 'google.protobuf'"

TensorFlow (pulled in by transformers) needs `google.protobuf.message` and `google.protobuf.descriptor`. If your protobuf is wrong or broken you get this. **Fix:** reinstall protobuf in the **same** Python/venv you use to run the pipeline:

**Command Prompt (project venv):**
```cmd
cd /d "c:\Users\user\Documents\Auto Posting Facebook"
.venv\Scripts\pip install --force-reinstall protobuf==3.20.3
.venv\Scripts\activate.bat
python run_continuous_posts.py
```

Or double‑click **`fix_protobuf.bat`** in the project folder, then run the pipeline as usual.

### `cannot import name 'AutoImageProcessor' or 'PreTrainedModel' from 'transformers'`

**Cause:** Incomplete/broken `transformers` install, or a global env where another package overwrote files.

**Fix (same Python you use for `run_continuous_posts.py`):**

```cmd
cd /d "c:\Users\user\Documents\Auto Posting Facebook"
python -m pip install --force-reinstall "transformers>=4.52.0,<5.0" "tokenizers>=0.22.0,<=0.23.0"
python -c "from transformers import PreTrainedModel, AutoImageProcessor; print('OK')"
```

Or double‑click **`fix_transformers.bat`**.

The project also loads **`transformers_shim.py`** before `diffusers` so submodule imports work when top-level exports are missing — **still reinstall** `transformers` for a stable setup.

### `cannot import name 'runtime_version' from 'google.protobuf'` (after `import tensorflow` / `PreTrainedModel`)

**Cause:** With `USE_TORCH` and `USE_TF` both on **AUTO**, Hugging Face `transformers` enables **TensorFlow** if it’s installed. TensorFlow 2.20+ needs **protobuf ≥ 5.28** (`runtime_version`). A **protobuf 3.20.x** pin (for diffusers/grpc) then conflicts.

**Fix (recommended for this project):** Run **PyTorch-only** — the pipeline sets this automatically via `transformers_shim` / `run_continuous_posts.py`:

- `USE_TORCH=1`
- `USE_TF=0`

Manual test in **cmd**:

```cmd
set USE_TORCH=1
set USE_TF=0
python -c "from transformers import PreTrainedModel; print('OK')"
```

**Alternative:** Upgrade protobuf for TensorFlow: `pip install "protobuf>=5.28.0,<6"` (may affect other tools that wanted protobuf 3.x).

### RTX 50 / Blackwell (e.g. RTX 5070) — “not supported by this PyTorch wheel — using CPU”

**Cause:** `imgen feb` detects **compute capability > 9** (e.g. **12.0** on RTX 5070). Many **stable** PyTorch wheels only ship SASS for older architectures; without **sm_120** kernels you can get **native crashes** or **“no kernel image”** errors, so the pipeline **defaults to CPU**.

**Automated fix (recommended):** from the project folder run:

```cmd
python scripts\setup_blackwell_gpu.py
```

Or double‑click **`setup_blackwell_gpu.bat`**. That installs **nightly PyTorch (cu128)** and adds missing lines to **`.env`** (`IMGEN_FEB_DEVICE`, `IMGEN_SKIP_GPU_CAPABILITY_CHECK`, `USE_TORCH`, `USE_TF`).

**Manual fix (GPU):**

1. Install a PyTorch build that includes **Blackwell / sm_120** support — usually **nightly** with **CUDA 12.8+** (check [pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/) for the current command). Example (verify URL on the site; **cu128** / **cu129** may apply):

```cmd
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

2. Use a **recent NVIDIA driver** (often **566+**) for CUDA 12.8.

3. In **`.env`** (same folder as `run_continuous_posts.py`):

```env
IMGEN_FEB_DEVICE=cuda
IMGEN_SKIP_GPU_CAPABILITY_CHECK=1
```

4. Restart the script. If you still see **CUDA kernel** errors, the wheel still lacks sm_120 — try another nightly / newer cu12x index, or use **CPU** until a matching stable build exists.

**Note:** `python scripts\setup_blackwell_gpu.py` now installs into **`.venv\Scripts\python.exe`** when a `.venv` folder exists (so it matches `run_continuous_posts` if you activate that venv). Use **`--use-current-python`** only if you intentionally use system Python.

### `CUDA error: no kernel image is available for execution on the device`

**Cause:** PyTorch in **this** environment has **no CUDA kernels** for your GPU (typical on **RTX 50 / sm_120** with an old wheel). **`torch.cuda.is_available()` can still be True.**

**Very common:** Nightly torch was installed for **system Python**, but you run the pipeline as **`(.venv) python run_continuous_posts.py`** — the **venv** still has an older torch.

**Fix (Windows, project folder):**

```cmd
cd /d "c:\Users\user\Documents\Auto Posting Facebook"
install_nightly_torch_venv.bat
```

Then verify (must say **kernel smoke test: OK**):

```cmd
.venv\Scripts\python.exe check_gpu.py
```

Always start the pipeline with the **same** Python:

```cmd
.venv\Scripts\activate.bat
python run_continuous_posts.py
```

### `unexpected keyword argument 'is_quantized'` (Windows / imgen_feb)

The `imgen feb` package patches `transformers.modeling_utils.load_state_dict` for Windows safetensors stability. Newer `transformers` passes `is_quantized=` into that function; the patch must forward it. **Fix:** update `C:\Users\user\Documents\imgen feb\generate_image.py` (the `_load_state_dict_tf` wrapper) — the project’s copy is patched to accept `is_quantized` and `**kwargs`.

### Paging file too small / `OSError: ... (os error 1455)` / `The paging file is too small`

**Cause:** Loading **Z-Image-Turbo** pulls **multi‑GB** safetensors into memory (and the default Windows loader may **clone** each tensor for stability). Windows needs enough **commit limit** = RAM + **page file**. If the page file is small or “System managed” can’t grow (disk full, policy), **`safe_open`** or weight load fails with **Win32 error 1455**.

**Fix (required for most PCs):**

1. **Win + I** → **System** → **About** → **Advanced system settings** → **Performance** → **Settings** → **Advanced** → **Virtual memory** → **Change**.
2. Uncheck **Automatically manage**, select the Windows drive, **Custom size**.
3. Set **Initial** and **Maximum** to at least **32768 MB** (use **49152–65536** if it still fails). Apply, **reboot**.
4. Before generating, close heavy apps (browsers with many tabs, games, other ML tools).

**Optional (may reduce peak RAM during load):** in the **same Command Prompt** before starting Python:

```cmd
set IMGEN_SAFE_SAFETENSORS_MODE=native
```

This uses diffusers’ default safetensors path instead of the **clone-per-tensor** Windows workaround. On some machines **native/mmap** was less stable (crashes); if that happens, remove the variable and rely on a **larger page file** instead.

The pipeline prints a short reminder when it detects this error (`windows_memory_errors.py`).

### Recurring Windows crash after “Loading checkpoint shards” / STRATEGY 1

**Cause:** Full-GPU preload (`IMGEN_TRY_DIRECT_GPU_FIRST` + direct load) often **native-exits** on ~12GB VRAM before Python can catch OOM.

**Fix (automatic):**

1. **`config.py`** (Windows + CUDA) **overwrites** risky `.env` values unless **`IMGEN_ALLOW_WINDOWS_DIRECT_GPU_UNSAFE=1`** — see **`PERFORMANCE.md`**.
2. All recommended launchers **`call windows_imgen_stable_env.cmd`** (same vars as **`run_continuous_in_this_window.cmd`**). Task Scheduler should use **`launch_continuous_posts_daily.cmd`** → **`run_continuous_scheduled.cmd`**.
3. Run **`verify_setup.cmd`** or **`.venv\Scripts\python.exe scripts\verify_windows_stability.py`** to confirm the clamp.

### Strict stabilization (`STRICT_IMAGE_GEN`, preflight, model-only)

`run_continuous_posts.py` loads **`image_gen_preflight.py`** when **`STRICT_IMAGE_GEN=1`** is set (your **`run_local.cmd`** / **`run_continuous_external_helper.cmd`** set this; plain `python run_continuous_posts.py` does not unless you add it to `.env`):

- Expects **`IMGEN_FEB_DEVICE=cuda`** and refuses to start if misconfigured.
- If **`IMGEN_ALLOW_CPU_FALLBACK=false`**, runs a **CUDA kernel smoke test** (same idea as `check_gpu.py`) so you don’t enter the loop with a broken Blackwell wheel.
- With **`IMAGE_GEN_WARM_LOAD=1`** (default with strict), runs **one small Z-Image generation** at startup so weight load happens once, visibly, before the first real post.
- **`config.py`** pins **`HF_DEACTIVATE_ASYNC_LOAD=1`** and (on Windows) **`IMGEN_SAFE_SAFETENSORS_MODE=clone`** when strict — override via `.env` if your machine needs **`native`** instead (may reduce RAM; some PCs crash with mmap).

`imgen feb` will **not** silently downgrade to CPU when **`IMGEN_ALLOW_CPU_FALLBACK=false`** and the GPU kernel probe fails — it returns no image instead.

To skip preflight for quick debugging: **`STRICT_IMAGE_GEN=0`** and/or **`IMAGE_GEN_WARM_LOAD=0`** in `.env`.

### CPU memory (Z-Image on 32GB RAM)

- In `.env`: `IMGEN_FEB_DEVICE=cpu`
- Defaults in `config.py`: **768px** width on CPU (override with `IMGEN_FEB_SIZE=1024` if you have headroom), and **clear pipeline after each image** on CPU (override with `IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE=false` to keep the model loaded for faster repeat runs).

## Reliable fix: use a dedicated venv

Create a **virtual environment** used only for this project. Then only this project’s dependencies are installed (protobuf 3.x, correct transformers, etc.) and nothing else can override them.

```powershell
cd "C:\Users\user\Documents\Auto Posting Facebook"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_continuous_posts.py
```

Always **activate** that venv (`.\.venv\Scripts\Activate.ps1`) before running the pipeline. Then you stop seeing these recurring import errors.

## What we did in code

- **protobuf** – At the top of `content_generator.py` we stub `runtime_version` on `google.protobuf` if it’s missing.  
- **transformers** – `transformers_shim.py` (imported from `content_generator.py`, `runpod_image.py`, and `imgen feb/generate_image.py`) attaches `AutoImageProcessor`, `PreTrainedModel`, `AutoTokenizer`, etc. from submodules if the top-level package omits them.

These workarounds help when you keep using system Python, but they are fragile: the next dependency that expects a different version can cause a **new** recurring error. The robust solution is the venv above.
