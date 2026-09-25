# Pixel-Perfect Modern Studio Qt6 UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kast 2.0 Qt6 masaüstü arayüzünü kullanıcının ilettiği görsel tasarımla (mockup) piksel düzeyinde birebir uyumlu, koyu gece mavisi (`#0b0f19`) zeminli, elektrik camgöbeği (`#00b4d8` / `#38bdf8`) vurgulu, kart içi kutulu (tiled) radyo butonlu, bulut ikonlu sürükle-bırak alanlı ve profesyonel terminal panelli modern stüdyo tasarımına dönüştürmek.

**Architecture:** `src/gui.py` içerisindeki `StudioTheme` QSS şablonu, `DropZoneWidget`, radyo seçim kartları ve `KastStudioWindow` görsel bileşenleri mockup'taki hiyerarşi ve tipografiye göre yeniden yapılandırılır; mevcut `ExtractionWorker` (QThread) ve `process_dubbing_file` motoruyla olan sinyal/slot entegrasyonu ve iş mantığı %100 korunarak giydirme tamamlanır.

**Tech Stack:** Python 3.10+, PySide6 6.5+ (Qt6), `pytest`, `pytest-asyncio`, Headless Offscreen QTest.

**Spec:** Kullanıcı tarafından sağlanan UI mockup görselindeki (`media_1790078891840.png`) renkler, tipografi, kutulu radyo kartları, format etiketleri ve konsol yerleşimi.

## Global Constraints

- Tasarım mockup görseline sadık kalınarak oluşturulacaktır:
  - Zemin rengi: `#0b0f19`, Kartlar: `#0f172a` (kenarlık: `#1e293b`), Vurgular: `#00b4d8`, `#06b6d4`, `#38bdf8`.
  - Başlık: `Kast 2.0` (Camgöbeği) + `— Dublaj Kast Çıkarma` (Beyaz) + Sağ üstte `● Windows Studio Edition • Qt6` hap rozeti.
  - Sürükle-Bırak Alanı: Kesikli kenarlık (`#223554`), dairesel bulut yükleme rozeti (`☁↑`), `.DOCX` ve `.PDF` format hapları, `☁ Dosya Seç` butonu.
  - Seçim Kartları: `Karakter Sıralama` ve `Çıktı Seçenekleri` kartları içinde kutulu/kapsüllü (tiled) radyo butonları; sağ kartta `(<ad>_kast.docx)` alt yazısı ve alt bilgi satırı (`Çıktı Biçimi: .docx Tablo  |  Varsayılan şablon v2.1`).
  - Aksiyon Butonları: Geniş parlak camgöbeği `▶ Kast Tablosunu Çıkar` butonu (siyah kalın yazı) ve yanındaki koyu `🗑 Temizle` butonu.
  - Durum & Konsol: `● Durum: Hazır` + `%0` durum satırı; `🖥 İŞLEM GÜNLÜĞÜ  |  UTF-8 / Terminal hazır` başlıklı siyah terminal alanı (`#080c14`).
  - Alt Çubuk: `PySide6 Modern Frame  |  Hazır` (sol) ve `Encoding: UTF-8` (sağ).
- Mevcut `ExtractionWorker` iş parçacığı, `process_dubbing_file` entegrasyonu ve tüm birim testlerin (`tests/test_gui.py`) yeşil kalması zorunludur.
- Living Architecture kurallarına (`AGENTS.md`) tam uyum sağlanacaktır.

---

### Task 1: Renk Paleti ve QSS Tema Motorunun Yenilenmesi (`StudioTheme`)

**Files:**
- Modify: `src/gui.py:15-140`
- Test: `tests/test_gui.py`

**Interfaces:**
- Produces: `StudioTheme.COLORS` (güncellenmiş gece mavisi ve neon camgöbeği tokenları), `StudioTheme.get_stylesheet() -> str`

- [ ] **Step 1: Failing test ekle (`tests/test_gui.py`)**

```python
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
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_studio_theme_mockup_color_palette -v`
Expected: FAIL with `AssertionError: assert '#1a1b26' == '#0b0f19'`

- [ ] **Step 3: `StudioTheme` sınıfını mockup görseline göre güncelle**

