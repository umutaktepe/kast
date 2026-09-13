"""DOCX Table Writer for Dubbing Cast Extraction (Kast 2.0).

Generates and formats the 4-column cast table and appends it directly to
a Word (.docx) document with proper styling, borders, and column widths.
"""
from collections import Counter
from typing import Optional, Tuple

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from src.models import CastExtractionResult


def set_cell_border(cell, **kwargs) -> None:
    """Apply w:tcBorders XML element to a table cell.

    Args:
        cell: python-docx table cell object.
        **kwargs: Edge specifications e.g. top={"sz": 4, "val": "single", "color": "000000"}.
    """
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


def detect_document_font(doc: Document) -> Tuple[Optional[str], Optional[float]]:
    """Detect dominant font name and font size (in pt) from document content and styles.

    Args:
        doc: python-docx Document object.

    Returns:
        tuple of (font_name, font_size_pt), each may be None if not detected.
    """
    font_counter: Counter[str] = Counter()
    size_counter: Counter[float] = Counter()

    # 1. Sample non-empty paragraphs in the document
    for p in doc.paragraphs:
        text_len = len(p.text.strip())
        if text_len == 0:
            continue

        # Check runs
        for r in p.runs:
            r_len = len(r.text)
            if r_len == 0:
                continue

            fname = r.font.name
            if not fname and r._r is not None:
                rPr = r._r.find(qn("w:rPr"))
                if rPr is not None:
                    rFonts = rPr.find(qn("w:rFonts"))
                    if rFonts is not None:
                        fname = (
                            rFonts.get(qn("w:ascii"))
                            or rFonts.get(qn("w:hAnsi"))
                            or rFonts.get(qn("w:cs"))
                        )
            if fname:
                font_counter[fname.strip("\"' ")] += r_len

            fsize = None
            if r.font.size is not None:
                fsize = r.font.size.pt
            elif r._r is not None:
                rPr = r._r.find(qn("w:rPr"))
                if rPr is not None:
                    sz = rPr.find(qn("w:sz"))
                    if sz is not None:
                        val = sz.get(qn("w:val"))
                        if val and val.isdigit():
                            fsize = int(val) / 2.0
            if fsize and 6.0 <= fsize <= 36.0:
                size_counter[fsize] += r_len

        # Check paragraph style
        if p.style is not None:
            sfname = p.style.font.name
            if not sfname and hasattr(p.style, "element") and p.style.element is not None:
                rPr = p.style.element.find(qn("w:rPr"))
                if rPr is not None:
                    rFonts = rPr.find(qn("w:rFonts"))
                    if rFonts is not None:
                        sfname = (
                            rFonts.get(qn("w:ascii"))
                            or rFonts.get(qn("w:hAnsi"))
                            or rFonts.get(qn("w:cs"))
                        )
            if sfname:
                font_counter[sfname.strip("\"' ")] += text_len

            sfsize = None
            if p.style.font.size is not None:
                sfsize = p.style.font.size.pt
            elif hasattr(p.style, "element") and p.style.element is not None:
                rPr = p.style.element.find(qn("w:rPr"))
                if rPr is not None:
                    sz = rPr.find(qn("w:sz"))
                    if sz is not None:
                        val = sz.get(qn("w:val"))
                        if val and val.isdigit():
                            sfsize = int(val) / 2.0
            if sfsize and 6.0 <= sfsize <= 36.0:
                size_counter[sfsize] += text_len

    # 2. Check doc.styles['Normal']
    if "Normal" in doc.styles:
        normal = doc.styles["Normal"]
        if normal.font.name:
            font_counter[normal.font.name.strip("\"' ")] += 1
        elif hasattr(normal, "element") and normal.element is not None:
            rPr = normal.element.find(qn("w:rPr"))
            if rPr is not None:
                rFonts = rPr.find(qn("w:rFonts"))
                if rFonts is not None:
                    fname = (
                        rFonts.get(qn("w:ascii"))
                        or rFonts.get(qn("w:hAnsi"))
                        or rFonts.get(qn("w:cs"))
                    )
                    if fname:
                        font_counter[fname.strip("\"' ")] += 1

        if normal.font.size is not None:
            size_counter[normal.font.size.pt] += 1
        elif hasattr(normal, "element") and normal.element is not None:
            rPr = normal.element.find(qn("w:rPr"))
            if rPr is not None:
                sz = rPr.find(qn("w:sz"))
                if sz is not None:
                    val = sz.get(qn("w:val"))
                    if val and val.isdigit():
                        v = int(val) / 2.0
                        if 6.0 <= v <= 36.0:
                            size_counter[v] += 1

    # 3. Check docDefaults in styles
    if hasattr(doc.styles, "element") and doc.styles.element is not None:
        docDefaults = doc.styles.element.find(qn("w:docDefaults"))
        if docDefaults is not None:
            rPrDef = docDefaults.find(qn("w:rPrDefault"))
            if rPrDef is not None:
                rPr = rPrDef.find(qn("w:rPr"))
                if rPr is not None:
                    rFonts = rPr.find(qn("w:rFonts"))
                    if rFonts is not None:
                        fname = (
                            rFonts.get(qn("w:ascii"))
                            or rFonts.get(qn("w:hAnsi"))
                            or rFonts.get(qn("w:cs"))
                        )
                        if fname:
                            font_counter[fname.strip("\"' ")] += 1
                    sz = rPr.find(qn("w:sz"))
                    if sz is not None:
                        val = sz.get(qn("w:val"))
                        if val and val.isdigit():
                            v = int(val) / 2.0
                            if 6.0 <= v <= 36.0:
                                size_counter[v] += 1

    chosen_font = font_counter.most_common(1)[0][0] if font_counter else None
    chosen_size = size_counter.most_common(1)[0][0] if size_counter else None

    return chosen_font, chosen_size


