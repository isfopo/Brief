"""Pytest configuration and fixtures."""

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Create QApplication instance for GUI tests."""
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture(scope="session", autouse=True)
def preload_summarizer():
    """Preload the summarizer model for tests."""
    from services.summarizer import preload_model
    preload_model()