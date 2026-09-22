# Kast 2.0 Living Architecture Wiki — Olay ve Değişiklik Günlüğü (Log)

Bu dosya, Andrej Karpathy'nin LLM Wiki prensiplerine uygun olarak kronolojik ve parse edilebilir (`grep "^## \[" log.md`) bir kayıt tutar.

---

## [2026-09-22] init | Kast 2.0 Living Architecture Ontolojik Modelleme ve Açılış Kaydı

- **Ajan Rolü:** Otonom Mimarlık Ajanı
- **Yapılan İşlem:**
  - Kast 2.0 kod tabanının baştan sona statik ve dinamik analizi tamamlandı.
  - Sayısal/kitap düzeni yasağı uygulanarak 6 fonksiyonel domain (`architecture-decisions`, `core-models`, `parsing-engine`, `pagination-subsystem`, `document-generation`, `interfaces-and-runtime`) oluşturuldu.
  - Kod tabanındaki geçmiş tasarım kırılmaları ve mimari seçimler 4 adet ADR (`adr-001`, `adr-002`, `adr-003`, `adr-004`) altında belgelendi.
  - 18 adet bağımsız atomik `.md` sayfası Obsidian uyumlu `wikilink` cluster topolojisiyle birbirine bağlandı.
  - Ana fihrist ([[index]]) ve proje kök kural seti (`AGENTS.md`) yayımlandı.
  - `docs/kast-app-wiki` ana ve tekil wiki dizini olarak belirlendi.
- **Mevcut Sistem Durumu:**
  - Çekirdek motor: `python-docx` ve OpenXML tabanlı sekme/tire ayrıştırması aktif.
  - Sayfalama motoru: Headless LibreOffice ve Word COM ile %100 kesin PDF eşleme akışı devrede; `dxpdf` tamamen tasfiye edilmiş durumda.
  - Arayüz: Textual TUI ve CLI hibrit başlatıcısı aktif.

---

## [2026-09-22] update | TypeSafe AI (System One) Protokolünün AGENTS.md Kural Setine Eklenmesi

- **Ajan Rolü:** Otonom Mimarlık Ajanı
- **Yapılan İşlem:**
  - `AGENTS.md` kural seti güncellendi: TypeSafe AI (`/typesafe-ai`) System One primitifleri (`Choice`, `Score`, `Noul`) için mimari standartlar tanımlandı.
  - Soru ve rubriklerin tek merkezden (`src/typesafe_judgments.py`) yönetilmesi, atomik soru ve kodda birleştirme, çevrimdışı fallback (sıfır bozulma) ve `TYPESAFE_API_KEY` güvenliği bağlayıcı kurallar arasına eklendi.
  - Mimari karar kayıtları (ADR) ve fonksiyonel domain listeleri (`core-models`, `parsing-engine`) TypeSafe entegrasyonuyla uyumlu hale getirildi.
- **Etkilenen Sayfalar:** `AGENTS.md`

---

## [2026-09-22] refactor | Wiki Dizin Standardizasyonu (docs/kast-app-wiki)

- **Ajan Rolü:** Otonom Mimarlık Ajanı
- **Yapılan İşlem:**
  - `docs/wiki` sembolik bağı (symlink) sistemden kaldırıldı.
  - Tüm dokümantasyon yolları ve `AGENTS.md` kural seti doğrudan ve yalnızca `docs/kast-app-wiki/` olarak standardize edildi.
- **Etkilenen Sayfalar:** `AGENTS.md`, [[log]]

---

## [2026-09-22] feat | DubbingPdfParser Doğrudan PDF Ayrıştırma Motoru
- **Ajan Rolü:** Task 1 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - PDF senaryolarından doğrudan diyalog satırı ve konuşmacı tespiti yapan `DubbingPdfParser` motoru eklendi (`src/pdf_parser.py`).
  - Standart Word DOCX tablosu üreten `process_pdf_document` kolaylık fonksiyonu entegre edildi.
  - TDD döngüsü işletilerek 7 adet kapsamlı birim testi hazırlandı (`tests/test_pdf_parser.py`).
- **Etkilenen Sayfalar:** [[dubbing-pdf-parser]], [[index]], [[log]]

---

## [2026-09-22] feat | Birleşik Dosya Yönlendiricisi (process_dubbing_file)
- **Ajan Rolü:** Task 2 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - `kast.py` içerisine `.docx` ve `.pdf` dosyalarını tek bir arayüzden karşılayan `process_dubbing_file` birleşik yönlendiricisi eklendi.
  - PDF için doğrudan `src.pdf_parser.process_pdf_document` sevk mekanizması kuruldu; `in_place=True` koruması (ValueError) ve dinamik sayfa ilerleme geri çağırması (`progress_callback`) sağlandı.
  - DOCX için `process_cast_document` akışı entegre edilip `CastExtractionResult` nesnesi döndürüldü.
  - TDD döngüsü işletilerek kapsamlı entegrasyon testleri eklendi (`tests/test_integration.py`).
- **Etkilenen Sayfalar:** [[hybrid-cli-dispatcher]], [[log]]

---

## [2026-09-22] feat | Qt6 Modern Koyu Stüdyo Teması ve Görsel Bileşenler (StudioTheme)
- **Ajan Rolü:** Task 3 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - `src/gui.py` modülü oluşturularak modern koyu stüdyo teması (`StudioTheme`) tanımlandı.
  - Windows stüdyolarına uygun yüksek kontrastlı renk paleti (`COLORS`), tipografi (`Segoe UI`) ve QSS stil şablonu (`get_stylesheet()`) sağlandı.
  - TDD döngüsü işletilerek stil, renk sözlüğü ve bileşen seçicilerini doğrulayan birim testleri eklendi (`tests/test_gui.py`).
