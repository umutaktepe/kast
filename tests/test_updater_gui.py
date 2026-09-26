import os
import tempfile
import zipfile
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.updater import DistributionType, ReleaseAssetInfo, ReleaseInfo
from src.updater_gui import (
    UpdateCheckWorker,
    UpdateDownloadWorker,
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
    assert results[0][2] == ""


def test_update_check_worker_with_error(qapp):
    """UpdateCheckWorker hata durumunda hata mesajını sinyal olarak yayar."""
    worker = UpdateCheckWorker(current_version="2.1.1", dist_type=DistributionType.SETUP)

    results = []
    worker.check_finished.connect(lambda has_up, rel, err: results.append((has_up, rel, err)))

    with patch("src.updater_gui.check_for_updates", return_value=(False, None, "Ağ bağlantı hatası")):
        worker.run()

    assert len(results) == 1
    assert results[0][0] is False
    assert results[0][1] is None
    assert results[0][2] == "Ağ bağlantı hatası"


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
        dist_type=DistributionType.SETUP,
    )

    assert "v2.2.0" in dialog.windowTitle()
    assert "2.1.1" in dialog.lbl_version_diff.text()
    assert "2.2.0" in dialog.lbl_version_diff.text()
    assert "64.0 MB" in dialog.lbl_asset_info.text()
    assert "Hızlı diyalog işleme" in dialog.txt_notes.toPlainText()
    assert "Şimdi Güncelle" in dialog.btn_update.text()
    assert dialog.btn_later.text() == "Daha Sonra"
    assert "Kurulum" in dialog.badge_dist.text()


def test_update_notification_dialog_portable_badge_and_open_web(qapp):
    """UpdateNotificationDialog portable rozetini ve web açma butonunu test eder."""
    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="https://github.com/umutaktepe/Kast/releases/tag/v2.2.0",
        assets=[],
        target_asset=None,
    )

    dialog = UpdateNotificationDialog(
        current_version="2.1.1",
        release_info=rel,
        dist_type=DistributionType.PORTABLE,
    )

    assert "Taşınabilir" in dialog.badge_dist.text()
    assert "Paket (0.0 MB)" in dialog.lbl_asset_info.text()
    assert "Ayrıntılı sürüm notu bulunmuyor." in dialog.txt_notes.toPlainText()

    with patch("webbrowser.open") as mock_open:
        dialog._open_web()
        mock_open.assert_called_once_with("https://github.com/umutaktepe/Kast/releases/tag/v2.2.0")


def test_update_download_worker(qapp, tmp_path):
    """UpdateDownloadWorker indirme işlemini başlatır ve sinyalleri yayar."""
    dest_file = str(tmp_path / "test.zip")
    worker = UpdateDownloadWorker("https://url/test.zip", dest_file)

    progress_events = []
    finished_events = []
    worker.progress.connect(lambda d, t: progress_events.append((d, t)))
    worker.download_finished.connect(lambda path: finished_events.append(path))

    def fake_download(url, dest, progress_callback=None, chunk_size=65536):
        if progress_callback:
            progress_callback(500, 1000)
            progress_callback(1000, 1000)

    with patch("src.updater_gui.download_release_asset", side_effect=fake_download):
        worker.run()

    assert len(progress_events) == 2
    assert progress_events[0] == (500, 1000)
    assert progress_events[1] == (1000, 1000)
    assert len(finished_events) == 1
    assert finished_events[0] == dest_file


def test_update_download_worker_error(qapp, tmp_path):
    """UpdateDownloadWorker indirme hatasında error sinyali yayar."""
    dest_file = str(tmp_path / "test.zip")
    worker = UpdateDownloadWorker("https://url/test.zip", dest_file)

    error_events = []
    worker.error.connect(lambda msg: error_events.append(msg))

    with patch("src.updater_gui.download_release_asset", side_effect=RuntimeError("İndirme koptu")):
        worker.run()

    assert len(error_events) == 1
    assert "İndirme koptu" in error_events[0]


def test_update_download_dialog_ui_and_progress(qapp):
    """UpdateDownloadDialog arayüz elemanlarını ve progress güncellemelerini test eder."""
    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="https://github.com/umutaktepe/Kast/releases/tag/v2.2.0",
        assets=[],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://url/setup.exe", 10485760),
    )

    with patch.object(UpdateDownloadWorker, "start"):
        dialog = UpdateDownloadDialog(rel, DistributionType.SETUP)
        assert dialog.worker is not None
        assert dialog.progress_bar.value() == 0

        # Normal progress
        dialog._on_progress(5242880, 10485760)
        assert dialog.progress_bar.value() == 50
        assert "5.0 MB / 10.0 MB (%50)" in dialog.lbl_meta.text()

        # Total bilinmiyor (0)
        dialog._on_progress(2097152, 0)
        assert "2.0 MB indirildi..." in dialog.lbl_meta.text()

        # Error
        dialog._on_error("Ağ zaman aşımı")
        assert "İndirme Başarısız: Ağ zaman aşımı" in dialog.lbl_status.text()
        assert dialog.btn_cancel.text() == "Kapat"


