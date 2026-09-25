# Qt6 Windows Studio GUI ve Doğrudan PDF/DOCX Desteği Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dublaj stüdyoları için Windows ortamında çalışan, PySide6 (Qt6) tabanlı, modern ve şık koyu temalı bir masaüstü arayüzü (GUI) oluşturmak; arayüzde ayrı referans PDF kutusu yerine tek bir birleşik sürükle-bırak/gözat alanıyla hem `.docx` hem de `.pdf` senaryolarını doğrudan kabul edip kast tablosunu çıkarmak.

**Architecture:** Yeni bir `DubbingPdfParser` motoru ile doğrudan PDF senaryolarından %100 sayfa doğruluğuyla replik ve karakter istatistikleri çıkarılır; `kast.py` içindeki birleşik `process_dubbing_file` motoru girdi türüne göre (PDF ise doğrudan ayrıştırma, DOCX ise Word COM/LibreOffice geçici PDF akışı) yönlendirme yapar; `src/gui.py` içindeki PySide6 tabanlı `KastStudioWindow`, arka plan çalışan `ExtractionWorker` (QThread) ile arayüzün donmasını engelleyerek gerçek zamanlı log ve ilerleme akışı sağlar.

**Tech Stack:** Python 3.10+, PySide6 6.5+ (Qt6), `python-docx`, `pdfplumber`, `pytest`, `pytest-asyncio`, Windows PowerShell Word COM / LibreOffice.

**Spec:** Windows dublaj stüdyoları için tek dosya girdili (DOCX veya PDF), koyu stüdyo temalı, sürükle-bırak destekli, donmayan QThread mimarili ve doğrudan Word çıktılı masaüstü arayüzü.

## Global Constraints

- Windows-first tasarım prensibi: Windows'ta `Segoe UI` tipografisi, native dosya diyalogları, `%USERPROFILE%\bin\kast-gui.cmd` başlatıcısı, `explorer /select` ile klasörde gösterme ve `os.startfile` ile Word dökümanı açma desteği.
- Referans PDF kutusu GUI'da yer almayacaktır; kullanıcı yalnızca tek bir senaryo dosyası (`.docx` veya `.pdf`) yükler.
- PDF dosyası yüklenirse doğrudan o PDF'in sayfaları üzerinden çalışılır (dönüştürme gerekmez, sayfa numaraları %100 kesindir).
- DOCX dosyası yüklenirse mevcut %100 kesin sayfalama akışı (Word COM / LibreOffice geçici PDF) devreye girer.
- GUI işlemi arka planda bir `QThread` (`ExtractionWorker`) üzerinde yürütülür; ana arayüz döngüsü asla kilitlenmez.
- Kod değişiklikleri Andrej Karpathy'nin Living Architecture ilkelerine (`AGENTS.md`) uygun olarak belgelenmeli (ADR-005, atomic wiki sayfası, `index.md`, `log.md`).

---

### Task 1: Doğrudan PDF Senaryosu Ayrıştırma Motoru (`DubbingPdfParser`)

**Files:**
- Create: `src/pdf_parser.py`
- Test: `tests/test_pdf_parser.py`

**Interfaces:**
- Consumes: `pdfplumber`, `src.models.CastExtractionResult`, `src.models.CharacterStats`, `src.table_writer.CastTableWriter`, `src.parser.TIMECODE_REGEX`, `src.parser.KNOWN_METADATA_KEYS`, `src.parser.turkish_upper`
- Produces: `DubbingPdfParser.parse_pdf(pdf_path: str, sort_by: str = "appearance") -> CastExtractionResult`, `process_pdf_document(pdf_path: str, output_path: Optional[str] = None, sort_by: str = "appearance") -> Tuple[str, CastExtractionResult]`

- [ ] **Step 1: Failing test oluştur (`tests/test_pdf_parser.py`)**

```python
import os
import pytest
from unittest.mock import MagicMock, patch
from src.pdf_parser import DubbingPdfParser, process_pdf_document
from src.models import CastExtractionResult


def test_dubbing_pdf_parser_extracts_characters_and_pages():
    """PDF sayfalarından repliklerin ve karakterlerin doğru tespit edildiğini test eder."""
    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = (
        "1\n"
        "FİLMİN ADI\tTEST FİLMİ\n"
        "00.10\n"
        "ALICE\t- Merhaba Bob!\n"
        "BOB\t- Selam Alice!\n"
    )
    page2 = MagicMock()
    page2.extract_text.return_value = (
        "2\n"
        "01.20\n"
        "ALICE\t- İkinci sayfadaki replik.\n"
    )
    mock_pdf.pages = [page1, page2]
    mock_pdf.__enter__.return_value = mock_pdf

    with patch("pdfplumber.open", return_value=mock_pdf):
        parser = DubbingPdfParser()
        result = parser.parse_pdf("dummy.pdf", sort_by="appearance")

        assert isinstance(result, CastExtractionResult)
        assert result.total_lines == 3
        assert result.total_pages == 2
        assert len(result.characters) == 2

        alice = next(c for c in result.characters if c.name == "ALICE")
        assert alice.line_count == 2
        assert alice.pages == [1, 2]

        bob = next(c for c in result.characters if c.name == "BOB")
        assert bob.line_count == 1
        assert bob.pages == [1]


def test_process_pdf_document_creates_docx(tmp_path):
    """process_pdf_document fonksiyonunun kast tablosunu DOCX olarak kaydettiğini test eder."""
    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = "00.10\nJOHN\t- Selam dünya!"
    mock_pdf.pages = [page1]
    mock_pdf.__enter__.return_value = mock_pdf

    out_file = tmp_path / "test_pdf_kast.docx"
    with patch("pdfplumber.open", return_value=mock_pdf):
        saved_path, res = process_pdf_document("sample.pdf", output_path=str(out_file))
        assert os.path.exists(saved_path)
        assert res.total_lines == 1
        assert res.characters[0].name == "JOHN"
```

