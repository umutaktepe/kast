# Dublaj Çevirisi DOCX Kast Çıkarma Sistemi (Kast 2.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dublaj çeviri metinlerini (.docx) doğrudan okuyarak başlık ve meta verileri (FİLMİN ADI, ÇEVİRMEN vb.) repliklerden ayıran, karakterlerin replik sayılarını ve geçtikleri sayfaları hatasız çıkaran, oluşturulan kast tablosunu dökümanın sonuna yeni sayfa olarak otomatik ekleyen modern bir Python aracı geliştirmek.

**Architecture:** Modüler 4 katmanlı mimari: (1) `parser`: DOCX OpenXML ve python-docx üzerinden sekme/tire ve metadata hiyerarşisini ayrıştıran motor, (2) `paginator`: Doğrudan XML sayfa kesmelerini (`w:lastRenderedPageBreak`), harici dönüştürücüleri (varsa) ve Arial 11pt / 1.5 satır aralığı / kenar boşluğu parametrelerine dayalı yüksek hassasiyetli Python mizanpaj simülasyonunu birleştiren çok katmanlı sayfa tespit motoru, (3) `table_writer`: Word uyumlu tam kenarlıklı (Table Grid) 4 sütunlu kast tablosunu oluşturup orijinal dökümanın sonuna yeni sayfa olarak ekleyen bileşen, (4) `cli`: Terminalden sürükle-bırak veya parametre ile çalışan Türkçe kullanıcı arayüzü.

**Tech Stack:** Python 3.10+, `python-docx`, `lxml` / OpenXML, `Pillow` (ImageFont font metrikleri için), `pdfplumber` (opsiyonel PDF/dönüştürme desteği için), `pytest`.

**Spec:** Dublaj çeviri standardı formatı:
- Başlık alanı: `FİLMİN ADI <TAB> Değer`, `ÇEVİRMEN <TAB> Değer` vb.
- Süre kodları: Paragraf başında tek başına `00.41`, `01.59` vb.
- Replikler: `KARAKTER ADI <TAB> - Replik metni`
- Çıktı: `Karakter` | `Replik Sayısı` | `Repliklerin Geçtiği Sayfalar` | `Notlar` tablosu.

## Global Constraints

- Orijinal dökümandaki hiçbir metin, diyalog veya biçimlendirme bozulmamalıdır.
- Tanımlayıcı başlıklar (`FİLMİN ADI`, `ÇEVİRMEN` vb.) kesinlikle karaktere dönüştürülmemelidir.
- Tablo sıralaması varsayılan olarak metindeki ilk görünme sırasına (Order of Appearance) göre olmalıdır (ekran görüntüsündeki gibi).
- Kod bağımsız çalışabilir olmalı, sistemde LibreOffice/Word bulunmasa dahi saf Python ile sayfa tespiti ve kast çıkarma yapabilmelidir.
- Çıktı dosyası orijinal dökümanın üzerine yazmak yerine varsayılan olarak `<dosya_adi>_kast.docx` olarak kaydedilmeli (veya opsiyonel `--in-place` ile orijinal dökümana eklenebilmeli), böylece orijinal döküman her zaman güvende kalmalıdır.

---

### Task 1: Veri Modelleri ve Temel Tiplerin Oluşturulması

**Files:**
- Create: `src/__init__.py`
- Create: `src/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: Yok (temel veri yapıları)
- Produces: `DialogueLine`, `CharacterStats`, `CastExtractionResult` veri sınıfları

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from src.models import DialogueLine, CharacterStats, CastExtractionResult

def test_dialogue_line_creation():
    line = DialogueLine(
        speaker="SAL",
        text="Hallettim.",
        timecode="02.45",
        page=1,
        paragraph_index=10
    )
    assert line.speaker == "SAL"
    assert line.text == "Hallettim."
    assert line.timecode == "02.45"
    assert line.page == 1
    assert line.paragraph_index == 10

def test_character_stats_aggregation():
    stats = CharacterStats(name="SAL", first_seen_order=2)
    stats.add_line(page=1)
    stats.add_line(page=2)
    stats.add_line(page=1)
    
    assert stats.line_count == 3
    assert stats.pages == {1, 2}
    assert stats.formatted_pages == "1, 2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py`
Expected: FAIL with "ModuleNotFoundError: No module named 'src'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/models.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

