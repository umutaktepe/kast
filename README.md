# Kast 2.0 — Dublaj Çevirisi Kast Çıkarma Sistemi

**Kast 2.0**, dublaj çevirmenleri, seslendirme yönetmenleri ve stüdyolar için geliştirilmiş modern bir kast tablosu çıkarma ve döküman zenginleştirme aracıdır.

Microsoft Word (`.docx`) formatındaki dublaj çeviri senaryolarını doğrudan analiz eder; karakterlerin repliklerini, replik sayılarını ve senaryodaki sayfa numaralarını yüksek hassasiyetle tespit ederek profesyonel bir **Kast Tablosu** oluşturur ve dökümanın sonuna yeni bir sayfa olarak otomatik ekler.

---

## 🚀 Kast 2.0 ile Gelen Yenilikler

Geleneksel kast çıkarma araçları veya manuel yöntemlere kıyasla Kast 2.0 şu temel avantajları sunar:

1. **DOCX Üzerinden Doğrudan Çalışma:**
   - Metinleri kopyalayıp düz metne (`.txt`) çevirmenize veya Word biçimlendirmelerini bozmanıza gerek yoktur. Dökümanı doğrudan olduğu gibi işler.
2. **Başlık ve Meta Veri Filtreleme (Başlık Silmeye Son!):**
   - Senaryonun başında yer alan `FİLMİN ADI`, `ÇEVİRMEN`, `KAYIT TARİHİ`, `SESLENDİRME STÜDYOSU` gibi proje başlıklarını ve `00.41`, `01.12.05` gibi süre kodlarını akıllıca ayırt eder.
   - Başlıkların veya zaman kodlarının yanlışlıkla karaktere dönüşmesi engellenir; senaryo başındaki künyeyi elle silme zorunluluğu tamamen ortadan kalkar.
3. **Çok Katmanlı Otomatik Sayfa Tespiti:**
   - Sayfa numaralarını bulmak için Word'de tek tek elle arama yapmaya veya PDF'e dönüştürmeye gerek kalmaz.
   - Belgedeki OpenXML sayfa sonlarını, isteğe bağlı referans PDF eşleştirmesini ve saf Python mizanpaj simülatörünü bir arada kullanarak repliklerin hangi sayfalarda geçtiğini otomatik tespit eder.
4. **Otomatik Tablo Entegrasyonu ve Güvenli Kayıt:**
   - Çıkarılan kast tablosu Word ile %100 uyumlu tam kenarlıklı (Table Grid) biçimde dökümanın en sonuna yeni bir sayfa olarak eklenir.
   - Orijinal dökümanın güvenliği için varsayılan olarak `<dosya_adi>_kast.docx` adıyla yeni bir kopya oluşturulur (istenirse `--in-place` ile doğrudan orijinal dosyaya da yazılabilir).

---

## 📋 Gereksinimler ve Kurulum

### Sistem Gereksinimleri
- **Python:** 3.10 veya üzeri
- İşletim Sistemi: Linux, macOS veya Windows

### Bağımlılıklar
- `python-docx` (>= 1.0.0) — Word dökümanlarını ayrıştırma ve tablo yazma
- `Pillow` (>= 10.0.0) — Mizanpaj motoru için yazı tipi ve piksel genişlik hesaplamaları
- `pdfplumber` (>= 0.10.0, opsiyonel) — Referans PDF sayfa eşleştirmesi için
- `pytest` (>= 8.0.0, geliştirici) — Birim ve entegrasyon testleri için

### Kurulum Adımları

1. Depoyu klonlayın veya indirin:
   ```bash
   git clone https://github.com/kullanici/Kast.git
   cd Kast
   ```

2. Sanal ortam (virtualenv) oluşturun ve etkinleştirin:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   # veya Windows için: .venv\Scripts\activate
   ```

3. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Kullanım Şekilleri

### 1. Terminalden Sürükle-Bırak Yöntemi (En Kolay)
Herhangi bir komut satırı argümanı ezberlemeden programı başlatabilirsiniz:

```bash
python3 kast.py
```

Terminalde şu karşılama ekranı görüntülenir:
```text
============================================================
 DUBLAJ ÇEVİRİSİ KAST ÇIKARMA PROGRAMI (Kast 2.0)
