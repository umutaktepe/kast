---
title: "Modül: Qt6 Desktop GUI ve DropZone Bileşeni"
type: component
status: active
date: 2026-09-22
domain: interfaces-and-runtime
tags:
  - gui
  - pyside6
  - qt6
  - drop-zone
  - theme
  - qthread
---

# Modül: Qt6 Desktop GUI ve DropZone Bileşeni

Bu sayfa, Kast 2.0 masaüstü grafiksel kullanıcı arayüzünün (`src/gui.py`), stüdyo sınıfı koyu temasının (`StudioTheme`), sürükle-bırak dosya girdi bileşeninin (`DropZoneWidget`), asenkron arka plan iş parçacığının (`ExtractionWorker`) ve ana pencere (`KastStudioWindow`) mimarisini belgeler.

Tasarım kararları ve gerekçeleri [[adr-005-qt6-windows-studio-gui]] belgesinde detaylandırılmıştır.

---

## 1. Mimari Rol ve Bileşen Yapısı

Kast 2.0 masaüstü arayüzü, PySide6 (Qt6) kütüphanesi üzerine kurulu olup şu temel bileşenlerden oluşur:

| Bileşen | Taban Sınıf | Temel Sorumluluk |
| :--- | :--- | :--- |
| `StudioTheme` | Nesne / Sabitler | Tokyo Night stüdyo renk paleti, tipografi kuralları ve QSS stil şablonunu sağlar. |
| `DropZoneWidget` | `QFrame` | `.docx` ve `.pdf` dosyalarını sürükle-bırak ve yerel dosya seçiciyle kabul eden çift durumlu görsel kart. |
| `ExtractionWorker` | `QThread` | Ağır ayrıştırma ve sayfalama işlemlerini arayüzü dondurmadan yürüten arka plan iş parçacığı. |
| `KastStudioWindow` | `QMainWindow` | Bırakma alanı, sıralama/çıktı kontrolleri, ilerleme çubuğu, sonuç kartı ve işlem günlüğünü barındıran ana pencere. |
| `launch_gui()` | Fonksiyon | Fusion stili ve stüdyo temasıyla Qt uygulamasını (`QApplication`) başlatan modül giriş noktası. |

---

## 2. StudioTheme ve Stüdyo Tasarım Dili

Arayüz, seslendirme ve dublaj stüdyolarında uzun saatler çalışan kullanıcıların göz yorgunluğunu önlemek amacıyla modern DAW (Digital Audio Workstation) ve gece mavisi/elektrik camgöbeği stüdyo paletine sahiptir:

### Renk Paleti

| Renk Anahtarı | HEX Kodu | Kullanım Alanı |
| :--- | :--- | :--- |
| `bg_dark` | `#0b0f19` | Pencere ana arka planı (Gece mavisi). |
| `card_bg` | `#0f172a` | Kart panelleri (`card-panel`) zemin rengi. |
| `card_tile` | `#131f38` | Kutulu radyo kartları (`OptionTileWidget`) ve format hapları. |
| `card_tile_selected` | `#1e2e4a` | Seçili radyo kartı arka planı. |
| `border` | `#1e293b` | Varsayılan çerçeve ve ayırıcı çizgi rengi. |
| `border_focus` | `#38bdf8` | Vurgulu / odaklanmış kenarlık rengi (Elektrik camgöbeği). |
| `accent_cyan` | `#38bdf8` | Radyo göstergesi, başlık vurgusu ve rozet rengi. |
| `btn_primary` | `#00e5ff` / `#38bdf8` | Birincil "Kast Tablosunu Çıkar" aksiyon butonu. |
| `terminal_bg` | `#080c14` | Canlı işlem günlüğü monospace konsol kutusu. |
| `text_main` | `#f8fafc` | Birincil metinler ve başlıklar. |
| `text_dim` | `#64748b` | İkincil metinler, ipuçları ve terminal meta bilgisi. |

### Tipografi ve QSS Stil Hiyerarşisi

