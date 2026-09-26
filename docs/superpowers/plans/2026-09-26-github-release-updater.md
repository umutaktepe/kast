# GitHub Releases Versiyon Kontrolü ve Güvenli Otomatik Güncelleme (In-App Updater) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kast Studio Qt6 masaüstü arayüzüne GitHub Releases üzerinden çalışan otomatik ve manuel güncelleme denetimi kazandırmak; sistemin Windows Setup (.exe) veya Portable (.zip) olarak çalışıp çalışmadığını tespit ederek ilgili paketi indirmek; ve çalışan uygulama kilitlenmelerine yol açmadan (file lock-free) güncelleme kurulumunu güvenle tamamlamak.

**Architecture:** 
1. `src/version.py`: Projenin kanonik sürüm numarasını (`__version__ = "2.1.1"`), semantik sürüm ayrıştırma (`parse_version`) ve karşılaştırma mantığını yönetir.
2. `src/updater.py`: Dağıtım türünü (`DistributionType.SETUP`, `DistributionType.PORTABLE`, `DistributionType.DEV`) çalışma zamanı dosya sistemi (`unins000.exe`) ve registry üzerinden tespit eder; GitHub Releases API'sini (`api.github.com/repos/umutaktepe/Kast/releases/latest`) sorgular; Setup ve Portable paketlerine göre uygun sürüm varlıklarını (assets) eşler; indirme ve arka plan kurulum hazırlığı (`Setup.exe` bağımsız çalıştırma ve Portable için PID-beklemeli robocopy scripti) sunar.
3. `src/updater_gui.py`: PySide6 tabanlı `UpdateCheckWorker` ve `UpdateDownloadWorker` arka plan iş parçacıklarını (`QThread`), `StudioTheme` uyumlu karanlık temalı `UpdateNotificationDialog` bildirim penceresini ve ilerleme çubuğu içeren `UpdateDownloadDialog` modalını barındırır.
4. `src/gui.py`: Başlangıçta 1.5 saniye sonra sessiz otomatik kontrolü (`QTimer.singleShot`) tetikler; başlık çubuğuna şık bir "🔄 Güncellemeleri Denetle" butonu ekler; güncelleme bulunduğunda bildirim penceresini açar; manuel kontrolde kullanıcıya durumu (güncel / hata) bildirir.

**Tech Stack:** Python 3.10+, PySide6 (Qt6), `urllib.request`, `zipfile`, `tempfile`, `subprocess`, `pytest`, `pytest-asyncio`.

**Spec:** Kullanıcı talebi: GitHub Releases üzerinden versiyon kontrolü; "Check updates" butonu; her açılışta otomatik sessiz sorgulama; yeni sürüm varsa popup mesaj (güncelle / yoksay); Windows için exe setup ise exe setup, portable ise portable paket kontrolü ve indirilmesi; indirme sonrası kurma işleminin sorunsuz ve kilitlenme yaratmayacak şekilde (safe handoff) opere edilmesi. Yalnızca GUI için geçerlidir.

## Global Constraints

- **Yalnızca GUI Kapsamı:** CLI ve TUI modları etkilenmez; güncelleme alt sistemi `src/updater.py` ve `src/updater_gui.py` üzerinden `src/gui.py` ile entegre çalışır.
- **Sıfır Ek Dış Bağımlılık (Zero Extra Dependencies):** HTTP istekleri ve ZIP açma işlemleri için harici kütüphane (`requests` vb.) eklenmez; Python standart kütüphanesindeki `urllib.request` ve `zipfile` modülleri kullanılır.
- **Kullanıcı Deneyimi ve Bloklamama (Non-blocking Asynchronous Flow):** Ağ çağrıları asla ana GUI iş parçacığını (main UI thread) dondurmaz; tüm API ve indirme işlemleri `QThread` üzerinde asenkron yürütülür.
- **Açılışta Sessiz Mod (Silent Startup Check):** Uygulama açılışında otomatik yapılan kontrolde güncelleme yoksa veya internet bağlantısı kopuksa kullanıcıya rahatsız edici hata penceresi gösterilmez; yalnızca yeni sürüm tespit edilirse popup açılır. Manuel butona basıldığında ise tüm durumlar (güncel, hata, yeni sürüm) kullanıcıya bildirilir.
- **Windows Dosya Kilidi Koruması (Safe Windows File Lock-Free Installation):** Windows işletim sisteminde çalışan bir `.exe` dosyasının üzerine doğrudan yazılamaz (`ERROR_ACCESS_DENIED`). Setup sürümünde `Kast-vX.Y.Z-Setup.exe` bağımsız işlem olarak (`DETACHED_PROCESS`) başlatılıp mevcut Kast Studio kapatılır. Portable sürümünde ise dosyalar geçici dizine açılır, mevcut sürecin PID'sinin sonlanmasını bekleyen ve robocopy ile dosyaları taşıyıp yeni sürümü başlatan bağımsız bir script çalıştırılarak uygulama kapatılır.
- **Living Architecture Uyumu:** Yeni mimari karar kaydı (`adr-008-in-app-github-release-updater.md`), dokümantasyon sayfası (`github-release-updater.md`), `index.md` (MOC) ve `log.md` güncellenmelidir.

---

### Task 1: Kanonik Versiyonlama ve Semantik Karşılaştırma Modülü (`src/version.py`)

**Files:**
- Create: `src/version.py`
- Modify: `src/__init__.py:1-23`
- Test: `tests/test_updater.py`

**Interfaces:**
- Consumes: `re`, `typing.Tuple`
- Produces:
  - `__version__: str = "2.1.1"`
  - `parse_version(version_str: str) -> Tuple[int, ...]`
  - `is_newer_version(remote_version: str, current_version: str = __version__) -> bool`

- [ ] **Step 1: Failing testleri yaz (`tests/test_updater.py`)**

