"""Multi-tier document paginator engine for Kast."""

import math
import os
from typing import List, Optional
from docx import Document
from PIL import ImageFont

from src.parser import ParsedParagraph

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


class PurePythonLayoutPaginator:
    """
    DOCX dosyasının sectPr (sayfa boyutu, kenar boşlukları) ve 
    paragraf stil parametrelerini (Arial 11pt, 1.5 satır aralığı, 10pt son boşluk, 1.5 inç girinti)
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
        font_path: str = "/usr/share/fonts/msfonts/Arial.TTF",
        font_size_pt: int = 11,
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
        self.space_after_pt = space_after_pt
        self.single_line_height = font_size_pt * line_spacing_multiplier
        self.font_size_pt = font_size_pt

        # Font yükleme (varsayılan ve yedek yollar)
        self.font: Optional[ImageFont.FreeTypeFont] = None
        candidates = [font_path] + [c for c in DEFAULT_FONT_CANDIDATES if c != font_path]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                try:
                    self.font = ImageFont.truetype(candidate, font_size_pt)
                    break
                except Exception:
                    continue

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
            # Fallback: Ortalama karakter genişliği (~6.0 pt for Arial 11)
            chars_per_line = max(1, int(max_width_pt / 6.0))
            return max(1, math.ceil(len(text) / chars_per_line))

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
            if p.is_timecode:
                lines = 1
            elif p.speaker and p.dialogue:
                lines = self.estimate_lines(p.dialogue, self.dialogue_width)
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
            self.layout_paginator = PurePythonLayoutPaginator(
                page_height_pt=sec.page_height.pt,
                page_width_pt=sec.page_width.pt,
                top_margin_pt=sec.top_margin.pt,
                bottom_margin_pt=sec.bottom_margin.pt,
                left_margin_pt=sec.left_margin.pt,
                right_margin_pt=sec.right_margin.pt,
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
                if not doc_p.text.strip():
                    # Yalnızca sayfa sonu içeren boş paragraf
                    current_page += len(break_elements)
                    para_pages[doc_idx] = current_page
                else:
                    # Metin içeren paragraf içinde sayfa sonu
                    current_page += len(break_elements)
                    para_pages[doc_idx] = current_page
            else:
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
