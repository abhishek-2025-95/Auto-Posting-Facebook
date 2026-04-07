@echo off
REM Task Scheduler: set "Start in" to this folder. First post ASAP, then US/ET slots (Cursor inbound only).
cd /d "%~dp0"
if exist "%~dp0windows_imgen_stable_env.cmd" call "%~dp0windows_imgen_stable_env.cmd"
set SKIP_FACEBOOK_POST=0
set DRY_RUN=0
if not defined CURSOR_INBOUND_MAX_WAIT_SECONDS set CURSOR_INBOUND_MAX_WAIT_SECONDS=600
set SKIP_US_ET_WAIT_FIRST_IMAGE_POST=1
REM Sidecar: Cursor Background Agents API and/or open prompt in Cursor (see scripts/cursor_inbound_auto_bridge.py).
start "Cursor inbound auto-bridge" /MIN cmd /k "%~dp0run_cursor_inbound_bridge_helper.cmd"
".venv\Scripts\python.exe" -u run_continuous_image_posts.py
