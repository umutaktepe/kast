"""Multi-tier document paginator engine for Kast."""

import math
import os
from typing import List, Optional, Tuple
from docx import Document
from PIL import ImageFont

from src.parser import ParsedParagraph

KNOWN_FONT_LINE_RATIOS: dict[str, float] = {
    "verdana": 1.2153,
    "arial": 1.1172,
    "calibri": 1.2207,
    "times new roman": 1.1074,
    "courier new": 1.1328,
    "segoe ui": 1.2500,
    "tahoma": 1.2065,
    "georgia": 1.1406,
}
DEFAULT_FONT_LINE_RATIO = 1.18

KNOWN_FONT_AVG_CHAR_WIDTHS: dict[str, float] = {
    "verdana": 0.60,
    "arial": 0.53,
    "calibri": 0.52,
    "times new roman": 0.47,
    "courier new": 0.60,
    "segoe ui": 0.53,
    "tahoma": 0.56,
    "georgia": 0.54,
}
DEFAULT_AVG_CHAR_WIDTH_RATIO = 0.53

SYSTEM_FONT_DIRS: List[str] = [
    # Windows
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    # Linux
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.local/share/fonts"),
    os.path.expanduser("~/.fonts"),
    # macOS
    "/System/Library/Fonts",
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
]

FONT_FILE_CANDIDATES: dict[str, List[str]] = {
    "verdana": [
        "verdana.ttf", "Verdana.ttf", "Verdana.TTF", "verdanab.ttf", "Verdanab.TTF"
    ],
    "arial": [
        "arial.ttf", "Arial.ttf", "Arial.TTF", "arialbd.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"
    ],
    "calibri": [
        "calibri.ttf", "Calibri.ttf", "Calibri.TTF", "carlito.ttf"
    ],
    "times new roman": [
        "times.ttf", "Times.ttf", "Times.TTF", "LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"
    ],
    "courier new": [
        "cour.ttf", "Cour.ttf", "LiberationMono-Regular.ttf", "DejaVuSansMono.ttf"
    ],
    "segoe ui": [
        "segoeui.ttf", "SegoeUI.ttf"
    ],
    "tahoma": [
        "tahoma.ttf", "Tahoma.ttf"
    ],
    "georgia": [
        "georgia.ttf", "Georgia.ttf"
    ],
}

