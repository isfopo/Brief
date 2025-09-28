import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QListWidget, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QThread, pyqtSignal

from ui.drop_zone import DropZone
from services.parser import parse_epub, parse_pdf, BookMetadata
from services import summarizer, storage


class SummarizationWorker(QThread):
    """Worker thread for summarization and storage."""

    finished = pyqtSignal(str, str)  # file_path, status_message
    error = pyqtSignal(str, str)     # file_path, error_message
    progress = pyqtSignal(str, str)  # file_path, progress_message

    def __init__(self, file_path: str, text: str, metadata: BookMetadata):
        super().__init__()
        self.file_path = file_path
        self.text = text
        self.metadata = metadata

    def run(self):
        try:
            self.progress.emit(self.file_path, "Starting summarization...")

            # Summarize the text
            summary = summarizer.summarize_book(self.text)
            if not summary:
                raise ValueError("Summarization failed: empty summary")

            self.progress.emit(self.file_path, "Summarization complete, saving...")

            # Save the summary
            metadata_dict = {
                'title': self.metadata.title,
                'author': self.metadata.author,
                'path': self.metadata.path,
                'timestamp': self.metadata.timestamp
            }
            storage.save_summary(metadata_dict, summary)

            self.finished.emit(self.file_path, f"Summarized and saved: {self.metadata.title}")

        except Exception as e:
            self.error.emit(self.file_path, f"Error processing {Path(self.file_path).name}: {str(e)}")


# Constants
WINDOW_TITLE = "Brief"
WINDOW_X = 200
WINDOW_Y = 200
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1200
WELCOME_TEXT = "Welcome to Brief!"


class MainWindow(QMainWindow):
    """Main application window for the Brief book summarization app."""

    def __init__(self) -> None:
        """Initialize the main window with title, geometry, and welcome list widget."""
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Keep track of workers
        self.workers = []
        # Track status per file
        self.file_status = {}
        # Track list item row per file
        self.file_rows = {}

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create list widget for displaying files
        self.list_widget = QListWidget()
        self.list_widget.addItem(WELCOME_TEXT)
        layout.addWidget(self.list_widget)

        # Create button for event handling demonstration
        self.button = QPushButton("Click me!")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)

        # Create drop zone for file uploads
        self.drop_zone = DropZone()
        layout.addWidget(self.drop_zone)
        self.drop_zone.filesDropped.connect(self.process_files)

    def process_files(self, file_paths: list[str]) -> None:
        """Process dropped files."""
        valid_files = [path for path in file_paths if self._is_valid_book_file(path)]
        invalid_files = [path for path in file_paths if not self._is_valid_book_file(path)]

        self.list_widget.clear()
        self.file_status.clear()
        self.file_rows.clear()
        if valid_files:
            self.list_widget.addItem("Processing files:")
            for file in valid_files:
                row = self.list_widget.count()
                self.list_widget.addItem(f"  {Path(file).name}: Processing...")
                self.file_rows[file] = row
                self.file_status[file] = "Processing"

                # Parse book files
                try:
                    if Path(file).suffix.lower() == '.epub':
                        text, metadata = parse_epub(file)
                    elif Path(file).suffix.lower() == '.pdf':
                        text, metadata = parse_pdf(file)
                    else:
                        continue

                    self._update_file_status(file, f"Parsed {len(text)} characters - Title: {metadata.title}, Author: {metadata.author}")

                    # Start summarization worker
                    worker = SummarizationWorker(file, text, metadata)
                    worker.finished.connect(self.on_summarization_finished)
                    worker.error.connect(self.on_summarization_error)
                    worker.progress.connect(self.on_summarization_progress)
                    self.workers.append(worker)  # Keep reference
                    worker.start()

                except ValueError as e:
                    self._update_file_status(file, f"Error: {e}")
        else:
            self.list_widget.addItem("No valid book files found")

        if invalid_files:
            invalid_names = [Path(f).name for f in invalid_files]
            self._show_error_message(f"The following files are not supported: {', '.join(invalid_names)}. Only EPUB and PDF files are accepted.")

    def on_summarization_finished(self, file_path: str, message: str):
        """Handle successful summarization."""
        self._update_file_status(file_path, f"✓ {message}")

    def on_summarization_error(self, file_path: str, error_message: str):
        """Handle summarization error."""
        self._update_file_status(file_path, f"✗ {error_message}")

    def on_summarization_progress(self, file_path: str, progress_message: str):
        """Handle summarization progress updates."""
        self._update_file_status(file_path, progress_message)

    def _update_file_status(self, file_path: str, status: str):
        """Update the status for a file in the list widget."""
        if file_path in self.file_rows:
            row = self.file_rows[file_path]
            file_name = Path(file_path).name
            item = self.list_widget.item(row)
            if item:
                item.setText(f"  {file_name}: {status}")
            self.file_status[file_path] = status

    def _is_valid_book_file(self, file_path: str) -> bool:
        """Check if the file is a valid book format (epub or pdf)."""
        path = Path(file_path)
        return path.exists() and path.is_file() and path.suffix.lower() in ['.epub', '.pdf']

    def on_button_click(self) -> None:
        """Handle button click event."""
        QMessageBox.information(self, "Info", "Button clicked!")

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