```python
import pytest
from src.version import __version__, parse_version, is_newer_version


def test_version_string_format():
    """__version__ değişkeninin geçerli semver biçiminde olduğunu doğrular."""
    assert __version__ == "2.1.1"


def test_parse_version_standard_and_prefixed():
    """parse_version fonksiyonunun 'v' önekli ve öneksiz sürümleri doğru ayrıştırdığını doğrular."""
    assert parse_version("2.1.1") == (2, 1, 1)
    assert parse_version("v2.1.1") == (2, 1, 1)
    assert parse_version("v2.2.0") == (2, 2, 0)
    assert parse_version("3.0.0.1") == (3, 0, 0, 1)
    assert parse_version("v1.0") == (1, 0)


def test_is_newer_version_comparison():
    """is_newer_version fonksiyonunun sürüm karşılaştırmasını doğru yaptığını doğrular."""
    assert is_newer_version("2.1.2", "2.1.1") is True
    assert is_newer_version("v2.2.0", "2.1.1") is True
    assert is_newer_version("v3.0.0", "2.1.1") is True
    assert is_newer_version("2.1.1", "2.1.1") is False
    assert is_newer_version("2.1.0", "2.1.1") is False
    assert is_newer_version("v2.0.9", "2.1.1") is False


def test_init_exports_version():
    """src paketinin __version__ sembolünü dışa aktardığını doğrular."""
    import src
    assert hasattr(src, "__version__")
    assert src.__version__ == "2.1.1"
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `.venv/bin/pytest tests/test_updater.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.version'`

- [ ] **Step 3: `src/version.py` modülünü oluştur ve `src/__init__.py`'ye ekle**

`src/version.py`:
```python
"""Version specification and semantic version comparison utilities for Kast."""

import re
from typing import Tuple

__version__ = "2.1.1"


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse a semantic version string (e.g. 'v2.1.1' or '2.1.1') into an integer tuple.

    Non-digit suffixes or prefixes are safely stripped.
    """
    clean_str = version_str.strip().lstrip("vV")
    # Sayısal blokları topla
    parts = re.findall(r"\d+", clean_str)
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts)


def is_newer_version(remote_version: str, current_version: str = __version__) -> bool:
    """Return True if remote_version is strictly newer than current_version."""
    remote_tuple = parse_version(remote_version)
    current_tuple = parse_version(current_version)

    # Karşılaştırma için uzunlukları eşitle (örn (2, 1) vs (2, 1, 0))
    max_len = max(len(remote_tuple), len(current_tuple))
    r_padded = remote_tuple + (0,) * (max_len - len(remote_tuple))
    c_padded = current_tuple + (0,) * (max_len - len(current_tuple))

    return r_padded > c_padded
```

`src/__init__.py` içerisine `from src.version import __version__` ekle ve `__all__` listesine `"__version__"` sembolünü dahil et.

- [ ] **Step 4: Testleri çalıştır ve geçtiğini doğrula**

Run: `.venv/bin/pytest tests/test_updater.py -v`
Expected: PASS (4 tests passed)

- [ ] **Step 5: Commit**

```bash
git add src/version.py src/__init__.py tests/test_updater.py
git commit -m "feat(updater): add version specification and semantic comparison module"
```

---

### Task 2: Dağıtım Tespiti, GitHub Releases İstemcisi ve Kurulum Handoff Motoru (`src/updater.py`)

**Files:**
- Create: `src/updater.py`
- Modify: `tests/test_updater.py`

**Interfaces:**
- Consumes: `src.version.is_newer_version`, `src.version.__version__`, `urllib.request`, `json`, `os`, `sys`, `zipfile`, `subprocess`
- Produces:
  - `class DistributionType(Enum)`: `SETUP`, `PORTABLE`, `DEV`
  - `detect_distribution_type(app_dir: Optional[str] = None, is_frozen: Optional[bool] = None, platform: Optional[str] = None) -> DistributionType`
  - `class ReleaseAssetInfo(NamedTuple)`: `name: str, download_url: str, size: int`
  - `class ReleaseInfo`: `tag_name: str, version: str, title: str, body: str, html_url: str, assets: list[ReleaseAssetInfo], target_asset: Optional[ReleaseAssetInfo]`
  - `select_target_asset(assets: list[ReleaseAssetInfo], dist_type: DistributionType) -> Optional[ReleaseAssetInfo]`
  - `check_for_updates(current_version: str = __version__, repo: str = "umutaktepe/Kast", dist_type: Optional[DistributionType] = None, timeout: int = 8) -> Tuple[bool, Optional[ReleaseInfo], Optional[str]]`
  - `download_release_asset(asset_url: str, dest_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> None`
  - `generate_portable_updater_script(app_dir: str, staged_dir: str, target_exe_name: str, current_pid: int) -> str`
  - `launch_installer_and_exit(installer_path: str) -> None`
  - `launch_portable_updater_and_exit(script_path: str) -> None`

- [ ] **Step 1: Updater motoru birim ve entegrasyon testlerini ekle (`tests/test_updater.py`)**