DEFAULT_FONT_CANDIDATES = [
    "/usr/share/fonts/msfonts/Arial.TTF",
    "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
    "/usr/share/fonts/msttcorefonts/Arial.ttf",
    "/usr/share/fonts/msfonts/Verdana.TTF",
    "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def find_font_file(font_name: str) -> Optional[str]:
    """Resolve font name to an absolute file path across Windows, Linux, and macOS."""
    clean_name = font_name.strip().lower()
    candidates = list(FONT_FILE_CANDIDATES.get(clean_name, []))
    candidates.extend([
        f"{clean_name}.ttf",
        f"{clean_name}.otf",
        f"{font_name}.ttf",
        f"{font_name}.TTF",
        f"{font_name}.otf",
    ])

    for d in SYSTEM_FONT_DIRS:
        if not d or not os.path.exists(d):
            continue
        # Direct check first (fast O(1))
        for cand in candidates:
            direct_path = os.path.join(d, cand)
            if os.path.exists(direct_path):
                return direct_path

        # Subdirectory walk (for Linux deep font hierarchies)
        for root, _, files in os.walk(d):
            lower_files = {f.lower(): f for f in files}
            for cand in candidates:
                cand_lower = cand.lower()
                if cand_lower in lower_files:
                    return os.path.join(root, lower_files[cand_lower])

    return None


def detect_document_font_and_format(doc: Document) -> Tuple[str, float, float, float]:
    """
    Extracts font name, font size (pt), line spacing multiplier, and space after (pt)
    from a docx Document, prioritizing paragraph-level formatting then Normal style.
    Returns: (font_name, font_size_pt, line_spacing, space_after_pt)
    """
    font_name = "Arial"
    font_size_pt = 11.0
    line_spacing = 1.5
    space_after_pt = 10.0

    # 1. Inspect Normal style first
    try:
        if "Normal" in doc.styles:
            normal = doc.styles["Normal"]
            if normal.font.name:
                font_name = normal.font.name
            if normal.font.size and hasattr(normal.font.size, "pt"):
                font_size_pt = float(normal.font.size.pt)
            if normal.paragraph_format.line_spacing:
                try:
                    line_spacing = float(normal.paragraph_format.line_spacing)
                except Exception:
                    pass
            if normal.paragraph_format.space_after and hasattr(
                normal.paragraph_format.space_after, "pt"
            ):
                space_after_pt = float(normal.paragraph_format.space_after.pt)
    except Exception:
        pass

    # 2. Inspect document paragraphs for overrides
    for p in doc.paragraphs[:50]:
        if not p.text.strip():
            continue
        if p.paragraph_format.line_spacing:
            try:
                line_spacing = float(p.paragraph_format.line_spacing)
            except Exception:
                pass
        if p.paragraph_format.space_after and hasattr(
            p.paragraph_format.space_after, "pt"
        ):
            space_after_pt = float(p.paragraph_format.space_after.pt)
        for r in p.runs:
            if r.font.name:
                font_name = r.font.name
            if r.font.size and hasattr(r.font.size, "pt"):
                font_size_pt = float(r.font.size.pt)
        if font_name.lower() != "arial":
            break

    return font_name, font_size_pt, line_spacing, space_after_pt


class PurePythonLayoutPaginator:
    """
    DOCX dosyasının sectPr (sayfa boyutu, kenar boşlukları) ve 
    paragraf stil parametrelerini (Font, 1.5 satır aralığı, 10pt son boşluk, 1.5 inç girinti)
    kullanarak her bir paragrafın hangi sayfaya düştüğünü hesaplayan yüksek hassasiyetli mizanpaj motoru.
    """

    def __init__(
        self,
        page_height_pt: float = 792.0,  # 11 inch (Letter) veya 842.0 (A4)
        page_width_pt: float = 612.0,
        top_margin_pt: float = 72.0,
        bottom_margin_pt: float = 72.0,
        left_margin_pt: float = 72.0,
        right_margin_pt: float = 72.0,
        dialogue_indent_pt: float = 108.0,  # 1.5 inch hanging indent
        font_path: Optional[str] = None,
        font_name: str = "Arial",
        font_size_pt: float = 11.0,
        line_spacing_multiplier: float = 1.5,
        space_after_pt: float = 10.0,
    ) -> None:
        self.page_height = page_height_pt
        self.page_width = page_width_pt
        self.top_margin = top_margin_pt
        self.bottom_margin = bottom_margin_pt
        self.left_margin = left_margin_pt
        self.right_margin = right_margin_pt

        self.printable_height = page_height_pt - top_margin_pt - bottom_margin_pt
        self.printable_width = page_width_pt - left_margin_pt - right_margin_pt
        self.dialogue_width = self.printable_width - dialogue_indent_pt

        self.font_name = font_name
        self.font_size_pt = float(font_size_pt)
        self.line_spacing_multiplier = float(line_spacing_multiplier)
        self.space_after_pt = float(space_after_pt)

        # Typographic line pitch ratio (Word lineRule="auto")
        self.font_ratio = KNOWN_FONT_LINE_RATIOS.get(
            self.font_name.lower(), DEFAULT_FONT_LINE_RATIO
        )
        self.single_line_height = (
            self.font_size_pt * self.font_ratio * self.line_spacing_multiplier
        )

        # Resolve font file
        resolved_path = (
            font_path
            if (font_path and os.path.exists(font_path))
            else find_font_file(font_name)
        )
        if not resolved_path:
            for candidate in DEFAULT_FONT_CANDIDATES:
                if os.path.exists(candidate):
                    resolved_path = candidate
                    break

        self.font: Optional[ImageFont.FreeTypeFont] = None
        if resolved_path:
            try:
                self.font = ImageFont.truetype(resolved_path, int(self.font_size_pt))
            except Exception:
                self.font = None

    def _estimate_single_block_lines(self, text: str, max_width_pt: float) -> int:
        """Satır sarma hesabı (tek satırlık blok için)."""
        if not text:
            return 1

        if self.font:
            total_width = self.font.getlength(text)
            if total_width <= max_width_pt:
                return 1

            words = text.split(" ")
            lines = 1
            current_line = ""

            for word in words:
                if not word:
                    continue
                test_line = f"{current_line} {word}".strip() if current_line else word
                if self.font.getlength(test_line) <= max_width_pt:
                    current_line = test_line
                else:
                    if current_line:
                        lines += 1
                        current_line = word
                        if self.font.getlength(word) > max_width_pt:
                            extra = int(self.font.getlength(word) / max_width_pt)
                            lines += extra
                            current_line = ""
                    else:
                        extra = int(self.font.getlength(word) / max_width_pt)
                        lines += extra
                        current_line = ""
            return max(1, lines)
        else:
            # Word-wrapping fallback when TrueType font cannot be loaded
            avg_ratio = KNOWN_FONT_AVG_CHAR_WIDTHS.get(
                self.font_name.lower(), DEFAULT_AVG_CHAR_WIDTH_RATIO
            )
            char_w = max(3.0, self.font_size_pt * avg_ratio)
            chars_per_line = max(1, int(max_width_pt / char_w))

            words = text.split(" ")
            lines = 1
            current_len = 0
            for word in words:
                if not word:
                    continue
                w_len = len(word)
                if current_len + (1 if current_len > 0 else 0) + w_len <= chars_per_line:
                    current_len += (1 if current_len > 0 else 0) + w_len
                else:
                    if current_len > 0:
                        lines += 1
                        current_len = w_len
                        if w_len > chars_per_line:
                            lines += w_len // chars_per_line
                            current_len = w_len % chars_per_line
                    else:
                        lines += w_len // chars_per_line
                        current_len = w_len % chars_per_line
            return max(1, lines)

    def estimate_lines(self, text: str, max_width_pt: float) -> int:
        """Verilen metnin belirtilen genişlikte kaç satıra sarılacağını tahmin eder."""
        if not text or not text.strip():
            return 1

        lines_count = 0
        for block in text.splitlines():
            block_clean = block.strip()
            if not block_clean:
                lines_count += 1
            else:
                lines_count += self._estimate_single_block_lines(block_clean, max_width_pt)

        return max(1, lines_count)

    def paginate_paragraphs(self, paragraphs: List[ParsedParagraph]) -> List[ParsedParagraph]:
        """Paragraf listesini mizanpaj kurallarına göre sayfalara böler."""
        current_page = 1
        current_y = 0.0

        for p in paragraphs:
            # Paragraf yüksekliğini hesapla
            if getattr(p, "is_empty", False):
                lines = 1
                para_height = self.single_line_height + self.space_after_pt
            elif p.is_timecode:
                lines = 1
                para_height = self.single_line_height + self.space_after_pt
            elif p.speaker and p.dialogue:
                lines = self.estimate_lines(p.dialogue, self.dialogue_width)
                para_height = (lines * self.single_line_height) + self.space_after_pt
            else:
                lines = self.estimate_lines(p.text, self.printable_width)
                para_height = (lines * self.single_line_height) + self.space_after_pt

            # Sayfa taşma kontrolü
            if (current_y + para_height > self.printable_height) and current_y > 0:
                current_page += 1
                current_y = 0.0

            p.page = current_page
            current_y += para_height

        return paragraphs


class DocumentPaginator:
    """
    Çok katmanlı sayfa tespit koordinatörü:
    1. Varsa harici PDF verisini kullanır (Tier 1).
    2. Varsa XML soft/hard page break'lerini okur (Tier 2).
    3. Saf Python layout motoruyla sayfaları hesaplar (Tier 3).
    """

    def __init__(self, doc: Optional[Document] = None) -> None:
        self.doc = doc
        if doc and hasattr(doc, "sections") and len(doc.sections) > 0:
            sec = doc.sections[0]
            page_height = (
                getattr(sec.page_height, "pt", 792.0)
                if getattr(sec, "page_height", None) is not None
                else 792.0
            )
            page_width = (
                getattr(sec.page_width, "pt", 612.0)
                if getattr(sec, "page_width", None) is not None
                else 612.0
            )
            top_margin = (
                getattr(sec.top_margin, "pt", 72.0)
                if getattr(sec, "top_margin", None) is not None
                else 72.0
            )
            bottom_margin = (
                getattr(sec.bottom_margin, "pt", 72.0)
                if getattr(sec, "bottom_margin", None) is not None
                else 72.0
            )
            left_margin = (
                getattr(sec.left_margin, "pt", 72.0)
                if getattr(sec, "left_margin", None) is not None
                else 72.0
            )
            right_margin = (
                getattr(sec.right_margin, "pt", 72.0)
                if getattr(sec, "right_margin", None) is not None
                else 72.0
            )

            font_name, font_size_pt, line_spacing, space_after = (
                detect_document_font_and_format(doc)
            )

            self.layout_paginator = PurePythonLayoutPaginator(
                page_height_pt=page_height,
                page_width_pt=page_width,
                top_margin_pt=top_margin,
                bottom_margin_pt=bottom_margin,
                left_margin_pt=left_margin,
                right_margin_pt=right_margin,
                font_name=font_name,
                font_size_pt=font_size_pt,
                line_spacing_multiplier=line_spacing,
                space_after_pt=space_after,
            )
        else:
            self.layout_paginator = PurePythonLayoutPaginator()

    def process(
        self,
        paragraphs: List[ParsedParagraph],
        pdf_path: Optional[str] = None,
    ) -> List[ParsedParagraph]:
        """
        Paragraflara sayfa numaralarını atar.
        Önce PDF (Tier 1), ardından XML sayfa sonları (Tier 2),
        en son Saf Python mizanpaj motoru (Tier 3) kullanılır.
        """
        # Tier 1: Harici PDF verilmişse pdfplumber ile eşleştir
        if pdf_path:
            return self._process_with_pdf(paragraphs, pdf_path)

        # Tier 2: XML soft / hard page break'leri varsa kullan
        if self.doc and self._has_native_page_breaks(self.doc):
            assigned = self._process_with_xml(paragraphs)
            if assigned and max((p.page for p in assigned), default=1) > 1:
                return assigned

        # Tier 3: Saf Python mizanpaj hesabı
        return self.layout_paginator.paginate_paragraphs(paragraphs)

    @classmethod
    def assign_pages(
        cls,
        doc: Optional[Document],
        parsed_paragraphs: List[ParsedParagraph],
        pdf_path: Optional[str] = None,
    ) -> List[ParsedParagraph]:
        """Convenience method compatible with Paginator.assign_pages interface."""
        paginator = cls(doc=doc)
        return paginator.process(paragraphs=parsed_paragraphs, pdf_path=pdf_path)

    def _has_native_page_breaks(self, doc: Document) -> bool:
        """Dökümanda XML tabanlı sayfa sonu etiketleri olup olmadığını kontrol eder."""
        try:
            breaks = doc._element.xpath(
                ".//w:lastRenderedPageBreak | .//w:r/w:br[@w:type='page'] | .//w:pPr/w:pageBreakBefore"
            )
            return len(breaks) > 0
        except Exception:
            return False

    def _process_with_xml(self, paragraphs: List[ParsedParagraph]) -> List[ParsedParagraph]:
        """Döküman XML'indeki soft ve hard page break'leri izleyerek sayfa numaralarını atar."""
        if not self.doc:
            return paragraphs

        current_page = 1
        para_pages: dict[int, int] = {}

        for doc_idx, doc_p in enumerate(self.doc.paragraphs):
            p_elm = doc_p._element
            # Paragraf öncesi sayfa kesmesi
            if p_elm.xpath(".//w:pPr/w:pageBreakBefore"):
                current_page += 1

            # Paragraf içindeki sayfa kesmeleri
            break_elements = p_elm.xpath(
                ".//w:lastRenderedPageBreak | .//w:r/w:br[@w:type='page']"
            )
            if break_elements:
                current_page += len(break_elements)

            para_pages[doc_idx] = current_page

        for p in paragraphs:
            if p.index in para_pages:
                p.page = para_pages[p.index]
            else:
                p.page = current_page

        return paragraphs

    def _process_with_pdf(
        self,
        paragraphs: List[ParsedParagraph],
        pdf_path: str,
    ) -> List[ParsedParagraph]:
        """PDF dosyasındaki sayfa metinleri ile replikleri eşleştirerek sayfa atar."""
        import pdfplumber

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {pdf_path}")

        with pdfplumber.open(pdf_path) as pdf:
            pdf_page_texts = [p.extract_text() or "" for p in pdf.pages]

        last_page = 1
        for p in paragraphs:
            if p.dialogue and p.speaker:
                search_needle = p.dialogue[:25].strip("- ").strip()
                if search_needle:
                    for page_num in range(last_page, len(pdf_page_texts) + 1):
                        if search_needle in pdf_page_texts[page_num - 1]:
                            last_page = page_num
                            break
            p.page = last_page

        return paragraphs


# Alias for compatibility with Task brief
Paginator = DocumentPaginator
