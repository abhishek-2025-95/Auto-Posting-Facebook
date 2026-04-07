@echo off
REM Right-click -> Run as administrator (once). Registers logon task for image poster + inbound watcher.
cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
  echo Requesting Administrator...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Register-FacebookImageAutomationLogonTask.ps1" -ProjectRoot "%~dp0."
if %errorLevel% neq 0 (
  echo Failed to register task.
  pause
  exit /b 1
)
echo.
pause
