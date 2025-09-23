"""Tests for main module."""

import pytest
from pathlib import Path
from unittest.mock import patch


def test_is_valid_book_file_epub():
    """Test valid EPUB file."""
    from main import MainWindow
    # Mock QApplication to avoid GUI issues
    with patch('PyQt6.QtWidgets.QApplication'):
        window = MainWindow()
        assert window._is_valid_book_file("test.epub") == True


def test_is_valid_book_file_pdf():
    """Test valid PDF file."""
    from main import MainWindow
    with patch('PyQt6.QtWidgets.QApplication'):
        window = MainWindow()
        assert window._is_valid_book_file("test.pdf") == True


def test_is_valid_book_file_invalid():
    """Test invalid file extension."""
    from main import MainWindow
    with patch('PyQt6.QtWidgets.QApplication'):
        window = MainWindow()
        assert window._is_valid_book_file("test.txt") == False


def test_is_valid_book_file_no_extension():
    """Test file without extension."""
    from main import MainWindow
    with patch('PyQt6.QtWidgets.QApplication'):
        window = MainWindow()
        assert window._is_valid_book_file("test") == False


@patch('pathlib.Path.exists')
def test_is_valid_book_file_not_exists(mock_exists):
    """Test file that doesn't exist."""
    mock_exists.return_value = False
    from main import MainWindow
    with patch('PyQt6.QtWidgets.QApplication'):
        window = MainWindow()
        assert window._is_valid_book_file("nonexistent.epub") == False


@patch('pathlib.Path.exists')
@patch('pathlib.Path.is_file')
def test_is_valid_book_file_not_file(mock_is_file, mock_exists):
    """Test path that is not a file."""
    mock_exists.return_value = True
    mock_is_file.return_value = False
    from main import MainWindow
    with patch('PyQt6.QtWidgets.QApplication'):
        window = MainWindow()
        assert window._is_valid_book_file("directory.epub") == False