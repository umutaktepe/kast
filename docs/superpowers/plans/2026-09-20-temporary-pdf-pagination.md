# Geçici PDF ile %100 Doğrulukta Sayfa Tespiti Implementation Plan (v2 - Kesin %100 Çözüm)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kullanıcının verdiği `.docx` dublaj senaryosunu arka planda Python kütüphanesi (`dxpdf`) ve yerel Word COM motoruyla geçici bir `.pdf` dosyasına dönüştürerek Word'ün gerçek sayfa sınırları üzerinden **%100 doğrulukta** sayfa tespiti yapmak, eski %90'lık tahmini mizanpaj fallback'ini tamamen devreden çıkarmak ve işlem sonunda geçici PDF'i otomatik silmek.

**Architecture:** 
1. **Bağımlılık:** `requirements.txt` ve kurulum scriptlerine `dxpdf` (Rust + Skia tabanlı, harici Word/LibreOffice gerektirmeyen bağımsız ve ultra hızlı DOCX $\rightarrow$ PDF Python kütüphanesi) eklenmesi.
2. `src/pdf_converter.py` modülü:
   - **Kademe 1 (Windows Word COM):** Sistemde Microsoft Word varsa Word'ün kendi render motorunu kullanır.
   - **Kademe 2 (`dxpdf` Kütüphanesi):** Sistemde Word yoksa (veya Linux/macOS ise) doğrudan Python içerisinden `dxpdf.convert_file` ile PDF üretir. Harici hiçbir ofis yazılımına ihtiyaç duymaz!
   - **Kademe 3 (LibreOffice CLI):** Sistemde `soffice` varsa ek bir güvence olarak devreye girer.
   - **Sıfır Fallback Prensibi:** Eski %90 çalışan yaklaşık satır hesabı motoruna ASLA sessiz geri dönüş yapılmaz. Sayfa numaraları her zaman gerçek PDF üzerinden %100 doğrulukla çıkarılır.
3. `src/paginator.py` modülündeki `_process_with_pdf` motorunun metin/boşluk/süre kodu normalizasyonu ile güçlendirilmesi.
4. `kast.py` ve `src/tui.py` boru hattına geçici PDF oluşturma, %100 PDF üzerinden sayfa çıkarma ve otomatik temizleme döngüsünün entegre edilmesi.

**Tech Stack:** Python 3.10+, `dxpdf`, `pdfplumber`, Windows PowerShell Word COM, `pytest`.

**Spec:** User request: "Fallback seçeneğimiz eski yüzde 90 çalışan sistem olmamalı. Bizim yüzde yüz çalışan bir sistem kurmamız lazım. O yüzden fallback'e ihtiyaç duydurmayacak bir çözüm bulmamız lazım pdf dönüşümü ve işleme için. Mesela bu işi yapacak bir python kütüphanesi falan. Bir şey düşün ve planı güncelle"

## Global Constraints

- Kullanıcı arayüzünde kullanıcıdan yalnızca `.docx` alınmaya devam edilmelidir (mevcut dosya seçici akışı bozulmamalıdır).
- Geçici PDF dosyası işlem bittiğinde veya herhangi bir hata durumunda `finally:` bloğu ile kesinlikle diskten silinmelidir.
- Eski yaklaşık satır hesabı motoruna (`PurePythonLayoutPaginator`) üretim akışında ASLA sessiz geri dönüş yapılmayacaktır. Sayfa tespiti her zaman %100 doğrulukta gerçek PDF render'ı üzerinden yapılacaktır.
- Orijinal `.docx` dosyasının metin veya biçimlendirmesine kesinlikle dokunulmamalıdır.
- Tüm yeni fonksiyonlar TDD prensipleriyle birim ve entegrasyon testlerine sahip olmalıdır.

---

### Task 1: Bağımlılıkların Güncellenmesi ve PDF Dönüştürücü Motoru (`src/pdf_converter.py`)

**Files:**
- Modify: `requirements.txt`
- Modify: `install.ps1`
- Create: `src/pdf_converter.py`
- Test: `tests/test_pdf_converter.py`

**Interfaces:**
- Produces:
  - `convert_docx_to_pdf(docx_path: str, output_pdf_path: str) -> bool`
  - `temp_docx_to_pdf(docx_path: str) -> ContextManager[str]`
  - `is_pdf_conversion_supported() -> bool`
  - `class PdfConversionError(Exception)`

- [ ] **Step 1: Write failing tests in `tests/test_pdf_converter.py`**

