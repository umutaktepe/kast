import pytest
from src.gui import StudioTheme


def test_studio_theme_mockup_color_palette():
    """StudioTheme paletinin mockup görselindeki gece mavisi ve neon camgöbeği renklerini içerdiğini doğrular."""
    colors = StudioTheme.COLORS
    assert colors["bg_dark"] == "#0b0f19"
    assert colors["card_bg"] == "#0f172a"
    assert colors["accent_cyan"] in ("#00b4d8", "#06b6d4", "#38bdf8")
    assert colors["terminal_bg"] == "#080c14"
    
    css = StudioTheme.get_stylesheet()
    assert "#0b0f19" in css
    assert "#00b4d8" in css or "#06b6d4" in css


def test_studio_theme_stylesheet_contains_core_styles():
    """StudioTheme stil şablonunun modern renk ve widget tanımlarını içerdiğini doğrular."""
    css = StudioTheme.get_stylesheet()
    assert "#0b0f19" in css or "#0f172a" in css  # Dark background
    assert "QProgressBar" in css
    assert "QPushButton" in css
    assert "card-panel" in css


def test_studio_theme_colors_dictionary():
    """StudioTheme.COLORS sözlüğünün gerekli renk paletini eksiksiz barındırdığını doğrular."""
    expected_keys = {
        "bg_dark",
        "card_bg",
        "card_tile",
        "card_tile_selected",
        "border",
        "border_dashed",
        "border_focus",
        "text_main",
        "text_sub",
        "text_dim",
        "accent_cyan",
        "btn_primary",
        "btn_primary_hover",
        "btn_secondary",
        "terminal_bg",
        "badge_bg",
        "badge_border",
        "accent_green",
        "accent_red",
    }
    assert expected_keys.issubset(StudioTheme.COLORS.keys())
    for k in expected_keys:
        assert StudioTheme.COLORS[k].startswith("#")


def test_studio_theme_widget_selectors():
    """Temada QMainWindow, QWidget, card-panel, tile-option, QTextEdit, QStatusBar gibi bileşenlerin yer aldığını doğrular."""
    css = StudioTheme.get_stylesheet()
    for widget in ["QMainWindow", "QWidget", "card-panel", "tile-option", "QTextEdit", "QStatusBar", "btn-primary", "btn-clear"]:
        assert widget in css


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_drop_zone_widget_mockup_elements(qapp):
    """DropZoneWidget bileşeninin mockup görselindeki ikon, metin ve hapları barındırdığını doğrular."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    assert "Microsoft Word veya metin formatlı çeviri PDF'leri" in widget.lbl_subprompt.text()
    assert widget.badge_docx.text() == ".DOCX"
    assert widget.badge_pdf.text() == ".PDF"
    assert "Dosya Seç" in widget.btn_browse.text()


def test_drop_zone_widget_file_selection(qapp, tmp_path):
    """DropZoneWidget dosya seçimi, doğrulama ve temizleme davranışını test eder."""
    from src.gui import DropZoneWidget

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


def test_drop_zone_widget_signals_and_validation(qapp, tmp_path):
    """DropZoneWidget sinyal yayımı ve geçersiz uzantı reddini test eder."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    emitted = []
    widget.file_selected.connect(lambda path: emitted.append(path))

    # Geçersiz uzantı
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("hello")
    widget.set_file(str(txt_file))
    assert widget.get_file_path() is None
    assert len(emitted) == 0

    # Geçerli dosya ile sinyal tetiklenmesi
    docx_file = tmp_path / "valid.docx"
    docx_file.write_text("content")
    widget.set_file(str(docx_file))
    assert len(emitted) == 1
    assert emitted[0] == str(docx_file)


