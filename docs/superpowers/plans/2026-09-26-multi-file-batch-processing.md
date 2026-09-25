# Çoklu Dosya Seçimi ve Güvenli Toplu İşleme (Multi-File Batch Processing) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kast 2.0 Qt6 masaüstü arayüzüne 25 dosyaya kadar çoklu dosya seçimi / sürükle-bırak desteği kazandırmak; yalnızca homojen dosya formatına (hepsi .docx veya hepsi .pdf) izin verip aksi durumlarda kullanıcıyı uyarmak; ve kast çıkarma işlemini işlemciyi yormayacak ve LibreOffice/Word kilitlenmelerini önleyecek güvenli sıralı grup (sequential batch) iş parçacığıyla yürütmek.

**Architecture:** `src/gui.py` modülü genişletilir: `DropZoneWidget` bileşenine çoklu dosya doğrulama (`MAX_FILES = 25`, homojen uzantı denetimi, `validation_error` sinyali ve `set_files` metodu) ve zenginleştirilmiş çoklu dosya yükleme arayüzü eklenir; çoklu dosyaları arka planda GUI'yi dondurmadan, kaynak tüketimini optimize ederek ve dosya bazında hata toleransı sağlayarak sırayla işleyen `BatchExtractionWorker` (QThread) geliştirilir; `KastStudioWindow` üzerinde tekli ve çoklu dosya akışları birleştirilerek toplu ilerleme ve sonuç özeti sunulur.

**Tech Stack:** Python 3.10+, PySide6 6.5+ (Qt6), `python-docx`, `pdfplumber`, `pytest`, `pytest-asyncio`.

**Spec:** Kullanıcı talebi: 25 adede kadar çoklu dosya seçimi ("Gözat" veya sürükle-bırak); homojen format zorunluluğu (tümü .docx veya tümü .pdf, aksi halde açık hata mesajı); kaynakları yormayan ve uygulamayı çökertmeyen güvenli gruplar halinde işleme ve sonuçlandırma.

## Global Constraints

- **Maksimum Dosya Sınırı:** En fazla 25 dosya (`MAX_FILES = 25`). 25'ten fazla dosya seçilirse işlem reddedilmeli ve açık bir hata mesajı gösterilmelidir.
- **Homojen Format Kuralı:** Seçilen tüm dosyalar istisnasız aynı formatta olmalıdır (ya hepsi `.docx` ya da hepsi `.pdf`). Karışık dosya seçimi veya desteklenmeyen formatlar reddedilmeli ve açıklayıcı hata mesajı verilmelidir.
- **Geriye Dönük Uyumluluk:** Tek dosya sürükleme veya seçme davranışı, mevcut API sözleşmesi (`set_file`, `get_file_path`, `file_selected`) bozulmadan çalışmaya devam etmelidir.
- **Kaynak Güvenliği ve Kilit Koruması:** LibreOffice (`soffice --headless`) ve Word COM motorlarının eşzamanlı çoklu profil kilitleme çakışmalarını (`profile lock deadlock`) ve CPU/RAM aşırı yüklenmesini önlemek için dosyalar arka plan iş parçacığında güvenli sıralı döngü (sequential batch, concurrency limit = 1) ile tek tek işlenmelidir.
- **Hata Toleransı (Fault-Tolerance):** Toplu işlem sırasında bir dosyada hata çıkması durumunda tüm süreç çökmemeli; hatalı dosya günlüğe kaydedilip diğer dosyaların işlenmesine devam edilmelidir. İşlem sonunda özet raporda başarılı ve hatalı dosya sayıları listelenmelidir.
- **Living Architecture Uyumu:** Değişiklikler için yeni bir ADR (`adr-007-batch-file-processing-pipeline.md`) oluşturulmalı, wiki sayfaları güncellenmeli ve `log.md` günlüğüne işlenmelidir.

---

### Task 1: `DropZoneWidget` Çoklu Dosya Doğrulama ve Yönetim Altyapısı

