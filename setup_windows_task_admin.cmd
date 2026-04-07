@echo off

setlocal EnableDelayedExpansion

REM Right-click -> Run as administrator (once).

REM Optional: pass local launch time (default 6:45 AM). Example for India PC ~ US morning EDT: 4:15PM

REM   setup_windows_task_admin.cmd 4:15PM

REM Or double-click: setup_windows_task_415pm_ist.cmd



cd /d "%~dp0"



if "%~1"=="" (set "LT=6:45AM") else (set "LT=%~1")



net session >nul 2>&1

if %errorLevel% neq 0 (

  echo Requesting Administrator...

  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -ArgumentList '%LT%'"

  exit /b 0

)



REM Use %~dp0. not %~dp0 — trailing \ before " breaks CMD quoting (path gets a stray ").

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Register-FacebookPostingTask.ps1" -ProjectRoot "%~dp0." -LaunchTime "!LT!"

if %errorLevel% neq 0 (

  echo Failed. See TASK_SCHEDULER_645_ET.md for manual steps.

  pause

  exit /b 1

)

echo.

pause