```python
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
            padding: 16px;
        }}
        QFrame#tile-option {{
            background-color: {c["card_tile"]};
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 8px 12px;
        }}
        QFrame#tile-option:hover {{
            background-color: #182847;
        }}
        QFrame#tile-option[selected="true"] {{
            background-color: {c["card_tile_selected"]};
            border: 1px solid {c["border_focus"]};
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
        """
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_studio_theme_mockup_color_palette -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): update StudioTheme to match midnight and electric cyan mockup"
```

---

### Task 2: Mockup Uyumlu Kutulu Radyo Buton Kartları (`OptionTileWidget`)

**Files:**
- Modify: `src/gui.py`
- Test: `tests/test_gui.py`

**Interfaces:**
- Produces: `OptionTileWidget(QFrame)`
  - Sol tarafta modern radyo göstergesi (seçildiğinde içi dolu camgöbeği halka).
  - Sağ tarafta ana başlık ve opsiyonel camgöbeği alt başlık (`subtext`).
  - Tıklandığında veya radyo değiştiğinde `clicked` sinyali ve `set_selected(bool)` durumu.

- [ ] **Step 1: Failing test ekle (`tests/test_gui.py`)**

```python
def test_option_tile_widget(qapp):
    """OptionTileWidget seçim durumlarını ve alt metin desteğini test eder."""
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
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_option_tile_widget -v`
Expected: FAIL with `NameError: name 'OptionTileWidget' is not defined`

- [ ] **Step 3: `OptionTileWidget` sınıfını `src/gui.py` içine ekle**

```python
class OptionTileWidget(QFrame):
    """Clickable modern option tile with radio indicator, title, and optional cyan subtext."""

    clicked = Signal()

    def __init__(self, title: str, subtext: Optional[str] = None, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("tile-option")
        self.setCursor(Qt.PointingHandCursor)
        self._is_selected = is_selected

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Radio glyph
        self.lbl_radio = QLabel()
        self.lbl_radio.setFixedSize(18, 18)
        self.lbl_radio.setAlignment(Qt.AlignCenter)

        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")
        text_layout.addWidget(self.lbl_title)

        self.lbl_subtext = None
        if subtext:
            self.lbl_subtext = QLabel(subtext)
            self.lbl_subtext.setStyleSheet("font-size: 11px; font-family: monospace; color: #38bdf8;")
            text_layout.addWidget(self.lbl_subtext)

        layout.addWidget(self.lbl_radio)
        layout.addLayout(text_layout)
        layout.addStretch()

        self.set_selected(is_selected)

    def is_selected(self) -> bool:
        return self._is_selected

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self.setProperty("selected", "true" if selected else "false")
        if selected:
            self.lbl_radio.setStyleSheet("""
                background-color: #38bdf8;
                border: 4px solid #131f38;
                border-radius: 9px;
            """)
            self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #ffffff;")
        else:
            self.lbl_radio.setStyleSheet("""
                background-color: transparent;
                border: 2px solid #334155;
                border-radius: 9px;
            """)
            self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 500; color: #94a3b8;")
        
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_option_tile_widget -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): add OptionTileWidget for mockup-accurate card options"
```

---

### Task 3: Mockup Uyumlu Sürükle-Bırak Alanı (`DropZoneWidget`)

**Files:**
- Modify: `src/gui.py:140-270`
- Test: `tests/test_gui.py`

**Interfaces:**
- Mockup tasarımı:
  - Kesikli koyu lacivert kenarlık (`border: 1.5px dashed #223554; border-radius: 12px; background: #0c1424;`).
  - Ortada dairesel mavi bulut ikonu rozeti (`☁↑`, `background: #111d33; border: 1.5px solid #0284c7; border-radius: 24px; width: 48px; height: 48px;`).
  - Ana metin: `Senaryo dosyasını (.docx veya .pdf) buraya sürükleyip bırakın`.
  - Alt metin: `Microsoft Word veya metin formatlı senaryo PDF'leri desteklenmektedir.`.
  - Mini format hapları: `.DOCX` ve `.PDF`.
  - Buton: `☁ Dosya Seç`.

