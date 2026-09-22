---
title: "Model: CastExtractionResult"
type: core-model
domain: core-models
tags:
  - model
  - aggregate
  - cast-result
  - schema
---

# Model: CastExtractionResult

`CastExtractionResult`, bir senaryonun analizi tamamlandığında üretilen, tablonun oluşturulması ve arayüze özet sunulması için gerekli tüm karakter ve meta verileri barındıran üst düzey toplu (aggregate) veri modelidir (`src/models.py`).

## Şema Tanımı

```python
@dataclass
class CastExtractionResult:
    characters: List[CharacterStats]
    metadata: Dict[str, str] = field(default_factory=dict)
    total_lines: int = 0
    total_pages: int = 0
```

## Alan Açıklamaları

| Alan Adı | Tip | Varsayılan | Açıklama |
| :--- | :--- | :--- | :--- |
| `characters` | `List[CharacterStats]` | *Zorunlu* | İstenen sıralama kuralına göre dizilmiş [[character-stats]] nesnelerinin listesi. |
| `metadata` | `Dict[str, str]` | `{}` | Senaryo başından çıkarılan künye bilgileri (`FİLMİN ADI`, `ÇEVİRMEN` vb.). |
| `total_lines` | `int` | `0` | Senaryoda tespit edilen toplam replik adedi. |
| `total_pages` | `int` | `0` | Senaryonun toplam sayfa sayısı. |

## Kullanıldığı Alanlar

1. **Tablo Yazma:** [[cast-table-writer]] modülü bu nesneyi alarak her karakter için bir tablo satırı oluşturur.
2. **Terminal Kullanıcı Arayüzü:** [[terminal-user-interface]] modülü işlem bittiğinde `total_lines`, `total_pages` ve `len(characters)` değerlerini ekrandaki özet bilgi paneline basar.
3. **Komut Satırı Çıktısı:** [[hybrid-cli-dispatcher]], işlem istatistiklerini terminale yazdırırken bu modeli okur.

## İlgili Sayfalar

- [[character-stats]]
- [[dialogue-line]]
- [[cast-table-writer]]
- [[terminal-user-interface]]
- [[adr-003-native-table-grid-generation]]
