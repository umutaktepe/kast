---
title: "Modül: DubbingPdfParser"
type: module
domain: parsing-engine
tags:
  - parser
  - engine
  - pdf
  - text-processing
---

# Modül: DubbingPdfParser

`DubbingPdfParser`, stüdyolardan gelen PDF formatındaki dublaj senaryolarını doğrudan sayfa sayfa okuyan, diyalog satırlarını ve karakter istatistiklerini DOCX dönüşümüne ihtiyaç duymadan %100 yerel sayfa doğruluğuyla çıkaran ayrıştırma motorudur (`src/pdf_parser.py`).

## Temel Sorumluluklar

1. **Doğrudan PDF Okuma:** `pdfplumber` ile PDF sayfalarını sırayla okur.
2. **Yerel Sayfa Hassasiyeti:** Her repliğin hangi PDF sayfasında yer aldığını doğrudan `page_idx` üzerinden kaydeder.
3. **Zaman Kodu ve Boşluk Filtreleme:** [[timecode-detection]] desenine uyan satırları ve sayfa numarası tekil rakamlarını atlar.
4. **Künye ve Başlık Filtreleme:** [[metadata-filtering]] anahtarları ve Türkçe büyük harf kuralı ile proje künyelerinin konuşmacı sanılmasını engeller.
5. **Diyalog Ayrıştırma:** Hem sekme-tire (`SPEAKER \t - Replik`) hem de tire (`SPEAKER - Replik`) modellerini destekler.
6. **İlerleme Bildirimi:** `progress_callback(page_idx, total_pages, message)` desteği ile GUI ve TUI arayüzlerine canlı tarama durumu aktarır.

## Temel Metotlar

### `parse_pdf(pdf_path: str, sort_by: str = "appearance", progress_callback=None) -> CastExtractionResult`
PDF dökümanını tarayarak karakterleri, replik sayılarını ve sayfa listelerini toplayan [[cast-extraction-result]] nesnesi üretir. `sort_by` parametresi `"appearance"`, `"count"` veya `"name"` değerlerini alabilir.

### `process_pdf_document(pdf_path: str, output_path: Optional[str] = None, sort_by: str = "appearance", progress_callback=None) -> Tuple[str, CastExtractionResult]`
PDF senaryosunu işler ve [[cast-table-writer]] kullanarak doğrudan bağımsız bir Word (`.docx`) kast tablosu dökümanı üretip kaydeder.

## İlgili Sayfalar

- [[dubbing-docx-parser]]
- [[metadata-filtering]]
- [[timecode-detection]]
- [[cast-extraction-result]]
- [[character-stats]]
- [[cast-table-writer]]
