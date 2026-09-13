"""Tests for Textual TUI Application (src/tui.py)."""

import os
import pytest
from docx import Document
from textual.widgets import Button

from src.tui import KastApp


@pytest.mark.asyncio
async def test_tui_app_mount_and_widgets():
    """Verify KastApp loads widgets correctly in headless test."""
    app = KastApp()
    async with app.run_test() as pilot:
        assert "Kast" in app.title
        docx_input = app.query_one("#docx-path")
        assert docx_input is not None

        pdf_input = app.query_one("#pdf-path")
        assert pdf_input is not None

        sort_radios = app.query_one("#sort-radios")
        assert sort_radios is not None

        cb_inplace = app.query_one("#cb-inplace")
        cb_standalone = app.query_one("#cb-standalone")
        assert cb_inplace is not None
        assert cb_standalone is not None

        btn_extract = app.query_one("#btn-extract")
        assert btn_extract is not None


@pytest.mark.asyncio
async def test_tui_checkbox_mutual_exclusivity():
    """Verify checking in-place unchecks standalone and vice-versa."""
    app = KastApp()
    async with app.run_test() as pilot:
        cb_inplace = app.query_one("#cb-inplace")
        cb_standalone = app.query_one("#cb-standalone")

        # Check in-place
        cb_inplace.value = True
        await pilot.pause()
        assert cb_inplace.value is True

        # Now check standalone -> inplace should be unchecked
        cb_standalone.value = True
        await pilot.pause()
        assert cb_standalone.value is True
        assert cb_inplace.value is False

        # Check inplace again -> standalone should be unchecked
        cb_inplace.value = True
        await pilot.pause()
        assert cb_inplace.value is True
        assert cb_standalone.value is False


@pytest.mark.asyncio
async def test_tui_extract_empty_path_shows_error():
    """Verify clicking extract without path writes error message."""
    app = KastApp()
    async with app.run_test() as pilot:
        app.query_one("#btn-extract", Button).action_press()
        await pilot.pause()

        log_area = app.query_one("#log-area")
        lines = [line.text for line in log_area.lines]
        combined = " ".join(lines)
        assert "Lütfen geçerli bir .docx dosyası belirtin" in combined or "Hata" in combined


@pytest.mark.asyncio
async def test_tui_successful_extraction(tmp_path):
    """Verify successful extraction end-to-end through TUI."""
    # Create a small script docx
    test_docx = tmp_path / "sample_script.docx"
    doc = Document()
    doc.add_paragraph("FİLMİN ADI\tDENEME")
    doc.add_paragraph("ÇEVİRMEN\tTEST")
    doc.add_paragraph("00.10")
    doc.add_paragraph("ALICE\t- Merhaba dünya!")
    doc.add_paragraph("BOB\t- Selam Alice!")
    doc.save(str(test_docx))

    app = KastApp()
    async with app.run_test() as pilot:
        # Input path with enclosing quotes (simulating drag & drop)
        docx_input = app.query_one("#docx-path")
        docx_input.value = f"'{test_docx}'"

        app.query_one("#btn-extract", Button).action_press()
        await pilot.pause()

        expected_output = tmp_path / "sample_script_kast.docx"
        assert os.path.exists(expected_output)

        out_doc = Document(str(expected_output))
        assert len(out_doc.tables) == 1
        table = out_doc.tables[0]
        assert len(table.rows) == 3  # Header + ALICE + BOB
