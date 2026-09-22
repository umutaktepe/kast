---
title: "ADR-001: OpenXML Sekme ve Tire Tabanlı Diyalog Ayrıştırma Mimarisi"
type: architecture-decision-record
status: accepted
date: 2026-09-13
domain: architecture-decisions
tags:
  - adr
  - parsing
  - openxml
  - dubbing-standards
---

# ADR-001: OpenXML Sekme ve Tire Tabanlı Diyalog Ayrıştırma Mimarisi

## Bağlam (Context)

Dublaj çeviri stüdyolarında ve seslendirme yönetmenleri arasında standart Word (`.docx`) senaryo şablonları kullanılır. Bu şablonlarda konuşmacı ve replik ayrımı görsel olarak sekme (tab) ve tire karakterleri ile sağlanır:

```text
KARAKTER <TAB> - Replik metni buraya gelir.
```

Aynı zamanda senaryonun en başında künye / meta veri alanları yer alır:
```text
FİLMİN ADI <TAB> Örnek Film Adı
ÇEVİRMEN <TAB> Çevirmen İsmi
```

Ve replik aralarında bağımsız süre kodları bulunur:
```text
01.23
01.24.15
```

Geleneksel yöntemlerde ya metinler düz metne (`.txt`) dönüştürülüp karmaşık ve kırılgan regex desenleriyle taranmakta ya da çevirmenler senaryo başındaki başlıkları elle silmek zorunda kalmaktaydı. Regex tabanlı düz metin yaklaşımları şu sorunlara yol açıyordu:
1. `FİLMİN ADI` veya `ÇEVİRMEN` gibi başlıkların yanlışlıkla "karakter" olarak algılanması.
2. Karakter isminde geçen iki nokta (`:`), tire (`-`) veya özel karakterlerin regex eşleşmelerini bozması.
3. Word paragraf yapısı içindeki biçimlendirmelerin ve OpenXML sekme işaretçilerinin (`w:tab`) kaybolması.

## Karar (Decision)

Düz metin regex yaklaşımı yerine doğrudan python-docx ve OpenXML paragraf ağacı üzerinden çalışan sekme ve tire hiyerarşisi (`DubbingDocxParser`) kararlaştırılmıştır:

1. **OpenXML Sekme Ayrımı (`\t`):** Her paragraf `\t` karakteri üzerinden en fazla iki parçaya bölünür (`text.split('\t', 1)`).
2. **Metadata Önceliği:** Paragraf ilk parçası, [[metadata-filtering]] modülündeki `KNOWN_METADATA_KEYS` sözlüğü ve Türkçe büyük harf uyumlu (`turkish_upper`) normalizasyon ile kontrol edilir. Eşleşirse paragraf doğrudan meta veri olarak işaretlenir ve diyalog sayımına dahil edilmez.
3. **Zaman Kodu İzolasyonu:** Paragraf metni [[timecode-detection]] regex'i ile kontrol edilir; bağımsız zaman kodları (`00.41`, `01:23:45:12`) replik metninden soyutlanır.
4. **Diyalog ve Tire Doğrulaması:** Sağ tarafındaki metin tire (`-`, `–`, `—`) ile başlayan ve sol tarafında konuşmacı adı bulunan satırlar kesin diyalog olarak kabul edilir ve [[dialogue-line]] modeline dönüştürülür.

## Alternatifler (Alternatives Considered)

- **Alternatif 1: Saf Regex ile Düz Metin Ayrıştırma:**
  - *Reddedilme Gerekçesi:* Karakter adları film adına veya çevirmen adına çok benzer yapıda olabildiğinden (`JOHN:`, `ÇEVİRMEN:`), yanlış pozitif (false positive) oranı kabul edilemez düzeydeydi.
- **Alternatif 2: LLM veya NLP Tabanlı Varlık Çıkarımı (NER):**
  - *Reddedilme Gerekçesi:* Ağır hesaplama maliyeti, internet/API bağımlılığı ve deterministik olmama riski. Stüdyolarda yerel, anlık ve sıfır bağımlılıklı deterministik çalışma zorunludur.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- Başlık silme zorunluluğu tamamen ortadan kalktı; kullanıcı ham senaryoyu doğrudan yükleyebilir.
- Deterministik, mikrosaniye seviyesinde hızlı ve %100 tekrarlanabilir ayrıştırma sağlandı.
- Karakter isimleri temizlenerek [[character-stats]] havuzuna güvenli şekilde aktarıldı.

### Olumsuz / Kısıtlar:
- Dublaj metninde sekme yerine yalnızca birden fazla boşluk kullanılan standart dışı senaryolarda sekme kuralı işletilemez; bu durumlar için stüdyo standart sekme formatı ön koşul kabul edilir.

## İlgili Sayfalar

- [[dubbing-docx-parser]]
- [[metadata-filtering]]
- [[timecode-detection]]
- [[dialogue-line]]
