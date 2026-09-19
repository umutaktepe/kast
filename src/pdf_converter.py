"""Cross-platform DOCX to PDF converter utility for Kast using Headless LibreOffice and Word COM."""

import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from typing import Generator, Optional


class PdfConversionError(RuntimeError):
    """Raised when DOCX to PDF conversion cannot be completed."""
    pass


def find_soffice_binary() -> Optional[str]:
    """
    Find the LibreOffice / soffice executable on the system.
    Searches system PATH, standard Windows installation paths, and macOS application bundles.
    """
    # 1. System PATH
    for cmd in ("soffice", "libreoffice"):
        which_path = shutil.which(cmd)
        if which_path:
            return which_path

    # 2. Windows standard installation paths
    if sys.platform == "win32":
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "LibreOffice", "program", "soffice.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "LibreOffice", "program", "soffice.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "LibreOffice", "program", "soffice.exe") if os.environ.get("LOCALAPPDATA") else "",
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return path

    # 3. macOS standard application path
    if sys.platform == "darwin":
        mac_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if os.path.exists(mac_path):
            return mac_path

    return None


def is_pdf_conversion_supported() -> bool:
    """Check if any PDF conversion engine (Word COM on Windows, or LibreOffice) is available."""
    if sys.platform == "win32":
        return True
    return find_soffice_binary() is not None


def convert_docx_to_pdf(docx_path: str, output_pdf_path: str) -> bool:
    """
    Convert a .docx file to .pdf with 100% layout fidelity.
    Strategy:
    1. If on Windows, try native Word COM (identical to MS Word).
    2. Try headless LibreOffice (soffice --headless --convert-to pdf).
    Returns True if conversion succeeded and output exists, False otherwise.
    """
    if not os.path.exists(docx_path):
        return False

    abs_docx = os.path.abspath(docx_path)
    abs_pdf = os.path.abspath(output_pdf_path)

    # 1. Windows: Native Word COM via PowerShell
    if sys.platform == "win32":
        ps_docx = abs_docx.replace("'", "''")
        ps_pdf = abs_pdf.replace("'", "''")
        ps_script = f"""
$ErrorActionPreference = 'Stop'
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone
    $doc = $word.Documents.Open('{ps_docx}', $false, $true)
    $doc.SaveAs([ref]'{ps_pdf}', [ref]17)
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

    # 2. LibreOffice / soffice (Linux/macOS/Windows fallback)
    soffice_cmd = find_soffice_binary()
    if soffice_cmd:
        out_dir = os.path.dirname(abs_pdf) or "."
        try:
            res = subprocess.run(
                [soffice_cmd, "--headless", "--convert-to", "pdf", abs_docx, "--outdir", out_dir],
                capture_output=True,
                timeout=45,
            )
            if res.returncode == 0:
                expected_lo_name = os.path.splitext(os.path.basename(abs_docx))[0] + ".pdf"
                lo_output = os.path.join(out_dir, expected_lo_name)
                if os.path.exists(lo_output) and os.path.getsize(lo_output) > 0:
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
                "Kast'ın %100 doğrulukta sayfa tespiti yapabilmesi için sistemde LibreOffice veya Microsoft Word bulunmalıdır. "
                "Lütfen './install.sh' (Windows'ta '.\\install.ps1') çalıştırın ya da LibreOffice yükleyin."
            )

        yield temp_pdf_path
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except OSError:
                pass
