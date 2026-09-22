---
title: "Modül: DubbingDocxParser"
type: module
domain: parsing-engine
tags:
  - parser
  - engine
  - docx
  - text-processing
---

# Modül: DubbingDocxParser

`DubbingDocxParser`, Microsoft Word (`.docx`) formatındaki dublaj çeviri senaryolarını okuyan, paragrafları hiyerarşik olarak analiz eden ve bunları yapılandırılmış veri modellerine dönüştüren ana ayrıştırma motorudur (`src/parser.py`).

Tasarım felsefesi ve mimari gerekçesi [[adr-001-openxml-tab-based-parsing]] belgesinde açıklanmıştır.

## Temel Sorumluluklar

1. **Paragraf İterasyonu:** Word dökümanındaki her paragrafı sırayla dolaşır.
2. **Boşluk Yönetimi:** Boş paragrafları `is_empty=True` olarak etiketler; bu sayede [[pure-python-layout-paginator]] mizanpaj boşluklarını hesaba katabilir.
3. **Zaman Kodu Tespiti:** [[timecode-detection]] kuralına uyan satırları yakalar ve bir sonraki replik için aktif zaman kodu olarak saklar.
4. **Başlık ve Künye Filtreleme:** [[metadata-filtering]] kütüphanesini kullanarak döküman başındaki proje bilgilerini ayıklar ve karaktere dönüşmelerini engeller.
5. **Diyalog Ayrıştırma:** Standart sekme ve tire (`SPEAKER \t - Dialogue`) yapısını çözerek konuşmacı adı ve replik metnini ayırır.

## Temel Metotlar

### `parse_dialogue_line(text: str) -> Tuple[bool, Optional[str], Optional[str]]`
Metni sekme karakterinden (`\t`) böler. Sağ taraf tire (`-`, `–`, `—`) ile başlıyorsa sol tarafı karakter adı, sağ tarafı replik olarak döndürür:
```python
parts = text_clean.split("\t", 1)
if len(parts) == 2:
    speaker, dialogue = parts[0].strip(), parts[1].strip()
    if dialogue.startswith(("-", "–", "—")):
        speaker_clean = speaker.strip(" \t:.-")
        return True, speaker_clean, dialogue
```

### `parse_document_paragraphs(doc: Document) -> List[ParsedParagraph]`
Word belgesindeki tüm paragrafları tarar ve her biri için bir [[parsed-paragraph]] nesnesi üretir.

### `parse_paragraphs(docx_path_or_doc) -> Tuple[Dict[str, str], List[DialogueLine]]`
Dökümanı ayrıştırıp doğrudan metadata sözlüğü ve [[dialogue-line]] listesi olarak teslim eden yüksek seviyeli kolaylık fonksiyonudur.

## İlgili Sayfalar

- [[metadata-filtering]]
- [[timecode-detection]]
- [[parsed-paragraph]]
- [[dialogue-line]]
- [[adr-001-openxml-tab-based-parsing]]