def test_drop_zone_widget_large_file_and_remove_button(qapp, tmp_path):
    """DropZoneWidget MB boyut formatlama ve '✕ Değiştir' butonunun clear çağrısını test eder."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    widget.show()
    large_pdf = tmp_path / "large_script.pdf"
    # 1.5 MB dosya oluştur
    large_pdf.write_bytes(b"0" * int(1.5 * 1024 * 1024))
    widget.set_file(str(large_pdf))

    assert "MB" in widget.lbl_filesize.text()
    assert not widget.loaded_container.isHidden()
    assert widget.empty_container.isHidden()

    # Değiştir butonuna tıklandığında temizleme
    widget.btn_remove.click()
    assert widget.get_file_path() is None
    assert widget.loaded_container.isHidden()
    assert not widget.empty_container.isHidden()


def test_drop_zone_widget_drag_and_drop_events(qapp, tmp_path):
    """DropZoneWidget dragEnter, dragLeave ve dropEvent işleyişini test eder."""
    from PySide6.QtCore import QPoint, QUrl, QMimeData, Qt
    from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()

    # 1. Geçersiz uzantılı dragEnterEvent
    mime_invalid = QMimeData()
    mime_invalid.setUrls([QUrl.fromLocalFile(str(tmp_path / "test.txt"))])
    event_invalid = QDragEnterEvent(
        QPoint(10, 10),
        Qt.CopyAction,
        mime_invalid,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    widget.dragEnterEvent(event_invalid)
    assert not event_invalid.isAccepted()

    # 2. Geçerli uzantılı dragEnterEvent
    valid_file = tmp_path / "dubbing.docx"
    valid_file.write_text("sample")
    mime_valid = QMimeData()
    mime_valid.setUrls([QUrl.fromLocalFile(str(valid_file))])
    event_valid = QDragEnterEvent(
        QPoint(10, 10),
        Qt.CopyAction,
        mime_valid,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    widget.dragEnterEvent(event_valid)
    assert event_valid.isAccepted()
    assert "#38bdf8" in widget.styleSheet()  # Hover border color

    # 3. dragLeaveEvent
    event_leave = QDragLeaveEvent()
    widget.dragLeaveEvent(event_leave)
    assert "#223554" in widget.styleSheet()  # Default border color

    # 4. dropEvent
    drop_event = QDropEvent(
        QPoint(10, 10),
        Qt.CopyAction,
        mime_valid,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    widget.dropEvent(drop_event)
    assert drop_event.isAccepted()
    assert widget.get_file_path() == str(valid_file)
    assert "#10b981" in widget.styleSheet()  # Loaded border color


def test_drop_zone_widget_open_file_dialog(qapp, tmp_path, monkeypatch):
    """_open_file_dialog fonksiyonunun seçilen dosyayı başarıyla ayarladığını test eder."""
    from PySide6.QtWidgets import QFileDialog
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    fake_file = tmp_path / "dialog_selected.pdf"
    fake_file.write_text("pdf dummy")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(fake_file)], "PDF Belgeleri (*.pdf)"),
    )

    widget._open_file_dialog()
    assert widget.get_file_path() == str(fake_file)
    assert "PDF" in widget.lbl_badge.text()


def test_option_tile_widget(qapp):
    """OptionTileWidget seçim durumlarını ve alt metin desteğini test eder."""
    from src.gui import OptionTileWidget

    tile = OptionTileWidget(
        title="Ayrı dosya olarak kaydet",
        subtext="(<ad>_kast.docx)",
        is_selected=True,
    )
    assert tile.is_selected() is True
    assert "Ayrı dosya olarak kaydet" in tile.lbl_title.text()
    assert "(<ad>_kast.docx)" in tile.lbl_subtext.text()
    assert tile.property("selected") == "true"

    tile.set_selected(False)
    assert tile.is_selected() is False
    assert tile.property("selected") == "false"

    # Alt başlıksız durum testi
    tile_no_sub = OptionTileWidget(title="Yalnızca başlık", subtext=None, is_selected=False)
    assert tile_no_sub.lbl_subtext is None
    assert tile_no_sub.is_selected() is False


def test_option_tile_widget_click_event(qapp):
    """OptionTileWidget mousePressEvent ile sol tıklandığında clicked sinyali yaydığını test eder."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from src.gui import OptionTileWidget

    tile = OptionTileWidget(title="Test", is_selected=False)
    clicked = []
    tile.clicked.connect(lambda: clicked.append(True))

    # Sol tık
    pos = QPointF(5.0, 5.0)
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pos,
        pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    tile.mousePressEvent(event)
    assert len(clicked) == 1

    # Sağ tık (sinyal tetiklenmemeli)
    right_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pos,
        pos,
        Qt.MouseButton.RightButton,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
    )
    tile.mousePressEvent(right_event)
    assert len(clicked) == 1




