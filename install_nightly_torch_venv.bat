@echo off
REM Fix "no kernel image" on RTX 50: install PyTorch nightly INTO .venv (same Python as run_continuous_posts).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo No .venv found. Create:  python -m venv .venv
  echo Then:  .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
echo Installing nightly cu128 torch into .venv ...
".venv\Scripts\python.exe" -m pip install --upgrade --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
if errorlevel 1 pause & exit /b 1
echo.
".venv\Scripts\python.exe" check_gpu.py
pause
