# Auto Posting to a Facebook Page (Windows)

This project lets you post text, links, and images to a Facebook Page using the Graph API. It includes a simple CLI and Windows-friendly instructions.

**Quick start:** See **[QUICKSTART.md](QUICKSTART.md)** for one-command runs (local, RunPod, Kaggle, verify).  
**Status checklist (external CMD, Task Scheduler, tokens):** **[SUPERAGENT_READY.md](SUPERAGENT_READY.md)** — run **`verify_setup.cmd`** to re-check Python, schedule tests, and the **Facebook Auto Posting 645** task.

## Prerequisites
- Python 3.10+ installed and on PATH
- A Facebook Page you manage
- A Facebook Developer app with Page access (see below)

## 1) Create your Facebook Page (if you don't have one)
- In Facebook, go to Pages → Create new Page.

## 2) Create a Facebook Developer app and get a Page access token
1. Go to the Facebook Developers site and create an app (e.g., "Business" type).
2. Add the "Facebook Login" product if needed and the "Pages API" permissions.
3. In "App Review", request and get approved for required permissions depending on what you plan to post (often `pages_manage_posts`, `pages_read_engagement`). For testing on your own Page in development mode, you can add yourself as a tester and bypass review until you go live.
4. Use the Graph API Explorer or your app to generate a **Page access token** for your Page. Ensure it's associated with the Page (not a user token) and has the scopes above.
5. Note your **Page ID** and the **Page Access Token**.

Tip: Long-lived tokens are recommended. See Facebook docs for converting short-lived to long-lived tokens.

## 3) Setup the project
```powershell
cd "C:\Users\user\Documents\Auto Posting Facebook"
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e "c:\Users\user\Documents\imgen feb"
copy .env.example .env
# Edit .env: add GEMINI_API_KEY (or use Ollama), NEWS_API_KEY (optional), PAGE_ID, PAGE_ACCESS_TOKEN
```

**Image generation:** For AI-generated images (e.g. Z-Image-Turbo), install the local image-gen package in editable mode:
```powershell
pip install -e "c:\Users\user\Documents\imgen feb"
```

**NVIDIA RTX 50 / Blackwell (e.g. RTX 5070):** Stable PyTorch may not include `sm_120` kernels. **`no kernel image`** usually means the **wrong Python** got nightly torch (system vs **`.venv`**). Use **`install_nightly_torch_venv.bat`** or **`setup_blackwell_gpu.bat`** (installs into `.venv` when present). Verify: **`.venv\Scripts\python.exe check_gpu.py`** must show **kernel smoke test: OK**. Details: **[IMAGE_GEN_TROUBLESHOOTING.md](IMAGE_GEN_TROUBLESHOOTING.md)**.

**GPU still slow after CUDA works?** Default is **offload-first** (`IMGEN_TRY_DIRECT_GPU_FIRST=0`) on CUDA for **~12 GB** stability; full-GPU needs **16+ GB VRAM** on Windows (see **[PERFORMANCE.md](PERFORMANCE.md)**). Optional: **6 inference steps** for Turbo via `.env` / setup script.

Edit `.env`:
```
PAGE_ID=123456789012345
PAGE_ACCESS_TOKEN=EAAB...snip
GRAPH_API_VERSION=v21.0
```

**Long-lived (“permanent”) Page token:** Explorer tokens often expire in hours. For 24/7 posting, exchange once using your app credentials:
1. Add **`FACEBOOK_APP_ID`** and **`FACEBOOK_APP_SECRET`** to `.env` (Meta → *Your App* → **Settings → Basic**).
2. Put your **current** `PAGE_ACCESS_TOKEN` in `.env` (the one to exchange) and correct **`PAGE_ID`**.
3. Run:
```powershell
python ensure_long_lived_token.py --write-env
```
This updates `.env` with a Page token that typically **does not expire on a short timer** (until you revoke the app, change password, or Meta invalidates it). A backup `.env.bak` is created the first time.  
Without `--write-env`, the script only prints the new token for manual paste.  
For **Business** apps, Meta also supports **System User** tokens for maximum uptime — see Meta docs for *System Users*.

## 4) Basic Usage
Post a text status:
```powershell
python cli.py post-text "Hello from the API!"
```