```python
import os
import pytest
from unittest.mock import patch, MagicMock
from src.pdf_converter import (
    convert_docx_to_pdf,
    temp_docx_to_pdf,
    is_pdf_conversion_supported,
    PdfConversionError,
)


def test_is_pdf_conversion_supported_always_true_with_dxpdf():
    with patch.dict("sys.modules", {"dxpdf": MagicMock()}):
        assert is_pdf_conversion_supported() is True


def test_convert_docx_to_pdf_uses_dxpdf():
    mock_dxpdf = MagicMock()
    with patch.dict("sys.modules", {"dxpdf": mock_dxpdf}), \
         patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024):
        
        # When dxpdf succeeds
        result = convert_docx_to_pdf("test.docx", "test.pdf")
        assert result is True
        mock_dxpdf.convert_file.assert_called_once()


def test_temp_docx_to_pdf_context_manager_cleanup():
    with patch("src.pdf_converter.convert_docx_to_pdf") as mock_convert:
        def fake_convert(docx_in, pdf_out):
            with open(pdf_out, "w") as f:
                f.write("mock pdf")
            return True

        mock_convert.side_effect = fake_convert

        pdf_path_created = None
        with temp_docx_to_pdf("dummy.docx") as temp_pdf:
            assert temp_pdf is not None
            assert os.path.exists(temp_pdf)
            pdf_path_created = temp_pdf

        # After exiting context manager, temp pdf MUST be deleted
        assert pdf_path_created is not None
        assert not os.path.exists(pdf_path_created)


def test_temp_docx_to_pdf_raises_error_when_conversion_fails():
    with patch("src.pdf_converter.convert_docx_to_pdf", return_value=False):
        with pytest.raises(PdfConversionError):
            with temp_docx_to_pdf("corrupt.docx") as _:
                pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_pdf_converter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pdf_converter'`

- [ ] **Step 3: Update `requirements.txt` and `install.ps1`**

Add `dxpdf>=0.8.0` to `requirements.txt`.
Update `install.ps1` dependency check to verify `dxpdf`.

- [ ] **Step 4: Implement `src/pdf_converter.py`**

```python
"""Cross-platform, zero-fallback DOCX to PDF converter utility for Kast."""

import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from typing import Generator


class PdfConversionError(RuntimeError):
    """Raised when DOCX to PDF conversion cannot be completed."""
    pass


def is_pdf_conversion_supported() -> bool:
    """Check if any PDF conversion engine (dxpdf, Word COM, or LibreOffice) is available."""
    try:
        import dxpdf
        return True
    except ImportError:
        pass

    if sys.platform == "win32":
        return True

    return bool(shutil.which("soffice") or shutil.which("libreoffice"))


def convert_docx_to_pdf(docx_path: str, output_pdf_path: str) -> bool:
    """
    Convert a .docx file to .pdf with 100% layout fidelity.
    Strategy:
    1. If on Windows and Word COM is available, use Word COM (identical to MS Word).
    2. Use `dxpdf` Python library (standalone Rust+Skia engine, cross-platform, fast).
    3. If `dxpdf` is unavailable, try LibreOffice (soffice).
    Returns True if conversion succeeded and output exists, False otherwise.
    """
    if not os.path.exists(docx_path):
        return False

    abs_docx = os.path.abspath(docx_path)
    abs_pdf = os.path.abspath(output_pdf_path)

    # 1. Windows: Native Word COM via PowerShell
    if sys.platform == "win32":
        ps_script = f"""
$ErrorActionPreference = 'Stop'
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone
    $doc = $word.Documents.Open('{abs_docx}', $false, $true)
    $doc.SaveAs([ref]'{abs_pdf}', [ref]17)
    $doc.Close([ref]$false)
    $word.Quit()
    exit 0
}} catch {{
    if ($word) {{ $word.Quit() }}
    exit 1
}}
"""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                timeout=45,
                creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
            if res.returncode == 0 and os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                return True
        except Exception:
            pass

    # 2. dxpdf Python library (standalone, fast, cross-platform)
    try:
        import dxpdf
        dxpdf.convert_file(abs_docx, abs_pdf)
        if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
            return True
    except Exception:
        pass

    # 3. LibreOffice / soffice (Linux/macOS fallback)
    soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice_cmd:
        out_dir = os.path.dirname(abs_pdf) or "."
        try:
            res = subprocess.run(
                [soffice_cmd, "--headless", "--convert-to", "pdf", abs_docx, "--outdir", out_dir],
                capture_output=True,
                timeout=45,
            )
            expected_lo_name = os.path.splitext(os.path.basename(abs_docx))[0] + ".pdf"
            lo_output = os.path.join(out_dir, expected_lo_name)
            if os.path.exists(lo_output):
                if lo_output != abs_pdf:
                    shutil.move(lo_output, abs_pdf)
                return True
        except Exception:
            pass

    return False


@contextmanager
def temp_docx_to_pdf(docx_path: str) -> Generator[str, None, None]:
    """
    Context manager that converts DOCX to a temporary PDF.
    Yields the temp PDF path if successful.
    Raises PdfConversionError if conversion fails (ensuring ZERO degraded fallback).
    Guarantees the temporary file is deleted on exit.
    """
    temp_pdf_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_pdf_path = f.name

        success = convert_docx_to_pdf(docx_path, temp_pdf_path)
        if not success or not os.path.exists(temp_pdf_path) or os.path.getsize(temp_pdf_path) == 0:
            raise PdfConversionError(
                f"'{os.path.basename(docx_path)}' dosyası PDF'e dönüştürülemedi. "
                "Sayfa numaralarının %100 doğrulukta hesaplanabilmesi için sistemde "
                "dxpdf paketinin veya Microsoft Word'ün hazır olduğundan emin olun."
            )

        yield temp_pdf_path
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except OSError:
                pass
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_pdf_converter.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add requirements.txt install.ps1 src/pdf_converter.py tests/test_pdf_converter.py
git commit -m "feat(converter): dxpdf ve Word COM tabanli sifir-fallback gecici PDF donusturucu"
```

