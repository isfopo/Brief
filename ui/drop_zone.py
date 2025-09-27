from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DropZone(QWidget):
    """Widget for dropping EPUB and PDF files."""

    filesDropped = pyqtSignal(list)  # Emits list of valid file paths

    def __init__(self, parent=None) -> None:
        """Initialize the drop zone with a styled label."""
        super().__init__(parent)

        # Create layout and label
        layout = QVBoxLayout(self)
        self.label = QLabel("Drop EPUB or PDF files here")
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                padding: 20px;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.label)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        """Handle drag enter events."""
        if a0 is None:
            return
        mime_data = a0.mimeData()
        if mime_data and mime_data.hasUrls():
            urls = mime_data.urls()
            if any(self._is_valid_book_file(url.toLocalFile()) for url in urls):
                a0.acceptProposedAction()
                self.label.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #4CAF50;
                        padding: 20px;
                        border-radius: 5px;
                        background-color: #e8f5e8;
                    }
                """)

    def dragLeaveEvent(self, a0) -> None:
        """Handle drag leave events."""
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                padding: 20px;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)

    def dropEvent(self, a0: QDropEvent | None) -> None:
        """Handle drop events."""
        if a0 is None:
            return
        mime_data = a0.mimeData()
        if mime_data is None:
            return
        urls = mime_data.urls()
        file_paths = [url.toLocalFile() for url in urls]
        self.filesDropped.emit(file_paths)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                padding: 20px;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        a0.acceptProposedAction()

    def _is_valid_book_file(self, file_path: str) -> bool:
        """Check if the file is a valid book format (epub or pdf)."""
        path = Path(file_path)
        return path.exists() and path.is_file() and path.suffix.lower() in ['.epub', '.pdf']