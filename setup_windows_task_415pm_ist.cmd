@echo off

REM Daily launch at 4:15 PM on THIS PC's clock.

REM When Windows is set to India (IST), this is 4:15 PM IST ~ aligns with ~6:45 AM US Eastern during EDT.

REM Right-click -> Run as administrator (once).

cd /d "%~dp0"

call "%~dp0setup_windows_task_admin.cmd" 4:15PM


