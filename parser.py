"""Module for parsing book files."""

from pathlib import Path
import ebooklib
import re
from ebooklib import epub
from pypdf import PdfReader


def clean_extracted_text(text: str) -> str:
    """Clean extracted text by normalizing encoding, removing headers/footers, and cleaning whitespace.

    Args:
        text: Raw extracted text.

    Returns:
        Cleaned text.
    """

    # Split into paragraphs (double newlines)
    paragraphs = re.split(r'\n\s*\n', text)

    cleaned_paragraphs = []
    for para in paragraphs:
        # Clean within paragraph: normalize whitespace
        para = re.sub(r'\s+', ' ', para.strip())
        if para:
            # Split into lines
            lines = para.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Skip lines that are just numbers (page numbers)
                if re.match(r'^\d+$', line):
                    continue
                # Skip very short lines that might be headers/footers (less than 10 chars, not starting with capital)
                if len(line) < 10 and not line[0].isupper():
                    continue
                cleaned_lines.append(line)
            if cleaned_lines:
                cleaned_paragraphs.append(' '.join(cleaned_lines))

    # Join paragraphs with double newlines
    return '\n\n'.join(cleaned_paragraphs)


def parse_epub(file_path: str) -> str:
    """Parse an EPUB file and extract text content.

    Args:
        file_path: Path to the EPUB file.

    Returns:
        Extracted text content from the book.

    Raises:
        ValueError: If the file cannot be parsed as EPUB.
    """
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    try:
        book = epub.read_epub(file_path)
    except Exception as e:
        raise ValueError(f"Failed to parse EPUB file: {e}")

    text_content = []

    # Iterate through all documents in the book
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Get the content and clean it
            content = item.get_content().decode('utf-8')
            # Simple text extraction - remove HTML tags
            import re
            cleaned_content = re.sub(r'<[^>]+>', '', content)
            cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
            if cleaned_content:
                text_content.append(cleaned_content)

    raw_text = '\n\n'.join(text_content)
    return clean_extracted_text(raw_text)


def parse_pdf(file_path: str) -> str:
    """Parse a PDF file and extract text content.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text content from the PDF.

    Raises:
        ValueError: If the file cannot be parsed as PDF.
    """
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    try:
        reader = PdfReader(file_path)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF file: {e}")

    text_content = []

    # Extract text from each page
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            text_content.append(text.strip())

    extracted_text = '\n\n'.join(text_content)

    # If no text extracted, it might be a scanned PDF requiring OCR
    if not extracted_text.strip():
        # Note: OCR implementation would require additional dependencies like pytesseract
        # For now, raise an error indicating OCR is needed
        raise ValueError("No text found in PDF. This appears to be a scanned document requiring OCR, which is not yet implemented.")

    return clean_extracted_text(extracted_text)