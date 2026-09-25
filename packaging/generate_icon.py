#!/usr/bin/env python3
"""packaging/generate_icon.py — Multi-resolution Windows .ico generator for Kast 2.0 Studio."""

import argparse
import os
import sys
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_SOURCE = os.path.join(ROOT_DIR, "packaging", "assets", "kast_icon.png")
DEFAULT_OUTPUT = os.path.join(ROOT_DIR, "packaging", "assets", "kast.ico")

ICON_SIZES: List[Tuple[int, int]] = [
    (16, 16),
    (24, 24),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]


def create_fallback_image(size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """Generate a clean geometric fallback icon (dark blue circle + cyan 'K' motif)."""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark blue studio circle with cyan border
    margin = 8
    draw.ellipse(
        [margin, margin, w - margin, h - margin],
        fill=(15, 23, 42, 255),       # #0f172a
        outline=(56, 189, 248, 255),  # #38bdf8
        width=6,
    )

    # Cyan motif: geometric 'K'
    # Vertical bar
    draw.rounded_rectangle([72, 60, 96, 196], radius=4, fill=(56, 189, 248, 255))
    # Top diagonal arm
    draw.polygon([(96, 132), (168, 60), (196, 60), (120, 140)], fill=(56, 189, 248, 255))
    # Bottom diagonal leg
    draw.polygon([(112, 132), (196, 196), (168, 196), (96, 148)], fill=(56, 189, 248, 255))

    return img


def generate_icon(
    source_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """Convert source PNG/JPEG into a multi-resolution .ico file or generate fallback.

    Args:
        source_path: Path to source image. Defaults to packaging/assets/kast_icon.png.
        output_path: Target path for .ico file. Defaults to packaging/assets/kast.ico.

    Returns:
        The resolved output file path.
    """
    source = os.path.abspath(source_path) if source_path else DEFAULT_SOURCE
    target = os.path.abspath(output_path) if output_path else DEFAULT_OUTPUT

    os.makedirs(os.path.dirname(target), exist_ok=True)

    if os.path.isfile(source):
        base_img = Image.open(source).convert("RGBA")
    else:
        base_img = create_fallback_image((256, 256))

    # Resize base image to highest 256x256 resolution
    img_256 = base_img.resize((256, 256), Image.Resampling.LANCZOS)
    sub_images = [img_256.resize(s, Image.Resampling.LANCZOS) for s in ICON_SIZES]

    # Save multi-resolution icon
    img_256.save(
        target,
        format="ICO",
        sizes=ICON_SIZES,
        append_images=sub_images,
    )

    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Kast Windows icon (.ico)")
    parser.add_argument("--source", default=None, help="Source PNG/JPEG image path")
    parser.add_argument("--output", default=None, help="Output .ico file path")
    args = parser.parse_args()

    result_path = generate_icon(args.source, args.output)
    print(f"Icon successfully generated at: {result_path}")


if __name__ == "__main__":
    main()