**Files:**
- Modify: `src/gui.py:183-385`
- Test: `tests/test_gui.py`

**Interfaces:**
- Consumes: `os.path`, `PySide6.QtCore.Signal`, `PySide6.QtWidgets.QFileDialog`
- Produces: 
  - `DropZoneWidget.MAX_FILES: int = 25`
  - `DropZoneWidget.files_selected: Signal(list)`
  - `DropZoneWidget.validation_error: Signal(str)`
  - `DropZoneWidget.validate_file_paths(paths: list[str]) -> Tuple[bool, str, list[str]]`
  - `DropZoneWidget.set_files(paths: list[str]) -> bool`
  - `DropZoneWidget.get_files() -> list[str]`
  - Geriye dönük uyumlu `set_file(path: str) -> None` ve `get_file_path() -> Optional[str]`

- [ ] **Step 1: Failing testleri yaz (`tests/test_gui.py`)**

```python
def test_drop_zone_widget_multi_file_validation_success(qapp, tmp_path):
    """DropZoneWidget homojen birden fazla dosyayı başarıyla doğrular ve listeye alır."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    f1 = tmp_path / "part1.docx"
    f2 = tmp_path / "part2.docx"
    f1.write_text("dummy1")
    f2.write_text("dummy2")

    emitted_files = []
    widget.files_selected.connect(lambda files: emitted_files.append(files))

    ok = widget.set_files([str(f1), str(f2)])
    assert ok is True
    assert widget.get_files() == [str(f1), str(f2)]
    assert widget.get_file_path() == str(f1)  # Geriye dönük uyumluluk
    assert len(emitted_files) == 1
    assert emitted_files[0] == [str(f1), str(f2)]


def test_drop_zone_widget_mixed_file_types_rejected(qapp, tmp_path):
    """DropZoneWidget karışık uzantılı dosya seçimlerini (.docx + .pdf) reddeder ve validation_error sinyali yayar."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    docx_file = tmp_path / "part1.docx"
    pdf_file = tmp_path / "part2.pdf"
    docx_file.write_text("docx")
    pdf_file.write_text("pdf")

    errors = []
    widget.validation_error.connect(lambda err: errors.append(err))

    ok = widget.set_files([str(docx_file), str(pdf_file)])
    assert ok is False
    assert widget.get_files() == []
    assert len(errors) == 1
    assert "aynı türden" in errors[0]


def test_drop_zone_widget_max_files_limit_rejected(qapp, tmp_path):
    """DropZoneWidget 25'ten fazla dosya verildiğinde seçimi reddeder ve hata mesajı üretir."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    files = []
    for i in range(26):
        f = tmp_path / f"part_{i}.docx"
        f.write_text("content")
        files.append(str(f))

    errors = []
    widget.validation_error.connect(lambda err: errors.append(err))

    ok = widget.set_files(files)
    assert ok is False
    assert widget.get_files() == []
    assert len(errors) == 1
    assert "En fazla 25 dosya" in errors[0]


def test_drop_zone_widget_unsupported_extensions_rejected(qapp, tmp_path):
    """DropZoneWidget desteklenmeyen uzantılı dosyaları (.txt, .xlsx) reddeder."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("notes")

    errors = []
    widget.validation_error.connect(lambda err: errors.append(err))

    ok = widget.set_files([str(txt_file)])
    assert ok is False
    assert widget.get_files() == []
    assert len(errors) == 1
    assert "Desteklenmeyen dosya formatı" in errors[0]
```

- [ ] **Step 2: Testleri çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_drop_zone_widget_multi_file_validation_success or test_drop_zone_widget_mixed_file_types_rejected or test_drop_zone_widget_max_files_limit_rejected or test_drop_zone_widget_unsupported_extensions_rejected" -v`
Expected: FAIL (AttributeError: 'DropZoneWidget' object has no attribute 'set_files' / 'files_selected' / 'validation_error')

- [ ] **Step 3: `DropZoneWidget` sınıfına çoklu dosya doğrulama ve seçim mantığını ekle (`src/gui.py`)**

