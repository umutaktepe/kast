import os
import pytest
from unittest.mock import patch, MagicMock
from src.pdf_converter import (
    find_soffice_binary,
    convert_docx_to_pdf,
    temp_docx_to_pdf,
    is_pdf_conversion_supported,
    PdfConversionError,
)


def test_dxpdf_not_referenced_in_pdf_converter():
    """Verify dxpdf is not imported or referenced anywhere in pdf_converter.py."""
    import src.pdf_converter as mod
    source_path = mod.__file__
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "dxpdf" not in content.lower(), "dxpdf should be completely removed from pdf_converter.py"


def test_find_soffice_binary_search_paths():
    with patch("shutil.which", return_value="/usr/bin/soffice"):
        assert find_soffice_binary() == "/usr/bin/soffice"

    with patch("shutil.which", side_effect=lambda cmd: "/usr/bin/libreoffice" if cmd == "libreoffice" else None):
        assert find_soffice_binary() == "/usr/bin/libreoffice"


def test_find_soffice_binary_windows_paths():
    with patch("sys.platform", "win32"), \
         patch("shutil.which", return_value=None), \
         patch("os.path.exists", side_effect=lambda p: p.endswith("soffice.exe")):
        assert find_soffice_binary() is not None
        assert find_soffice_binary().endswith("soffice.exe")


def test_find_soffice_binary_darwin_path():
    with patch("sys.platform", "darwin"), \
         patch("shutil.which", return_value=None), \
         patch("os.path.exists", side_effect=lambda p: p == "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        assert find_soffice_binary() == "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def test_find_soffice_binary_not_found():
    with patch("sys.platform", "linux"), \
         patch("shutil.which", return_value=None):
        assert find_soffice_binary() is None


def test_is_pdf_conversion_supported_platform_checks():
    with patch("sys.platform", "win32"):
        assert is_pdf_conversion_supported() is True

    with patch("sys.platform", "linux"), patch("src.pdf_converter.find_soffice_binary", return_value=None):
        assert is_pdf_conversion_supported() is False

    with patch("sys.platform", "linux"), patch("src.pdf_converter.find_soffice_binary", return_value="/usr/bin/soffice"):
        assert is_pdf_conversion_supported() is True


def test_convert_docx_to_pdf_nonexistent_docx():
    with patch("os.path.exists", return_value=False):
        assert convert_docx_to_pdf("nonexistent.docx", "out.pdf") is False


def test_convert_docx_to_pdf_executes_libreoffice():
    def mock_exists(p):
        if p == "test.docx":
            return True
        if p.endswith("test.pdf"):
            return True
        return False

    with patch("sys.platform", "linux"), \
         patch("os.path.exists", side_effect=mock_exists), \
         patch("os.path.getsize", return_value=1024), \
         patch("src.pdf_converter.find_soffice_binary", return_value="/usr/bin/soffice"), \
         patch("subprocess.run") as mock_run:

        mock_run.return_value = MagicMock(returncode=0)
        result = convert_docx_to_pdf("test.docx", "test.pdf")
        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "/usr/bin/soffice"
        assert "--headless" in cmd
        assert "--convert-to" in cmd
        assert "pdf" in cmd


def test_convert_docx_to_pdf_windows_fallback_to_libreoffice():
    """When Word COM fails on Windows, it falls back to LibreOffice."""
    def mock_exists(p):
        if p == "test.docx":
            return True
        if p.endswith("test.pdf"):
            return True
        return False

    with patch("sys.platform", "win32"), \
         patch("os.path.exists", side_effect=mock_exists), \
         patch("os.path.getsize", return_value=1024), \
         patch("src.pdf_converter.find_soffice_binary", return_value=r"C:\Program Files\LibreOffice\program\soffice.exe"), \
         patch("subprocess.run") as mock_run:

        # First call is powershell (fails with returncode=1), second is soffice (succeeds)
        mock_run.side_effect = [
            MagicMock(returncode=1),  # PowerShell Word COM failed
            MagicMock(returncode=0),  # LibreOffice succeeded
        ]
        result = convert_docx_to_pdf("test.docx", "test.pdf")
        assert result is True
        assert mock_run.call_count == 2
        soffice_cmd = mock_run.call_args_list[1][0][0]
        assert soffice_cmd[0] == r"C:\Program Files\LibreOffice\program\soffice.exe"
        assert "--headless" in soffice_cmd


def test_convert_docx_to_pdf_powershell_path_escaping():
    with patch("sys.platform", "win32"), \
         patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024), \
         patch("subprocess.run") as mock_run:

        mock_run.return_value = MagicMock(returncode=0)
        docx_path = r"C:\Users\John's Documents\my 'test' doc.docx"
        pdf_path = r"C:\Users\John's Documents\my 'test' out.pdf"

        result = convert_docx_to_pdf(docx_path, pdf_path)
        assert result is True
        mock_run.assert_called_once()

        # Verify PowerShell command contains escaped single quotes
        called_cmd = mock_run.call_args[0][0]
        script_arg = called_cmd[4]
        assert "John''s Documents" in script_arg
        assert "my ''test'' doc.docx" in script_arg
        assert "my ''test'' out.pdf" in script_arg


def test_convert_docx_to_pdf_libreoffice_fails_on_nonzero_returncode():
    with patch("sys.platform", "linux"), \
         patch("os.path.exists", return_value=True), \
         patch("src.pdf_converter.find_soffice_binary", return_value="/usr/bin/soffice"), \
         patch("subprocess.run") as mock_run:

        mock_run.return_value = MagicMock(returncode=1)
        result = convert_docx_to_pdf("test.docx", "test.pdf")
        assert result is False


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


def test_temp_docx_to_pdf_cleanup_on_exception():
    with patch("src.pdf_converter.convert_docx_to_pdf") as mock_convert:
        pdf_path_created = None

        def fake_convert(docx_in, pdf_out):
            nonlocal pdf_path_created
            pdf_path_created = pdf_out
            with open(pdf_out, "w") as f:
                f.write("mock pdf")
            return True

        mock_convert.side_effect = fake_convert

        with pytest.raises(RuntimeError, match="error inside with block"):
            with temp_docx_to_pdf("dummy.docx") as _:
                raise RuntimeError("error inside with block")

        assert pdf_path_created is not None
        assert not os.path.exists(pdf_path_created)


def test_temp_docx_to_pdf_raises_error_when_conversion_fails():
    with patch("src.pdf_converter.convert_docx_to_pdf", return_value=False):
        with pytest.raises(PdfConversionError) as exc_info:
            with temp_docx_to_pdf("corrupt.docx") as _:
                pass

        error_msg = str(exc_info.value)
        assert "LibreOffice veya Microsoft Word bulunmalıdır" in error_msg
        assert "install.sh" in error_msg or "install.ps1" in error_msg


def test_temp_docx_to_pdf_raises_error_when_file_is_empty():
    with patch("src.pdf_converter.convert_docx_to_pdf") as mock_convert:
        def fake_convert_empty(docx_in, pdf_out):
            with open(pdf_out, "w") as f:
                pass  # 0 bytes
            return True

        mock_convert.side_effect = fake_convert_empty

        with pytest.raises(PdfConversionError):
            with temp_docx_to_pdf("empty.docx") as _:
                pass
