# Stop any Python process running this project's run_continuous_posts.py (for clean restart).
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
    $_.CommandLine -like '*run_continuous_posts.py*' -and
    ($_.CommandLine -like "*${root}*" -or $_.CommandLine -like "*$( $root.Replace('\', '/') )*")
}
foreach ($p in $procs) {
    Write-Host "Stopping previous continuous runner (PID $($p.ProcessId))..."
    Stop-Process -Id $p.ProcessId -Force
}
exit 0
