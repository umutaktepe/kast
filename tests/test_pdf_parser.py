import os
import pytest
from unittest.mock import MagicMock, patch
from src.pdf_parser import DubbingPdfParser, process_pdf_document
from src.models import CastExtractionResult


def test_dubbing_pdf_parser_extracts_characters_and_pages(tmp_path):
    """PDF sayfalarından repliklerin ve karakterlerin doğru tespit edildiğini test eder."""
    dummy_pdf = tmp_path / "dummy.pdf"
    dummy_pdf.touch()

    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = (
        "1\n"
        "FİLMİN ADI\tTEST FİLMİ\n"
        "00.10\n"
        "ALICE\t- Merhaba Bob!\n"
        "BOB\t- Selam Alice!\n"
    )
    page2 = MagicMock()
    page2.extract_text.return_value = (
        "2\n"
        "01.20\n"
        "ALICE\t- İkinci sayfadaki replik.\n"
    )
    mock_pdf.pages = [page1, page2]
    mock_pdf.__enter__.return_value = mock_pdf

    with patch("pdfplumber.open", return_value=mock_pdf):
        parser = DubbingPdfParser()
        result = parser.parse_pdf(str(dummy_pdf), sort_by="appearance")

        assert isinstance(result, CastExtractionResult)
        assert result.total_lines == 3
        assert result.total_pages == 2
        assert len(result.characters) == 2

        alice = next(c for c in result.characters if c.name == "ALICE")
        assert alice.line_count == 2
        assert alice.pages == [1, 2]

        bob = next(c for c in result.characters if c.name == "BOB")
        assert bob.line_count == 1
        assert bob.pages == [1]


def test_process_pdf_document_creates_docx(tmp_path):
    """process_pdf_document fonksiyonunun kast tablosunu DOCX olarak kaydettiğini test eder."""
    dummy_pdf = tmp_path / "sample.pdf"
    dummy_pdf.touch()

    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = "00.10\nJOHN\t- Selam dünya!"
    mock_pdf.pages = [page1]
    mock_pdf.__enter__.return_value = mock_pdf

    out_file = tmp_path / "test_pdf_kast.docx"
    with patch("pdfplumber.open", return_value=mock_pdf):
        saved_path, res = process_pdf_document(str(dummy_pdf), output_path=str(out_file))
        assert os.path.exists(saved_path)
        assert res.total_lines == 1
        assert res.characters[0].name == "JOHN"


def test_dubbing_pdf_parser_file_not_found():
    """Var olmayan PDF dosyasında FileNotFoundError fırlatıldığını doğrular."""
    parser = DubbingPdfParser()
    with pytest.raises(FileNotFoundError, match="PDF dosyası bulunamadı"):
        parser.parse_pdf("nonexistent_path_to_pdf_file_987654.pdf")


def test_dubbing_pdf_parser_sorting_options(tmp_path):
    """Karakter sıralama seçeneklerinin (appearance, count, name) doğruluğunu test eder."""
    dummy_pdf = tmp_path / "dummy.pdf"
    dummy_pdf.touch()

    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = (
        "CHAR_B\t- Replik 1\n"
        "CHAR_A\t- Replik 2\n"
        "CHAR_A\t- Replik 3\n"
        "CHAR_C\t- Replik 4\n"
    )
    mock_pdf.pages = [page1]
    mock_pdf.__enter__.return_value = mock_pdf

    with patch("pdfplumber.open", return_value=mock_pdf):
        parser = DubbingPdfParser()

        # By appearance: CHAR_B, CHAR_A, CHAR_C
        res_app = parser.parse_pdf(str(dummy_pdf), sort_by="appearance")
        assert [c.name for c in res_app.characters] == ["CHAR_B", "CHAR_A", "CHAR_C"]

        # By count: CHAR_A (2), then CHAR_B (1) / CHAR_C (1)
        res_cnt = parser.parse_pdf(str(dummy_pdf), sort_by="count")
        assert res_cnt.characters[0].name == "CHAR_A"
        assert res_cnt.characters[0].line_count == 2

        # By name: CHAR_A, CHAR_B, CHAR_C
        res_name = parser.parse_pdf(str(dummy_pdf), sort_by="name")
        assert [c.name for c in res_name.characters] == ["CHAR_A", "CHAR_B", "CHAR_C"]


def test_dubbing_pdf_parser_hyphen_syntax_and_metadata_filtering(tmp_path):
    """Tireli ayrıştırma ve künye/metadata satırlarının elendiğini test eder."""
    dummy_pdf = tmp_path / "dummy.pdf"
    dummy_pdf.touch()

    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = (
        "ÇEVİRMEN - AHMET YILMAZ\n"
        "SESLENDİRME YÖNETMENİ - MEHMET ÖZ\n"
        "00:15:20\n"
        "KAPTAN - Rotayı sancak tarafına çevirin!\n"
        "TAYFA - Emredersiniz efendim!\n"
    )
    mock_pdf.pages = [page1]
    mock_pdf.__enter__.return_value = mock_pdf

    with patch("pdfplumber.open", return_value=mock_pdf):
        parser = DubbingPdfParser()
        res = parser.parse_pdf(str(dummy_pdf))

        # Metadata should be skipped, only KAPTAN and TAYFA captured
        names = [c.name for c in res.characters]
        assert "KAPTAN" in names
        assert "TAYFA" in names
        assert "ÇEVİRMEN" not in names
        assert "SESLENDİRME YÖNETMENİ" not in names
        assert res.total_lines == 2


def test_dubbing_pdf_parser_progress_callback(tmp_path):
    """İlerleme geri çağırma (progress_callback) fonksiyonunun çağrıldığını doğrular."""
    dummy_pdf = tmp_path / "dummy.pdf"
    dummy_pdf.touch()

    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = "ALICE\t- Merhaba!"
    mock_pdf.pages = [page1]
    mock_pdf.__enter__.return_value = mock_pdf

    calls = []

    def callback(curr, total, msg):
        calls.append((curr, total, msg))

    with patch("pdfplumber.open", return_value=mock_pdf):
        parser = DubbingPdfParser()
        parser.parse_pdf(str(dummy_pdf), progress_callback=callback)

        assert len(calls) == 1
        assert calls[0][0] == 1
        assert calls[0][1] == 1
        assert "Sayfa 1/1" in calls[0][2]


def test_process_pdf_document_default_output_path(tmp_path):
    """output_path belirtilmediğinde {base}_kast.docx adıyla kaydedildiğini doğrular."""
    dummy_input = tmp_path / "sample_video_script.pdf"
    dummy_input.touch()
    expected_docx = str(tmp_path / "sample_video_script_kast.docx")

    mock_pdf = MagicMock()
    page1 = MagicMock()
    page1.extract_text.return_value = "ALICE\t- Test repliği"
    mock_pdf.pages = [page1]
    mock_pdf.__enter__.return_value = mock_pdf

    with patch("pdfplumber.open", return_value=mock_pdf):
        saved_path, res = process_pdf_document(str(dummy_input))
        assert saved_path == expected_docx
        assert os.path.exists(expected_docx)
        assert res.total_lines == 1
