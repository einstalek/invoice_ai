"""Extract text from PDF invoices using pdfplumber."""

import logging
import tempfile
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)

MAX_PAGES = 10


def extract_text_from_path(file_path: str | Path) -> str:
    """Extract text from a local PDF file path."""
    with pdfplumber.open(file_path) as pdf:
        if not pdf.pages:
            raise RuntimeError("PDF has no pages")

        pages = pdf.pages[:MAX_PAGES]
        text_parts = []

        for page in pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    full_text = "\n\n".join(text_parts)
    if not full_text.strip():
        raise RuntimeError("PDF text extraction returned empty result")

    return full_text


def extract_text(file_field) -> str:
    """
    Extract text from a Django FileField.

    Works with both local storage (uses .path) and remote storage like S3
    (downloads to a temp file first).
    """
    # Try local file path first
    try:
        return extract_text_from_path(file_field.path)
    except (NotImplementedError, AttributeError):
        pass  # S3 storage doesn't support .path

    # Remote file (S3) — download to temp file
    file_field.open("rb")
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            for chunk in file_field.chunks():
                tmp.write(chunk)
            tmp.flush()
            return extract_text_from_path(tmp.name)
    finally:
        file_field.close()
