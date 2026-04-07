@echo off
cd /d "%~dp0"
echo Generating updated sample image (Breaking News + headline bar + AI label)...
"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" sample_overlay_current_news.py
if %ERRORLEVEL% equ 0 (
    echo.
    echo Done. Opening: sample_overlay_preview.jpg
    start "" "sample_overlay_preview.jpg"
) else (
    echo Script failed. Check errors above.
    pause
)
