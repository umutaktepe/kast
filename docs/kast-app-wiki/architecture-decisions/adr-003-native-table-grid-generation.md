---
title: "ADR-003: Yerel OpenXML Table Grid ve Dinamik Tipografi Entegrasyonu"
type: architecture-decision-record
status: accepted
date: 2026-09-13
domain: architecture-decisions
tags:
  - adr
  - table-generation
  - openxml
  - styling
  - typography
---

# ADR-003: Yerel OpenXML Table Grid ve Dinamik Tipografi Entegrasyonu

## Bağlam (Context)

Dublaj kast tablosu, senaryo metninin hemen ardından gelen ve seslendirme yönetmeninin dökümanı incelerken veya yazdırırken doğrudan kullanacağı nihai tablodur. Standart `python-docx` kütüphanesinin varsayılan tablo ekleme metodu (`doc.add_table`), stillerin Word veya OnlyOffice gibi farklı ofis yazılımlarında açıldığında kenarlıksız, dağınık ve hizalamasız görünmesine neden olabilmektedir.

Ayrıca şu tipografik ve yapısal gereksinimler mevcuttur:
1. **Kenarlık Uyumu:** Tablonun her hücresi ince, siyah ve net tek çizgi (`Table Grid`) kenarlıklara sahip olmalıdır.
2. **Dikey Hizalama:** Hücre içi metinler estetik açıdan dikeyde ortalanmalıdır (`center`).
3. **Sayfa Geçişinde Satır Bölünmesini Engelleme:** Bir karakterin verisinin iki sayfa arasına yarı yarıya bölünmesi okunabilirliği bozar (`w:cantSplit`).
4. **Tipografik Bütünlük:** Senaryo hangi yazı tipi (ör. Verdana 11pt, Arial 10.5pt, Georgia vb.) ile yazılmışsa, eklenen tablonun da aynı font ailesi ve puntolarla oluşturulması gerekir. Tablonun dökümana "yama" gibi durmaması esastır.

## Karar (Decision)

Word dökümanı manipülasyonunda python-docx'in soyutlamasıyla yetinilmeyip, doğrudan OpenXML düzeyinde stil enjeksiyonu yapan [[openxml-styling]] ve [[cast-table-writer]] mimarisi kararlaştırılmıştır:

1. **Hücre Kenarlıkları (`set_cell_border`):** Her hücrenin `tcPr` etiketine doğrudan `w:tcBorders` XML elemanı enjekte edilir; üst, alt, sol ve sağ kenarlıklar `w:val="single"`, `w:sz="4"` (1/2 pt), `w:color="000000"` olarak sabitlenir.
2. **Dikey Ortalama:** Tüm hücrelere `WD_ALIGN_VERTICAL.CENTER` uygulanır.
3. **Satır Bölünme Koruması (`w:cantSplit`):** Başlık ve veri satırlarının tamamına `trPr/w:cantSplit` özelliği eklenerek Word'ün satırları sayfa sonlarında bölmesi önlenir.
4. **Dinamik Font ve Punto Tespiti (`detect_document_font`):** Dökümanın ilk 50 paragrafı, paragraflardaki `run` elemanları, `Normal` stili ve `docDefaults` etiketleri taranır. En baskın yazı tipi (ör. Verdana) ve punto istatistiksel frekans analiziyle (`Counter`) bulunur ve tablo buna göre biçimlendirilir.
5. **Esnek Çıktı Modları:**
   - *Varsayılan Mod:* Belgenin sonuna `w:pageBreak` eklenerek `<orijinal_adi>_kast.docx` adıyla yeni kopya oluşturulur (orijinal dosya korunur).
   - *Yerinde Mod (`--in-place`):* Doğrudan kaynak dosyaya yazar.
   - *Bağımsız Mod (`--standalone`):* Senaryo metnini içermeyen, yalnızca 4 sütunlu tablodan oluşan temiz bir Word belgesi üretir.

## Alternatifler (Alternatives Considered)

- **Alternatif 1: HTML veya PDF Olarak Çıktı Vermek:**
  - *Reddedilme Gerekçesi:* Çevirmenler ve yönetmenler teslimatlarını Word dökümanı üzerinden yapar ve dökümanın tek parça kalmasını tercih eder.
- **Alternatif 2: python-docx Yerleşik Tablo Stillerine Güvenmek (`Table Grid`):**
  - *Reddedilme Gerekçesi:* Farklı Word sürümleri ve yerelleştirmelerde (örneğin Türkçe Word'de `Tablo Kılavuzu`, İngilizce'de `Table Grid`) stil adları uyuşmazlığı nedeniyle stiller kaybolabiliyordu. Doğrudan OpenXML `w:tcBorders` enjeksiyonu platformdan bağımsız %100 kararlılık sağlar.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- Microsoft Word, macOS Word, LibreOffice Writer ve OnlyOffice'de pikselsel olarak kusursuz ve yeknesak tablo çıktısı.
- Senaryonun orijinal tasarım diliyle tam uyumlu tipografi.
- Veri kaybı veya orijinal dosya bozulması riski sıfırlandı.

### Olumsuz / Kısıtlar:
- OpenXML etiketlerinin doğrudan manipülasyonu python-docx iç veri yapılarına (`_tc`, `_tr`) erişim gerektirir; bu nedenle kod bağımsız testlerle sıkı şekilde denetlenmelidir.

## İlgili Sayfalar

- [[cast-table-writer]]
- [[openxml-styling]]
- [[document-font-detection]]
- [[cast-extraction-result]]