@dataclass
class DialogueLine:
    speaker: str
    text: str
    timecode: Optional[str] = None
    page: int = 1
    paragraph_index: int = 0

@dataclass
class CharacterStats:
    name: str
    first_seen_order: int
    line_count: int = 0
    pages: Set[int] = field(default_factory=set)
    notes: str = ""

    def add_line(self, page: int):
        self.line_count += 1
        self.pages.add(page)

    @property
    def formatted_pages(self) -> str:
        return ", ".join(str(p) for p in sorted(self.pages))

@dataclass
class CastExtractionResult:
    characters: List[CharacterStats]
    metadata: Dict[str, str] = field(default_factory=dict)
    total_lines: int = 0
    total_pages: int = 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py`
Expected: PASS

- [ ] **Step 5: Git commit / checkpoint**

Create `src/__init__.py` and verify all tests pass.

---

### Task 2: DOCX Dublaj Formatı Ayrıştırıcı Motoru (Parser)

**Files:**
- Create: `src/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: `DialogueLine`, `src/models.py`
- Produces: `DubbingDocxParser.parse_paragraphs(docx_path) -> (metadata: dict, raw_lines: list[RawLine])`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parser.py
from src.parser import DubbingDocxParser

def test_detect_metadata_vs_dialogue():
    parser = DubbingDocxParser()
    
    # Metadata örneği (tire içermeyen veya bilinen header anahtarları)
    is_meta, key, val = parser.parse_header_line("FİLMİN ADI\tANOTHER END")
    assert is_meta is True
    assert key == "FİLMİN ADI"
    assert val == "ANOTHER END"

    # Diyalog örneği (sekme ve ardından tire ile başlayan satır)
    is_dial, char, text = parser.parse_dialogue_line("SAL\t- Hallettim.")
    assert is_dial is True
    assert char == "SAL"
    assert text == "- Hallettim."

def test_timecode_detection():
    parser = DubbingDocxParser()
    assert parser.is_timecode("01.59") is True
    assert parser.is_timecode("01.00.06") is True
    assert parser.is_timecode("01:23") is True
    assert parser.is_timecode("MC COOKIE") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser.py`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.parser'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/parser.py
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from docx import Document

KNOWN_METADATA_KEYS = {
    "FİLMİN ADI", "FİLM ADI", "DİZİ ADI", "DİZİ", "ÇEVİRMEN", "ÇEVİREN",
    "SEZON", "BÖLÜM", "BÖLÜM ADI", "KAYIT", "STÜDYO", "YÖNETMEN",
    "SESLENDİRME YÖNETMENİ", "TARİH", "TITLE", "TRANSLATOR"
}

TIMECODE_REGEX = re.compile(r"^\d{2}[\.:]\d{2}(?:[\.:]\d{2})?$")

@dataclass
class ParsedParagraph:
    index: int
    text: str
    speaker: Optional[str] = None
    dialogue: Optional[str] = None
    timecode: Optional[str] = None
    is_metadata: bool = False
    is_timecode: bool = False
    meta_key: Optional[str] = None
    meta_value: Optional[str] = None

class DubbingDocxParser:
    def __init__(self):
        pass

    def is_timecode(self, text: str) -> bool:
        cleaned = text.strip()
        return bool(TIMECODE_REGEX.match(cleaned))

    def parse_header_line(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        text_clean = text.strip()
        if not text_clean:
            return False, None, None
        
        parts = text_clean.split("\t", 1)
        if len(parts) == 2:
            key, val = parts[0].strip(), parts[1].strip()
            if key in KNOWN_METADATA_KEYS or any(key.startswith(k) for k in KNOWN_METADATA_KEYS):
                return True, key, val
            if not val.startswith("-") and key.isupper() and len(key.split()) <= 4:
                # Muhtemel başlık tanımlayıcısı
                if any(m in key for m in ["AD", "ÇEVİR", "TARİH", "METİN", "PROJE", "KOD"]):
                    return True, key, val
        return False, None, None

    def parse_dialogue_line(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        text_clean = text.strip()
        if not text_clean:
            return False, None, None
            
        parts = text_clean.split("\t", 1)
        if len(parts) == 2:
            speaker, dialogue = parts[0].strip(), parts[1].strip()
            # Standart format: Diyalog tire ile başlar (- Replik)
            if dialogue.startswith("-") or dialogue.startswith("–") or dialogue.startswith("—"):
                # Karakter ismi temizliği (büyük harf ve varsa gereksiz işaretler)
                speaker_clean = speaker.strip(" \t:.-")
                return True, speaker_clean, dialogue
        return False, None, None

    def parse_document_paragraphs(self, doc: Document) -> List[ParsedParagraph]:
        parsed = []
        current_timecode = None
        
        for idx, p in enumerate(doc.paragraphs):
            text = p.text.strip()
            if not text:
                continue
            
            # 1. Süre kodu kontrolü
            if self.is_timecode(text):
                current_timecode = text
                parsed.append(ParsedParagraph(index=idx, text=text, is_timecode=True, timecode=text))
                continue
            
            # 2. Başlık / Metadata kontrolü
            is_meta, m_key, m_val = self.parse_header_line(p.text)
            if is_meta:
                parsed.append(ParsedParagraph(index=idx, text=text, is_metadata=True, meta_key=m_key, meta_value=m_val))
                continue
            
            # 3. Diyalog kontrolü
            is_dial, speaker, dial_text = self.parse_dialogue_line(p.text)
            if is_dial:
                parsed.append(ParsedParagraph(
                    index=idx,
                    text=text,
                    speaker=speaker,
                    dialogue=dial_text,
                    timecode=current_timecode
                ))
            else:
                # Bilinmeyen / düz metin paragrafı
                parsed.append(ParsedParagraph(index=idx, text=text))
                
        return parsed
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser.py`
Expected: PASS