def test_option_tile_widget_compatibility_and_group(qapp):
    """OptionTileWidget isChecked/setChecked uyumluluğunu, grup karşılıklı dışlamasını ve devre dışı durumunu test eder."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from src.gui import OptionTileGroup, OptionTileWidget

    t1 = OptionTileWidget("Seçenek 1", is_selected=True)
    t2 = OptionTileWidget("Seçenek 2", is_selected=False)
    group = OptionTileGroup([t1, t2])

    assert t1.isChecked() is True
    assert t2.isChecked() is False

    # t2'yi setChecked(True) ile seçince t1 kapanmalı
    t2.setChecked(True)
    assert t1.isChecked() is False
    assert t2.isChecked() is True

    # Devre dışı bırakıldığında tıklama yok sayılmalı
    t1.setEnabled(False)
    assert not t1.isEnabled()
    pos = QPointF(5.0, 5.0)
    click_evt = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pos,
        pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    t1.mousePressEvent(click_evt)
    # t1 devre dışı olduğu için seçilmemeli, t2 seçili kalmalı
    assert t1.isChecked() is False
    assert t2.isChecked() is True


def test_kast_studio_window_mockup_layout(qapp):
    """KastStudioWindow bileşenlerinin mockup başlıklarını, rozetini, terminal başlığını ve kartlarını test eder."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from src.gui import KastStudioWindow

    window = KastStudioWindow()
    # Başlık ve Rozet
    assert "Windows Studio Edition • Qt6" in window.lbl_badge.text()
    assert "Kast 2.0" in window.lbl_title_prefix.text()
    assert "Dublaj Kast Çıkarma" in window.lbl_title_suffix.text()
    assert "diyalogları ve karakter listesini otomatik analiz eder" in window.lbl_subtitle.text()

    # İki Kart Paneli
    assert "Karakter Sıralama" in window.lbl_sort_title.text()
    assert "Çıktı Seçenekleri" in window.lbl_out_title.text()
    assert "İlk Görünme Sırası" in window.tile_appearance.lbl_title.text()
    assert "Replik Sayısına Göre" in window.tile_count.lbl_title.text()
    assert "Karakter Adına Göre" in window.tile_name.lbl_title.text()
    assert "Ayrı dosya olarak kaydet" in window.tile_standalone.lbl_title.text()
    assert "(<ad>_kast.docx)" in window.tile_standalone.lbl_subtext.text()
    assert "Orijinal Word dökümanının sonuna ekle" in window.tile_inplace.lbl_title.text()
    assert "Çıktı Biçimi: .docx Tablo" in window.lbl_output_meta.text()

    # Butonlar
    assert "Kast Tablosunu Çıkar" in window.btn_extract.text()
    assert "Temizle" in window.btn_clear.text()

    # Durum ve İlerleme Çubuğu
    assert "Durum: Hazır" in window.lbl_status.text()
    assert window.lbl_pct.text() == "%0"
    assert not window.progress_bar.isTextVisible()
    assert window.progress_bar.height() == 6

    # Terminal / Günlük
    assert "İŞLEM GÜNLÜĞÜ" in window.lbl_log_title.text()
    assert "Terminal hazır" in window.lbl_log_meta.text()
    assert window.log_area.isReadOnly()

    # Durum Çubuğu (StatusBar)
    assert "PySide6 Modern Frame  |  Hazır" in window.lbl_status_left.text()
    assert "Encoding: UTF-8" in window.lbl_status_right.text()

    # Kart içi tıklama ile karşılıklı dışlama (Mutual Exclusion)
    assert window.tile_appearance.isChecked() is True
    assert window.tile_count.isChecked() is False

    # tile_count'a sol tık
    pos = QPointF(10.0, 10.0)
    click_evt = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pos,
        pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.tile_count.mousePressEvent(click_evt)
    assert window.tile_count.isChecked() is True
    assert window.tile_appearance.isChecked() is False
    assert window.tile_name.isChecked() is False


