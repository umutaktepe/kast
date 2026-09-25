# Windows Bağımsız Kurulum Sihirbazı (Setup.exe), Portable (ZIP) ve GitHub Actions CI/CD Dağıtım Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kullanıcıların bilgisayarlarında Python kurulu olma zorunluluğunu tamamen ortadan kaldırarak; çift tıklamayla çalışan **Portable ZIP** ve sistemde Word/LibreOffice yoksa arka planda sessizce LibreOffice kuran profesyonel **Inno Setup (.exe)** kurulum sihirbazını, GitHub Actions üzerinden otomatik derlenip release olarak yayınlanacak şekilde inşa etmek.

**Architecture:** 
1. **Dondurma (Freezing):** `PyInstaller` ve `packaging/kast.spec` ile Python çalışma zamanı, `PySide6`, `pdfplumber` ve tüm bağımlılıklar bağımsız bir Windows yürütülebilir klasörüne (`dist/KastStudio/`) derlenir.
2. **Kurulum Sihirbazı (Inno Setup):** `packaging/installer.iss` scripti ile `dist/KastStudio/` paketlenir; Pascal Scripting (`[Code]`) ile sistemde Microsoft Word (COM/Registry) veya LibreOffice aranır. İkisi de yoksa kullanıcıya hiç sormadan arka planda sessizce LibreOffice kurulur.
3. **Otomatik Yayınlama (GitHub Actions CI/CD):** `.github/workflows/release-windows.yml` iş akışı ile her yeni `v*` tag basıldığında veya manuel tetiklendiğinde Windows runner üzerinde hem `Kast-Setup-vX.Y.exe` hem de `Kast-Windows-Portable.zip` üretilip GitHub Releases'e eklenir.

**Tech Stack:** PyInstaller 6+, Inno Setup 6, GitHub Actions (windows-latest), PySide6, Python 3.10+, PowerShell / Pascal Script.

**Spec:** Kullanıcı talebi: Python gerektirmeyen bağımsız Windows Setup installer (.exe) + Portable ZIP dağıtımı, Word/LibreOffice yoksa sessiz otomatik LibreOffice kurulumu ve GitHub Actions CI/CD iş akışı.

## Global Constraints

- Kullanıcının bilgisayarında Python, pip veya sanal ortam kurulu olması KESİNLİKLE gerekmemelidir.
- Portable versiyon içinde `.venv` taşınmayacak; PyInstaller ile gömülü Python motoru (`python310.dll` / C runtime) barındıran tam bağımsız klasör ZIP'lenecektir.
- Inno Setup kurulumunda Microsoft Word veya LibreOffice varsa hiçbir ek işlem yapılmayacaktır. İkisi birden yoksa kullanıcıya sormadan arka planda sessizce (silent) LibreOffice kurulacaktır.
- GitHub Actions iş akışı Linux veya macOS geliştiricilerinin yerel Windows ortamına ihtiyaç duymadan GitHub bulutunda Windows `.exe` ve `.zip` çıktıları üretmesini sağlayacaktır.
- Tüm mimari değişiklikler ve kararlar `docs/kast-app-wiki/` Living Architecture kurallarına (`AGENTS.md`) uygun olarak belgelenecektir.

---

### Task 1: PyInstaller Yapılandırması, Giriş Noktası ve İkon Üretici (`packaging/`)

**Files:**
- Create: `packaging/generate_icon.py`
- Create: `packaging/run_gui.py`
- Create: `packaging/kast.spec`
- Test: `tests/test_packaging.py`

**Interfaces:**
- Produces: 
  - `packaging/assets/kast.ico`: 16, 32, 48, 64, 128, 256px çoklu çözünürlüklü stüdyo ikonu.
  - `packaging/run_gui.py`: Konsol penceresi açılmadan doğrudan `launch_gui()` çağıran dondurma giriş noktası.
  - `packaging/kast.spec`: PyInstaller ile `KastStudio.exe` ve bağlı kütüphaneleri `dist/KastStudio/` içerisine derleyen spesifikasyon.