- [ ] **Step 5: Verify against example document**

Add an integration test in `tests/test_parser.py` testing against `example/PORORO: SWEET CASTLE ADVENTURE.docx` to verify that 982 dialogue lines and 0 metadata false positives are produced.

---

### Task 3: Çok Katmanlı Sayfa Numarası Hesaplayıcı (Paginator Engine)

**Files:**
- Create: `src/paginator.py`
- Test: `tests/test_paginator.py`

**Interfaces:**
- Consumes: `ParsedParagraph`, `Document`
- Produces: `Paginator.assign_pages(doc: Document, parsed_paragraphs: list[ParsedParagraph]) -> list[ParsedParagraph]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_paginator.py
from src.paginator import PurePythonLayoutPaginator
from src.parser import ParsedParagraph

def test_layout_paginator_initialization():
    paginator = PurePythonLayoutPaginator(page_height_pt=792, top_margin_pt=72, bottom_margin_pt=72)
    assert paginator.printable_height == 648

def test_layout_paginator_advance():
    paginator = PurePythonLayoutPaginator(page_height_pt=792, top_margin_pt=72, bottom_margin_pt=72)
    p1 = ParsedParagraph(index=0, text="Header")
    p2 = ParsedParagraph(index=1, text="Dialogue 1", speaker="SAL", dialogue="- Test")
    
    assigned = paginator.paginate_paragraphs([p1, p2])
    assert len(assigned) == 2
    assert assigned[0].page == 1
    assert assigned[1].page == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_paginator.py`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.paginator'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/paginator.py
import math
from typing import List, Optional
from docx import Document
from PIL import ImageFont
from src.parser import ParsedParagraph

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
        dialogue_indent_pt: float = 108.0, # 1.5 inch hanging indent
        font_path: str = "/usr/share/fonts/msfonts/Arial.TTF",
        font_size_pt: int = 11,
        line_spacing_multiplier: float = 1.5,
        space_after_pt: float = 10.0
    ):
        self.page_height = page_height_pt
        self.page_width = page_width_pt
        self.printable_height = page_height_pt - top_margin_pt - bottom_margin_pt
        self.printable_width = page_width_pt - left_margin_pt - right_margin_pt
        self.dialogue_width = self.printable_width - dialogue_indent_pt
        self.space_after_pt = space_after_pt
        self.single_line_height = font_size_pt * line_spacing_multiplier
        
        try:
            self.font = ImageFont.truetype(font_path, font_size_pt)
        except Exception:
            self.font = None

    def estimate_lines(self, text: str, max_width_pt: float) -> int:
        if not text:
            return 1
        if self.font:
            total_width = self.font.getlength(text)
            if total_width <= max_width_pt:
                return 1
            # Kelime bazlı sarma hesabı
            words = text.split(" ")
            lines = 1
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if self.font.getlength(test_line) <= max_width_pt:
                    current_line = test_line
                else:
                    lines += 1
                    current_line = word
            return max(1, lines)
        else:
            # Fallback: Ortalama karakter genişliği (~6.0 pt for Arial 11)
            chars_per_line = max(1, int(max_width_pt / 6.0))
            return max(1, math.ceil(len(text) / chars_per_line))

    def paginate_paragraphs(self, paragraphs: List[ParsedParagraph]) -> List[ParsedParagraph]:
        current_page = 1
        current_y = 0.0

        for p in paragraphs:
            # Paragraf yüksekliğini hesapla
            if p.is_timecode:
                lines = 1
                col_width = self.printable_width
            elif p.speaker and p.dialogue:
                # Diyalog metninin satır sayısını hesapla
                lines = self.estimate_lines(p.dialogue, self.dialogue_width)
            else:
                lines = self.estimate_lines(p.text, self.printable_width)

            para_height = (lines * self.single_line_height) + self.space_after_pt

            # Sayfa taşma kontrolü
            if current_y + para_height > self.printable_height and current_y > 0:
                current_page += 1
                current_y = 0.0

            p.page = current_page
            current_y += para_height

        return paragraphs

