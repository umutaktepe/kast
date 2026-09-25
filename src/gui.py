import os
import subprocess
import sys
from typing import Dict, Optional

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kast import process_dubbing_file

ROOT_DIR = getattr(sys, "_MEIPASS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class StudioTheme:
    """Mockup-accurate studio-grade dark palette and QSS stylesheets."""

    COLORS: Dict[str, str] = {
        "bg_dark": "#0b0f19",
        "card_bg": "#0f172a",
        "card_tile": "#131f38",
        "card_tile_selected": "#162b4d",
        "border": "#1e293b",
        "border_dashed": "#223554",
        "border_focus": "#38bdf8",
        "text_main": "#f8fafc",
        "text_sub": "#cbd5e1",
        "text_dim": "#64748b",
        "accent_cyan": "#38bdf8",
        "btn_primary": "#00b4d8",
        "btn_primary_hover": "#38bdf8",
        "btn_secondary": "#162033",
        "terminal_bg": "#080c14",
        "badge_bg": "#0f293a",
        "badge_border": "#084c61",
        "accent_green": "#10b981",
        "accent_red": "#f43f5e",
    }

    @classmethod
    def get_stylesheet(cls) -> str:
        c = cls.COLORS
        return f"""
        QMainWindow {{
            background-color: {c["bg_dark"]};
            color: {c["text_main"]};
            font-family: 'Segoe UI', Inter, -apple-system, sans-serif;
            font-size: 13px;
        }}
        QWidget {{
            color: {c["text_main"]};
            font-family: 'Segoe UI', Inter, -apple-system, sans-serif;
        }}
        QFrame#card-panel {{
            background-color: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: 10px;
            padding: 12px 14px;
        }}
        QFrame#tile-option {{
            background-color: {c["card_tile"]};
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 0px;
        }}
        QFrame#tile-option:hover {{
            background-color: #182847;
        }}
        QFrame#tile-option[selected="true"] {{
            background-color: {c["card_tile_selected"]};
            border: 1px solid {c["border_focus"]};
        }}
        QFrame#tile-option:disabled {{
            background-color: #0c1424;
            border: 1px solid transparent;
        }}
        QFrame#tile-option:disabled:hover {{
            background-color: #0c1424;
        }}
        QPushButton#btn-primary {{
            background-color: {c["btn_primary"]};
            color: #031726;
            font-size: 14px;
            font-weight: 800;
            padding: 11px 24px;
            border: none;
            border-radius: 8px;
        }}
        QPushButton#btn-primary:hover {{
            background-color: {c["btn_primary_hover"]};
        }}
        QPushButton#btn-primary:disabled {{
            background-color: #1e293b;
            color: #475569;
        }}
        QPushButton#btn-clear {{
            background-color: {c["btn_secondary"]};
            color: {c["text_sub"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
            padding: 11px 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton#btn-clear:hover {{
            background-color: #1e2e4a;
            border-color: #334155;
            color: #ffffff;
        }}
        QProgressBar {{
            background-color: #111a2e;
            border: none;
            border-radius: 3px;
            text-align: center;
            height: 6px;
        }}
        QProgressBar::chunk {{
            background-color: {c["btn_primary"]};
            border-radius: 3px;
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: {c["terminal_bg"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
            color: #cbd5e1;
            font-family: 'Cascadia Code', 'Consolas', monospace;
            font-size: 12px;
            padding: 12px;
        }}
        QStatusBar {{
            background-color: {c["terminal_bg"]};
            color: {c["text_dim"]};
            border-top: 1px solid #162033;
            font-size: 11px;
        }}
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: {c["bg_dark"]};
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {c["border"]};
            min-height: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c["accent_cyan"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        """


class DropZoneWidget(QFrame):
    """Pixel-perfect modern drag-drop zone supporting single and multi-file workflows."""

    file_selected = Signal(str)
    files_selected = Signal(list)
    validation_error = Signal(str)

    MAX_FILES: int = 25

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._file_paths: list[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("drop-zone")
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 8, 16, 8)

        # 1. Empty State
        self.empty_container = QFrame()
        empty_layout = QVBoxLayout(self.empty_container)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(4)

        # Circular Cloud Icon Container
        self.icon_container = QFrame()
        self.icon_container.setFixedSize(40, 40)
        self.icon_container.setStyleSheet("""
            background-color: #111d33;
            border: 1.5px solid #0284c7;
            border-radius: 20px;
        """)
        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_icon = QLabel("☁↑")
        self.lbl_icon.setStyleSheet("font-size: 16px; color: #38bdf8; font-weight: bold; border: none; background: transparent;")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.lbl_icon)

        self.lbl_prompt = QLabel("Çeviri dosyasını (.docx veya .pdf) buraya sürükleyip bırakın")
        self.lbl_prompt.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc;")
        self.lbl_prompt.setAlignment(Qt.AlignCenter)

        self.lbl_subprompt = QLabel("Microsoft Word veya metin formatlı çeviri PDF'leri desteklenmektedir.")
        self.lbl_subprompt.setStyleSheet("font-size: 11px; color: #64748b;")
        self.lbl_subprompt.setAlignment(Qt.AlignCenter)

        # Format pills row
        pills_layout = QHBoxLayout()
        pills_layout.setAlignment(Qt.AlignCenter)
        pills_layout.setSpacing(8)

        self.badge_docx = QLabel(".DOCX")
        self.badge_docx.setStyleSheet("background-color: #131f38; border: 1px solid #1e293b; color: #94a3b8; font-size: 10px; font-weight: bold; padding: 2px 7px; border-radius: 4px;")
        self.badge_pdf = QLabel(".PDF")
        self.badge_pdf.setStyleSheet("background-color: #131f38; border: 1px solid #1e293b; color: #94a3b8; font-size: 10px; font-weight: bold; padding: 2px 7px; border-radius: 4px;")

        pills_layout.addWidget(self.badge_docx)
        pills_layout.addWidget(self.badge_pdf)

        # Browse Button
        self.btn_browse = QPushButton("☁  Dosya Seç")
        self.btn_browse.setFixedHeight(28)
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #162238;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 20px;
            }
            QPushButton:hover {
                background-color: #1e2e4a;
                border-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.btn_browse.clicked.connect(self._open_file_dialog)

        empty_layout.addWidget(self.icon_container, alignment=Qt.AlignCenter)
        empty_layout.addWidget(self.lbl_prompt)
        empty_layout.addWidget(self.lbl_subprompt)
        empty_layout.addLayout(pills_layout)
        empty_layout.addWidget(self.btn_browse, alignment=Qt.AlignCenter)

        # 2. Loaded State
        self.loaded_container = QFrame()
        self.loaded_container.setVisible(False)
        loaded_layout = QHBoxLayout(self.loaded_container)
        loaded_layout.setAlignment(Qt.AlignCenter)
        loaded_layout.setSpacing(14)

        self.lbl_badge = QLabel("DOCX")
        self.lbl_badge.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 4px;"
        )

        info_box = QVBoxLayout()
        self.lbl_filename = QLabel("")
        self.lbl_filename.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        self.lbl_filesize = QLabel("")
        self.lbl_filesize.setStyleSheet("font-size: 11px; color: #64748b;")
        info_box.addWidget(self.lbl_filename)
        info_box.addWidget(self.lbl_filesize)

        self.btn_remove = QPushButton("✕ Değiştir")
        self.btn_remove.setStyleSheet("background: #f43f5e; color: #ffffff; border: none; padding: 6px 14px; font-weight: bold; border-radius: 6px;")
        self.btn_remove.clicked.connect(self.clear)

        loaded_layout.addWidget(self.lbl_badge)
        loaded_layout.addLayout(info_box)
        loaded_layout.addWidget(self.btn_remove)

        self.main_layout.addWidget(self.empty_container)
        self.main_layout.addWidget(self.loaded_container)

        self._update_border_style(is_hover=False)

    @property
    def _file_path(self) -> Optional[str]:
        return self._file_paths[0] if self._file_paths else None

    @_file_path.setter
    def _file_path(self, val: Optional[str]) -> None:
        if val is None:
            self._file_paths = []
        else:
            self._file_paths = [val]

    def _update_border_style(self, is_hover: bool = False) -> None:
        has_files = bool(self._file_paths)
        border_color = "#38bdf8" if is_hover else ("#223554" if not has_files else "#10b981")
        bg_color = "#111d33" if is_hover else "#0c1424"
        border_type = "dashed" if not has_files else "solid"
        self.setStyleSheet(f"""
            QFrame#drop-zone {{
                background-color: {bg_color};
                border: 1.5px {border_type} {border_color};
                border-radius: 12px;
            }}
        """)

    def _open_file_dialog(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Dublaj Çeviri Dosyaları Seçin (En Fazla 25 Dosya)",
            "",
            "Dublaj Çevirileri (*.docx *.pdf);;Word Belgeleri (*.docx);;PDF Belgeleri (*.pdf);;Tüm Dosyalar (*.*)",
        )
        if file_paths:
            self.set_files(file_paths)

    @classmethod
    def validate_file_paths(cls, paths: list[str]) -> tuple[bool, str, list[str]]:
        """Validate list of file paths according to studio rules.

        Rules:
        1. Non-empty list.
        2. At most MAX_FILES (25) files.
        3. Only .docx or .pdf files.
        4. Uniform file type: all must be .docx OR all must be .pdf.
        """
        if not paths:
            return False, "Hiçbir dosya seçilmedi.", []

        clean_paths = [p.strip().strip("'\"") for p in paths if p and p.strip().strip("'\"")]
        clean_paths = list(dict.fromkeys(clean_paths))
        if not clean_paths:
            return False, "Hiçbir geçerli dosya yolu belirtilmedi.", []

        if len(clean_paths) > cls.MAX_FILES:
            return (
                False,
                f"En fazla {cls.MAX_FILES} dosya seçebilirsiniz. ({len(clean_paths)} dosya seçildi. Lütfen seçimi azaltın.)",
                [],
            )

        extensions = set()
        for p in clean_paths:
            ext = os.path.splitext(p)[1].lower()
            if ext not in (".docx", ".pdf"):
                return (
                    False,
                    f"Desteklenmeyen dosya formatı tespit edildi: '{os.path.basename(p)}'. Yalnızca .docx ve .pdf dosyaları desteklenmektedir.",
                    [],
                )
            extensions.add(ext)

        if len(extensions) > 1:
            return (
                False,
                "Çoklu dosya işlemlerinde yalnızca aynı türden dosyalar seçilebilir. Lütfen yalnızca .docx dosyalarını veya yalnızca .pdf dosyalarını seçin.",
                [],
            )

        return True, "", clean_paths

    def _update_loaded_ui_for_files(self, paths: list[str]) -> None:
        if not paths:
            return
        count = len(paths)
        ext = os.path.splitext(paths[0])[1].lower()
        is_pdf = (ext == ".pdf")

        total_bytes = 0
        for p in paths:
            try:
                if os.path.exists(p):
                    total_bytes += os.path.getsize(p)
            except OSError:
                pass

        size_str = (
            f"{total_bytes / 1024:.1f} KB"
            if total_bytes < 1024 * 1024
            else f"{total_bytes / (1024 * 1024):.1f} MB"
        )

        badge_type = "PDF" if is_pdf else "DOCX"
        badge_color = "#f43f5e" if is_pdf else "#0284c7"

        if count == 1:
            filename = os.path.basename(paths[0])
            self.lbl_badge.setText(badge_type)
            self.lbl_filename.setText(filename)
            self.lbl_filename.setToolTip(paths[0])
            self.lbl_filesize.setText(f"{size_str} • {paths[0]}")
        else:
            self.lbl_badge.setText(f"{badge_type} ({count} Dosya)")
            self.lbl_filename.setText(f"{count} adet çeviri dosyası hazır")
            tooltip_text = "\n".join(f"• {os.path.basename(p)}" for p in paths)
            self.lbl_filename.setToolTip(tooltip_text)
            self.lbl_filesize.setText(f"Toplam Boyut: {size_str} • En Fazla {self.MAX_FILES} Dosya")

        self.lbl_badge.setStyleSheet(
            f"background-color: {badge_color}; color: #ffffff; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 4px;"
        )

        self.empty_container.setVisible(False)
        self.loaded_container.setVisible(True)
        self._update_border_style()

    def set_files(self, paths: list[str]) -> bool:
        """Validate and set multiple files."""
        is_valid, err_msg, clean_paths = self.validate_file_paths(paths)
        if not is_valid:
            self.validation_error.emit(err_msg)
            return False

        self._file_paths = clean_paths
        self._update_loaded_ui_for_files(self._file_paths)
        self.file_selected.emit(self._file_paths[0])
        self.files_selected.emit(self._file_paths)
        return True

    def set_file(self, path: str) -> None:
        """Backward-compatible setter for single file."""
        if not path:
            return
        self.set_files([path])

    def get_files(self) -> list[str]:
        """Return list of currently selected file paths."""
        return list(self._file_paths)

    def get_file_path(self) -> Optional[str]:
        """Backward-compatible getter returning first file or None."""
        return self._file_paths[0] if self._file_paths else None

    def clear(self) -> None:
        self._file_paths = []
        self.empty_container.setVisible(True)
        self.loaded_container.setVisible(False)
        self._update_border_style()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            local_paths = [u.toLocalFile() for u in urls if u.toLocalFile()]
            if any(p.lower().endswith((".docx", ".pdf")) for p in local_paths):
                event.acceptProposedAction()
                self._update_border_style(is_hover=True)

    def dragLeaveEvent(self, event) -> None:
        self._update_border_style(is_hover=False)

    def dropEvent(self, event) -> None:
        self._update_border_style(is_hover=False)
        local_paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        if local_paths:
            success = self.set_files(local_paths)
            if success:
                event.acceptProposedAction()


