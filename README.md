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

## ⚡ Hızlı Kurulum (Tek Komutla)

Depoyu klonladıktan sonra işletim sisteminize uygun kurulum scriptini çalıştırarak programı sisteminize entegre edebilirsiniz:

### 🐧 Linux (Bash)
```bash
git clone https://github.com/umutaktepe/kast.git
cd kast
chmod +x install.sh && ./install.sh
```
*Bu script sanal ortamı kurar, bağımlılıkları yükler ve `~/.local/bin/kast` sembolik bağını oluşturur. Artık terminalinizin herhangi bir yerinden sadece `kast` yazmanız yeterlidir.*

### 🪟 Windows (PowerShell)
```powershell
git clone https://github.com/umutaktepe/kast.git
cd kast
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
*Bu script sanal ortamı kurar, bağımlılıkları yükler, `%USERPROFILE%\bin\kast.cmd` başlatıcısını oluşturur ve Kullanıcı `PATH` ortam değişkenine otomatik ekler. Artık CMD veya PowerShell'de sadece `kast` yazmanız yeterlidir.*

---

## 💻 Kullanım Şekilleri

### 1. Görsel Terminal Arayüzü (TUI) — Önerilen

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

### Test Kapsamı (61/61 Başarılı Test):
- `tests/test_models.py` — Veri modelleri, replik ekleme ve sayfa formatlama testleri.
- `tests/test_parser.py` — Başlık tespiti, zaman kodu ayrıştırma ve karmaşık diyalog satırları.
- `tests/test_paginator.py` — Çok katmanlı sayfa motoru, Pillow font simülasyonu, XML kesmeleri ve PDF referansı.
- `tests/test_table_writer.py` — Tablo oluşturma, OpenXML kenarlıkları, dikey ortalama, dinamik font tespiti, sütun genişlikleri ve bağımsız belge modu.
- `tests/test_integration.py` — Uçtan uca boru hattı, CLI argümanları, `--count` kısayolu, sürükle-bırak parametreleri, TUI dispatch ve Pororo örnek döküman doğrulaması.
- `tests/test_tui.py` — Textual TUI widget montajı, buton aksiyonları, hata yakalama ve uçtan uca arayüz testleri.


---

## 📄 Lisans

Bu proje açık kaynaklıdır ve dublaj çeviri süreçlerini kolaylaştırmak amacıyla geliştirilmiştir.