Post a link with optional UTM tagging:
```powershell
python cli.py post-link "https://example.com/landing" --message "Check this out" \
  --utm_source facebook --utm_medium social --utm_campaign launch
```

Post an image from a file:
```powershell
python cli.py post-image "C:\path\to\image.jpg" --caption "Nice photo"
```

Post an image from a URL:
```powershell
python cli.py post-image-url "https://example.com/image.jpg" --caption "Remote image"
```

### Manual Cursor video (18s, five scenes)

**Scene images:** use **Cursor’s image tool only**. This workflow does not call local Z-Image/imgen or any other automated generator for those five frames.

Assisted workflow: one finance story → five Cursor-generated stills → one vertical MP4 with **full-summary subtitles** and **breaking-news branding** (`video_branding.brand_video_for_posting`). Requires **ffmpeg** on PATH and **moviepy**.

**From the news pipeline (fresh US/UK–scoped finance story):** writes `article.json`, `cursor_video_pack.json`, and `CURSOR_IMAGES_README.txt` under the output folder — you then create the five images in Cursor and run `render`.

```powershell
cd "C:\Users\user\Documents\Auto Posting Facebook"
python scripts\render_manual_cursor_video.py fetch-us-uk-pack --out-dir .\cursor_video_work
```

1. **Export prompts** when you already have an article JSON:

```powershell
cd "C:\Users\user\Documents\Auto Posting Facebook"
python scripts\render_manual_cursor_video.py prompts --article .\my_article.json -o .\manual_cursor_pack.json
```

`my_article.json` uses fields like `title`, `summary` or `description` (same shape as other article dicts). Or pass `--title` and `--summary` without `--article`.

2. **Generate images in Cursor** from the five `cursor_prompts` entries (hook → context → catalyst → reaction → outlook). Save as `scene0.png` … `scene4.png`.

3. **Render the final file** (default: burn-in subtitles + branding):

```powershell
python scripts\render_manual_cursor_video.py render `
  --images .\scene0.png .\scene1.png .\scene2.png .\scene3.png .\scene4.png `
  --output .\manual_post_video.mp4 `
  --article .\my_article.json
```

The **output path** you pass to `--output` is the deliverable MP4. Use `--subtitle-text "..."` to override on-screen text; `--headline "..."` sets the branded lower-third title. Pass `--no-subtitles` or `--no-branding` to skip a step.

Python API (same pipeline): `build_render_plan`, `build_manual_video_story_arc`, `build_cursor_prompt_pack`, `build_final_manual_cursor_video` in `manual_cursor_video_flow.py`. Tests: `python -m pytest tests/test_manual_cursor_video_flow.py -v`.

## 5) Content Calendar (CSV/JSON)
- CSV headers supported (case-insensitive): `when,type,message,link,image_path,image_url,caption,utm_source,utm_medium,utm_campaign,utm_term,utm_content`
- JSON can be an array of items or `{ "items": [ ... ] }` with the same fields.
- Date formats supported: `YYYY-MM-DD HH:MM`, `YYYY-MM-DD HH:MM:SS`, or ISO like `2025-10-16T09:00`.

Run due items and exit:
```powershell
python cli.py post-from-calendar ".\calendar.csv" --dry-run   # preview
python cli.py post-from-calendar ".\calendar.csv"            # actually post
python cli.py post-from-calendar ".\calendar.json" --max 3   # cap number
```

Run a simple scheduler (polls every 60s by default):
```powershell
python cli.py run-scheduler ".\calendar.csv" --interval 60
```

Example CSV (`calendar.csv`):
```
when,type,message,link,image_path,image_url,caption,utm_source,utm_medium,utm_campaign
2025-10-17 09:00,text,"Good morning!",,,,,,,
2025-10-17 10:00,link,"Read our blog",https://example.com/blog,,,,,facebook,social,october
2025-10-17 11:00,image,,,"C:\\images\\post1.jpg",,"Nice pic",,,,
```

## 6) Folder Ingestion (images + captions)
Post all images in a folder. Captions can be derived from filenames, `.txt` sidecars, or none.
```powershell
# From filenames (default): image `my_new_product.jpg` -> caption "my new product"
python cli.py post-from-folder "C:\images" --caption-source filename

