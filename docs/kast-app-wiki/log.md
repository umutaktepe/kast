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

---

## [2026-09-22] refactor | Pixel-Perfect DropZoneWidget Mockup Güncellemesi
- **Ajan Rolü:** Task 3 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - `DropZoneWidget` bileşeni mockup tasarımına pixel-for-pixel uyumlu hale getirildi:
    - Boş durum: Dairesel bulut ikonu rozeti (`☁↑`), ana metin (`Senaryo dosyasını (.docx veya .pdf) buraya sürükleyip bırakın`), alt metin (`Microsoft Word veya metin formatlı senaryo PDF'leri desteklenmektedir.`), format hapları (`.DOCX` ve `.PDF`) ve `☁  Dosya Seç` butonu.
    - Yüklü durum: Dosya türü rozeti (`#0284c7` / `#f43f5e`), dosya boyutu ve yolu bilgisi, `✕ Değiştir` butonu.
    - Dinamik kenarlık ve arka plan stilleri: Boşta kesikli `#223554` (`#0c1424`), hover anında `#38bdf8` (`#111d33`), yüklü halde dolu `#10b981`.
  - TDD döngüsü ile `test_drop_zone_widget_mockup_elements` birim testi eklendi ve tüm mevcut testler (`test_drop_zone_widget_*`) güncel palete adapte edildi.
- **Etkilenen Sayfalar:** [[qt6-desktop-gui]], [[log]]

---

## [2026-09-22] feat | Ana Pencere Yerleşimi, Başlık Rozeti ve Konsol Güncellemesi (KastStudioWindow)
- **Ajan Rolü:** Task 4 Kodlama ve TDD Ajanı
- **Yapılan İşlem:**
  - `KastStudioWindow` ve `OptionTileWidget` bileşenleri stüdyo mockup tasarımına göre pixel-for-pixel uyarlandı:
    - Başlık: `lbl_title_prefix` ("Kast 2.0", `#38bdf8`), `lbl_title_suffix` (" — Dublaj Kast Çıkarma", `#f8fafc`), `lbl_subtitle` ve `lbl_badge` ("● Windows Studio Edition • Qt6", `#0f293a` zemin, `#084c61` kenarlık).
    - Çift kart paneli: Sol kartta `lbl_sort_title` ve 3 adet `OptionTileWidget` (`tile_appearance`, `tile_count`, `tile_name`); sağ kartta `lbl_out_title` ve 2 adet `OptionTileWidget` (`tile_standalone` with `(<ad>_kast.docx)`, `tile_inplace`), ayırıcı çizgi ve `lbl_output_meta` alt bilgi satırı.
    - Karşılıklı dışlama: `OptionTileGroup` sınıfı eklendi; kartlar tıklandığında veya `setChecked(True)` çağrıldığında kardeş kartları devreden çıkaracak şekilde bağlandı.
    - Geriye dönük uyumluluk: `OptionTileWidget` içine `isChecked()` ve `setChecked(bool)` eklendi; `window.rb_*` takma adları korundu; PDF seçiminde in-place devre dışı bırakma mantığı korundu.
    - Aksiyon butonları: `btn_extract` ("▶  Kast Tablosunu Çıkar", `#btn-primary`, stretch=4) ve `btn_clear` ("🗑  Temizle", `#btn-clear`, stretch=1).
    - Durum & İlerleme: `lbl_status` ("● Durum: Hazır"), `lbl_pct` ("%0") ve 6px ince camgöbeği `progress_bar`.
    - Konsol: `lbl_log_title` ("🖥  İŞLEM GÜNLÜĞÜ"), `lbl_log_meta` ("UTF-8 / Terminal hazır") ve `#080c14` zeminli `log_area`.
    - Durum Çubuğu: `lbl_status_left` ("PySide6 Modern Frame  |  Hazır") ve `lbl_status_right` ("Encoding: UTF-8").
  - TDD döngüsü ile `test_kast_studio_window_mockup_layout` ve `test_option_tile_widget_compatibility_and_group` testleri eklendi; 22 GUI testi ve tüm 133 sistem testi yeşil geçti.
- **Etkilenen Sayfalar:** [[qt6-desktop-gui]], [[log]]