- **Yazı Tipi Ailesi:** Platforma göre `Segoe UI` (Windows), `Inter`, `-apple-system` (macOS) veya `sans-serif` sırası izlenir.
- **Konsol Fontu:** Log alanında sabit genişlikli `Consolas`, `Cascadia Code` veya `monospace` kullanılır.
- **QSS Sayfası (`get_stylesheet()`):** Tüm Qt widget'ları (`QMainWindow`, `QGroupBox`, `QRadioButton`, `QPushButton`, `QProgressBar`, `QTextEdit`, `QScrollBar`) için modern köşe yuvarlama (`border-radius`), geçiş ve dolgu (padding) tanımlarını merkezi olarak enjekte eder.

---

## 3. DropZoneWidget ve Sürükle-Bırak Motoru

`DropZoneWidget`, kullanıcının senaryo dosyasını en az eforla sisteme aktarmasını sağlayan interaktif bir bileşendir:

### Sürükle-Bırak Mekanizması
- `setAcceptDrops(True)` ile olayları dinler.
- `dragEnterEvent`: Bırakılmak istenen nesnenin yerel bir dosya URL'si olup olmadığını (`event.mimeData().hasUrls()`) ve uzantısının `.docx` veya `.pdf` olduğunu doğrular. Geçerliyse kenarlık rengini `border_focus` (`#7aa2f7`) yapar ve `event.acceptProposedAction()` çağırır.
- `dragLeaveEvent`: Fare bırakma alanından çıktığında kenarlık rengini varsayılan `border` durumuna döndürür.
- `dropEvent`: Bırakılan ilk geçerli dosya yolunu alır, `set_file(path)` metodunu tetikler.

### Çift Durumlu Görsel Arayüz (Dual-State Layout)
- **Boş Durum (`empty_container`):**
  - Kesikli lacivert kenarlık (`dashed 1.5px #223554`, arka plan `#0c1424`, fare üzerine gelince `#38bdf8` / `#111d33`).
  - Dairesel mavi bulut ikonu rozeti (`☁↑`, `border: 1.5px solid #0284c7`, zemin `#111d33`, çap 52px).
  - Başlık metni ("Senaryo dosyasını (.docx veya .pdf) buraya sürükleyip bırakın").
  - Alt metin ("Microsoft Word veya metin formatlı senaryo PDF'leri desteklenmektedir.").
  - Format hapları (`.DOCX` ve `.PDF` etiketleri).
  - "☁  Dosya Seç" butonu (`QFileDialog.getOpenFileName`).
- **Yüklü Durum (`loaded_container`):**
  - Dolu yeşil kenarlık (`solid 1.5px #10b981`).
  - **Format Rozeti:** Dosya türüne göre dinamik renklendirilen `QLabel` rozeti (DOCX için `#0284c7`, PDF için `#f43f5e`).
  - **Dosya Bilgisi:** Dosya adı ve insan tarafından okunabilir dosya boyutu (ör. `1.4 MB`).
  - **"✕ Değiştir" Butonu:** Mevcut seçimi sıfırlayarak boş duruma geri döndürür (`clear()`).

### Sinyal ve Metot Sözleşmesi
- `file_selected(str)`: Yeni bir dosya yüklendiğinde dosya yolunu yayınlayan Qt Sinyali.
- `set_file(path: str)`: Dosyayı programa alır, etiketleri günceller ve arayüzü yüklü duruma geçirir.
- `clear()`: Seçili dosyayı temizler ve bileşeni boş duruma getirir.
- `get_file_path() -> Optional[str]`: Seçili dosyanın mutlak yolunu döner.

---

## 4. ExtractionWorker QThread Asenkron Mimarisi

Kast çıkarma süreci (özellikle LibreOffice ile PDF sayfa eşleme veya büyük Word senaryolarının OpenXML analizi) yoğun CPU ve I/O işlemi gerektirir. Ana arayüz iş parçacığının (GUI main thread) kilitlenmesini önlemek için `ExtractionWorker(QThread)` mimarisi kullanılır:

### Sinyal Arayüzü

| Sinyal | Parametre Tipleri | Görevi |
| :--- | :--- | :--- |
| `progress` | `int, str` | Yüzdelik ilerleme değeri (0-100) ve durum metni. |
| `log` | `str` | Konsol alanına yazılacak renkli işlem günlüğü satırı. |
| `finished` | `str, object` | Üretilen çıktı dosyasının yolu ve [[cast-extraction-result]] nesnesi. |
| `error` | `str` | İşlem sırasında fırlatılan hata iletisi. |

