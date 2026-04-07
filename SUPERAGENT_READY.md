# Project status — Auto Posting Facebook

This file is the **single checklist** for “everything is wired.” Re-run **`verify_setup.cmd`** anytime to confirm Python + tests + **Facebook Auto Posting 645** task.

## What’s already done in code

| Item | Status |
|------|--------|
| US Eastern (EST/EDT via `America/New_York`) + daily cap | `posting_schedule.py` + `config.py` (omit `POSTING_SCHEDULE_TIMEZONE` for US) |
| Morning flood + lunch/evening slots | `.env`: `POSTING_SCHEDULE_FLOOD_WINDOWS=morning` |
| First comment + article URL | `run_continuous_posts.py` + `NEWS_LINK_IN_FIRST_COMMENT` |
| Long-lived Page token flow | `ensure_long_lived_token.py --write-env` |
| Token / Page connection check | `check_page_token_comments.py` |
| External CMD launcher | **`run_local.cmd`** / **`restart_continuous_external.cmd`** (kill prior runner → new window), **`launch_continuous_posts_daily.cmd`** (Task Scheduler — same restart so latest files load daily), **`run_continuous_external_only.cmd`** (no kill), **`windows_imgen_stable_env.cmd`** (shared env) |
| Task Scheduler guide + XML | `TASK_SCHEDULER_645_ET.md`, `TaskScheduler_FacebookPosting_645.xml` |
| One-click task registration (admin) | **`setup_windows_task_admin.cmd`** (default **6:45 AM** local) or **`setup_windows_task_415pm_ist.cmd`** (**4:15 PM** IST for India PC + US Eastern windows) |
| Cursor/VS Code tasks | `.vscode/tasks.json` → **Terminal → Run Task…** |
| Full verify (compile + news filter + tests + task + Windows clamp test) | Double-click **`verify_setup.cmd`** or task **Facebook: Full verify…** (`scripts/verify_windows_stability.py`) |

## What only you can do on the PC (one-time)

1. **Task Scheduler** — Registers **6:45 AM** on the PC clock. For **US Eastern posting**, set the trigger to **6:45 AM US Eastern** (Eastern PC), or convert from ET (`TASK_SCHEDULER_645_ET.md`). **`setup_windows_task_admin.cmd`** (Run as administrator) or manual steps there.

2. **`.env`** — Keep `PAGE_ID`, `PAGE_ACCESS_TOKEN`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` current. **Never commit `.env`.**

3. **Ollama** — Running locally if you use it for captions/prompts (`ollama serve`).

## Quick commands (Command Prompt)

```cmd
cd /d "C:\Users\user\Documents\Auto Posting Facebook"
run_local.cmd
```

```cmd
cd /d "C:\Users\user\Documents\Auto Posting Facebook"
.venv\Scripts\activate.bat
python check_page_token_comments.py
python tests\test_posting_schedule.py
```

## From Cursor

- **Terminal → Run Task…** → **Facebook: Open external terminal (continuous posting)**  
- Or double-click **`run_local.cmd`** in File Explorer.

## Security reminder

Rotate **Page token** and **App Secret** if they were ever pasted in chat or logs.
