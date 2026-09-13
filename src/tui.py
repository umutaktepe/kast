"""Terminal User Interface (TUI) for Dubbing Cast Extraction (Kast 2.0).

Built with Textual, providing a modern, interactive full-screen interface with
drag-and-drop file inputs, sorting options, output flags, and live extraction logs.
"""

import os
import sys
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
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
    Static,
)

from kast import process_cast_document


TUI_CSS = """
Screen {
    background: $surface-darken-1;
}

#main-container {
    width: 100%;
    height: 100%;
    padding: 1 2;
}

.panel-box {
    border: round $primary;
    background: $surface;
    padding: 1 2;
    margin-bottom: 1;
}

.section-title {
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

.input-label {
    text-style: bold;
    color: $text;
    margin-top: 1;
    margin-bottom: 0;
}

Input {
    margin-bottom: 1;
    border: tall $surface-lighten-2;
}

Input:focus {
    border: tall $accent;
}

#options-container {
    height: auto;
    margin-bottom: 1;
}

.options-col {
    width: 1fr;
    padding: 0 1;
}

RadioSet {
    background: transparent;
    border: none;
}

RadioButton {
    margin-bottom: 0;
}

Checkbox {
    margin-bottom: 0;
    background: transparent;
    border: none;
}

#button-bar {
    height: 3;
    margin-top: 1;
    margin-bottom: 1;
    align: center middle;
}

#button-bar Button {
    margin-right: 2;
    min-width: 16;
}

#log-area {
    height: 10;
    border: round $secondary;
    background: $background;
    padding: 0 1;
}
"""


class KastApp(App):
    """Textual application for Kast 2.0."""

    TITLE = "Kast 2.0 — Dublaj Çevirisi Kast Çıkarma"
    SUB_TITLE = "Word (.docx) senaryolarından otomatik kast tablosu oluşturucu"
    CSS = TUI_CSS
    BINDINGS = [
        ("q", "quit", "Çıkış"),
        ("ctrl+r", "extract", "Kast Çıkar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="main-container"):
            with Vertical(classes="panel-box"):
                yield Label("📁 Senaryo ve Referans Dosyaları", classes="section-title")
                yield Label("Senaryo Dosyası (.docx):", classes="input-label")
                yield Input(
                    id="docx-path",
                    placeholder="DOCX dosyasını buraya sürükleyin veya tam yolunu yazın...",
                )
                yield Label("Referans PDF Dosyası (Opsiyonel):", classes="input-label")
                yield Input(
                    id="pdf-path",
                    placeholder="Opsiyonel referans .pdf dosyasını sürükleyin...",
                )

            with Horizontal(id="options-container"):
                with Vertical(classes="panel-box options-col"):
                    yield Label("📊 Karakter Sıralama Türü", classes="section-title")
                    with RadioSet(id="sort-radios"):
                        yield RadioButton(
                            "İlk Görünme Sırası (Appearance)",
                            id="sort-appearance",
                            value=True,
                        )
                        yield RadioButton(
                            "Replik Sayısına Göre (Count)",
                            id="sort-count",
                        )
                        yield RadioButton(
                            "Karakter Adına Göre (A-Z)",
                            id="sort-name",
                        )

                with Vertical(classes="panel-box options-col"):
                    yield Label("⚙️ Çıktı Seçenekleri", classes="section-title")
                    yield Checkbox(
                        "Orijinal dosyanın sonuna ekle (--in-place)",
                        id="cb-inplace",
                    )
                    yield Checkbox(
                        "Sadece kast tablosunu ayrı DOCX olarak kaydet (--standalone)",
                        id="cb-standalone",
                    )

            with Horizontal(id="button-bar"):
                yield Button("🚀 Kast Çıkar", id="btn-extract", variant="success")
                yield Button("🗑️ Temizle", id="btn-clear", variant="default")
                yield Button("❌ Çıkış", id="btn-exit", variant="error")

            with Vertical(classes="panel-box"):
                yield Label("📋 İşlem Günlüğü ve Sonuç Özeti", classes="section-title")
                yield RichLog(id="log-area", highlight=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        log = self.query_one("#log-area", RichLog)
        log.write("[bold cyan]Kast 2.0 hazır.[/bold cyan] Lütfen senaryo dosyasını yukarıdaki kutuya sürükleyin ve [bold green]Kast Çıkar[/bold green] butonuna tıklayın.")

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

    def action_clear(self) -> None:
        """Reset inputs and log area."""
        self.query_one("#docx-path", Input).value = ""
        self.query_one("#pdf-path", Input).value = ""
        self.query_one("#cb-inplace", Checkbox).value = False
        self.query_one("#cb-standalone", Checkbox).value = False
        self.query_one("#sort-appearance", RadioButton).value = True
        log = self.query_one("#log-area", RichLog)
        log.clear()
        log.write("[dim]Tüm alanlar temizlendi.[/dim]")

    def action_extract(self) -> None:
        """Execute cast extraction with the selected options."""
        log = self.query_one("#log-area", RichLog)
        docx_raw = self.query_one("#docx-path", Input).value.strip()
        pdf_raw = self.query_one("#pdf-path", Input).value.strip()

        docx_path = docx_raw.strip("'\"")
        pdf_path = pdf_raw.strip("'\"") if pdf_raw else None

        if not docx_path:
            log.write("[bold red][!] Hata:[/bold red] Lütfen geçerli bir .docx dosyası belirtin.")
            return

        if not os.path.exists(docx_path):
            log.write(f"[bold red][!] Hata:[/bold red] Dosya bulunamadı: [yellow]{docx_path}[/yellow]")
            return

        if not docx_path.lower().endswith(".docx"):
            log.write(f"[bold red][!] Hata:[/bold red] Seçilen dosya bir Word dökümanı (.docx) değil.")
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
            log.write(f"[bold green][✓] Başarıyla tamamlandı![/bold green]")
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
