@echo off
REM By default: stops any previous continuous runner for this project, then opens a NEW window.
REM Same .venv + env as run_continuous_in_this_window.cmd. Ctrl+C stops python; window stays open (cmd /k).
REM To start WITHOUT killing a previous instance: run run_continuous_external_only.cmd
REM If you see "paging file is too small" (Win error 1455) while loading Z-Image:
REM   System > Advanced > Performance > Virtual memory: Custom 32768-65536 MB, reboot.
call "%~dp0restart_continuous_external.cmd"
