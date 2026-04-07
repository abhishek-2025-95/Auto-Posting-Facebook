@echo off
REM One-shot health check: Python compile + schedule tests + Task Scheduler task.
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo ERROR: .venv not found. Create venv and pip install -r requirements.txt
  exit /b 1
)
echo === py_compile ===
"%PY%" -m py_compile run_continuous_posts.py posting_schedule.py config.py protobuf_runtime_shim.py content_generator.py runpod_image.py windows_zimage_safetensors_patch.py blackwell_diagnostics.py facebook_api.py minimal_overlay.py news_fetcher.py reddit_news_fetcher.py google_news_fetcher.py reputed_rss_fetcher.py enhanced_news_diversity.py
if errorlevel 1 exit /b 1
echo === verify_windows_stability ===
"%PY%" scripts\verify_windows_stability.py
if errorlevel 1 exit /b 1
echo === test_news_markets_filter ===
"%PY%" tests\test_news_markets_filter.py
if errorlevel 1 exit /b 1
echo === test_breaking_reputed_filter ===
"%PY%" tests\test_breaking_reputed_filter.py
if errorlevel 1 exit /b 1
echo === test_posting_schedule ===
"%PY%" tests\test_posting_schedule.py
if errorlevel 1 exit /b 1
echo === test_posting_schedule_ist ===
"%PY%" tests\test_posting_schedule_ist.py
if errorlevel 1 exit /b 1
echo === import run_continuous_posts ===
"%PY%" -c "import run_continuous_posts; print('OK')"
if errorlevel 1 exit /b 1
echo === Task Scheduler: Facebook Auto Posting 645 ===
schtasks.exe /Query /TN "Facebook Auto Posting 645" /FO LIST 2>nul
if errorlevel 1 (
  echo WARNING: Task not found. Run setup_windows_task_admin.cmd as Administrator once.
  exit /b 1
)
echo.
echo verify_setup.cmd: ALL OK
exit /b 0
