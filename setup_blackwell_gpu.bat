@echo off
REM Automated: nightly PyTorch cu128 + .env flags for RTX 50 / Blackwell (sm_120)
cd /d "%~dp0"
echo.
echo === Blackwell / RTX 50 GPU setup (Auto Posting Facebook) ===
echo If .venv exists, PyTorch is installed there (same as typical run_continuous_posts).
echo.
python scripts\setup_blackwell_gpu.py
if errorlevel 1 pause
exit /b %errorlevel%
