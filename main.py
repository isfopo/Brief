import sys

from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow

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
        """Initialize the main window with title, geometry, and welcome label."""
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)
        label = QLabel(WELCOME_TEXT)
        self.setCentralWidget(label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())