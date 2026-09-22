---
title: "Modül: Saf Python Mizanpaj Motoru (PurePythonLayoutPaginator)"
type: module
domain: pagination-subsystem
tags:
  - layout
  - simulation
  - pillow
  - typography
---

# Modül: Saf Python Mizanpaj Motoru (PurePythonLayoutPaginator)

`PurePythonLayoutPaginator`, sistemde LibreOffice veya Word gibi harici hiçbir ofis paketi bulunmadığında devreye giren, belgenin sayfa geometrisini ve tipografisini saf Python ile simüle eden mizanpaj motorudur (`src/paginator.py`).

## Geometrik ve Tipografik Parametreler

Motor, Word dökümanının ilk bölümündeki (`doc.sections[0]`) OpenXML özelliklerini otomatik okur:

| Parametre | Değer / Kaynak | Açıklama |
| :--- | :--- | :--- |
| `page_height` | `sec.page_height` (792pt / Letter veya 842pt / A4) | Fiziksel sayfa yüksekliği. |
| `page_width` | `sec.page_width` (612pt / Letter veya 595pt / A4) | Fiziksel sayfa genişliği. |
| Kenar Boşlukları | `top`, `bottom`, `left`, `right` (varsayılan 72pt = 1 inç) | Yazdırılabilir alan sınırları. |
| `dialogue_indent_pt` | 108.0 pt (1.5 inç) | Standart dublaj senaryolarındaki asılı girinti (hanging indent). Replik metinlerinin satır sarma sınırını daraltır. |
| `line_spacing` | 1.5 satır | Dublaj şablonu standart satır aralığı çarpanı. |
| `space_after` | 10.0 pt | Paragraf sonrası bırakılan standart dikey boşluk. |

## Font Çözümleme ve Pillow Metrikleri

1. **Sistem Font Dizinleri (`SYSTEM_FONT_DIRS`):** Windows (`C:\Windows\Fonts`), Linux (`/usr/share/fonts`, `~/.local/share/fonts`) ve macOS (`/Library/Fonts`) taranarak belgedeki fontun (ör. Arial, Verdana) TrueType dosyası aranır (`find_font_file`).
2. **Pillow Metrikleri:** Font dosyası bulunduğunda `ImageFont.truetype` ile yüklenir ve `font.getlength(text)` metodu ile metnin pikselsel genişliği ölçülür.
3. **Karakter Genişliği Çarpanları (`KNOWN_FONT_LINE_RATIOS` & `KNOWN_FONT_AVG_CHAR_WIDTHS`):** Font dosyası fiziksel olarak bulunamazsa her yazı tipinin bilinen tipografik en-boy oranları (Verdana için 0.60, Arial için 0.53) kullanılarak karakter sayısı üzerinden satır sarma simülasyonu yapılır.

## Satır Sarma ve Sayfa Taşma Döngüsü

Paragraflar sırayla işlenirken dikey konum (`current_y`) hesaplanır:
```python
if (current_y + para_height > self.printable_height) and current_y > 0:
    current_page += 1
    current_y = 0.0

p.page = current_page
current_y += para_height
```

Belge içindeki yerel sayfa kesmeleri (`w:pageBreakBefore`, `w:br[@w:type="page"]`) de hesaba katılarak sayfa sıçramaları senkronize edilir.

## İlgili Sayfalar

- [[document-paginator]]
- [[pdf-matching-engine]]
- [[document-font-detection]]
- [[adr-002-strict-pdf-pagination-flow]]