def test_kast_studio_window_responsive_layout_non_fullscreen(qapp):
    """Pencere tam ekran olmadığında veya küçültüldüğünde etiketlerin ezilmediğini ve çakışmadığını test eder."""
    from src.gui import KastStudioWindow

    window = KastStudioWindow()
    window.resize(800, 600)
    window.show()
    qapp.processEvents()

    # 1. OptionTileWidget başlık ve alt metinleri sıfır yüksekliğe ezilmemeli
    assert window.tile_appearance.lbl_title.height() > 0
    assert window.tile_count.lbl_title.height() > 0
    assert window.tile_name.lbl_title.height() > 0
    assert window.tile_standalone.lbl_title.height() > 0
    assert window.tile_standalone.lbl_subtext.height() > 0
    assert window.tile_inplace.lbl_title.height() > 0

    # 2. DropZoneWidget elemanları birbiri üzerine binmemeli
    dz = window.drop_zone
    assert dz.btn_browse.height() > 0
    assert not dz.icon_container.geometry().intersects(dz.lbl_prompt.geometry())

    # 3. QScrollArea merkezi widget olarak mevcut olmalı
    assert hasattr(window, "scroll_area")


def test_kast_studio_window_interactions(qapp, tmp_path):

    """KastStudioWindow bileşenlerini, seçeneklerini ve akışını test eder."""
    from src.gui import KastStudioWindow

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


def test_extraction_worker_success(tmp_path, monkeypatch):
    """ExtractionWorker'ın process_dubbing_file'ı arka planda çağırıp sinyalleri doğru yaydığını test eder."""
    import src.gui as gui_mod
    from src.gui import ExtractionWorker
    from src.models import CastExtractionResult, CharacterStats

    char = CharacterStats(name="AHMET", first_seen_order=1, line_count=3, pages={1, 2})
    fake_result = CastExtractionResult(characters=[char], total_lines=3, total_pages=2)
    fake_saved = str(tmp_path / "output_kast.docx")

    call_kwargs = {}

    def fake_process_dubbing_file(**kwargs):
        call_kwargs.update(kwargs)
        if kwargs.get("progress_callback"):
            kwargs["progress_callback"](50, "Ayrıştırılıyor...")
        return fake_saved, fake_result

    monkeypatch.setattr(gui_mod, "process_dubbing_file", fake_process_dubbing_file)

    script_file = tmp_path / "test_script.docx"
    script_file.write_text("sample")

    worker = ExtractionWorker(
        file_path=str(script_file),
        sort_by="count",
        in_place=False,
        standalone=True,
        output_dir=str(tmp_path),
    )

    progress_events = []
    log_events = []
    finished_events = []
    error_events = []

    worker.progress.connect(lambda pct, msg: progress_events.append((pct, msg)))
    worker.log.connect(lambda msg: log_events.append(msg))
    worker.finished.connect(lambda path, res: finished_events.append((path, res)))
    worker.error.connect(lambda err: error_events.append(err))

    worker.run()

    assert len(finished_events) == 1
    assert finished_events[0][0] == fake_saved
    assert finished_events[0][1] == fake_result
    assert len(error_events) == 0
    assert (50, "Ayrıştırılıyor...") in progress_events
    assert any("[*] İşlem başlatılıyor:" in msg for msg in log_events)
    assert call_kwargs["sort_by"] == "count"
    assert call_kwargs["output_path"] == str(tmp_path / "test_script_kast.docx")


def test_extraction_worker_error(tmp_path, monkeypatch):
    """ExtractionWorker'ın hata durumunda error sinyali yaydığını test eder."""
    import src.gui as gui_mod
    from src.gui import ExtractionWorker

    def failing_process(**kwargs):
        raise RuntimeError("Dosya okunamadı!")

    monkeypatch.setattr(gui_mod, "process_dubbing_file", failing_process)

    worker = ExtractionWorker(
        file_path=str(tmp_path / "broken.docx"),
        sort_by="appearance",
        in_place=False,
        standalone=True,
    )

    error_events = []
    worker.error.connect(lambda err: error_events.append(err))

    worker.run()

    assert len(error_events) == 1
    assert "Dosya okunamadı!" in error_events[0]


