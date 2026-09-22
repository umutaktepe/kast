---
title: "Model: ParsedParagraph"
type: core-model
domain: core-models
tags:
  - model
  - parser
  - intermediate-representation
  - schema
---

# Model: ParsedParagraph

`ParsedParagraph`, Word belgesindeki her bir XML paragrafının ayrıştırıcı ([[dubbing-docx-parser]]) tarafından ilk tarama sırasında dönüştürüldüğü ara temsil (intermediate representation) modelidir (`src/parser.py`).

Bu model hem diyalogları hem de diyalog olmayan paragrafları (boş satırlar, başlıklar, zaman kodları, açıklamalar) mizanpaj ve sayfalama motoruna ([[document-paginator]]) eksiksiz aktarmak için kullanılır.

## Şema Tanımı

```python
@dataclass
class ParsedParagraph:
    index: int
    text: str
    speaker: Optional[str] = None
    dialogue: Optional[str] = None
    timecode: Optional[str] = None
    is_metadata: bool = False
    is_timecode: bool = False
    is_empty: bool = False
    meta_key: Optional[str] = None
    meta_value: Optional[str] = None
    page: int = 1

    def to_dialogue_line(self) -> Optional[DialogueLine]:
        if self.speaker and self.dialogue:
            return DialogueLine(
                speaker=self.speaker,
                text=self.dialogue,
                timecode=self.timecode,
                page=self.page,
                paragraph_index=self.index,
            )
        return None
```

## Alan Açıklamaları

| Alan Adı | Tip | Varsayılan | Açıklama |
| :--- | :--- | :--- | :--- |
| `index` | `int` | *Zorunlu* | Paragrafın dökümandaki sırası (`doc.paragraphs` indeksi). |
| `text` | `str` | *Zorunlu* | Paragrafın orijinal ham metni. |
| `speaker` | `Optional[str]` | `None` | Tespit edilmişse konuşmacı adı. |
| `dialogue` | `Optional[str]` | `None` | Tespit edilmişse replik metni. |
| `timecode` | `Optional[str]` | `None` | Varsa ilişkili zaman kodu. |
| `is_metadata` | `bool` | `False` | Paragraf bir proje künyesi (`FİLMİN ADI` vb.) ise `True`. |
| `is_timecode` | `bool` | `False` | Paragraf bağımsız bir zaman kodu satırı ise `True`. |
| `is_empty` | `bool` | `False` | Boş satır ise `True` (mizanpaj motorunun satır boşluğunu hesaplaması için kritiktir). |
| `meta_key` | `Optional[str]` | `None` | Meta verinin anahtarı (Örn: `FİLMİN ADI`). |
| `meta_value` | `Optional[str]` | `None` | Meta verinin değeri. |
| `page` | `int` | `1` | Paragrafın hesaplanan veya eşleştirilen sayfa numarası. |

## Dönüşüm

Eğer `speaker` ve `dialogue` alanları doluysa, `to_dialogue_line()` metodu çağrılarak güvenli şekilde atomik [[dialogue-line]] modeline dönüştürülür.

## İlgili Sayfalar

- [[dialogue-line]]
- [[dubbing-docx-parser]]
- [[document-paginator]]
- [[pure-python-layout-paginator]]
