#Requires -Version 5.1
<#
  Registers a daily Task Scheduler job at a LOCAL time that runs launch_continuous_posts_daily.cmd
  (stops any prior runner for this project, then opens external CMD with latest code from disk).

  -LaunchTime examples: 6:45AM, 4:15PM (Windows local clock = IST if PC is set to India)

  Run elevated, or use setup_windows_task_admin.cmd [LaunchTime] (right-click -> Run as administrator).
#>
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$LaunchTime = "6:45AM"
)

# Strip stray quotes / trailing slashes (CMD "%~dp0" before closing " can inject a quote into the path)
$ProjectRoot = $ProjectRoot.Trim().Trim('"').TrimEnd('\', '/')
if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
}

if ([string]::IsNullOrWhiteSpace($LaunchTime)) {
    $LaunchTime = "6:45AM"
}

$launcher = Join-Path $ProjectRoot "launch_continuous_posts_daily.cmd"
if (-not (Test-Path $launcher)) {
    Write-Error "Not found: $launcher"
    exit 1
}

$taskName = "Facebook Auto Posting 645"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$launcher`"" -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $LaunchTime
# StopExisting: if a previous task run is still marked active, prefer a clean start (pairs with launcher that exits quickly).
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances StopExisting
$principal = New-ScheduledTaskPrincipal -LogonType Interactive -UserId $env:USERNAME

try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "OK: Registered task '$taskName' daily at $LaunchTime (this PC's local time)."
    Write-Host "    Launcher: $launcher"
    Write-Host "    See TASK_SCHEDULER_645_ET.md (India / US Eastern notes)."
} catch {
    Write-Error $_
    exit 1
}
