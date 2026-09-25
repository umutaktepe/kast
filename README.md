# Kast 2.0 — Dublaj Çevirisi Kast Çıkarma Sistemi

**Kast 2.0**, dublaj çevirmenleri, seslendirme yönetmenleri ve stüdyolar için geliştirilmiş modern bir kast tablosu çıkarma ve döküman zenginleştirme aracıdır.

Microsoft Word (`.docx`) formatındaki dublaj çeviri senaryolarını doğrudan analiz eder; karakterlerin repliklerini, replik sayılarını ve senaryodaki sayfa numaralarını yüksek hassasiyetle tespit ederek profesyonel bir **Kast Tablosu** oluşturur ve dökümanın sonuna yeni bir sayfa olarak otomatik ekler.

---

## 🚀 Kast 2.0 ile Gelen Yenilikler

Geleneksel kast çıkarma araçları veya manuel yöntemlere kıyasla Kast 2.0 şu temel avantajları sunar:

1. **Modern Terminal Kullanıcı Arayüzü (TUI):**
   - Terminalde yalnızca `kast` yazarak açılan, koyu temalı görsel bir Textual arayüzü sunar.
   - Sürükle-bırak dosya girdi alanları, radyo butonları, çıktı seçenekleri ve canlı işlem günlüğü içerir.
2. **Akıllı Hibrit Başlatıcı:**
   - Argümansız çalıştırıldığında (`kast`) görsel TUI açılır; dosya veya bayrak ile çalıştırıldığında (`kast dosya.docx --count`) doğrudan süper hızlı komut satırı modunda çalışır.
3. **DOCX Üzerinden Doğrudan Çalışma:**
   - Metinleri kopyalayıp düz metne (`.txt`) çevirmenize veya Word biçimlendirmelerini bozmanıza gerek yoktur. Dökümanı doğrudan olduğu gibi işler.
4. **Başlık ve Meta Veri Filtreleme (Başlık Silmeye Son!):**
   - Senaryonun başında yer alan `FİLMİN ADI`, `ÇEVİRMEN`, `KAYIT TARİHİ`, `SESLENDİRME STÜDYOSU` gibi proje başlıklarını ve `00.41`, `01.12.05` gibi süre kodlarını akıllıca ayırt eder.
   - Başlıkların veya zaman kodlarının yanlışlıkla karaktere dönüşmesi engellenir; senaryo başındaki künyeyi elle silme zorunluluğu tamamen ortadan kalkar.
5. **Çok Katmanlı Otomatik Sayfa Tespiti:**
   - Sayfa numaralarını bulmak için Word'de tek tek elle arama yapmaya veya PDF'e dönüştürmeye gerek kalmaz.
   - Belgedeki OpenXML sayfa sonlarını, isteğe bağlı referans PDF eşleştirmesini ve saf Python mizanpaj simülatörünü bir arada kullanarak repliklerin hangi sayfalarda geçtiğini otomatik tespit eder.
6. **Otomatik Tablo Entegrasyonu ve Güvenli Kayıt:**
   - Çıkarılan kast tablosu Word ile %100 uyumlu tam kenarlıklı (Table Grid) biçimde dökümanın en sonuna yeni bir sayfa olarak eklenir.
   - Orijinal dökümanın güvenliği için varsayılan olarak `<dosya_adi>_kast.docx` adıyla yeni bir kopya oluşturulur (istenirse `--in-place` ile doğrudan orijinal dosyaya da yazılabilir).

---

## ⚡ Kurulum ve İndirme

### 🪟 Windows (Önerilen — Sıfır Bağımlılık / Python GEREKTİRMEZ)

