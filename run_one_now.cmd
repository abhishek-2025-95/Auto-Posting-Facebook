@echo off
REM One full workflow: news -> image (Z-Image) -> overlay -> Facebook, then exit.
REM Same env as continuous runner. Does NOT wait for ET windows (unlike first post in run_continuous_posts).
REM Optional: set SKIP_FB_DUP_CHECK=1 before running to bypass duplicate detection (test only).
cd /d "%~dp0"
call "%~dp0windows_imgen_stable_env.cmd"
if "%SKIP_FB_DUP_CHECK%"=="1" set CHECK_FACEBOOK_FOR_DUPLICATES=0
".venv\Scripts\python.exe" -u run_one_cycle.py
echo.
pause
