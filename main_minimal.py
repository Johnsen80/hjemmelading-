import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

class MinimalMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HJEMMELADING - Minimal Test")
        self.setGeometry(100, 100, 800, 400)
        label = QLabel("Minimal test: Hvis du ser dette, er det en ekstern ressurs/modul som feiler i fullversjonen.", self)
        label.setGeometry(50, 150, 700, 50)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimalMainWindow()
    window.show()
    sys.exit(app.exec())