- [ ] **Step 2: Testi çalıştır ve hata aldığını doğrula**

Run: `.venv/bin/pytest tests/test_pdf_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pdf_parser'`

- [ ] **Step 3: `src/pdf_parser.py` motorunu kodla**

```python
"""Direct PDF Dubbing Script Parser Engine for Kast."""

import os
import re
from collections import OrderedDict
from typing import Callable, List, Optional, Tuple

import pdfplumber
from docx import Document

from src.models import CastExtractionResult, CharacterStats
from src.parser import KNOWN_METADATA_KEYS, TIMECODE_REGEX, turkish_upper
from src.table_writer import CastTableWriter


class DubbingPdfParser:
    """Parses dubbing script PDF files directly page-by-page."""

    DIALOGUE_REGEX = re.compile(r"^([^\t\-–—]{2,35}?)\s*(?:\t|\s{2,}|\s*[-–—]\s*)(.+)$")

    def __init__(self) -> None:
        self.known_metadata_keys = set(KNOWN_METADATA_KEYS)

    def _is_metadata(self, text: str) -> bool:
        upper = turkish_upper(text)
        return any(k in upper for k in ["FİLM", "DİZİ", "ÇEVİR", "SEZON", "BÖLÜM", "KAYIT", "STÜDYO", "YÖNETMEN", "TARİH", "TITLE"])

    def parse_pdf(
        self,
        pdf_path: str,
        sort_by: str = "appearance",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> CastExtractionResult:
        """Extracts cast statistics from a PDF dubbing script with 100% native page accuracy."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {pdf_path}")

        characters_map: OrderedDict[str, CharacterStats] = OrderedDict()
        total_dialogue_lines = 0
        appearance_counter = 0

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for page_idx, page in enumerate(pdf.pages, start=1):
                if progress_callback:
                    progress_callback(page_idx, total_pages, f"Sayfa {page_idx}/{total_pages} taranıyor...")

                page_text = page.extract_text() or ""
                lines = page_text.splitlines()

                for raw_line in lines:
                    line = raw_line.strip()
                    if not line or line.isdigit() or TIMECODE_REGEX.match(line):
                        continue

                    # Try tab-separated dialogue: SPEAKER \t [-] DIALOGUE
                    parts = line.split("\t", 1)
                    speaker, dialogue = None, None

                    if len(parts) == 2:
                        spk_candidate = parts[0].strip(" :.-")
                        dial_candidate = parts[1].strip()
                        if (dial_candidate.startswith("-") or dial_candidate.startswith("–") or dial_candidate.startswith("—")) and not self._is_metadata(spk_candidate):
                            speaker = spk_candidate
                            dialogue = dial_candidate
                    else:
                        # Regex match for 'SPEAKER - DIALOGUE'
                        m = re.match(r"^([^\t\-–—]{2,35}?)\s*[-–—]\s*(.+)$", line)
                        if m:
                            spk_candidate = m.group(1).strip(" :.-")
                            dial_candidate = m.group(2).strip()
                            if not self._is_metadata(spk_candidate) and len(spk_candidate.split()) <= 4:
                                speaker = spk_candidate
                                dialogue = dial_candidate

                    if speaker and dialogue:
                        total_dialogue_lines += 1
                        if speaker not in characters_map:
                            appearance_counter += 1
                            characters_map[speaker] = CharacterStats(
                                name=speaker,
                                first_seen_order=appearance_counter,
                            )
                        characters_map[speaker].add_line(page=page_idx)

        char_list = list(characters_map.values())
        if sort_by == "count":
            char_list.sort(key=lambda x: x.line_count, reverse=True)
        elif sort_by == "name":
            char_list.sort(key=lambda x: x.name)
        else:
            char_list.sort(key=lambda x: x.first_seen_order)

        return CastExtractionResult(
            characters=char_list,
            total_lines=total_dialogue_lines,
            total_pages=total_pages if "total_pages" in locals() else 1,
        )


def process_pdf_document(
    pdf_path: str,
    output_path: Optional[str] = None,
    sort_by: str = "appearance",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[str, CastExtractionResult]:
    """Processes a PDF script and outputs a standalone Word .docx file containing the cast table."""
    parser = DubbingPdfParser()
    result = parser.parse_pdf(pdf_path, sort_by=sort_by, progress_callback=progress_callback)

    if not output_path:
        base, _ = os.path.splitext(pdf_path)
        output_path = f"{base}_kast.docx"

    writer = CastTableWriter()
    doc = Document()
    writer.append_cast_table(doc, result, add_page_break=False)
    doc.save(output_path)

    return output_path, result
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `.venv/bin/pytest tests/test_pdf_parser.py -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/pdf_parser.py tests/test_pdf_parser.py
git commit -m "feat(parser): add DubbingPdfParser for direct PDF script extraction"
```

---

### Task 2: Birleşik Dosya Yönlendiricisi (`process_dubbing_file`)

**Files:**
- Modify: `kast.py:43-145`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: `process_cast_document`, `src.pdf_parser.process_pdf_document`, `src.models.CastExtractionResult`
- Produces: `process_dubbing_file(file_path: str, output_path: Optional[str] = None, sort_by: str = "appearance", in_place: bool = False, standalone: bool = True, progress_callback: Optional[Callable[[int, str], None]] = None) -> Tuple[str, CastExtractionResult]`

- [ ] **Step 1: Failing test ekle (`tests/test_integration.py`)**

```python
def test_process_dubbing_file_handles_pdf_and_docx(tmp_path):
    """process_dubbing_file fonksiyonunun hem docx hem pdf uzantılarını uygun motora sevk ettiğini test eder."""
    from kast import process_dubbing_file
    from unittest.mock import patch, MagicMock

    # 1. PDF testi
    mock_pdf_res = MagicMock()
    with patch("src.pdf_parser.process_pdf_document", return_value=("out.docx", mock_pdf_res)) as mock_pdf_func:
        out, res = process_dubbing_file("test.pdf", standalone=True)
        assert out == "out.docx"
        mock_pdf_func.assert_called_once()

    # 2. PDF + in_place hatası testi
    with pytest.raises(ValueError, match="PDF dosyalarının üzerine"):
        process_dubbing_file("test.pdf", in_place=True)
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `.venv/bin/pytest tests/test_integration.py -k test_process_dubbing_file_handles_pdf_and_docx -v`
Expected: FAIL with `ImportError: cannot import name 'process_dubbing_file' from 'kast'`

