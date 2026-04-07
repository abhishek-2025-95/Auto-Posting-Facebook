# Option A — Import (no empty repo needed): as abhishekchd664-pixel, open
#   https://github.com/new/import
# and import from https://github.com/abhishek-2025-95/Auto-Posting-Facebook (main).
#
# Option B — Empty repo: create https://github.com/abhishekchd664-pixel/Auto-Posting-Facebook
# with no README, then run this script to push from your PC (needs pixel Git credentials).
#
# From project root:
#   powershell -ExecutionPolicy Bypass -File scripts\push_pixel_repo_after_github_create.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Push failed. Use GitHub credentials for abhishekchd664-pixel (PAT or gh auth login)." -ForegroundColor Yellow
    exit $LASTEXITCODE
}
Write-Host "Done. Set Cursor Cloud Agents GitHub app on this repo if you use the API bridge." -ForegroundColor Green
