# Kast 2.0 - Windows Kaldirma (Uninstall) Scripti
# Kullanim: powershell -ExecutionPolicy Bypass -File .\uninstall.ps1

$ErrorActionPreference = "Continue"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Kast 2.0 -- Windows Kaldirma Scripti                " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$UserBin = Join-Path $env:USERPROFILE "bin"
$KastCmd = Join-Path $UserBin "kast.cmd"

if (Test-Path $KastCmd) {
    Remove-Item -Path $KastCmd -Force
    Write-Host "[OK] Baslatici ($KastCmd) basariyla silindi." -ForegroundColor Green
} else {
    Write-Host "[i] Baslatici ($KastCmd) bulunamadi veya zaten silinmis." -ForegroundColor Yellow
}

$RepoDir = $PSScriptRoot
if (-not $RepoDir) {
    $RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

Write-Host ""
Write-Host "Kast 2.0 terminal entegrasyonu basariyla kaldirildi." -ForegroundColor Green
Write-Host "Program dosyalarini ve sanal ortami (.venv) tamamen silmek icin:" -ForegroundColor White
Write-Host "  Remove-Item -Recurse -Force `"$RepoDir`"" -ForegroundColor Yellow
Write-Host ""