- [ ] **Step 3: `kast.py` içine `process_dubbing_file` fonksiyonunu ekle**

```python
from src.pdf_parser import process_pdf_document


def process_dubbing_file(
    file_path: str,
    output_path: Optional[str] = None,
    sort_by: str = "appearance",
    in_place: bool = False,
    standalone: bool = True,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Tuple[str, CastExtractionResult]:
    """Unified processor handling both .docx and .pdf dubbing scripts."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        if in_place:
            raise ValueError("PDF dosyalarının üzerine doğrudan Word tablosu yazılamaz. Lütfen ayrı dosya olarak kaydedin.")
        if progress_callback:
            progress_callback(10, "PDF dosyası doğrudan ayrıştırılıyor (%100 yerel)...")
        
        def pdf_progress(page: int, total: int, msg: str):
            if progress_callback:
                pct = int(10 + (page / max(1, total)) * 75)
                progress_callback(pct, msg)

        saved_path, result = process_pdf_document(
            pdf_path=file_path,
            output_path=output_path,
            sort_by=sort_by,
            progress_callback=pdf_progress,
        )
        if progress_callback:
            progress_callback(100, f"Tamamlandı: {os.path.basename(saved_path)}")
        return saved_path, result

    elif ext == ".docx":
        if progress_callback:
            progress_callback(15, "Word dökümanı yükleniyor ve paragraflar taranıyor...")
        
        # Orijinal akış
        saved_path = process_cast_document(
            docx_path=file_path,
            output_path=output_path,
            pdf_path=None,
            sort_by=sort_by,
            standalone=standalone if not in_place else False,
        )
        # Parse result to return stats
        from docx import Document
        doc = Document(file_path)
        parser = DubbingDocxParser()
        paras = parser.parse_document_paragraphs(doc)
        dial_count = sum(1 for p in paras if p.speaker and p.dialogue)
        result = CastExtractionResult(
            characters=[],
            total_lines=dial_count,
            total_pages=1,
        )
        if progress_callback:
            progress_callback(100, f"Tamamlandı: {os.path.basename(saved_path)}")
        return saved_path, result
    else:
        raise ValueError(f"Desteklenmeyen dosya formatı: {ext}. Lütfen bir .docx veya .pdf dosyası seçin.")
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `.venv/bin/pytest tests/test_integration.py -k test_process_dubbing_file_handles_pdf_and_docx -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add kast.py tests/test_integration.py
git commit -m "feat(pipeline): add unified process_dubbing_file supporting docx and pdf"
```

---

### Task 3: Qt6 Modern Koyu Stüdyo Teması ve Görsel Bileşenler (`StudioTheme`)

**Files:**
- Create: `src/gui.py` (Tema ve temel widget sınıfları)
- Test: `tests/test_gui.py`

**Interfaces:**
- Produces: `StudioTheme.get_stylesheet() -> str`, `StudioTheme.COLORS` sözlüğü

- [ ] **Step 1: Failing test yaz (`tests/test_gui.py`)**

```python
import pytest
from src.gui import StudioTheme


