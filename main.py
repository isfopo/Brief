import sys
import logging
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QListWidget, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget, QTabWidget, QScrollArea, QLabel, QFrame, QHBoxLayout, QLineEdit, QComboBox
from PyQt6.QtCore import QThread, pyqtSignal

from ui.drop_zone import DropZone
from ui.summary_panel import SummaryPanel
from services.parser import parse_epub, parse_pdf, BookMetadata
from services import summarizer, storage

# Configure logging
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"log_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)

# Preload the summarization model in background
import threading
def preload_summarizer():
    """Preload summarizer in background thread."""
    try:
        logging.info("Starting to preload summarization model...")
        summarizer.preload_model()
        logging.info("Summarization model preloaded successfully.")
    except Exception as e:
        logging.warning(f"Failed to preload summarizer: {e}")

preload_thread = threading.Thread(target=preload_summarizer, daemon=True)
preload_thread.start()


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
            logging.info(f"Starting summarization for {Path(self.file_path).name}")
            self.progress.emit(self.file_path, "Starting summarization...")

            # Summarize the text
            summary = summarizer.summarize_book(self.text)
            if not summary:
                raise ValueError("Summarization failed: empty summary")

            logging.info(f"Summarization complete for {Path(self.file_path).name}")
            self.progress.emit(self.file_path, "Summarization complete, saving...")

            # Save the summary
            metadata_dict = {
                'title': self.metadata.title,
                'author': self.metadata.author,
                'path': self.metadata.path,
                'timestamp': self.metadata.timestamp
            }
            storage.save_summary(metadata_dict, summary)

            logging.info(f"Summary saved for {self.metadata.title}")
            self.finished.emit(self.file_path, f"Summarized and saved: {self.metadata.title}")

        except Exception as e:
            logging.error(f"Error processing {Path(self.file_path).name}: {str(e)}")
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
        """Initialize the main window with title, geometry, and tabbed interface."""
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Keep track of workers
        self.workers = []
        # Track status per file
        self.file_status = {}
        # Track list item row per file
        self.file_rows = {}

        # Create central widget with tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create processing tab
        self._create_processing_tab()

        # Create summaries tab
        self._create_summaries_tab()

    def _create_processing_tab(self):
        """Create the file processing tab."""
        processing_widget = QWidget()
        layout = QVBoxLayout(processing_widget)

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

        self.tab_widget.addTab(processing_widget, "Process Files")

    def _create_summaries_tab(self):
        """Create the summaries viewing tab."""
        summaries_widget = QWidget()
        layout = QVBoxLayout(summaries_widget)

        # Create scroll area for summaries
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Create container for summary panels
        self.summaries_container = QWidget()
        self.summaries_layout = QVBoxLayout(self.summaries_container)
        scroll_area.setWidget(self.summaries_container)

        # Add search and control buttons
        controls_layout = QVBoxLayout()

        # Search and sort controls
        search_sort_layout = QHBoxLayout()

        # Search
        search_label = QLabel("Search:")
        search_sort_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, author, or content...")
        self.search_input.textChanged.connect(self.filter_summaries)
        search_sort_layout.addWidget(self.search_input)

        # Sort
        sort_label = QLabel("Sort by:")
        search_sort_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Date (newest first)", "Date (oldest first)", "Title (A-Z)", "Title (Z-A)", "Author (A-Z)", "Author (Z-A)"])
        self.sort_combo.currentTextChanged.connect(self.sort_summaries)
        search_sort_layout.addWidget(self.sort_combo)

        controls_layout.addLayout(search_sort_layout)

        # Control buttons
        buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Summaries")
        self.refresh_button.clicked.connect(self.refresh_summaries)
        buttons_layout.addWidget(self.refresh_button)

        self.load_more_button = QPushButton("Load More")
        self.load_more_button.clicked.connect(self.load_more_summaries)
        self.load_more_button.setVisible(False)
        buttons_layout.addWidget(self.load_more_button)

        buttons_layout.addStretch()
        controls_layout.addLayout(buttons_layout)

        layout.addLayout(controls_layout)

        self.tab_widget.addTab(summaries_widget, "View Summaries")

        # Initialize pagination
        self.current_page = 0
        self.page_size = 10
        self.all_summaries = []

        # Load summaries initially
        self.refresh_summaries()

    def load_more_summaries(self):
        """Load the next page of summaries."""
        self.current_page += 1
        self._display_summaries_page()

    def filter_summaries(self):
        """Filter summaries based on search text."""
        search_text = self.search_input.text().lower()
        if not search_text:
            # Show all summaries
            self.refresh_summaries()
            return

        # Clear current display
        while self.summaries_layout.count() > 0:
            item = self.summaries_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()

        # Filter and display matching summaries
        filtered_summaries = []
        for summary in self.all_summaries:
            if (search_text in summary.title.lower() or
                search_text in summary.author.lower() or
                search_text in summary.summary.lower()):
                filtered_summaries.append(summary)

        if not filtered_summaries:
            no_results_label = QLabel(f"No summaries found matching '{self.search_input.text()}'")
            no_results_label.setStyleSheet("color: gray; font-style: italic;")
            self.summaries_layout.addWidget(no_results_label)
            self.load_more_button.setVisible(False)
            return

        # Display filtered results (no pagination for filtered results)
        for summary_data in filtered_summaries:
            panel = SummaryPanel(summary_data)
            self.summaries_layout.addWidget(panel)
        self.load_more_button.setVisible(False)

    def sort_summaries(self):
        """Sort summaries based on selected criteria."""
        if not self.all_summaries:
            return

        sort_option = self.sort_combo.currentText()

        if sort_option == "Date (newest first)":
            self.all_summaries.sort(key=lambda s: s.timestamp, reverse=True)
        elif sort_option == "Date (oldest first)":
            self.all_summaries.sort(key=lambda s: s.timestamp)
        elif sort_option == "Title (A-Z)":
            self.all_summaries.sort(key=lambda s: s.title.lower())
        elif sort_option == "Title (Z-A)":
            self.all_summaries.sort(key=lambda s: s.title.lower(), reverse=True)
        elif sort_option == "Author (A-Z)":
            self.all_summaries.sort(key=lambda s: s.author.lower())
        elif sort_option == "Author (Z-A)":
            self.all_summaries.sort(key=lambda s: s.author.lower(), reverse=True)

        # Re-display with new sorting
        self.current_page = 0
        while self.summaries_layout.count() > 0:
            item = self.summaries_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()
        self._display_summaries_page()

    def refresh_summaries(self):
        """Refresh the summaries display by reloading from storage."""
        # Reset pagination
        self.current_page = 0
        self.all_summaries = []

        # Clear existing summaries
        while self.summaries_layout.count() > 0:
            item = self.summaries_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()

        # Load all summaries from storage
        try:
            from services.storage import list_summaries

            self.all_summaries = list_summaries()
            if not self.all_summaries:
                no_summaries_label = QLabel("No summaries found. Process some books first!")
                no_summaries_label.setStyleSheet("color: gray; font-style: italic;")
                self.summaries_layout.addWidget(no_summaries_label)
                self.load_more_button.setVisible(False)
                return

            # Display first page
            self._display_summaries_page()

        except Exception as e:
            error_label = QLabel(f"Error loading summaries: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.summaries_layout.addWidget(error_label)
            self.load_more_button.setVisible(False)

    def _display_summaries_page(self):
        """Display the current page of summaries."""
        if not self.all_summaries:
            return

        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.all_summaries))

        for i in range(start_idx, end_idx):
            summary_data = self.all_summaries[i]
            panel = SummaryPanel(summary_data)
            self.summaries_layout.addWidget(panel)

        # Show/hide load more button
        has_more = end_idx < len(self.all_summaries)
        self.load_more_button.setVisible(has_more)

    def process_files(self, file_paths: list[str]) -> None:
        """Process dropped files."""
        logging.info(f"Processing {len(file_paths)} dropped files")
        valid_files = [path for path in file_paths if self._is_valid_book_file(path)]
        invalid_files = [path for path in file_paths if not self._is_valid_book_file(path)]

        self.list_widget.clear()
        self.file_status.clear()
        self.file_rows.clear()
        if valid_files:
            logging.info(f"Found {len(valid_files)} valid book files")
            self.list_widget.addItem("Processing files:")
            for file in valid_files:
                row = self.list_widget.count()
                self.list_widget.addItem(f"  {Path(file).name}: Processing...")
                self.file_rows[file] = row
                self.file_status[file] = "Processing"

                # Parse book files
                try:
                    logging.info(f"Parsing {Path(file).name}")
                    if Path(file).suffix.lower() == '.epub':
                        text, metadata = parse_epub(file)
                    elif Path(file).suffix.lower() == '.pdf':
                        text, metadata = parse_pdf(file)
                    else:
                        continue

                    logging.info(f"Parsed {Path(file).name}: {len(text)} characters, Title: {metadata.title}")
                    self._update_file_status(file, f"Parsed {len(text)} characters - Title: {metadata.title}, Author: {metadata.author}")

                    # Start summarization worker
                    worker = SummarizationWorker(file, text, metadata)
                    worker.finished.connect(self.on_summarization_finished)
                    worker.error.connect(self.on_summarization_error)
                    worker.progress.connect(self.on_summarization_progress)
                    self.workers.append(worker)  # Keep reference
                    worker.start()

                except ValueError as e:
                    logging.error(f"Error parsing {Path(file).name}: {e}")
                    self._update_file_status(file, f"Error: {e}")
        else:
            logging.info("No valid book files found")
            self.list_widget.addItem("No valid book files found")

        if invalid_files:
            invalid_names = [Path(f).name for f in invalid_files]
            logging.warning(f"Unsupported files: {', '.join(invalid_names)}")
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
