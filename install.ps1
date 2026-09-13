# Kast 2.0 - Windows PowerShell Kurulum Scripti
# Kullanım: powershell -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Kast 2.0 — Windows Kurulum ve Entegrasyon Scripti   " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$RepoDir = $PSScriptRoot
if (-not $RepoDir) {
    $RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# 1. Python kontrolü
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} else {
    Write-Host "[Hata] Sistemde Python bulunamadı." -ForegroundColor Red
    Write-Host "Lütfen https://www.python.org adresinden Python 3.10 veya üzerini kurun ve PATH seçeneğini işaretleyin." -ForegroundColor Red
    exit 1
}

$PyVersion = & $PythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[✓] Python $PyVersion bulundu ($PythonCmd)." -ForegroundColor Green

# 2. Sanal ortam (.venv) kontrolü ve kurulumu
$VenvDir = Join-Path $RepoDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[➜] Sanal ortam (.venv) oluşturuluyor..." -ForegroundColor Cyan
    & $PythonCmd -m venv $VenvDir
} else {
    Write-Host "[✓] Mevcut sanal ortam (.venv) kullanılacak." -ForegroundColor Green
}

# 3. Bağımlılıkların yüklenmesi
Write-Host "[➜] Bağımlılıklar kontrol ediliyor..." -ForegroundColor Cyan
$CheckDeps = & $VenvPython -c "import docx, PIL, textual" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] Gerekli tüm bağımlılıklar zaten sanal ortamda mevcut." -ForegroundColor Green
} else {
    Write-Host "[➜] Eksik paketler yükleniyor (requirements.txt)..." -ForegroundColor Cyan
    $ReqFile = Join-Path $RepoDir "requirements.txt"
    & $VenvPython -m pip install --quiet -r $ReqFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Uyarı] pip ile paketler yüklenirken bir sorun oluştu. İnternet bağlantınızı kontrol edin." -ForegroundColor Yellow
    } else {
        Write-Host "[✓] Bağımlılıklar başarıyla yüklendi." -ForegroundColor Green
    }
}

# 4. %USERPROFILE%\bin dizininin hazırlanması ve kast.cmd kopyalanması
$UserBin = Join-Path $env:USERPROFILE "bin"
if (-not (Test-Path $UserBin)) {
    New-Item -ItemType Directory -Path $UserBin -Force | Out-Null
    Write-Host "[✓] '$UserBin' dizini oluşturuldu." -ForegroundColor Green
}

$KastCmdTarget = Join-Path $UserBin "kast.cmd"
$CmdContent = @"
@echo off
setlocal
if exist "$VenvPython" (
    "$VenvPython" "$RepoDir\kast.py" %*
) else (
    python "$RepoDir\kast.py" %*
)
endlocal
"@

Set-Content -Path $KastCmdTarget -Value $CmdContent -Encoding ASCII
Write-Host "[✓] Başlatıcı dosyası oluşturuldu: $KastCmdTarget" -ForegroundColor Green

# 5. Kullanıcı PATH ortam değişkenine ekleme
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $UserPath) {
    $UserPath = ""
}

$PathElements = $UserPath -split ';' | Where-Object { $_ -ne "" }
if ($PathElements -notcontains $UserBin) {
    $NewUserPath = if ($UserPath -ne "") { "$UserPath;$UserBin" } else { $UserBin }
    [Environment]::SetEnvironmentVariable("Path", $NewUserPath, "User")
    $env:Path = "$env:Path;$UserBin"
    Write-Host "[✓] '$UserBin' Kullanıcı PATH ortam değişkenine eklendi." -ForegroundColor Green
} else {
    Write-Host "[✓] '$UserBin' zaten PATH ortam değişkeninde kayıtlı." -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Kurulum Başarıyla Tamamlandı!                       " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "Artık yeni bir komut istemi (CMD) veya PowerShell penceresi açarak:" -ForegroundColor White
Write-Host "  kast              (Görsel TUI arayüzünü açar)" -ForegroundColor Yellow
Write-Host "  kast dosya.docx   (Hızlı komut satırı modunda çalıştırır)" -ForegroundColor Yellow
Write-Host "komutlarını doğrudan kullanabilirsiniz." -ForegroundColor White
Write-Host ""
