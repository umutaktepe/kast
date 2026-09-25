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
  - batch-processing
---

# Modül: Qt6 Desktop GUI ve DropZone Bileşeni

Bu sayfa, Kast 2.0 masaüstü grafiksel kullanıcı arayüzünün (`src/gui.py`), stüdyo sınıfı koyu temasının (`StudioTheme`), sürükle-bırak ve yerel dosya seçici destekli girdi bileşeninin (`DropZoneWidget`), sıralı ve kaynak güvenli arka plan iş parçacığının (`BatchExtractionWorker` / `ExtractionWorker`) ve ana pencere (`KastStudioWindow`) mimarisini belgeler.

Tasarım kararları ve gerekçeleri [[adr-005-qt6-windows-studio-gui]] ve [[adr-007-batch-file-processing-pipeline]] belgelerinde detaylandırılmıştır.

---

## 1. Mimari Rol ve Bileşen Yapısı

Kast 2.0 masaüstü arayüzü, PySide6 (Qt6) kütüphanesi üzerine kurulu olup şu temel bileşenlerden oluşur:

| Bileşen | Taban Sınıf | Temel Sorumluluk |
| :--- | :--- | :--- |
| `StudioTheme` | Nesne / Sabitler | Tokyo Night stüdyo renk paleti, tipografi kuralları ve QSS stil şablonunu sağlar. |
| `DropZoneWidget` | `QFrame` | 25 dosyaya kadar `.docx` ve `.pdf` dosyalarını sürükle-bırak ve yerel dosya seçiciyle kabul eden, homojenlik doğrulayan çift durumlu görsel kart. |
| `BatchExtractionWorker` | `QThread` | Birden çok çeviri dosyasını sıralı (concurrency = 1) işleyen, dosya bazında hata toleransı sağlayan ve arayüzü dondurmayan arka plan iş parçacığı. |
| `ExtractionWorker` | `BatchExtractionWorker` | Geriye dönük uyumluluk sağlayan tekil dosya iş parçacığı sarmalayıcısı. |
| `KastStudioWindow` | `QMainWindow` | Bırakma alanı, sıralama/çıktı kontrolleri, ilerleme çubuğu, dinamik sonuç kartı ve işlem günlüğünü barındıran ana pencere. |
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

## 3. DropZoneWidget ve Çoklu Dosya Doğrulama Motoru

`DropZoneWidget`, kullanıcının tekil veya çoklu (25 adede kadar) senaryo dosyalarını en az eforla sisteme aktarmasını sağlayan interaktif ve korumalı bir bileşendir:

### Sürükle-Bırak Mekanizması ve Dosya Seçici
- `setAcceptDrops(True)` ile sürükleme olaylarını dinler.
- `dragEnterEvent`: Bırakılmak istenen nesnelerin yerel dosya URL'si olup olmadığını (`event.mimeData().hasUrls()`) denetler. En az bir geçerli `.docx` veya `.pdf` varsa kenarlık rengini `border_focus` (`#38bdf8`) yapar ve `event.acceptProposedAction()` çağırır.
- `dragLeaveEvent`: Fare bırakma alanından çıktığında kenarlık rengini varsayılan `border` durumuna döndürür.
- `dropEvent`: Bırakılan tüm URL yollarını ayıklar ve `set_files(paths)` doğrulama motoruna iletir.
- **Yerel Çoklu Dosya Seçici:** "☁  Dosya Seç" butonu `QFileDialog.getOpenFileNames(...)` çağırarak kullanıcının yerel dosya yöneticisinden `Ctrl+A` veya `Shift+Tık` ile çoklu seçim yapabilmesini sağlar.

### Çoklu Dosya Doğrulama Kuralları (`validate_file_paths`)
Bileşen, sisteme dosya kabul etmeden önce sınıf seviyesindeki `validate_file_paths(paths)` fonksiyonunu çalıştırır:
1. **Yol Temizliği ve Tekilleştirme:** Liste elemanlarındaki boşluklar ve tırnaklar (`p.strip().strip("'\"")`) temizlenir; boş öğeler elenir; sıralı sıra korunarak `dict.fromkeys` ile yinelenen yollar elenir.
2. **Boş Liste Kontrolü:** Geçerli dosya yolu kalmamışsa işlem reddedilir (`Dosya listesi boş.`).
3. **25 Dosya Tavan Sınırı (`MAX_FILES = 25`):** Seçilen dosya sayısı 25'i aşıyorsa işlem reddedilir (`En fazla 25 dosya seçebilirsiniz. (N dosya seçildi)`).
4. **Desteklenen Uzantı Kontrolü:** Yalnızca `.docx` ve `.pdf` uzantılı dosyalar kabul edilir; farklı uzantılar (`.txt`, `.xlsx` vb.) reddedilir.
5. **Homojen Dosya Türü Kuralı (Uniform Extension):** Liste hem `.docx` hem `.pdf` dosyalarını aynı anda içeremez (`Lütfen yalnızca .docx veya yalnızca .pdf dosyaları seçin. Karma dosya türleri desteklenmemektedir.`).