Dublaj stüdyoları ve Windows kullanıcıları için herhangi bir Python kurulumu, terminal veya ortam konfigürasyonu gerektirmeyen hazır paketler sunulmaktadır. [GitHub Releases](https://github.com/umutaktepe/kast/releases) sayfasından en son sürümü temin edebilirsiniz:

- **💾 Kurulum Sihirbazı (`Kast-vX.Y.Z-Setup.exe`):**
  - Çift tıklayarak klasik Windows sihirbazı ile kolayca kurun.
  - Masaüstü ve Başlat Menüsü kısayollarını otomatik oluşturur.
  - **Akıllı Ofis Tespiti:** Sistemde Microsoft Word veya LibreOffice varlığını otomatik denetler. İkisi de yoksa, senaryo sayfa numaralarını %100 kesinlikle tespit edebilmek için gereken LibreOffice paketini arka planda sessizce (silent) indirip kurar. Sizin hiçbir ek işlem yapmanız gerekmez!
- **💼 Taşınabilir Sürüm (`Kast-vX.Y.Z-Windows-Portable.zip`):**
  - Kurulum veya yönetici yetkisi gerektirmez.
  - ZIP arşivini dilediğiniz bir klasöre veya USB belleğe çıkartıp `KastStudio.exe` dosyasını doğrudan çalıştırabilirsiniz.

---

### 🛠️ Kaynak Koddan Kurulum (Geliştiriciler ve Linux/macOS)

Depoyu klonlayarak yerel Python ortamınızda çalıştırmak isterseniz:

#### 🐧 Linux / macOS (Bash)
```bash
git clone https://github.com/umutaktepe/kast.git
cd kast
chmod +x install.sh && ./install.sh
```
*Bu script sanal ortamı kurar, bağımlılıkları yükler ve `~/.local/bin/kast` sembolik bağını oluşturur. Artık terminalinizin herhangi bir yerinden sadece `kast` yazmanız yeterlidir.*

#### 🪟 Windows (Kaynak Kod / Geliştirici Betiği)
```cmd
git clone https://github.com/umutaktepe/kast.git
cd kast
install.bat
```
*(Veya doğrudan `install.bat` dosyasına çift tıklayabilir ya da PowerShell ile `powershell -ExecutionPolicy Bypass -File .\install.ps1` çalıştırabilirsiniz).*
*Bu script sanal ortamı kurar, bağımlılıkları yükler, `%USERPROFILE%\bin\kast-gui.cmd` ve `%USERPROFILE%\bin\kast.cmd` başlatıcılarını oluşturur ve Kullanıcı `PATH` ortam değişkenine otomatik ekler. Artık masaüstünden, Başlat/Çalıştır'dan veya terminalden `kast-gui` yazmanız yeterlidir.*

#### 🗑️ Programı Kaldırma (Uninstall)
- **Kurulum Sihirbazı ile Kurulduysa:** Windows Ayarlar -> Uygulamalar (Program Ekle/Kaldır) üzerinden "Kast Studio" seçilerek tek tıkla kaldırılabilir.
- **Kaynak Kod Kurulumu:**
  - Linux: `./uninstall.sh`
  - Windows: `uninstall.bat` *(veya `powershell -ExecutionPolicy Bypass -File .\uninstall.ps1`)*
*Bu işlem terminal başlatıcısını sisteminizden temizler. Ardından klasörü silebilirsiniz.*

---

## 💻 Kullanım Şekilleri

### 1. Modern Masaüstü Grafik Arayüzü (Qt6 Studio GUI) — Windows Stüdyoları İçin

Windows kullanıcıları ve seslendirme stüdyoları için tasarlanmış piksel hassasiyetindeki grafiksel arayüz:

- **Çift Tıklama ile Başlatma:** Klasördeki `kast-gui.cmd` dosyasına doğrudan çift tıklayarak açabilirsiniz (veya sağ tıklayıp masaüstüne kısayol oluşturabilirsiniz).
- **Çalıştır (Run) ile:** `Win + R` tuşlarına basıp `kast-gui` yazarak anında başlatabilirsiniz.
- **Terminalden:** `kast-gui` veya `kast --gui`

**Öne Çıkan Özellikler:**
- **Sürükle-Bırak:** `.docx` veya `.pdf` senaryo dosyasını doğrudan bulut rozetli alana sürükleyip bırakın (ayrı referans PDF gerekmez).
- **Doğrudan PDF Desteği:** PDF senaryolarda Word dönüşümüne ihtiyaç kalmadan doğrudan ve kayıpsız sayfa analizi yapar.
- **Kutulu Seçenekler:** İlk Görünme Sırası, Replik Sayısı ve Karakter Adına göre sıralama seçenekleri.
- **Çıktı Tercihleri:** Ayrı kopya (`<ad>_kast.docx`) veya orijinal belgenin sonuna ekleme.
- **Canlı Monospace Konsol:** Analiz aşamalarını gerçek zamanlı terminal günlüğünde izleme.

---

### 2. Görsel Terminal Arayüzü (TUI)

Terminalde sadece `kast` yazın:

```bash
kast
```

Karşınıza modern, tam ekran bir metin arayüzü gelecektir:
- **DOCX Senaryo Dosyası:** Senaryo dosyanızı dosya yöneticinizden sürükleyip doğrudan bu kutucuğa bırakın (tırnak işaretleri otomatik temizlenir).
- **Referans PDF (Opsiyonel):** Kesin sayfa eşleştirmesi için referans PDF dosyanızı sürükleyip bırakabilirsiniz.
- **Sıralama Seçenekleri:**
  - `İlk Görünme Sırası (Appearance)` (Varsayılan)
  - `Replik Sayısına Göre (Count)`
  - `Karakter Adına Göre (A-Z)`
- **Çıktı Seçenekleri:**
  - `[ ] Orijinal dosyanın sonuna ekle (--in-place)`
  - `[ ] Sadece kast tablosunu ayrı DOCX olarak kaydet (--standalone)`
- **İşlem Butonları:**
  - `[Kast Tablosunu Çıkar]` (Enter veya tıklama ile işlemi başlatır)
  - `[Temizle]`
  - `[Çıkış (Q)]`
- **İşlem Günlüğü ve Özeti:** Analiz tamamlandığında toplam paragraf, replik, tespit edilen karakter sayısı ve kaydedilen dosya yolu anında görüntülenir.

---

### 2. Komut Satırı (CLI) ile Hızlı Kullanım

Herhangi bir grafik arayüz açmadan hızlıca işlem yapmak için dosya adını doğrudan argüman olarak verebilirsiniz:

#### Temel Kullanım
```bash
python3 kast.py "senaryo.docx"
```
*Çıktı:* `senaryo_kast.docx` olarak dökümanın sonuna kast tablosu eklenmiş yeni bir dosya oluşturulur.

#### Karakter Sıralama Seçenekleri (`--count`, `--name`, `--sort`)
Kast tablosundaki karakterlerin listelenme sırasını belirlemek için:

- **`--count` veya `-c`:** En çok konuşan karakterden en aza doğru (başrollerden figürasyona):
  ```bash
  python3 kast.py "senaryo.docx" --count
  # veya
  python3 kast.py "senaryo.docx" --sort count
  ```
- **`--name` veya `-n`:** Karakter adına göre alfabetik (A-Z):
  ```bash
  python3 kast.py "senaryo.docx" --name
  # veya
  python3 kast.py "senaryo.docx" --sort name
  ```
- **`--sort appearance` (Varsayılan):** Karakterlerin senaryoda ilk konuşma / görünme sırasına göre:
  ```bash
  python3 kast.py "senaryo.docx"
  ```


#### Orijinal Dosyanın Üzerine Yazma (`--in-place`)
Yeni bir dosya oluşturmak yerine orijinal dökümanın sonuna eklemek için:
```bash
python3 kast.py "senaryo.docx" --in-place
```

#### Yalnızca Bağımsız Kast Tablosu Kaydetme (`--standalone`)
Orijinal senaryo metnini içermeyen, sadece kast tablosunun bulunduğu bağımsız bir Word belgesi üretmek için:
```bash
python3 kast.py "senaryo.docx" --standalone
```

#### Referans PDF ile Kesin Sayfa Tespiti (`--pdf`)
Eğer senaryonun PDF çıktısı mevcutsa, sayfa numaralarını PDF üzerinden birebir doğrulamak için:
```bash
python3 kast.py "senaryo.docx" --pdf "senaryo.pdf"
```

#### Özel Çıktı Dosya Yolu (`-o`, `--output`)
```bash
python3 kast.py "senaryo.docx" -o "cikti/ozel_kast_raporu.docx"
```

#### Yardım Menüsü
```bash
python3 kast.py --help
```

---

## 📊 Kast Tablosu Yapısı

Oluşturulan tablo dökümanın sonuna yeni bir sayfada eklenir ve Microsoft Word ile tam uyumlu **Table Grid** kenarlık stiline sahiptir:

| Sütun Adı | Genişlik | Açıklama |
| :--- | :---: | :--- |
| **Karakter** | 2.0 inç | Senaryoda tespit edilen konuşmacı adı (Örn: `PORORO`, `MC COOKIE`). |
| **Replik Sayısı** | 1.0 inç | Karakterin senaryodaki toplam replik adedi. |
| **Repliklerin Geçtiği Sayfalar** | 2.3 inç | Karakterin repliklerinin bulunduğu sayfa numaraları (Örn: `1, 2, 5, 8`). |
| **Notlar** | 1.2 inç | Dublaj yönetmeni / seslendirme teknisyeni için ayrılmış boş not alanı (Oyuncu seçimi, ses rengi vb.). |

---

## 🏗️ Mimari ve Teknik Detaylar

Kast 2.0, birbirinden bağımsız test edilebilir 4 modüler katmandan oluşur:

```
kast.py (CLI & Orkestrasyon)
   │
   ├──> src/parser.py (DubbingDocxParser)
   │       └── OpenXML sekmeleri, tire ayrıştırma, başlık ve zaman kodu filtreleme
   │
   ├──> src/paginator.py (DocumentPaginator & LayoutPaginator)
   │       └── XML sayfa kesmeleri, PDF eşleme ve saf Python mizanpaj simülatörü
   │
   ├──> src/table_writer.py (CastTableWriter & detect_document_font)
   │       └── OpenXML w:tcBorders Table Grid, dikey ortalama (vAlign), yazı tipi ve boyutu uyumu
   │
   └──> src/models.py
           └── DialogueLine, CharacterStats, CastExtractionResult
```

### 1. `src/parser.py` (DubbingDocxParser)
- Döküman paragraflarındaki XML sekmelerini (`w:tab`, `\t`) ve karakter-replik ayrımını (`KARAKTER <TAB> - Replik`) inceler.
- Tanımlayıcı başlık sözlüğünü (`FİLMİN ADI`, `ÇEVİRMEN`, `SESLENDİRME`, `KAYIT TARİHİ` vb.) kullanarak senaryo meta verilerini ayıklar.
- Tek başına duran veya satır başındaki zaman kodlarını (`00.41`, `01:23:45:12`) tespit ederek replik metninden ayırır.

### 2. `src/paginator.py` (DocumentPaginator & LayoutPaginator)
Üç aşamalı hibrit sayfa belirleme stratejisi uygular:
1. **XML Sayfa Kesmeleri:** Döküman içindeki Word tarafından işlenmiş sayfa işaretçilerini (`w:lastRenderedPageBreak` veya `w:br[@w:type="page"]`) denetler.
2. **PDF Entegrasyonu (Opsiyonel):** `--pdf` parametresi verilmişse `pdfplumber` ile PDF sayfalarını metin bazında tarayarak kesin sayfa ataması yapar.
3. **Saf Python Mizanpaj Motoru (`LayoutPaginator`):** Harici bir ofis paketi (Word, LibreOffice) bulunmayan ortamlarda dökümanın sayfa boyutlarını, kenar boşluklarını (margins), Arial/Verdana yazı tipi metriklerini, satır aralıklarını (1.5 satır katsayısı) ve Pillow font genişliklerini kullanarak satır sarma (word-wrap) ve sayfa taşma simülasyonunu %98+ doğrulukla gerçekleştirir.

### 3. `src/table_writer.py` (CastTableWriter)
- Belgenin sonuna `w:pageBreak` ekleyerek yeni bir sayfa açar ve doğrudan tablo ile başlar.
- **Yazı Tipi ve Boyutu Uyumu (`detect_document_font`):** Dökümanın paragraflarından, stillerinden veya varsayılanlarından kullanılan ana fontu (örneğin `Verdana`) ve boyutunu (örneğin `11pt`) otomatik tespit eder. Tablo öğelerini ve sütun başlıklarını bu font ailesi ve boyutuna tam uyumlu olarak üretir.
- **Hücre İçi Dikey Ortalama:** Tüm tablo hücreleri dikey olarak ortalanmıştır (`w:vAlign w:val="center"`).
- **Sayfa Düzeni ve Kenarlıklar:** Başlık satırı yalnızca tablonun başında yer alır, satırların sayfa geçişinde bölünmesi engellenmiştir (`w:cantSplit`). OpenXML düzeyinde `w:tcBorders` (Table Grid) etiketleri ile Word/OnlyOffice uyumu sağlanır.

---

## 🧪 Testler

Proje kapsamlı bir test süitine (`pytest`) sahiptir:

```bash
# Tüm testleri çalıştırmak için:
.venv/bin/pytest -v
```

### Test Kapsamı (154 Başarılı Test):
- `tests/test_models.py` — Veri modelleri, diyalog nesneleri, replik ekleme ve sayfa formatlama testleri.
- `tests/test_parser.py` — Başlık tespiti, zaman kodu ayrıştırma ve karmaşık diyalog satırları.
- `tests/test_pdf_parser.py` — Doğrudan PDF diyalog ve sayfa ayrıştırma, künye filtreleme ve standart Word tablosu üretimi.
- `tests/test_paginator.py` — Çok katmanlı sayfa motoru, Pillow font simülasyonu, XML kesmeleri ve PDF referansı.
- `tests/test_pdf_converter.py` — Headless LibreOffice ve Word COM dönüştürücüleri ve otomatik ofis algılama.
- `tests/test_table_writer.py` — Tablo oluşturma, OpenXML Table Grid kenarlıkları, dikey ortalama, dinamik font tespiti, sütun genişlikleri ve bağımsız mod.
- `tests/test_integration.py` — Uçtan uca boru hattı, CLI argümanları, `--count` kısayolu, sürükle-bırak parametreleri, birleşik dosya yönlendirici ve Pororo doğrulaması.
- `tests/test_tui.py` — Textual TUI widget montajı, buton aksiyonları, hata yakalama ve uçtan uca terminal arayüz testleri.
- `tests/test_gui.py` — PySide6 Qt6 masaüstü GUI, StudioTheme koyu paleti, DropZoneWidget sürükle-bırak, ExtractionWorker arka plan iş parçacığı ve duyarlı pencere testleri.
- `tests/test_packaging.py` — PyInstaller kast.spec mimarisi, izole GUI başlatıcı (run_gui.py) ve 7 çözünürlüklü stüdyo ikonu üretimi (generate_icon.py).
- `tests/test_inno_setup.py` — Inno Setup kurulum yapılandırması (installer.iss), Pascal script ile Word/LibreOffice tespiti ve sessiz kurulum fallback'i.
- `tests/test_ci_workflow.py` — GitHub Actions Windows CI/CD boru hattı (release-windows.yml), yapı adımları, izinler ve yayın otomasyonu.


---

## 📄 Lisans

Bu proje açık kaynaklıdır ve dublaj çeviri süreçlerini kolaylaştırmak amacıyla geliştirilmiştir.
