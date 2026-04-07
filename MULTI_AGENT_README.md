# Multi-Agent: Multiple Pages with Different Themes

Run one content cycle for **multiple Facebook pages** at once, each with its own **theme** and **persona**. All sectors run in parallel.

## Setup

1. **Copy the example config**
   - Copy `sectors.example.json` to `sectors.json`.
   - Do not commit `sectors.json` (it contains tokens); it is in `.gitignore`.

2. **Edit `sectors.json`** (or `config.json`)
   - One object per page. Each needs: `sector`, `theme`, `page_id`, `token`. Optional: `system_prompt` (persona), `tone`, `hashtag_focus`, `visual_style` to shape content and visuals per page.
   - **Content and theme:** See **[CONTENT_AND_THEME.md](CONTENT_AND_THEME.md)** for how to set persona, theme, tone, hashtags, and image style so each page gets on-brand content.

3. **Shared config**
   - `.env` / `config.py`: Gemini, News API, Ollama, etc. are shared by all sectors. Only Facebook page and persona/theme are per-sector in `sectors.json`.

## Run

**One cycle for all sectors in parallel:**
```bash
python orchestrator.py
```

**Only page 1 (first sector) — e.g. to focus on one page first:**
```bash
python orchestrator.py --page 1
```
Use `--page 2`, `--page 3`, etc. to run only that sector (1-based).

**Single-sector test (one config in a JSON file):**
```bash
set SECTOR_CONFIG_JSON=path\to\one_sector.json
python worker_cycle.py
```

## Flow

- **Orchestrator** (`orchestrator.py`): loads `sectors.json`, runs one **worker** per sector in a separate process (so image generation and temp files don’t clash).
- **Worker** (`worker_cycle.py`): for one sector: fetch viral news → generate caption and image prompt (using that sector’s `system_prompt` and `theme`) → generate image → post to that sector’s `page_id` with its `token`.

Existing single-page flow is unchanged: `run_continuous_posts.py` and `main.py` still use `config.py` / `.env` for one page.