# From sidecar .txt: for `photo.jpg`, use `photo.txt` as caption
python cli.py post-from-folder "C:\images" --caption-source txt

# Apply filters, limit and add prefix/suffix
python cli.py post-from-folder "C:\images" --pattern "*.jpg" --limit 10 --prefix "New:" --suffix "#promo"
```

## 7) Scheduling on Windows (Task Scheduler)
Use Task Scheduler to automate posts.

Example: daily run of due calendar items at 9:00 AM.
1. Open Task Scheduler → Create Task.
2. General: Run only when user is logged on (for simplicity during setup).
3. Triggers: New → Daily → 9:00 AM.
4. Actions: New → Start a program.
   - Program/script: `powershell.exe`
   - Add arguments (use `-Path` or `-CalendarPath` for the calendar file):
     ```
     -NoProfile -ExecutionPolicy Bypass -File "C:\Users\user\Documents\Auto Posting Facebook\scripts\post.ps1" -Command "post-from-calendar" -Path "C:\Users\user\Documents\Auto Posting Facebook\calendar.csv"
     ```
   - Start in: `C:\Users\user\Documents\Auto Posting Facebook`

**Check that auto posting is working:**
- **Dry-run (no real post):**  
  `python cli.py post-from-calendar ".\calendar.csv" --dry-run`  
  Shows which items would run. Times in the calendar use your **local PC time**.
- **Run due items once:**  
  `python cli.py post-from-calendar ".\calendar.csv"`  
  Posts all due items and exits.
- **Continuous scheduler (runs until you stop it):**  
  `python cli.py run-scheduler ".\calendar.csv" --interval 60`  
  Checks every 60 seconds and posts when an item’s time is due.
- If you use **Task Scheduler**, ensure the task runs at the right time, the user is logged on (unless configured otherwise), and the **Start in** folder is the project folder so `.\calendar.csv` and `.env` are found.

## 8) Ollama (open-source, local – instead of Gemini)
For **captions** and **image prompts** (and optional **image generation**), the project can use [Ollama](https://ollama.com) so you don’t depend on Gemini quota or keys.

- **Install Ollama:** Download from https://ollama.com and run `ollama serve` (or start the app).
- **Pull a text model:** e.g. `ollama pull llama3.2` or `ollama pull mistral`.
- **Optional image model:** e.g. `ollama pull x/z-image-turbo` (if your Ollama supports image generation).
- **Config in `config.py`:** Set `USE_OLLAMA = True`, and optionally `OLLAMA_TEXT_MODEL`, `OLLAMA_IMAGE_MODEL`, `OLLAMA_BASE_URL`.

When `USE_OLLAMA` is True and Ollama is running, captions and image prompts use Ollama; image generation tries imgen_feb → Ollama → Vertex/Gemini/placeholder.

**Multiple projects using Ollama at once:** By default Ollama handles one request at a time. To allow **concurrent** requests, set this on the **machine where Ollama runs**, then restart Ollama: **Windows:** System Properties → Environment variables → New → `OLLAMA_NUM_PARALLEL` = `4` (or 6–8 if you have enough VRAM). **Mac/Linux:** `export OLLAMA_NUM_PARALLEL=4` before `ollama serve`. With `OLLAMA_NUM_PARALLEL=4`, up to four projects can get responses at the same time.

## 9) Vintage Newspaper style (Flodia / 2026 strategy)
For **Human Interest** and **long-form** news, the project can apply a vintage newspaper look to images (paper texture, sepia, serif headline bar, subtle tape/stains). This can improve "Time on Post" and CMP.

- **Toggle in config:** Set `USE_VINTAGE_NEWSPAPER_STYLE = True` (or `False`) in `config.py`.
- **Applied automatically** when using image fallback (e.g. `test_image_post_then_schedule.py`).
- **Content ideas:** "On This Day" history, long-form profiles, myth-busting/trivia in broadsheet style. Headlines use high-contrast serif for Meta’s AI and storytelling reach.

## 9a) Using Kaggle's free GPU
You can run the **full post cycle** on **Kaggle's free GPU** (P100 or T4 x2, ~30 hours/week) so you don't need a local GPU.

**Notebook:** `kaggle_free_gpu.ipynb` in this project.

1. **Upload:** Go to [Kaggle Notebooks](https://www.kaggle.com/code) → **New Notebook** → **File** → **Upload Notebook** → select `kaggle_free_gpu.ipynb` (or create a notebook and copy its cells).
2. **Enable GPU:** Right panel → **Settings** → **Accelerator** → **GPU** (P100 or T4 x2). Save.
3. **Secrets:** **Add-ons** → **Secrets** → create and attach:
   - `GEMINI_API_KEY` – Google AI Studio API key  
   - `NEWS_API_KEY` – newsdata.io key *(optional; if missing, uses BBC News RSS)*  
   - `PAGE_ACCESS_TOKEN` – Facebook Page access token  
   - `PAGE_ID` – Facebook Page ID  
4. **Run All.** The notebook will: fetch one article (newsdata.io or BBC RSS), generate caption and image prompt with **Gemini** (locally you can use **Ollama** via `USE_OLLAMA` in config; on Kaggle only Gemini is available), generate the image with **Z-Image-Turbo on GPU**, apply a headline overlay, and post to your Facebook Page. The image is saved at `/kaggle/working/post_image.jpg` and shown in the last cell; download from the **Output** tab if needed.

**Reference:** `kaggle_free_gpu_run.py` is a single-file version of the same flow for copy-paste into a new notebook.

## 9b) RunPod (24/7 or scheduled in the cloud)
Run the pipeline on a **RunPod** GPU pod (e.g. RTX 2000 Ada) for 24/7 or scheduled posting without using your PC. Supports open source (Z-Image-Turbo, Ollama) and API-based (Gemini) models.

**Run everything on RunPod only (no VPS):** See **[RUNPOD_ONLY.md](RUNPOD_ONLY.md)** — one pod does news, caption, image (GPU), overlay, and Facebook post. From your PC run `python deploy_and_run_runpod.py` to create a pod (if needed) and deploy + start the pipeline; set `RUNPOD=1` when running on the pod; do not set `RUNPOD_IMAGE_API_URL`.

**Full steps / other options:** See **[RUNPOD_SETUP.md](RUNPOD_SETUP.md)**.

**Short version (full pod):** Deploy a pod → SSH in → clone project → `pip install -r requirements.txt` → create `.env` (GEMINI_API_KEY, PAGE_ID, PAGE_ACCESS_TOKEN) → set `RUNPOD=1` → run `python run_continuous_posts.py` (continuous; **US/Eastern windows + 10 posts/day** by default — see **US/Eastern schedule** below) or `RUNPOD=1 python run_one_cycle.py` (single cycle for cron).

**Split (image-only on RunPod, rest on VPS):** Run **only** `runpod_image_server.py` on the RunPod pod; on your VPS set `RUNPOD_IMAGE_API_URL=http://<pod-ip>:5000` and run the full pipeline (no GPU on VPS). See **RUNPOD_SETUP.md** → "Alternative: Split setup".

