# After you create an EMPTY repo at https://github.com/abhishekchd664-pixel/Auto-Posting-Facebook
# (no README, no .gitignore — same name as origin), run this from PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts\push_pixel_repo_after_github_create.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Push failed. Use GitHub credentials for abhishekchd664-pixel (PAT or gh auth login)." -ForegroundColor Yellow
    exit $LASTEXITCODE
}
Write-Host "Done. Set Cursor Cloud Agents GitHub app on this repo if you use the API bridge." -ForegroundColor Green
