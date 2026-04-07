# Copy this workflow to a separate Cursor project

Use this in a **new Cursor project folder** to get the same pipeline (news → caption → image → overlay → post to Facebook).

---

## Option A: Copy the whole project (easiest)

**From your current project folder** (e.g. `Auto Posting Facebook`), copy everything **except** `.venv`, `__pycache__`, `.git`, and `.env` (so you don’t leak secrets).

### PowerShell (run in the folder that contains “Auto Posting Facebook”)

```powershell
$src = "C:\Users\user\Documents\Auto Posting Facebook"
$dst = "C:\Users\user\Documents\MyIndiaNewsPage"
New-Item -ItemType Directory -Path $dst -Force
Get-ChildItem $src -Force | Where-Object { $_.Name -notin @('.venv','__pycache__','.git','.env') } | ForEach-Object { Copy-Item $_.FullName -Destination $dst -Recurse -Force }
```

Replace `$src` and `$dst` with your actual paths.

### Command Prompt (xcopy)

```cmd
xcopy "C:\Users\user\Documents\Auto Posting Facebook\*" "C:\Users\user\Documents\MyIndiaNewsPage\" /E /I /H /EXCLUDE:exclude.txt
```

Create `exclude.txt` in the current folder with:

```
\.venv\
\__pycache__\
\.git\
\.env
```

---

## Option B: Copy only the files needed for the workflow

Create the new project folder and copy **only** these files and folders.

### Folders to copy (entire folder)

- `assets` (logos used in overlay)
- `fonts` (optional; for custom headline font)

### Files to copy (root of project)

```
config.py
content_generator.py
facebook_api.py
run_continuous_posts.py
run_india_page.py
enhanced_news_diversity.py
news_fetcher.py
reputed_rss_fetcher.py
minimal_overlay.py
design_config.py
design_utils.py
design_agent.py
text_removal.py
ai_label.py
ollama_client.py
runpod_image.py
start_runpod.py
runpod_image_server.py
sensational_overlay.py
vintage_newspaper.py
requirements.txt
.env.example
.env.india.example
MULTI_PAGE_INDIA.md
```

### PowerShell (minimal copy)

```powershell
$src = "C:\Users\user\Documents\Auto Posting Facebook"
$dst = "C:\Users\user\Documents\MyIndiaNewsPage"
$files = @(
  "config.py","content_generator.py","facebook_api.py","run_continuous_posts.py","run_india_page.py",
  "enhanced_news_diversity.py","news_fetcher.py","reputed_rss_fetcher.py","minimal_overlay.py",
  "design_config.py","design_utils.py","design_agent.py","text_removal.py","ai_label.py",
  "ollama_client.py","runpod_image.py","start_runpod.py","runpod_image_server.py",
  "sensational_overlay.py","vintage_newspaper.py","requirements.txt",".env.example",".env.india.example","MULTI_PAGE_INDIA.md"
)
New-Item -ItemType Directory -Path $dst -Force
foreach ($f in $files) { Copy-Item "$src\$f" "$dst\" -Force -ErrorAction SilentlyContinue }
Copy-Item "$src\assets" "$dst\assets" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item "$src\fonts" "$dst\fonts" -Recurse -Force -ErrorAction SilentlyContinue
```

Replace `$src` and `$dst` with your paths.

---

## In the NEW project (after copy)

1. **Open the new folder in Cursor** (File → Open Folder → select `MyIndiaNewsPage` or your folder).

2. **Create `.env`** (never commit this):
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` and set:
   - `NEWS_API_KEY` (newsdata.io)
   - `GEMINI_API_KEY` (optional, for caption fallback)
   - `PAGE_ID` = your Facebook page ID  
   - `PAGE_ACCESS_TOKEN` = your page access token  

3. **For India-only page**, also create `.env.india` from the example:
   ```powershell
   copy .env.india.example .env.india
   ```
   Set India page `PAGE_ID`, `PAGE_ACCESS_TOKEN`, and e.g. `NEWS_COUNTRIES=in`, `TOPIC_THEME=India and South Asian news`, `POSTED_ARTICLES_FILE=posted_articles_india.json`.

4. **Install dependencies** (no venv):
   ```powershell
   pip install -r requirements.txt
   ```
   Or with venv:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. **Run**
   - Main page: `python run_continuous_posts.py`
   - India page: `python run_india_page.py`

6. **Optional (CPU only):** In `.env` set `IMGEN_FEB_DEVICE=cpu`.

---

## One-time: tokenizers (if you see tokenizers error)

```powershell
pip install "tokenizers>=0.22.0,<=0.23.0" "transformers>=4.52.0"
```

---

## Summary

| Goal              | Copy                    | Run                      |
|-------------------|-------------------------|--------------------------|
| Same workflow     | Option A or B            | `python run_continuous_posts.py` |
| India-only page   | Same + `.env.india`      | `python run_india_page.py`       |

After copy, the new Cursor project has the same pipeline; only `.env` (and optionally `.env.india`) need your keys and page settings.