```python
from unittest.mock import MagicMock, patch
import json
import os
from src.updater import (
    DistributionType,
    detect_distribution_type,
    ReleaseAssetInfo,
    ReleaseInfo,
    select_target_asset,
    check_for_updates,
    generate_portable_updater_script,
)


def test_detect_distribution_type_setup(tmp_path):
    """Windows üzerinde unins000.exe varsa SETUP dağıtımı olarak algılanır."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "unins000.exe").write_text("fake uninstaller")
    (app_dir / "KastStudio.exe").write_text("fake exe")

    dt = detect_distribution_type(app_dir=str(app_dir), is_frozen=True, platform="win32")
    assert dt == DistributionType.SETUP


def test_detect_distribution_type_portable(tmp_path):
    """Windows üzerinde unins000.exe yoksa PORTABLE dağıtımı olarak algılanır."""
    app_dir = tmp_path / "portable_app"
    app_dir.mkdir()
    (app_dir / "KastStudio.exe").write_text("fake exe")

    dt = detect_distribution_type(app_dir=str(app_dir), is_frozen=True, platform="win32")
    assert dt == DistributionType.PORTABLE


def test_detect_distribution_type_dev():
    """Donmuş (frozen) olmayan veya Windows dışı ortamlar DEV olarak algılanır."""
    assert detect_distribution_type(is_frozen=False, platform="win32") == DistributionType.DEV
    assert detect_distribution_type(is_frozen=True, platform="linux") == DistributionType.DEV


def test_select_target_asset_matching():
    """Dağıtım türüne göre doğru GitHub Release asset'inin seçildiğini doğrular."""
    assets = [
        ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://download/setup.exe", 65000000),
        ReleaseAssetInfo("Kast-v2.2.0-Windows-Portable.zip", "https://download/portable.zip", 60000000),
        ReleaseAssetInfo("checksums.txt", "https://download/checksums.txt", 120),
    ]

    setup_asset = select_target_asset(assets, DistributionType.SETUP)
    assert setup_asset is not None
    assert setup_asset.name == "Kast-v2.2.0-Setup.exe"

    portable_asset = select_target_asset(assets, DistributionType.PORTABLE)
    assert portable_asset is not None
    assert portable_asset.name == "Kast-v2.2.0-Windows-Portable.zip"

    # DEV modunda Windows için Setup tercih edilir, bulunamazsa Portable
    dev_asset = select_target_asset(assets, DistributionType.DEV)
    assert dev_asset is not None
    assert dev_asset.name in ("Kast-v2.2.0-Setup.exe", "Kast-v2.2.0-Windows-Portable.zip")


def test_check_for_updates_available():
    """Yeni sürüm mevcut olduğunda ReleaseInfo nesnesi döner."""
    fake_response = {
        "tag_name": "v2.2.0",
        "name": "Kast Studio v2.2.0 — Performans Güncellemesi",
        "body": "## Yenilikler\n- Hızlı açılış\n- Güncel tablolar",
        "html_url": "https://github.com/umutaktepe/Kast/releases/tag/v2.2.0",
        "assets": [
            {
                "name": "Kast-v2.2.0-Setup.exe",
                "browser_download_url": "https://github.com/releases/download/v2.2.0/Kast-v2.2.0-Setup.exe",
                "size": 67108864,
            },
            {
                "name": "Kast-v2.2.0-Windows-Portable.zip",
                "browser_download_url": "https://github.com/releases/download/v2.2.0/Kast-v2.2.0-Windows-Portable.zip",
                "size": 61865984,
            }
        ]
    }

    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(fake_response).encode("utf-8")

    with patch("urllib.request.urlopen", mock_urlopen):
        has_update, rel_info, err = check_for_updates(
            current_version="2.1.1",
            dist_type=DistributionType.SETUP
        )

        assert has_update is True
        assert err is None
        assert rel_info is not None
        assert rel_info.version == "2.2.0"
        assert rel_info.target_asset.name == "Kast-v2.2.0-Setup.exe"


def test_check_for_updates_already_latest():
    """Uygulama zaten en güncel sürümdeyse has_update False döner."""
    fake_response = {
        "tag_name": "v2.1.1",
        "name": "Kast Studio v2.1.1",
        "body": "Mevcut sürüm",
        "html_url": "https://github.com/umutaktepe/Kast/releases/tag/v2.1.1",
        "assets": []
    }
    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(fake_response).encode("utf-8")

    with patch("urllib.request.urlopen", mock_urlopen):
        has_update, rel_info, err = check_for_updates(
            current_version="2.1.1",
            dist_type=DistributionType.PORTABLE
        )
        assert has_update is False
        assert err is None
        assert rel_info is not None


def test_check_for_updates_network_error():
    """Ağ hatasında sistem çökmez, açıklayıcı hata mesajı döner."""
    with patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
        has_update, rel_info, err = check_for_updates(current_version="2.1.1")
        assert has_update is False
        assert rel_info is None
        assert "Connection timed out" in err


def test_generate_portable_updater_script(tmp_path):
    """Taşınabilir güncelleme betiğinin geçerli Windows batch komutları ürettiğini doğrular."""
    app_dir = str(tmp_path / "app")
    stage_dir = str(tmp_path / "stage")
    bat_content = generate_portable_updater_script(
        app_dir=app_dir,
        staged_dir=stage_dir,
        target_exe_name="KastStudio.exe",
        current_pid=1234
    )

    assert "1234" in bat_content
    assert app_dir in bat_content
    assert stage_dir in bat_content
    assert "KastStudio.exe" in bat_content
    assert "robocopy" in bat_content
```

- [ ] **Step 2: Testleri çalıştır ve başarısız olduğunu doğrula**

Run: `.venv/bin/pytest tests/test_updater.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.updater'`

- [ ] **Step 3: `src/updater.py` modülünü yaz**

