"""Pytest configuration and fixtures."""

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Create QApplication instance for GUI tests."""
    app = QApplication([])
    yield app
    app.quit()