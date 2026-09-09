"""
Backward compatibility layer for converter module.
Redirects to modules.file_converter.
"""
from modules.file_converter import (
    docx_to_pdf,
    pdf_to_docx,
    convert_file,
    ConversionError
)

__all__ = ["docx_to_pdf", "pdf_to_docx", "convert_file", "ConversionError"]
