---
title: "Model: CharacterStats"
type: core-model
domain: core-models
tags:
  - model
  - statistics
  - character
  - schema
---

# Model: CharacterStats

`CharacterStats`, senaryoda konuşan tekil bir karaktere ait tüm istatistiklerin (toplam replik sayısı, ilk görünme sırası, repliklerin geçtiği sayfalar kümesi ve notlar) toplandığı veri sınıfıdır (`src/models.py`).

## Şema Tanımı

```python
@dataclass
class CharacterStats:
    name: str
    first_seen_order: int
    line_count: int = 0
    pages: Set[int] = field(default_factory=set)
    notes: str = ""

    def add_line(self, page: int) -> None:
        self.line_count += 1
        self.pages.add(page)

    @property
    def formatted_pages(self) -> str:
        return ", ".join(str(p) for p in sorted(self.pages))
```

## Alanlar ve Metotlar

| Alan / Metot | Tip | Açıklama |
| :--- | :--- | :--- |
| `name` | `str` | Karakterin senaryodaki adı. |
| `first_seen_order` | `int` | Karakterin senaryoda ilk kez replik söylediği sıra (1 tabanlı sayaç). Varsayılan sıralama (`appearance`) için anahtar görevi görür. |
| `line_count` | `int` | Karakterin senaryodaki toplam replik sayısı. |
| `pages` | `Set[int]` | Karakterin konuştuğu benzersiz sayfa numaralarının kümesi. |
| `notes` | `str` | Dublaj yönetmeni / stüdyo için boş bırakılan not alanı. |
| `add_line(page)` | `method` | Karakterin replik sayısını 1 artırır ve sayfa numarasını `pages` kümesine ekler. |
| `formatted_pages` | `property` | Sayfaları küçükten büyüğe sıralı ve virgülle ayrılmış bir metin (`"1, 2, 5, 8"`) olarak döndürür. |

## Sıralama Davranışları

[[hybrid-cli-dispatcher]] veya [[terminal-user-interface]] üzerinden seçilen sıralama mantığı doğrudan `CharacterStats` alanlarını temel alır:
- **`appearance` (Varsayılan):** `first_seen_order` alanına göre küçükten büyüğe.
- **`count` (`--count`, `-c`):** `line_count` alanına göre büyükten küçüğe (en çok konuşandan en aza).
- **`name` (`--name`, `-n`):** `name` alanına göre alfabetik (A-Z).

## İlgili Sayfalar

- [[dialogue-line]]
- [[cast-extraction-result]]
- [[cast-table-writer]]
- [[hybrid-cli-dispatcher]]
