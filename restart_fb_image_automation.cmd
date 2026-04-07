@echo off
setlocal
REM Clean restart: image poster only (Cursor image tool — no Z-Image sidecar).
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo [restart] Stopping FB image poster (and legacy watcher if any)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\kill_fb_image_automation.ps1" "%ROOT%"
if exist "%ROOT%.run_continuous_image_posts.lock" (
  for /f "usebackq delims=" %%p in ("%ROOT%.run_continuous_image_posts.lock") do (
    taskkill /PID %%p /T /F >nul 2>&1
  )
  del /f /q "%ROOT%.run_continuous_image_posts.lock" >nul 2>&1
)
if exist "%ROOT%.cursor_inbound_watcher.lock" (
  for /f "usebackq delims=" %%p in ("%ROOT%.cursor_inbound_watcher.lock") do (
    taskkill /PID %%p /T /F >nul 2>&1
  )
  del /f /q "%ROOT%.cursor_inbound_watcher.lock" >nul 2>&1
)
if exist "%ROOT%.cursor_inbound_auto_bridge.lock" del /f /q "%ROOT%.cursor_inbound_auto_bridge.lock" >nul 2>&1
ping 127.0.0.1 -n 2 >nul
echo [restart] Starting image poster...
start "Facebook Image Posts" /D "%ROOT%" cmd /k "%ROOT%run_continuous_image_posts_scheduled.cmd"
endlocal
