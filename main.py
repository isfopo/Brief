import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QListWidget, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# Constants
WINDOW_TITLE = "Brief"
WINDOW_X = 100
WINDOW_Y = 100
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 300
WELCOME_TEXT = "Welcome to Brief!"


class MainWindow(QMainWindow):
    """Main application window for the Brief book summarization app."""

    def __init__(self) -> None:
        """Initialize the main window with title, geometry, and welcome list widget."""
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create list widget for displaying files
        self.list_widget = QListWidget()
        self.list_widget.addItem(WELCOME_TEXT)
        layout.addWidget(self.list_widget)
        
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events to accept file drops."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if all(self._is_valid_book_file(url.toLocalFile()) for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events to process dropped files."""
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        valid_files = [path for path in file_paths if self._is_valid_book_file(path)]
        
        self.list_widget.clear()
        if valid_files:
            self.list_widget.addItem("Dropped files:")
            for file in valid_files:
                self.list_widget.addItem(f"  {Path(file).name}")
        else:
            self.list_widget.addItem("No valid book files found")
        event.acceptProposedAction()

    def _is_valid_book_file(self, file_path: str) -> bool:
        """Check if the file is a valid book format (epub or pdf)."""
        path = Path(file_path)
        return path.suffix.lower() in ['.epub', '.pdf']


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())