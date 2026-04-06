

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt
import eclipsum_utils
import INFO

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("test")
        self.setGeometry(160, 90, 160, 90)

        label = QLabel(text=f"{INFO.VERSION}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