### Çift Durumlu Görsel Arayüz (Dual-State Layout)
- **Boş Durum (`empty_container`):**
  - Kesikli lacivert kenarlık (`dashed 1.5px #223554`, arka plan `#0c1424`, fare üzerine gelince `#38bdf8` / `#111d33`).
  - Dairesel mavi bulut ikonu rozeti (`☁↑`, `border: 1.5px solid #0284c7`, zemin `#111d33`, çap 52px).
  - Başlık metni ("Çeviri dosyasını (.docx veya .pdf) buraya sürükleyip bırakın").
  - Alt metin ("Microsoft Word veya metin formatlı çeviri PDF'leri desteklenmektedir.").
  - Format hapları (`.DOCX` ve `.PDF` etiketleri).
  - "☁  Dosya Seç" butonu (`QFileDialog.getOpenFileNames`).
- **Yüklü Durum (`loaded_container`):**
  - Dolu yeşil kenarlık (`solid 1.5px #10b981`).
  - **Dinamik Format Rozeti:**
    - Tekil dosya seçildiğinde: `DOCX` (`#0284c7`) veya `PDF` (`#f43f5e`).
    - Çoklu dosya seçildiğinde: `DOCX (N Dosya)` veya `PDF (N Dosya)` rozeti.
  - **Dosya Bilgisi:**
    - Tekil dosyada: Tam dosya adı (ör. `bolum_01.docx`).
    - Çoklu dosyada: `N adet çeviri dosyası hazır` başlığı ve dosya listesi tooltip'i.
    - **Tooltip:** Fare bileşen üzerine geldiğinde seçilen tüm dosyaların tam yollarını listeleyen açıklama penceresi (`\n` ile birleştirilmiş).
  - **Kümülatif Boyut Bilgisi:** Seçili tüm geçerli dosyaların disk boyutlarının toplamı insan tarafından okunabilir biçimde gösterilir (ör. `14.2 MB`).
  - **"✕ Değiştir" Butonu:** Mevcut seçimi sıfırlayarak boş duruma geri döndürür (`clear()`).

### Sinyal ve Metot Sözleşmesi
- `MAX_FILES = 25`: Tek bir işlemde seçilebilecek azami dosya adedi sabiti.
- `file_selected(str)`: Yeni bir dosya yüklendiğinde ilk dosya yolunu yayınlayan geriye dönük uyumlu Qt Sinyali.
- `files_selected(list)`: Doğrulanmış dosya yolları listesini (`list[str]`) yayınlayan birincil Qt Sinyali.
- `validation_error(str)`: Format, karma uzantı veya maksimum adet kuralları ihlal edildiğinde hata metnini yayınlayan Qt Sinyali.
- `validate_file_paths(paths: list[str]) -> tuple[bool, str, list[str]]`: Dosya listesini homojenlik, uzantı ve 25 dosya sınırına göre doğrulayan sınıf metodu.
- `set_files(paths: list[str]) -> bool`: Dosya listesini doğrulayıp arayüze yükler, hata durumunda `validation_error` sinyali yayar.
- `get_files() -> list[str]`: Seçili tüm dosya yollarının listesini döner.
- `set_file(path: str)`: Tekil dosya atayan geriye dönük uyumlu metod (`set_files([path])` çağırır).
- `clear()`: Seçili dosyaları temizler ve bileşeni boş duruma getirir.
- `get_file_path() -> Optional[str]`: İlk seçili dosyanın mutlak yolunu döner (geriye dönük uyumlu).

---

## 4. BatchExtractionWorker ve ExtractionWorker Asenkron İşleme Mimarisi

