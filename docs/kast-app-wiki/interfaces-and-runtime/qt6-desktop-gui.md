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

Arayüz, seslendirme ve dublaj stüdyolarında uzun saatler çalışan kullanıcıların göz yorgunluğunu önlemek amacıyla Tokyo Night ve modern DAW (Digital Audio Workstation) yazılımlarından ilham alan koyu bir tema paletine sahiptir:

### Renk Paleti

| Renk Anahtarı | HEX Kodu | Kullanım Alanı |
| :--- | :--- | :--- |
| `bg_dark` | `#1a1b26` | Pencere ana arka planı. |
| `bg_card` | `#24283b` | Kartlar, paneller ve bırakma alanı zeminleri. |
| `bg_card_hover` | `#2f354a` | Bırakma alanı ve buton üzerine gelme (hover) rengi. |
| `border` | `#414868` | Varsayılan çerçeve ve ayırıcı çizgi rengi. |
| `border_focus` | `#7aa2f7` | Vurgulu / odaklanmış kenarlık rengi (Mavi). |
| `accent_blue` | `#7aa2f7` | Birincil butonlar, DOCX rozeti ve aktif seçimler. |
| `accent_green` | `#9ece6a` | Başarı durumları, tamamlanma rozetleri ve onay butonları. |
| `accent_pink` | `#f7768e` | PDF format rozeti, hata mesajları ve iptal butonları. |
| `text_main` | `#c0caf5` | Birincil metinler ve etiketler. |
| `text_dim` | `#7982a9` | İkincil metinler, ipuçları ve pasif etiketler. |
| `bg_console` | `#16161e` | Canlı işlem günlüğü (log) konsolu arka planı. |

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
  - Geniş kesikli kenarlık (`dashed 2px #414868`).
  - Büyük sembol (`📥`), açıklama metni ("Senaryo dosyasını buraya sürükleyin (.docx veya .pdf)").
  - "📁 Dosya Seç" butonu (`QFileDialog.getOpenFileName`).
- **Yüklü Durum (`loaded_container`):**
  - Dolu kenarlık (`solid 2px #7aa2f7`).
  - **Format Rozeti:** Dosya türüne göre dinamik renklendirilen `QLabel` rozeti (DOCX için mavi `#7aa2f7`, PDF için pembe `#f7768e`).
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

`KastStudioWindow`, kullanıcıya baştan sona rehberlik eden bir iş istasyonu düzeni sunar:

1. **Akıllı Format Denetimi:**
   - Bir PDF dosyası yüklendiğinde, orijinal PDF üzerine Word tablosu yazılamayacağı için "Orijinal Dosyaya Ekle (In-Place)" seçeneği kilitlenir (`setEnabled(False)`) ve "Ayrı Belge (Standalone)" seçeneği zorunlu kılınır.
   - DOCX yüklendiğinde her iki çıktı modu da serbestçe seçilebilir.
2. **Sıralama Seçenekleri:** Replik Sayısına Göre (`count`), İlk Görünme Sırasına Göre (`appearance`) veya Alfabetik (`name`).
3. **Canlı Monospace Konsol (`log_area`):**
   - İşlemin her adımını zaman damgası ve renk kodlarıyla konsol formatında gösterir (Bilgi için mavi `#7dcfff`, ilerleme için lila `#bb9af7`, başarı için yeşil `#9ece6a`, hata için pembe `#f7768e`).
4. **Sonuç Rozet Kartı (`result_card`):**
   - İşlem bittiğinde toplam karakter sayısı, replik adedi ve sayfa sayısını görsel rozetler halinde sunar.
   - **"📁 Klasörde Göster" Butonu:** Çıktı dosyasının bulunduğu dizini işletim sisteminin yerel dosya yöneticisinde seçili olarak açar (`explorer /select,` / `open -R` / `xdg-open`).
   - **"📄 Dosyayı Aç" Butonu:** Üretilen Word belgesini varsayılan ofis uygulamasında açar (`os.startfile` / `open` / `xdg-open`).

---

## 6. Başlatma ve Dağıtım Mekanizmaları

Masaüstü arayüzü farklı kullanım senaryolarına göre başlatılabilir:

- **Windows Masaüstü / Çift Tıklama:** Kurulumda oluşturulan `kast-gui.cmd` dosyası sanal ortamı (`.venv`) otomatik bağlayarak doğrudan GUI penceresini açar.
- **Komut Satırı:** `kast --gui` veya `kast -g` parametresi hibrit başlatıcı ([[hybrid-cli-dispatcher]]) tarafından yakalanıp `launch_gui()` fonksiyonunu çalıştırır.
- **Otomatik Kurulum:** Windows için `install.ps1` betiği `PySide6` kütüphanesini sanal ortama kurar ve `%USERPROFILE%\bin\kast-gui.cmd` dosyasını oluşturur ([[cross-platform-installers]]).

---

## 7. İlgili Sayfalar

- [[adr-005-qt6-windows-studio-gui]] — Qt6 masaüstü grafik arayüzü mimari kararı.
- [[hybrid-cli-dispatcher]] — CLI, TUI ve GUI başlatma mantığı.
- [[cross-platform-installers]] — Windows batch başlatıcısı ve kurulum betikleri.
- [[terminal-user-interface]] — Textual tabanlı terminal kullanıcı arayüzü.
- [[dubbing-pdf-parser]] — PDF doğrudan senaryo ayrıştırma motoru.
- [[cast-extraction-result]] — GUI sonuç kartına beslenen özet veri modeli.
