import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from pdf2docx import Converter


class ConversionError(Exception):
    """Custom exception raised when file conversion fails."""
    pass


def docx_to_pdf(input_path: str, output_path: str = None) -> str:
    """
    Convert a DOCX file to PDF using LibreOffice in headless mode.
    """
    in_file = Path(input_path).resolve()
    if not in_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if in_file.suffix.lower() not in [".docx", ".doc"]:
        raise ValueError(f"Expected a Word document (.docx/.doc), got: {in_file.suffix}")

    if output_path is None:
        out_file = in_file.with_suffix(".pdf")
    else:
        out_file = Path(output_path).resolve()

    out_file.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            str(in_file),
            "--outdir",
            temp_dir
        ]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"LibreOffice conversion failed: {e.stderr or e.stdout}")

        expected_converted = Path(temp_dir) / f"{in_file.stem}.pdf"
        if not expected_converted.exists():
            raise ConversionError(f"LibreOffice failed to produce PDF output: {result.stderr}")

        shutil.move(str(expected_converted), str(out_file))

    return str(out_file)


def pdf_to_docx(input_path: str, output_path: str = None) -> str:
    """
    Convert a PDF file to DOCX using pdf2docx.
    """
    in_file = Path(input_path).resolve()
    if not in_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if in_file.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file (.pdf), got: {in_file.suffix}")

    if output_path is None:
        out_file = in_file.with_suffix(".docx")
    else:
        out_file = Path(output_path).resolve()

    out_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        cv = Converter(str(in_file))
        cv.convert(str(out_file))
        cv.close()
    except Exception as e:
        raise ConversionError(f"PDF to DOCX conversion failed: {e}")

    if not out_file.exists():
        raise ConversionError("pdf2docx failed to create DOCX output file.")

    return str(out_file)


def convert_file(input_path: str, output_path: str = None) -> str:
    """
    Automatically detects the file extension and converts:
      .docx/.doc -> .pdf
      .pdf -> .docx
    """
    in_file = Path(input_path)
    suffix = in_file.suffix.lower()

    if suffix in [".docx", ".doc"]:
        return docx_to_pdf(input_path, output_path)
    elif suffix == ".pdf":
        return pdf_to_docx(input_path, output_path)
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Supported formats: .docx, .doc, .pdf")