## 10) Troubleshooting
- 400/403: permissions or token issues. Verify token scopes and Page association.
- 429/5xx: transient; the client retries with backoff.
- Token expired? Regenerate Page token.

**Why is our model (imgen_feb / Z-Image-Turbo) failing?**  
When you run the poster from the Auto Posting Facebook folder, Python uses **this project’s** environment (its `.venv` or system packages). The imgen_feb code runs from the "imgen feb" folder, but **diffusers** and **huggingface_hub** are loaded from the **Auto Posting Facebook** environment. Newer `huggingface_hub` removed `is_offline_mode`, which older `diffusers` still expects, so you get: `cannot import name 'is_offline_mode' from 'huggingface_hub'`.  

**Fix (use the same env you use to run the poster):**
```cmd
cd "c:\Users\user\Documents\Auto Posting Facebook"
.venv\Scripts\activate
pip install "huggingface_hub>=0.20,<0.26"
```
Then run `python test_image_post_then_schedule.py` again. If you don’t use a venv here, run the `pip install` in the same Python environment you use for the script.

## Troubleshooting: "can't open file ... feb\\.venv\\Scripts\\python.exe"
That error means something is running Python with the wrong "script" (a non-existent venv path). Fix it by running the script explicitly:
- **In CMD or PowerShell (from project folder):**
  ```powershell
  & "C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" "test_image_post_then_schedule.py"
  ```