Kast çıkarma süreci (özellikle LibreOffice ile PDF sayfa eşleme veya büyük Word senaryolarının OpenXML analizi) yoğun CPU ve I/O işlemi gerektirir. Ana arayüz iş parçacığının (GUI main thread) donmasını engellemek ve LibreOffice / Word kilitlenmelerini önlemek amacıyla [[adr-007-batch-file-processing-pipeline]] kararı uyarınca sıralı ve hata toleranslı `BatchExtractionWorker(QThread)` mimarisi kullanılır.

### Sıralı Yürütme Mimarisi (Concurrency = 1)
Toplu dosya işleme sürecinde paralel iş parçacığı (`QThreadPool` / çoklu thread) yerine bilhassa **sıralı yürütme (`concurrency = 1`)** tercih edilmiştir:
1. **LibreOffice Profil Kilidi Güvenliği:** Headless LibreOffice (`soffice`) motoru arka planda kullanıcı profil dizininde `.lock` kilit dosyası oluşturur. Birden fazla süreç aynı anda çağrıldığında profil çekişmesi sebebiyle kilitlenmeler (deadlock) ve çökme hataları oluşur.
2. **Microsoft Word COM Çakışmaları:** Windows Word COM otomasyonu tekil STA iş parçacığı modelinde çalışır; paralel çağrılarda `RPC_E_SERVERCALL_RETRYLATER` hataları fırlatır.
3. **Sistem Kaynak Koruması:** Dublaj stüdyolarındaki iş istasyonlarında DAW (Pro Tools, Nuendo vb.) yazılımları aktifken aşırı CPU/RAM tüketiminin stüdyo kayıtlarını aksatması önlenir.

### BatchExtractionWorker Sinyal Arayüzü

| Sinyal | Parametre Tipleri | Görevi |
| :--- | :--- | :--- |
| `progress` | `int, str` | Yüzdelik genel ilerleme değeri (0-100) ve detaylı dosya durum metni. |
| `log` | `str` | Konsol alanına yazılacak renkli ve biçimlendirilmiş işlem günlüğü satırı. |
| `file_started` | `int, int, str` | Dosya başladığında `(current_index, total_files, filename)`. |
| `file_completed` | `int, int, str, object` | Dosya başarıyla bittiğinde `(current_index, total_files, output_path, result)`. |
| `file_error` | `int, int, str, str` | Dosyada hata çıktığında `(current_index, total_files, filename, error_msg)`. |
| `all_finished` | `list` | Tüm dosyaların durum özetini (`list[dict]`) yayınlar. |

### İlerleme Matematiği (Progress Math)
Toplu işleme sürecinde yüzdelik ilerleme çubuğu dosya adetlerine göre dilimlenir ve pürüzsüz biçimde ilerler:
- Toplam $N$ dosya için dosya başına yüzdelik dilim: $P_{\text{file}} = 100.0 / N$.
- $i$. dosya işlenirken ($i \in [0, N-1]$), taban yüzde: $\text{base\_pct} = \lfloor i \times P_{\text{file}} \rfloor$.
- Dosya içindeki alt işlemden gelen yüzde $p \in [0, 100]$ şu formülle genel ilerlemeye ölçeklenir:
  $$\text{overall\_pct} = \text{base\_pct} + \left\lfloor \frac{p \times P_{\text{file}}}{100.0} \right\rfloor$$
- Bir dosya tamamlandığında genel ilerleme doğrudan bir sonraki dilime yükseltilir: $\lfloor (i + 1) \times P_{\text{file}} \rfloor$.
- Tüm liste bittiğinde `%100` sinyaliyle süreç sonlanır. Bu matematik ilerlemenin sıçrama yapmadan monoton artmasını garanti eder.

### Dosya Bazında Hata İzolasyonu ve Toleransı (Per-File Fault Tolerance)
Worker, dosyaları tek tek sıralı döngüyle işler:
- Her bir dosya bağımsız `try...except Exception as e` bloğunda çalıştırılır.
- Bir dosyada `PermissionError`, `ValueError` veya bozuk XML gibi bir istisna oluşursa işlem durmaz; hata yakalanır, `file_error` sinyali yayılır, konsola kırmızı renkle yazılır ve özet tablosuna eklenir:
  ```python
  summary.append({
      "file_path": path,
      "output_path": None,
      "result": None,
      "status": "error",
      "error": str(e)
  })
  ```
- Sıradaki diğer dosyalar kesintisiz işlenmeye devam eder (`fail-fast` uygulanmaz).
- Başarıyla tamamlanan dosyalar özet tablosuna eklenir:
  ```python
  summary.append({
      "file_path": path,
      "output_path": out_path,
      "result": result,
      "status": "success",
      "error": None
  })
  ```