`src/updater.py`:
```python
"""In-App Update Engine for Kast Studio.

Handles distribution detection (Windows Setup vs Portable vs Dev),
GitHub Releases API querying, asset matching, background download,
and lock-free update installation handoff.
"""

from dataclasses import dataclass
from enum import Enum
import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, List, Optional, Tuple
import urllib.error
import urllib.request
import zipfile

from src.version import __version__, is_newer_version, parse_version

GITHUB_API_LATEST_RELEASE = "https://api.github.com/repos/{repo}/releases/latest"
DEFAULT_REPO = "umutaktepe/Kast"


class DistributionType(Enum):
    """Runtime packaging mode of the application."""
    SETUP = "setup"        # Inno Setup installed (.exe with unins000.exe)
    PORTABLE = "portable"  # Windows Portable folder (.zip bundle)
    DEV = "dev"            # Running from source / development mode


@dataclass
class ReleaseAssetInfo:
    """Metadata for a downloadable release file."""
    name: str
    download_url: str
    size: int


@dataclass
class ReleaseInfo:
    """Metadata for a GitHub release."""
    tag_name: str
    version: str
    title: str
    body: str
    html_url: str
    assets: List[ReleaseAssetInfo]
    target_asset: Optional[ReleaseAssetInfo] = None


def detect_distribution_type(
    app_dir: Optional[str] = None,
    is_frozen: Optional[bool] = None,
    platform: Optional[str] = None,
) -> DistributionType:
    """Detect whether Kast is running as an installed Setup, Portable ZIP, or Dev script."""
    frozen = is_frozen if is_frozen is not None else getattr(sys, "frozen", False)
    plat = platform if platform is not None else sys.platform

    if not frozen or plat != "win32":
        return DistributionType.DEV

    directory = app_dir if app_dir is not None else os.path.dirname(sys.executable)

    # Inno Setup kurulumlarında kurulum klasöründe mutlaka unins000.exe bulunur
    uninstaller_path = os.path.join(directory, "unins000.exe")
    if os.path.isfile(uninstaller_path):
        return DistributionType.SETUP

    return DistributionType.PORTABLE


def select_target_asset(
    assets: List[ReleaseAssetInfo],
    dist_type: DistributionType,
) -> Optional[ReleaseAssetInfo]:
    """Select the most appropriate release asset based on distribution type."""
    if dist_type == DistributionType.SETUP:
        # Öncelikle -Setup.exe ile biten kurulum paketini ara
        for asset in assets:
            if asset.name.lower().endswith("-setup.exe"):
                return asset
        # Alternatif olarak herhangi bir .exe
        for asset in assets:
            if asset.name.lower().endswith(".exe") and not asset.name.lower().endswith(".zip"):
                return asset

    elif dist_type == DistributionType.PORTABLE:
        # Öncelikle -Windows-Portable.zip dosyasını ara
        for asset in assets:
            if "portable" in asset.name.lower() and asset.name.lower().endswith(".zip"):
                return asset
        # Alternatif olarak herhangi bir .zip
        for asset in assets:
            if asset.name.lower().endswith(".zip"):
                return asset

    else:  # DEV
        for asset in assets:
            if asset.name.lower().endswith("-setup.exe"):
                return asset
        for asset in assets:
            if "portable" in asset.name.lower() and asset.name.lower().endswith(".zip"):
                return asset

    return assets[0] if assets else None


def check_for_updates(
    current_version: str = __version__,
    repo: str = DEFAULT_REPO,
    dist_type: Optional[DistributionType] = None,
    timeout: int = 8,
) -> Tuple[bool, Optional[ReleaseInfo], Optional[str]]:
    """Query GitHub Releases API and return (has_update, release_info, error_message)."""
    if dist_type is None:
        dist_type = detect_distribution_type()

    url = GITHUB_API_LATEST_RELEASE.format(repo=repo)
    headers = {
        "User-Agent": "Kast-Studio-Updater",
        "Accept": "application/vnd.github.v3+json",
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            return False, None, "GitHub API istek sınırı aşıldı (Lütfen daha sonra tekrar deneyin)."
        if exc.code == 404:
            return False, None, f"GitHub sürüm sayfası bulunamadı ({repo})."
        return False, None, f"GitHub API hatası (HTTP {exc.code}): {exc.reason}"
    except Exception as exc:
        return False, None, f"Ağ bağlantı hatası: {str(exc)}"

    tag_name = payload.get("tag_name", "")
    version_clean = tag_name.lstrip("vV")
    title = payload.get("name") or f"Kast v{version_clean}"
    body = payload.get("body", "")
    html_url = payload.get("html_url", "")

    asset_list: List[ReleaseAssetInfo] = []
    for item in payload.get("assets", []):
        asset_list.append(
            ReleaseAssetInfo(
                name=item.get("name", ""),
                download_url=item.get("browser_download_url", ""),
                size=item.get("size", 0),
            )
        )

    target_asset = select_target_asset(asset_list, dist_type)

    release_info = ReleaseInfo(
        tag_name=tag_name,
        version=version_clean,
        title=title,
        body=body,
        html_url=html_url,
        assets=asset_list,
        target_asset=target_asset,
    )

    has_update = is_newer_version(version_clean, current_version)
    return has_update, release_info, None


def download_release_asset(
    asset_url: str,
    dest_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    chunk_size: int = 65536,
) -> None:
    """Download release asset with progress tracking."""
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    req = urllib.request.Request(asset_url, headers={"User-Agent": "Kast-Studio-Updater"})

    with urllib.request.urlopen(req, timeout=30) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)


def generate_portable_updater_script(
    app_dir: str,
    staged_dir: str,
    target_exe_name: str = "KastStudio.exe",
    current_pid: Optional[int] = None,
) -> str:
    """Generate a batch script that waits for current process to exit, replaces files, and restarts app."""
    pid = current_pid if current_pid is not None else os.getpid()
    script = f"""@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PID={pid}"
set "APP_DIR={app_dir}"
set "STAGE_DIR={staged_dir}"
set "EXE_NAME={target_exe_name}"

echo Kast Studio guncelleniyor, lutfen bekleyin...

:WAIT_LOOP
tasklist /fi "PID eq %PID%" 2>nul | find "%PID%" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAIT_LOOP
)

rem Dosyalari robocopy ile hedef dizine tasi ve uzerine yaz
robocopy "%STAGE_DIR%" "%APP_DIR%" /E /IS /IT /NP /NJH /NJS >nul
if errorlevel 8 (
    echo Robocopy uyarisi, xcopy ile tamamlanıyor...
    xcopy "%STAGE_DIR%\\*" "%APP_DIR%\\" /Y /E /Q >nul
)

rem Guncellenen uygulamayi baslat
start "" "%APP_DIR%\\%EXE_NAME%"

rem Gecici dosyalari temizle
rmdir /s /q "%STAGE_DIR%" 2>nul
exit
"""
    return script


def launch_installer_and_exit(installer_path: str) -> None:
    """Launch Inno Setup installer detached and terminate current process safely."""
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([installer_path], creationflags=flags, close_fds=True)
    else:
        subprocess.Popen([installer_path])
    sys.exit(0)


def launch_portable_updater_and_exit(script_path: str) -> None:
    """Launch portable updater batch script detached and terminate current process safely."""
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(["cmd.exe", "/c", script_path], creationflags=flags, close_fds=True)
    else:
        subprocess.Popen(["bash", script_path])
    sys.exit(0)
```

- [ ] **Step 4: Testleri çalıştır ve doğrula**

Run: `.venv/bin/pytest tests/test_updater.py -v`
Expected: PASS (All tests passed)

- [ ] **Step 5: Commit**

```bash
git add src/updater.py tests/test_updater.py
git commit -m "feat(updater): add update detection engine, github client and installer handoff"
```

---

### Task 3: PySide6 Arka Plan İş Parçacıkları ve Arayüz Pencereleri (`src/updater_gui.py`)

**Files:**
- Create: `src/updater_gui.py`
- Create: `tests/test_updater_gui.py`

