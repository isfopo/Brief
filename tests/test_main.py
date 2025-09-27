"""Tests for main module."""

from unittest.mock import patch


@patch('pathlib.Path.exists')
@patch('pathlib.Path.is_file')
def test_is_valid_book_file_epub(mock_is_file, mock_exists):
    """Test valid EPUB file."""
    mock_exists.return_value = True
    mock_is_file.return_value = True
    from main import MainWindow
    window = MainWindow()
    assert window._is_valid_book_file("test.epub") == True


@patch('pathlib.Path.exists')
@patch('pathlib.Path.is_file')
def test_is_valid_book_file_pdf(mock_is_file, mock_exists):
    """Test valid PDF file."""
    mock_exists.return_value = True
    mock_is_file.return_value = True
    from main import MainWindow
    window = MainWindow()
    assert window._is_valid_book_file("test.pdf") == True


def test_is_valid_book_file_invalid():
    """Test invalid file extension."""
    from main import MainWindow
    window = MainWindow()
    assert window._is_valid_book_file("test.txt") == False


def test_is_valid_book_file_no_extension():
    """Test file without extension."""
    from main import MainWindow
    window = MainWindow()
    assert window._is_valid_book_file("test") == False


@patch('pathlib.Path.exists')
def test_is_valid_book_file_not_exists(mock_exists):
    """Test file that doesn't exist."""
    mock_exists.return_value = False
    from main import MainWindow
    window = MainWindow()
    assert window._is_valid_book_file("nonexistent.epub") == False


@patch('pathlib.Path.exists')
@patch('pathlib.Path.is_file')
def test_is_valid_book_file_not_file(mock_is_file, mock_exists):
    """Test path that is not a file."""
    mock_exists.return_value = True
    mock_is_file.return_value = False
    from main import MainWindow
    window = MainWindow()
    assert window._is_valid_book_file("directory.epub") == False