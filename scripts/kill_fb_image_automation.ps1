# Stop Python processes for this project: image poster + inbound auto-bridge (+ legacy watcher)
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)
$ErrorActionPreference = 'SilentlyContinue'
try {
    $root = (Resolve-Path -LiteralPath $ProjectRoot).Path.TrimEnd('\')
} catch {
    exit 0
}
$procs = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and
    $_.CommandLine -and
    (
        ($_.CommandLine -like '*run_continuous_image_posts.py*') -or
        ($_.CommandLine -like '*cursor_inbound_watcher.py*') -or
        ($_.CommandLine -like '*cursor_inbound_auto_bridge.py*')
    ) -and
    ($_.CommandLine -like "*${root}*" -or $_.CommandLine -like "*$( $root.Replace('\', '/') )*")
}
foreach ($p in $procs) {
    Write-Host "Stopping FB image automation (PID $($p.ProcessId))..."
    Stop-Process -Id $p.ProcessId -Force
}
exit 0