### Yürütme ve Hata İzolasyonu (`run()`)
Worker, `process_dubbing_file()` birleşik yönlendiricisini çağırır:
```python
output_path, result = process_dubbing_file(
    input_path=self.file_path,
    sort_by=self.sort_by,
    in_place=self.in_place,
    standalone=self.standalone,
    progress_callback=lambda pct, msg: self.progress.emit(pct, msg)
)
self.finished.emit(output_path, result)
```
Olası `ValueError`, `FileNotFoundError` veya beklenmeyen istisnalar `except Exception as e` ile yakalanarak güvenle `error` sinyaliyle ana pencereye aktarılır; GUI kesinlikle çökmez.

---

## 5. KastStudioWindow ve Stüdyo İş Akışı

`KastStudioWindow`, gece mavisi ve elektrik camgöbeği stüdyo mockup görseliyle birebir uyumlu bir iş istasyonu hiyerarşisi sunar:

1. **Header Bölümü:**
   - İki parçalı başlık: `lbl_title_prefix` ("Kast 2.0", `#38bdf8`, 20px, bold) ve `lbl_title_suffix` (" — Dublaj Kast Çıkarma", `#f8fafc`, 20px, bold).
   - Alt başlık: `lbl_subtitle` ("Senaryo belgelerindeki diyalogları ve karakter listesini otomatik analiz eder.", `#64748b`, 13px).
   - Sağ üst rozet: `lbl_badge` ("● Windows Studio Edition • Qt6", background `#0f293a`, border `1px solid #084c61`, color `#38bdf8`, padding `4px 12px`, border-radius `12px`).

2. **Merkezi Bırakma Alanı (`DropZoneWidget`):**
   - Dairesel bulut yükleme rozeti (`☁↑`), `.DOCX` ve `.PDF` format etiketleri ve dosya seçici entegre tekil bırakma alanı.

3. **İki Yan Yana Kart Paneli (`QFrame#card-panel`):**
   - **Sol Panel (`card_sort`):** `lbl_sort_title` ("🗂  Karakter Sıralama", `#38bdf8`) başlığı altında 3 adet `OptionTileWidget` kartı:
     - `tile_appearance` ("İlk Görünme Sırası", varsayılan seçili).
     - `tile_count` ("Replik Sayısına Göre").
     - `tile_name` ("Karakter Adına Göre (A-Z)").
   - **Sağ Panel (`card_output`):** `lbl_out_title` ("📄  Çıktı Seçenekleri", `#38bdf8`) başlığı altında 2 adet `OptionTileWidget` kartı:
     - `tile_standalone` ("Ayrı dosya olarak kaydet", alt metin: `(<ad>_kast.docx)`, varsayılan seçili).
     - `tile_inplace` ("Orijinal Word dökümanının sonuna ekle").
     - Yatay ayraç çizgisi ve `lbl_output_meta` alt bilgi satırı (`Çıktı Biçimi: .docx Tablo  |  Varsayılan şablon v2.1`).
   - **Grup ve Karşılıklı Dışlama (`OptionTileGroup`):**
     - Kartlar radyo göstergesi, başlık ve opsiyonel camgöbeği alt metin içerir.
     - Tıklama veya programatik `setChecked(True)` çağrısı aynı gruptaki kardeş kartları otomatik olarak devreden çıkarır.
     - Geriye uyumluluk için `window.rb_appearance`, `window.rb_count`, `window.rb_name`, `window.rb_standalone`, `window.rb_inplace` takma adları korunmuştur.
     - PDF seçildiğinde `tile_inplace.setEnabled(False)` ve `tile_standalone.setChecked(True)` kuralı işletilir.

4. **Aksiyon Butonları:**
   - Geniş parlak camgöbeği `btn_extract` ("▶  Kast Tablosunu Çıkar", `btn-primary`, stretch=4).
   - Koyu ikincil `btn_clear` ("🗑  Temizle", `btn-clear`, stretch=1).

5. **Durum ve İlerleme Göstergesi:**
   - Sol tarafta `lbl_status` ("● Durum: Hazır", `#94a3b8`) ve sağ tarafta yüzdelik `lbl_pct` ("%0", `#38bdf8`, bold).
   - 6px yüksekliğinde ince elektrik camgöbeği ilerleme çizgisi (`progress_bar`, `textVisible=False`).