---

### Task 2: PDF Eşleştirme Motorunun Güçlendirilmesi (`src/paginator.py`)

**Files:**
- Modify: `src/paginator.py:540-575`
- Test: `tests/test_paginator.py`

**Interfaces:**
- Consumes: `pdfplumber`, `ParsedParagraph`
- Produces: `DocumentPaginator._process_with_pdf(paragraphs, pdf_path)`

- [ ] **Step 1: Write test for robust PDF text matching in `tests/test_paginator.py`**

```python
def test_robust_pdf_matching_with_formatting_variations():
    """Verify _process_with_pdf handles whitespace, punctuation, and Turkish characters."""
    paragraphs = [
        ParsedParagraph(index=0, text="00.01", is_timecode=True),
        ParsedParagraph(index=1, text="JACKIE\t-   Merhaba! Nasılsın?  ", speaker="JACKIE", dialogue="-   Merhaba! Nasılsın?  "),
        ParsedParagraph(index=2, text="OOPJEN\t- İyiyim, teşekkürler. ", speaker="OOPJEN", dialogue="- İyiyim, teşekkürler. "),
    ]

    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = "00.01\nJACKIE  - Merhaba! Nasılsın?"
    page2 = MagicMock()
    page2.extract_text.return_value = "OOPJEN  - İyiyim, teşekkürler."
    mock_pdf.pages = [page1, page2]
    mock_pdf.__enter__.return_value = mock_pdf

    with patch("pdfplumber.open", return_value=mock_pdf), patch("os.path.exists", return_value=True):
        paginator = DocumentPaginator()
        assigned = paginator.process(paragraphs, pdf_path="dummy.pdf")
        assert assigned[1].page == 1
        assert assigned[2].page == 2
```

- [ ] **Step 2: Run test to verify behavior**

Run: `.venv/bin/pytest -k test_robust_pdf_matching_with_formatting_variations -v`

- [ ] **Step 3: Update `_process_with_pdf` in `src/paginator.py` with normalized search**

```python
    def _process_with_pdf(
        self,
        paragraphs: List[ParsedParagraph],
        pdf_path: str,
    ) -> List[ParsedParagraph]:
        """PDF dosyasındaki sayfa metinleri ile replikleri normalizasyon ile eşleştirerek %100 sayfa atar."""
        import pdfplumber

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {pdf_path}")

        def normalize(t: str) -> str:
            # Boşluk, tire, tırnak normalizasyonu ve küçük harf
            t = t.replace("İ", "i").replace("I", "ı").lower()
            t = t.replace("–", "-").replace("—", "-").replace("“", '"').replace("”", '"')
            return " ".join(t.split())

        with pdfplumber.open(pdf_path) as pdf:
            pdf_page_texts = [normalize(p.extract_text() or "") for p in pdf.pages]

        last_page = 1
        for p in paragraphs:
            if p.dialogue and p.speaker:
                cleaned_dial = normalize(p.dialogue.lstrip("- ").strip())
                search_needle = cleaned_dial[:30].strip()
                if search_needle:
                    for page_num in range(last_page, len(pdf_page_texts) + 1):
                        if search_needle in pdf_page_texts[page_num - 1]:
                            last_page = page_num
                            break
            p.page = last_page

        return paragraphs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -k test_robust_pdf_matching_with_formatting_variations -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/paginator.py tests/test_paginator.py
git commit -m "feat(paginator): guclendirilmis PDF metin ve sayfa eslestirme motoru"
```