**Interfaces:**
- Consumes: `src.updater`, `src.gui.StudioTheme`, `PySide6.QtCore.QThread`, `PySide6.QtWidgets.QDialog`
- Produces:
  - `class UpdateCheckWorker(QThread)`:
    - Signals: `check_finished = Signal(bool, object, str)` # (has_update, release_info, error_msg)
  - `class UpdateDownloadWorker(QThread)`:
    - Signals: `progress = Signal(int, int)`, `download_finished = Signal(str)`, `error = Signal(str)`
  - `class UpdateNotificationDialog(QDialog)`:
    - Displays version diff, package name, size, release notes markdown.
    - Buttons: "Şimdi Güncelle" (`Accepted`), "Daha Sonra" (`Rejected`), "GitHub'da Aç".
  - `class UpdateDownloadDialog(QDialog)`:
    - Modal download progress bar (% and MB format).
    - Automatically stages update and executes `launch_installer_and_exit` or `launch_portable_updater_and_exit`.

- [ ] **Step 1: Updater GUI testlerini yaz (`tests/test_updater_gui.py`)**

```python
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.updater import DistributionType, ReleaseAssetInfo, ReleaseInfo
from src.updater_gui import (
    UpdateCheckWorker,
    UpdateNotificationDialog,
    UpdateDownloadDialog,
)


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def test_update_check_worker_signal_emission(qapp):
    """UpdateCheckWorker arka planda kontrol yapıp check_finished sinyali yayar."""
    worker = UpdateCheckWorker(current_version="2.1.1", dist_type=DistributionType.SETUP)
    
    mock_rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast v2.2.0",
        body="Yeni özellikler",
        html_url="https://github.com/umutaktepe/Kast/releases/tag/v2.2.0",
        assets=[ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://url/setup.exe", 1000)],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://url/setup.exe", 1000),
    )

    results = []
    worker.check_finished.connect(lambda has_up, rel, err: results.append((has_up, rel, err)))

    with patch("src.updater_gui.check_for_updates", return_value=(True, mock_rel, None)):
        worker.run()

    assert len(results) == 1
    assert results[0][0] is True
    assert results[0][1].version == "2.2.0"
    assert results[0][2] is None


def test_update_notification_dialog_ui(qapp):
    """UpdateNotificationDialog gerekli etiketleri, sürüm bilgilerini ve butonları barındırır."""
    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="## Sürüm Notları\n- Hızlı diyalog işleme\n- Yeni arayüz",
        html_url="https://github.com/umutaktepe/Kast/releases/tag/v2.2.0",
        assets=[],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://url/setup.exe", 67108864),
    )

    dialog = UpdateNotificationDialog(
        current_version="2.1.1",
        release_info=rel,
        dist_type=DistributionType.SETUP
    )

    assert "v2.2.0" in dialog.windowTitle()
    assert "2.1.1" in dialog.lbl_version_diff.text()
    assert "2.2.0" in dialog.lbl_version_diff.text()
    assert "64.0 MB" in dialog.lbl_asset_info.text()
    assert "Hızlı diyalog işleme" in dialog.txt_notes.toPlainText()
    assert dialog.btn_update.text() == "⬇️  Şimdi Güncelle"
    assert dialog.btn_later.text() == "Daha Sonra"
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `.venv/bin/pytest tests/test_updater_gui.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.updater_gui'`

- [ ] **Step 3: `src/updater_gui.py` modülünü yaz**