- Tüm dosyalar tamamlandığında `all_finished(summary)` sinyaliyle tam liste ana pencereye iletilir.

### Geriye Dönük Uyumluluk (`ExtractionWorker`)
Eski tekil dosya işleme akışını ve testleri korumak için `ExtractionWorker`, `BatchExtractionWorker([file_path], ...)` sınıfından kalıtım alır:
- `finished = Signal(str, object)` ve `error = Signal(str)` sinyallerini barındırır.
- `all_finished` sinyalini dinleyerek ilk dosyanın başarı durumuna göre `finished` veya `error` yayar.
- `is_single_compat` moduyla tekil dosya ilerleme ve log formatlarını tam geriye dönük uyumlu korur.

---

## 5. KastStudioWindow ve Stüdyo İş Akışı

`KastStudioWindow`, gece mavisi ve elektrik camgöbeği stüdyo mockup görseliyle birebir uyumlu bir iş istasyonu hiyerarşisi sunar:

1. **Header Bölümü:**
   - İki parçalı başlık: `lbl_title_prefix` ("Kast 2.0", `#38bdf8`, 20px, bold) ve `lbl_title_suffix` (" — Dublaj Kast Çıkarma", `#f8fafc`, 20px, bold).
   - Alt başlık: `lbl_subtitle` ("Senaryo belgelerindeki diyalogları ve karakter listesini otomatik analiz eder.", `#64748b`, 13px).
   - Sağ üst rozet: `lbl_badge` ("● Windows Studio Edition • Qt6", background `#0f293a`, border `1px solid #084c61`, color `#38bdf8`, padding `4px 12px`, border-radius `12px`).

2. **Merkezi Bırakma Alanı (`DropZoneWidget`):**
   - 25 dosyaya kadar çoklu sürükle-bırak veya dosya seçici kabul eden korumalı girdi paneli.
   - Dosya seçildiğinde `_on_files_selected(paths)` tetiklenir:
     - Tekil dosyada dosya adı ve uzantı bilgisi konsola yazılır.
     - Çoklu dosyada `N adet dosya seçildi` bilgisi günlüğe düşülür.
     - PDF seçildiğinde `tile_inplace.setEnabled(False)` ve `tile_standalone.setChecked(True)` kuralı işletilir.
     - Durum çubuğu metni önceki olası hataları temizleyerek `● Durum: Hazır` haline getirilir.
   - Doğrulama hatasında `_on_validation_error(err_msg)` tetiklenir:
     - Durum çubuğu kırmızı `● Hata: {err_msg}` metnine bürünür.
     - Konsol günlüğüne kırmızı renkle hata kaydı yazılır.

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

4. **Aksiyon Butonları:**
   - Geniş parlak camgöbeği `btn_extract` ("▶  Kast Tablosunu Çıkar", `btn-primary`, stretch=4).
   - Koyu ikincil `btn_clear` ("🗑  Temizle", `btn-clear`, stretch=1).

5. **Durum ve İlerleme Göstergesi:**
   - Sol tarafta `lbl_status` ("● Durum: Hazır", `#94a3b8`) ve sağ tarafta yüzdelik `lbl_pct` ("%0", `#38bdf8`, bold).
   - 6px yüksekliğinde ince elektrik camgöbeği ilerleme çizgisi (`progress_bar`, `textVisible=False`).

6. **İşlem Günlüğü Monospace Terminali (`log_area`):**
   - Başlık satırı: `lbl_log_title` ("🖥  İŞLEM GÜNLÜĞÜ", `#64748b`, bold) ve `lbl_log_meta` ("UTF-8 / Terminal hazır", `#475569`, monospace).
   - Siyah stüdyo konsol kutusu (`QTextEdit`, `#080c14` zemin, `#cbd5e1` monospace metin).