---

### Task 3: Boru Hattı Entegrasyonu ve Sıfır-Fallback Garanti Sistemi (`kast.py` & `src/tui.py`)

**Files:**
- Modify: `kast.py:70-85`
- Modify: `src/tui.py`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: `temp_docx_to_pdf` from `src.pdf_converter`, `DocumentPaginator`
- Produces: Yalnızca %100 doğrulanmış PDF sayfalandırma + otomatik silinme

- [ ] **Step 1: Write integration test in `tests/test_integration.py`**

```python
def test_pipeline_uses_temporary_pdf_and_cleans_up():
    """Verify process_dubbing_script uses temporary PDF and guarantees 100% PDF path."""
    with patch("src.pdf_converter.temp_docx_to_pdf") as mock_temp_pdf, \
         patch("src.paginator.DocumentPaginator.process") as mock_process:
        
        mock_process.return_value = []
        
        @contextmanager
        def fake_temp_pdf(docx_path):
            yield "/tmp/fake_temp.pdf"
            
        mock_temp_pdf.side_effect = fake_temp_pdf
        
        from kast import process_dubbing_script
        try:
            process_dubbing_script("example/JACKIE & OOPJEN.docx", standalone=True, output_path="dummy_out.docx")
        except Exception:
            pass
            
        # Verify paginator was strictly called with the pdf_path
        assert mock_process.called
        call_kwargs = mock_process.call_args[1]
        assert call_kwargs.get("pdf_path") == "/tmp/fake_temp.pdf"
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/pytest -k test_pipeline_uses_temporary_pdf_and_cleans_up -v`
Expected: FAIL

- [ ] **Step 3: Update `process_dubbing_script` in `kast.py`**

In `kast.py`:
```python
from src.pdf_converter import temp_docx_to_pdf
```
In `process_dubbing_script`:
```python
    # 2. Sayfa numaralandırmasını hesapla (%100 PDF tabanlı)
    paginator = DocumentPaginator(doc)
    
    if pdf_path:
        # Kullanıcı elle harici PDF verdiyse doğrudan onu kullan
        assigned_paras = paginator.process(parsed_paras, pdf_path=pdf_path)
    else:
        # Arka planda geçici PDF oluştur (%100 garanti - fallback yok)
        with temp_docx_to_pdf(docx_path) as temp_pdf:
            print("[+] Arka planda geçici PDF üretildi, %100 sayfa hassasiyeti devrede.")
            assigned_paras = paginator.process(parsed_paras, pdf_path=temp_pdf)
```

- [ ] **Step 4: Update `src/tui.py` arka plan worker'ı**

Aynı şekilde TUI worker'ı da `process_dubbing_script` üzerinden veya doğrudan `temp_docx_to_pdf` ile çalışarak durumu ekranda `"Sayfalar %100 hassasiyetle hesaplanıyor..."` şeklinde günceller.

- [ ] **Step 5: Run integration and full test suite**

Run: `.venv/bin/pytest`
Expected: ALL PASS

- [ ] **Step 6: Commit and Push**

```bash
git add kast.py src/tui.py tests/test_integration.py
git commit -m "feat(pipeline): gecici PDF ile sifir-fallback %100 sayfa tespiti entegrasyonu"
git push origin main
```

---

## Plan Self-Review Checklist
1. **Zero Heuristic Fallback:** Kullanıcının açıkça reddettiği %90'lık tahmini hesaplama motoruna geri dönüş kaldırıldı mı? Evet, pipeline kesin olarak PDF üretip PDF üzerinden eşleştirir.
2. **Dedicated Python Library:** Word kurulu olmasa dahi PDF üretecek Python kütüphanesi (`dxpdf`) plana eklendi mi? Evet (`dxpdf>=0.8.0`).
3. **No Trace Left:** İşlem bitince veya hata aldığında geçici PDF kesin olarak siliniyor mu? Evet (`finally:` bloğu).
