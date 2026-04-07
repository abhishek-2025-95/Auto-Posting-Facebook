@echo off
setlocal
REM Kill any previous run_continuous_posts.py for THIS folder, remove stale lock, open a NEW cmd window.
REM Default way to "restart" the pipeline with fresh code (caption fixes, config, etc.).
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo [restart] Stopping any previous continuous runner for this project...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\kill_continuous_runner.ps1" "%ROOT%"
if exist "%ROOT%.run_continuous_posts.lock" (
  for /f "usebackq delims=" %%p in ("%ROOT%.run_continuous_posts.lock") do (
    echo [restart] Lock file PID %%p — forcing taskkill / tree...
    taskkill /PID %%p /T /F >nul 2>&1
  )
  del /f /q "%ROOT%.run_continuous_posts.lock" >nul 2>&1
)

REM ~1s delay without timeout.exe (fails in non-interactive / redirected stdin)
ping 127.0.0.1 -n 2 >nul
echo [restart] Starting new window: Facebook Auto Posting
start "Facebook Auto Posting" /D "%ROOT%" cmd /k "%ROOT%run_continuous_external_helper.cmd"
endlocal
