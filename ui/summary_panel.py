"""Summary panel component for displaying book summaries."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextEdit
from PyQt6.QtCore import Qt
from services.storage import SummaryData


class SummaryPanel(QFrame):
    """A panel component for displaying individual book summaries."""

    def __init__(self, summary_data: SummaryData, parent=None):
        """Initialize the summary panel.

        Args:
            summary_data: The summary data to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.summary_data = summary_data
        self.expanded = False
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            SummaryPanel {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
                background-color: #ffffff;
            }
            SummaryPanel:hover {
                border-color: #999;
                background-color: #f8f8f8;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header with title and metadata
        header_layout = QHBoxLayout()

        title_label = QLabel(f"<b>{self.summary_data.title}</b>")
        title_label.setStyleSheet("font-size: 16px; color: #2c3e50;")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, stretch=1)

        # Expand/collapse button
        self.expand_button = QPushButton("▼")
        self.expand_button.setFixedSize(30, 30)
        self.expand_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 14px;
                color: #666;
            }
            QPushButton:hover {
                color: #333;
            }
        """)
        self.expand_button.clicked.connect(self._toggle_expanded)
        header_layout.addWidget(self.expand_button, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addLayout(header_layout)

        # Author and date
        author_date = f"<i>{self.summary_data.author}</i> • {self.summary_data.timestamp}"
        metadata_label = QLabel(author_date)
        metadata_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(metadata_label)

        # Summary text area
        self.summary_text = QTextEdit()
        self.summary_text.setPlainText(self.summary_data.summary)
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                line-height: 1.5;
                color: #34495e;
            }
        """)

        # Initially show truncated text
        self._update_text_display()
        layout.addWidget(self.summary_text)

        # Action buttons
        buttons_layout = QHBoxLayout()

        # View full button (if truncated)
        self.view_full_button = QPushButton("View Full Summary")
        self.view_full_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #3498db;
                background: transparent;
                color: #3498db;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #3498db;
                color: white;
            }
        """)
        self.view_full_button.clicked.connect(self._toggle_expanded)
        buttons_layout.addWidget(self.view_full_button)
        buttons_layout.addStretch()

        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #e74c3c;
                background: transparent;
                color: #e74c3c;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #e74c3c;
                color: white;
            }
        """)
        delete_button.clicked.connect(self._delete_summary)
        buttons_layout.addWidget(delete_button)

        layout.addLayout(buttons_layout)

    def _update_text_display(self):
        """Update the text display based on expanded state."""
        if self.expanded:
            self.summary_text.setPlainText(self.summary_data.summary)
            self.expand_button.setText("▲")
            self.view_full_button.setVisible(False)
        else:
            # Show truncated text
            full_text = self.summary_data.summary
            if len(full_text) > 300:
                truncated = full_text[:300] + "..."
                self.summary_text.setPlainText(truncated)
                self.view_full_button.setVisible(True)
            else:
                self.summary_text.setPlainText(full_text)
                self.view_full_button.setVisible(False)
            self.expand_button.setText("▼")

    def _toggle_expanded(self):
        """Toggle between expanded and collapsed view."""
        self.expanded = not self.expanded
        self._update_text_display()

    def _delete_summary(self):
        """Delete this summary from storage."""
        # TODO: Implement deletion
        pass