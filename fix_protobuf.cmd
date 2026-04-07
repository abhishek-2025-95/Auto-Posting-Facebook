@echo off
REM Fix: cannot import name 'runtime_version' from 'google.protobuf'
REM Run this if image generation fails with that error. Use a venv to avoid conflicts with TensorFlow etc.
echo Installing protobuf 3.x for diffusers compatibility...
pip install "protobuf>=3.20.0,<4.0.0" --force-reinstall
echo.
echo Done. Run: python run_continuous_posts.py
pause