```python
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
```

- [ ] **Step 4: Testleri çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_drop_zone_widget_multi_file_validation_success or test_drop_zone_widget_mixed_file_types_rejected or test_drop_zone_widget_max_files_limit_rejected or test_drop_zone_widget_unsupported_extensions_rejected" -v`
Expected: PASS

- [ ] **Step 5: Değişiklikleri commit'le**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): add multi-file validation rules and state management to DropZoneWidget"
```

---

### Task 2: `DropZoneWidget` Çoklu Dosya Görsel Arayüzü ve Sürükle-Bırak Entegrasyonu

**Files:**
- Modify: `src/gui.py:270-385`
- Test: `tests/test_gui.py`

**Interfaces:**
- Consumes: `DropZoneWidget._file_paths`, `DropZoneWidget.validate_file_paths`
- Produces:
  - `DropZoneWidget._update_loaded_ui_for_files(paths: list[str])`
  - Güncellenmiş `_open_file_dialog()` (`QFileDialog.getOpenFileNames` ile çoklu seçim)
  - Güncellenmiş `dragEnterEvent` ve `dropEvent` (çoklu dosya yakalama ve doğrulama)

- [ ] **Step 1: Failing testleri yaz (`tests/test_gui.py`)**

```python
def test_drop_zone_widget_multi_file_visual_state(qapp, tmp_path):
    """DropZoneWidget çoklu dosya seçildiğinde rozet metnini ve toplam boyut bilgisini doğru görüntüler."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    f1 = tmp_path / "film_part1.docx"
    f2 = tmp_path / "film_part2.docx"
    f3 = tmp_path / "film_part3.docx"
    for f in (f1, f2, f3):
        f.write_bytes(b"0" * 2048)

    widget.set_files([str(f1), str(f2), str(f3)])

    assert "DOCX (3 Dosya)" in widget.lbl_badge.text()
    assert "3 adet senaryo dosyası hazır" in widget.lbl_filename.text()
    assert "KB" in widget.lbl_filesize.text()
    assert str(widget.lbl_filename.toolTip()).count("film_part") == 3


def test_drop_zone_widget_multi_file_drag_and_drop(qapp, tmp_path):
    """DropZoneWidget çoklu dosya sürükle-bırak olaylarını kabul eder ve dosyaları yükler."""
    from PySide6.QtCore import QPoint, QUrl, QMimeData, Qt
    from PySide6.QtGui import QDropEvent
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    f1 = tmp_path / "part1.pdf"
    f2 = tmp_path / "part2.pdf"
    f1.write_text("pdf1")
    f2.write_text("pdf2")

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(f1)), QUrl.fromLocalFile(str(f2))])

    drop_event = QDropEvent(
        QPoint(10, 10),
        Qt.CopyAction,
        mime,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    widget.dropEvent(drop_event)

    assert drop_event.isAccepted()
    assert len(widget.get_files()) == 2
    assert "PDF (2 Dosya)" in widget.lbl_badge.text()


def test_drop_zone_widget_dialog_multi_selection(qapp, tmp_path, monkeypatch):
    """_open_file_dialog çağrıldığında getOpenFileNames sonucunu set_files ile yükler."""
    from PySide6.QtWidgets import QFileDialog
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    f1 = tmp_path / "scene1.docx"
    f2 = tmp_path / "scene2.docx"
    f1.write_text("d1")
    f2.write_text("d2")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(f1), str(f2)], "Dublaj Senaryoları (*.docx *.pdf)"),
    )

    widget._open_file_dialog()
    assert len(widget.get_files()) == 2
    assert widget.get_files() == [str(f1), str(f2)]
```

- [ ] **Step 2: Testleri çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_drop_zone_widget_multi_file_visual_state or test_drop_zone_widget_multi_file_drag_and_drop or test_drop_zone_widget_dialog_multi_selection" -v`
Expected: FAIL

- [ ] **Step 3: `DropZoneWidget` görsel durumunu ve dialog/drag-drop metodlarını güncelle (`src/gui.py`)**

```python
    def _open_file_dialog(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Dublaj Senaryo Dosyaları Seçin (En Fazla 25 Dosya)",
            "",
            "Dublaj Senaryoları (*.docx *.pdf);;Word Belgeleri (*.docx);;PDF Belgeleri (*.pdf);;Tüm Dosyalar (*.*)",
        )
        if file_paths:
            self.set_files(file_paths)

    def _update_loaded_ui_for_files(self, paths: list[str]) -> None:
        count = len(paths)
        ext = os.path.splitext(paths[0])[1].lower()
        is_pdf = (ext == ".pdf")

        total_bytes = sum(os.path.getsize(p) for p in paths if os.path.exists(p))
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
            self.lbl_filename.setText(f"{count} adet senaryo dosyası hazır")
            tooltip_text = "\n".join(f"• {os.path.basename(p)}" for p in paths)
            self.lbl_filename.setToolTip(tooltip_text)
            self.lbl_filesize.setText(f"Toplam Boyut: {size_str} • En Fazla {self.MAX_FILES} Dosya")

        self.lbl_badge.setStyleSheet(
            f"background-color: {badge_color}; color: #ffffff; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 4px;"
        )

        self.empty_container.setVisible(False)
        self.loaded_container.setVisible(True)
        self._update_border_style()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            local_paths = [u.toLocalFile() for u in urls if u.toLocalFile()]
            if any(p.lower().endswith((".docx", ".pdf")) for p in local_paths):
                event.acceptProposedAction()
                self._update_border_style(is_hover=True)

    def dropEvent(self, event) -> None:
        self._update_border_style(is_hover=False)
        local_paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        filtered_paths = [p for p in local_paths if p.lower().endswith((".docx", ".pdf"))]
        if filtered_paths:
            success = self.set_files(filtered_paths)
            if success:
                event.acceptProposedAction()
```

- [ ] **Step 4: Testleri çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_drop_zone_widget_multi_file_visual_state or test_drop_zone_widget_multi_file_drag_and_drop or test_drop_zone_widget_dialog_multi_selection" -v`
Expected: PASS

- [ ] **Step 5: Değişiklikleri commit'le**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): integrate multi-file visual indicators and drag-drop/dialog handling into DropZoneWidget"
```

---

### Task 3: Kaynak Güvenli ve Sıralı Toplu İşleme Motoru (`BatchExtractionWorker`)

**Files:**
- Modify: `src/gui.py:519-570`
- Test: `tests/test_gui.py`

**Interfaces:**
- Consumes: `src.gui.process_dubbing_file`, `src.models.CastExtractionResult`
- Produces:
  - `BatchExtractionWorker(QThread)`:
    - Parametreler: `file_paths: list[str]`, `sort_by: str`, `in_place: bool`, `standalone: bool`, `output_dir: Optional[str] = None`
    - Sinyaller:
      - `progress = Signal(int, str)`
      - `log = Signal(str)`
      - `file_started = Signal(int, int, str)`  # (current_index, total, filename)
      - `file_completed = Signal(int, int, str, object)`  # (current_index, total, output_path, result)
      - `file_error = Signal(int, int, str, str)`  # (current_index, total, filename, error_msg)
      - `all_finished = Signal(list)`  # list of summary dicts
  - Geriye dönük uyumluluk: `ExtractionWorker` tek dosya için `BatchExtractionWorker([file_path], ...)` sınıfını sarmalar veya miras alır.

- [ ] **Step 1: Failing testleri yaz (`tests/test_gui.py`)**

```python
def test_batch_extraction_worker_sequential_execution(tmp_path, monkeypatch):
    """BatchExtractionWorker birden fazla dosyayı sırayla işler, ilerleme yüzdesini düzgün yayar ve tümünü tamamlar."""
    import src.gui as gui_mod
    from src.gui import BatchExtractionWorker
    from src.models import CastExtractionResult, CharacterStats

    char = CharacterStats(name="DENEME", first_seen_order=1, line_count=5, pages={1})
    dummy_res = CastExtractionResult(characters=[char], total_lines=5, total_pages=1)

    processed_files = []

    def mock_process_dubbing_file(file_path, output_path=None, sort_by="appearance", in_place=False, standalone=True, progress_callback=None):
        processed_files.append(file_path)
        if progress_callback:
            progress_callback(50, "Ayrıştırılıyor...")
        out = output_path or f"{file_path}_kast.docx"
        return out, dummy_res

    monkeypatch.setattr(gui_mod, "process_dubbing_file", mock_process_dubbing_file)

    f1 = tmp_path / "ep1.docx"
    f2 = tmp_path / "ep2.docx"
    f1.write_text("ep1")
    f2.write_text("ep2")

    worker = BatchExtractionWorker(
        file_paths=[str(f1), str(f2)],
        sort_by="appearance",
        in_place=False,
        standalone=True,
    )

    progress_events = []
    completed_events = []
    all_summary = []

    worker.progress.connect(lambda pct, msg: progress_events.append((pct, msg)))
    worker.file_completed.connect(lambda idx, tot, out, res: completed_events.append((idx, tot, out)))
    worker.all_finished.connect(lambda summary: all_summary.extend(summary))

    worker.run()

    # Dosyaların sırayla işlendiğini doğrula
    assert processed_files == [str(f1), str(f2)]
    assert len(completed_events) == 2
    assert completed_events[0] == (1, 2, f"{f1}_kast.docx")
    assert completed_events[1] == (2, 2, f"{f2}_kast.docx")
    assert len(all_summary) == 2
    assert all_summary[0]["status"] == "success"
    assert all_summary[1]["status"] == "success"
    # İlerleme %100'e ulaşmalı
    assert progress_events[-1][0] == 100


def test_batch_extraction_worker_fault_tolerance(tmp_path, monkeypatch):
    """BatchExtractionWorker bir dosyada hata çıkarsa durmaz; hatayı kaydeder ve sonraki dosyayı işlemeye devam eder."""
    import src.gui as gui_mod
    from src.gui import BatchExtractionWorker
    from src.models import CastExtractionResult

    def mock_process_dubbing_file(file_path, **kwargs):
        if "corrupt" in file_path:
            raise ValueError("Bozuk XML yapısı!")
        return f"{file_path}_kast.docx", CastExtractionResult([], 0, 1)

    monkeypatch.setattr(gui_mod, "process_dubbing_file", mock_process_dubbing_file)

    f1 = tmp_path / "corrupt.docx"
    f2 = tmp_path / "valid.docx"
    f1.write_text("bad")
    f2.write_text("good")

    worker = BatchExtractionWorker(
        file_paths=[str(f1), str(f2)],
        sort_by="count",
        in_place=False,
        standalone=True,
    )

    error_events = []
    all_summary = []
    worker.file_error.connect(lambda idx, tot, path, err: error_events.append((idx, tot, path, err)))
    worker.all_finished.connect(lambda summary: all_summary.extend(summary))

    worker.run()

    assert len(error_events) == 1
    assert "Bozuk XML" in error_events[0][3]
    assert len(all_summary) == 2
    assert all_summary[0]["status"] == "error"
    assert all_summary[1]["status"] == "success"
```

- [ ] **Step 2: Testleri çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_batch_extraction_worker_sequential_execution or test_batch_extraction_worker_fault_tolerance" -v`
Expected: FAIL (ImportError / AttributeError: cannot import name 'BatchExtractionWorker' from 'src.gui')

- [ ] **Step 3: `BatchExtractionWorker` ve geriye dönük uyumlu `ExtractionWorker` uygulamasını geliştir (`src/gui.py`)**

```python
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
    ):
        super().__init__()
        self.file_paths = file_paths
        self.sort_by = sort_by
        self.in_place = in_place
        self.standalone = standalone
        self.output_dir = output_dir

    def run(self) -> None:
        total_files = len(self.file_paths)
        if total_files == 0:
            self.progress.emit(100, "İşlenecek dosya yok.")
            self.all_finished.emit([])
            return

        summary: list[dict] = []
        file_weight = 100.0 / total_files

        self.log.emit(f"[*] Toplu işlem başlatıldı: Toplam {total_files} senaryo dosyası işlenecek.")

        for idx, file_path in enumerate(self.file_paths, start=1):
            filename = os.path.basename(file_path)
            self.file_started.emit(idx, total_files, filename)
            self.log.emit(f"[{idx}/{total_files}] Başlatılıyor: {filename}")

            base_pct = int((idx - 1) * file_weight)

            def sub_progress(sub_pct: int, msg: str):
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
```

- [ ] **Step 4: Testleri çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_batch_extraction_worker_sequential_execution or test_batch_extraction_worker_fault_tolerance or test_extraction_worker_success or test_extraction_worker_error" -v`
Expected: PASS

- [ ] **Step 5: Değişiklikleri commit'le**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): introduce BatchExtractionWorker with resource-safe sequential execution and fault tolerance"
```

---

### Task 4: `KastStudioWindow` Çoklu Dosya Entegrasyonu ve Sonuç Ekranı

**Files:**
- Modify: `src/gui.py:572-945`
- Test: `tests/test_gui.py`

**Interfaces:**
- Consumes: `DropZoneWidget.files_selected`, `DropZoneWidget.validation_error`, `BatchExtractionWorker`
- Produces:
  - `KastStudioWindow._on_files_selected(paths: list[str])`
  - `KastStudioWindow._on_validation_error(err_msg: str)`
  - Güncellenmiş `_start_extraction()` (`BatchExtractionWorker` bağlantısı)
  - `KastStudioWindow._on_batch_finished(summary: list[dict])`
  - Çoklu dosya için zenginleştirilmiş sonuç kartı ve klasör açma davranışı

- [ ] **Step 1: Failing testleri yaz (`tests/test_gui.py`)**

```python
def test_kast_studio_window_multi_file_flow(qapp, tmp_path, monkeypatch):
    """KastStudioWindow çoklu dosya seçildiğinde PDF/DOCX kontrollerini ayarlar, worker'ı başlatır ve sonuç özetini gösterir."""
    import src.gui as gui_mod
    from src.gui import KastStudioWindow
    from src.models import CastExtractionResult, CharacterStats

    window = KastStudioWindow()
    window.show()

    f1 = tmp_path / "part1.docx"
    f2 = tmp_path / "part2.docx"
    f1.write_text("part1")
    f2.write_text("part2")

    window.drop_zone.set_files([str(f1), str(f2)])

    assert window.btn_extract.isEnabled()
    assert "[BİLGİ] 2 adet DOCX" in window.log_area.toPlainText()

    # Worker.start metodunu yakala
    worker_instances = []
    monkeypatch.setattr(gui_mod.BatchExtractionWorker, "start", lambda self: worker_instances.append(self))

    window._start_extraction()
    assert len(worker_instances) == 1
    worker = worker_instances[0]
    assert worker.file_paths == [str(f1), str(f2)]

    # Worker tamamlandığında sonuç kartı güncellemesi
    dummy_summary = [
        {"path": str(f1), "output": str(tmp_path / "part1_kast.docx"), "status": "success", "result": CastExtractionResult([CharacterStats("ALİ", 1, 10, {1})], 10, 1)},
        {"path": str(f2), "output": str(tmp_path / "part2_kast.docx"), "status": "success", "result": CastExtractionResult([CharacterStats("VELİ", 1, 5, {1})], 5, 1)},
    ]
    window._on_batch_finished(dummy_summary)

    assert window.result_card.isVisible()
    assert "2/2 dosya başarıyla oluşturuldu" in window.lbl_result_text.text()
    assert "Toplam: 2 Karakter • 15 Replik" in window.lbl_result_text.text()


