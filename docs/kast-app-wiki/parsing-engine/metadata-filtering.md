---
title: "Özellik: Başlık ve Meta Veri Filtreleme"
type: feature-spec
domain: parsing-engine
tags:
  - metadata
  - filtering
  - turkish-language
  - text-processing
---

# Özellik: Başlık ve Meta Veri Filtreleme

Başlık ve meta veri filtreleme özelliği, dublaj çeviri senaryolarının başında yer alan künye, stüdyo ve çevirmen bilgilerinin yanlışlıkla konuşan bir karaktere dönüşmesini kesin olarak engelleyen filtreleme mekanizmasıdır (`src/parser.py`).

Kullanıcıların senaryoyu işlemeden önce başındaki künyeyi elle silme zorunluluğunu tamamen ortadan kaldırır.

## Bilinen Meta Veri Anahtarları (`KNOWN_METADATA_KEYS`)

Filtreleme motoru aşağıdaki standart dublaj ve çeviri başlıklarını tanır:

- `FİLMİN ADI`, `FİLM ADI`, `TITLE`
- `DİZİ ADI`, `DİZİ`
- `ÇEVİRMEN`, `ÇEVİREN`, `TRANSLATOR`
- `SEZON`, `BÖLÜM`, `BÖLÜM ADI`
- `KAYIT`, `STÜDYO`, `TARİH`
- `YÖNETMEN`, `SESLENDİRME YÖNETMENİ`

## Türkçe Karakter Normalizasyonu (`turkish_upper`)

Python'un varsayılan `.upper()` fonksiyonu Türkçe küçük `i` harfini İngilizce `I` harfine çevirir; bu durum `FİLMİN ADI` gibi başlıkların `FILMIN ADI` ile eşleşememesine ve başlık filtresinin delinmesine neden olabilir.

Bu sorunu çözmek için özel karakter tablosu dönüşümü kullanılır:
```python
def turkish_upper(text: str) -> str:
    """Convert text to uppercase with Turkish character handling (i -> İ, ı -> I)."""
    return text.translate({ord("i"): "İ", ord("ı"): "I"}).upper()
```

## Eşleme Algoritması

1. Paragraf sekme (`\t`) içeriyorsa ikiye ayrılır (`key`, `val`).
2. `key` metni hem standart hem de Türkçe büyük harf türevleriyle varyant kümesine (`key_variants`) dönüştürülür.
3. Varyantlardan herhangi biri `KNOWN_METADATA_KEYS` içindeki bir anahtarla veya o anahtarla başlayan bir sözcükle örtüşüyorsa satır doğrudan meta veri olarak kabul edilir.
4. **Heuristic Güvenlik Ağı:** Eğer sağ taraf (`val`) tire ile başlamıyorsa ve sol taraftaki kelime sayısı 4 veya daha azsa; anahtar içinde `AD`, `ÇEVİR`, `TARİH`, `METİN`, `PROJE`, `KOD` kökleri taranarak standart dışı başlıklar da yakalanır.

## İlgili Sayfalar

- [[dubbing-docx-parser]]
- [[parsed-paragraph]]
- [[adr-001-openxml-tab-based-parsing]]
