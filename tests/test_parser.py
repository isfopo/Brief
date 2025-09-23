"""Tests for parser module."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from parser import parse_epub, parse_pdf, clean_extracted_text


class TestCleanExtractedText:
    """Test clean_extracted_text function."""

    def test_clean_basic_text(self):
        """Test basic text cleaning."""
        text = "  Hello   world  \n\n  This is a test.  "
        result = clean_extracted_text(text)
        assert result == "Hello world\n\nThis is a test."

    def test_remove_page_numbers(self):
        """Test removal of page numbers."""
        text = "Chapter 1\n\n1\n\nContent here\n\n2\n\nMore content"
        result = clean_extracted_text(text)
        assert "Chapter 1" in result
        assert "Content here" in result
        assert "More content" in result
        # Page numbers should be removed
        assert result.count("1") == 1  # only in "Chapter 1"
        assert "2" not in result

    def test_remove_short_lines(self):
        """Test removal of short non-capital lines."""
        text = "This is a long sentence.\n\nx\n\nAnother long sentence."
        result = clean_extracted_text(text)
        assert "x" not in result
        assert "This is a long sentence." in result

    def test_preserve_short_capital_lines(self):
        """Test preservation of short capital lines."""
        text = "Chapter 1\n\nThe\n\nContent"
        result = clean_extracted_text(text)
        assert "The" in result
        assert "Chapter 1" in result

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        text = "Word1\t\tword2\n\n\nWord3"
        result = clean_extracted_text(text)
        assert result == "Word1 word2\n\nWord3"


class TestParseEpub:
    """Test parse_epub function."""

    def test_file_not_exists(self):
        """Test error when file does not exist."""
        with pytest.raises(ValueError, match="File does not exist"):
            parse_epub("nonexistent.epub")

    @patch('ebooklib.epub.read_epub')
    def test_invalid_epub(self, mock_read):
        """Test error for invalid EPUB."""
        mock_read.side_effect = Exception("Invalid EPUB")
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ValueError, match="Failed to parse EPUB file"):
                parse_epub("test.epub")

    @patch('ebooklib.epub.read_epub')
    def test_successful_parsing(self, mock_read):
        """Test successful EPUB parsing."""
        # Mock book and items
        mock_book = mock_read.return_value
        mock_item = type('MockItem', (), {
            'get_type': lambda self: 9,  # ITEM_DOCUMENT
            'get_content': lambda self: b'<p>Hello world</p>'
        })()
        mock_book.get_items.return_value = [mock_item]

        with patch('pathlib.Path.exists', return_value=True):
            result = parse_epub("test.epub")
            assert "Hello world" in result


class TestParsePdf:
    """Test parse_pdf function."""

    def test_file_not_exists(self):
        """Test error when file does not exist."""
        with pytest.raises(ValueError, match="File does not exist"):
            parse_pdf("nonexistent.pdf")

    @patch('pypdf.PdfReader')
    def test_invalid_pdf(self, mock_reader):
        """Test error for invalid PDF."""
        mock_reader.side_effect = Exception("Invalid PDF")
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ValueError, match="Failed to parse PDF file"):
                parse_pdf("test.pdf")

    @patch('parser.PdfReader')
    def test_no_text_pdf(self, mock_reader):
        """Test error for PDF with no extractable text."""
        mock_reader.return_value.pages = []
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ValueError, match="No text found in PDF"):
                parse_pdf("test.pdf")

    @patch('parser.PdfReader')
    def test_successful_parsing(self, mock_reader):
        """Test successful PDF parsing."""
        mock_page = type('MockPage', (), {'extract_text': lambda self: 'Hello world'})()
        mock_reader.return_value.pages = [mock_page]

        with patch('pathlib.Path.exists', return_value=True):
            result = parse_pdf("test.pdf")
            assert "Hello world" in result