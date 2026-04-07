# PowerShell script for Windows Task Scheduler
# This script runs the automation system

# Set the working directory
$ScriptDir = "C:\Users\user\Documents\Auto Posting Facebook"
Set-Location $ScriptDir

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

# Run the monetization-optimized automation system
Write-Host "Starting MONETIZATION-OPTIMIZED Facebook Automation System..."
Write-Host "Features: Maximum USA reach, easy monetization, peak engagement times"
Write-Host "Time: $(Get-Date)"
Write-Host "Directory: $ScriptDir"

try {
    python monetization_optimized_schedule.py
    Write-Host "Monetization-optimized automation completed successfully"
} catch {
    Write-Host "Error running monetization automation: $_"
    exit 1
}
