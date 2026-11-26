<#
.SYNOPSIS
    Resets the demo database from the golden read-only copy.
.DESCRIPTION
    Restores smart_shopping.db to pristine condition using smart_shopping.demo.db.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$GoldenDb = Join-Path $ScriptDir "smart_shopping.demo.db"
$LiveDb = Join-Path $ScriptDir "smart_shopping.db"

if (-not (Test-Path $GoldenDb)) {
    Write-Error "Golden database $GoldenDb does not exist!"
    exit 1
}

Write-Host "Restoring smart_shopping.db from golden copy..." -ForegroundColor Cyan
Copy-Item -Path $GoldenDb -Destination $LiveDb -Force
Write-Host "Reset complete! smart_shopping.db is restored to golden baseline." -ForegroundColor Green