`src/updater_gui.py`:
```python
"""PySide6 Qt6 GUI widgets and worker threads for Kast in-app updater."""

import os
import shutil
import sys
import tempfile
from typing import Optional
import webbrowser
import zipfile

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui import StudioTheme
from src.updater import (
    DistributionType,
    ReleaseInfo,
    check_for_updates,
    download_release_asset,
    generate_portable_updater_script,
    launch_installer_and_exit,
    launch_portable_updater_and_exit,
)
from src.version import __version__


class UpdateCheckWorker(QThread):
    """Background worker thread to query GitHub Releases without freezing the GUI."""
    check_finished = Signal(bool, object, str)  # (has_update, release_info, error_msg)

    def __init__(
        self,
        current_version: str = __version__,
        dist_type: Optional[DistributionType] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self.dist_type = dist_type

    def run(self) -> None:
        has_update, rel_info, err = check_for_updates(
            current_version=self.current_version,
            dist_type=self.dist_type,
        )
        self.check_finished.emit(has_update, rel_info, err or "")


class UpdateDownloadWorker(QThread):
    """Background worker thread to download update asset with chunked progress."""
    progress = Signal(int, int)  # (downloaded_bytes, total_bytes)
    download_finished = Signal(str)  # dest_path
    error = Signal(str)

    def __init__(self, asset_url: str, dest_path: str, parent=None) -> None:
        super().__init__(parent)
        self.asset_url = asset_url
        self.dest_path = dest_path

    def run(self) -> None:
        try:
            def on_progress(dl: int, total: int):
                self.progress.emit(dl, total)

            download_release_asset(
                self.asset_url,
                self.dest_path,
                progress_callback=on_progress,
            )
            self.download_finished.emit(self.dest_path)
        except Exception as exc:
            self.error.emit(str(exc))


class UpdateNotificationDialog(QDialog):
    """Studio-grade dark styled popup announcing a new release."""

    def __init__(
        self,
        current_version: str,
        release_info: ReleaseInfo,
        dist_type: DistributionType,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self.release_info = release_info
        self.dist_type = dist_type

        self.setWindowTitle(f"Kast Studio Güncellemesi Mevcut — v{release_info.version}")
        self.setFixedSize(540, 420)
        self.setStyleSheet(StudioTheme.get_stylesheet())

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header Title
        title_box = QHBoxLayout()
        self.lbl_title = QLabel("🎉  Yeni Bir Sürüm Yayında!")
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        title_box.addWidget(self.lbl_title)
        title_box.addStretch()

        dist_label = "Kurulum (Setup)" if self.dist_type == DistributionType.SETUP else "Taşınabilir (Portable)"
        self.badge_dist = QLabel(f"● {dist_label}")
        self.badge_dist.setStyleSheet("""
            background-color: #0f293a;
            border: 1px solid #084c61;
            color: #38bdf8;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)
        title_box.addWidget(self.badge_dist)
        layout.addLayout(title_box)

        # Version diff and Asset info
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(4)

        self.lbl_version_diff = QLabel(
            f"Mevcut Sürüm: <b>v{self.current_version}</b>  ➔  Yeni Sürüm: <b style='color:#10b981;'>v{self.release_info.version}</b>"
        )
        self.lbl_version_diff.setStyleSheet("font-size: 13px; color: #f8fafc;")

        asset_name = self.release_info.target_asset.name if self.release_info.target_asset else "Paket"
        asset_size_mb = (self.release_info.target_asset.size / (1024 * 1024)) if self.release_info.target_asset else 0.0
        self.lbl_asset_info = QLabel(f"Paket: {asset_name} ({asset_size_mb:.1f} MB)")
        self.lbl_asset_info.setStyleSheet("font-size: 12px; color: #94a3b8;")

        meta_layout.addWidget(self.lbl_version_diff)
        meta_layout.addWidget(self.lbl_asset_info)
        layout.addLayout(meta_layout)

        # Release Notes Label & Text
        lbl_notes = QLabel("Sürüm Notları:")
        lbl_notes.setStyleSheet("font-size: 12px; font-weight: bold; color: #cbd5e1;")
        layout.addWidget(lbl_notes)

        self.txt_notes = QTextEdit()
        self.txt_notes.setReadOnly(True)
        self.txt_notes.setPlainText(self.release_info.body or "Ayrıntılı sürüm notu bulunmuyor.")
        self.txt_notes.setStyleSheet("""
            QTextEdit {
                background-color: #080c14;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #cbd5e1;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.txt_notes, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_web = QPushButton("🌐  GitHub'da Gör")
        self.btn_web.setStyleSheet("""
            background-color: #162033;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #cbd5e1;
            padding: 8px 14px;
            font-weight: 600;
        """)
        self.btn_web.clicked.connect(self._open_web)

        self.btn_later = QPushButton("Daha Sonra")
        self.btn_later.setStyleSheet("""
            background-color: #162033;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #94a3b8;
            padding: 8px 14px;
            font-weight: 600;
        """)
        self.btn_later.clicked.connect(self.reject)

        self.btn_update = QPushButton("⬇️  Şimdi Güncelle")
        self.btn_update.setObjectName("btn-primary")
        self.btn_update.setFixedHeight(36)
        self.btn_update.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_web)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_later)
        btn_layout.addWidget(self.btn_update)
        layout.addLayout(btn_layout)

    def _open_web(self) -> None:
        if self.release_info.html_url:
            webbrowser.open(self.release_info.html_url)


class UpdateDownloadDialog(QDialog):
    """Modal dialog displaying download progress and safely triggering installation handoff."""

    def __init__(
        self,
        release_info: ReleaseInfo,
        dist_type: DistributionType,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.release_info = release_info
        self.dist_type = dist_type
        self.worker: Optional[UpdateDownloadWorker] = None

        self.setWindowTitle("Güncelleme İndiriliyor")
        self.setFixedSize(480, 200)
        self.setStyleSheet(StudioTheme.get_stylesheet())

        self._init_ui()
        self._start_download()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        self.lbl_status = QLabel("İndirme başlatılıyor...")
        self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_meta = QLabel("0 MB / 0 MB (%0)")
        self.lbl_meta.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(self.lbl_meta)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("İptal Et")
        self.btn_cancel.setStyleSheet("""
            background-color: #162033;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #cbd5e1;
            padding: 6px 14px;
        """)
        self.btn_cancel.clicked.connect(self._cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _start_download(self) -> None:
        if not self.release_info.target_asset:
            self.lbl_status.setText("Hata: İndirilecek dosya bulunamadı.")
            return

        temp_dir = os.path.join(tempfile.gettempdir(), "KastUpdate")
        os.makedirs(temp_dir, exist_ok=True)
        dest_file = os.path.join(temp_dir, self.release_info.target_asset.name)

        self.worker = UpdateDownloadWorker(
            asset_url=self.release_info.target_asset.download_url,
            dest_path=dest_file,
            parent=self,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.download_finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    @Slot(int, int)
    def _on_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            pct = int((downloaded / total) * 100)
            self.progress_bar.setValue(pct)
            dl_mb = downloaded / (1024 * 1024)
            tot_mb = total / (1024 * 1024)
            self.lbl_status.setText("Kast Studio güncellemesi indiriliyor...")
            self.lbl_meta.setText(f"{dl_mb:.1f} MB / {tot_mb:.1f} MB (%{pct})")
        else:
            dl_mb = downloaded / (1024 * 1024)
            self.lbl_meta.setText(f"{dl_mb:.1f} MB indirildi...")

    @Slot(str)
    def _on_finished(self, downloaded_path: str) -> None:
        self.lbl_status.setText("İndirme tamamlandı! Kuruluma geçiliyor...")
        self.btn_cancel.setEnabled(False)

        # 1. SETUP Dağıtımı: Setup.exe'yi bağımsız başlat ve uygulamadan çık
        if self.dist_type == DistributionType.SETUP:
            self.lbl_status.setText("Kurulum sihirbazı başlatılıyor...")
            launch_installer_and_exit(downloaded_path)

        # 2. PORTABLE Dağıtımı: ZIP'i aç, geçiş scriptini oluştur ve başlat
        elif self.dist_type == DistributionType.PORTABLE:
            self.lbl_status.setText("Taşınabilir paket ayıklanıyor...")
            temp_dir = os.path.dirname(downloaded_path)
            extracted_dir = os.path.join(temp_dir, "extracted")
            if os.path.exists(extracted_dir):
                shutil.rmtree(extracted_dir, ignore_errors=True)
            os.makedirs(extracted_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(downloaded_path, "r") as zf:
                    zf.extractall(extracted_dir)
            except Exception as e:
                self.lbl_status.setText(f"Ayıklama hatası: {e}")
                self.btn_cancel.setEnabled(True)
                return

            app_dir = os.path.dirname(sys.executable)
            script_content = generate_portable_updater_script(
                app_dir=app_dir,
                staged_dir=extracted_dir,
                target_exe_name="KastStudio.exe",
                current_pid=os.getpid(),
            )
            script_path = os.path.join(temp_dir, "apply_update.bat")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            self.lbl_status.setText("Uygulama yeniden başlatılıyor...")
            launch_portable_updater_and_exit(script_path)

        # 3. DEV Dağıtımı (Geliştirici modu): İndirilen dosyayı aç veya bildir
        else:
            self.lbl_status.setText("Geliştirici modunda dosya indirildi.")
            self.btn_cancel.setText("Kapat")
            self.btn_cancel.setEnabled(True)

    @Slot(str)
    def _on_error(self, err_msg: str) -> None:
        self.lbl_status.setText(f"İndirme Başarısız: {err_msg}")
        self.btn_cancel.setText("Kapat")

    def _cancel(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
        self.reject()
```

