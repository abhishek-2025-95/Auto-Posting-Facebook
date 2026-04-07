param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("post-text", "post-link", "post-image", "post-image-url", "post-from-folder", "post-from-calendar", "run-scheduler")]
    [string]$Command,

    [string]$Message,
    [string]$Url,
    [string]$Path,
    [string]$Caption,
    [string]$Directory,
    [string]$CaptionSource = "filename",
    [string[]]$Pattern,
    [int]$Limit,
    [string]$Prefix,
    [string]$Suffix,
    [string]$CalendarPath,
    [switch]$DryRun,
    [int]$Interval = 60,
    [string]$EnvPath = ".env"
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvActivate = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}

switch ($Command) {
    "post-text" { python "$projectRoot\cli.py" --env $EnvPath post-text "$Message" }
    "post-link" { python "$projectRoot\cli.py" --env $EnvPath post-link "$Url" --message "$Message" }
    "post-image" { python "$projectRoot\cli.py" --env $EnvPath post-image "$Path" --caption "$Caption" }
    "post-image-url" { python "$projectRoot\cli.py" --env $EnvPath post-image-url "$Url" --caption "$Caption" }
    "post-from-folder" {
        $args = @("$projectRoot\cli.py", "--env", $EnvPath, "post-from-folder", $Directory, "--caption-source", $CaptionSource)
        if ($Pattern) { foreach ($p in $Pattern) { $args += @("--pattern", $p) } }
        if ($Limit) { $args += @("--limit", $Limit) }
        if ($Prefix) { $args += @("--prefix", $Prefix) }
        if ($Suffix) { $args += @("--suffix", $Suffix) }
        python @args
    }
    "post-from-calendar" {
        $calPath = if ($CalendarPath) { $CalendarPath } else { $Path }
        if (-not $calPath) { Write-Error "post-from-calendar requires -CalendarPath or -Path (e.g. calendar.csv)"; exit 1 }
        $args = @("$projectRoot\cli.py", "--env", $EnvPath, "post-from-calendar", $calPath)
        if ($DryRun) { $args += "--dry-run" }
        python @args
    }
    "run-scheduler" {
        $calPath = if ($CalendarPath) { $CalendarPath } else { $Path }
        if (-not $calPath) { Write-Error "run-scheduler requires -CalendarPath or -Path (e.g. calendar.csv)"; exit 1 }
        $args = @("$projectRoot\cli.py", "--env", $EnvPath, "run-scheduler", $calPath, "--interval", $Interval)
        if ($DryRun) { $args += "--dry-run" }
        python @args
    }
}
