# Kast 2.0 - Windows Kaldırma (Uninstall) Scripti
# Kullanım: powershell -ExecutionPolicy Bypass -File .\uninstall.ps1

$ErrorActionPreference = "Stop"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Kast 2.0 — Windows Kaldırma Scripti                 " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$UserBin = Join-Path $env:USERPROFILE "bin"
$KastCmd = Join-Path $UserBin "kast.cmd"

if (Test-Path $KastCmd) {
    Remove-Item -Path $KastCmd -Force
    Write-Host "[✓] Başlatıcı ($KastCmd) başarıyla silindi." -ForegroundColor Green
} else {
    Write-Host "[ℹ] Başlatıcı ($KastCmd) bulunamadı veya zaten silinmiş." -ForegroundColor Yellow
}

$RepoDir = $PSScriptRoot
if (-not $RepoDir) {
    $RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

Write-Host ""
Write-Host "Kast 2.0 terminal entegrasyonu başarıyla kaldırıldı." -ForegroundColor Green
Write-Host "Program dosyalarını ve sanal ortamı (.venv) tamamen silmek için:" -ForegroundColor White
Write-Host "  Remove-Item -Recurse -Force `"$RepoDir`"" -ForegroundColor Yellow
Write-Host ""