def test_kast_studio_window_validation_error_displayed(qapp, tmp_path):
    """KastStudioWindow doğrulama hatası sinyali aldığında log paneline kırmızı hata basar ve durumu günceller."""
    from src.gui import KastStudioWindow

    window = KastStudioWindow()
    window.show()

    f_docx = tmp_path / "part1.docx"
    f_pdf = tmp_path / "part2.pdf"
    f_docx.write_text("d")
    f_pdf.write_text("p")

    window.drop_zone.set_files([str(f_docx), str(f_pdf)])

    assert "Doğrulama Hatası" in window.lbl_status.text()
    assert "aynı türden dosyalar" in window.log_area.toPlainText()
    assert not window.btn_extract.isEnabled()
```

- [ ] **Step 2: Testleri çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_kast_studio_window_multi_file_flow or test_kast_studio_window_validation_error_displayed" -v`
Expected: FAIL

- [ ] **Step 3: `KastStudioWindow` sınıfına çoklu dosya ve toplu sonuç yönetimini ekle (`src/gui.py`)**

```python
    def _init_ui(self) -> None:
        # ...
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_selected.connect(self._on_files_selected)
        self.drop_zone.validation_error.connect(self._on_validation_error)
        # Geriye dönük uyumluluk için file_selected bağlantısı:
        self.drop_zone.file_selected.connect(self._on_file_selected)
        main_layout.addWidget(self.drop_zone)
        # ...

    def _on_files_selected(self, file_paths: list[str]) -> None:
        if not file_paths:
            return
        self.btn_extract.setEnabled(True)
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
                    f"<span style='color:#38bdf8;'>[BİLGİ] {count} adet PDF senaryosu algılandı. (Doğrudan ayrıştırma devrede)</span>"
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
                    f"<span style='color:#38bdf8;'>[BİLGİ] {count} adet DOCX senaryosu algılandı. (Word/LibreOffice sayfalama devrede)</span>"
                )

    def _on_validation_error(self, err_msg: str) -> None:
        self.btn_extract.setEnabled(False)
        self.lbl_status.setText("● Durum: Doğrulama Hatası")
        self.log_area.append(f"<span style='color:#f43f5e; font-weight:bold;'>[!] Doğrulama Hatası: {err_msg}</span>")

    def _start_extraction(self) -> None:
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
        total_lines = sum(getattr(s["result"], "total_lines", 0) for s in successes if s.get("result"))

        if len(errors) == 0:
            self.lbl_status.setText("● Durum: Tamamlandı")
            self.lbl_result_text.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
            self.lbl_result_text.setText(
                f"✓ {len(successes)}/{total} dosya başarıyla oluşturuldu! (Toplam: {total_chars} Karakter • {total_lines} Replik)"
            )
        else:
            self.lbl_status.setText(f"● Durum: Tamamlandı ({len(errors)} hata)")
            self.lbl_result_text.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 13px;")
            self.lbl_result_text.setText(
                f"⚠️ Kısmi Tamamlandı: {len(successes)}/{total} başarılı, {len(errors)} dosyada hata oluştu."
            )

        if total > 1:
            self.btn_open_file.setText("📄 Son Dosyayı Aç")
        else:
            self.btn_open_file.setText("📄 Dosyayı Aç")
```