def test_kast_studio_window_clear_all_and_sort_modes(qapp, tmp_path):
    """KastStudioWindow temizleme ve sıralama opsiyonlarını test eder."""
    from src.gui import KastStudioWindow

    window = KastStudioWindow()
    docx_file = tmp_path / "script.docx"
    docx_file.write_text("text")

    window.drop_zone.set_file(str(docx_file))
    window.rb_count.setChecked(True)
    window.progress_bar.setValue(50)
    window.log_area.append("Bazı günlük kayıtları...")

    window._clear_all()

    assert window.drop_zone.get_file_path() is None
    assert not window.btn_extract.isEnabled()
    assert window.progress_bar.value() == 0
    assert not window.result_card.isVisible()
    assert window.rb_appearance.isChecked()
    assert window.rb_standalone.isChecked()
    assert window.log_area.toPlainText() == ""


def test_kast_studio_window_start_extraction_options(qapp, tmp_path, monkeypatch):
    """KastStudioWindow _start_extraction fonksiyonunun sıralama ve çıktı parametrelerini doğru worker'a ilettiğini test eder."""
    from src.gui import KastStudioWindow

    window = KastStudioWindow()
    # Dosya yokken start
    window._start_extraction()
    assert window.worker is None

    docx_file = tmp_path / "film.docx"
    docx_file.write_text("dummy")
    window.drop_zone.set_file(str(docx_file))

    # 1. Sıralama: name, Çıktı: in_place
    window.rb_name.setChecked(True)
    window.rb_inplace.setChecked(True)

    # Worker.start() çağrısını mockla ki ayrı thread başlatmasın
    worker_created = []

    def mock_start(worker_self):
        worker_created.append(worker_self)

    monkeypatch.setattr("src.gui.BatchExtractionWorker.start", mock_start)

    window._start_extraction()

    assert len(worker_created) == 1
    assert window.worker.sort_by == "name"
    assert window.worker.in_place is True
    assert window.worker.standalone is False
    assert not window.btn_extract.isEnabled()
    assert not window.btn_clear.isEnabled()


def test_kast_studio_window_worker_callbacks(qapp, tmp_path):
    """KastStudioWindow worker callback metodlarının (progress, log, finished, error) arayüzü güncellediğini test eder."""
    from src.gui import KastStudioWindow
    from src.models import CastExtractionResult, CharacterStats

    window = KastStudioWindow()
    window.show()

    # Progress ve Log
    window._on_worker_progress(65, "İşleniyor")
    assert window.progress_bar.value() == 65

    window._on_worker_log("İşlem adımı 1")
    assert "İşlem adımı 1" in window.log_area.toPlainText()

    # Finished (çok sayfalı)
    chars = [
        CharacterStats(name="ALİ", first_seen_order=1, line_count=10, pages={1, 2}),
        CharacterStats(name="VELİ", first_seen_order=2, line_count=5, pages={2}),
    ]
    result = CastExtractionResult(characters=chars, total_lines=15, total_pages=2)
    fake_out = str(tmp_path / "out_kast.docx")

    window._on_worker_finished(fake_out, result)

    assert window.last_output_file == fake_out
    assert window.progress_bar.value() == 100
    assert window.btn_extract.isEnabled()
    assert window.btn_clear.isEnabled()
    assert window.result_card.isVisible()
    assert "2 Karakter • 15 Replik • 2 Sayfa" in window.lbl_result_text.text()

    # Error
    window._on_worker_error("Beklenmeyen hata")
    assert window.progress_bar.value() == 0
    assert window.btn_extract.isEnabled()
    assert "Beklenmeyen hata" in window.log_area.toPlainText()


