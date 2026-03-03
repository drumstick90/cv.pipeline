"""Extract text from PDFs using raw text extraction (simulates CMD+A -> CMD+C)."""

from pypdf import PdfReader
from io import BytesIO


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF in reading order.
    Simulates what a user gets when opening a PDF in a viewer,
    selecting all (CMD+A) and copying (CMD+C) — no AI parsing.
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)
