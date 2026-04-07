@echo off
REM Run continuous cycle in THIS window (good for copy-paste or "cmd /c run_continuous_in_this_window.cmd")
cd /d "%~dp0"
call "%~dp0windows_imgen_stable_env.cmd"
".venv\Scripts\python.exe" -u run_continuous_posts.py
echo.
pause
