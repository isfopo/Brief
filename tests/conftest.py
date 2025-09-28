"""Pytest configuration and fixtures."""

import pytest
import logging
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Set up logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


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