"""Entry point del simulatore UI."""
import sys
from PySide6.QtWidgets import QApplication
from .ui.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()