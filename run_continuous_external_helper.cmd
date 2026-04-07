@echo off
REM Used by run_local.cmd / restart_continuous_external.cmd — same env as run_continuous_in_this_window.cmd (no pause).
cd /d "%~dp0"
call "%~dp0windows_imgen_stable_env.cmd"
".venv\Scripts\python.exe" -u run_continuous_posts.py