class DocumentPaginator:
    """
    Çok katmanlı sayfa tespit koordinatörü:
    1. Varsa XML soft page break'lerini okur.
    2. Varsa harici PDF verisini kullanır.
    3. Saf Python layout motoruyla sayfaları hesaplar.
    """
    def __init__(self, doc: Optional[Document] = None):
        self.doc = doc
        self.layout_paginator = PurePythonLayoutPaginator()

    def process(self, paragraphs: List[ParsedParagraph], pdf_path: Optional[str] = None) -> List[ParsedParagraph]:
        # Tier 1: Harici PDF verilmişse veya dönüştürülmüşse pdfplumber ile eşleştir
        if pdf_path:
            return self._process_with_pdf(paragraphs, pdf_path)
            
        # Tier 2: Saf Python mizanpaj hesabı
        return self.layout_paginator.paginate_paragraphs(paragraphs)

    def _process_with_pdf(self, paragraphs: List[ParsedParagraph], pdf_path: str) -> List[ParsedParagraph]:
        import pdfplumber
        # PDF'teki sayfalara göre satır eşleştirmesi
        with pdfplumber.open(pdf_path) as pdf:
            pdf_page_texts = [p.extract_text() or "" for p in pdf.pages]

        # Her diyalog paragrafını PDF sayfa metinlerinde ara
        last_page = 1
        for p in paragraphs:
            if not p.dialogue or not p.speaker:
                continue
            search_needle = p.dialogue[:25].strip("- ")
            found = False
            for page_num in range(last_page, len(pdf_page_texts) + 1):
                if search_needle in pdf_page_texts[page_num - 1]:
                    p.page = page_num
                    last_page = page_num
                    found = True
                    break
            if not found:
                p.page = last_page
        return paragraphs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_paginator.py`
Expected: PASS

---

### Task 4: Kast Tablosu Oluşturucu ve DOCX Entegratörü (Table Writer)

**Files:**
- Create: `src/table_writer.py`
- Test: `tests/test_table_writer.py`

**Interfaces:**
- Consumes: `CastExtractionResult`, `Document`
- Produces: `append_cast_table(doc: Document, result: CastExtractionResult) -> Document`, `save_result(doc: Document, output_path: str)`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_table_writer.py
from docx import Document
from src.models import CharacterStats, CastExtractionResult
from src.table_writer import CastTableWriter

def test_table_generation():
    doc = Document()
    writer = CastTableWriter()
    
    char1 = CharacterStats(name="K KOMŞU", first_seen_order=1)
    char1.add_line(page=1)
    char1.add_line(page=2)
    
    result = CastExtractionResult(characters=[char1], total_lines=2, total_pages=2)
    
    writer.append_cast_table(doc, result)
    
    # Dökümana tablo eklenmiş olmalı
    assert len(doc.tables) == 1
    table = doc.tables[0]
    assert len(table.rows) == 2 # 1 başlık + 1 veri
    assert table.rows[0].cells[0].text == "Karakter"
    assert table.rows[0].cells[1].text == "Replik Sayısı"
    assert table.rows[0].cells[2].text == "Repliklerin Geçtiği Sayfalar"
    assert table.rows[0].cells[3].text == "Notlar"
    
    assert table.rows[1].cells[0].text == "K KOMŞU"
    assert table.rows[1].cells[1].text == "2"
    assert table.rows[1].cells[2].text == "1, 2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_table_writer.py`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.table_writer'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/table_writer.py
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from src.models import CastExtractionResult