7. **Dinamik Sonuç Rozet Kartı (`result_card`):**
   - `BatchExtractionWorker` tamamlandığında `_on_batch_finished(summary)` tetiklenir ve sonuçlar analiz edilir:
     - **Tam Başarı (0 Hata):** Yeşil (`#10b981`) rozetle toplam karakter sayısı, replik adedi ve işlenen dosya oranı (`✓ M/N dosya başarıyla oluşturuldu! (Toplam: X Karakter • Y Replik)`).
     - **Kısmi Hata (`len(successes) > 0 and len(errors) > 0`):** Kehribar sarısı (`#f59e0b`) rozetle `⚠️ Kısmi Tamamlandı: M/N başarılı, K dosyada hata oluştu.`
     - **Tam Başarısızlık (`len(successes) == 0`):** Kırmızı (`#f43f5e`) rozetle `❌ İşlem Başarısız: K/N dosyada hata oluştu.`
   - **Aksiyon Butonları Uyarlaması:**
     - Tekil dosyada: `"📄 Dosyayı Aç"`.
     - Çoklu dosyada: `"📄 Son Dosyayı Aç"`.
     - En az bir başarılı dosya varsa ve `last_output_file` mevcutsa buton aktifleşir; aksi halde pasifleşir.
     - "📁 Klasörde Göster" butonu ile yerel dosya gezgini son çıktının bulunduğu dizini açar.

8. **Durum Çubuğu (StatusBar):**
   - Sol: `lbl_status_left` ("PySide6 Modern Frame  |  Hazır").
   - Sağ: `lbl_status_right` ("Encoding: UTF-8").

9. **Pencere İkonu ve Görev Çubuğu:**
   - `KastStudioWindow.__init__` içinde `setWindowIcon(QIcon(...))` çağrısıyla `packaging/assets/kast_icon.png` veya `kast.ico` pencereye atanır.
   - PyInstaller demetlerinde `sys._MEIPASS` desteğiyle ikonun gömülü paket içinden sorunsuz bulunması sağlanır.

10. **Dinamik Mizanpaj ve QScrollArea Taşıyıcısı:**
    - Düşük çözünürlüklü ekranlar veya tam ekran olmayan pencereli kullanımlarda bileşenlerin ezilmesini önlemek için merkezi widget `QScrollArea` (`scroll_area`) ile sarmalanmıştır.
    - `OptionTileWidget` ve `DropZoneWidget` bileşenleri sabit/minimum yükseklik ve `QSizePolicy.Fixed` dikey boyutuyla korunur; pencere büyütüldüğünde ekstra dikey alan `log_area` konsoluna aktarılır (`stretch=1`).

---

## 6. Başlatma ve Dağıtım Mekanizmaları

Masaüstü arayüzü farklı kullanım senaryolarına göre başlatılabilir:

- **Bağımsız Windows Kurulum ve Taşınabilir Paketleri (Zero-Python):** Son kullanıcılar için üretilen `Kast-vX.Y.Z-Setup.exe` kurulum sihirbazı veya `Kast-vX.Y.Z-Windows-Portable.zip` dağıtımı, Python kurulumu gerektirmeden doğrudan masaüstü/başlat menüsü kısayolları ve `KastStudio.exe` üzerinden konsolsuz çalışır ([[inno-setup-installer]], [[pyinstaller-standalone-packaging]]).
- **Komut Satırı / Terminal Entegrasyonu:** `install.bat` / `install.ps1` veya `install.sh` betikleriyle geliştirici ortamı kurulduğunda, terminalden `kast --gui` veya `kast -g` komutu verilerek doğrudan Qt6 Studio arayüzü başlatılır ([[hybrid-cli-dispatcher]], [[cross-platform-installers]]). Bu sayede sisteme ayrı/fazladan bir başlatıcı dosya yüklenmeden tekil `kast` komutu üzerinden GUI'ye erişilir.

---

## 7. İlgili Sayfalar

- [[adr-005-qt6-windows-studio-gui]] — Qt6 masaüstü grafik arayüzü mimari kararı.
- [[adr-007-batch-file-processing-pipeline]] — Çoklu dosya seçimi ve sıralı toplu işleme mimari kararı.
- [[pyinstaller-standalone-packaging]] — Bağımsız Windows PyInstaller paketleme ve çoklu ikon üretici.
- [[hybrid-cli-dispatcher]] — CLI, TUI ve GUI başlatma mantığı.
- [[cross-platform-installers]] — Windows batch başlatıcısı ve kurulum betikleri.
- [[terminal-user-interface]] — Textual tabanlı terminal kullanıcı arayüzü.
- [[dubbing-pdf-parser]] — PDF doğrudan senaryo ayrıştırma motoru.
- [[dubbing-docx-parser]] — DOCX senaryo ayrıştırma motoru.
- [[headless-pdf-converter]] — Headless LibreOffice ve Word COM dönüştürücü motoru.
- [[cast-extraction-result]] — GUI sonuç kartına beslenen özet veri modeli.