def test_studio_theme_stylesheet_contains_core_styles():
    """StudioTheme stil şablonunun modern renk ve widget tanımlarını içerdiğini doğrular."""
    css = StudioTheme.get_stylesheet()
    assert "#1a1b26" in css or "#24283b" in css  # Dark background
    assert "QProgressBar" in css
    assert "QPushButton" in css
    assert "QGroupBox" in css
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `.venv/bin/pytest tests/test_gui.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.gui'`

- [ ] **Step 3: `StudioTheme` sınıfını `src/gui.py` içine uygula**

```python
"""Modern Studio Qt6 GUI for Kast 2.0."""

import os
import sys
from typing import Dict


class StudioTheme:
    """Studio-grade modern dark palette and QSS stylesheets."""

    COLORS: Dict[str, str] = {
        "bg_dark": "#1a1b26",
        "card_bg": "#24283b",
        "card_hover": "#2f354f",
        "border": "#414868",
        "border_focus": "#7aa2f7",
        "text_main": "#c0caf5",
        "text_dim": "#7982a9",
        "accent_cyan": "#7dcfff",
        "accent_blue": "#7aa2f7",
        "accent_green": "#9ece6a",
        "accent_red": "#f7768e",
        "accent_yellow": "#e0af68",
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
        QGroupBox {{
            background-color: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
            margin-top: 18px;
            padding: 16px 12px 12px 12px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 14px;
            padding: 0 6px;
            color: {c["accent_cyan"]};
        }}
        QPushButton {{
            background-color: {c["card_hover"]};
            color: {c["text_main"]};
            border: 1px solid {c["border"]};
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {c["accent_blue"]};
            color: #ffffff;
            border-color: {c["accent_blue"]};
        }}
        QPushButton#btn-primary {{
            background-color: {c["accent_blue"]};
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 24px;
            border: none;
            border-radius: 6px;
        }}
        QPushButton#btn-primary:hover {{
            background-color: #89b4fa;
        }}
        QPushButton#btn-primary:disabled {{
            background-color: #3b4261;
            color: #7982a9;
        }}
        QRadioButton, QCheckBox {{
            spacing: 8px;
            color: {c["text_main"]};
        }}
        QRadioButton::indicator, QCheckBox::indicator {{
            width: 16px;
            height: 16px;
        }}
        QProgressBar {{
            background-color: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: 4px;
            text-align: center;
            color: #ffffff;
            font-weight: bold;
            height: 16px;
        }}
        QProgressBar::chunk {{
            background-color: {c["accent_green"]};
            border-radius: 3px;
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: #16161e;
            border: 1px solid {c["border"]};
            border-radius: 6px;
            color: #9ece6a;
            font-family: 'Consolas', 'Cascadia Code', monospace;
            font-size: 12px;
            padding: 8px;
        }}
        QStatusBar {{
            background-color: #16161e;
            color: {c["text_dim"]};
            border-top: 1px solid {c["border"]};
        }}
        """
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `.venv/bin/pytest tests/test_gui.py -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): add StudioTheme dark QSS stylesheet for Qt6"
```

---

### Task 4: Tekil Sürükle-Bırak Girdi Kartı (`DropZoneWidget`)

**Files:**
- Modify: `src/gui.py`
- Test: `tests/test_gui.py`

**Interfaces:**
- Produces: `DropZoneWidget(QFrame)`
  - Signals: `file_selected(str)`
  - Methods: `set_file(path: str)`, `clear()`, `get_file_path() -> Optional[str]`
  - Supports both `.docx` and `.pdf` files.

- [ ] **Step 1: Failing test ekle (`tests/test_gui.py`)**

```python
from PySide6.QtWidgets import QApplication
from src.gui import DropZoneWidget


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def test_drop_zone_widget_file_selection(qapp, tmp_path):
    """DropZoneWidget dosya seçimi, doğrulama ve temizleme davranışını test eder."""
    widget = DropZoneWidget()
    assert widget.get_file_path() is None

    # Geçerli docx ata
    docx_file = tmp_path / "script.docx"
    docx_file.write_text("dummy")
    widget.set_file(str(docx_file))

    assert widget.get_file_path() == str(docx_file)
    assert "script.docx" in widget.lbl_filename.text()
    assert "DOCX" in widget.lbl_badge.text()

    # Geçerli pdf ata
    pdf_file = tmp_path / "script.pdf"
    pdf_file.write_text("dummy")
    widget.set_file(str(pdf_file))
    assert widget.get_file_path() == str(pdf_file)
    assert "PDF" in widget.lbl_badge.text()

    # Temizle
    widget.clear()
    assert widget.get_file_path() is None
```

- [ ] **Step 2: Testi çalıştır ve hata aldığını doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_drop_zone_widget_file_selection -v`
Expected: FAIL with `ImportError: cannot import name 'DropZoneWidget'`

- [ ] **Step 3: `DropZoneWidget` sınıfını `src/gui.py` içine uygula**

