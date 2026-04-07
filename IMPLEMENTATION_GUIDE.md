# How to Implement All Changes

All code changes are **already in your project**. The **next image you generate** will use them automatically.

---

## Next image: use the new overlay

- **No config change or reinstall needed.** Just run your usual image flow from the project folder.
- **One full cycle (news → caption → image → post):**
  ```powershell
  cd "c:\Users\user\Documents\Auto Posting Facebook"
  python run_continuous_posts.py
  ```
  The first image in that run will already have only: headline box + headline, Breaking News label, AI Generated label, Source, Unseen Economy logo (no vintage overlay, no bottom gradient, no bar texture).
- **One-off test image only (no posting):**
  ```powershell
  cd "c:\Users\user\Documents\Auto Posting Facebook"
  python test_image_post_then_schedule.py
  ```
- **Overlay only** (you provide an image file):
  ```powershell
  python sample_overlay_current_news.py
  ```

---

## 1. Verify (optional)

From the project folder:

```powershell
cd "c:\Users\user\Documents\Auto Posting Facebook"
python verify_fixes.py
```

You should see: `OK: design_agent...`, `OK: minimal_overlay...`, `OK: headline box clamped...`, `All checks passed.`

---

## 2. Run locally

- **One-off image + overlay:**  
  Run your usual flow (e.g. `run_one_cycle.py` or whatever starts the pipeline). New images will use:
  - Headline only in the bottom box (no duplicate)
  - Complete headline in 2 lines (or ellipsis if too long)
  - Pipeline caching (model loaded once, then reused)
  - Design schema without Gemini if no API key
  - 1024px image size (config)
  - Noto fonts from `fonts/` if present

- **Fonts (same look as RunPod):**  
  If you haven’t already:
  ```powershell
  python download_fonts.py
  ```
  This fills `fonts/` with Noto Sans so typography matches.

---

## 3. Run updated image generation on RunPod

So the pod uses the same behavior as local (one headline in the box only, no text in the image, 15-word summary, etc.):

### Step A: Deploy updated code to the pod (from your PC)

In PowerShell, from the project folder:

```powershell
cd "c:\Users\user\Documents\Auto Posting Facebook"
python setup_runpod_full.py
```

This uploads the latest code (e.g. `content_generator.py`, `runpod_image.py`, `minimal_overlay.py`, `design_config.py`, `design_agent.py`, `design_utils.py`, `config.py`, `download_fonts.py`, `fonts/`, etc.) to the pod. Ensure `.env` has `RUNPOD_SSH_USER` (and `RUNPOD_SSH_KEY` if needed). See `RUNPOD_SETUP.md` if the pod is not set up yet.

### Step B: On the pod — run image generation

**One-off test (one post):**
```bash
cd /workspace/auto-posting-facebook
source .venv/bin/activate
export RUNPOD=1
python run_one_cycle.py
```

**24/7 in background:**
```bash
cd /workspace/auto-posting-facebook && source .venv/bin/activate && export RUNPOD=1 && nohup python start_runpod.py >> runpod.log 2>&1 &
```

**Or use the start script (sets RUNPOD=1 and runs continuous posts):**
```bash
cd /workspace/auto-posting-facebook && . .venv/bin/activate && RUNPOD=1 python -u start_runpod.py
```

No code edits are required on the pod if you redeploy from this project. The next image generated on the pod will use the updated overlay and no-text image prompt.

---

## 4. Summary of what’s in place

| Change | Where | Effect |
|--------|--------|--------|
| Headline box only at bottom | `minimal_overlay.py`, `design_config.py` | Headline never drawn on top of image |
| No duplicate headline | `content_generator.py` (vintage_headline), image prompt | One headline in box; no second from vintage or baked into image |
| Complete headline in box | `minimal_overlay.py`, `design_config.py` | Up to 15 words, 2 lines, ellipsis if truncated; min font 10px |
| Design schema without Gemini | `design_agent.py` | No "No API_KEY" error; uses Ollama or skips |
| Pipeline caching | `runpod_image.py`, `content_generator.py` | Model loaded once per run, reused for later images |
| Same behavior local vs RunPod | `content_generator.py`, `runpod_image.py` | Same config, same post-gen cleanup |
| Larger headline box | `design_config.py` | MODERN_HEADLINE_MAX_BOX_HEIGHT_RATIO = 0.52 |
| 1024 image size | `config.py` | IMGEN_FEB_SIZE = 1024 |
| Noto fonts in project | `download_fonts.py`, `fonts/`, `design_utils.py` | Same fonts local and on RunPod if `fonts/` deployed |
| RunPod path in sys.path | `minimal_overlay.py` | design_config loads reliably on RunPod |
| **Only 5 overlays** | `content_generator.py`, `minimal_overlay.py` | No vintage overlay; no bottom-third gradient; no bar texture. Only: headline box + headline, Breaking News, AI Generated, Source, Unseen Economy logo |
| No text in image | `runpod_image.py`, `runpod_image_server.py` | Negative prompt and guidance_scale 3.5; optional REMOVE_TEXT_FROM_IMAGE plus opencv/easyocr to inpaint text before overlay |
| RunPod deploy | `setup_runpod_full.py` | Deploys ai_label.py, text_removal.py, facebook_api.py and all overlay/image modules |
| Long captions | `content_generator.py`, `config.py` | OLLAMA_CAPTION_NUM_PREDICT=1024; expand if under 90 words; Gemini fallback when Ollama unavailable (e.g. RunPod with GEMINI_API_KEY) |

---

## 5. If something doesn’t work

- **RunPod still different from local:**  
  Redeploy so the pod has the latest `design_config.py`, `minimal_overlay.py`, and `fonts/` (run `download_fonts.py` locally first, then deploy).

- **Extra headline text still in image after redeploy:** Redeploy from the folder with latest code (`python setup_runpod_full.py`). On the pod run `pip install -r requirements.txt` for opencv/easyocr. Check logs for "Removed text from image" or "Text removal skipped". The pipeline now strips title words from the prompt and has an OpenCV-only fallback to remove bright text regions.

- **Design schema error again:**  
  Ensure `design_agent.py` on the pod is the one that checks for API key before calling Gemini (and tries Ollama when no key).

- **Headline still duplicated:**  
  Ensure only one overlay runs (minimal **or** sensational) and that `vintage_headline = None` when minimal was applied (in `content_generator.py`).

- **Headline still incomplete:**  
  Check `design_config.py`: MODERN_HEADLINE_MAX_WORDS = 20, and in `minimal_overlay.py` the modern block uses `min_size=10` and caps to 2 lines with ellipsis.

You don’t need to re-implement code; just run/deploy as above and the changes will be active.
