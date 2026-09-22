---
title: "Özellik: Otomatik Doküman Fontu ve Boyutu Tespiti"
type: feature-spec
domain: document-generation
tags:
  - font-detection
  - typography
  - docx-styles
---

# Özellik: Otomatik Doküman Fontu ve Boyutu Tespiti

Kast 2.0'ın öne çıkan estetik özelliklerinden biri, senaryoya eklenen kast tablosunun belgenin orijinal yazı tipi ve boyutlarıyla birebir uyumlu olmasını sağlayan dinamik tipografi tespit motorudur (`src/table_writer.py` ve `src/paginator.py`).

Tasarım felsefesi [[adr-003-native-table-grid-generation]] belgesinde açıklanmıştır.

## Tespit Algoritması (`detect_document_font`)

Bir Word belgesinde font tanımları paragraf seviyesinde, metin parçacığı (`run`) seviyesinde, stil seviyesinde veya belgenin varsayılanlarında (`docDefaults`) gizlenmiş olabilir. Kast, istatistiksel frekans analizi (`collections.Counter`) kullanarak ağırlıklı baskın fontu tespit eder:

```python
font_counter: Counter[str] = Counter()
size_counter: Counter[float] = Counter()
```

### Tarama Kademeleri

1. **Paragraf ve Run Seviyesi:**
   Dökümandaki paragrafların içindeki her bir `run` elemanı taranır. Metin uzunluğu ağırlık katsayısı olarak kullanılır (`font_counter[fname] += r_len`). Font adı `rPr/w:rFonts` (`ascii`, `hAnsi`, `cs`) ve boyutu `rPr/w:sz` (yarım punto cinsinden) etiketlerinden okunur.
2. **Paragraf Stili Seviyesi:**
   Paragrafın uygulandığı stilin fontu ve boyutu ağırlıklandırmaya katılır.
3. **`Normal` Stil Denetimi:**
   `doc.styles['Normal']` font adı ve boyutu incelenir.
4. **`docDefaults` Denetimi:**
   Word stillerinin kökündeki varsayılan font (`w:rPrDefault/w:rPr/w:rFonts`) incelenir.

### Sonuç Belirleme

```python
chosen_font = font_counter.most_common(1)[0][0] if font_counter else "Arial"
chosen_size = size_counter.most_common(1)[0][0] if size_counter else 10.0
```

En çok karakter barındıran font ailesi ve punto seçilir. Böylece senaryo ister 11pt Verdana, ister 10.5pt Arial, ister 12pt Times New Roman olsun; oluşturulan tablo başlığı ve hücreleri tam olarak aynı tipografiyle üretilir.

## İlgili Sayfalar

- [[cast-table-writer]]
- [[openxml-styling]]
- [[pure-python-layout-paginator]]
- [[adr-003-native-table-grid-generation]]