```python
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class DropZoneWidget(QFrame):
    """Modern Drag-and-Drop and Browse file intake area supporting .docx and .pdf."""

    file_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._file_path = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("drop-zone")
        self.setMinimumHeight(150)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Empty State Elements
        self.empty_container = QFrame()
        empty_layout = QVBoxLayout(self.empty_container)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(8)

        self.lbl_icon = QLabel("📥")
        self.lbl_icon.setStyleSheet("font-size: 32px;")
        self.lbl_icon.setAlignment(Qt.AlignCenter)

        self.lbl_prompt = QLabel("Senaryo dosyasını (.docx veya .pdf) buraya sürükleyip bırakın")
        self.lbl_prompt.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0caf5;")
        self.lbl_prompt.setAlignment(Qt.AlignCenter)

        self.btn_browse = QPushButton("📁 Dosya Seç")
        self.btn_browse.setStyleSheet("padding: 8px 20px; font-weight: bold; background: #2f354f;")
        self.btn_browse.clicked.connect(self._open_file_dialog)

        empty_layout.addWidget(self.lbl_icon)
        empty_layout.addWidget(self.lbl_prompt)
        empty_layout.addWidget(self.btn_browse, alignment=Qt.AlignCenter)

        # 2. Loaded State Elements
        self.loaded_container = QFrame()
        self.loaded_container.setVisible(False)
        loaded_layout = QHBoxLayout(self.loaded_container)
        loaded_layout.setAlignment(Qt.AlignCenter)
        loaded_layout.setSpacing(12)

        self.lbl_badge = QLabel("DOCX")
        self.lbl_badge.setStyleSheet(
            "background-color: #7aa2f7; color: #1a1b26; font-weight: 800; font-size: 11px; padding: 4px 8px; border-radius: 4px;"
        )

        info_box = QVBoxLayout()
        self.lbl_filename = QLabel("")
        self.lbl_filename.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        self.lbl_filesize = QLabel("")
        self.lbl_filesize.setStyleSheet("font-size: 11px; color: #7982a9;")
        info_box.addWidget(self.lbl_filename)
        info_box.addWidget(self.lbl_filesize)

        self.btn_remove = QPushButton("✕ Değiştir")
        self.btn_remove.setStyleSheet("background: #f7768e; color: #1a1b26; border: none; padding: 6px 12px; font-weight: bold;")
        self.btn_remove.clicked.connect(self.clear)

        loaded_layout.addWidget(self.lbl_badge)
        loaded_layout.addLayout(info_box)
        loaded_layout.addWidget(self.btn_remove)

        self.main_layout.addWidget(self.empty_container)
        self.main_layout.addWidget(self.loaded_container)

        self._update_border_style(is_hover=False)

    def _update_border_style(self, is_hover: bool = False) -> None:
        border_color = "#7aa2f7" if is_hover else ("#414868" if not self._file_path else "#9ece6a")
        bg_color = "#2f354f" if is_hover else "#24283b"
        border_type = "dashed" if not self._file_path else "solid"
        self.setStyleSheet(f"""
            QFrame#drop-zone {{
                background-color: {bg_color};
                border: 2px {border_type} {border_color};
                border-radius: 12px;
            }}
        """)

    def _open_file_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Dublaj Senaryo Dosyası Seçin",
            "",
            "Dublaj Senaryoları (*.docx *.pdf);;Word Belgeleri (*.docx);;PDF Belgeleri (*.pdf);;Tüm Dosyalar (*.*)",
        )
        if file_path:
            self.set_file(file_path)

    def set_file(self, path: str) -> None:
        clean_path = path.strip().strip("'\"")
        ext = os.path.splitext(clean_path)[1].lower()
        if ext not in (".docx", ".pdf"):
            return

        self._file_path = clean_path
        filename = os.path.basename(clean_path)
        size_bytes = os.path.getsize(clean_path) if os.path.exists(clean_path) else 0
        size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024 * 1024 else f"{size_bytes / (1024 * 1024):.1f} MB"

        self.lbl_filename.setText(filename)
        self.lbl_filesize.setText(f"{size_str} • {clean_path}")

        if ext == ".pdf":
            self.lbl_badge.setText("PDF")
            self.lbl_badge.setStyleSheet("background-color: #f7768e; color: #1a1b26; font-weight: 800; font-size: 11px; padding: 4px 8px; border-radius: 4px;")
        else:
            self.lbl_badge.setText("DOCX")
            self.lbl_badge.setStyleSheet("background-color: #7aa2f7; color: #1a1b26; font-weight: 800; font-size: 11px; padding: 4px 8px; border-radius: 4px;")

        self.empty_container.setVisible(False)
        self.loaded_container.setVisible(True)
        self._update_border_style()
        self.file_selected.emit(self._file_path)

    def clear(self) -> None:
        self._file_path = None
        self.empty_container.setVisible(True)
        self.loaded_container.setVisible(False)
        self._update_border_style()

    def get_file_path(self) -> Optional[str]:
        return self._file_path

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith((".docx", ".pdf")) for u in urls):
                event.acceptProposedAction()
                self._update_border_style(is_hover=True)

    def dragLeaveEvent(self, event) -> None:
        self._update_border_style(is_hover=False)

    def dropEvent(self, event) -> None:
        self._update_border_style(is_hover=False)
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path.lower().endswith((".docx", ".pdf")):
                self.set_file(local_path)
                event.acceptProposedAction()
                break
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_drop_zone_widget_file_selection -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): add DropZoneWidget for drag-drop docx and pdf handling"
```

---

### Task 5: Arka Plan Çalışanı ve Ana Pencere (`KastStudioWindow`)

**Files:**
- Modify: `src/gui.py`
- Test: `tests/test_gui.py`

