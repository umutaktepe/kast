---
title: "Modül: PDF Metin Eşleme Motoru (PDF Matching Engine)"
type: module
domain: pagination-subsystem
tags:
  - pdf
  - pdfplumber
  - text-matching
  - normalization
---

# Modül: PDF Metin Eşleme Motoru (PDF Matching Engine)

`PDF Metin Eşleme Motoru`, `src/paginator.py` içerisinde `_process_with_pdf` metodu altında çalışan ve repliklerin PDF üzerindeki kesin fiziksel sayfalarını bulan motordur.

Bu motor, harici bir referans PDF veya [[headless-pdf-converter]] tarafından arka planda üretilen geçici PDF ile beslenir. Mimari kararı [[adr-002-strict-pdf-pagination-flow]] belgesinde yer almaktadır.

## Çalışma Algoritması

1. **PDF Sayfalarının Çıkarılması:** `pdfplumber.open(pdf_path)` ile belge açılır ve her sayfanın metni `extract_text()` ile okunur.
2. **Kapsamlı Karakter Normalizasyonu (`normalize`):**
   Word ve PDF arasındaki tipografik karakter farklarını gidermek için özel bir normalizasyon fonksiyonu uygulanır:
   - Türkçe karakter dönüşümü (`İ -> i`, `I -> ı`).
   - Tire varyasyonları standartlaştırılır (`–`, `—` $\rightarrow$ `-`).
   - Akıllı tırnak ve kesme işaretleri standartlaştırılır (`“`, `”` $\rightarrow$ `"`, `’`, `‘` $\rightarrow$ `'`).
   - Çoklu boşluklar tek boşluğa indirgenir (`" ".join(t.split())`).
3. **Monoton İlerleyen Sayfa Taraması (Monotonic Window):**
   Senaryo akışı doğası gereği kronolojiktir (1. sayfadaki replik 5. sayfadan sonra gelemez). Bu nedenle arama penceresi her zaman `last_page` noktasından başlatılır:
   ```python
   search_needle = cleaned_dial[:30].strip()
   if search_needle:
       for page_num in range(last_page, len(pdf_page_texts) + 1):
           if search_needle in pdf_page_texts[page_num - 1]:
               last_page = page_num
               break
   p.page = last_page
   ```
4. **İğne Metin (Needle):** Repliğin ilk 30 karakterlik temizlenmiş kısmı aranarak sayfa geçişlerindeki küçük kesintilerden etkilenmeden hızlı ve hatasız eşleşme sağlanır.

## Performans ve Güvenilirlik

- `O(N)` karmaşıklığında doğrusal tarama.
- Sayfa arama aralığı kısıtlandığı için yüzlerce sayfalık senaryolar dahi saniyeler içinde tamamlanır.

## İlgili Sayfalar

- [[document-paginator]]
- [[headless-pdf-converter]]
- [[adr-002-strict-pdf-pagination-flow]]
- [[parsed-paragraph]]