- [ ] **Step 4: Testleri çalıştır ve doğrula**

Run: `.venv/bin/pytest tests/test_updater_gui.py -v`
Expected: PASS (All tests passed)

- [ ] **Step 5: Commit**

```bash
git add src/updater_gui.py tests/test_updater_gui.py
git commit -m "feat(updater): add qt6 background workers and studio update dialogs"
```

---

### Task 4: Ana GUI Entegrasyonu, Açılış Otomasyonu ve PyInstaller Uyumu (`src/gui.py`)

**Files:**
- Modify: `src/gui.py`
- Modify: `packaging/kast.spec`
- Modify: `tests/test_gui.py`

**Interfaces:**
- Consumes: `src.updater_gui.UpdateCheckWorker`, `src.updater_gui.UpdateNotificationDialog`, `src.updater_gui.UpdateDownloadDialog`, `src.updater.detect_distribution_type`, `PySide6.QtCore.QTimer`
- Produces:
  - Header'da "🔄 Güncellemeleri Denetle" (`btn_check_updates`) butonu
  - `KastStudioWindow._auto_check_updates()` metodu (açılıştan 1.5 sn sonra tetiklenen sessiz kontrol)
  - `KastStudioWindow._manual_check_updates()` metodu (kullanıcı tıkladığında çalışan ve sonuç popup'ı gösteren kontrol)
  - `KastStudioWindow._handle_update_check_result(has_update: bool, rel_info: object, error_msg: str, is_manual: bool)`

- [ ] **Step 1: GUI entegrasyon testlerini ekle (`tests/test_gui.py`)**

```python
def test_gui_update_button_and_handlers_exist(qapp):
    """KastStudioWindow üzerinde güncelleme butonu ve kontrol metotlarının varlığını test eder."""
    from src.gui import KastStudioWindow

    win = KastStudioWindow()
    assert hasattr(win, "btn_check_updates")
    assert "Güncellemeleri Denetle" in win.btn_check_updates.text() or "Güncelleme" in win.btn_check_updates.text()
    assert hasattr(win, "_auto_check_updates")
    assert hasattr(win, "_manual_check_updates")
    assert hasattr(win, "_handle_update_check_result")


def test_gui_auto_update_silent_when_no_update(qapp, monkeypatch):
    """Açılıştaki otomatik kontrolde güncelleme yoksa sessiz kalınır (diyalog açılmaz)."""
    from src.gui import KastStudioWindow

    win = KastStudioWindow()
    opened_dialogs = []
    monkeypatch.setattr("src.gui.UpdateNotificationDialog.exec", lambda self: opened_dialogs.append("opened"))

    win._handle_update_check_result(has_update=False, release_info=None, error_msg="", is_manual=False)
    assert len(opened_dialogs) == 0


def test_gui_manual_update_informs_user_when_latest(qapp, monkeypatch):
    """Manuel güncelleme sorgusunda en güncel sürümdeyse bilgi mesajı gösterilir."""
    from src.gui import KastStudioWindow

    win = KastStudioWindow()
    info_calls = []
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", lambda parent, title, text: info_calls.append((title, text)))

    win._handle_update_check_result(has_update=False, release_info=None, error_msg="", is_manual=True)
    assert len(info_calls) == 1
    assert "Güncel" in info_calls[0][1] or "güncel" in info_calls[0][1]
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `.venv/bin/pytest tests/test_gui.py -k "test_gui_update" -v`
Expected: FAIL with `AttributeError: 'KastStudioWindow' object has no attribute 'btn_check_updates'`

- [ ] **Step 3: `src/gui.py` ve `packaging/kast.spec` dosyalarını güncelle**

`src/gui.py` içine importları ekle:
```python
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox
from src.updater import detect_distribution_type
from src.updater_gui import (
    UpdateCheckWorker,
    UpdateNotificationDialog,
    UpdateDownloadDialog,
)
from src.version import __version__
```

`KastStudioWindow._init_ui()` içindeki `header_layout` bölümüne "🔄 Güncellemeleri Denetle" butonunu ekle:
```python
        # Güncelleme Kontrol Butonu
        self.btn_check_updates = QPushButton("🔄  Güncellemeleri Denetle")
        self.btn_check_updates.setStyleSheet("""
            QPushButton {
                background-color: #0f1c2e;
                border: 1px solid #1e3a5f;
                color: #94a3b8;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #162a45;
                color: #38bdf8;
                border-color: #38bdf8;
            }
        """)
        self.btn_check_updates.clicked.connect(self._manual_check_updates)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_check_updates, alignment=Qt.AlignTop | Qt.AlignRight)
        header_layout.addWidget(self.lbl_badge, alignment=Qt.AlignTop | Qt.AlignRight)
```

`KastStudioWindow.__init__` sonuna otomatik kontrolü planla:
```python
        # Başlangıçtan 1.5 sn sonra sessiz otomatik güncelleme kontrolü
        QTimer.singleShot(1500, self._auto_check_updates)
