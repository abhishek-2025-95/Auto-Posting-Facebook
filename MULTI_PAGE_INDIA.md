# Running the same workflow for an India-focused page

You can run the **exact same pipeline** (news → caption → image → overlay → post) for a **second Facebook page** that focuses on **news from India**, without duplicating the codebase.

## How it works

- **One codebase.** The same scripts, overlay, and image generation run for both pages.
- **Page-specific settings** come from a second env file (`.env.india`) that overrides only what’s needed for the India page: page credentials, news countries, and optional theme.
- **Separate posting history.** The India page uses its own `posted_articles_india.json` so it doesn’t treat the main page’s posts as “already posted.”

## Setup (India page)

1. **Create the India page env file**
   - Copy `.env.india.example` to `.env.india`.
   - Edit `.env.india` and set:
     - `PAGE_ID` = your **India page’s** Facebook Page ID.
     - `PAGE_ACCESS_TOKEN` = your **India page’s** Page Access Token (long-lived).
     - `NEWS_COUNTRIES=in` (India-only news from newsdata.io).
     - Optionally: `TOPIC_THEME=India and South Asian news` so captions are tailored.
     - Optionally: `POSTED_ARTICLES_FILE=posted_articles_india.json` (this is already in the example).

2. **Keep your main `.env`**
   - `.env` should still have `NEWS_API_KEY`, `GEMINI_API_KEY`, and any shared keys (Ollama, RunPod, etc.).  
   - Your **main page** credentials can stay in `.env` for the default runner.

3. **Get India page token**
   - Use the same flow as the main page (Graph API Explorer or your token script), but select the **India page** and get a Page Access Token for that page.  
   - Put that token (and the India page’s ID) only in `.env.india`.

## Run the India page

From the project root:

```bash
python run_india_page.py
```

- This loads `.env` first, then `.env.india`, so India page credentials and `NEWS_COUNTRIES=in` override where needed.
- It then runs the same continuous loop as `run_continuous_posts.py`, but posting to the India page and using India-only news (and optional India theme in captions).

## Run both pages

- **Main page:** `python run_continuous_posts.py` (uses `.env` only, or `.env` + `ENV_FILE` if you set it).
- **India page:** `python run_india_page.py` (uses `.env` + `.env.india`).

Run them in two terminals, or on two machines/RunPods. Each keeps its own `posted_articles*.json` so they don’t conflict.

## Optional env (in `.env.india`)

| Variable | Example | Purpose |
|----------|---------|--------|
| `NEWS_COUNTRIES` | `in` or `in,pk,bd` | News from India (and optionally neighbours). |
| `TOPIC_THEME` | `India and South Asian news` | Ties captions to India/South Asia. |
| `POSTED_ARTICLES_FILE` | `posted_articles_india.json` | Separate history for the India page. |
| `NEWS_LANGUAGE` | `en` | Keep `en` for English headlines, or use another code if you add support. |

## Adding more pages

To add a third page (e.g. UK-only):

1. Copy `.env.india.example` to `.env.uk` (or similar).
2. Set `PAGE_ID`, `PAGE_ACCESS_TOKEN`, `NEWS_COUNTRIES=gb`, `TOPIC_THEME=UK news`, `POSTED_ARTICLES_FILE=posted_articles_uk.json`.
3. Duplicate `run_india_page.py` to `run_uk_page.py` and change `.env.india` to `.env.uk` (or use a single runner that takes the env file name from a command-line argument).

The same workflow (captions, images, overlay, first comment, etc.) runs for every page; only env and posting history change.
