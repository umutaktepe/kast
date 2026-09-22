---
title: "Özellik: OpenXML Stil ve Kenarlık Manipülasyonu"
type: feature-spec
domain: document-generation
tags:
  - openxml
  - borders
  - styling
  - docx-internals
---

# Özellik: OpenXML Stil ve Kenarlık Manipülasyonu

Word belgelerinin farklı ofis yazılımlarında (Word 2016-365, LibreOffice Writer, OnlyOffice, Google Docs) pikselsel ve yapısal tutarlılıkla görüntülenmesi için `src/table_writer.py` içerisinde doğrudan OpenXML düzeyinde stil manipülasyonu uygulanır.

Mimarisi [[adr-003-native-table-grid-generation]] belgesinde açıklanmıştır.

## Hücre Kenarlığı Uygulama (`set_cell_border`)

Word'ün `Table Grid` stili platformdan platforma isim değiştirebildiğinden, Kast hücre seviyesinde XML kenarlık etiketi (`w:tcBorders`) üretir:

```python
def set_cell_border(cell, **kwargs) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    existing_borders = tcPr.find(qn("w:tcBorders"))
    if existing_borders is not None:
        tcPr.remove(existing_borders)

    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f"w:{edge}"
            element = OxmlElement(tag)
            element.set(qn("w:val"), str(edge_data.get("val", "single")))
            element.set(qn("w:sz"), str(edge_data.get("sz", 4)))
            element.set(qn("w:space"), str(edge_data.get("space", 0)))
            element.set(qn("w:color"), str(edge_data.get("color", "000000")))
            tcBorders.append(element)
    tcPr.append(tcBorders)
```

- **`w:val="single"`:** Kesiksiz düz çizgi.
- **`w:sz="4"`:** 4 sekizlik nokta = 0.5 pt kalınlık (ince, şık kenarlık).
- **`w:color="000000"`:** Saf siyah kenarlık.

## Satır Bölünme Koruması (`w:cantSplit`)

Tablo sayfalar arasında uzadığında bir karakterin satırının ikiye bölünmesini engellemek için satır özellikleri (`trPr`) içerisine `w:cantSplit` eklenir:
```python
row_trPr = row._tr.get_or_add_trPr()
row_trPr.append(OxmlElement("w:cantSplit"))
```

## Dikey Ortalama

Tüm hücrelerin dikey eksende ortalanması sağlanır:
```python
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
```

Bu sayede dar veya geniş satırlarda metinler hücrenin ortasında dengeli durur.

## İlgili Sayfalar

- [[cast-table-writer]]
- [[document-font-detection]]
- [[adr-003-native-table-grid-generation]]
