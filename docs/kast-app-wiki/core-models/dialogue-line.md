---
title: "Model: DialogueLine"
type: core-model
domain: core-models
tags:
  - model
  - dialogue
  - schema
---

# Model: DialogueLine

`DialogueLine`, bir dublaj senaryosundaki tekil, doğrulanmış ve ayrıştırılmış bir diyalog repliğini temsil eden temel veri modelidir (`src/models.py`).

Ayrıştırma aşamasında [[dubbing-docx-parser]] tarafından üretilir veya [[parsed-paragraph]] nesnesinin `to_dialogue_line()` metodu ile dönüştürülür.

## Şema Tanımı

```python
@dataclass
class DialogueLine:
    speaker: str
    text: str
    timecode: Optional[str] = None
    page: int = 1
    paragraph_index: int = 0
```

## Alan Açıklamaları

| Alan Adı | Tip | Varsayılan | Açıklama |
| :--- | :--- | :--- | :--- |
| `speaker` | `str` | *Zorunlu* | Repliği söyleyen karakterin temizlenmiş adı (Örn: `JACKIE`, `PORORO`). Baş ve sondaki noktalama işaretleri temizlenmiştir. |
| `text` | `str` | *Zorunlu* | Replik metni. Başlangıçtaki tire ve boşlukları içerir (Örn: `- Merhaba dünya!`). |
| `timecode` | `Optional[str]` | `None` | Varsa replikten hemen önce veya aynı blokta yer alan süre kodu (`00.41`, `01.23.45`). |
| `page` | `int` | `1` | Bu repliğin geçtiği kesin sayfa numarası. [[document-paginator]] veya [[pdf-matching-engine]] tarafından atanır. |
| `paragraph_index` | `int` | `0` | Paragrafın orijinal Word dökümanındaki sıfır tabanlı indeks numarası. |

## Yaşam Döngüsü ve İlişkiler

1. [[dubbing-docx-parser]], Word dökümanını okuyup diyalog satırını tespit eder.
2. Varsa en son görülen zaman kodu [[timecode-detection]] üzerinden `timecode` alanına işlenir.
3. [[document-paginator]], repliğin senaryo içerisindeki kesin sayfa numarasını tespit ederek `page` alanını günceller.
4. Boru hattı orkestratörü ([[hybrid-cli-dispatcher]]), repliği ilgili konuşmacının [[character-stats]] nesnesine `add_line(page)` çağrısıyla ekler.

## İlgili Sayfalar

- [[character-stats]]
- [[parsed-paragraph]]
- [[dubbing-docx-parser]]
- [[document-paginator]]
- [[adr-001-openxml-tab-based-parsing]]
