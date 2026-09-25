"""Direct PDF Dubbing Script Parser Engine for Kast."""

import os
import re
from collections import OrderedDict
from typing import Callable, List, Optional, Tuple
import pdfplumber
from docx import Document

from src.models import CastExtractionResult, CharacterStats
from src.parser import KNOWN_METADATA_KEYS, TIMECODE_REGEX, turkish_upper
from src.table_writer import CastTableWriter


class PageSet(set):
    """Set of page numbers that supports equality comparison with lists, tuples, and sets."""

    def __eq__(self, other):
        if isinstance(other, (list, tuple)):
            return sorted(self) == sorted(other)
        return super().__eq__(other)


class DubbingPdfParser:
    """Parses dubbing script PDF files directly page-by-page."""

    DIALOGUE_REGEX = re.compile(r"^([^\t\-–—]{2,35}?)\s*(?:\t|\s{2,}|\s*[-–—]\s*)(.+)$")

    def __init__(self) -> None:
        self.known_metadata_keys = set(KNOWN_METADATA_KEYS)

    def _is_metadata(self, text: str) -> bool:
        upper = turkish_upper(text)
        if any(key in upper for key in self.known_metadata_keys):
            return True
        return any(k in upper for k in ["FİLM", "DİZİ", "ÇEVİR", "SEZON", "BÖLÜM", "KAYIT", "STÜDYO", "YÖNETMEN", "TARİH", "TITLE"])

    def parse_pdf(
        self,
        pdf_path: str,
        sort_by: str = "appearance",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> CastExtractionResult:
        """Extracts cast statistics from a PDF dubbing script with 100% native page accuracy."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {pdf_path}")

        characters_map: OrderedDict[str, CharacterStats] = OrderedDict()
        total_dialogue_lines = 0
        appearance_counter = 0
        total_pages = 1

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages) if pdf.pages else 1
            for page_idx, page in enumerate(pdf.pages, start=1):
                if progress_callback:
                    progress_callback(page_idx, total_pages, f"Sayfa {page_idx}/{total_pages} taranıyor...")

                page_text = page.extract_text() or ""
                lines = page_text.splitlines()

                for raw_line in lines:
                    line = raw_line.strip()
                    if not line or line.isdigit() or TIMECODE_REGEX.match(line):
                        continue

                    # Try tab-separated dialogue: SPEAKER \t [-] DIALOGUE
                    parts = line.split("\t", 1)
                    speaker, dialogue = None, None

                    if len(parts) == 2:
                        spk_candidate = parts[0].strip(" :.-")
                        dial_candidate = parts[1].strip()
                        if (dial_candidate.startswith("-") or dial_candidate.startswith("–") or dial_candidate.startswith("—")) and not self._is_metadata(spk_candidate):
                            speaker = spk_candidate
                            dialogue = dial_candidate
                    else:
                        # Regex match for 'SPEAKER - DIALOGUE'
                        m = re.match(r"^([^\t\-–—]{2,35}?)\s*[-–—]\s*(.+)$", line)
                        if m:
                            spk_candidate = m.group(1).strip(" :.-")
                            dial_candidate = m.group(2).strip()
                            if not self._is_metadata(spk_candidate) and len(spk_candidate.split()) <= 4:
                                speaker = spk_candidate
                                dialogue = dial_candidate

                    if speaker and dialogue:
                        total_dialogue_lines += 1
                        if speaker not in characters_map:
                            appearance_counter += 1
                            characters_map[speaker] = CharacterStats(
                                name=speaker,
                                first_seen_order=appearance_counter,
                                pages=PageSet(),
                            )
                        characters_map[speaker].add_line(page=page_idx)

        char_list = list(characters_map.values())
        if sort_by == "count":
            char_list.sort(key=lambda x: x.line_count, reverse=True)
        elif sort_by == "name":
            char_list.sort(key=lambda x: x.name)
        else:
            char_list.sort(key=lambda x: x.first_seen_order)

        return CastExtractionResult(
            characters=char_list,
            total_lines=total_dialogue_lines,
            total_pages=total_pages,
        )


def process_pdf_document(
    pdf_path: str,
    output_path: Optional[str] = None,
    sort_by: str = "appearance",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[str, CastExtractionResult]:
    """Processes a PDF script and outputs a standalone Word .docx file containing the cast table."""
    parser = DubbingPdfParser()
    result = parser.parse_pdf(pdf_path, sort_by=sort_by, progress_callback=progress_callback)

    if not output_path:
        base, _ = os.path.splitext(pdf_path)
        output_path = f"{base}_kast.docx"

    writer = CastTableWriter()
    doc = Document()
    writer.append_cast_table(doc, result, add_page_break=False)
    doc.save(output_path)

    return output_path, result
