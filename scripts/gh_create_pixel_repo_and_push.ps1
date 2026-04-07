# Creates github.com/abhishekchd664-pixel/Auto-Posting from this folder and pushes main.
# Requires: gh auth login  →  GitHub account abhishekchd664-pixel (not abhishek-2025-95).
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$want = "abhishekchd664-pixel"
$login = (gh api user -q .login 2>$null).Trim()
if ($login -ne $want) {
    Write-Host "Current gh user: '$login'. Switch to pixel first:" -ForegroundColor Yellow
    Write-Host "  gh auth login" -ForegroundColor Gray
    Write-Host "Then re-run: powershell -ExecutionPolicy Bypass -File scripts\gh_create_pixel_repo_and_push.ps1" -ForegroundColor Gray
    exit 1
}

$exists = $false
gh repo view "$want/Auto-Posting" --json name 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { $exists = $true }

if ($exists) {
    git remote remove pixel 2>$null
    git remote add pixel "https://github.com/$want/Auto-Posting.git"
    git push -u pixel main
} else {
    git remote remove pixel 2>$null
    gh repo create Auto-Posting --public --source=. --remote=pixel --push
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$pixelUrl = "https://github.com/abhishekchd664-pixel/Auto-Posting"
$envFile = Join-Path $root ".env"
if (Test-Path $envFile) {
    $raw = [IO.File]::ReadAllText($envFile)
    $line = "CURSOR_BACKGROUND_AGENT_REPO=$pixelUrl"
    if ($raw -match "(?m)^CURSOR_BACKGROUND_AGENT_REPO=") {
        $raw = $raw -replace "(?m)^CURSOR_BACKGROUND_AGENT_REPO=.*$", $line
    } else {
        $raw = $raw.TrimEnd() + "`r`n" + $line + "`r`n"
    }
    [IO.File]::WriteAllText($envFile, $raw)
    Write-Host "Updated .env CURSOR_BACKGROUND_AGENT_REPO" -ForegroundColor Green
}

Write-Host "Done. Grant Cursor GitHub app on $pixelUrl ; restart restart_fb_image_automation.cmd if needed." -ForegroundColor Green
