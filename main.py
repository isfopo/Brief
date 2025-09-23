import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QListWidget, QMainWindow, QMessageBox, QVBoxLayout, QWidget
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

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        """Handle drag enter events to accept file drops."""
        if a0 is None:
            return
        mime_data = a0.mimeData()
        if mime_data and mime_data.hasUrls():
            urls = mime_data.urls()
            if any(self._is_valid_book_file(url.toLocalFile()) for url in urls):
                a0.acceptProposedAction()

    def dropEvent(self, a0: QDropEvent | None) -> None:
        """Handle drop events to process dropped files."""
        if a0 is None:
            return
        mime_data = a0.mimeData()
        if mime_data is None:
            return
        urls = mime_data.urls()
        file_paths = [url.toLocalFile() for url in urls]
        valid_files = [path for path in file_paths if self._is_valid_book_file(path)]
        invalid_files = [path for path in file_paths if not self._is_valid_book_file(path)]
        
        self.list_widget.clear()
        if valid_files:
            self.list_widget.addItem("Dropped files:")
            for file in valid_files:
                self.list_widget.addItem(f"  {Path(file).name}")
        else:
            self.list_widget.addItem("No valid book files found")
        
        if invalid_files:
            invalid_names = [Path(f).name for f in invalid_files]
            self._show_error_message(f"The following files are not supported: {', '.join(invalid_names)}. Only EPUB and PDF files are accepted.")
        
        a0.acceptProposedAction()

    def _is_valid_book_file(self, file_path: str) -> bool:
        """Check if the file is a valid book format (epub or pdf)."""
        path = Path(file_path)
        return path.exists() and path.is_file() and path.suffix.lower() in ['.epub', '.pdf']

    def _show_error_message(self, message: str) -> None:
        """Show an error message dialog."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Unsupported File Format")
        msg_box.setText(message)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())