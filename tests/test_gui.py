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
    assert "Microsoft Word veya metin formatlı senaryo PDF'leri" in widget.lbl_subprompt.text()
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
        "getOpenFileName",
        lambda *args, **kwargs: (str(fake_file), "PDF Belgeleri (*.pdf)"),
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

    monkeypatch.setattr("src.gui.ExtractionWorker.start", mock_start)

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




