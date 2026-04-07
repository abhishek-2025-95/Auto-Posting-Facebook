# Agent instructions — Facebook **cursor_only** image pipeline

Use this file when running a **Cursor Background Agent**, **Automation**, or any scheduled agent on this repository.

## Goal

Produce **one** 4:5 vertical still for the current news story so the Python daemon can finish the post. **No Z-Image / no local diffusion** — only the Cursor **image** tool (or equivalent in your agent session).

## Repository policy (enforced in code)

`config.py` **locks** `IMAGE_GENERATION_MODE` to Cursor-only for Facebook post stills and **disables** all PIL/API placeholder paths. Do not add scripted image fallbacks or re-enable Z-Image for this pipeline without an explicit product decision.

## Paths (relative to repo root)

| Role | Path |
|------|------|
| Read this first | `CURSOR_POST_IMAGE_PROMPT.txt` |
| Write the bitmap here (overwrite) | `cursor_post_image.png` |

The prompt file contains the **exact absolute path** on disk under the line *“Save the file to this exact path”* — use that path if it differs from `cursor_post_image.png`.

## Every run — do this in order

1. Open and read **`CURSOR_POST_IMAGE_PROMPT.txt`** completely (article block + image prompt).
2. If it says **scene only (no on-image headline)** / no chyron: generate a **photoreal 4:5** still **without** headline, ticker, or lower-third text.
3. Use the **image generation tool** to create **one** image matching the prompt and aspect ratio (**4:5 portrait**).
4. **Save** the result to the path specified in the bundle (default: repo root **`cursor_post_image.png`**, PNG or JPEG as allowed there).
5. Do not rename the story file; only replace the inbound image file.

## Coordination with Python

- **`run_continuous_image_posts.py`** (or `scripts/agent_post_one_cursor.py finish`) expects the inbound file **after** it writes/updates the prompt.
- In **`.env`**, set **`CURSOR_INBOUND_MAX_WAIT_SECONDS`** to at least **600** (10 minutes) so the daemon **waits** for this agent to drop the file inside each posting attempt.

## Fully automatic operation (PC + Cursor)

1. **Windows**: Run **`run_continuous_image_posts_scheduled.cmd`** at logon (Task Scheduler → `setup_windows_task_image_logon_admin.cmd`) or double-click **`run_fb_cursor_image_autostart.cmd`**. It starts a minimized **auto-bridge** (`scripts/cursor_inbound_auto_bridge.py`) plus the poster. The first post **does not wait** for the next ET slot; later posts follow **`posting_schedule.py`**.
2. **Images (choose one)**  
   - **A — Cursor Background Agents API (hands-free):** In **`.env`**, set **`CURSOR_API_KEY`** (Cursor Dashboard → Integrations), **`CURSOR_BACKGROUND_AGENT_AUTO=1`**, and **`CURSOR_BACKGROUND_AGENT_REPO=https://github.com/ORG/REPO`** (or use a **`git remote origin`** on GitHub). The bridge launches an agent per prompt change and downloads the committed PNG from the agent branch. No Z-Image/PIL.  
   - **B — Cursor dashboard Automation:** Schedule an automation using **`scripts/cursor_automation_agent_instructions.txt`**.  
   - **C — Semi-auto:** With no API vars, the bridge defaults to **focus** mode: it opens **`CURSOR_POST_IMAGE_PROMPT.txt`** in Cursor so you can run the image tool quickly.

## Cursor Automations (dashboard)

Automations are created in the **Cursor** product UI (Cloud agent / Automations), not only via files in this repo.

1. **New automation** → connect **this repository**.
2. **Trigger**: **Schedule** (cron). Align with your posting windows if you like (e.g. a few runs per day inside US/Eastern 7–9, 12–1, 19–22), or use a modest interval during those windows only (your choice).
3. **Optional trigger**: If your plan supports **file / commit** triggers, prefer **when `CURSOR_POST_IMAGE_PROMPT.txt` changes** so you only generate when the daemon refreshes the prompt.
4. **Task / instructions**: Paste the contents of **`scripts/cursor_automation_agent_instructions.txt`**, or: *“Follow `AGENTS.md` for the Facebook cursor-only image inbound task.”*
5. Ensure the automation runs with **write access** to the repo workspace so **`cursor_post_image.png`** can be created or overwritten.

## Failure handling

- If the prompt file is missing, **do nothing** (the news daemon may be idle).
- If generation fails, **do not** create a placeholder; the Python side will retry on the next cycle.