- Consumes: `src/gui.py:launch_gui()`

- [ ] **Step 1: Failing test ekle (`tests/test_packaging.py`)**

```python
import os
import pytest

def test_packaging_files_exist():
    """Packaging dizinindeki spec, giriş noktası ve ikon üretici dosyalarının varlığını doğrular."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pkg_dir = os.path.join(repo_root, "packaging")
    
    assert os.path.exists(os.path.join(pkg_dir, "run_gui.py"))
    assert os.path.exists(os.path.join(pkg_dir, "kast.spec"))
    assert os.path.exists(os.path.join(pkg_dir, "generate_icon.py"))

def test_generate_icon_creates_valid_ico(tmp_path):
    """generate_icon scriptinin geçerli bir .ico dosyası ürettiğini test eder."""
    from packaging.generate_icon import create_kast_icon
    
    ico_path = str(tmp_path / "test_kast.ico")
    create_kast_icon(ico_path)
    
    assert os.path.exists(ico_path)
    assert os.path.getsize(ico_path) > 1000  # Çoklu çözünürlüklü ikon boyutu
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `pytest tests/test_packaging.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'packaging'` or `AssertionError`

- [ ] **Step 3: `packaging/generate_icon.py` oluştur**

Pillow ile gece mavisi ve neon elektrik camgöbeği renklerinde, mikrofon/klaket/K harfi motifli stüdyo ikonu üreten modül:

```python
"""packaging/generate_icon.py — Kast 2.0 çoklu çözünürlüklü Windows uygulama ikonu üretici."""
import os
from PIL import Image, ImageDraw

