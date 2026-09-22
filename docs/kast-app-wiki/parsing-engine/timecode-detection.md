---
title: "Özellik: Zaman Kodu Tespiti (Timecode Detection)"
type: feature-spec
domain: parsing-engine
tags:
  - timecode
  - regex
  - text-processing
---

# Özellik: Zaman Kodu Tespiti (Timecode Detection)

Dublaj senaryolarında konuşma bloklarının veya sahnelerin başlangıcında video zaman kodları (TC / Timecode) yer alır. Bu zaman kodları kimi zaman ayrı bir paragraf olarak, kimi zaman ise bir sonraki repliğin hemen üstünde bulunur (`src/parser.py`).

Zaman kodu tespiti motoru, bu süre işaretçilerini yakalayarak diyalog metinlerinden ve karakter adlarından tamamen izole eder.

## Düzenli İfade (Regex) Deseni

```python
TIMECODE_REGEX = re.compile(r"^\d{2}[\.:]\d{2}(?:[\.:]\d{2}(?:[\.:]\d{2})?)?$")
```

## Desteklenen Zaman Kodu Formatları

Filtre motoru stüdyolarda sıkça karşılaşılan şu varyasyonları destekler:

- `00.41` veya `00:41` (Dakika . Saniye)
- `01.59.10` veya `01:59:10` (Saat . Dakika . Saniye)
- `01.23.45.12` veya `01:23:45:12` (Saat : Dakika : Saniye : Kare/Frame)

## Davranış Mantığı

1. Paragrafın baş ve sonundaki boşluklar temizlenir (`strip()`).
2. Metin `TIMECODE_REGEX` desenine uyuyorsa:
   - Paragraf `is_timecode=True` olarak etiketlenir.
   - `DubbingDocxParser` içindeki `current_timecode` durum değişkeni bu değerle güncellenir.
   - Bu satır asla diyalog veya karakter olarak sayılmaz.
3. Bir sonraki diyalog satırı geldiğinde, `current_timecode` değeri ilgili [[dialogue-line]] nesnesine iliştirilir.
4. [[pure-python-layout-paginator]], zaman kodu paragraflarını tek satırlık standart paragraf yüksekliğiyle hesaba katarak sayfa taşmalarının doğruluğunu korur.

## İlgili Sayfalar

- [[dubbing-docx-parser]]
- [[dialogue-line]]
- [[parsed-paragraph]]
- [[adr-001-openxml-tab-based-parsing]]