- Or double-click **`run_post_now_then_schedule.bat`** in the project folder.
If you use Task Scheduler or a shortcut, set the **program** to `python.exe` and the **argument** to `test_image_post_then_schedule.py` (not any path containing `feb` or `.venv`).

## 11) Memory & performance
If the process stops during image generation or you want to reduce RAM/VRAM use:

- **Image size:** In `config.py`, set `IMGEN_FEB_SIZE = 512` (default 768) to lower VRAM for imgen_feb (Z-Image-Turbo). 512 is enough for 4:5 overlay; 768 needs more GPU memory.
- **Image style (default):** **`IMAGE_VISUAL_MODE=classic`** (default)—photoreal news/editorial photography; prompts forbid abstract chart/terminal templates. Optional **`IMAGE_VISUAL_MODE=institutional`** for dark-mode terminal / abstract chart art. Optional: `INSTITUTIONAL_ACCENT_HEX=#00B8D4`. **News:** Defaults favor **US/European financial markets + economy** only (`NEWS_MARKETS_US_EUROPE_ONLY`, `NEWS_BREAKING_FINANCE_REPUTED_ONLY`) from **reputed outlets** (no Reddit/Google in that mode). Adjust in `.env` only if you need a wider scope.
- **Design agent:** In `design_config.py`, set `USE_DESIGN_AGENT = False` to skip per-image color analysis (K-Means) and optional LLM design schema. Saves one image load and some CPU/memory per post.
- **Design LLM only:** Keep `USE_DESIGN_AGENT = True` but set `USE_DESIGN_AGENT_LLM_SCHEMA = False` to keep color theming but skip the extra Gemini/Ollama call for mood/typography schema.
- **Generated image path:** The post image is always saved as `post_image.jpg` in the project folder so the pipeline and cleanup find it reliably.

### Memory-efficient workflow & productivity
The pipeline is tuned for low memory use and faster cycles:

- **One file open per image:** With the minimal overlay, the "AI Generated" label is drawn in the same pass as the overlay and the image is saved once. The Facebook post step does not reopen the file (no duplicate label pass).
- **Caption + image prompt in parallel:** `run_continuous_posts.py` runs caption generation and image-prompt generation in parallel, then generates the image. This shortens each cycle.
- **GC after each cycle:** The runner runs `gc.collect()` after each post so memory (and GPU allocations where applicable) can be reclaimed before the next cycle.
- **Design agent:** K-Means color analysis uses a 2000-pixel sample and a downsampled image to limit RAM; disable with `USE_DESIGN_AGENT = False` if you want to save more.

### How many parallel workflows can I run?
Each run of `run_continuous_posts.py` (or `test_image_post_then_schedule.py`) is **one workflow**: fetch news → caption → generate image (imgen_feb) → overlay → post. The app does **not** run multiple workflows inside one process; it’s one cycle after another.

To run **parallel** workflows you run **multiple processes** (e.g. several terminals, each in a **different project copy** so each has its own `post_image.jpg` and `posted_articles.json`). The limit is usually **GPU VRAM**, because each process loads its own copy of the imgen_feb (Z-Image-Turbo) model:

| Your VRAM (typical) | IMGEN_FEB_SIZE | Suggested max parallel workflows |
|---------------------|----------------|-----------------------------------|
| ~12 GB (e.g. RTX 4070/5070) | 768 (default) | **1** (safe) |
| ~12 GB | 512 | **1–2** (2 may be tight; try and watch for OOM) |
| ~16 GB+ | 768 or 1024 | **2** (possibly 3 at 768 if you don’t run other GPU apps) |

So with your **current** setup (768, 12GB-class GPU): run **1** workflow at a time. For 2 parallel workflows on 12GB, set `IMGEN_FEB_SIZE = 512` and run two separate project copies; if you see out-of-memory errors, reduce back to 1.

### Posting schedule — **US Eastern (EST/EDT)** (`run_continuous_posts.py`)
By default the runner uses **`America/New_York`**, which follows **US Eastern Time** correctly year-round (**EST** in winter, **EDT** in summer). Posting windows are:

| Window | US Eastern local time (end exclusive) |
|--------|----------------------------------------|
| Morning | 07:00–09:00 |
| Lunch | 12:00–13:00 |
| Evening | 19:00–22:00 |

- **Cap:** Up to **`POSTS_PER_DAY`** successful Facebook posts per **US Eastern calendar day** when using the default timezone (default `10` in `config.py`). Only a **successful** post increments the counter (failed cycles, duplicates, preview-only do not).
- **Slot times (default):** Posts are **spread by clock** inside the windows. The day’s `POSTS_PER_DAY` is split across windows **by length** (morning 2h, lunch 1h, evening 3h), then each block uses **even spacing** between window start and end. For **10** posts that is **3 + 2 + 5** with typical **US Eastern** times:
  - **Morning:** 7:30 AM, 8:00 AM, 8:30 AM  
  - **Lunch:** 12:20 PM, 12:40 PM  
  - **Evening:** 7:30, 8:00, 8:30, 9:00, 9:30 PM  
  Post **#1** cannot start before slot 1; if you start late, you **catch up** inside the next open window (still one post per successful completion toward the cap). Changing **`POSTS_PER_DAY`** recomputes counts and spacing automatically.
- **Flood mode (disabled by default):** **`POSTING_SCHEDULE_SLOTS_ONLY=true`** (default) forces **slot timing only** — **`POSTING_SCHEDULE_FLOOD_WINDOWS` is ignored**. To use flood (posts can bunch inside a window), set **`POSTING_SCHEDULE_SLOTS_ONLY=0`**, then **`POSTING_SCHEDULE_FLOOD_WINDOWS=1`** or **`morning`**. **Task Scheduler:** **`TASK_SCHEDULER_645_ET.md`**.
- **State:** Count + date are stored in **`posting_schedule_state.json`** (gitignored). With the default zone, the date is **US Eastern** calendar day.
- **Other timezones (optional):** Set **`POSTING_SCHEDULE_TIMEZONE`** (IANA or alias **`EST`**, **`ET`**, **`IST`**, etc.). Use **US Eastern** for a US audience; use **`IST`** only if you intentionally want 7–9 / 12–1 / 7–10 on **India** local time.
- **Disable:** Set **`ENABLE_US_ET_POSTING_WINDOWS=0`** (or `false` / `off`) in `.env` for the previous **24/7** behavior (still uses `CONTINUOUS_POST_COOLDOWN_SECONDS` between attempts).
- **Windows / `zoneinfo`:** Install **`tzdata`** if you see timezone errors (`pip install tzdata` — already listed in `requirements.txt`).
- **Self-check:** `python tests/test_posting_schedule.py` (US Eastern default). Optional IST override: `python tests/test_posting_schedule_ist.py`

## 12) Export the workflow (replicate or move this working model)

To **export** or **replicate** this workflow on another machine or share it with someone:

### What the workflow does (one cycle)
1. **Fetch** – Get fresh news from **Newsdata.io** (US/UK/Europe), **Reddit**, **Google News**, and **reputed RSS**; skip if already in **local** history (last 25 in `posted_articles.json`).  
   **Defaults:** **`NEWS_MARKETS_US_EUROPE_ONLY=1`** — US/European **markets & economy** angle. **`NEWS_BREAKING_FINANCE_REPUTED_ONLY=1`** — **breaking-style / market-moving** headlines only, **tier‑1 outlets only** (Reuters, Bloomberg, BBC, CNBC, WSJ, FT, etc.); **no Reddit or Google News**. Set either to **`0`** in `.env` to widen sources again. Optional **`NEWS_REQUIRE_BREAKING_HEADLINE=0`** for reputed-only without strict “breaking” wording.
2. **Caption + prompt (parallel)** – Generate Facebook caption and image prompt at the same time (Gemini or Ollama).
2b. **Duplicate check (Facebook)** – If `CHECK_FACEBOOK_FOR_DUPLICATES` is True in `config.py`, compare caption and headline to the **last 50 page posts**; skip this article if too similar (no duplicate post).
3. **Image** – Generate image with imgen_feb (Z-Image-Turbo) at 4:5; apply minimal overlay (Breaking News label, red gradient headline bar, source bottom-left, logo top-right, AI Generated label).
4. **Post** – Upload image + caption to Facebook Page via Graph API; delete local image; repeat after cooldown.

