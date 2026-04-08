

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt
import eclipsum_utils
import qasync
import INFO

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("test")
        self.setGeometry(160, 90, 250, 115)

        label = QLabel(text=f"{INFO.VERSION}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)

def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    window = Window()
    window.show()
    
    try:
        loop.run_forever()
    except:
        pass


if __name__ == "__main__":
    main()