## [2026-09-22] [hata-duzeltme-ve-mizanpaj] | Pencereli Modda Duyarlı (Responsive) Mizanpaj ve QScrollArea İyileştirmesi
- **Ajan Rolü:** Living Architecture & Qt6 GUI Mühendisi
- **Yapılan İşlem:**
  - Tam ekran olmayan veya küçük pencereli kullanımlarda `OptionTileWidget` başlıklarının 0 yüksekliğe ezilmesi ve `DropZoneWidget` ikon/başlık elemanlarının üst üste binmesi sorunu giderildi.
  - `OptionTileWidget` ve `DropZoneWidget` bileşenlerine `QSizePolicy.Fixed` dikey boyutu ve koruyucu minimum yükseklikler atandı. QSS `padding` ile Python layout `contentsMargins` arasındaki çakışma giderildi.
  - `DropZoneWidget` boş durum konteynerindeki çift marjin temizlendi, ikon boyutu (40x40px) ve eleman aralıkları optimize edilerek çakışmasız 160px yüksekliğe uyarlandı.
  - `KastStudioWindow` ana içerik alanı `QScrollArea` ile sarmalandı; ekstra dikey alan `log_area` konsoluna bağlandı (`stretch=1`). Pencere boyutu küçüldüğünde içerikler ezilmeden şık koyu kaydırma çubuğu devreye alındı.
  - `test_kast_studio_window_responsive_layout_non_fullscreen` birim testi yazıldı ve 800x600, 860x740, 1024x768, 1920x1080 çözünürlüklerde doğrulandı; 23 GUI testi ve projenin tüm 134 testi eksiksiz geçti.
- **Etkilenen Sayfalar:** [[qt6-desktop-gui]], [[log]]

---

## [2026-09-23] feat | PyInstaller Yapılandırması, Giriş Noktası ve İkon Üretici (Task 1)
- **Ajan Rolü:** Task 1 Kodlama ve Paketleme Ajanı
- **Yapılan İşlem:**
  - `packaging/generate_icon.py` geliştirildi: PNG/JPEG veya geometrik fallback üzerinden 7 çözünürlüklü (`16x16` - `256x256`) `.ico` üreten CLI ve modül API'si oluşturuldu.
  - `packaging/run_gui.py` oluşturuldu: PyInstaller için konsolsuz doğrudan `launch_gui()` çağıran izole giriş noktası sağlandı.
  - `packaging/kast.spec` yapılandırıldı: Klasör demeti (`dist/KastStudio/`), veri dosyaları (`docs`, `example`, `packaging/assets`), gizli modüller (`PySide6`, `docx`, `pdfplumber`, `pypdf`, `PIL`) ve gereksiz kütüphane dışlamaları (`tkinter`, `matplotlib`, `scipy`) ayarlandı.
  - `src/gui.py` güncellendi: `KastStudioWindow.__init__` içerisinde `QIcon` ile `kast_icon.png` ve `kast.ico` pencerelere bağlandı; `sys._MEIPASS` PyInstaller uyumu sağlandı.
- **Etkilenen Sayfalar:** [[pyinstaller-standalone-packaging]], [[qt6-desktop-gui]], [[index]], [[log]]

---

## [2026-09-23] feat | Inno Setup Kurulum Sihirbazı (installer.iss) ve Sessiz LibreOffice Kurulumu (Task 2)
- **Ajan Rolü:** Task 2 Kodlama ve Inno Setup Paketleme Ajanı
- **Yapılan İşlem:**
  - `packaging/installer.iss` scripti geliştirildi: Inno Setup 6 ile Modern Wizard stili, `x64` mimarisi, `lzma2/ultra64` sıkıştırma, Türkçe/İngilizce dil desteği ve `{autopf}\Kast Studio` hedef dizini yapılandırıldı.
  - Başlat Menüsü, Masaüstü (`desktopicon` görevi) ve Windows Program Ekle/Kaldır entegrasyonu `assets\kast.ico` ikonuyla bağlandı.
  - Pascal Script (`[Code]`) bloğu inşa edildi:
    - `IsWordInstalled()`: `HKLM`/`HKCU` `App Paths\Winword.exe` ve `HKCR` `Word.Application` COM nesnesini sorgular.
    - `IsLibreOfficeInstalled()`: `HKLM`/`HKCU` `LibreOffice\UNO\InstallPath`, `The Document Foundation` kayıtları ve bilinen dizinlerdeki (`{pf}`, `{pf32}`, `{localappdata}`) `soffice.exe` varlığını denetler.
    - `CurStepChanged(ssPostInstall)`: Eğer ne Word ne de LibreOffice bulunamazsa, kullanıcıya sormadan arka planda sessizce önce `winget` (`TheDocumentFoundation.LibreOffice --silent`), başarısız olursa PowerShell ile doğrudan resmi LibreOffice MSI paketini indirip `msiexec /i ... /qn /norestart` ile kurar.
  - `tests/test_inno_setup.py` birim test takımı yazıldı: Bölüm varlığı, meta veri & ikonlar, diller, dosyalar, kısayollar, Pascal ofis tespiti ve sessiz kurulum argümanları test edildi (7/7 yeşil).
  - Yaşayan mimari dokümantasyonu oluşturuldu (`docs/kast-app-wiki/interfaces-and-runtime/inno-setup-installer.md`), `index.md` ve `pyinstaller-standalone-packaging.md` sayfaları çapraz bağlandı.
- **Etkilenen Sayfalar:** [[inno-setup-installer]], [[pyinstaller-standalone-packaging]], [[index]], [[log]]

---

