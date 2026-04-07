# Copy workflow to new project — India-only page

Use this in a **new Cursor project** that will run **only** your India Facebook page (India news, one page, same pipeline).

---

## Step 1: Copy the project (PowerShell)

Run in PowerShell. Change `$dst` to your new project path.

```powershell
$src = "C:\Users\user\Documents\Auto Posting Facebook"
$dst = "C:\Users\user\Documents\IndiaNewsPage"
New-Item -ItemType Directory -Path $dst -Force
Get-ChildItem $src -Force | Where-Object { $_.Name -notin @('.venv','__pycache__','.git','.env') } | ForEach-Object { Copy-Item $_.FullName -Destination $dst -Recurse -Force }
```

---

## Step 2: Open the new folder in Cursor

File → Open Folder → select `IndiaNewsPage` (or whatever you used for `$dst`).

---

## Step 3: Create `.env` (India page only)

In the new project root, create a file named `.env` with:

```env
# India page credentials
PAGE_ID=your_india_page_id
PAGE_ACCESS_TOKEN=your_india_page_access_token

# India-only news
NEWS_COUNTRIES=in

# Caption theme for India/South Asia
TOPIC_THEME=India and South Asian news

# Shared keys (same as main project)
NEWS_API_KEY=your_newsdata_io_key
GEMINI_API_KEY=your_gemini_key_if_you_use_it
```

Replace `your_india_page_id`, `your_india_page_access_token`, and API keys with your real values.

---

## Step 4: Install and run

In the new project folder:

```powershell
pip install -r requirements.txt
python run_continuous_posts.py
```

Use **only** `run_continuous_posts.py`. It will use India news and your India page from `.env`.

---

## Optional: CPU-only image generation

If you don’t have a GPU or want to avoid GPU errors, add to `.env`:

```env
IMGEN_FEB_DEVICE=cpu
```

---

## Optional: tokenizers fix

If you see a tokenizers version error:

```powershell
pip install "tokenizers>=0.22.0,<=0.23.0" "transformers>=4.52.0"
```

---

## Summary

| Step | Action |
|------|--------|
| 1 | Copy project (PowerShell above), exclude `.venv`, `__pycache__`, `.git`, `.env` |
| 2 | Open new folder in Cursor |
| 3 | Create `.env` with India `PAGE_ID`, `PAGE_ACCESS_TOKEN`, `NEWS_COUNTRIES=in`, `TOPIC_THEME=...`, API keys |
| 4 | `pip install -r requirements.txt` then `python run_continuous_posts.py` |

No `.env.india` or `run_india_page.py` needed in the new project — it’s India-only by default.