def test_kast_studio_window_open_folder_and_file(qapp, tmp_path, monkeypatch):
    """KastStudioWindow dosya ve klasör açma işlemlerini farklı platformlarda test eder."""
    import subprocess
    from src.gui import KastStudioWindow

    window = KastStudioWindow()

    # Dosya yokken çağrılar hiçbir şey yapmamalı
    window._open_output_folder()
    window._open_output_file()

    fake_file = tmp_path / "output.docx"
    fake_file.write_text("content")
    window.last_output_file = str(fake_file)

    commands_run = []

    def mock_subprocess_run(cmd, *args, **kwargs):
        commands_run.append(cmd)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    # 1. Linux test
    monkeypatch.setattr("sys.platform", "linux")
    window._open_output_folder()
    assert commands_run[-1] == ["xdg-open", str(tmp_path)]
    window._open_output_file()
    assert commands_run[-1] == ["xdg-open", str(fake_file)]

    # 2. Darwin test
    monkeypatch.setattr("sys.platform", "darwin")
    window._open_output_folder()
    assert commands_run[-1] == ["open", "-R", str(fake_file)]
    window._open_output_file()
    assert commands_run[-1] == ["open", str(fake_file)]

    # 3. Windows test
    monkeypatch.setattr("sys.platform", "win32")
    window._open_output_folder()
    assert commands_run[-1][0] == "explorer"

    opened_files = []
    monkeypatch.setattr("os.startfile", lambda f: opened_files.append(f), raising=False)
    window._open_output_file()
    assert opened_files[-1] == str(fake_file)


def test_launch_gui(monkeypatch):
    """launch_gui fonksiyonunun QApplication oluşturup pencereyi gösterdiğini doğrular."""
    from src.gui import launch_gui, KastStudioWindow
    from PySide6.QtWidgets import QApplication

    shown = []
    monkeypatch.setattr(KastStudioWindow, "show", lambda self: shown.append(True))

    class MockApp:
        def __init__(self, *args, **kwargs):
            pass
        def setStyle(self, style):
            pass
        def exec(self):
            return 42

    monkeypatch.setattr(QApplication, "instance", lambda: MockApp())

    exit_code = launch_gui()
    assert exit_code == 42
    assert len(shown) == 1


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
    assert "3 adet çeviri dosyası hazır" in widget.lbl_filename.text()
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
        lambda *args, **kwargs: ([str(f1), str(f2)], "Dublaj Çevirileri (*.docx *.pdf)"),
    )

    widget._open_file_dialog()
    assert len(widget.get_files()) == 2
    assert widget.get_files() == [str(f1), str(f2)]


def test_drop_zone_widget_order_preserving_deduplication(qapp, tmp_path):
    """DropZoneWidget yinelenen dosya yollarını sırasını koruyarak tekilleştirir."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    f1 = tmp_path / "a.docx"
    f2 = tmp_path / "b.docx"
    f1.write_text("a")
    f2.write_text("b")

    ok = widget.set_files([str(f1), str(f2), str(f1), str(f2)])
    assert ok is True
    assert widget.get_files() == [str(f1), str(f2)]


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


def test_drop_zone_widget_exact_25_files_allowed(qapp, tmp_path):
    """DropZoneWidget tam 25 dosya sınır değerini kabul eder ve tüm dosyaları başarıyla yükler."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    files = []
    for i in range(25):
        f = tmp_path / f"part_{i:02d}.docx"
        f.write_text(f"content {i}")
        files.append(str(f))

    emitted_files = []
    widget.files_selected.connect(lambda paths: emitted_files.append(paths))

    ok = widget.set_files(files)
    assert ok is True
    assert len(widget.get_files()) == 25
    assert widget.get_files() == files
    assert len(emitted_files) == 1
    assert emitted_files[0] == files
    assert "DOCX (25 Dosya)" in widget.lbl_badge.text()
    assert "25 adet çeviri dosyası hazır" in widget.lbl_filename.text()


