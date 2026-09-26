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
            if asset.name.lower().endswith(".exe"):
                return asset
        return None

    elif dist_type == DistributionType.PORTABLE:
        # Öncelikle -Windows-Portable.zip dosyasını ara
        for asset in assets:
            if "portable" in asset.name.lower() and asset.name.lower().endswith(".zip"):
                return asset
        # Alternatif olarak herhangi bir .zip
        for asset in assets:
            if asset.name.lower().endswith(".zip"):
                return asset
        return None

    else:  # DEV
        # Geliştirici modunda: Windows üzerinde Setup, diğer platformlarda Portable önceliklidir
        if sys.platform == "win32":
            for asset in assets:
                if asset.name.lower().endswith("-setup.exe"):
                    return asset
            for asset in assets:
                if "portable" in asset.name.lower() and asset.name.lower().endswith(".zip"):
                    return asset
        else:
            for asset in assets:
                if "portable" in asset.name.lower() and asset.name.lower().endswith(".zip"):
                    return asset
            for asset in assets:
                if asset.name.lower().endswith("-setup.exe"):
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
        try:
            total_size = int(resp.headers.get("Content-Length") or 0)
        except (ValueError, TypeError):
            total_size = 0
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
    clean_app_dir = app_dir.replace("/", "\\").rstrip("\\") if sys.platform == "win32" else app_dir
    clean_stage_dir = staged_dir.replace("/", "\\").rstrip("\\") if sys.platform == "win32" else staged_dir
    script = f"""@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PID={pid}"
set "APP_DIR={clean_app_dir}"
set "STAGE_DIR={clean_stage_dir}"
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