- [ ] **Step 1: Failing test ekle (`tests/test_gui.py`)**

```python
def test_drop_zone_widget_mockup_elements(qapp):
    """DropZoneWidget bileşeninin mockup görselindeki ikon, metin ve hapları barındırdığını doğrular."""
    widget = DropZoneWidget()
    assert "Microsoft Word veya metin formatlı senaryo PDF'leri" in widget.lbl_subprompt.text()
    assert widget.badge_docx.text() == ".DOCX"
    assert widget.badge_pdf.text() == ".PDF"
    assert "Dosya Seç" in widget.btn_browse.text()
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_drop_zone_widget_mockup_elements -v`
Expected: FAIL with `AttributeError: 'DropZoneWidget' object has no attribute 'lbl_subprompt'`

- [ ] **Step 3: `DropZoneWidget` sınıfını mockup görseline göre güncelle**

```python
class DropZoneWidget(QFrame):
    """Pixel-perfect modern drag-drop zone matching the studio mockup."""

    file_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._file_path = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("drop-zone")
        self.setMinimumHeight(190)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setContentsMargins(24, 20, 24, 20)

        # 1. Empty State
        self.empty_container = QFrame()
        empty_layout = QVBoxLayout(self.empty_container)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)

        # Circular Cloud Icon Container
        self.icon_container = QFrame()
        self.icon_container.setFixedSize(52, 52)
        self.icon_container.setStyleSheet("""
            background-color: #111d33;
            border: 1.5px solid #0284c7;
            border-radius: 26px;
        """)
        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_icon = QLabel("☁↑")
        self.lbl_icon.setStyleSheet("font-size: 20px; color: #38bdf8; font-weight: bold; border: none; background: transparent;")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.lbl_icon)

        self.lbl_prompt = QLabel("Senaryo dosyasını (.docx veya .pdf) buraya sürükleyip bırakın")
        self.lbl_prompt.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        self.lbl_prompt.setAlignment(Qt.AlignCenter)

        self.lbl_subprompt = QLabel("Microsoft Word veya metin formatlı senaryo PDF'leri desteklenmektedir.")
        self.lbl_subprompt.setStyleSheet("font-size: 12px; color: #64748b;")
        self.lbl_subprompt.setAlignment(Qt.AlignCenter)

        # Format pills row
        pills_layout = QHBoxLayout()
        pills_layout.setAlignment(Qt.AlignCenter)
        pills_layout.setSpacing(8)

        self.badge_docx = QLabel(".DOCX")
        self.badge_docx.setStyleSheet("background-color: #131f38; border: 1px solid #1e293b; color: #94a3b8; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 4px;")
        self.badge_pdf = QLabel(".PDF")
        self.badge_pdf.setStyleSheet("background-color: #131f38; border: 1px solid #1e293b; color: #94a3b8; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 4px;")

        pills_layout.addWidget(self.badge_docx)
        pills_layout.addWidget(self.badge_pdf)

        # Browse Button
        self.btn_browse = QPushButton("☁  Dosya Seç")
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #162238;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 600;
                padding: 7px 22px;
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

    def _update_border_style(self, is_hover: bool = False) -> None:
        border_color = "#38bdf8" if is_hover else ("#223554" if not self._file_path else "#10b981")
        bg_color = "#111d33" if is_hover else "#0c1424"
        border_type = "dashed" if not self._file_path else "solid"
        self.setStyleSheet(f"""
            QFrame#drop-zone {{
                background-color: {bg_color};
                border: 1.5px {border_type} {border_color};
                border-radius: 12px;
            }}
        """)
```

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_drop_zone_widget_mockup_elements -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): redesign DropZoneWidget matching cloud icon, pills, and mockup"
```

---

### Task 4: Ana Pencere Yerleşimi, Başlık Rozeti ve Konsol Güncellemesi (`KastStudioWindow`)

**Files:**
- Modify: `src/gui.py:340-580`
- Test: `tests/test_gui.py`

**Interfaces:**
- Mockup hiyerarşisi:
  - Header: `Kast 2.0` (cyan) + ` — Dublaj Kast Çıkarma` (beyaz), alt yazı ve sağ üstte `● Windows Studio Edition • Qt6` hap rozeti.
  - İki yan yana kart (`QFrame#card-panel`):
    - Sol kart: `🗂 Karakter Sıralama` başlığı ve 3 adet `OptionTileWidget` (İlk Görünme Sırası, Replik Sayısı, Karakter Adı).
    - Sağ kart: `📄 Çıktı Seçenekleri` başlığı ve 2 adet `OptionTileWidget` (Ayrı dosya `(<ad>_kast.docx)` ve Orijinal döküman), yatay ayraç ve alt bilgi (`Çıktı Biçimi: .docx Tablo  |  Varsayılan şablon v2.1`).
  - Butonlar: `▶ Kast Tablosunu Çıkar` (geniş, parlak camgöbeği) + `🗑 Temizle` (koyu gri/lacivert).
  - Durum Satırı: `● Durum: Hazır` (sol) ve `%0` (sağ) + ince camgöbeği ilerleme çubuğu.
  - İşlem Günlüğü: `🖥 İŞLEM GÜNLÜĞÜ` (sol) ve `UTF-8 / Terminal hazır` (sağ), siyah monospace terminal kutusu.
  - Alt Çubuk: `PySide6 Modern Frame  |  Hazır` (sol) ve `Encoding: UTF-8` (sağ).

