import sys
from PyQt6.QtWidgets import QApplication, QLabel

app = QApplication(sys.argv)
label = QLabel('PyQt6 testvindu - hvis du ser denne, funker Qt!')
label.setGeometry(100, 100, 400, 100)
label.show()
sys.exit(app.exec())
