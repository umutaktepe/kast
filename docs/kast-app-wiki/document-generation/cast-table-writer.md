---
title: "Modül: CastTableWriter (Kast Tablosu Oluşturucu)"
type: module
domain: document-generation
tags:
  - docx
  - table-writer
  - openxml
  - formatting
---

# Modül: CastTableWriter (Kast Tablosu Oluşturucu)

`CastTableWriter`, analiz edilen dublaj istatistiklerini ([[cast-extraction-result]]) Microsoft Word (`.docx`) belgesi içerisine profesyonel ve biçimlendirilmiş bir kast tablosu olarak yazan bileşendir (`src/table_writer.py`).

Tasarım standartları [[adr-003-native-table-grid-generation]] belgesinde belirlenmiştir.

## Tablo Sütun Yapısı ve Boyutları

Tablo Word ile tam uyumlu 4 sütundan oluşur:

| Sütun No | Sütun Başlığı | Genişlik | Hizalama | Açıklama |
| :---: | :--- | :---: | :---: | :--- |
| 1 | **Karakter** | 2.0 inç | Sola / Dikey Orta | Karakterin adı. |
| 2 | **Replik Sayısı** | 1.0 inç | Sola / Dikey Orta | Toplam replik adedi. |
| 3 | **Repliklerin Geçtiği Sayfalar** | 2.3 inç | Sola / Dikey Orta | Virgülle ayrılmış sayfa listesi (`1, 2, 5`). |
| 4 | **Notlar** | 1.2 inç | Sola / Dikey Orta | Ses rengi veya oyuncu seçimi için boş not alanı. |

## Temel Metotlar

### `append_cast_table(doc: Document, result: CastExtractionResult, add_page_break: bool = True) -> Document`
1. **Tipografi Uyumu:** [[document-font-detection]] ile dökümanın ana fontunu ve puntosunu tespit eder (`detect_document_font`).
2. **Sayfa Kesmesi:** İstenirse tablonun öncesine yeni sayfa kesmesi (`doc.add_page_break()`) ekler.
3. **Tablo Oluşturma:** `doc.add_table(rows=1, cols=4)` çağrılır ve `col_widths` tanımları atanır.
4. **Başlık Satırı:**
   - Kalın yazı tipi (`bold = True`), tespit edilen font ve punto uygulanır.
   - Paragraf girintileri sıfırlanır (`left_indent = 0`).
   - `w:cantSplit` özelliği eklenir.
5. **Veri Satırları:** Her bir [[character-stats]] nesnesi için yeni bir satır açılır; kenarlıklar ([[openxml-styling]]) ve dikey hizalama atanır.

### `save_result(doc: Document, output_path: str) -> str`
Oluşturulan veya güncellenen Word belgesini hedef dosya yoluna kaydeder.

## Çalışma Modları

- **Eklemeli Mod (Append / Varsayılan):** Orijinal senaryo metninin en sonuna yeni bir sayfa açılarak tablo eklenir.
- **Bağımsız Mod (`--standalone`):** Boş bir `Document()` nesnesi oluşturularak yalnızca kast tablosunun yer aldığı bağımsız bir rapor üretilir.

## İlgili Sayfalar

- [[openxml-styling]]
- [[document-font-detection]]
- [[cast-extraction-result]]
- [[character-stats]]
- [[adr-003-native-table-grid-generation]]