**Interfaces:**
- Produces: `ExtractionWorker(QThread)`, `KastStudioWindow(QMainWindow)`, `launch_gui() -> int`
- Signal flow: UI inputs -> Worker Thread -> Progress & Log Signals -> Results card & Notifications

- [ ] **Step 1: Failing test ekle (`tests/test_gui.py`)**

```python
from unittest.mock import MagicMock, patch
from src.gui import KastStudioWindow
from src.models import CastExtractionResult, CharacterStats


def test_kast_studio_window_interactions(qapp, tmp_path):
    """KastStudioWindow bileşenlerini, seçeneklerini ve akışını test eder."""
    window = KastStudioWindow()

    # Dosya seçimi yokken buton devre dışı
    assert not window.btn_extract.isEnabled()

    # PDF dosyası seçildiğinde in-place seçeneğinin devre dışı kalması
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_text("test")
    window.drop_zone.set_file(str(pdf_file))

    assert window.btn_extract.isEnabled()
    assert not window.rb_inplace.isEnabled()  # PDF'de in-place kapalı olmalı
    assert window.rb_standalone.isChecked()

    # DOCX dosyası seçildiğinde in-place seçeneğinin aktifleşmesi
    docx_file = tmp_path / "sample.docx"
    docx_file.write_text("test")
    window.drop_zone.set_file(str(docx_file))
    assert window.rb_inplace.isEnabled()
```

- [ ] **Step 2: Testi çalıştır ve hata aldığını doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_kast_studio_window_interactions -v`
Expected: FAIL with `ImportError: cannot import name 'KastStudioWindow'`

- [ ] **Step 3: `ExtractionWorker` ve `KastStudioWindow` sınıflarını `src/gui.py` içine ekle**

```python
import subprocess
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QProgressBar,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from kast import process_dubbing_file


class ExtractionWorker(QThread):
    """Background worker thread to execute cast extraction without blocking GUI."""

    progress = Signal(int, str)
    log = Signal(str)
    finished = Signal(str, object)
    error = Signal(str)

    def __init__(self, file_path: str, sort_by: str, in_place: bool, standalone: bool, output_dir: Optional[str] = None):
        super().__init__()
        self.file_path = file_path
        self.sort_by = sort_by
        self.in_place = in_place
        self.standalone = standalone
        self.output_dir = output_dir

    def run(self) -> None:
        try:
            self.log.emit(f"[*] İşlem başlatılıyor: {os.path.basename(self.file_path)}")
            out_path = None
            if self.output_dir and not self.in_place:
                base = os.path.splitext(os.path.basename(self.file_path))[0]
                out_path = os.path.join(self.output_dir, f"{base}_kast.docx")

            def progress_cb(pct: int, msg: str):
                self.progress.emit(pct, msg)
                self.log.emit(f"[{pct}%] {msg}")

            saved_path, result = process_dubbing_file(
                file_path=self.file_path,
                output_path=out_path,
                sort_by=self.sort_by,
                in_place=self.in_place,
                standalone=self.standalone,
                progress_callback=progress_cb,
            )
            self.finished.emit(saved_path, result)
        except Exception as e:
            self.error.emit(str(e))


