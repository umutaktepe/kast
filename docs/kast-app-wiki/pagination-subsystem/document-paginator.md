---
title: "Modül: DocumentPaginator (Çok Katmanlı Sayfa Koordinatörü)"
type: module
domain: pagination-subsystem
tags:
  - pagination
  - coordinator
  - multi-tier
---

# Modül: DocumentPaginator (Çok Katmanlı Sayfa Koordinatörü)

`DocumentPaginator`, bir Word belgesindeki paragrafların hangi sayfalarda yer aldığını tespit etmek için geliştirilmiş çok katmanlı koordinatör sınıftır (`src/paginator.py`).

Sistemde bulunan araçlara ve kullanıcı girdilerine göre en yüksek doğruluk sağlayan katmanı devreye sokar.

## Çok Katmanlı Sayfalama Hiyerarşisi

```mermaid
flowchart TD
    Start["Girdi: Paragraf Listesi"] --> CheckPDF{"Harici / Geçici PDF Var mı?"}
    CheckPDF -- "Evet (Tier 1)" --> PDFEngine["pdf-matching-engine (pdfplumber)"]
    CheckPDF -- "Hayır" --> CheckXML{"Kapsamlı XML Sayfa Kesmesi Var mı?"}
    CheckXML -- "Evet (Tier 2)" --> XMLEngine["_process_with_xml (w:lastRenderedPageBreak)"]
    CheckXML -- "Hayır (Tier 3)" --> LayoutEngine["pure-python-layout-paginator (Pillow & Geometri)"]
    PDFEngine --> Output["Çıktı: Sayfa Numaraları Atanmış Paragraflar"]
    XMLEngine --> Output
    LayoutEngine --> Output
```

## Katmanların Özellikleri

### 1. Kademe (Tier 1) — PDF Eşleme Motoru (`_process_with_pdf`)
- Eğer kullanıcı bir referans PDF verdiyse veya arka planda [[headless-pdf-converter]] ile geçici PDF üretilmişse çalışır.
- [[pdf-matching-engine]] kullanılarak her replik PDF sayfalarıyla eşleştirilir.
- Doğruluk oranı: **%100**.

### 2. Kademe (Tier 2) — OpenXML Soft/Hard Sayfa Kesmeleri (`_process_with_xml`)
- Word dökümanı kaydedilirken Word render motorunun XML içerisine bıraktığı `w:lastRenderedPageBreak` ve `w:br[@w:type="page"]` etiketlerini okur.
- Eğer dökümandaki yumuşak sayfa sonu sayısı yeterli sıklıktaysa (`_has_comprehensive_soft_breaks`) devreye girer.

### 3. Kademe (Tier 3) — Saf Python Mizanpaj Motoru (`PurePythonLayoutPaginator`)
- Sistemde ofis paketi bulunmayan izole ortamlarda yedek simülatör olarak çalışır.
- [[pure-python-layout-paginator]] dökümanın sayfa boyutları, kenar boşlukları ve font metrikleriyle satır sarma simülasyonu yapar.

## `process(paragraphs, pdf_path=None)` Metodu

Koordinatörün ana yürütme metodudur. Parametre olarak gelen paragraflara sırayla yukarıdaki hiyerarşiyi uygular ve `page` alanları güncellenmiş [[parsed-paragraph]] listesini döndürür.

## İlgili Sayfalar

- [[pdf-matching-engine]]
- [[headless-pdf-converter]]
- [[pure-python-layout-paginator]]
- [[adr-002-strict-pdf-pagination-flow]]