6. **İşlem Günlüğü Monospace Terminali (`log_area`):**
   - Başlık satırı: `lbl_log_title` ("🖥  İŞLEM GÜNLÜĞÜ", `#64748b`, bold) ve `lbl_log_meta` ("UTF-8 / Terminal hazır", `#475569`, monospace).
   - Siyah stüdyo konsol kutusu (`QTextEdit`, `#080c14` zemin, `#cbd5e1` monospace metin).

7. **Sonuç Rozet Kartı (`result_card`):**
   - İşlem bittiğinde toplam karakter sayısı, replik adedi ve sayfa sayısını yeşil rozetle sunar.
   - "📁 Klasörde Göster" ve "📄 Dosyayı Aç" yerel sistem entegrasyon butonları.

8. **Durum Çubuğu (StatusBar):**
   - Sol: `lbl_status_left` ("PySide6 Modern Frame  |  Hazır").
   - Sağ: `lbl_status_right` ("Encoding: UTF-8").

9. **Pencere İkonu ve Görev Çubuğu:**
   - `KastStudioWindow.__init__` içinde `setWindowIcon(QIcon(...))` çağrısıyla `packaging/assets/kast_icon.png` veya `kast.ico` pencereye atanır.
   - PyInstaller demetlerinde `sys._MEIPASS` desteğiyle ikonun gömülü paket içinden sorunsuz bulunması sağlanır.

10. **Dinamik Mizanpaj ve QScrollArea Taşıyıcısı:**
   - Düşük çözünürlüklü ekranlar veya tam ekran olmayan pencereli kullanımlarda bileşenlerin ezilmesini ve metinlerin 0 yüksekliğe düşmesini önlemek için merkezi widget `QScrollArea` (`scroll_area`) ile sarmalanmıştır.
   - `OptionTileWidget` ve `DropZoneWidget` bileşenleri sabit/minimum yükseklik ve `QSizePolicy.Fixed` dikey boyutuyla korunur; pencere büyütüldüğünde veya tam ekrana alındığında ekstra dikey alan `log_area` konsoluna aktarılır (`stretch=1`).

---

## 6. Başlatma ve Dağıtım Mekanizmaları

Masaüstü arayüzü farklı kullanım senaryolarına göre başlatılabilir:

- **Bağımsız Windows Paketi (PyInstaller):** Python gerektirmeyen `dist/KastStudio/` dağıtımı, `packaging/run_gui.py` giriş noktası üzerinden doğrudan konsolsuz çalışır ([[pyinstaller-standalone-packaging]]).
- **Windows Masaüstü / Çift Tıklama:** Kurulumda oluşturulan `kast-gui.cmd` dosyası sanal ortamı (`.venv`) otomatik bağlayarak doğrudan GUI penceresini açar.
- **Komut Satırı:** `kast --gui` veya `kast -g` parametresi hibrit başlatıcı ([[hybrid-cli-dispatcher]]) tarafından yakalanıp `launch_gui()` fonksiyonunu çalıştırır.
- **Otomatik Kurulum:** Windows için `install.ps1` betiği `PySide6` kütüphanesini sanal ortama kurar ve `%USERPROFILE%\bin\kast-gui.cmd` dosyasını oluşturur ([[cross-platform-installers]]).

---

## 7. İlgili Sayfalar

- [[adr-005-qt6-windows-studio-gui]] — Qt6 masaüstü grafik arayüzü mimari kararı.
- [[pyinstaller-standalone-packaging]] — Bağımsız Windows PyInstaller paketleme ve çoklu ikon üretici.
- [[hybrid-cli-dispatcher]] — CLI, TUI ve GUI başlatma mantığı.
- [[cross-platform-installers]] — Windows batch başlatıcısı ve kurulum betikleri.
- [[terminal-user-interface]] — Textual tabanlı terminal kullanıcı arayüzü.
- [[dubbing-pdf-parser]] — PDF doğrudan senaryo ayrıştırma motoru.
- [[cast-extraction-result]] — GUI sonuç kartına beslenen özet veri modeli.