## [2026-09-23] feat | GitHub Actions Otomatik Windows Derleme ve Sürüm Dağıtımı (Task 3)
- **Ajan Rolü:** Task 3 Kodlama ve CI/CD Dağıtım Ajanı
- **Yapılan İşlem:**
  - `.github/workflows/release-windows.yml` iş akışı oluşturuldu: `windows-latest` koşucusunda Python 3.11 ortamı, bağımlılık kurulumu, çoklu çözünürlüklü ikon üretimi, PyInstaller ile `dist/KastStudio/` klasör demeti, taşınabilir `dist/Kast-v<VERSION>-Windows-Portable.zip`, Chocolatey ile Inno Setup kurulumu ve `dist/Kast-v<VERSION>-Setup.exe` derlemesi sağlandı.
  - Kriptografik bütünlük için PowerShell `Get-FileHash` ile SHA256 sağlama listesi (`dist/checksums.txt`) oluşturuldu.
  - `softprops/action-gh-release@v2` eylemi ile etiket itmelerinde (`v*`) veya manuel `workflow_dispatch` tetikleyicilerinde varlıklar ve sürüm notları GitHub Releases üzerinde yayımlanacak şekilde yapılandırıldı.
  - `tests/test_ci_workflow.py` birim test takımı yazıldı (6/6 yeşil): YAML sözdizimi, tetikleyiciler, izinler, koşucu, adımlar, özel kabuklar (`pwsh`, `cmd`) ve yayın koşulları doğrulandı.
  - Yaşayan mimari dokümantasyonu oluşturuldu (`docs/kast-app-wiki/interfaces-and-runtime/github-actions-release-workflow.md`), `index.md`, `inno-setup-installer.md` ve `pyinstaller-standalone-packaging.md` sayfaları çapraz bağlandı.
- **Etkilenen Sayfalar:** [[github-actions-release-workflow]], [[inno-setup-installer]], [[pyinstaller-standalone-packaging]], [[index]], [[log]]

---

## [2026-09-23] docs | Living Architecture Wiki Senkronizasyonu ve ADR-006 (Windows Standalone & CI/CD)
- **Ajan Rolü:** Task 4 Living Architecture ve Dokümantasyon Ajanı
- **Yapılan İşlem:**
  - `adr-006-windows-standalone-installer-and-ci.md` mimari karar kaydı yayımlandı: PyInstaller klasör demeti, Inno Setup 6 akıllı ofis tespiti (Word/LibreOffice sessiz kurulum stratejisi), Portable ZIP ve GitHub Actions CI/CD bulut derleme mimarisi belgelendi.
  - `cross-platform-installers.md` güncellendi: Windows Standalone Setup (`.exe`) ve Portable (`.zip`) dağıtım matrisine eklendi; sıfır Python gereksinimi ve sessiz ofis stratejisi açıklandı.
  - `README.md` güncellendi: Kurulum bölümünün başına Windows Setup ve Portable indirmeleri öncelikli olarak yerleştirildi; Python gerektirmediği ve akıllı ofis tespiti vurgulandı; test kapsamı 154 teste güncellendi.
  - Fihrist (`index.md`) güncellenerek ADR-006 MOC listesine eklendi.
  - İlgili tüm atomik modüller (`pyinstaller-standalone-packaging.md`, `inno-setup-installer.md`, `github-actions-release-workflow.md`, `cross-platform-installers.md`) çift yönlü wikilink grafına bağlandı.
  - Living Architecture graf hijyeni (kırık link ve yetim sayfa denetimi) çalıştırıldı ve %100 temiz geçti.
- **Etkilenen Sayfalar:** [[adr-006-windows-standalone-installer-and-ci]], [[cross-platform-installers]], [[pyinstaller-standalone-packaging]], [[inno-setup-installer]], [[github-actions-release-workflow]], [[index]], [[log]]

---

## [2026-09-26] feat | Wine ve Eski Windows Sistemleri için ICU Kütüphanelerinin Pakete Dahil Edilmesi (v2.1.1)
- **Ajan Rolü:** Paketleme ve Dağıtım Mühendisi
- **Yapılan İşlem:**
  - `packaging/kast.spec` güncellendi: Windows System32 altındaki `icuuc.dll` ve `icuin.dll` sistem kütüphaneleri `binaries` listesine eklenerek PyInstaller paketine dahil edildi.
  - Wine (Linux) ortamında sanal system32 içerisinde `icuuc.dll` bulunmamasından kaynaklanan `ImportError: DLL load failed while importing QtCore` hatası giderildi.
  - `tests/test_packaging.py` içine spec dosyasının `icuuc.dll` içerdiğini doğrulayan birim testi eklendi.
  - Inno Setup varsayılan sürümü `2.1.1` olarak güncellendi.
- **Etkilenen Sayfalar:** [[pyinstaller-standalone-packaging]], [[inno-setup-installer]], [[log]]