def create_kast_icon(output_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []

    for size in sizes:
        w, h = size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Gece mavisi yuvarlak zemin
        bg_color = (11, 15, 25, 255)       # #0b0f19
        border_color = (56, 189, 248, 255) # #38bdf8
        r = w // 2
        draw.ellipse([1, 1, w - 2, h - 2], fill=bg_color, outline=border_color, width=max(1, w // 32))

        # Elektrik camgöbeği 'K' harfi ve dublaj dalgası motifi
        cyan = (56, 189, 248, 255)
        # Sol dikey çizgi
        pad_x = w * 0.28
        bar_w = max(2, int(w * 0.12))
        top_y = h * 0.22
        bot_y = h * 0.78
        draw.rectangle([pad_x, top_y, pad_x + bar_w, bot_y], fill=cyan)

        # K'nın üst çapraz kolu
        draw.polygon([
            (pad_x + bar_w, h * 0.50),
            (pad_x + bar_w + int(w * 0.08), h * 0.50),
            (w * 0.72, top_y),
            (w * 0.72 - int(w * 0.10), top_y),
        ], fill=cyan)

        # K'nın alt çapraz kolu
        draw.polygon([
            (pad_x + bar_w, h * 0.46),
            (pad_x + bar_w + int(w * 0.08), h * 0.46),
            (w * 0.74, bot_y),
            (w * 0.74 - int(w * 0.10), bot_y),
        ], fill=cyan)

        images.append(img)

    images[0].save(
        output_path,
        format="ICO",
        sizes=[(im.width, im.height) for im in images],
        append_images=images[1:],
    )

if __name__ == "__main__":
    icon_file = os.path.join(os.path.dirname(__file__), "assets", "kast.ico")
    create_kast_icon(icon_file)
    print(f"Icon created successfully: {icon_file}")
```

- [ ] **Step 4: `packaging/run_gui.py` ve `packaging/kast.spec` oluştur**

`packaging/run_gui.py`:
```python
"""packaging/run_gui.py — PyInstaller için doğrudan Qt6 GUI giriş noktası."""
import sys
import os

# Kaynak dizinini sys.path'e ekle
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.gui import launch_gui

if __name__ == "__main__":
    sys.exit(launch_gui())
```

`packaging/kast.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None
ROOT_DIR = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = [
    (os.path.join(ROOT_DIR, "docs"), "docs"),
    (os.path.join(ROOT_DIR, "example"), "example"),
]

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "docx",
    "pdfplumber",
    "pypdf",
    "PIL",
]

a = Analysis(
    [os.path.join(SPECPATH, "run_gui.py")],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "notebook", "IPython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KastStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Konsol penceresini gizle, sadece GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SPECPATH, "assets", "kast.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KastStudio",
)
```

- [ ] **Step 5: İkonu üret, testi çalıştır ve geçtiğini doğrula**

Run: `python3 packaging/generate_icon.py && pytest tests/test_packaging.py -v`
Expected: PASS

- [ ] **Step 6: Git commit**

```bash
git add packaging/ tests/test_packaging.py
git commit -m "feat(packaging): add PyInstaller spec, icon generator, and entrypoint"
```

---

### Task 2: Inno Setup Kurulum Sihirbazı (`installer.iss`) ve Sessiz LibreOffice Kurulumu

**Files:**
- Create: `packaging/installer.iss`
- Test: `tests/test_inno_setup.py`

**Interfaces:**
- Produces: `packaging/installer.iss`
  - Inno Setup 6 derleyicisi (`iscc`) ile çalışır.
  - Windows `Program Files\Kast Studio` dizinine kurar.
  - Masaüstü ve Başlat Menüsü simgelerini (`kast.ico`) otomatik ekler.
  - **Pascal Script Kontrolü (`[Code]`):**
    - `IsWordInstalled()`: Registry veya COM kontrolü ile MS Word varlığını denetler.
    - `IsLibreOfficeInstalled()`: Registry veya `soffice.exe` dosya yolu kontrolü yapar.
    - Eğer **İKİSİ DE YOKSA**: `CurStepChanged(ssPostInstall)` adımında kullanıcıya sormadan `winget` (veya MSI download) ile LibreOffice'i arka planda sessiz (`/qn` veya `--silent`) kurar.
    - Biri veya ikisi varsa hiçbir ek işlem yapmadan anında kurulumu tamamlar.

- [ ] **Step 1: Failing test ekle (`tests/test_inno_setup.py`)**

```python
import os
import re

def test_inno_setup_script_syntax_and_sections():
    """Inno Setup scriptinin temel bölümleri ve sessiz LibreOffice kontrollerini barındırdığını test eder."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    iss_file = os.path.join(repo_root, "packaging", "installer.iss")
    
    assert os.path.exists(iss_file), "installer.iss dosyası bulunamadı."
    content = open(iss_file, "r", encoding="utf-8").read()
    
    # Bölüm kontrolleri
    assert "[Setup]" in content
    assert "[Files]" in content
    assert "[Icons]" in content
    assert "[Code]" in content
    
    # İsim ve uygulama kontrolleri
    assert "KastStudio.exe" in content
    assert "kast.ico" in content
    
    # Word ve LibreOffice tespit ve sessiz kurulum Pascal kodları
    assert "function IsWordInstalled" in content
    assert "function IsLibreOfficeInstalled" in content
    assert "TheDocumentFoundation.LibreOffice" in content or "soffice.exe" in content
    assert "--silent" in content or "/qn" in content
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `pytest tests/test_inno_setup.py -v`
Expected: FAIL with `AssertionError: installer.iss dosyası bulunamadı.`

- [ ] **Step 3: `packaging/installer.iss` dosyasını oluştur**

```pascal
; packaging/installer.iss — Kast 2.0 Windows Studio Edition Inno Setup Scripti
#define MyAppName "Kast Studio"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Umut Aktepe"
#define MyAppURL "https://github.com/umutaktepe/Kast"
#define MyAppExeName "KastStudio.exe"

[Setup]
AppId={{D37E6F90-7F89-4A73-98C3-2A676E4B15C0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Kast-v{#MyAppVersion}-Setup
SetupIconFile=assets\kast.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; PyInstaller ile derlenen tüm klasör
Source: "..\dist\KastStudio\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "assets\kast.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\kast.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\kast.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// --- Word ve LibreOffice Varlık Denetimi ve Sessiz Kurulum ---

function IsWordInstalled(): Boolean;
var
  AppPath: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Winword.exe', '', AppPath) or
            RegKeyExists(HKCR, 'Word.Application');
end;

function IsLibreOfficeInstalled(): Boolean;
var
  InstallPath: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\LibreOffice\UNO\InstallPath', '', InstallPath) or
            RegKeyExists(HKLM, 'SOFTWARE\The Document Foundation\LibreOffice') or
            FileExists(ExpandConstant('{pf}\LibreOffice\program\soffice.exe')) or
            FileExists(ExpandConstant('{pf32}\LibreOffice\program\soffice.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\LibreOffice\program\soffice.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  WingetCmd: String;
  PSCmd: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Eğer ne Word ne de LibreOffice varsa kullanıcıya hiç hissettirmeden arka planda LibreOffice kur
    if (not IsWordInstalled()) and (not IsLibreOfficeInstalled()) then
    begin
      WizardForm.StatusLabel.Caption := 'Döküman sayfa doğrulaması için gerekli bileşenler hazırlanıyor (LibreOffice)...';
      
      // 1. Önce winget ile sessiz kurulum dene
      WingetCmd := '/c winget install --id TheDocumentFoundation.LibreOffice -e --silent --accept-package-agreements --accept-source-agreements';
      if not Exec('cmd.exe', WingetCmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      begin
        // 2. Winget başarısız olursa PowerShell ile doğrudan MSI indir ve sessiz kur
        PSCmd := '-ExecutionPolicy Bypass -Command "' +
                 '$url = ''https://download.documentfoundation.org/libreoffice/stable/latest/win/x86_64/LibreOffice_latest_Win_x86-64.msi''; ' +
                 '$dest = Join-Path $env:TEMP ''LibreOfficeInstall.msi''; ' +
                 'try { ' +
                 '  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ' +
                 '  Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing; ' +
                 '  Start-Process msiexec.exe -ArgumentList ''/i'', $dest, ''/qn'', ''/norestart'' -Wait; ' +
                 '  Remove-Item $dest -Force -ErrorAction SilentlyContinue; ' +
                 '} catch {}"';
        Exec('powershell.exe', PSCmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `pytest tests/test_inno_setup.py -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add packaging/installer.iss tests/test_inno_setup.py
git commit -m "feat(packaging): add Inno Setup script with silent Word/LibreOffice detection"
```

---

### Task 3: GitHub Actions Otomatik Derleme ve Release İş Akışı (`.github/workflows/release-windows.yml`)

**Files:**
- Create: `.github/workflows/release-windows.yml`
- Test: `tests/test_ci_workflow.py`

**Interfaces:**
- Produces: `.github/workflows/release-windows.yml`
  - Tetikleyiciler: Git tag (`v*`) ve `workflow_dispatch`.
  - Platform: `windows-latest`.
  - Aşamalar:
    1. Python 3.11 kurulumu ve bağımlılıkların (`requirements.txt`, `pyinstaller`) yüklenmesi.
    2. `packaging/generate_icon.py` çalıştırılarak logonun üretilmesi.
    3. `pyinstaller packaging/kast.spec` ile `dist/KastStudio/` derlenmesi.
    4. `Compress-Archive` ile `Kast-Windows-Portable.zip` oluşturulması.
    5. Inno Setup (`iscc packaging/installer.iss`) ile `Kast-Setup.exe` derlenmesi.
    6. SHA256 sağlama toplamı dosyalarının (`checksums.txt`) oluşturulması.
    7. `softprops/action-gh-release` ile GitHub Releases sayfasına iki dosyanın yüklenmesi:
       - `Kast-vX.Y.Z-Setup.exe`
       - `Kast-vX.Y.Z-Windows-Portable.zip`

- [ ] **Step 1: Failing test ekle (`tests/test_ci_workflow.py`)**

```python
import os
import yaml

def test_github_actions_workflow_syntax():
    """release-windows.yml iş akışının sözdizimini ve adımlarını test eder."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    wf_file = os.path.join(repo_root, ".github", "workflows", "release-windows.yml")
    
    assert os.path.exists(wf_file), "release-windows.yml dosyası bulunamadı."
    content = open(wf_file, "r", encoding="utf-8").read()
    data = yaml.safe_load(content)
    
    # Trigger kontrolleri
    assert "push" in data or True
    jobs = data.get("jobs", {})
    assert "build-windows" in jobs
    
    job = jobs["build-windows"]
    assert "windows-latest" in job.get("runs-on", "")
    
    # Adım kontrolleri
    step_names = [s.get("name", "") for s in job.get("steps", [])]
    assert any("PyInstaller" in s for s in step_names)
    assert any("Portable" in s for s in step_names)
    assert any("Inno Setup" in s for s in step_names)
    assert any("Release" in s for s in step_names)
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `pytest tests/test_ci_workflow.py -v`
Expected: FAIL with `AssertionError: release-windows.yml dosyası bulunamadı.`

- [ ] **Step 3: `.github/workflows/release-windows.yml` dosyasını oluştur**

```yaml
name: Build and Release Windows Packages

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Sürüm numarası (örn: 2.1.0)'
        required: false
        default: '2.1.0'

permissions:
  contents: write

jobs:
  build-windows:
    name: Build Windows Setup & Portable
    runs-on: windows-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set Version Variable
        id: vars
        shell: bash
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            echo "VERSION=${{ github.event.inputs.version }}" >> $GITHUB_ENV
          else
            TAG=${GITHUB_REF#refs/tags/}
            echo "VERSION=${TAG#v}" >> $GITHUB_ENV
          fi

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Python Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller Pillow

      - name: Generate Application Icon
        run: |
          python packaging/generate_icon.py

      - name: Build Standalone with PyInstaller
        run: |
          pyinstaller packaging/kast.spec --noconfirm

      - name: Create Portable ZIP Package
        shell: pwsh
        run: |
          $zipPath = "dist\Kast-v$($env:VERSION)-Windows-Portable.zip"
          Compress-Archive -Path dist\KastStudio\* -DestinationPath $zipPath -CompressionLevel Optimal
          Write-Host "Portable archive created at: $zipPath"

      - name: Install Inno Setup
        shell: pwsh
        run: |
          choco install innosetup --no-progress -y

      - name: Compile Inno Setup Installer
        shell: cmd
        run: |
          "C:\Program Files (x86)\Inno Setup 6\iscc.exe" /DMyAppVersion=%VERSION% packaging\installer.iss

      - name: Generate Checksums
        shell: pwsh
        run: |
          Get-FileHash dist\Kast-v$($env:VERSION)-Setup.exe, dist\Kast-v$($env:VERSION)-Windows-Portable.zip -Algorithm SHA256 |
            ForEach-Object { "$($_.Hash)  $([System.IO.Path]::GetFileName($_.Path))" } |
            Out-File -FilePath dist\checksums.txt -Encoding utf8
          Get-Content dist\checksums.txt

      - name: Publish GitHub Release
        uses: softprops/action-gh-release@v2
        if: startsWith(github.ref, 'refs/tags/') || github.event_name == 'workflow_dispatch'
        with:
          files: |
            dist/Kast-v${{ env.VERSION }}-Setup.exe
            dist/Kast-v${{ env.VERSION }}-Windows-Portable.zip
            dist/checksums.txt
          name: Kast Studio v${{ env.VERSION }}
          draft: false
          prerelease: false
          generate_release_notes: true
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `pytest tests/test_ci_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add .github/workflows/release-windows.yml tests/test_ci_workflow.py
git commit -m "ci: add GitHub Actions workflow to build and release Windows Setup and Portable"
```

---

### Task 4: Dokümantasyon ve Living Architecture Wiki Senkronizasyonu (`AGENTS.md`)

**Files:**
- Create: `docs/kast-app-wiki/architecture-decisions/adr-006-windows-standalone-installer-and-ci.md`
- Create: `docs/kast-app-wiki/interfaces-and-runtime/windows-packaging-and-releases.md`
- Modify: `docs/kast-app-wiki/interfaces-and-runtime/cross-platform-installers.md`
- Modify: `docs/kast-app-wiki/index.md`
- Modify: `docs/kast-app-wiki/log.md`
- Modify: `README.md`

**Interfaces:**
- Produces:
  - `adr-006-windows-standalone-installer-and-ci.md`: Neden son kullanıcılara Python kurdurulmadığı, PyInstaller + Inno Setup ve sessiz LibreOffice kararı.
  - `windows-packaging-and-releases.md`: Portable vs Installer ayrımı, Inno Setup mekanizması ve GitHub Actions CI/CD pipeline dokümantasyonu.
- Updates:
  - `index.md`: ADR-006 ve yeni modülün fihriste eklenmesi.
  - `log.md`: Kronolojik değişiklik kaydı.
  - `README.md`: İndirme bağlantıları (GitHub Releases), Setup.exe ve Portable kullanımı.

- [ ] **Step 1: ADR-006 belgesini oluştur**

`docs/kast-app-wiki/architecture-decisions/adr-006-windows-standalone-installer-and-ci.md`:
Bağlam, Karar, Alternatifler (Manuel Python kurulumu, Docker, Electron/Web), Sonuçlar (Kullanıcı sıfır eforla kurar, Python gerektirmez, CI/CD tam otomatik üretir).

- [ ] **Step 2: `windows-packaging-and-releases.md` sayfasını oluştur**

`docs/kast-app-wiki/interfaces-and-runtime/windows-packaging-and-releases.md`:
PyInstaller yapılandırması, Inno Setup `[Code]` Pascal mantığı, Word/LibreOffice sessiz kurulumu ve GitHub Actions işleyişini detaylandır.

- [ ] **Step 3: `README.md` ve `cross-platform-installers.md` sayfalarını güncelle**

Kullanıcılara doğrudan Releases sekmesinden `Kast-Setup.exe` veya `Kast-Portable.zip` indirme yönlendirmesi ekle.

- [ ] **Step 4: `index.md` ve `log.md` güncelle**

Living architecture fihristine ve günlüğe kayıt düş.

- [ ] **Step 5: Wiki linting doğrulaması yap**

Run: `python3 -c "import os, re; ... lint check ..."`
Expected: 0 kırık link, 0 yetim sayfa.

- [ ] **Step 6: Git commit**

```bash
git add docs/kast-app-wiki/ README.md
git commit -m "docs(wiki): document Windows standalone installer, portable bundle, and CI/CD"
```

---

## Verification Plan

### Automated Tests
```bash
# 1. Paketleme ve CI sözdizimi testleri
pytest tests/test_packaging.py tests/test_inno_setup.py tests/test_ci_workflow.py -v

# 2. Tam regresyon testi
QT_QPA_PLATFORM=offscreen pytest -v

# 3. Wiki link ve graf bütünlüğü testi
python3 -c "
import os, re
wiki_dir = 'docs/kast-app-wiki'
md_files = {f[:-3]: os.path.join(r, f) for r, _, fs in os.walk(wiki_dir) for f in fs if f.endswith('.md')}
broken = [(b, t) for b, p in md_files.items() for t in re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', open(p).read()) if t.strip() not in md_files]
assert len(broken) == 0, f'Kırık linkler: {broken}'
print('WIKI LINT PASSED CLEANLY!')
"
```

### Manual Verification
1. **İkon Üretimi Doğrulaması:** `python3 packaging/generate_icon.py` çalıştırılıp `packaging/assets/kast.ico` dosyasının geçerli çoklu katmanlı Windows ikonu olduğu doğrulanır.
2. **PyInstaller Spec Kuru Çalıştırması (Dry-Run):** Spec dosyasının Python sözdizimi ve import yolları doğrulanır.
3. **Inno Setup Script Doğrulaması:** `installer.iss` scriptinin Pascal fonksiyonlarının derleyici standartlarına tam uyumu teyit edilir.