### How to run it (local)
- **Verify news sources:** `python verify_all_sources.py`
- **CMD (copy-paste one line):**
  ```cmd
  cd /d "C:\Users\user\Documents\Auto Posting Facebook" && python run_continuous_posts.py
  ```
  Or double-click **`run_local.cmd`** in the project folder.
- **One post now (test):**  
  `python test_image_post_then_schedule.py`
- **Continuous:**  
  `python run_continuous_posts.py`  
  (posts one immediately, then keeps running cycles with cooldown between them).

**Lighter load (faster image gen):** In `config.py`, `RUN_CAPTION_PROMPT_SEQUENTIAL = True` (caption then prompt, no parallel), `IMGEN_FEB_CLEAR_PIPELINE_AFTER_GENERATE = False` (model stays in memory after first image), `IMGEN_FEB_SIZE = 768` (faster than 1024).

### What to copy to “export” the workflow
- **Code:** This project folder (or at least the core files below).
- **Config (edit for new env):**  
  `config.py` – API keys (Gemini, Newsdata.io, Facebook), `NEWS_COUNTRIES`, `IMGEN_FEB_SIZE`, etc.  
  `design_config.py` – Overlay look (red bar, headline colors, logo, AI label size).
- **Secrets:** `.env` with `PAGE_ID` and `PAGE_ACCESS_TOKEN` (or set `FACEBOOK_ACCESS_TOKEN` / `FACEBOOK_PAGE_ID` in `config.py`).
- **Image model:** Install imgen_feb in the same Python env:  
  `pip install -e "c:\Users\user\Documents\imgen feb"`  
  (or your path to the “imgen feb” package).

### Core files (minimal set for this workflow)
| Role | Files |
|------|--------|
| Runner | `run_continuous_posts.py`, `test_image_post_then_schedule.py` |
| Content + image | `content_generator.py`, `config.py` |
| Overlay | `minimal_overlay.py`, `design_config.py`, `design_utils.py`, `ai_label.py` |
| News | `news_fetcher.py`, `enhanced_news_diversity.py`, `reddit_news_fetcher.py` (if used) |
| Post | `facebook_api.py` |
| Optional | `design_agent.py`, `ollama_client.py` |

### One-command export (same machine)
To run the full workflow with one command (e.g. from Task Scheduler or a shortcut):
```powershell
cd "C:\Users\user\Documents\Auto Posting Facebook"
.\.venv\Scripts\Activate.ps1; python run_continuous_posts.py
```
Or use the batch file: **`run_post_now_then_schedule.bat`** if it points at this workflow.

### Replicate on another PC
1. Copy the project (or the core files above + `requirements.txt`).
2. Create a venv, install deps: `pip install -r requirements.txt` and `pip install -e "<path-to-imgen-feb>"`.
3. Copy and edit `config.py` and `design_config.py`; add `.env` or set Facebook credentials in config.
4. Run `python test_image_post_then_schedule.py` once to verify, then `python run_continuous_posts.py` for continuous posting.

A more detailed step-by-step and file list is in **`WORKFLOW_EXPORT.md`** in this folder.

## Overlay layout on the generated image

The overlay is applied only when you use the **main pipeline** (e.g. `run_continuous_posts.py` or `test_image_post_then_schedule.py` → `content_generator.generate_post_image_fallback`) with **`USE_SENSATIONAL_BREAKING_TEMPLATE`** and **`USE_MINIMAL_BREAKING_OVERLAY`** true in `config.py`. It is **not** applied if you generate images only (e.g. Colab notebook or a script that does not call `apply_minimal_breaking_overlay`).

Positions (same order they are drawn):