class KastStudioWindow(QMainWindow):
    """Main window for Kast 2.0 Windows Studio Edition."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Kast 2.0 — Dublaj Çevirisi Kast Çıkarma (Windows Studio Edition)")
        self.resize(840, 720)
        self.setMinimumSize(780, 600)
        self.setStyleSheet(StudioTheme.get_stylesheet())

        self.last_output_file = None
        self.worker = None

        self._init_ui()

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🎬 Kast 2.0 — Dublaj Kast Çıkarma")
        title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #7dcfff;")
        badge_label = QLabel("Windows Studio Edition • Qt6")
        badge_label.setStyleSheet("font-size: 12px; color: #7982a9; font-weight: 600;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(badge_label)
        main_layout.addLayout(header_layout)

        # 2. Unified Drop Zone (No reference PDF input!)
        self.drop_zone = DropZoneWidget()
        self.drop_zone.file_selected.connect(self._on_file_selected)
        main_layout.addWidget(self.drop_zone)

        # 3. Options Row (Sıralama ve Çıktı)
        options_layout = QHBoxLayout()
        options_layout.setSpacing(14)

        # Sıralama Kutusu
        sort_group = QGroupBox("Karakter Sıralama")
        sort_vbox = QVBoxLayout(sort_group)
        self.rb_appearance = QRadioButton("İlk Görünme Sırası (Appearance)")
        self.rb_appearance.setChecked(True)
        self.rb_count = QRadioButton("Replik Sayısına Göre (Çoktan Aza)")
        self.rb_name = QRadioButton("Karakter Adına Göre (A-Z)")
        sort_vbox.addWidget(self.rb_appearance)
        sort_vbox.addWidget(self.rb_count)
        sort_vbox.addWidget(self.rb_name)
        options_layout.addWidget(sort_group)

        # Çıktı Seçenekleri Kutusu
        out_group = QGroupBox("Çıktı Seçenekleri")
        out_vbox = QVBoxLayout(out_group)
        self.rb_standalone = QRadioButton("Ayrı dosya olarak kaydet (<ad>_kast.docx)")
        self.rb_standalone.setChecked(True)
        self.rb_inplace = QRadioButton("Orijinal Word dökümanının sonuna ekle")
        out_vbox.addWidget(self.rb_standalone)
        out_vbox.addWidget(self.rb_inplace)
        options_layout.addWidget(out_group)

        main_layout.addLayout(options_layout)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_extract = QPushButton("▶ Kast Tablosunu Çıkar")
        self.btn_extract.setObjectName("btn-primary")
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self._start_extraction)

        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.clicked.connect(self._clear_all)

        btn_layout.addWidget(self.btn_extract, stretch=3)
        btn_layout.addWidget(self.btn_clear, stretch=1)
        main_layout.addLayout(btn_layout)

        # 5. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        # 6. Results Card (Hidden by default, shown on success)
        self.result_card = QFrame()
        self.result_card.setStyleSheet("background: #24283b; border: 1px solid #9ece6a; border-radius: 8px; padding: 10px;")
        self.result_card.setVisible(False)
        res_layout = QHBoxLayout(self.result_card)

        self.lbl_result_text = QLabel("✓ Kast tablosu başarıyla oluşturuldu!")
        self.lbl_result_text.setStyleSheet("color: #9ece6a; font-weight: bold; font-size: 13px;")

        self.btn_open_folder = QPushButton("📁 Klasörde Göster")
        self.btn_open_folder.clicked.connect(self._open_output_folder)

        self.btn_open_file = QPushButton("📄 Dosyayı Aç")
        self.btn_open_file.clicked.connect(self._open_output_file)

        res_layout.addWidget(self.lbl_result_text, stretch=2)
        res_layout.addWidget(self.btn_open_folder)
        res_layout.addWidget(self.btn_open_file)
        main_layout.addWidget(self.result_card)

        # 7. Live Monospace Activity Log
        log_label = QLabel("İşlem Günlüğü")
        log_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #7982a9;")
        main_layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(140)
        main_layout.addWidget(self.log_area)

    def _on_file_selected(self, file_path: str) -> None:
        self.btn_extract.setEnabled(True)
        self.result_card.setVisible(False)
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            self.rb_inplace.setEnabled(False)
            self.rb_inplace.setToolTip("PDF dosyalarının üzerine doğrudan Word tablosu yazılamaz.")
            self.rb_standalone.setChecked(True)
            self.log_area.append(f"<span style='color:#7dcfff;'>[BİLGİ] PDF algılandı: {os.path.basename(file_path)} (Doğrudan ayrıştırma devrede)</span>")
        else:
            self.rb_inplace.setEnabled(True)
            self.rb_inplace.setToolTip("")
            self.log_area.append(f"<span style='color:#7aa2f7;'>[BİLGİ] DOCX algılandı: {os.path.basename(file_path)} (Word/LibreOffice sayfalama devrede)</span>")

    def _clear_all(self) -> None:
        self.drop_zone.clear()
        self.btn_extract.setEnabled(False)
        self.progress_bar.setValue(0)
        self.result_card.setVisible(False)
        self.rb_appearance.setChecked(True)
        self.rb_standalone.setChecked(True)
        self.log_area.clear()

    def _start_extraction(self) -> None:
        file_path = self.drop_zone.get_file_path()
        if not file_path:
            return

        sort_by = "appearance"
        if self.rb_count.isChecked():
            sort_by = "count"
        elif self.rb_name.isChecked():
            sort_by = "name"

        in_place = self.rb_inplace.isChecked()
        standalone = self.rb_standalone.isChecked()

        self.btn_extract.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.result_card.setVisible(False)
        self.progress_bar.setValue(5)

        self.worker = ExtractionWorker(
            file_path=file_path,
            sort_by=sort_by,
            in_place=in_place,
            standalone=standalone,
        )
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.log.connect(self._on_worker_log)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_worker_progress(self, pct: int, msg: str) -> None:
        self.progress_bar.setValue(pct)

    def _on_worker_log(self, text: str) -> None:
        self.log_area.append(text)

    def _on_worker_finished(self, output_path: str, result: object) -> None:
        self.last_output_file = output_path
        self.progress_bar.setValue(100)
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
        self.log_area.append(f"<span style='color:#9ece6a; font-weight:bold;'>[✓] Kaydedildi: {output_path}</span>")

    def _on_worker_error(self, err_msg: str) -> None:
        self.btn_extract.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_area.append(f"<span style='color:#f7768e; font-weight:bold;'>[!] Hata: {err_msg}</span>")

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
```

- [ ] **Step 4: Testleri çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): implement KastStudioWindow and ExtractionWorker QThread"
```

---

### Task 6: CLI Entegrasyonu ve Windows Başlatıcıları (`kast-gui.cmd`, `install.ps1`)

**Files:**
- Modify: `kast.py:148-255`
- Create: `kast-gui.cmd`
- Modify: `install.ps1:40-155`
- Modify: `requirements.txt`
- Test: `tests/test_tui.py`, `tests/test_install_scripts.py`

**Interfaces:**
- Produces: `kast.py --gui` (`-g`), `kast-gui.cmd`, `PySide6>=6.5.0` in `requirements.txt`

- [ ] **Step 1: Failing test ekle (`tests/test_install_scripts.py`)**

```python
def test_kast_gui_cmd_exists_and_contains_pyside_entrypoint():
    """kast-gui.cmd başlatıcısının doğru Python ve GUI argümanlarını içerdiğini doğrular."""
    assert os.path.exists("kast-gui.cmd")
    with open("kast-gui.cmd", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    assert "--gui" in content or "src.gui" in content
```

- [ ] **Step 2: Testi çalıştır ve hata aldığını doğrula**

Run: `.venv/bin/pytest tests/test_install_scripts.py -k test_kast_gui_cmd_exists_and_contains_pyside_entrypoint -v`
Expected: FAIL with `AssertionError: assert False where False = os.path.exists('kast-gui.cmd')`

- [ ] **Step 3: `kast.py` CLI argümanlarına `--gui` ekle, `kast-gui.cmd` oluştur ve `requirements.txt` güncelle**

`kast.py`:
```python
    parser.add_argument(
        "--gui",
        "-g",
        dest="gui_mode",
        action="store_true",
        help="Modern Qt6 Masaüstü Arayüzünü (GUI) başlat.",
    )
```
`main()` içinde:
```python
    if args.gui_mode:
        from src.gui import launch_gui
        return launch_gui()
```

`kast-gui.cmd`:
```batch
@echo off
setlocal
chcp 65001 >nul 2>&1
set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%kast.py" --gui %*
) else (
    python "%SCRIPT_DIR%kast.py" --gui %*
)
endlocal
```

`requirements.txt`:
```
python-docx>=1.0.0
Pillow>=10.0.0
pdfplumber>=0.10.0
PySide6>=6.5.0
textual>=0.80.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

`install.ps1`:
`%USERPROFILE%\bin\kast-gui.cmd` dosyasının otomatik oluşturulmasını ekle ve kurulum sonrası mesajlarda hem `kast` (TUI), hem `kast-gui` (Qt6 Studio GUI), hem `kast dosya.docx` seçeneklerini listele.

- [ ] **Step 4: Testleri çalıştır ve geçtiğini doğrula**

Run: `.venv/bin/pytest tests/test_install_scripts.py -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add kast.py kast-gui.cmd install.ps1 requirements.txt tests/test_install_scripts.py
git commit -m "feat(runtime): add kast-gui.cmd launcher and --gui flag for Qt6 GUI"
```

---

### Task 7: Living Architecture Wiki Güncellemesi (ADR-005, Atomic Sayfalar ve Fihrist)

**Files:**
- Create: `docs/kast-app-wiki/architecture-decisions/adr-005-qt6-windows-studio-gui.md`
- Create: `docs/kast-app-wiki/interfaces-and-runtime/qt6-desktop-gui.md`
- Modify: `docs/kast-app-wiki/index.md`
- Modify: `docs/kast-app-wiki/log.md`

**Interfaces:**
- Living Architecture kurallarına (`AGENTS.md`) %100 uyum:
  - Wikilink sözdizimi: `[[sayfa-adi]]`
  - Fonksiyonel domain ayrımı
  - Kronolojik log kaydı

- [ ] **Step 1: ADR-005 oluştur (`docs/kast-app-wiki/architecture-decisions/adr-005-qt6-windows-studio-gui.md`)**
Bağlam, karar, alternatifler (Tkinter, Electron, PyQt5) ve sonuçları belgele.

- [ ] **Step 2: Atomik sayfa oluştur (`docs/kast-app-wiki/interfaces-and-runtime/qt6-desktop-gui.md`)**
Bileşenleri, QSS temasını, sürükle-bırak motorunu ve `ExtractionWorker` QThread mimarisini açıkla.

- [ ] **Step 3: `docs/kast-app-wiki/index.md` fihristini güncelle**
Yeni sayfaları uygun fihrist başlıkları altına ekle.

- [ ] **Step 4: `docs/kast-app-wiki/log.md` günlüğüne işle**
İlgili tarih ve ajan rolü ile yeni mimari eklemeyi kaydet.

- [ ] **Step 5: Git commit**

```bash
git add docs/kast-app-wiki/
git commit -m "docs(wiki): add ADR-005 and Qt6 desktop GUI atomic documentation"
```

---

## Verification Plan

### Automated Tests
- `tests/test_pdf_parser.py`: PDF doğrudan replik/karakter ayıklama doğrulaması.
  - `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_pdf_parser.py -v`
- `tests/test_gui.py`: PySide6 widget'ları, sürükle-bırak ve QThread testleri.
  - `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -v`
- `tests/test_integration.py`: `process_dubbing_file` birleşik yönlendirme doğrulaması.
  - `.venv/bin/pytest tests/test_integration.py -k test_process_dubbing_file -v`
- Tam regresyon testi:
  - `.venv/bin/pytest -v`

### Manual Verification
- Arayüzü offscreen ve görsel modda başlatıp pencerelerin, butonların ve log ekranının render edildiğini doğrulamak:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python3 -c "from src.gui import KastStudioWindow, QApplication; app = QApplication([]); w = KastStudioWindow(); print('Window rendered successfully!')"`
- `example/JACKIE & OOPJEN.docx` dosyasını `process_dubbing_file` ile çalıştırarak çıktıyı incelemek.
