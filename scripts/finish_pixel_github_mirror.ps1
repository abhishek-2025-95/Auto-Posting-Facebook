# Pushes main -> remote "pixel" and points CURSOR_BACKGROUND_AGENT_REPO at pixel on success.
# If push fails: create/import the repo while logged in as abhishekchd664-pixel, then re-run.
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$pixelUrl = "https://github.com/abhishekchd664-pixel/Auto-Posting-Facebook"
git push -u pixel main
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Push to 'pixel' failed (repo missing or wrong GitHub login)." -ForegroundColor Yellow
    Write-Host "1) Log in as abhishekchd664-pixel in the browser, then either:" -ForegroundColor Gray
    Write-Host "   Import: $pixelUrl (use Import from abhishek-2025-95/Auto-Posting-Facebook)" -ForegroundColor Gray
    Write-Host "   Or new empty repo: $pixelUrl" -ForegroundColor Gray
    Write-Host "2) gh auth login  (choose pixel account) OR use a PAT for git push" -ForegroundColor Gray
    Write-Host "3) Re-run: powershell -ExecutionPolicy Bypass -File scripts\finish_pixel_github_mirror.ps1" -ForegroundColor Gray
    exit $LASTEXITCODE
}

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
    Write-Host "Updated .env CURSOR_BACKGROUND_AGENT_REPO -> $pixelUrl" -ForegroundColor Green
}

Write-Host "Done. Grant Cursor GitHub app access on the pixel repo; restart FB image automation if it is running." -ForegroundColor Green