| Element | Position | When shown |
|--------|----------|------------|
| **Breaking News** label | **Top-left** – margin from top/left (`BREAKING_LABEL_MARGIN_RATIO`), small gradient bar with "BREAKING NEWS" text | When `SHOW_BREAKING_LABEL` is True in `design_config.py` |
| **Logo** (The Unseen Economy) | **Top-right** – image from `UNSEEN_ECONOMY_LOGO_IMAGE_PATH` or text "The Unseen Economy" | Always (image if file exists, else text) |
| **Headline** (detailed format) | **Lower third** – rounded box near bottom with up to 15 words, scaled to fit; style from `HEADLINE_BOX_STYLE` (`modern` / `frosted` / `minimal`) | When `USE_HEADLINE_BOX` is True in `design_config.py`; headline text comes from the article (short headline) passed by the pipeline |
| **Source** | **Bottom-left** – "Source: &lt;name&gt;" in small white text, just above bottom edge | When the pipeline passes a non-empty `source` to the overlay (from article) |
| **AI Generated** label | **Bottom-right** – mandatory compliance label | Always |

Ensure **`USE_HEADLINE_BOX = True`** and **`HEADLINE_BOX_STYLE = "modern"`** or **`"frosted"`** in `design_config.py` so the **headline appears in the detailed lower-third box**. If the headline is missing, confirm the image was created via the pipeline that calls `apply_minimal_breaking_overlay` with a `headline` argument (e.g. `generate_post_image_fallback` in `content_generator.py`).

**If the image has no Breaking News label, logo, or headline:** Run from the **project folder** (e.g. `cd "C:\Users\user\Documents\Auto Posting Facebook"` then `python run_continuous_posts.py` or `python test_image_post_then_schedule.py`). In `config.py` set **`USE_SENSATIONAL_BREAKING_TEMPLATE = True`** and **`USE_MINIMAL_BREAKING_OVERLAY = True`**. You should see a log line like "Applying overlay..." then "Applied minimal Breaking News overlay...". If you see "Overlay did not apply" or "Minimal overlay failed", check the traceback and that `design_config.py` and `design_utils.py` load (e.g. no import errors).

## Notes
- UTM parameters are supported for `post-link` and calendar link items.
- Endpoints used: `/PAGE_ID/feed` for text/link, `/PAGE_ID/photos` for images.
- **AI Generated label:** Every image posted to the Page (via `facebook_api`, `facebook_poster`, or any script) has the "AI Generated" compliance label applied before upload. This is mandatory and cannot be disabled.
- **Text overlay / legibility:** Design utilities take inspiration from [caption-forge](https://github.com/KvaytG/caption-forge) (automatic contrast-based text color, fit-text-in-box). We use a similar contrast color helper (`get_contrast_text_color` in `design_utils.py`) so headline or label text can be chosen for legibility on any background; optional region sampling for the bar area.
- **Headline box styles** (`design_config.py` → `HEADLINE_BOX_STYLE`): **`modern`** = lower-third rounded box with yellow left accent and optional blur; **`frosted`** = glassmorphism (dark semi-transparent fill, thin white “glass edge” outline, no accent); **`minimal`** = legacy full-width bar. Use **`frosted`** for a sleek Apple/premium-tech look.
- **Text overlay options (ComfyUI-TextOverlay–style):** In `design_config.py` you can use **hex colors** (e.g. `BREAKING_LABEL_TEXT_COLOR = "#FFFFFF"` or `MODERN_HEADLINE_STROKE_FILL = "#000000"`); **`BREAKING_LABEL_X_SHIFT` / `BREAKING_LABEL_Y_SHIFT`** to nudge the top-left label; **`MODERN_HEADLINE_STROKE_RATIO`** (e.g. `0.05`) so headline stroke scales with font size. See [ComfyUI-TextOverlay](https://github.com/Munkyfoot/ComfyUI-TextOverlay) for the inspiration.
- **Professional-grade overlay:** Practices inspired by [CreatiPoster](https://github.com/graphic-design-ai/creatiposter) (multi-layer, editable compositions, text overlay on images): explicit **layer order** (gradient → bar → text → logo → AI label → branding), **safe zone** inset (e.g. 4% from edges) so content never crowds the crop, **minimum headline font size** (10px) for readability, and optional **contrast-based headline color** (`USE_CONTRAST_HEADLINE_COLOR` in `design_config.py`) so the headline adapts to the bar for legibility. Together with fit-text-in-box and strong drop-shadow, overlays stay readable and layout-consistent across devices.