def test_drop_zone_widget_empty_and_whitespace_paths(qapp, tmp_path):
    """DropZoneWidget boş liste, boşluk karakterleri veya tırnak içeren dosya yollarını uygun şekilde işler/reddeder."""
    from src.gui import DropZoneWidget

    widget = DropZoneWidget()
    errors = []
    widget.validation_error.connect(lambda err: errors.append(err))

    # 1. Boş liste
    ok1 = widget.set_files([])
    assert ok1 is False
    assert len(errors) == 1
    assert "Hiçbir dosya seçilmedi" in errors[-1]

    # 2. Sadece boşluk veya tırnak içeren yollar
    ok2 = widget.set_files(["", "   ", "  \t  ", "\n", "''", '""'])
    assert ok2 is False
    assert len(errors) == 2
    assert "Hiçbir geçerli dosya yolu belirtilmedi" in errors[-1]

    # 3. Geçerli yolların etrafındaki boşluk ve tırnakların temizlenmesi ve tekilleştirme
    f1 = tmp_path / "clean_part1.docx"
    f2 = tmp_path / "clean_part2.docx"
    f1.write_text("clean1")
    f2.write_text("clean2")

    ok3 = widget.set_files([
        f"  '{str(f1)}'  ",
        "",
        "   ",
        f'  "{str(f2)}"  ',
        f"  {str(f1)}  ",  # Deduplication testi
    ])
    assert ok3 is True
    assert widget.get_files() == [str(f1), str(f2)]
    assert len(widget.get_files()) == 2


def test_kast_studio_window_multi_file_partial_error_flow(qapp, tmp_path, monkeypatch):
    """KastStudioWindow kısmi hata ve tam hata akışlarında buton, rozet ve durum metinlerini doğrular; doğrulama hatasının temizlendiğini test eder."""
    import src.gui as gui_mod
    from src.gui import KastStudioWindow
    from src.models import CastExtractionResult, CharacterStats

    window = KastStudioWindow()
    window.show()

    f1 = tmp_path / "p1.docx"
    f2 = tmp_path / "p2.docx"
    f_invalid = tmp_path / "invalid.pdf"
    f1.write_text("p1")
    f2.write_text("p2")
    f_invalid.write_text("pdf")

    # 1. Doğrulama hatası oluştur ve ardından geçerli dosyalarla durumun 'Hazır'a döndüğünü doğrula
    window.drop_zone.set_files([str(f1), str(f_invalid)])
    assert "Doğrulama Hatası" in window.lbl_status.text()
    assert not window.btn_extract.isEnabled()

    window.drop_zone.set_files([str(f1), str(f2)])
    assert window.lbl_status.text() == "● Durum: Hazır"
    assert window.btn_extract.isEnabled()

    # 2. _start_extraction'ın last_output_file'ı sıfırladığını doğrula
    window.last_output_file = str(tmp_path / "old_output.docx")
    monkeypatch.setattr(gui_mod.BatchExtractionWorker, "start", lambda self: None)
    window._start_extraction()
    assert window.last_output_file is None

    # 3. Kısmi Hata Durumu (1 Başarılı, 1 Hatalı)
    partial_summary = [
        {
            "path": str(f1),
            "output": str(tmp_path / "p1_kast.docx"),
            "status": "success",
            "result": CastExtractionResult([CharacterStats("DENEME", 1, 5, {1})], 5, 1),
        },
        {
            "path": str(f2),
            "error": "Bozuk XML yapısı",
            "status": "error",
        },
    ]
    window._on_batch_finished(partial_summary)

    assert window.result_card.isVisible()
    assert window.last_output_file == str(tmp_path / "p1_kast.docx")
    assert window.btn_extract.isEnabled()
    assert window.btn_clear.isEnabled()
    assert "⚠️ Kısmi Tamamlandı: 1/2 başarılı, 1 dosyada hata oluştu." in window.lbl_result_text.text()
    assert "1 hata" in window.lbl_status.text()
    assert window.btn_open_file.text() == "📄 Son Dosyayı Aç"

    # 4. Tam Başarısızlık Durumu (0 Başarılı, 2 Hatalı)
    window._start_extraction()
    assert window.last_output_file is None

    fail_summary = [
        {"path": str(f1), "error": "Hata 1", "status": "error"},
        {"path": str(f2), "error": "Hata 2", "status": "error"},
    ]
    window._on_batch_finished(fail_summary)

    assert window.result_card.isVisible()
    assert window.last_output_file is None
    assert window.btn_extract.isEnabled()
    assert window.btn_clear.isEnabled()
    assert "❌ İşlem Başarısız: 2/2 dosyada hata oluştu." in window.lbl_result_text.text()
    assert "2 hata" in window.lbl_status.text()