class CastTableWriter:
    """Formats and writes dubbing cast statistics table to DOCX documents."""

    def __init__(
        self,
        border_color: str = "000000",
        border_size: int = 4,
        font_name: Optional[str] = None,
        font_size_pt: Optional[float] = None,
    ):
        self.border_color = border_color
        self.border_size = border_size
        self.font_name = font_name
        self.font_size_pt = font_size_pt

    def append_cast_table(
        self,
        doc: Document,
        result: CastExtractionResult,
        add_page_break: bool = True
    ) -> Document:
        """Append a formatted 4-column cast table to the given Word document.

        Args:
            doc: Document instance to append the table to.
            result: CastExtractionResult containing character statistics.
            add_page_break: Whether to insert a page break before the table.

        Returns:
            The Document instance for method chaining.
        """
        # Font ve font boyutu tespiti
        detected_font, detected_size = detect_document_font(doc)
        font_name = self.font_name or detected_font or "Arial"
        item_size_pt = self.font_size_pt or detected_size or 10.0
        header_size_pt = self.font_size_pt or detected_size or 11.0
        # 1. Metnin sonuna yeni sayfa kesmesi ekle
        if add_page_break:
            doc.add_page_break()

        # 2. 4 sütunlu tablo oluştur
        table = doc.add_table(rows=1, cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Sütun genişlikleri (Karakter, Replik Sayısı, Sayfalar, Notlar)
        col_widths = [Inches(2.0), Inches(1.0), Inches(2.3), Inches(1.2)]
        for idx, width in enumerate(col_widths):
            table.columns[idx].width = width

        # Kenarlık özellikleri (İnce siyah tek çizgi)
        border_spec = {"val": "single", "sz": self.border_size, "color": self.border_color}
        all_borders = {k: border_spec for k in ["top", "left", "bottom", "right"]}

        # 4. Başlık satırı
        hdr_row = table.rows[0]
        hdr_trPr = hdr_row._tr.get_or_add_trPr()
        hdr_trPr.append(OxmlElement("w:cantSplit"))

        hdr_cells = hdr_row.cells
        headers = ["Karakter", "Replik Sayısı", "Repliklerin Geçtiği Sayfalar", "Notlar"]

        for i, text in enumerate(headers):
            hdr_cells[i].text = text
            hdr_cells[i].width = col_widths[i]
            hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_border(hdr_cells[i], **all_borders)
            hp = hdr_cells[i].paragraphs[0]
            hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            hp.paragraph_format.space_before = Pt(2)
            hp.paragraph_format.space_after = Pt(2)
            hp.paragraph_format.left_indent = Inches(0)
            hp.paragraph_format.right_indent = Inches(0)
            hp.paragraph_format.first_line_indent = Inches(0)
            if hp.runs:
                hp.runs[0].font.bold = True
                hp.runs[0].font.name = font_name
                hp.runs[0].font.size = Pt(header_size_pt)

        # 5. Veri satırları
        for char in result.characters:
            row = table.add_row()
            row_trPr = row._tr.get_or_add_trPr()
            row_trPr.append(OxmlElement("w:cantSplit"))

            row_cells = row.cells
            row_cells[0].text = char.name or ""
            row_cells[1].text = str(char.line_count)
            row_cells[2].text = char.formatted_pages
            row_cells[3].text = char.notes or ""

            for i in range(4):
                row_cells[i].width = col_widths[i]
                row_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_border(row_cells[i], **all_borders)
                rp = row_cells[i].paragraphs[0]
                rp.paragraph_format.space_before = Pt(2)
                rp.paragraph_format.space_after = Pt(2)
                rp.paragraph_format.left_indent = Inches(0)
                rp.paragraph_format.right_indent = Inches(0)
                rp.paragraph_format.first_line_indent = Inches(0)
                if rp.runs:
                    rp.runs[0].font.name = font_name
                    rp.runs[0].font.size = Pt(item_size_pt)

        return doc

    def save_result(self, doc: Document, output_path: str) -> str:
        """Save the document to the specified output file path.

        Args:
            doc: Document instance to save.
            output_path: Target .docx file path.

        Returns:
            The saved output path.
        """
        doc.save(output_path)
        return output_path


def append_cast_table(
    doc: Document,
    result: CastExtractionResult,
    add_page_break: bool = True,
    font_name: Optional[str] = None,
    font_size_pt: Optional[float] = None,
) -> Document:
    """Convenience function to append cast table using default CastTableWriter."""
    writer = CastTableWriter(font_name=font_name, font_size_pt=font_size_pt)
    return writer.append_cast_table(doc, result, add_page_break=add_page_break)


def save_result(doc: Document, output_path: str) -> str:
    """Convenience function to save document to file path."""
    writer = CastTableWriter()
    return writer.save_result(doc, output_path)
