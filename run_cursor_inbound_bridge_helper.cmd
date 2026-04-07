@echo off
REM Minimized sidecar for run_continuous_image_posts_scheduled.cmd — Cursor API / editor focus for inbound PNG.
cd /d "%~dp0"
if exist "%~dp0windows_imgen_stable_env.cmd" call "%~dp0windows_imgen_stable_env.cmd"
".venv\Scripts\python.exe" -u "%~dp0scripts\cursor_inbound_auto_bridge.py"