- [ ] **Step 1: Failing test ekle (`tests/test_gui.py`)**

```python
def test_kast_studio_window_mockup_layout(qapp):
    """KastStudioWindow bileşenlerinin mockup başlıklarını, rozetini ve terminal başlığını içerdiğini test eder."""
    window = KastStudioWindow()
    assert "Windows Studio Edition • Qt6" in window.lbl_badge.text()
    assert "Kast 2.0" in window.lbl_title_prefix.text()
    assert "Karakter Sıralama" in window.lbl_sort_title.text()
    assert "Çıktı Seçenekleri" in window.lbl_out_title.text()
    assert "İŞLEM GÜNLÜĞÜ" in window.lbl_log_title.text()
    assert "Terminal hazır" in window.lbl_log_meta.text()
    assert "Kast Tablosunu Çıkar" in window.btn_extract.text()
    assert "Temizle" in window.btn_clear.text()
```

- [ ] **Step 2: Testi çalıştır ve başarısız olduğunu doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_kast_studio_window_mockup_layout -v`
Expected: FAIL with `AttributeError: 'KastStudioWindow' object has no attribute 'lbl_badge'`

- [ ] **Step 3: `KastStudioWindow` sınıfını mockup görseline göre güncelle**

`KastStudioWindow._init_ui()` metodunu mockup hiyerarşisine göre yeniden yaz:
1. Header Bar:
   - `lbl_title_prefix` ("Kast 2.0", `#38bdf8`, 20px, bold) + `lbl_title_suffix` (" — Dublaj Kast Çıkarma", `#ffffff`, 20px, bold).
   - `lbl_subtitle` ("Senaryo belgelerindeki diyalogları ve karakter listesini otomatik analiz eder.", `#64748b`, 13px).
   - `lbl_badge` ("● Windows Studio Edition • Qt6", background `#0f293a`, border `1px solid #084c61`, color `#38bdf8`, padding 4px 12px, border-radius 12px).
2. Central DropZone:
   - `self.drop_zone` entegre.
3. Two Side-by-Side Cards:
   - Left Panel (`QFrame#card-panel`): `lbl_sort_title` ("🗂  Karakter Sıralama", `#38bdf8`, bold) + 3 `OptionTileWidget` nesnesi.
   - Right Panel (`QFrame#card-panel`): `lbl_out_title` ("📄  Çıktı Seçenekleri", `#38bdf8`, bold) + 2 `OptionTileWidget` nesnesi (`tile_standalone` with `(<ad>_kast.docx)`, `tile_inplace`), divider line, and footer metadata row (`Çıktı Biçimi: .docx Tablo`, `Varsayılan şablon v2.1`).
4. Action Buttons:
   - `btn_extract` ("▶  Kast Tablosunu Çıkar", `#btn-primary`, stretch=4).
   - `btn_clear` ("🗑  Temizle", `#btn-clear`, stretch=1).
