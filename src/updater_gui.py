"""PySide6 Qt6 GUI widgets and worker threads for Kast in-app updater."""

import os
import shutil
import sys
import tempfile
from typing import Optional
import webbrowser
import zipfile

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
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


def create_download_icon(color: str = "#031726", size: int = 14) -> QIcon:
    """Create a crisp vector download arrow icon."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)

    # Downward arrow stem
    mid = size / 2.0
    p.drawLine(mid, 2.0, mid, size - 5.0)

    # Downward arrow head
    arrow = QPainterPath()
    arrow.moveTo(mid - 3.5, size - 7.5)
    arrow.lineTo(mid, size - 4.0)
    arrow.lineTo(mid + 3.5, size - 7.5)
    p.drawPath(arrow)

    # Base tray line
    tray = QPainterPath()
    tray.moveTo(2.0, size - 5.0)
    tray.lineTo(2.0, size - 2.0)
    tray.lineTo(size - 2.0, size - 2.0)
    tray.lineTo(size - 2.0, size - 5.0)
    p.drawPath(tray)

    p.end()
    return QIcon(pix)


def create_external_link_icon(color: str = "#cbd5e1", size: int = 14) -> QIcon:
    """Create a crisp vector external link / web icon."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)

    # Diagonal arrow pointing top-right
    p.drawLine(size - 8.0, 8.0, size - 2.5, 2.5)
    # Arrow head
    head = QPainterPath()
    head.moveTo(size - 6.0, 2.5)
    head.lineTo(size - 2.5, 2.5)
    head.lineTo(size - 2.5, 6.0)
    p.drawPath(head)

    # Small box on bottom-left
    box = QPainterPath()
    box.moveTo(size - 6.5, 6.0)
    box.lineTo(2.5, 6.0)
    box.lineTo(2.5, size - 2.5)
    box.lineTo(size - 2.5, size - 2.5)
    box.lineTo(size - 2.5, size - 6.5)
    p.drawPath(box)

    p.end()
    return QIcon(pix)


def _get_theme_stylesheet() -> str:
    try:
        from src.gui import StudioTheme
        return StudioTheme.get_stylesheet()
    except (ImportError, AttributeError):
        return ""
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
        try:
            has_update, rel_info, err = check_for_updates(
                current_version=self.current_version,
                dist_type=self.dist_type,
            )
            self.check_finished.emit(has_update, rel_info, err or "")
        except Exception as exc:
            self.check_finished.emit(False, None, f"Güncelleme denetleme hatası: {exc}")


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
        self.setStyleSheet(_get_theme_stylesheet())

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header Title
        title_box = QHBoxLayout()
        self.lbl_title = QLabel("Yeni Bir Sürüm Yayında!")
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        title_box.addWidget(self.lbl_title)
        title_box.addStretch()

        if self.dist_type == DistributionType.SETUP:
            dist_label = "Kurulum (Setup)"
            dist_badge_color = "#38bdf8"
            dist_badge_bg = "#0f293a"
            dist_badge_border = "#084c61"
        elif self.dist_type == DistributionType.PORTABLE:
            dist_label = "Taşınabilir (Portable)"
            dist_badge_color = "#38bdf8"
            dist_badge_bg = "#0f293a"
            dist_badge_border = "#084c61"
        else:
            dist_label = "Geliştirici Sürümü (Dev)"
            dist_badge_color = "#f59e0b"
            dist_badge_bg = "#291e0a"
            dist_badge_border = "#784c0e"

        self.badge_dist = QLabel(f"● {dist_label}")
        self.badge_dist.setStyleSheet(f"""
            background-color: {dist_badge_bg};
            border: 1px solid {dist_badge_border};
            color: {dist_badge_color};
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

        if self.release_info.target_asset:
            asset_name = self.release_info.target_asset.name
            asset_size_mb = self.release_info.target_asset.size / (1024 * 1024)
        else:
            asset_name = "Paket"
            asset_size_mb = 0.0

        self.lbl_asset_info = QLabel(f"Paket: {asset_name} ({asset_size_mb:.1f} MB)")
        self.lbl_asset_info.setStyleSheet("font-size: 12px; color: #94a3b8;")

        meta_layout.addWidget(self.lbl_version_diff)
        meta_layout.addWidget(self.lbl_asset_info)

        if self.dist_type == DistributionType.DEV:
            self.lbl_dev_notice = QLabel("💡 Geliştirici modundasınız. Kaynak kodunuzu terminalden 'git pull' ile güncelleyebilirsiniz.")
            self.lbl_dev_notice.setStyleSheet("font-size: 11px; color: #f59e0b;")
            meta_layout.addWidget(self.lbl_dev_notice)

        layout.addLayout(meta_layout)

        # Release Notes Label & Text
        lbl_notes = QLabel("Sürüm Notları:")
        lbl_notes.setStyleSheet("font-size: 12px; font-weight: bold; color: #cbd5e1;")
        layout.addWidget(lbl_notes)

        self.txt_notes = QTextEdit()
        self.txt_notes.setReadOnly(True)
        notes = self.release_info.body or "Ayrıntılı sürüm notu bulunmuyor."
        if hasattr(self.txt_notes, "setMarkdown"):
            self.txt_notes.setMarkdown(notes)
        else:
            self.txt_notes.setPlainText(notes)
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

        self.btn_web = QPushButton("GitHub'da Gör")
        self.btn_web.setIcon(create_external_link_icon(color="#cbd5e1", size=14))
        self.btn_web.setCursor(Qt.PointingHandCursor)
        self.btn_web.setStyleSheet("""
            QPushButton {
                background-color: #162033;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                padding: 7px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e2e4a;
                border-color: #38bdf8;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0a0f1d;
                border-color: #0284c7;
                color: #38bdf8;
                padding-top: 9px;
                padding-bottom: 5px;
            }
        """)
        self.btn_web.clicked.connect(self._open_web)

        self.btn_later = QPushButton("Daha Sonra")
        self.btn_later.setCursor(Qt.PointingHandCursor)
        self.btn_later.setStyleSheet("""
            QPushButton {
                background-color: #162033;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #94a3b8;
                padding: 7px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e2e4a;
                border-color: #64748b;
                color: #f8fafc;
            }
            QPushButton:pressed {
                background-color: #0a0f1d;
                border-color: #38bdf8;
                color: #38bdf8;
                padding-top: 9px;
                padding-bottom: 5px;
            }
        """)
        self.btn_later.clicked.connect(self.reject)

        self.btn_update = QPushButton("Şimdi Güncelle")
        self.btn_update.setObjectName("btn-primary")
        self.btn_update.setIcon(create_download_icon(color="#031726", size=14))
        self.btn_update.setFixedHeight(36)
        self.btn_update.setCursor(Qt.PointingHandCursor)
        if not self.release_info.target_asset:
            self.btn_update.setEnabled(False)
            self.btn_update.setToolTip("Bu dağıtım türüne uygun paket sürümde bulunmuyor.")
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
        self.setStyleSheet(_get_theme_stylesheet())

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
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #162033;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e2e4a;
                border-color: #f43f5e;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0a0f1d;
                border-color: #be123c;
                color: #f43f5e;
                padding-top: 8px;
                padding-bottom: 4px;
            }
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
            try:
                self.worker.download_finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.worker.terminate()
            self.worker.wait(1000)
        self.reject()

    def closeEvent(self, event) -> None:
        self._cancel()
        event.accept()
