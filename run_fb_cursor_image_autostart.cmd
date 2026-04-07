@echo off
REM Opens a dedicated console: first post ASAP, then US/ET schedule (same as run_continuous_image_posts_scheduled.cmd).
REM Use Task Scheduler with run_continuous_image_posts_scheduled.cmd directly, or this for a visible window on double-click.
cd /d "%~dp0"
start "Facebook Cursor-image posts" /D "%~dp0" cmd /k "%~dp0run_continuous_image_posts_scheduled.cmd"
exit /b 0