============================================================
Lütfen çeviri DOCX dosyasını buraya sürükleyip bırakın ve Enter'a basın:
> 
```
Dosya yöneticinizden (Finder, Nautilus, Windows Explorer) `.docx` dosyasını terminal penceresine sürükleyip bırakın ve `Enter` tuşuna basın. Program dökümanı işleyip `<dosya_adi>_kast.docx` dosyasını aynı klasörde oluşturacaktır.

---

### 2. Komut Satırı (CLI) ile Kullanım

#### Temel Kullanım
```bash
python3 kast.py "senaryo.docx"
```
*Çıktı:* `senaryo_kast.docx` olarak dökümanın sonuna kast tablosu eklenmiş yeni bir dosya oluşturulur.

#### Karakter Sıralama Seçenekleri (`--sort`)
Kast tablosundaki karakterlerin listelenme sırasını `--sort` parametresiyle belirleyebilirsiniz:

- **`appearance` (Varsayılan):** Karakterlerin senaryoda ilk konuşma / görünme sırasına göre.
  ```bash
  python3 kast.py "senaryo.docx" --sort appearance
  ```
- **`count`:** En çok konuşan karakterden en aza doğru (başrollerden figürasyona):
  ```bash
  python3 kast.py "senaryo.docx" --sort count
  ```
- **`name`:** Karakter adına göre alfabetik (A-Z):
  ```bash
  python3 kast.py "senaryo.docx" --sort name
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
| **Karakter** | 1.8 inç | Senaryoda tespit edilen konuşmacı adı (Örn: `PORORO`, `MC COOKIE`). |
| **Replik Sayısı** | 1.1 inç | Karakterin senaryodaki toplam replik adedi. |
| **Repliklerin Geçtiği Sayfalar** | 2.3 inç | Karakterin repliklerinin bulunduğu sayfa numaraları (Örn: `1, 2, 5, 8`). |
| **Notlar** | 1.3 inç | Dublaj yönetmeni / seslendirme teknisyeni için ayrılmış boş not alanı (Oyuncu seçimi, ses rengi vb.). |

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
   ├──> src/table_writer.py (CastTableWriter)
   │       └── OpenXML w:tcBorders Table Grid, sayfa sonu, sütun genişliği ve Arial formatı
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
3. **Saf Python Mizanpaj Motoru (`LayoutPaginator`):** Harici bir ofis paketi (Word, LibreOffice) bulunmayan ortamlarda dökümanın sayfa boyutlarını, kenar boşluklarını (margins), Arial 11pt yazı tipi metriklerini, satır aralıklarını (1.5 satır katsayısı) ve Pillow font genişliklerini kullanarak satır sarma (word-wrap) ve sayfa taşma simülasyonunu %98+ doğrulukla gerçekleştirir.

### 3. `src/table_writer.py` (CastTableWriter)
- Belgenin sonuna `w:pageBreak` ekleyerek yeni bir sayfa açar.
- 4 sütunlu tabloyu oluşturur; Word'ün varsayılan kenarlık kaybolma sorununu önlemek için OpenXML düzeyinde `w:tcBorders` (Table Grid) etiketlerini hücre bazında uygular.
- Sütun genişliklerini sabitler ve başlıkları kalın (bold) Arial stiliyle biçimlendirir.

---

## 🧪 Testler

Proje kapsamlı bir test süitine (`pytest`) sahiptir:

```bash
# Tüm testleri çalıştırmak için:
.venv/bin/pytest -v
```

### Test Kapsamı (50/50 Başarılı Test):
- `tests/test_models.py` — Veri modelleri, replik ekleme ve sayfa formatlama testleri.
- `tests/test_parser.py` — Başlık tespiti, zaman kodu ayrıştırma ve karmaşık diyalog satırları.
- `tests/test_paginator.py` — Çok katmanlı sayfa motoru, Pillow font simülasyonu, XML kesmeleri ve PDF referansı.
- `tests/test_table_writer.py` — Tablo oluşturma, OpenXML kenarlıkları, sütun genişlikleri ve bağımsız belge modu.
- `tests/test_integration.py` — Uçtan uca boru hattı, CLI argümanları, tırnaklı sürükle-bırak yolu ve Pororo örnek döküman doğrulaması.

---

## 📄 Lisans

Bu proje açık kaynaklıdır ve dublaj çeviri süreçlerini kolaylaştırmak amacıyla geliştirilmiştir.
