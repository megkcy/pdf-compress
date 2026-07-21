#!/usr/bin/env python3
"""Losslessly compress PDF files.

Re-encodes content streams with maximum deflate compression and
deduplicates identical objects (fonts, images, etc). Does not touch
image or text quality, so output is visually/textually identical to
the input.

Usage:
    python compress_pdf.py input.pdf
    python compress_pdf.py input.pdf output.pdf
    python compress_pdf.py some_folder/                # batch, writes *_compressed.pdf next to each source
    python compress_pdf.py some_folder/ out_folder/     # batch, mirrors folder structure into out_folder
    python compress_pdf.py input.pdf --in-place         # overwrite the original
"""
import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def compress_pdf(input_path: Path, output_path: Path, level: int = 9) -> tuple[int, int]:
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        page.compress_content_streams(level=level)

    if hasattr(writer, "compress_identical_objects"):
        try:
            writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
        except TypeError:
            writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return input_path.stat().st_size, output_path.stat().st_size


def iter_pdfs(path: Path):
    if path.is_file():
        yield path
    else:
        yield from sorted(path.rglob("*.pdf"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="PDF file or folder")
    parser.add_argument("output", type=Path, nargs="?", help="Output file or folder (default: *_compressed.pdf next to input)")
    parser.add_argument("--level", type=int, default=9, choices=range(0, 10), help="Deflate compression level 0-9 (default 9)")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the input file(s) instead of writing a new one")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Not found: {args.input}")
    if args.in_place and args.output:
        sys.exit("--in-place cannot be combined with an output path")

    targets = list(iter_pdfs(args.input))
    if not targets:
        sys.exit("No PDF files found.")

    total_before = total_after = 0
    for src in targets:
        try:
            if args.in_place:
                tmp = src.with_suffix(src.suffix + ".tmp")
                before, after = compress_pdf(src, tmp, args.level)
                tmp.replace(src)
            elif args.output:
                dst = args.output if args.input.is_file() else args.output / src.relative_to(args.input)
                before, after = compress_pdf(src, dst, args.level)
            else:
                dst = src.with_name(f"{src.stem}_compressed.pdf")
                before, after = compress_pdf(src, dst, args.level)
        except Exception as exc:
            print(f"{src.name}: FAILED ({exc})", file=sys.stderr)
            continue

        total_before += before
        total_after += after
        pct = (1 - after / before) * 100 if before else 0
        print(f"{src.name}: {before / 1024:.1f} KB -> {after / 1024:.1f} KB ({pct:.1f}% smaller)")

    if len(targets) > 1 and total_before:
        pct = (1 - total_after / total_before) * 100
        print(f"\nTotal: {total_before / 1024:.1f} KB -> {total_after / 1024:.1f} KB ({pct:.1f}% smaller)")


if __name__ == "__main__":
    main()
