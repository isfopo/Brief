"""Integration tests for the summarization pipeline."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from services.parser import parse_epub, parse_pdf, BookMetadata
from services import summarizer, storage
from main import SummarizationWorker


class TestIntegration:
    """Test the full summarization and storage pipeline."""

    @patch('services.summarizer.summarize_book')
    @patch('services.storage.save_summary')
    def test_summarization_worker_success(self, mock_save, mock_summarize):
        """Test successful summarization worker execution."""
        # Setup mocks
        mock_summarize.return_value = "This is a summary."

        # Create test data
        text = "This is the full book text."
        metadata = BookMetadata(
            title="Test Book",
            author="Test Author",
            path="/path/to/book.epub",
            timestamp="2023-01-01T00:00:00"
        )

        # Create worker
        worker = SummarizationWorker("/path/to/book.epub", text, metadata)

        # Mock signals
        finished_called = False
        error_called = False

        def on_finished(file_path, message):
            nonlocal finished_called
            finished_called = True
            assert file_path == "/path/to/book.epub"
            assert "Summarized and saved: Test Book" in message

        def on_error(file_path, error_msg):
            nonlocal error_called
            error_called = True

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)

        # Run worker
        worker.run()

        # Assertions
        assert finished_called
        assert not error_called
        mock_summarize.assert_called_once_with(text)
        mock_save.assert_called_once_with({
            'title': 'Test Book',
            'author': 'Test Author',
            'path': '/path/to/book.epub',
            'timestamp': '2023-01-01T00:00:00'
        }, "This is a summary.")

    @patch('services.summarizer.summarize_book')
    def test_summarization_worker_summarization_failure(self, mock_summarize):
        """Test worker when summarization fails."""
        # Setup mock to fail
        mock_summarize.return_value = ""

        # Create test data
        text = "This is the full book text."
        metadata = BookMetadata(
            title="Test Book",
            author="Test Author",
            path="/path/to/book.epub",
            timestamp="2023-01-01T00:00:00"
        )

        # Create worker
        worker = SummarizationWorker("/path/to/book.epub", text, metadata)

        # Mock signals
        finished_called = False
        error_called = False

        def on_finished(file_path, message):
            nonlocal finished_called
            finished_called = True

        def on_error(file_path, error_msg):
            nonlocal error_called
            error_called = True
            assert file_path == "/path/to/book.epub"
            assert "Summarization failed" in error_msg

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)

        # Run worker
        worker.run()

        # Assertions
        assert not finished_called
        assert error_called
        mock_summarize.assert_called_once_with(text)

    @patch('services.storage.save_summary')
    @patch('services.summarizer.summarize_book')
    def test_summarization_worker_storage_failure(self, mock_summarize, mock_save):
        """Test worker when storage fails."""
        # Setup mocks
        mock_summarize.return_value = "This is a summary."
        mock_save.side_effect = Exception("Storage error")

        # Create test data
        text = "This is the full book text."
        metadata = BookMetadata(
            title="Test Book",
            author="Test Author",
            path="/path/to/book.epub",
            timestamp="2023-01-01T00:00:00"
        )

        # Create worker
        worker = SummarizationWorker("/path/to/book.epub", text, metadata)

        # Mock signals
        finished_called = False
        error_called = False

        def on_finished(file_path, message):
            nonlocal finished_called
            finished_called = True

        def on_error(file_path, error_msg):
            nonlocal error_called
            error_called = True
            assert file_path == "/path/to/book.epub"
            assert "Storage error" in error_msg

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)

        # Run worker
        worker.run()

        # Assertions
        assert not finished_called
        assert error_called
        mock_summarize.assert_called_once_with(text)
        mock_save.assert_called_once()

    def test_parser_metadata_extraction_epub(self):
        """Test metadata extraction from EPUB (mocked)."""
        with patch('ebooklib.epub.read_epub') as mock_read, \
             patch('pathlib.Path.exists', return_value=True):

            # Mock book with metadata
            mock_book = MagicMock()
            mock_book.get_metadata.side_effect = lambda ns, name: {
                ('DC', 'title'): [('Test Title', {})],
                ('DC', 'creator'): [('Test Author', {})]
            }.get((ns, name), [])
            mock_book.get_items.return_value = []

            mock_read.return_value = mock_book

            text, metadata = parse_epub("test.epub")

            assert metadata.title == "Test Title"
            assert metadata.author == "Test Author"
            assert metadata.path == "test.epub"
            assert isinstance(metadata.timestamp, str)

    def test_parser_metadata_extraction_pdf(self):
        """Test metadata extraction from PDF."""
        with patch('services.parser.PdfReader') as mock_reader, \
             patch('pathlib.Path.exists', return_value=True):

            # Mock PDF reader
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Some text content"
            mock_reader.return_value.pages = [mock_page]

            text, metadata = parse_pdf("test.pdf")

            assert metadata.title == "test"  # filename stem
            assert metadata.author == "Unknown"
            assert metadata.path == "test.pdf"
            assert isinstance(metadata.timestamp, str)
            assert "Some text content" in text