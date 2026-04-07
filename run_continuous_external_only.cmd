@echo off
REM Open a NEW window with continuous posting WITHOUT stopping an existing instance.
REM If one is already running, the new window will exit immediately (single-instance lock).
cd /d "%~dp0"
start "Facebook Auto Posting" /D "%~dp0" cmd /k "%~dp0run_continuous_external_helper.cmd"
