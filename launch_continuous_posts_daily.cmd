@echo off
REM Task Scheduler / daily: always use the latest files in THIS folder — stop any prior
REM continuous runner (old in-memory Python), then open a new window like run_local.cmd.
cd /d "%~dp0"
call "%~dp0restart_continuous_external.cmd"
