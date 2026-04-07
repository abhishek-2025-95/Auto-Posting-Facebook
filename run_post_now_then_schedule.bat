@echo off
cd /d "%~dp0"
call "%~dp0windows_imgen_stable_env.cmd"
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Create .venv first: python -m venv .venv
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "test_image_post_then_schedule.py" %*
set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% neq 0 (
    echo.
    echo Script stopped with exit code %EXIT_CODE%. If it stopped during "Loading pipeline components", often OOM or CUDA crash. Try IMGEN_FEB_SIZE=512 in config.py or close other apps.
    pause
)
