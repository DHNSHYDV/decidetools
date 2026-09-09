#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path
from converter import convert_file, ConversionError


def main():
    parser = argparse.ArgumentParser(
        description="Fast & Simple Local File Converter: DOCX ↔ PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py report.docx              # Converts report.docx -> report.pdf
  python cli.py document.pdf             # Converts document.pdf -> document.docx
  python cli.py report.docx -o final.pdf # Specifies custom output path
        """
    )

    parser.add_argument("input_file", help="Path to the input file (.docx, .doc, or .pdf)")
    parser.add_argument("-o", "--output", help="Path to the converted output file (optional)", default=None)

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file does not exist: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    suffix = input_path.suffix.lower()
    if suffix in [".docx", ".doc"]:
        target_fmt = "PDF"
    elif suffix == ".pdf":
        target_fmt = "DOCX"
    else:
        print(f"Error: Unsupported file format '{suffix}'. Supported formats: .docx, .doc, .pdf", file=sys.stderr)
        sys.exit(1)

    print(f"Converting '{input_path.name}' to {target_fmt}...")
    start_time = time.time()

    try:
        output_file = convert_file(args.input_file, args.output)
        elapsed = time.time() - start_time
        print(f"Conversion successful ({elapsed:.2f}s)!")
        print(f"Output saved to: {output_file}")
    except ConversionError as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
