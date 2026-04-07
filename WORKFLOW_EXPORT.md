# Export the workflow – Auto Posting Facebook (working model)

This document describes how to **export** or **replicate** the current working workflow so you can run it on another machine, back it up, or hand it off to someone else.

---

## 1. What this workflow does (one cycle)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. FETCH NEWS                                                           │
│    Newsdata.io (US, UK, Europe) + Reddit → pool of articles              │
│    Skip if same story in last 5 posts (posted_articles.json)             │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. CAPTION + IMAGE PROMPT (parallel)                                     │
│    Gemini or Ollama → caption for Facebook + image prompt for imgen_feb  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. GENERATE IMAGE                                                        │
│    imgen_feb (Z-Image-Turbo) → 4:5 image → save as post_image.jpg       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. OVERLAY (minimal)                                                     │
│    • Breaking News label (top-left)                                      │
│    • Red gradient headline bar (bottom) + white/yellow headline text      │
│    • Source (bottom-left, 50% AI label size)                             │
│    • The Unseen Economy logo (top-right)                                 │
│    • AI Generated label (bottom-right)                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. POST                                                                  │
│    facebook_api → upload post_image.jpg + caption to Page                 │
│    Delete post_image.jpg, save article to posted_articles.json          │
│    gc.collect(); wait CONTINUOUS_POST_COOLDOWN_SECONDS; repeat           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. How to run it

| Goal | Command |
|------|--------|
| **One post now (test)** | `python test_image_post_then_schedule.py` |
| **Continuous 24×7** | `python run_continuous_posts.py` |

Both use the same pipeline; the continuous runner loops with a cooldown (default 30 s).

---

## 3. What to copy to export the workflow

### 3.1 Minimum set of files

- **Runners:** `run_continuous_posts.py`, `test_image_post_then_schedule.py`
- **Content + image gen:** `content_generator.py`, `config.py`
- **Overlay:** `minimal_overlay.py`, `design_config.py`, `design_utils.py`, `ai_label.py`
- **News:** `news_fetcher.py`, `enhanced_news_diversity.py`
- **Optional news:** `reddit_news_fetcher.py` (if Reddit is used)
- **Post:** `facebook_api.py`
- **Optional:** `design_agent.py`, `ollama_client.py`, `vintage_newspaper.py`, `sensational_overlay.py`
- **Project:** `requirements.txt`, `.env.example` (then create `.env`)

### 3.2 Config you must set for a new environment

- **`config.py`**  
  - `GEMINI_API_KEY`, `NEWS_API_KEY`, `FACEBOOK_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`  
  - `NEWS_COUNTRIES`, `IMGEN_FEB_SIZE`, `CONTINUOUS_POST_COOLDOWN_SECONDS`, `USE_OLLAMA`, etc.

- **`design_config.py`**  
  - Overlay behaviour: red bar, headline colors, logo path, AI label size, source label, etc.

- **Secrets**  
  - Either `.env` with `PAGE_ID` and `PAGE_ACCESS_TOKEN`, or set `FACEBOOK_ACCESS_TOKEN` and `FACEBOOK_PAGE_ID` in `config.py`.

### 3.3 External dependency (image model)

- **imgen_feb** (Z-Image-Turbo) must be installed in the **same** Python environment:
  ```powershell
  pip install -e "c:\Users\user\Documents\imgen feb"
  ```
  Use the path where your “imgen feb” package lives. The workflow expects this package to be available when generating images.

---

## 4. One-command run (same machine)

From PowerShell (project folder):

```powershell
cd "C:\Users\user\Documents\Auto Posting Facebook"
.\.venv\Scripts\Activate.ps1; python run_continuous_posts.py
```

Or use **`run_post_now_then_schedule.bat`** if it’s configured to run `run_continuous_posts.py` or `test_image_post_then_schedule.py`.

---

## 5. Replicate on another PC

1. **Copy** the project (or the minimum set in §3.1).
2. **Python:** Create a venv and install deps:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -e "<path-to-imgen-feb>"
   ```
3. **Config:** Edit `config.py` and `design_config.py`; add `.env` or set Facebook credentials in `config.py`.
4. **Test:** Run `python test_image_post_then_schedule.py` once.
5. **Run:** `python run_continuous_posts.py` for continuous posting.

---

## 6. Optional: export config only (no code)

To save only the “working” configuration for this model:

- Copy **`config.py`** and **`design_config.py`** (and optionally `.env` with secrets removed or placeholders).
- Store them with a note like: “Auto Posting Facebook – working config – &lt;date&gt;”.
- On a fresh clone or copy of the repo, overwrite `config.py` and `design_config.py` with these files and add credentials.

This gives you a reproducible “working model” setup without moving the whole codebase.