def set_cell_border(cell, **kwargs):
    """
    w:tcBorders XML elemanını hücreye uygular.
    Örnek kwargs: top={"sz": 4, "val": "single", "color": "000000"}
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = OxmlElement(tag)
            element.set(qn('w:val'), edge_data.get('val', 'single'))
            element.set(qn('w:sz'), str(edge_data.get('sz', 4)))
            element.set(qn('w:space'), '0')
            element.set(qn('w:color'), edge_data.get('color', '000000'))
            tcBorders.append(element)
    tcPr.append(tcBorders)

class CastTableWriter:
    def __init__(self):
        pass

    def append_cast_table(self, doc: Document, result: CastExtractionResult) -> None:
        # Metnin sonuna yeni sayfa kesmesi ekle
        doc.add_page_break()

        # Tablo başlığı
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run("KAST TABLOSU")
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = "Arial"

        # 4 sütunlu tablo oluştur
        table = doc.add_table(rows=1, cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Sütun genişlikleri (Karakter, Replik Sayısı, Sayfalar, Notlar)
        col_widths = [Inches(1.8), Inches(1.1), Inches(2.3), Inches(1.3)]

        # Başlık satırı
        hdr_cells = table.rows[0].cells
        headers = ["Karakter", "Replik Sayısı", "Repliklerin Geçtiği Sayfalar", "Notlar"]
        border_spec = {"val": "single", "sz": 4, "color": "000000"}
        all_borders = {k: border_spec for k in ['top', 'left', 'bottom', 'right']}

        for i, text in enumerate(headers):
            hdr_cells[i].text = text
            hdr_cells[i].width = col_widths[i]
            set_cell_border(hdr_cells[i], **all_borders)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if p.runs:
                p.runs[0].font.bold = True
                p.runs[0].font.name = "Arial"
                p.runs[0].font.size = Pt(11)

        # Veri satırları
        for char in result.characters:
            row_cells = table.add_row().cells
            row_cells[0].text = char.name
            row_cells[1].text = str(char.line_count)
            row_cells[2].text = char.formatted_pages
            row_cells[3].text = char.notes

            for i in range(4):
                row_cells[i].width = col_widths[i]
                set_cell_border(row_cells[i], **all_borders)
                p = row_cells[i].paragraphs[0]
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(2)
                if p.runs:
                    p.runs[0].font.name = "Arial"
                    p.runs[0].font.size = Pt(10)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_table_writer.py`
Expected: PASS

---

### Task 5: Ana Uygulama Orkestrasyonu ve CLI / Sürükle-Bırak Entegrasyonu

**Files:**
- Modify: `kast.py`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: `src.parser`, `src.paginator`, `src.table_writer`, `src.models`
- Produces: CLI çalıştırılabilir `python kast.py [dosya.docx]`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
import os
import shutil
from docx import Document
from kast import process_cast_document

def test_full_pipeline_on_example(tmp_path):
    src_file = "example/PORORO: SWEET CASTLE ADVENTURE.docx"
    assert os.path.exists(src_file)
    
    target_copy = tmp_path / "test_pororo.docx"
    shutil.copy(src_file, target_copy)
    
    output_path = process_cast_document(str(target_copy))
    assert os.path.exists(output_path)
    
    # Çıktı dosyasını doğrula
    doc = Document(output_path)
    assert len(doc.tables) >= 1
    table = doc.tables[-1]
    
    # Karakter sayısını doğrula (Pororo'da en az 30 karakter)
    assert len(table.rows) > 30
    
    # İlk karakterin PORORO veya ilk konuşan karakter olduğunu doğrula
    char_names = [row.cells[0].text for row in table.rows[1:]]
    assert "MC COOKIE" in char_names
    assert "PORORO" in char_names
    assert "SUGAR QUEEN" in char_names
    
    # Tanımlayıcıların karaktere dönüşmediğini doğrula
    assert "FİLMİN ADI" not in char_names
    assert "ÇEVİRMEN" not in char_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_integration.py`
Expected: FAIL (process_cast_document henüz tanımlı değil)

- [ ] **Step 3: Implement `kast.py`**

```python
# kast.py
import os
import sys
from typing import Optional
from docx import Document
from collections import OrderedDict
from src.parser import DubbingDocxParser
from src.paginator import DocumentPaginator
from src.table_writer import CastTableWriter
from src.models import CharacterStats, CastExtractionResult

def process_cast_document(
    docx_path: str,
    output_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    sort_by: str = "appearance"
) -> str:
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Dosya bulunamadı: {docx_path}")

    print(f"[*] Döküman yükleniyor: {docx_path}")
    doc = Document(docx_path)

    # 1. Paragrafları ayrıştır (Diyalog, Süre Kodu, Metadata)
    parser = DubbingDocxParser()
    parsed_paras = parser.parse_document_paragraphs(doc)

    dialogue_paras = [p for p in parsed_paras if p.speaker and p.dialogue]
    print(f"[+] Toplam {len(parsed_paras)} paragraf incelendi.")
    print(f"[+] {len(dialogue_paras)} replik tespit edildi.")

    # 2. Sayfa numaralandırmasını hesapla
    paginator = DocumentPaginator(doc)
    assigned_paras = paginator.process(parsed_paras, pdf_path=pdf_path)

    # 3. Karakter istatistiklerini derle (Sıralama: İlk görünme sırasına göre)
    characters_map = OrderedDict()
    appearance_counter = 0

    for p in assigned_paras:
        if not p.speaker or not p.dialogue:
            continue
        if p.speaker not in characters_map:
            appearance_counter += 1
            characters_map[p.speaker] = CharacterStats(
                name=p.speaker,
                first_seen_order=appearance_counter
            )
        characters_map[p.speaker].add_line(page=p.page or 1)

    char_list = list(characters_map.values())
    if sort_by == "count":
        char_list.sort(key=lambda x: x.line_count, reverse=True)
    elif sort_by == "name":
        char_list.sort(key=lambda x: x.name)
    else: # appearance
        char_list.sort(key=lambda x: x.first_seen_order)

    print(f"[+] {len(char_list)} farklı karakter tespit edildi.")

    result = CastExtractionResult(
        characters=char_list,
        total_lines=len(dialogue_paras),
        total_pages=max((p.page for p in assigned_paras if p.page), default=1)
    )

    # 4. Kast tablosunu dökümanın sonuna ekle
    writer = CastTableWriter()
    writer.append_cast_table(doc, result)

    # 5. Kaydet
    if not output_path:
        base, ext = os.path.splitext(docx_path)
        output_path = f"{base}_kast{ext}"

    doc.save(output_path)
    print(f"[✓] Başarıyla tamamlandı! Kast tablosu eklendi:")
    print(f"    -> {output_path}")
    return output_path

def main():
    print("=" * 60)
    print(" DUBLAJ ÇEVİRİSİ KAST ÇIKARMA PROGRAMI (Kast 2.0)")
    print("=" * 60)

    if len(sys.argv) > 1:
        docx_file = sys.argv[1].strip("'\"")
    else:
        docx_file = input("Lütfen çeviri DOCX dosyasını buraya sürükleyip bırakın ve Enter'a basın:\n> ").strip("'\"")

    if not docx_file:
        print("Hata: Dosya belirtilmedi.")
        sys.exit(1)

    try:
        process_cast_document(docx_file)
    except Exception as e:
        print(f"\n[!] Bir hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run integration tests to verify they pass**

Run: `pytest tests/test_integration.py`
Expected: PASS

- [ ] **Step 5: Verify directly on example file**

Run: `python3 kast.py "example/PORORO: SWEET CASTLE ADVENTURE.docx"`
Inspect generated `example/PORORO: SWEET CASTLE ADVENTURE_kast.docx`.

---

### Task 6: Doğrulama, Belgelendirme ve Kullanıcı Kılavuzu

**Files:**
- Create: `README.md`
- Test: Tüm testlerin çalıştırılması (`pytest`)

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`
Expected: All tests pass.

- [ ] **Step 2: Create README.md documentation**

Belgelendirilecek konular:
- Programın ne yaptığı ve nasıl çalıştığı
- DOCX üzerinden doğrudan çalışma prensibi
- Karakterlerin sıralama kuralı
- Tablo biçimi ve kolon açıklamaları
- Terminalden sürükle-bırak kullanımı
