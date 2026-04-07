# Quick start

One command per scenario. Ensure `.env` exists (copy from `.env.example`) with `PAGE_ID`, `PAGE_ACCESS_TOKEN`, and optionally `GEMINI_API_KEY` / `NEWS_API_KEY`.

---

## Local (your PC)

**External terminal (recommended):** double-click **`run_local.cmd`** — stops any **previous** continuous runner for this project, then opens a **new** Command Prompt with `.venv` and runs the pipeline (`cmd /k`). Use **`run_continuous_external_only.cmd`** if you want a second window without killing the first (the new one will exit on lock if one is already running).

**Same window (e.g. already in CMD):**
```cmd
cd /d "C:\Users\user\Documents\Auto Posting Facebook" && .venv\Scripts\activate.bat && python run_continuous_posts.py
```

**Schedule (default):** **US Eastern (EST/EDT)** via `America/New_York` — **7:00–9:00**, **12:00–13:00**, **19:00–22:00** (ends exclusive); up to **10** **successful** posts per **US Eastern** day. Leave **`POSTING_SCHEDULE_TIMEZONE`** unset unless you need another zone (see README). **`pip install tzdata`** on Windows if needed.

---

## RunPod (24/7 or scheduled in cloud)

1. Deploy: [RunPod RTX 2000 Ada + PyTorch](https://console.runpod.io/deploy?type=GPU&gpu=RTX+2000+Ada&count=1&template=runpod-torch-v240)
2. Full steps: **[RUNPOD_SETUP.md](RUNPOD_SETUP.md)**
3. On the pod after setup:
   ```bash
   cd /workspace/auto-posting-facebook && source .venv/bin/activate && RUNPOD=1 python run_continuous_posts.py
   ```
   Single cycle (for cron): `RUNPOD=1 .venv/bin/python run_one_cycle.py`

---

## Kaggle (free GPU, manual run)

1. Upload **`kaggle_free_gpu.ipynb`** to [Kaggle Notebooks](https://www.kaggle.com/code).
2. Settings → Accelerator → **GPU**; Add-ons → **Secrets** → add `GEMINI_API_KEY`, `PAGE_ACCESS_TOKEN`, `PAGE_ID` (and optionally `NEWS_API_KEY`).
3. **Run All.**

---

## Verify (sources + token)

```cmd
cd /d "C:\Users\user\Documents\Auto Posting Facebook" && python verify_all_sources.py && python simple_token_manager.py
```

---

**Config:** `config.py` (image size 768, sequential caption/prompt, no pipeline clear for faster local). Secrets in `.env` (never commit).
