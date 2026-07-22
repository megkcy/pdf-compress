#!/usr/bin/env python3
"""Compress PDF files.

By default, only re-encodes content streams with maximum deflate
compression. Does not touch image or text quality, so output is
visually/textually identical to the input (truly lossless).

Pass --lossy to also recompress embedded raster images as JPEG at a
given quality. This DOES reduce image quality, but shrinks image-heavy
PDFs much more than the lossless mode can.

Pass --dedup to additionally merge duplicate objects (repeated fonts,
repeated images, orphaned objects) via pypdf's compress_identical_objects.
This can save a lot more space, but that pypdf feature has a history of
hash-collision bugs that can wrongly merge two DIFFERENT images and
corrupt the output. To guard against that, every image is fingerprinted
before and after dedup; if anything doesn't match up, this tool discards
the dedup result and silently falls back to the safe (non-dedup) output
for that file, and prints a warning.

Usage:
    python compress_pdf.py                              # no args: compress every *.pdf sitting next to this script
    python compress_pdf.py input.pdf
    python compress_pdf.py input.pdf output.pdf
    python compress_pdf.py some_folder/                # batch, writes *_compressed.pdf next to each source
    python compress_pdf.py some_folder/ out_folder/     # batch, mirrors folder structure into out_folder
    python compress_pdf.py input.pdf --in-place         # overwrite the original
    python compress_pdf.py input.pdf --lossy                        # also recompress images (default quality 80)
    python compress_pdf.py input.pdf --lossy --image-quality 60     # more aggressive image recompression
    python compress_pdf.py input.pdf --dedup                        # also merge duplicate objects (verified safe)
"""
import argparse
import hashlib
import io
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def _recompress_image(img, quality: int) -> None:
    """Replace img with a JPEG re-encode, but only if that's actually smaller."""
    pil_img = img.image
    if pil_img is None:
        return
    if pil_img.mode not in ("RGB", "L"):
        pil_img = pil_img.convert("RGB")

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality, optimize=True)
    new_size = buf.tell()

    # img.data is the image's raw bytes as currently stored in the PDF stream.
    # Only swap in the re-encode if it actually saves meaningful space -
    # small/already-optimized images can come out LARGER as JPEG.
    if new_size < len(img.data) * 0.9:
        img.replace(pil_img, quality=quality, optimize=True)


def _image_signatures(pages) -> list:
    """Per-page list of image content hashes, used to detect dedup corruption."""
    sigs = []
    for page in pages:
        page_sigs = []
        try:
            for img in page.images:
                page_sigs.append(hashlib.sha256(img.data).hexdigest())
        except Exception:
            pass
        sigs.append(page_sigs)
    return sigs


def _run_dedup(writer: PdfWriter) -> None:
    try:
        writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
    except TypeError:
        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)


def compress_pdf(
    input_path: Path,
    output_path: Path,
    level: int = 9,
    lossy: bool = False,
    image_quality: int = 80,
    dedup: bool = False,
) -> tuple[int, int, bool]:
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        page.compress_content_streams(level=level)

    dedup_ok = True
    if dedup:
        before_sigs = _image_signatures(PdfReader(str(input_path)).pages)
        _run_dedup(writer)
        after_sigs = _image_signatures(writer.pages)
        if after_sigs != before_sigs:
            dedup_ok = False
            # Corruption detected - throw away this writer and rebuild cleanly without dedup.
            writer = PdfWriter()
            writer.append(PdfReader(str(input_path)))
            for page in writer.pages:
                page.compress_content_streams(level=level)

    if lossy:
        for page in writer.pages:
            for img in page.images:
                try:
                    _recompress_image(img, image_quality)
                except Exception:
                    pass  # leave images pypdf/Pillow can't safely re-encode (e.g. CMYK, 1-bit) untouched

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return input_path.stat().st_size, output_path.stat().st_size, dedup_ok


def iter_pdfs(path: Path, recursive: bool = True):
    if path.is_file():
        yield path
        return
    pdfs = path.rglob("*.pdf") if recursive else path.glob("*.pdf")
    for p in sorted(pdfs):
        if p.stem.endswith("_compressed"):
            continue
        yield p


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, nargs="?", help="PDF file or folder (default: the folder this script is in)")
    parser.add_argument("output", type=Path, nargs="?", help="Output file or folder (default: *_compressed.pdf next to input)")
    parser.add_argument("--level", type=int, default=9, choices=range(0, 10), help="Deflate compression level 0-9 (default 9)")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the input file(s) instead of writing a new one")
    parser.add_argument("--lossy", action="store_true", help="Also recompress embedded images as JPEG (reduces image quality)")
    parser.add_argument("--image-quality", type=int, default=80, choices=range(1, 101), metavar="1-100",
                         help="JPEG quality when --lossy is set (default 80; lower = smaller file, worse quality)")
    parser.add_argument("--dedup", action="store_true",
                         help="Also merge duplicate objects (fonts/images/orphans) for extra savings; "
                              "auto-verified against image corruption, falls back safely if verification fails")
    args = parser.parse_args()

    recursive = args.input is not None
    if args.input is None:
        args.input = Path(__file__).resolve().parent

    if not args.input.exists():
        sys.exit(f"Not found: {args.input}")
    if args.in_place and args.output:
        sys.exit("--in-place cannot be combined with an output path")

    targets = list(iter_pdfs(args.input, recursive=recursive))
    if not targets:
        sys.exit("No PDF files found.")

    total_before = total_after = 0
    for src in targets:
        try:
            if args.in_place:
                tmp = src.with_suffix(src.suffix + ".tmp")
                before, after, dedup_ok = compress_pdf(src, tmp, args.level, args.lossy, args.image_quality, args.dedup)
                tmp.replace(src)
            elif args.output:
                dst = args.output if args.input.is_file() else args.output / src.relative_to(args.input)
                before, after, dedup_ok = compress_pdf(src, dst, args.level, args.lossy, args.image_quality, args.dedup)
            else:
                dst = src.with_name(f"{src.stem}_compressed.pdf")
                before, after, dedup_ok = compress_pdf(src, dst, args.level, args.lossy, args.image_quality, args.dedup)
        except Exception as exc:
            print(f"{src.name}: FAILED ({exc})", file=sys.stderr)
            continue

        total_before += before
        total_after += after
        pct = (1 - after / before) * 100 if before else 0
        tag = f", lossy q{args.image_quality}" if args.lossy else ""
        if args.dedup:
            tag += ", dedup" if dedup_ok else ""
        print(f"{src.name}: {before / 1024:.1f} KB -> {after / 1024:.1f} KB ({pct:.1f}% smaller{tag})")
        if args.dedup and not dedup_ok:
            print(f"  [warning] dedup verification failed for {src.name} - fell back to safe (non-dedup) output", file=sys.stderr)

    if len(targets) > 1 and total_before:
        pct = (1 - total_after / total_before) * 100
        print(f"\nTotal: {total_before / 1024:.1f} KB -> {total_after / 1024:.1f} KB ({pct:.1f}% smaller)")


if __name__ == "__main__":
    main()
