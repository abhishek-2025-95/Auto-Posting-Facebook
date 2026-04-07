@echo off
REM Fix "cannot import name 'message' from 'google.protobuf'" and similar protobuf errors.
REM Run this from the project folder, then run run_continuous_posts.py with the SAME venv.

cd /d "%~dp0"

if exist ".venv\Scripts\pip.exe" (
    echo Reinstalling protobuf in project venv...
    .venv\Scripts\pip install --force-reinstall "protobuf==3.20.3"
    echo Done. Run: .venv\Scripts\activate.bat then python run_continuous_posts.py
) else (
    echo No .venv found. Reinstalling protobuf in current Python...
    pip install --force-reinstall "protobuf==3.20.3"
    echo Done. Run: python run_continuous_posts.py
)
pause
