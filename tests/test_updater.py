import pytest
from src.version import __version__, parse_version, is_newer_version


def test_version_string_format():
    """__version__ değişkeninin geçerli semver biçiminde olduğunu doğrular."""
    assert __version__ == "2.1.4"
    assert parse_version(__version__) >= (2, 1, 4)


def test_parse_version_standard_and_prefixed():
    """parse_version fonksiyonunun 'v' önekli ve öneksiz sürümleri doğru ayrıştırdığını doğrular."""
    assert parse_version("2.1.1") == (2, 1, 1)
    assert parse_version("v2.1.1") == (2, 1, 1)
    assert parse_version("v2.2.0") == (2, 2, 0)
    assert parse_version("3.0.0.1") == (3, 0, 0, 1)
    assert parse_version("v1.0") == (1, 0)


def test_is_newer_version_comparison():
    """is_newer_version fonksiyonunun sürüm karşılaştırmasını doğru yaptığını doğrular."""
    assert is_newer_version("2.1.5", "2.1.4") is True
    assert is_newer_version("v2.2.0", "2.1.4") is True
    assert is_newer_version("v3.0.0", "2.1.4") is True
    assert is_newer_version("2.1.4", "2.1.4") is False
    assert is_newer_version("2.1.0", "2.1.4") is False
    assert is_newer_version("v2.0.9", "2.1.4") is False


def test_init_exports_version():
    """src paketinin __version__ sembolünü dışa aktardığını doğrular."""
    import src
    assert hasattr(src, "__version__")
    assert src.__version__ == "2.1.4"


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


def test_check_for_updates_http_errors():
    """HTTP 403, 404 ve 500 hatalarının uygun mesajlarla döndüğünü doğrular."""
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("url", 403, "Forbidden", {}, None)):
        has_update, rel_info, err = check_for_updates()
        assert has_update is False
        assert "istek sınırı" in err

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("url", 404, "Not Found", {}, None)):
        has_update, rel_info, err = check_for_updates()
        assert has_update is False
        assert "bulunamadı" in err

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("url", 500, "Server Error", {}, None)):
        has_update, rel_info, err = check_for_updates()
        assert has_update is False
        assert "HTTP 500" in err


def test_download_release_asset(tmp_path):
    """Varlık indirme ve ilerleme takibini doğrular."""
    from src.updater import download_release_asset

    dest = tmp_path / "sub" / "downloaded.exe"
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Length": "12"}
    mock_resp.read.side_effect = [b"hello ", b"world!", b""]
    mock_resp.__enter__.return_value = mock_resp

    progress_calls = []

    def callback(downloaded, total):
        progress_calls.append((downloaded, total))

    with patch("urllib.request.urlopen", return_value=mock_resp):
        download_release_asset("https://fake.url/file.exe", str(dest), progress_callback=callback, chunk_size=6)

    assert dest.read_bytes() == b"hello world!"
    assert progress_calls == [(6, 12), (12, 12)]


def test_launch_installer_and_exit():
    """Kurulum dosyasının arka planda çalıştırılıp uygulamanın sonlandırıldığını doğrular."""
    from src.updater import launch_installer_and_exit
    with patch("subprocess.Popen") as mock_popen, patch("sys.exit") as mock_exit:
        launch_installer_and_exit("fake_installer.exe")
        mock_popen.assert_called_once()
        mock_exit.assert_called_once_with(0)


def test_launch_portable_updater_and_exit():
    """Taşınabilir betiğin arka planda çalıştırılıp uygulamanın sonlandırıldığını doğrular."""
    from src.updater import launch_portable_updater_and_exit
    with patch("subprocess.Popen") as mock_popen, patch("sys.exit") as mock_exit:
        launch_portable_updater_and_exit("fake_script.bat")
        mock_popen.assert_called_once()
        mock_exit.assert_called_once_with(0)

