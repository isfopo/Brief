"""Tests for storage module."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from services.storage import get_file_path, save_summary, load_summary, SummaryData


class TestGetFilePath:
    """Test get_file_path function."""

    @patch('services.storage.STORAGE_DIR', Path('/tmp/test_storage'))
    def test_get_file_path(self):
        """Test file path generation."""
        book_path = "/path/to/book.epub"
        expected_hash = "d41d8cd98f00b204e9800998ecf8427e"  # MD5 of empty string, but actually for the path
        # Actually calculate the hash
        import hashlib
        expected_hash = hashlib.md5(book_path.encode('utf-8')).hexdigest()
        expected_path = Path('/tmp/test_storage') / f"{expected_hash}.summary.json.gz"
        result = get_file_path(book_path)
        assert result == expected_path


class TestSaveSummary:
    """Test save_summary function."""

    def test_save_summary_missing_metadata(self):
        """Test ValueError for missing metadata fields."""
        metadata = {"title": "Test", "author": "Author"}  # missing path, timestamp
        with pytest.raises(ValueError, match="Missing metadata field"):
            save_summary(metadata, "summary text")

    @patch('services.storage.STORAGE_DIR', Path('/tmp/test_storage'))
    @patch('pathlib.Path.mkdir')
    @patch('gzip.open', new_callable=mock_open)
    @patch('json.dumps')
    def test_save_summary_success(self, mock_json_dumps, mock_gzip_open, mock_mkdir):
        """Test successful summary saving."""
        metadata = {
            "title": "Test Book",
            "author": "Test Author",
            "path": "/path/to/book.epub",
            "timestamp": "2023-01-01T00:00:00Z"
        }
        summary = "This is a test summary."

        mock_json_dumps.return_value = '{"test": "data"}'

        save_summary(metadata, summary)

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_json_dumps.assert_called_once()
        mock_gzip_open.assert_called_once()


class TestLoadSummary:
    """Test load_summary function."""

    @patch('services.storage.STORAGE_DIR', Path('/tmp/test_storage'))
    @patch('pathlib.Path.exists', return_value=False)
    def test_load_summary_not_found(self, mock_exists):
        """Test returning None when file does not exist."""
        result = load_summary("/path/to/book.epub")
        assert result is None

    @patch('services.storage.STORAGE_DIR', Path('/tmp/test_storage'))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('gzip.open', new_callable=mock_open, read_data='{"title": "Test", "author": "Author", "path": "/path/to/book.epub", "timestamp": "2023-01-01T00:00:00Z", "summary": "Test summary"}')
    @patch('json.loads')
    def test_load_summary_success(self, mock_json_loads, mock_gzip_open, mock_exists):
        """Test successful summary loading."""
        mock_json_loads.return_value = {
            "title": "Test Book",
            "author": "Test Author",
            "path": "/path/to/book.epub",
            "timestamp": "2023-01-01T00:00:00Z",
            "summary": "Test summary"
        }

        result = load_summary("/path/to/book.epub")

        assert isinstance(result, SummaryData)
        assert result.title == "Test Book"
        assert result.summary == "Test summary"

    @patch('services.storage._cache', {'/path/to/book.epub': SummaryData(title="Cached", author="Author", path="/path/to/book.epub", timestamp="2023-01-01T00:00:00Z", summary="Cached summary")})
    def test_load_summary_cache_hit(self):
        """Test returning cached data without file access."""
        result = load_summary("/path/to/book.epub")
        assert isinstance(result, SummaryData)
        assert result.title == "Cached"
        assert result.summary == "Cached summary"

    @patch('services.storage._cache', {})
    @patch('services.storage.STORAGE_DIR', Path('/tmp/test_storage'))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('gzip.open', side_effect=OSError("Gzip error"))
    def test_load_summary_corruption(self, mock_gzip_open, mock_exists):
        """Test handling of corrupted files."""
        result = load_summary("/path/to/book.epub")
        assert result is None

    def test_load_summary_invalid_input(self):
        """Test handling of invalid input."""
        assert load_summary("") is None
        assert load_summary(None) is None  # type: ignore
        assert load_summary(123) is None  # type: ignore

    @patch('services.storage._cache', {})
    @patch('services.storage.STORAGE_DIR', Path('/tmp/test_storage'))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('gzip.open', new_callable=mock_open, read_data='invalid json')
    @patch('json.loads', side_effect=json.JSONDecodeError("Invalid JSON", "invalid json", 0))
    def test_load_summary_invalid_json(self, mock_json_loads, mock_gzip_open, mock_exists):
        """Test handling of invalid JSON."""
        result = load_summary("/path/to/book.epub")
        assert result is None