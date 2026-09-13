# Kast 2.0 - Windows PowerShell Kurulum Scripti
# Kullanim: powershell -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Kast 2.0 -- Windows Kurulum ve Entegrasyon Scripti   " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$RepoDir = $PSScriptRoot
if (-not $RepoDir) {
    $RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# 1. Python kontrolu
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} else {
    Write-Host "[HATA] Sistemde Python bulunamadi." -ForegroundColor Red
    Write-Host "Lutfen https://www.python.org adresinden Python 3.10 veya uzerini kurun ve PATH secenegini isaretleyin." -ForegroundColor Red
    exit 1
}

$PyVersion = & $PythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[OK] Python $PyVersion bulundu ($PythonCmd)." -ForegroundColor Green

# 2. Sanal ortam (.venv) kontrolu ve kurulumu
$VenvDir = Join-Path $RepoDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[*] Sanal ortam (.venv) olusturuluyor..." -ForegroundColor Cyan
    & $PythonCmd -m venv $VenvDir
} else {
    Write-Host "[OK] Mevcut sanal ortam (.venv) kullanilacak." -ForegroundColor Green
}

# 3. Bagimliliklarin yuklenmesi
Write-Host "[*] Bagimliliklar kontrol ediliyor..." -ForegroundColor Cyan
$CheckDeps = & $VenvPython -c "import docx, PIL, textual" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Gerekli tum bagimliliklar zaten sanal ortamda mevcut." -ForegroundColor Green
} else {
    Write-Host "[*] Eksik paketler yukleniyor (requirements.txt)..." -ForegroundColor Cyan
    $ReqFile = Join-Path $RepoDir "requirements.txt"
    & $VenvPython -m pip install --quiet -r $ReqFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[UYARI] pip ile paketler yuklenirken bir sorun olustu. Internet baglantinizi kontrol edin." -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Bagimliliklar basariyla yuklendi." -ForegroundColor Green
    }
}

# 4. %USERPROFILE%\bin dizininin hazirlanmasi ve kast.cmd olusturulmasi
$UserBin = Join-Path $env:USERPROFILE "bin"
if (-not (Test-Path $UserBin)) {
    New-Item -ItemType Directory -Path $UserBin -Force | Out-Null
    Write-Host "[OK] '$UserBin' dizini olusturuldu." -ForegroundColor Green
}

$KastCmdTarget = Join-Path $UserBin "kast.cmd"
$CmdLines = @(
    "@echo off",
    "setlocal",
    "if exist `"$VenvPython`" (",
    "    `"$VenvPython`" `"$RepoDir\kast.py`" %*",
    ") else (",
    "    python `"$RepoDir\kast.py`" %*",
    ")",
    "endlocal"
)
$CmdLines | Set-Content -Path $KastCmdTarget -Encoding ASCII
Write-Host "[OK] Baslatici dosyasi olusturuldu: $KastCmdTarget" -ForegroundColor Green

# 5. Kullanici PATH ortam degiskenine ekleme
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $UserPath) {
    $UserPath = ""
}

$PathElements = $UserPath -split ';' | Where-Object { $_ -ne "" }
if ($PathElements -notcontains $UserBin) {
    if ($UserPath -ne "") {
        $NewUserPath = "$UserPath;$UserBin"
    } else {
        $NewUserPath = $UserBin
    }
    [Environment]::SetEnvironmentVariable("Path", $NewUserPath, "User")
    $env:Path = "$env:Path;$UserBin"
    Write-Host "[OK] '$UserBin' Kullanici PATH ortam degiskenine eklendi." -ForegroundColor Green
} else {
    Write-Host "[OK] '$UserBin' zaten PATH ortam degiskeninde kayitli." -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Kurulum Basariyla Tamamlandi!                       " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "Artik yeni bir komut istemi (CMD) veya PowerShell penceresi acarak:" -ForegroundColor White
Write-Host "  kast              (Gorsel TUI arayuzunu acar)" -ForegroundColor Yellow
Write-Host "  kast dosya.docx   (Hizli komut satiri modunda calistirir)" -ForegroundColor Yellow
Write-Host "komutlarini dogrudan kullanabilirsiniz." -ForegroundColor White
Write-Host ""