- **Etkilenen Sayfalar:** [[qt6-desktop-gui]], [[log]]

---

## [2026-09-22] feat | Tekil Sürükle-Bırak Girdi Kartı (DropZoneWidget)
- **Ajan Rolü:** Task 4 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - `src/gui.py` içine `DropZoneWidget` bileşeni uygulandı: `.docx` ve `.pdf` için sürükle-bırak (`dragEnterEvent`, `dragLeaveEvent`, `dropEvent`) ve yerel dosya seçici (`QFileDialog`).
  - Boş (`empty_container`) ve yüklü (`loaded_container`) durumlar, dinamik kenarlık stilleri, rozet renklendirmesi (DOCX: `#7aa2f7`, PDF: `#f7768e`) ve dosya boyutu gösterimi sağlandı.
  - Sinyal (`file_selected`) ve yardımcı arayüz metotları (`set_file`, `clear`, `get_file_path`) eklendi.
  - TDD döngüsü tamamlanarak 5 yeni birim testi `tests/test_gui.py` içine yazıldı ve doğrulandı.
- **Etkilenen Sayfalar:** [[qt6-desktop-gui]], [[index]], [[log]]

---

## [2026-09-22] feat | Arka Plan Çalışanı ve Ana Pencere (ExtractionWorker & KastStudioWindow)
- **Ajan Rolü:** Task 5 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - `src/gui.py` içerisine arka planda kast çıkarma sürecini GUI donmadan yürüten `ExtractionWorker(QThread)` eklendi (`progress`, `log`, `finished`, `error` sinyalleri).
  - Modern `KastStudioWindow(QMainWindow)` ana penceresi geliştirildi: `DropZoneWidget` entegrasyonu, PDF'e göre akıllı in-place kilidi, sıralama radyo butonları, sonuç rozet kartı ("Klasörde Göster", "Dosyayı Aç"), ilerleme çubuğu ve konsol stili renkli `log_area`.
  - GUI giriş noktası `launch_gui() -> int` fonksiyonu eklendi.
  - TDD döngüsü tamamlanarak `tests/test_gui.py` içine toplam 8 yeni birim testi yazıldı ve tüm 16 GUI testi başarıyla geçti.
- **Etkilenen Sayfalar:** [[qt6-desktop-gui]], [[log]]

---

## [2026-09-22] feat | CLI Entegrasyonu ve Windows Başlatıcıları (kast-gui.cmd, install.ps1, kast.py --gui)
- **Ajan Rolü:** Task 6 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - `kast.py` CLI ayrıştırıcısına `--gui` (`-g`) bayrağı eklendi ve `main()` akışında `launch_gui()` yönlendirmesi kuruldu.
  - Windows stüdyoları için çift tıklama ve komut satırından sanal ortam destekli `kast-gui.cmd` batch başlatıcısı oluşturuldu.
  - `install.ps1` kurulum betiği güncellendi: `%USERPROFILE%\bin\kast-gui.cmd` dosyasının otomatik oluşturulması, `PySide6` bağımlılık kontrolü ve kurulum sonrası yönerge metinleri entegre edildi.
  - `requirements.txt` bağımlılık dosyasına `PySide6>=6.5.0` eklendi.
  - TDD döngüsü tamamlanarak `tests/test_install_scripts.py` ve `tests/test_integration.py` testleri başarıyla doğrulandı.
- **Etkilenen Sayfalar:** [[hybrid-cli-dispatcher]], [[cross-platform-installers]], [[log]]
 
---

## [2026-09-22] docs | Living Architecture Wiki Güncellemesi (ADR-005 ve Qt6 Masaüstü GUI)
- **Ajan Rolü:** Task 7 Living Architecture ve Dokümantasyon Ajanı
- **Yapılan İşlem:**
  - `adr-005-qt6-windows-studio-gui.md` mimari karar kaydı oluşturuldu: Windows stüdyo ortamlarının gereksinimleri, PySide6 (Qt6) seçimi, Tkinter/Electron/PyQt5/TUI alternatif analizleri ve QThread arka plan iş parçacığı mimarisi belgelendi.
  - `qt6-desktop-gui.md` atomik sayfası zenginleştirilerek tamamlandı: `StudioTheme` Tokyo Night paleti, tipografi, `DropZoneWidget` çift durumlu sürükle-bırak motoru, `ExtractionWorker` QThread sinyal modeli ve `KastStudioWindow` masaüstü iş akışı detaylandırıldı.
  - Fihrist (`index.md`) güncellenerek ADR-005 eklendi ve `qt6-desktop-gui` modül tanımı güncellendi.
  - `hybrid-cli-dispatcher.md` ve `cross-platform-installers.md` sayfalarının ilgili sayfalar grafı (`[[adr-005-qt6-windows-studio-gui]]`, `[[qt6-desktop-gui]]`) bağlandı.
  - Living Architecture graf hijyeni (yetim sayfa ve kırık link kontrolü) test edildi, %100 uyum doğrulandı.
- **Etkilenen Sayfalar:** [[adr-005-qt6-windows-studio-gui]], [[qt6-desktop-gui]], [[index]], [[hybrid-cli-dispatcher]], [[cross-platform-installers]], [[log]]