- [ ] **Step 4: Testleri çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k "test_kast_studio_window_multi_file_flow or test_kast_studio_window_validation_error_displayed" -v`
Expected: PASS

- [ ] **Step 5: Değişiklikleri commit'le**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): integrate multi-file batch execution and summary reporting in KastStudioWindow"
```

---

### Task 5: Tüm GUI Test Paketinin Doğrulanması ve Regresyon Testleri

**Files:**
- Modify: `tests/test_gui.py`
- Test: `tests/test_gui.py`

**Interfaces:**
- Consumes: Tüm `src.gui` sınıfları ve test fonksiyonları
- Produces: %100 geçen birim ve entegrasyon test paketi (mevcut 23 test + yeni çoklu dosya testleri)

- [ ] **Step 1: `tests/test_gui.py` dosyasına regresyon ve sınır değer testlerini ekle**
- 25 tam sınır dosya seçimi testi.
- Boş liste ve None path testleri.
- Kısmi hatalı çoklu dosya akışında GUI buton durumlarının doğrulanması.

- [ ] **Step 2: Tüm GUI test paketini çalıştır**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -v`
Expected: Tüm testler (mevcut ve yeni) yeşil (PASS).

- [ ] **Step 3: Kod biçim ve import temizliği yap**

- [ ] **Step 4: Commit**

```bash
git add tests/test_gui.py
git commit -m "test(gui): complete multi-file batch processing test suite with 100% coverage"
```

---

### Task 6: Living Architecture Wiki ve ADR Dokümantasyonu (`AGENTS.md` Kural Seti)

**Files:**
- Create: `docs/kast-app-wiki/architecture-decisions/adr-007-batch-file-processing-pipeline.md`
- Modify: `docs/kast-app-wiki/interfaces-and-runtime/qt6-desktop-gui.md`
- Modify: `docs/kast-app-wiki/index.md`
- Modify: `docs/kast-app-wiki/log.md`

**Interfaces:**
- Consumes: ADR şablonu, Obsidian uyumlu `[[wikilink]]` sözdizimi, `log.md` kronolojik formatı
- Produces:
  - `adr-007-batch-file-processing-pipeline.md`: 25 dosya sınırı, homojen uzantı kuralı ve LibreOffice/Word kilit koruması için sıralı batch mimarisi.
  - Güncellenmiş `qt6-desktop-gui.md`
  - Güncellenmiş `index.md` (ADR-007 referansı)
  - Güncellenmiş `log.md` (Tarih ve ajan kayıtları)

- [ ] **Step 1: `adr-007-batch-file-processing-pipeline.md` belgesini oluştur**
  - Zorunlu 5 bölüm: Bağlam, Karar, Alternatifler, Sonuçlar ve İlgili Sayfalar.
  - Neden 25 dosya sınırı konulduğu ve neden paralel yerine sıralı (sequential, concurrency limit=1) iş parçacığı seçildiği (LibreOffice soffice user-profile kilitlenmelerini önleme) detaylandırılır.

- [ ] **Step 2: `qt6-desktop-gui.md` belgesine `BatchExtractionWorker` ve çoklu dosya DropZone bilgilerini işle**

- [ ] **Step 3: `index.md` fihristine ADR-007 bağlantısını ekle**

- [ ] **Step 4: `log.md` dosyasına kronolojik kayıt düş**

- [ ] **Step 5: Wiki lint denetimi yap (Kırık wikilink ve yetim sayfa kontrolü)**

- [ ] **Step 6: Wiki güncellemelerini commit'le**

```bash
git add docs/kast-app-wiki/
git commit -m "docs(wiki): document ADR-007 batch file processing pipeline and update living architecture"
```

---

## Self-Review Checklist

- **Spec Coverage:**
  - 25 dosyaya kadar çoklu dosya seçimi / sürükle-bırak: **Task 1 & Task 2**
  - Homojen dosya türü kuralı (hepsi .docx veya hepsi .pdf, aksi halde hata): **Task 1 & Task 4**
  - İşlemciyi yormayacak ve uygulamayı çökertmeyecek güvenli gruplar halinde işleme (LibreOffice kilit güvenliği için sıralı iş parçacığı): **Task 3**
  - Hata toleransı ve toplu sonuç ekranı: **Task 3 & Task 4**
  - AGENTS.md Living Architecture & ADR gereksinimleri: **Task 6**
- **Placeholder Scan:** "TODO", "TBD", "implement later" veya eksik kod blokları içermez.
- **Type & Interface Consistency:** `set_files(paths: list[str])`, `get_files() -> list[str]`, `validation_error = Signal(str)`, `BatchExtractionWorker` sinyal ve metot adları tüm görevlerde tutarlıdır.