class OptionTileWidget(QFrame):
    """Clickable modern option tile with radio indicator, title, and optional cyan subtext."""

    clicked = Signal()

    def __init__(self, title: str, subtext: Optional[str] = None, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("tile-option")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(50 if subtext else 40)
        self._is_selected = is_selected
        self._tile_group: Optional["OptionTileGroup"] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Radio glyph
        self.lbl_radio = QLabel()
        self.lbl_radio.setFixedSize(18, 18)
        self.lbl_radio.setAlignment(Qt.AlignCenter)
        self.lbl_radio.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")
        self.lbl_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_title.setMinimumHeight(18)
        text_layout.addWidget(self.lbl_title)

        self.lbl_subtext = None
        if subtext:
            self.lbl_subtext = QLabel(subtext)
            self.lbl_subtext.setStyleSheet("font-size: 11px; font-family: monospace; color: #38bdf8;")
            self.lbl_subtext.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.lbl_subtext.setMinimumHeight(14)
            text_layout.addWidget(self.lbl_subtext)

        layout.addWidget(self.lbl_radio)
        layout.addLayout(text_layout)
        layout.addStretch()

        self.set_selected(is_selected)

    def is_selected(self) -> bool:
        return self._is_selected

    def isChecked(self) -> bool:
        return self._is_selected

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self._update_appearance()

    def setChecked(self, selected: bool) -> None:
        if selected and self._tile_group:
            self._tile_group.select(self)
        else:
            self.set_selected(selected)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self._update_appearance()

    def _update_appearance(self) -> None:
        if not self.isEnabled():
            self.lbl_radio.setStyleSheet("""
                background-color: transparent;
                border: 2px solid #1e293b;
                border-radius: 9px;
            """)
            self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 500; color: #475569;")
            if self.lbl_subtext:
                self.lbl_subtext.setStyleSheet("font-size: 11px; font-family: monospace; color: #334155;")
        elif self._is_selected:
            self.lbl_radio.setStyleSheet("""
                background-color: #38bdf8;
                border: 4px solid #131f38;
                border-radius: 9px;
            """)
            self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #ffffff;")
            if self.lbl_subtext:
                self.lbl_subtext.setStyleSheet("font-size: 11px; font-family: monospace; color: #38bdf8;")
        else:
            self.lbl_radio.setStyleSheet("""
                background-color: transparent;
                border: 2px solid #334155;
                border-radius: 9px;
            """)
            self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 500; color: #94a3b8;")
            if self.lbl_subtext:
                self.lbl_subtext.setStyleSheet("font-size: 11px; font-family: monospace; color: #64748b;")

        if self.style():
            self.style().unpolish(self)
            self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        if not self.isEnabled():
            return
        if event.button() == Qt.LeftButton:
            if self._tile_group:
                self._tile_group.select(self)
            else:
                self.set_selected(True)
            self.clicked.emit()
        super().mousePressEvent(event)


class OptionTileGroup:
    """Manages mutual exclusion for a group of OptionTileWidgets."""

    def __init__(self, tiles: Optional[list["OptionTileWidget"]] = None):
        self.tiles: list[OptionTileWidget] = []
        if tiles:
            for t in tiles:
                self.add_tile(t)

    def add_tile(self, tile: "OptionTileWidget") -> None:
        self.tiles.append(tile)
        tile._tile_group = self

    def select(self, target_tile: "OptionTileWidget") -> None:
        for t in self.tiles:
            t.set_selected(t is target_tile)


class BatchExtractionWorker(QThread):
    """Background worker thread to sequentially and safely process up to 25 files without resource contention."""

    progress = Signal(int, str)
    log = Signal(str)
    file_started = Signal(int, int, str)
    file_completed = Signal(int, int, str, object)
    file_error = Signal(int, int, str, str)
    all_finished = Signal(list)

    def __init__(
        self,
        file_paths: list[str],
        sort_by: str,
        in_place: bool,
        standalone: bool,
        output_dir: Optional[str] = None,
        is_single_compat: bool = False,
    ):
        super().__init__()
        self.file_paths = file_paths
        self.sort_by = sort_by
        self.in_place = in_place
        self.standalone = standalone
        self.output_dir = output_dir
        self.is_single_compat = is_single_compat

    def run(self) -> None:
        total_files = len(self.file_paths)
        if total_files == 0:
            self.progress.emit(100, "İşlenecek dosya yok.")
            self.all_finished.emit([])
            return

        summary: list[dict] = []
        file_weight = 100.0 / total_files

        if self.is_single_compat:
            self.log.emit(f"[*] İşlem başlatılıyor: {os.path.basename(self.file_paths[0])}")
        else:
            self.log.emit(f"[*] Toplu işlem başlatıldı: Toplam {total_files} çeviri dosyası işlenecek.")

        for idx, file_path in enumerate(self.file_paths, start=1):
            filename = os.path.basename(file_path)
            self.file_started.emit(idx, total_files, filename)
            if not self.is_single_compat:
                self.log.emit(f"[{idx}/{total_files}] Başlatılıyor: {filename}")

            base_pct = int((idx - 1) * file_weight)

            def sub_progress(sub_pct: int, msg: str):
                if self.is_single_compat:
                    self.progress.emit(sub_pct, msg)
                    self.log.emit(f"[{sub_pct}%] {msg}")
                else:
                    overall_pct = int(base_pct + (sub_pct / 100.0) * file_weight)
                    overall_pct = max(0, min(99, overall_pct))
                    status_str = f"[{idx}/{total_files}] {filename} ({sub_pct}%): {msg}"
                    self.progress.emit(overall_pct, status_str)

            try:
                out_path = None
                if self.output_dir and not self.in_place:
                    base = os.path.splitext(filename)[0]
                    out_path = os.path.join(self.output_dir, f"{base}_kast.docx")

                saved_path, result = process_dubbing_file(
                    file_path=file_path,
                    output_path=out_path,
                    sort_by=self.sort_by,
                    in_place=self.in_place,
                    standalone=self.standalone,
                    progress_callback=sub_progress,
                )

                char_count = len(getattr(result, "characters", []))
                line_count = getattr(result, "total_lines", 0)
                self.log.emit(
                    f"<span style='color:#10b981;'>[✓] [{idx}/{total_files}] Tamamlandı: {os.path.basename(saved_path)} "
                    f"({char_count} Karakter • {line_count} Replik)</span>"
                )
                self.file_completed.emit(idx, total_files, saved_path, result)
                summary.append({
                    "path": file_path,
                    "output": saved_path,
                    "result": result,
                    "status": "success",
                    "error": None,
                })
            except PermissionError:
                if self.is_single_compat:
                    err_msg = (
                        "Dosyaya erişim engellendi. Dosya şu anda Microsoft Word, PDF okuyucu veya başka bir programda açık olabilir. "
                        "Lütfen dosyayı kapatıp tekrar deneyin."
                    )
                else:
                    err_msg = (
                        f"Dosyaya erişim engellendi ({filename}). Dosya Microsoft Word, PDF okuyucu veya "
                        "başka bir programda açık olabilir. Lütfen kapatıp tekrar deneyin."
                    )
                self.log.emit(f"<span style='color:#f43f5e;'>[!] [{idx}/{total_files}] HATA: {err_msg}</span>")
                self.file_error.emit(idx, total_files, filename, err_msg)
                summary.append({
                    "path": file_path,
                    "output": None,
                    "result": None,
                    "status": "error",
                    "error": err_msg,
                })
            except Exception as e:
                err_msg = str(e)
                self.log.emit(f"<span style='color:#f43f5e;'>[!] [{idx}/{total_files}] HATA ({filename}): {err_msg}</span>")
                self.file_error.emit(idx, total_files, filename, err_msg)
                summary.append({
                    "path": file_path,
                    "output": None,
                    "result": None,
                    "status": "error",
                    "error": err_msg,
                })

        success_count = sum(1 for s in summary if s["status"] == "success")
        if self.is_single_compat:
            self.progress.emit(100, "İşlem tamamlandı")
        else:
            self.progress.emit(100, f"Toplu işlem tamamlandı ({success_count}/{total_files} başarılı)")
            self.log.emit(f"[*] İşlem bitti: {success_count}/{total_files} dosya başarıyla oluşturuldu.")
        self.all_finished.emit(summary)


class ExtractionWorker(BatchExtractionWorker):
    """Backward-compatible single-file worker wrapper."""

    finished = Signal(str, object)
    error = Signal(str)

    def __init__(
        self,
        file_path: str,
        sort_by: str,
        in_place: bool,
        standalone: bool,
        output_dir: Optional[str] = None,
    ):
        super().__init__(
            file_paths=[file_path],
            sort_by=sort_by,
            in_place=in_place,
            standalone=standalone,
            output_dir=output_dir,
            is_single_compat=True,
        )
        self.file_path = file_path
        self.all_finished.connect(self._handle_compat_finished)

    def _handle_compat_finished(self, summary: list[dict]) -> None:
        if not summary:
            return
        item = summary[0]
        if item["status"] == "success":
            self.finished.emit(item["output"], item["result"])
        else:
            self.error.emit(item["error"] or "Bilinmeyen hata")


class KastStudioWindow(QMainWindow):
    """Main window for Kast 2.0 Windows Studio Edition."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Kast 2.0 — Dublaj Çevirisi Kast Çıkarma (Windows Studio Edition)")
        self.resize(860, 740)
        self.setMinimumSize(740, 520)
        self.setStyleSheet(StudioTheme.get_stylesheet())

        self.last_output_file: Optional[str] = None
        self.batch_worker: Optional[BatchExtractionWorker] = None
        self.worker: Optional[BatchExtractionWorker] = None

        # Pencere ve görev çubuğu ikonu
        icon_paths = [
            os.path.join(ROOT_DIR, "packaging", "assets", "kast_icon.png"),
            os.path.join(ROOT_DIR, "packaging", "assets", "kast.ico"),
            os.path.join(os.path.dirname(__file__), "..", "packaging", "assets", "kast_icon.png"),
        ]
        for p in icon_paths:
            if os.path.exists(p):
                self.setWindowIcon(QIcon(p))
                break

        self._init_ui()

    def _init_ui(self) -> None:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        central = QWidget()
        central.setObjectName("central-content")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # 1. Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(4)

        title_hbox = QHBoxLayout()
        title_hbox.setSpacing(0)
        self.lbl_title_prefix = QLabel("Kast 2.0")
        self.lbl_title_prefix.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        self.lbl_title_suffix = QLabel(" — Dublaj Kast Çıkarma")
        self.lbl_title_suffix.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8fafc;")
        title_hbox.addWidget(self.lbl_title_prefix)
        title_hbox.addWidget(self.lbl_title_suffix)
        title_hbox.addStretch()

        self.lbl_subtitle = QLabel("Çeviri belgelerindeki diyalogları ve karakter listesini otomatik analiz eder.")
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #64748b;")

        title_vbox.addLayout(title_hbox)
        title_vbox.addWidget(self.lbl_subtitle)

        self.lbl_badge = QLabel("● Windows Studio Edition • Qt6")
        self.lbl_badge.setStyleSheet("""
            background-color: #0f293a;
            border: 1px solid #084c61;
            color: #38bdf8;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_badge, alignment=Qt.AlignTop | Qt.AlignRight)
        main_layout.addLayout(header_layout)

        # 2. Central Drop Zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_selected.connect(self._on_files_selected)
        self.drop_zone.validation_error.connect(self._on_validation_error)
        # Geriye dönük uyumluluk için file_selected bağlantısı:
        self.drop_zone.file_selected.connect(self._on_file_selected)
        main_layout.addWidget(self.drop_zone)

        # 3. Dual Card Panels (Karakter Sıralama ve Çıktı Seçenekleri)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        # Sol kart: Karakter Sıralama
        self.card_sort = QFrame()
        self.card_sort.setObjectName("card-panel")
        self.card_sort.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sort_vbox = QVBoxLayout(self.card_sort)
        sort_vbox.setContentsMargins(0, 0, 0, 0)
        sort_vbox.setSpacing(6)

        self.lbl_sort_title = QLabel("🗂  Karakter Sıralama")
        self.lbl_sort_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
        sort_vbox.addWidget(self.lbl_sort_title)

        self.tile_appearance = OptionTileWidget("İlk Görünme Sırası", subtext=None, is_selected=True)
        self.tile_count = OptionTileWidget("Replik Sayısına Göre", subtext=None, is_selected=False)
        self.tile_name = OptionTileWidget("Karakter Adına Göre (A-Z)", subtext=None, is_selected=False)

        self.sort_group = OptionTileGroup([self.tile_appearance, self.tile_count, self.tile_name])
        sort_vbox.addWidget(self.tile_appearance)
        sort_vbox.addWidget(self.tile_count)
        sort_vbox.addWidget(self.tile_name)
        sort_vbox.addStretch()

        # Sağ kart: Çıktı Seçenekleri
        self.card_output = QFrame()
        self.card_output.setObjectName("card-panel")
        self.card_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        out_vbox = QVBoxLayout(self.card_output)
        out_vbox.setContentsMargins(0, 0, 0, 0)
        out_vbox.setSpacing(6)

        self.lbl_out_title = QLabel("📄  Çıktı Seçenekleri")
        self.lbl_out_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
        out_vbox.addWidget(self.lbl_out_title)

        self.tile_standalone = OptionTileWidget("Ayrı dosya olarak kaydet", subtext="(<ad>_kast.docx)", is_selected=True)
        self.tile_inplace = OptionTileWidget("Orijinal Word dökümanının sonuna ekle", subtext=None, is_selected=False)
        self.output_group = OptionTileGroup([self.tile_standalone, self.tile_inplace])
        out_vbox.addWidget(self.tile_standalone)
        out_vbox.addWidget(self.tile_inplace)

        # Divider + Footer metadata row
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #1e293b; max-height: 1px; border: none; margin-top: 4px; margin-bottom: 2px;")
        out_vbox.addWidget(divider)

        self.lbl_output_meta = QLabel("Çıktı Biçimi: .docx Tablo  |  Varsayılan şablon v2.1")
        self.lbl_output_meta.setStyleSheet("font-size: 11px; color: #64748b;")
        out_vbox.addWidget(self.lbl_output_meta)
        out_vbox.addStretch()

        cards_layout.addWidget(self.card_sort, stretch=1)
        cards_layout.addWidget(self.card_output, stretch=1)
        main_layout.addLayout(cards_layout)

        # Backward compatibility aliases
        self.rb_appearance = self.tile_appearance
        self.rb_count = self.tile_count
        self.rb_name = self.tile_name
        self.rb_standalone = self.tile_standalone
        self.rb_inplace = self.tile_inplace

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_extract = QPushButton("▶  Kast Tablosunu Çıkar")
        self.btn_extract.setObjectName("btn-primary")
        self.btn_extract.setFixedHeight(40)
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self._start_extraction)

        self.btn_clear = QPushButton("🗑  Temizle")
        self.btn_clear.setObjectName("btn-clear")
        self.btn_clear.setFixedHeight(40)
        self.btn_clear.clicked.connect(self._clear_all)

        btn_layout.addWidget(self.btn_extract, stretch=4)
        btn_layout.addWidget(self.btn_clear, stretch=1)
        main_layout.addLayout(btn_layout)

        # 5. Status & Progress
        status_progress_vbox = QVBoxLayout()
        status_progress_vbox.setSpacing(5)

        status_info_layout = QHBoxLayout()
        self.lbl_status = QLabel("● Durum: Hazır")
        self.lbl_status.setStyleSheet("font-size: 12px; color: #94a3b8;")
        self.lbl_pct = QLabel("%0")
        self.lbl_pct.setStyleSheet("font-size: 12px; font-weight: bold; color: #38bdf8;")
        status_info_layout.addWidget(self.lbl_status)
        status_info_layout.addStretch()
        status_info_layout.addWidget(self.lbl_pct)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)

        status_progress_vbox.addLayout(status_info_layout)
        status_progress_vbox.addWidget(self.progress_bar)
        main_layout.addLayout(status_progress_vbox)

        # 6. Results Card (Hidden by default, shown on success)
        self.result_card = QFrame()
        self.result_card.setStyleSheet("background: #111e33; border: 1px solid #10b981; border-radius: 8px; padding: 10px;")
        self.result_card.setVisible(False)
        res_layout = QHBoxLayout(self.result_card)

        self.lbl_result_text = QLabel("✓ Kast tablosu başarıyla oluşturuldu!")
        self.lbl_result_text.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")

        self.btn_open_folder = QPushButton("📁 Klasörde Göster")
        self.btn_open_folder.setStyleSheet("background-color: #162238; border: 1px solid #334155; border-radius: 6px; color: #cbd5e1; padding: 6px 14px; font-weight: 600;")
        self.btn_open_folder.clicked.connect(self._open_output_folder)

        self.btn_open_file = QPushButton("📄 Dosyayı Aç")
        self.btn_open_file.setStyleSheet("background-color: #162238; border: 1px solid #334155; border-radius: 6px; color: #cbd5e1; padding: 6px 14px; font-weight: 600;")
        self.btn_open_file.clicked.connect(self._open_output_file)

        res_layout.addWidget(self.lbl_result_text, stretch=2)
        res_layout.addWidget(self.btn_open_folder)
        res_layout.addWidget(self.btn_open_file)
        main_layout.addWidget(self.result_card)

        # 7. Live Monospace Activity Log
        log_vbox = QVBoxLayout()
        log_vbox.setSpacing(6)

        log_header_layout = QHBoxLayout()
        self.lbl_log_title = QLabel("🖥  İŞLEM GÜNLÜĞÜ")
        self.lbl_log_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b;")
        self.lbl_log_meta = QLabel("UTF-8 / Terminal hazır")
        self.lbl_log_meta.setStyleSheet("font-size: 11px; font-family: monospace; color: #475569;")
        log_header_layout.addWidget(self.lbl_log_title)
        log_header_layout.addStretch()
        log_header_layout.addWidget(self.lbl_log_meta)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(80)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #080c14;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #cbd5e1;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)

        log_vbox.addLayout(log_header_layout)
        log_vbox.addWidget(self.log_area)
        main_layout.addLayout(log_vbox, stretch=1)

        self.scroll_area.setWidget(central)
        self.setCentralWidget(self.scroll_area)

        # 8. Status Bar
        status_bar = self.statusBar()
        self.lbl_status_left = QLabel("PySide6 Modern Frame  |  Hazır")
        self.lbl_status_left.setStyleSheet("color: #64748b; font-size: 11px; padding-left: 8px;")
        self.lbl_status_right = QLabel("Encoding: UTF-8")
        self.lbl_status_right.setStyleSheet("color: #64748b; font-size: 11px; padding-right: 8px;")
        status_bar.addWidget(self.lbl_status_left)
        status_bar.addPermanentWidget(self.lbl_status_right)

    def _on_files_selected(self, file_paths: list[str]) -> None:
        if not file_paths:
            return
        self.btn_extract.setEnabled(True)
        self.lbl_status.setText("● Durum: Hazır")
        self.result_card.setVisible(False)

        count = len(file_paths)
        ext = os.path.splitext(file_paths[0])[1].lower()

        if ext == ".pdf":
            self.tile_inplace.setEnabled(False)
            self.tile_inplace.setToolTip("PDF dosyalarının üzerine doğrudan Word tablosu yazılamaz.")
            self.tile_standalone.setChecked(True)
            if count == 1:
                self.log_area.append(
                    f"<span style='color:#38bdf8;'>[BİLGİ] PDF algılandı: {os.path.basename(file_paths[0])} (Doğrudan ayrıştırma devrede)</span>"
                )
            else:
                self.log_area.append(
                    f"<span style='color:#38bdf8;'>[BİLGİ] {count} adet PDF çevirisi algılandı. (Doğrudan ayrıştırma devrede)</span>"
                )
        else:
            self.tile_inplace.setEnabled(True)
            self.tile_inplace.setToolTip("")
            if count == 1:
                self.log_area.append(
                    f"<span style='color:#38bdf8;'>[BİLGİ] DOCX algılandı: {os.path.basename(file_paths[0])} (Word/LibreOffice sayfalama devrede)</span>"
                )
            else:
                self.log_area.append(
                    f"<span style='color:#38bdf8;'>[BİLGİ] {count} adet DOCX çevirisi algılandı. (Word/LibreOffice sayfalama devrede)</span>"
                )

    def _on_file_selected(self, file_path: str) -> None:
        """Geriye dönük uyumluluk için tek dosya seçimi yöneticisi."""
        if not file_path:
            return
        # drop_zone sinyalleri ile çifte log yazılmasını engelle
        if self.drop_zone.get_files():
            return
        self._on_files_selected([file_path])

    def _on_validation_error(self, err_msg: str) -> None:
        self.btn_extract.setEnabled(False)
        self.lbl_status.setText("● Durum: Doğrulama Hatası")
        self.log_area.append(f"<span style='color:#f43f5e; font-weight:bold;'>[!] Doğrulama Hatası: {err_msg}</span>")

    def _clear_all(self) -> None:
        self.drop_zone.clear()
        self.btn_extract.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_pct.setText("%0")
        self.lbl_status.setText("● Durum: Hazır")
        self.result_card.setVisible(False)
        self.tile_inplace.setEnabled(True)
        self.tile_inplace.setToolTip("")
        self.tile_appearance.setChecked(True)
        self.tile_standalone.setChecked(True)
        self.btn_open_file.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.btn_open_file.setText("📄 Dosyayı Aç")
        self.log_area.clear()

    def _start_extraction(self) -> None:
        self.last_output_file = None
        file_paths = self.drop_zone.get_files()
        if not file_paths:
            return

        sort_by = "appearance"
        if self.tile_count.isChecked():
            sort_by = "count"
        elif self.tile_name.isChecked():
            sort_by = "name"

        in_place = self.tile_inplace.isChecked()
        standalone = self.tile_standalone.isChecked()

        self.btn_extract.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.result_card.setVisible(False)
        self.progress_bar.setValue(2)
        self.lbl_pct.setText("%2")
        self.lbl_status.setText("● Durum: Toplu işlem başlatılıyor...")

        self.batch_worker = BatchExtractionWorker(
            file_paths=file_paths,
            sort_by=sort_by,
            in_place=in_place,
            standalone=standalone,
        )
        # Geriye dönük uyumluluk referansı
        self.worker = self.batch_worker

        self.batch_worker.progress.connect(self._on_worker_progress)
        self.batch_worker.log.connect(self._on_worker_log)
        self.batch_worker.all_finished.connect(self._on_batch_finished)
        self.batch_worker.start()

    def _on_batch_finished(self, summary: list[dict]) -> None:
        total = len(summary)
        successes = [s for s in summary if s["status"] == "success"]
        errors = [s for s in summary if s["status"] == "error"]

        if successes:
            self.last_output_file = successes[-1]["output"]

        self.progress_bar.setValue(100)
        self.lbl_pct.setText("%100")
        self.btn_extract.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.result_card.setVisible(True)

        total_chars = sum(len(getattr(s["result"], "characters", [])) for s in successes if s.get("result"))
        total_lines = 0
        for s in successes:
            res = s.get("result")
            if not res:
                continue
            chars = getattr(res, "characters", [])
            chars_lines = sum(getattr(c, "line_count", 0) for c in chars)
            res_lines = getattr(res, "total_lines", 0)
            total_lines += chars_lines if chars_lines > 0 else (res_lines if isinstance(res_lines, int) else 0)

        if len(errors) == 0:
            self.lbl_status.setText("● Durum: Tamamlandı")
            self.lbl_result_text.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
            self.lbl_result_text.setText(
                f"✓ {len(successes)}/{total} dosya başarıyla oluşturuldu! (Toplam: {total_chars} Karakter • {total_lines} Replik)"
            )
            self.btn_open_file.setEnabled(True)
            self.btn_open_folder.setEnabled(True)
        elif len(successes) == 0:
            self.lbl_status.setText(f"● Durum: İşlem Başarısız ({len(errors)} hata)")
            self.lbl_result_text.setStyleSheet("color: #f43f5e; font-weight: bold; font-size: 13px;")
            self.lbl_result_text.setText(
                f"❌ İşlem Başarısız: {len(errors)}/{total} dosyada hata oluştu."
            )
            self.btn_open_file.setEnabled(False)
            self.btn_open_folder.setEnabled(False)
        else:
            self.lbl_status.setText(f"● Durum: Tamamlandı ({len(errors)} hata)")
            self.lbl_result_text.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 13px;")
            self.lbl_result_text.setText(
                f"⚠️ Kısmi Tamamlandı: {len(successes)}/{total} başarılı, {len(errors)} dosyada hata oluştu."
            )
            self.btn_open_file.setEnabled(True)
            self.btn_open_folder.setEnabled(True)

        if total > 1:
            self.btn_open_file.setText("📄 Son Dosyayı Aç")
        else:
            self.btn_open_file.setText("📄 Dosyayı Aç")

    def _on_worker_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)
        self.lbl_pct.setText(f"%{pct}")
        self.lbl_status.setText(f"● Durum: {msg}")

    def _on_worker_log(self, text: str) -> None:
        self.log_area.append(text)

    def _on_worker_finished(self, output_path: str, result: object) -> None:
        self.last_output_file = output_path
        self.progress_bar.setValue(100)
        self.lbl_pct.setText("%100")
        self.lbl_status.setText("● Durum: Tamamlandı")
        self.btn_extract.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.result_card.setVisible(True)

        char_count = len(getattr(result, "characters", []))
        total_lines = getattr(result, "total_lines", 0)
        total_pages = getattr(result, "total_pages", 0)

        stat_summary = f"{char_count} Karakter • {total_lines} Replik"
        if total_pages > 1:
            stat_summary += f" • {total_pages} Sayfa"

        self.lbl_result_text.setText(f"✓ Başarıyla tamamlandı! ({stat_summary})")
        self.log_area.append(f"<span style='color:#10b981; font-weight:bold;'>[✓] Kaydedildi: {output_path}</span>")

    def _on_worker_error(self, err_msg: str) -> None:
        self.btn_extract.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_pct.setText("%0")
        self.lbl_status.setText("● Durum: Hata oluştu")
        self.log_area.append(f"<span style='color:#f43f5e; font-weight:bold;'>[!] Hata: {err_msg}</span>")

    def _open_output_folder(self) -> None:
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            return
        folder = os.path.dirname(os.path.abspath(self.last_output_file))
        if sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{os.path.abspath(self.last_output_file)}"])
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R", self.last_output_file])
        else:
            subprocess.run(["xdg-open", folder])

    def _open_output_file(self) -> None:
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            return
        if sys.platform == "win32":
            os.startfile(os.path.abspath(self.last_output_file))
        elif sys.platform == "darwin":
            subprocess.run(["open", self.last_output_file])
        else:
            subprocess.run(["xdg-open", self.last_output_file])


def launch_gui() -> int:
    """Entry point to launch the Kast Qt6 GUI."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = KastStudioWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(launch_gui())