5. Status & Progress:
   - Status label ("● Durum: Hazır", `#94a3b8`) + percent label ("0%", `#38bdf8`, bold).
   - `progress_bar` (6px thin cyan line).
6. Console Log Area:
   - Log header (`lbl_log_title` "🖥  İŞLEM GÜNLÜĞÜ", `lbl_log_meta` "UTF-8 / Terminal hazır").
   - `log_area` (`QTextEdit`, `#080c14` background, monospace).
7. Status Bar:
   - `PySide6 Modern Frame  |  Hazır` and `Encoding: UTF-8`.

- [ ] **Step 4: Testi çalıştır ve geçtiğini doğrula**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -k test_kast_studio_window_mockup_layout -v`
Expected: PASS

- [ ] **Step 5: Git commit**

```bash
git add src/gui.py tests/test_gui.py
git commit -m "feat(gui): overhaul KastStudioWindow layout to mirror pixel-perfect mockup"
```

---

### Task 5: Tüm Testlerin Doğrulanması ve Uçtan Uca Doğrulama

**Files:**
- Modify: `tests/test_gui.py`
- Test: Full test suite

**Interfaces:**
- Mevcut tüm 37+ testin ve yeni görsel bileşen testlerinin yeşil olduğunun doğrulanması.
- `example/JACKIE & OOPJEN.docx` dosyasının CLI ve GUI entegrasyonlarıyla başarıyla çalıştığının teyidi.

- [ ] **Step 1: Test paketini çalıştır**

Run: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_pdf_parser.py tests/test_gui.py tests/test_install_scripts.py tests/test_integration.py -v`
Expected: ALL PASS

- [ ] **Step 2: Gerçek örnek dosya ile uçtan uca test et**

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python3 -c "
from src.gui import KastStudioWindow, QApplication
app = QApplication.instance() or QApplication([])
w = KastStudioWindow()
w.drop_zone.set_file('example/JACKIE & OOPJEN.docx')
assert w.btn_extract.isEnabled()
print('GUI initialized and loaded sample file successfully!')
"
```

- [ ] **Step 3: Git commit**

```bash
git add tests/test_gui.py
git commit -m "test(gui): ensure comprehensive test coverage for pixel-perfect UI"
```

---

### Task 6: Living Architecture Wiki Dokümantasyonunun Güncellenmesi (`AGENTS.md`)

**Files:**
- Modify: `docs/kast-app-wiki/interfaces-and-runtime/qt6-desktop-gui.md`
- Modify: `docs/kast-app-wiki/log.md`

**Interfaces:**
- `qt6-desktop-gui.md` içerisindeki görsel tasarım spesifikasyonunu, `#0b0f19` ve `#00b4d8` renk paletini, `OptionTileWidget` mimarisini güncelle.
- `log.md` dosyasına UI görsel yenileme kaydı ekle.

- [ ] **Step 1: `docs/kast-app-wiki/interfaces-and-runtime/qt6-desktop-gui.md` güncelle**
- [ ] **Step 2: `docs/kast-app-wiki/log.md` kronolojik kaydını gir**
- [ ] **Step 3: Git commit**

```bash
git add docs/kast-app-wiki/
git commit -m "docs(wiki): document pixel-perfect Qt6 studio UI redesign in living architecture"
```

---

## Verification Plan

### Automated Tests
```bash
# 1. Qt6 Arayüz testleri (Offscreen headless)
QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_gui.py -v

# 2. Tam regresyon testi
QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_pdf_parser.py tests/test_gui.py tests/test_install_scripts.py tests/test_integration.py -v
```

### Manual Verification
1. **Pencere Render Testi:**
   ```bash
   QT_QPA_PLATFORM=offscreen .venv/bin/python3 -c "from src.gui import KastStudioWindow, QApplication; app = QApplication([]); w = KastStudioWindow(); print('Window rendered successfully!')"
   ```
2. **Görsel Kontrol:**
   Mockup görselindeki öğelerin (`☁↑` rozet, `.DOCX`/`.PDF` hapları, kutulu radyo kartları, parlak camgöbeği buton, terminal alanı) yerinde olduğunu doğrulamak.
