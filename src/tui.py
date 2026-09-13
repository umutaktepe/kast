"""Terminal User Interface (TUI) for Dubbing Cast Extraction (Kast 2.0).

Built with Textual, providing a compact, modern, non-scrolling interface with
drag-and-drop file inputs, native OS file picker buttons, sorting options,
output flags, and live extraction logs.
"""

import os
import platform
import shutil
import subprocess
import sys
import urllib.parse
from typing import List, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
    RichLog,
)

from kast import process_cast_document


def clean_drag_drop_path(raw_text: str) -> str:
    """Clean paths originating from terminal drag-and-drop or clipboard.

    Handles:
    - 'file:///path/to/file.docx' -> '/path/to/file.docx'
    - 'file:/path/to/file.docx' -> '/path/to/file.docx'
    - URL percent-encoding ('My%20File.docx' -> 'My File.docx')
    - Enclosing quotes ('...', "...")
    - Trailing newlines, tabs, and carriage returns
    """
    if not raw_text:
        return ""
    path = raw_text.strip()
    path = path.strip("'\"")
    if path.startswith("file://"):
        path = path[7:]
    elif path.startswith("file:"):
        path = path[5:]
    path = urllib.parse.unquote(path)
    return path.strip("'\" \r\n\t")


def select_file_dialog(title: str, extensions: List[str]) -> Optional[str]:
    """Open a native OS file dialog to select a file.

    Supports:
    - Linux: zenity, kdialog, or tkinter fallback
    - Windows: PowerShell System.Windows.Forms.OpenFileDialog
    - macOS: AppleScript osascript
    """
    system = platform.system()

    # 1. Linux
    if system == "Linux":
        if shutil.which("zenity"):
            filters = " ".join(f"*.{ext} *.{ext.upper()}" for ext in extensions)
            pattern = f"Desteklenen Dosyalar | {filters}"
            cmd = ["zenity", "--file-selection", f"--title={title}", f"--file-filter={pattern}"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    selected = res.stdout.strip()
                    return selected if (selected and os.path.exists(selected)) else None
                # Kullanıcı iptal etti (Cancel / ESC / kapatma) -> başka diyalog açma
                return None
            except Exception:
                pass

        if shutil.which("kdialog"):
            filters = " ".join(f"*.{ext}" for ext in extensions)
            cmd = ["kdialog", "--getopenfilename", os.path.expanduser("~"), filters, "--title", title]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    selected = res.stdout.strip()
                    return selected if (selected and os.path.exists(selected)) else None
                # Kullanıcı iptal etti -> başka diyalog açma
                return None
            except Exception:
                pass

    # 2. Windows
    elif system == "Windows":
        filter_str = f"Desteklenen Dosyalar (*.{extensions[0]})|*.{extensions[0]}|Tum Dosyalar (*.*)|*.*"
        ps_cmd = (
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"$d = New-Object System.Windows.Forms.OpenFileDialog; "
            f"$d.Title = '{title}'; "
            f"$d.Filter = '{filter_str}'; "
            f"if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{ Write-Output $d.FileName }}"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if res.returncode == 0:
                selected = res.stdout.strip()
                return selected if (selected and os.path.exists(selected)) else None
            return None
        except Exception:
            pass

    # 3. macOS
    elif system == "Darwin":
        ext_list = ", ".join(f'"{ext}"' for ext in extensions)
        apple_script = f'POSIX path of (choose file with prompt "{title}" of type {{{ext_list}}})'
        try:
            res = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                selected = res.stdout.strip()
                return selected if (selected and os.path.exists(selected)) else None
            return None
        except Exception:
            pass

    # 4. Tkinter fallback (Yalnızca yerel diyalog aracı bulunamazsa veya başlatılamazsa)
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_types = [
            ("Desteklenen Dosyalar", tuple(f"*.{ext}" for ext in extensions)),
            ("Tüm Dosyalar", "*.*"),
        ]
        selected = filedialog.askopenfilename(title=title, filetypes=file_types)
        root.destroy()
        if selected and os.path.exists(selected):
            return selected
        return None
    except Exception:
        pass

    return None


class PathInput(Input):
    """Input widget that cleanly handles file drag-and-drop and clipboard pasting."""

    def _on_paste(self, event: events.Paste) -> None:
        event.stop()
        event.prevent_default()
        if event.text:
            cleaned = clean_drag_drop_path(event.text)
            if self.id == "docx-path" and cleaned.lower().endswith(".pdf"):
                pdf_inp = self.app.query_one("#pdf-path", PathInput)
                pdf_inp.value = cleaned
                return
            if self.id == "pdf-path" and cleaned.lower().endswith(".docx"):
                docx_inp = self.app.query_one("#docx-path", PathInput)
                docx_inp.value = cleaned
                return
            self.value = cleaned


TUI_CSS = """
Screen {
    background: $surface-darken-1;
    overflow: hidden;
}

#main-container {
    width: 100%;
    height: 100%;
    padding: 0 1;
}

#files-row {
    height: 5;
    margin-top: 1;
    margin-bottom: 0;
}

.file-box {
    width: 1fr;
    height: 100%;
    background: $surface;
    border: round $primary;
    padding: 0 1;
    margin-right: 1;
}

.file-box-last {
    margin-right: 0;
    border: round $secondary;
}

.box-title {
    text-style: bold;
    color: $accent;
    height: 1;
}

.input-row {
    height: 3;
}

.file-input {
    width: 1fr;
    height: 3;
}

.browse-btn {
    min-width: 11;
    margin-left: 1;
    height: 3;
}

#options-row {
    height: 5;
    margin-top: 1;
    margin-bottom: 0;
}

.options-col {
    width: 1fr;
    height: 100%;
    border: round $primary-darken-1;
    background: $surface;
    padding: 0 1;
    margin-right: 1;
}

.options-col-last {
    margin-right: 0;
}

RadioSet {
    background: transparent;
    border: none;
    height: auto;
}

RadioButton {
    height: 1;
    padding: 0;
}

Checkbox {
    height: 1;
    padding: 0;
    background: transparent;
    border: none;
}

#buttons-row {
    height: 3;
    margin-top: 1;
    margin-bottom: 1;
    align: center middle;
}

#buttons-row Button {
    margin: 0 1;
    min-width: 18;
}

#log-card {
    height: 1fr;
    background: $surface;
    border: round $primary;
    padding: 0 1;
}

#log-area {
    height: 100%;
    background: $background;
    border: none;
}
"""


class KastApp(App):
    """Textual application for Kast 2.0 with compact, non-scrolling layout."""

    TITLE = "Kast 2.0 — Dublaj Çevirisi Kast Çıkarma"
    SUB_TITLE = "Word (.docx) senaryolarından otomatik kast tablosu oluşturucu"
    CSS = TUI_CSS
    BINDINGS = [
        ("q", "quit", "Çıkış"),
        ("ctrl+r", "extract", "Kast Çıkar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-container"):
            # 1. Dosya Seçim Alanı (Yan yana 2 kutu)
            with Horizontal(id="files-row"):
                with Vertical(classes="file-box"):
                    yield Label("📥 1. Senaryo (.docx) [Buraya Sürükleyin]:", classes="box-title")
                    with Horizontal(classes="input-row"):
                        yield PathInput(
                            id="docx-path",
                            classes="file-input",
                            placeholder="DOCX dosyasını buraya sürükleyin veya yazın...",
                        )
                        yield Button("📂 Gözat", id="btn-browse-docx", classes="browse-btn")

                with Vertical(classes="file-box file-box-last"):
                    yield Label("📄 2. Referans PDF [Opsiyonel]:", classes="box-title")
                    with Horizontal(classes="input-row"):
                        yield PathInput(
                            id="pdf-path",
                            classes="file-input",
                            placeholder="Opsiyonel referans PDF dosyasını sürükleyin...",
                        )
                        yield Button("📂 Gözat", id="btn-browse-pdf", classes="browse-btn")

            # 2. Seçenekler Alanı (Yan yana 2 kutu)
            with Horizontal(id="options-row"):
                with Vertical(classes="options-col"):
                    yield Label("📊 Karakter Sıralama", classes="box-title")
                    with RadioSet(id="sort-radios"):
                        yield RadioButton("İlk Görünme (Appearance)", id="sort-appearance", value=True)
                        yield RadioButton("Replik Sayısı (Count)", id="sort-count")
                        yield RadioButton("Karakter Adı (A-Z)", id="sort-name")

                with Vertical(classes="options-col options-col-last"):
                    yield Label("⚙️ Çıktı Seçenekleri", classes="box-title")
                    yield Checkbox("Orijinal dosyanın sonuna ekle (--in-place)", id="cb-inplace")
                    yield Checkbox("Sadece kast tablosunu kaydet (--standalone)", id="cb-standalone")

            # 3. Butonlar Barı
            with Horizontal(id="buttons-row"):
                yield Button("🚀 Kast Çıkar", id="btn-extract", variant="success")
                yield Button("🗑️ Temizle", id="btn-clear", variant="default")
                yield Button("❌ Çıkış", id="btn-exit", variant="error")

            # 4. İşlem Günlüğü Kartı (Kalan tüm dikey alanı kaplar)
            with Vertical(id="log-card"):
                yield RichLog(id="log-area", highlight=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        docx_input = self.query_one("#docx-path", PathInput)
        docx_input.focus()

        log = self.query_one("#log-area", RichLog)
        log.write("[bold cyan]Kast 2.0 Hazır![/bold cyan]")
        log.write(
            "• Senaryo dosyanızı [bold yellow]pencerenin herhangi bir yerine sürükleyip bırakabilir[/bold yellow],\n"
            "• veya [bold green][📂 Gözat][/bold green] butonuna basarak dosya seçebilirsiniz."
        )

    def on_paste(self, event: events.Paste) -> None:
        """Handle drag-and-drop or clipboard paste at the whole-window level."""
        event.stop()
        event.prevent_default()
        if event.text:
            self._handle_file_drop(event.text)

    def _handle_file_drop(self, raw_text: str) -> None:
        """Route dropped file to appropriate input and notify user."""
        clean = clean_drag_drop_path(raw_text)
        if not clean:
            return

        log = self.query_one("#log-area", RichLog)
        if clean.lower().endswith(".pdf"):
            self.query_one("#pdf-path", PathInput).value = clean
            log.write(f"[bold cyan][✓] Referans PDF algılandı:[/bold cyan] {clean}")
            self.notify(f"PDF eklendi: {os.path.basename(clean)}", title="Dosya Algılandı")
        else:
            docx_inp = self.query_one("#docx-path", PathInput)
            docx_inp.value = clean
            docx_inp.focus()
            log.write(f"[bold green][✓] Senaryo dosyası algılandı:[/bold green] {clean}")
            self.notify(f"DOCX eklendi: {os.path.basename(clean)}", title="Dosya Algılandı")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Smart routing and cleaning when input content changes."""
        cleaned = clean_drag_drop_path(event.value)
        # Sürüklenen PDF yanlışlıkla DOCX kutusuna bırakılırsa otomatik taşı
        if event.input.id == "docx-path" and cleaned.lower().endswith(".pdf"):
            event.input.value = ""
            self.query_one("#pdf-path", PathInput).value = cleaned
            return
        # Sürüklenen DOCX yanlışlıkla PDF kutusuna bırakılırsa otomatik taşı
        if event.input.id == "pdf-path" and cleaned.lower().endswith(".docx"):
            event.input.value = ""
            self.query_one("#docx-path", PathInput).value = cleaned
            return

        if cleaned != event.value:
            event.input.value = cleaned

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle mutual exclusivity between in-place and standalone."""
        cb_inplace = self.query_one("#cb-inplace", Checkbox)
        cb_standalone = self.query_one("#cb-standalone", Checkbox)

        if event.checkbox == cb_inplace and event.value:
            if cb_standalone.value:
                cb_standalone.value = False
        elif event.checkbox == cb_standalone and event.value:
            if cb_inplace.value:
                cb_inplace.value = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-extract":
            self.action_extract()
        elif event.button.id == "btn-clear":
            self.action_clear()
        elif event.button.id == "btn-exit":
            self.app.exit(0)
        elif event.button.id == "btn-browse-docx":
            self.action_browse_docx()
        elif event.button.id == "btn-browse-pdf":
            self.action_browse_pdf()

    def action_browse_docx(self) -> None:
        """Open native file chooser for DOCX."""
        selected = select_file_dialog("DOCX Senaryo Dosyası Seçin", ["docx", "DOCX"])
        if selected:
            docx_input = self.query_one("#docx-path", PathInput)
            docx_input.value = selected
            docx_input.focus()
            log = self.query_one("#log-area", RichLog)
            log.write(f"[bold green][✓] DOCX dosyası seçildi:[/bold green] {selected}")

    def action_browse_pdf(self) -> None:
        """Open native file chooser for PDF."""
        selected = select_file_dialog("Referans PDF Dosyası Seçin", ["pdf", "PDF"])
        if selected:
            pdf_input = self.query_one("#pdf-path", PathInput)
            pdf_input.value = selected
            log = self.query_one("#log-area", RichLog)
            log.write(f"[bold cyan][✓] Referans PDF dosyası seçildi:[/bold cyan] {selected}")

    def action_clear(self) -> None:
        """Reset inputs and log area."""
        self.query_one("#docx-path", PathInput).value = ""
        self.query_one("#pdf-path", PathInput).value = ""
        self.query_one("#cb-inplace", Checkbox).value = False
        self.query_one("#cb-standalone", Checkbox).value = False
        self.query_one("#sort-appearance", RadioButton).value = True
        log = self.query_one("#log-area", RichLog)
        log.clear()
        log.write("[dim]Tüm alanlar temizlendi.[/dim]")
        self.query_one("#docx-path", PathInput).focus()

    def action_extract(self) -> None:
        """Execute cast extraction with the selected options."""
        log = self.query_one("#log-area", RichLog)
        docx_raw = self.query_one("#docx-path", PathInput).value
        pdf_raw = self.query_one("#pdf-path", PathInput).value

        docx_path = clean_drag_drop_path(docx_raw)
        pdf_path = clean_drag_drop_path(pdf_raw) if pdf_raw else None

        if not docx_path:
            log.write("[bold red][!] Hata:[/bold red] Lütfen geçerli bir .docx dosyası belirtin.")
            return

        if not os.path.exists(docx_path):
            log.write(f"[bold red][!] Hata:[/bold red] Dosya bulunamadı: [yellow]{docx_path}[/yellow]")
            return

        if not docx_path.lower().endswith(".docx"):
            log.write("[bold red][!] Hata:[/bold red] Seçilen dosya bir Word dökümanı (.docx) değil.")
            return

        # Determine sort_by
        sort_by = "appearance"
        if self.query_one("#sort-count", RadioButton).value:
            sort_by = "count"
        elif self.query_one("#sort-name", RadioButton).value:
            sort_by = "name"

        # Determine output options
        in_place = self.query_one("#cb-inplace", Checkbox).value
        standalone = self.query_one("#cb-standalone", Checkbox).value
        output_path = docx_path if in_place else None

        log.write(f"\n[bold blue][*] İşlem başlatılıyor:[/bold blue] {docx_path}")
        log.write(f"    Sıralama: [magenta]{sort_by}[/magenta] | In-Place: {in_place} | Standalone: {standalone}")

        try:
            saved_file = process_cast_document(
                docx_path=docx_path,
                output_path=output_path,
                pdf_path=pdf_path,
                sort_by=sort_by,
                standalone=standalone,
            )
            log.write("[bold green][✓] Başarıyla tamamlandı![/bold green]")
            log.write(f"    Kast Tablosu Kaydedildi: [bold underline green]{saved_file}[/bold underline green]")
        except Exception as exc:
            log.write(f"[bold red][!] Çıkarma sırasında hata oluştu:[/bold red] {exc}")


def launch_tui() -> int:
    """Entry point to start the Kast Textual TUI."""
    app = KastApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(launch_tui())
