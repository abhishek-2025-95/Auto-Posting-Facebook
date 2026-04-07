@echo off
REM Task Scheduler / "start in folder" helper: same env as run_continuous_in_this_window.cmd
cd /d "%~dp0"
call "%~dp0windows_imgen_stable_env.cmd"
".venv\Scripts\python.exe" -u run_continuous_posts.py
