# Task Scheduler: daily 6:45 AM (≈15 min before 7:00 AM ET)

The script waits for **US Eastern** windows inside Python. With **`POSTING_SCHEDULE_FLOOD_WINDOWS=morning`** in `.env`, posting can start at **7:00 AM ET**. Launch at **6:45 AM Eastern** (or your local equivalent) so the PC has time to load the model.

---

## Automated setup (recommended)

1. **US Eastern PC (6:45 AM local ≈ 6:45 AM ET):** Right-click **`setup_windows_task_admin.cmd`** → **Run as administrator** (once).  
2. **India PC (IST), US Eastern posting:** Right-click **`setup_windows_task_415pm_ist.cmd`** → **Run as administrator** (once).  
   Registers **`Facebook Auto Posting 645`** daily at **4:15 PM IST** (when Windows is set to India) — roughly **6:45 AM US Eastern** during **EDT**; adjust when US is on **EST** (see section below).  
3. **Custom time:** `setup_windows_task_admin.cmd 7:30AM` (or `4:15PM`, etc.) as administrator.

**Latest code on disk:** The task runs **`launch_continuous_posts_daily.cmd`**, which calls **`restart_continuous_external.cmd`** — it stops any previous `run_continuous_posts.py` for this folder, then starts a **new** window. Python always loads the current `*.py` / `.env` from the project directory (same as **`run_local.cmd`**). Re-run **setup** as administrator once if you registered an older task (so **StopExisting** and this launcher are applied).

---

## Quick setup (manual, US Eastern PC clock)

1. **Task Scheduler** → **Create Task…** (not Basic Task — you get more options).
2. **General:** Name e.g. `Facebook Auto Posting`; choose **Run only when user is logged on** if you want to **see** the external CMD window.
3. **Triggers** → **New…** → **Daily** → start **6:45:00 AM**, recur every **1** days → OK.
4. **Actions** → **New…** → **Start a program**
   - **Program/script:**  
     `C:\Users\user\Documents\Auto Posting Facebook\launch_continuous_posts_daily.cmd`
   - **Start in (optional):**  
     `C:\Users\user\Documents\Auto Posting Facebook`
5. **Conditions** (optional): Uncheck **Start the task only if the computer is on AC power** if you use a laptop on battery.
6. **Settings** (optional): Enable **Run task as soon as possible after a scheduled start is missed**.

---

## Same steps, copy-paste

| Field | Value |
|--------|--------|
| Trigger | Daily **6:45 AM** (your **local** time = **6:45 AM ET** if you are in the Eastern time zone) |
| Action → Program/script | `C:\Users\user\Documents\Auto Posting Facebook\launch_continuous_posts_daily.cmd` |
| Action → Start in | `C:\Users\user\Documents\Auto Posting Facebook` |

---

## Not on US Eastern time?

Task Scheduler uses **local** time. Convert **6:45 AM America/New_York** to your time zone (watch **DST**).

Examples (when ET is UTC−5): **6:45 AM ET** ≈ **5:45 AM CT** / **4:45 AM MT** / **3:45 AM PT**.

### PC in **India (IST)** — read this

- **Python (default):** Posting windows still follow **`America/New_York`** if you **do not** set `POSTING_SCHEDULE_TIMEZONE`. That is correct for a **US audience**; your PC being in India does not change those hours.
- **Task Scheduler:** The registered task runs at **6:45 AM in Windows local time**. If Windows is set to **India**, **6:45 AM = 6:45 AM IST**, which is **not** 6:45 AM US Eastern.
- **To launch ~15 minutes before 7:00 AM US Eastern** from India, set the trigger to the **IST equivalent of 6:45 AM New York** (changes when US is on EST vs EDT):
  - **US on EDT** (roughly Mar–Nov): **6:45 AM ET** ≈ **4:15 PM IST** same calendar date.
  - **US on EST** (roughly Nov–Mar): **6:45 AM ET** ≈ **5:15 PM IST** same calendar date.
  Double-check in [time zone converter](https://www.timeanddate.com/worldclock/converter.html) for the exact date.

**If you want posting windows on India local time** (7–9 / 12–1 / 7–10 **IST**), set in `.env`: **`POSTING_SCHEDULE_TIMEZONE=IST`** (or `Asia/Kolkata`). Then **6:45 AM** on an India clock **is** the right pre-window launch time.

---

## Optional: import a task (XML)

1. Edit **`TaskScheduler_FacebookPosting_645.xml`** if your folder is not the default path.
2. Task Scheduler → **Import Task…** → select the XML → name the task → OK.
3. Open the task → **Triggers** → set the start time to **6:45** in **your** local time (see above).

---

## Optional: `schtasks` (admin CMD)

Adjust `/TN` (task name) and paths if needed:

```cmd
schtasks /Create /TN "Facebook Auto Posting" /TR "C:\Users\user\Documents\Auto Posting Facebook\launch_continuous_posts_daily.cmd" /SC DAILY /ST 06:45 /RL HIGHEST /F
```

`/ST` is **local** time. Add `/RU` `/RP` if you need to run when not logged on (may not show the window).

---

## Notes

- **`launch_continuous_posts_daily.cmd`** opens an **external** Command Prompt (`start … cmd /k`) and runs **`run_continuous_scheduled.cmd`**, which **`call`s `windows_imgen_stable_env.cmd`** (same stable Z-Image flags as **`run_continuous_in_this_window.cmd`**).
- Close that window to stop posting.
- Ensure **`.env`** has `PAGE_ACCESS_TOKEN`, `PAGE_ID`, and (if you want) `POSTING_SCHEDULE_FLOOD_WINDOWS=morning`.