def test_update_download_dialog_missing_asset(qapp):
    """UpdateDownloadDialog target_asset olmadığında hata mesajı gösterir."""
    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="https://github.com/umutaktepe/Kast/releases/tag/v2.2.0",
        assets=[],
        target_asset=None,
    )

    dialog = UpdateDownloadDialog(rel, DistributionType.SETUP)
    assert dialog.worker is None
    assert "Hata: İndirilecek dosya bulunamadı." in dialog.lbl_status.text()


def test_update_download_dialog_cancel(qapp):
    """UpdateDownloadDialog iptal edildiğinde worker'ı durdurur ve reddeder."""
    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="",
        assets=[],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://url/setup.exe", 100),
    )

    with patch.object(UpdateDownloadWorker, "start"):
        dialog = UpdateDownloadDialog(rel, DistributionType.SETUP)
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        dialog.worker = mock_worker

        with patch.object(dialog, "reject") as mock_reject:
            dialog._cancel()
            mock_worker.terminate.assert_called_once()
            mock_reject.assert_called_once()


def test_update_download_dialog_finished_setup(qapp):
    """UpdateDownloadDialog SETUP modunda kurulumu başlatır."""
    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="",
        assets=[],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://url/setup.exe", 100),
    )

    with patch.object(UpdateDownloadWorker, "start"):
        dialog = UpdateDownloadDialog(rel, DistributionType.SETUP)
        with patch("src.updater_gui.launch_installer_and_exit") as mock_launch:
            dialog._on_finished("/tmp/Kast-v2.2.0-Setup.exe")
            mock_launch.assert_called_once_with("/tmp/Kast-v2.2.0-Setup.exe")


def test_update_download_dialog_finished_portable(qapp, tmp_path):
    """UpdateDownloadDialog PORTABLE modunda paketi ayıklar ve scripti başlatır."""
    # Test için geçerli bir zip dosyası hazırla
    zip_path = tmp_path / "portable.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("KastStudio.exe", "fake exe binary")

    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="",
        assets=[],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Portable.zip", "https://url/portable.zip", 100),
    )

    with patch.object(UpdateDownloadWorker, "start"):
        dialog = UpdateDownloadDialog(rel, DistributionType.PORTABLE)
        with patch("src.updater_gui.launch_portable_updater_and_exit") as mock_launch:
            dialog._on_finished(str(zip_path))
            mock_launch.assert_called_once()
            script_arg = mock_launch.call_args[0][0]
            assert script_arg.endswith("apply_update.bat")
            assert os.path.exists(script_arg)


def test_update_download_dialog_finished_portable_corrupt_zip(qapp, tmp_path):
    """UpdateDownloadDialog bozuk zip dosyasında ayıklama hatasını gösterir."""
    corrupt_zip = tmp_path / "corrupt.zip"
    corrupt_zip.write_text("not a real zip")

    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="",
        assets=[],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Portable.zip", "https://url/portable.zip", 100),
    )

    with patch.object(UpdateDownloadWorker, "start"):
        dialog = UpdateDownloadDialog(rel, DistributionType.PORTABLE)
        dialog._on_finished(str(corrupt_zip))
        assert "Ayıklama hatası:" in dialog.lbl_status.text()
        assert dialog.btn_cancel.isEnabled() is True


def test_update_download_dialog_finished_dev(qapp, tmp_path):
    """UpdateDownloadDialog DEV modunda bilgilendirme mesajı gösterir."""
    rel = ReleaseInfo(
        tag_name="v2.2.0",
        version="2.2.0",
        title="Kast Studio v2.2.0",
        body="",
        html_url="",
        assets=[],
        target_asset=ReleaseAssetInfo("Kast-v2.2.0-Setup.exe", "https://url/setup.exe", 100),
    )

    with patch.object(UpdateDownloadWorker, "start"):
        dialog = UpdateDownloadDialog(rel, DistributionType.DEV)
        dialog._on_finished(str(tmp_path / "dummy.exe"))
        assert "Geliştirici modunda dosya indirildi." in dialog.lbl_status.text()
        assert dialog.btn_cancel.text() == "Kapat"
        assert dialog.btn_cancel.isEnabled() is True
