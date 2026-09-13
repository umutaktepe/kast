#!/usr/bin/env python3
"""Dublaj Çevirisi Kast Çıkarma Sistemi (Kast 2.0).

CLI ve kütüphane arayüzü: Dublaj DOCX senaryolarını okuyarak kast tablosunu
otomatik oluşturur ve Word dökümanına ekler veya ayrı dosya olarak kaydeder.
"""

import argparse
import os
import sys

# Proje sanal ortamını (.venv) veya kullanıcı paketlerini otomatik algıla
try:
    import docx
except ImportError:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_site = os.path.join(base_dir, ".venv", "lib")
    if os.path.isdir(venv_site):
        for py_dir in os.listdir(venv_site):
            sp = os.path.join(venv_site, py_dir, "site-packages")
            if os.path.isdir(sp) and sp not in sys.path:
                sys.path.insert(0, sp)
    user_site = os.path.expanduser("~/.local/lib")
    if os.path.isdir(user_site):
        for py_dir in os.listdir(user_site):
            sp = os.path.join(user_site, py_dir, "site-packages")
            if os.path.isdir(sp) and sp not in sys.path:
                sys.path.insert(0, sp)

from collections import OrderedDict
from typing import List, Optional

from docx import Document

from src.models import CastExtractionResult, CharacterStats
from src.paginator import DocumentPaginator
from src.parser import DubbingDocxParser
from src.table_writer import CastTableWriter


def process_cast_document(
    docx_path: str,
    output_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    sort_by: str = "appearance",
    standalone: bool = False,
) -> str:
    """Process a dubbing DOCX script, extract cast statistics, and output cast table.

    Args:
        docx_path: Path to the input dubbing script .docx file.
        output_path: Optional destination .docx path. If None, saves as <basename>_kast.docx.
        pdf_path: Optional reference PDF path for page number detection.
        sort_by: Character sorting mode ('appearance', 'count', or 'name').
        standalone: If True, outputs a standalone document with only the cast table.
                    If False (default), appends the cast table to the script document.

    Returns:
        The output file path.
    """
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

    # 3. Karakter istatistiklerini derle
    characters_map: OrderedDict[str, CharacterStats] = OrderedDict()
    appearance_counter = 0

    for p in assigned_paras:
        if not p.speaker or not p.dialogue:
            continue
        if p.speaker not in characters_map:
            appearance_counter += 1
            characters_map[p.speaker] = CharacterStats(
                name=p.speaker,
                first_seen_order=appearance_counter,
            )
        characters_map[p.speaker].add_line(page=p.page or 1)

    char_list = list(characters_map.values())
    if sort_by == "count":
        char_list.sort(key=lambda x: x.line_count, reverse=True)
    elif sort_by == "name":
        char_list.sort(key=lambda x: x.name)
    else:  # appearance
        char_list.sort(key=lambda x: x.first_seen_order)

    print(f"[+] {len(char_list)} farklı karakter tespit edildi.")

    result = CastExtractionResult(
        characters=char_list,
        total_lines=len(dialogue_paras),
        total_pages=max((p.page for p in assigned_paras if p.page), default=1),
    )

    # 4. Kast tablosunu dökümana ekle
    writer = CastTableWriter()
    if standalone:
        target_doc = Document()
        writer.append_cast_table(target_doc, result, add_page_break=False)
        save_doc = target_doc
    else:
        writer.append_cast_table(doc, result, add_page_break=True)
        save_doc = doc

    # 5. Kaydet
    if not output_path:
        base, ext = os.path.splitext(docx_path)
        output_path = f"{base}_kast{ext}"

    save_doc.save(output_path)
    print(f"[✓] Başarıyla tamamlandı! Kast tablosu kaydedildi:")
    print(f"    -> {output_path}")
    return output_path


def build_cli_parser() -> argparse.ArgumentParser:
    """Build command line argument parser for Kast CLI."""
    parser = argparse.ArgumentParser(
        description="DUBLAJ ÇEVİRİSİ KAST ÇIKARMA PROGRAMI (Kast 2.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "docx_file",
        nargs="?",
        default=None,
        help="İşlenecek dublaj DOCX dosyasının yolu.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        default=None,
        help="Çıktı DOCX dosya yolu (varsayılan: <dosya>_kast.docx).",
    )
    parser.add_argument(
        "--sort",
        dest="sort_by",
        choices=["appearance", "count", "name"],
        default="appearance",
        help="Karakter sıralama türü: appearance (varsayılan), count veya name.",
    )
    parser.add_argument(
        "--in-place",
        dest="in_place",
        action="store_true",
        help="Tabloyu orijinal dökümanın üzerine kaydet.",
    )
    parser.add_argument(
        "--pdf",
        dest="pdf_path",
        default=None,
        help="Sayfa tespiti için opsiyonel referans PDF dosyası yolu.",
    )
    parser.add_argument(
        "--standalone",
        dest="standalone",
        action="store_true",
        help="Kast tablosunu orijinal metin olmadan ayrı bir DOCX olarak kaydet.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI and interactive entry point."""
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    print("=" * 60)
    print(" DUBLAJ ÇEVİRİSİ KAST ÇIKARMA PROGRAMI (Kast 2.0)")
    print("=" * 60)

    docx_file = args.docx_file
    if not docx_file:
        raw_input = input("Lütfen çeviri DOCX dosyasını buraya sürükleyip bırakın ve Enter'a basın:\n> ")
        docx_file = raw_input.strip("'\"")

    if not docx_file:
        print("Hata: Dosya belirtilmedi.")
        return 1

    docx_file = docx_file.strip("'\"")

    if args.in_place and args.standalone:
        print("Hata: --in-place ve --standalone seçenekleri birlikte kullanılamaz.")
        return 1

    output_path = args.output_path
    if args.in_place:
        output_path = docx_file

    try:
        process_cast_document(
            docx_path=docx_file,
            output_path=output_path,
            pdf_path=args.pdf_path,
            sort_by=args.sort_by,
            standalone=args.standalone,
        )
        return 0
    except Exception as e:
        print(f"\n[!] Bir hata oluştu: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