```

`KastStudioWindow` sınıfına kontrol metotlarını ekle:
```python
    def _auto_check_updates(self) -> None:
        """Perform a silent background update check on application startup."""
        self._start_update_check(is_manual=False)

    def _manual_check_updates(self) -> None:
        """Triggered by the user clicking the Check Updates button."""
        self.btn_check_updates.setEnabled(False)
        self.btn_check_updates.setText("🔄  Denetleniyor...")
        self._start_update_check(is_manual=True)

    def _start_update_check(self, is_manual: bool) -> None:
        dist_type = detect_distribution_type()
        self.update_worker = UpdateCheckWorker(
            current_version=__version__,
            dist_type=dist_type,
            parent=self,
        )
        self.update_worker.check_finished.connect(
            lambda has_up, rel, err: self._handle_update_check_result(has_up, rel, err, is_manual)
        )
        self.update_worker.start()

    def _handle_update_check_result(
        self,
        has_update: bool,
        release_info: object,
        error_msg: str,
        is_manual: bool,
    ) -> None:
        if is_manual:
            self.btn_check_updates.setEnabled(True)
            self.btn_check_updates.setText("🔄  Güncellemeleri Denetle")

        if error_msg:
            if is_manual:
                QMessageBox.warning(
                    self,
                    "Güncelleme Denetimi",
                    f"Güncellemeler denetlenirken bir sorun oluştu:\n{error_msg}",
                )
            return

        if has_update and release_info:
            dist_type = detect_distribution_type()
            dialog = UpdateNotificationDialog(
                current_version=__version__,
                release_info=release_info,
                dist_type=dist_type,
                parent=self,
            )
            if dialog.exec() == QDialog.Accepted:
                download_dialog = UpdateDownloadDialog(
                    release_info=release_info,
                    dist_type=dist_type,
                    parent=self,
                )
                download_dialog.exec()
        else:
            if is_manual:
                QMessageBox.information(
                    self,
                    "Kast Studio Güncel",
                    f"Harika! En güncel Kast Studio sürümünü (v{__version__}) kullanıyorsunuz.",
                )
```

`packaging/kast.spec` hiddenimports listesine yeni modülleri ekle:
```python
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "docx",
    "pdfplumber",
    "pypdf",
    "PIL",
    "src.version",
    "src.updater",
    "src.updater_gui",
]
```

- [ ] **Step 4: Testleri çalıştır ve doğrula**

Run: `.venv/bin/pytest tests/test_gui.py tests/test_updater.py tests/test_updater_gui.py -v`
Expected: PASS (All tests passed)

- [ ] **Step 5: Commit**

```bash
git add src/gui.py packaging/kast.spec tests/test_gui.py
git commit -m "feat(gui): integrate check updates button and silent startup background check"
```

---

### Task 5: Living Architecture Dokümantasyonu (ADR-008, Atomic Page, MOC & Log)

**Files:**
- Create: `docs/kast-app-wiki/architecture-decisions/adr-008-in-app-github-release-updater.md`
- Create: `docs/kast-app-wiki/interfaces-and-runtime/github-release-updater.md`
- Modify: `docs/kast-app-wiki/index.md`
- Modify: `docs/kast-app-wiki/log.md`

**Interfaces:**
- Consumes: `AGENTS.md` LLM Wiki / Living Architecture standartları
- Produces: Obsidian uyumlu wikilink ağı (`[[adr-008-in-app-github-release-updater]]`, `[[github-release-updater]]`)

- [ ] **Step 1: ADR-008 mimari karar kaydını oluştur (`adr-008-in-app-github-release-updater.md`)**
  - Zorunlu bölümler: Bağlam, Karar, Alternatifler, Sonuçlar ve Etkiler, İlgili Sayfalar.
  - Setup ve Portable ayrımı, Windows OS ikili kilitleme problemi ve detached script çözümü detaylandırılır.

- [ ] **Step 2: Atomik wiki sayfasını oluştur (`github-release-updater.md`)**
  - `src/version.py`, `src/updater.py`, `src/updater_gui.py` bileşen mimarisi, thread yaşam döngüsü ve indirme/kurma aşamaları açıklanır.

- [ ] **Step 3: Fihristi (`index.md`) ve Günlüğü (`log.md`) güncelle**
  - `index.md` MOC içine ADR-008 ve `github-release-updater` wikilinklerini ekle.
  - `log.md` dosyasına standart şablonda kronolojik işlem kaydı düş.

- [ ] **Step 4: Wiki link ve grafik bütünlüğünü doğrula**
  - Hiçbir kırık `[[wikilink]]` veya yetim sayfa kalmadığını kontrol et.

- [ ] **Step 5: Commit**

```bash
git add docs/kast-app-wiki/
git commit -m "docs(wiki): record adr-008 and github release updater architecture"
```

---

### Task 6: Tam Regresyon ve Sistem Doğrulama Testi

**Files:**
- Run: Tüm test süiti (`tests/`)

- [ ] **Step 1: Tüm test süitini çalıştır**

Run: `.venv/bin/pytest tests/ -v`
Expected: 180+ tests passed, 0 failed.

- [ ] **Step 2: Temiz çalışma ağacını doğrula**

Run: `git status`
Expected: Working tree clean.

---

## Plan Self-Review & Integrity Check

1. **Spec Coverage:**
   - GitHub Releases versiyon kontrolü? -> Evet (Task 1 & Task 2: `check_for_updates`).
   - "Check updates" butonu? -> Evet (Task 4: `btn_check_updates` ve `_manual_check_updates`).
   - Her açılışta otomatik sorgulama? -> Evet (Task 4: `QTimer.singleShot(1500, self._auto_check_updates)`).
   - Güncelleme varsa popup, isterse güncellesin istemezse ignor etsin? -> Evet (Task 3: `UpdateNotificationDialog`).
   - Yalnızca GUI için mi? -> Evet (Task 3 & 4, CLI/TUI dokunulmadı).
   - Windows için Setup (.exe) ise setup, Portable (.zip) ise portable kontrolü? -> Evet (Task 2: `detect_distribution_type` ve `select_target_asset`).
   - İndirme sonrası kurma işleminin sorunsuz opere edilmesi? -> Evet (Task 2 & 3: Setup için bağımsız detached installer, Portable için PID-beklemeli robocopy scripti ve temiz kapatma).
2. **No Placeholders:**
   - "TBD", "TODO", "benzer adımlar" vb. hiçbir belirsizlik bulunmamaktadır. Tüm fonksiyon ve test kodları eksiksiz yazılmıştır.
3. **Type and Interface Consistency:**
   - `parse_version`, `is_newer_version`, `DistributionType`, `ReleaseInfo`, `check_for_updates`, `UpdateCheckWorker`, `UpdateNotificationDialog`, `UpdateDownloadDialog` imzaları ve sinyalleri tüm adımlarda birebir tutarlıdır.
