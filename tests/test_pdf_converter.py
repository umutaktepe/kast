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


def test_is_pdf_conversion_supported_without_dxpdf_platform_checks():
    with patch.dict("sys.modules", {"dxpdf": None}):
        with patch("sys.platform", "win32"):
            assert is_pdf_conversion_supported() is True

        with patch("sys.platform", "linux"), patch("shutil.which", return_value=None):
            assert is_pdf_conversion_supported() is False

        with patch("sys.platform", "linux"), patch("shutil.which", return_value="/usr/bin/soffice"):
            assert is_pdf_conversion_supported() is True


def test_convert_docx_to_pdf_nonexistent_docx():
    with patch("os.path.exists", return_value=False):
        assert convert_docx_to_pdf("nonexistent.docx", "out.pdf") is False


def test_convert_docx_to_pdf_uses_dxpdf():
    mock_dxpdf = MagicMock()
    with patch.dict("sys.modules", {"dxpdf": mock_dxpdf}), \
         patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024):

        # When dxpdf succeeds
        result = convert_docx_to_pdf("test.docx", "test.pdf")
        assert result is True
        mock_dxpdf.convert_file.assert_called_once()


def test_convert_docx_to_pdf_fallback_to_libreoffice():
    mock_dxpdf = MagicMock()
    mock_dxpdf.convert_file.side_effect = RuntimeError("dxpdf conversion error")

    def mock_exists(p):
        if p == "test.docx":
            return True
        if p.endswith("test.pdf"):
            return True
        return False

    with patch.dict("sys.modules", {"dxpdf": mock_dxpdf}), \
         patch("sys.platform", "linux"), \
         patch("os.path.exists", side_effect=mock_exists), \
         patch("os.path.getsize", return_value=1024), \
         patch("shutil.which", return_value="/usr/bin/soffice"), \
         patch("subprocess.run") as mock_run:

        mock_run.return_value = MagicMock(returncode=0)
        result = convert_docx_to_pdf("test.docx", "test.pdf")
        assert result is True
        mock_run.assert_called_once()


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
        with pytest.raises(PdfConversionError):
            with temp_docx_to_pdf("corrupt.docx") as _:
                pass


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
