#Requires -Version 5.1
<#
  Registers a Task Scheduler job at user logon that runs run_continuous_image_posts_scheduled.cmd
  (first post ASAP via SKIP_US_ET_WAIT_FIRST_IMAGE_POST, then US/ET slots; Cursor image tool for stills).

  Run elevated once: setup_windows_task_image_logon_admin.cmd
#>
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ProjectRoot = $ProjectRoot.Trim().Trim('"').TrimEnd('\', '/')
if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
}

$launcher = Join-Path $ProjectRoot "run_continuous_image_posts_scheduled.cmd"
if (-not (Test-Path $launcher)) {
    Write-Error "Not found: $launcher"
    exit 1
}

$taskName = "Facebook Image Auto Posting (logon)"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/k `"$launcher`"" -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances StopExisting
$principal = New-ScheduledTaskPrincipal -LogonType Interactive -UserId $env:USERNAME

try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "OK: Registered '$taskName' at logon for $env:USERNAME."
    Write-Host "    Launcher: $launcher"
    Write-Host "    Keep PC awake / disable sleep for overnight slots (Power & sleep settings)."
} catch {
    Write-Error $_
    exit 1
}
