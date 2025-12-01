from PyQt6.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel('Qt test: Hvis du ser dette vinduet, fungerer Qt!')
label.setWindowTitle('Qt Window Test')
label.resize(400, 120)
label.show()
app.exec()
