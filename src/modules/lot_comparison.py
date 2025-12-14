from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.utils.optional_deps import FigureCanvas as FigureCanvas
from src.utils.optional_deps import plt


class LotComparisonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Sammenlign Lot/batcher"))
        self.lot_select_1 = QComboBox()
        self.lot_select_2 = QComboBox()
        layout.addWidget(QLabel("Velg Lot 1:"))
        layout.addWidget(self.lot_select_1)
        layout.addWidget(QLabel("Velg Lot 2:"))
        layout.addWidget(self.lot_select_2)
        self.compare_btn = QPushButton("Sammenlign")
        self.compare_btn.clicked.connect(self.compare_lots)
        layout.addWidget(self.compare_btn)
        self.result_label = QLabel()
        layout.addWidget(self.result_label)
        self.graph_canvas = None

        # Image upload and display
        self.image_label_1 = QLabel()
        self.image_label_2 = QLabel()
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("Bilde Lot 1:"))
        img_layout.addWidget(self.image_label_1)
        img_layout.addWidget(QLabel("Bilde Lot 2:"))
        img_layout.addWidget(self.image_label_2)
        self.upload_img_btn_1 = QPushButton("Last opp bilde Lot 1")
        self.upload_img_btn_1.clicked.connect(self.upload_image_1)
        self.upload_img_btn_2 = QPushButton("Last opp bilde Lot 2")
        self.upload_img_btn_2.clicked.connect(self.upload_image_2)
        layout.addLayout(img_layout)
        layout.addWidget(self.upload_img_btn_1)
        layout.addWidget(self.upload_img_btn_2)

        # Documentation and notes
        layout.addWidget(QLabel("Dokumentasjon:"))
        self.doc_text = QTextEdit()
        self.doc_text.setPlaceholderText("Notater og dokumentasjon...")
        layout.addWidget(self.doc_text)

        # Image analysis button and result placeholder
        self.analyze_img_btn = QPushButton("Analyser bilder")
        self.analyze_img_btn.clicked.connect(self.analyze_images)
        layout.addWidget(self.analyze_img_btn)
        self.analysis_result_label = QLabel()
        layout.addWidget(self.analysis_result_label)

        # Save to log and report generation buttons
        self.save_log_btn = QPushButton("Lagre til testlogg")
        self.save_log_btn.clicked.connect(self.save_to_log)
        layout.addWidget(self.save_log_btn)
        self.export_report_btn = QPushButton("Generer rapport")
        self.export_report_btn.clicked.connect(self.export_report)
        layout.addWidget(self.export_report_btn)

    def compare_lots(self):
        # Dummy data for eksempel
        lot1 = self.lot_select_1.currentText()
        lot2 = self.lot_select_2.currentText()
        x = [100, 200, 300, 400, 500]
        y1 = [30, 25, 20, 18, 15]  # Lot 1 treffgruppe
        y2 = [32, 27, 22, 19, 16]  # Lot 2 treffgruppe
        fig, ax = plt.subplots()
        ax.plot(x, y1, label=f"{lot1} treffgruppe", marker="o")
        ax.plot(x, y2, label=f"{lot2} treffgruppe", marker="x")
        ax.set_xlabel("Avstand (m)")
        ax.set_title("Sammenligning av Lot")
        ax.legend()
        if self.graph_canvas:
            self.layout().removeWidget(self.graph_canvas)
            self.graph_canvas.deleteLater()
        self.graph_canvas = FigureCanvas(fig)
        self.layout().addWidget(self.graph_canvas)
        fig.tight_layout()
        # Statistikk
        avg1 = sum(y1) / len(y1)
        avg2 = sum(y2) / len(y2)
        self.result_label.setText(
            f"Snitt treffgruppe Lot 1: {avg1:.1f} mm\nSnitt treffgruppe Lot 2: {avg2:.1f} mm"
        )

    def upload_image_1(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Velg bilde Lot 1", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            self.image_label_1.setPixmap(pixmap.scaled(200, 200))

    def upload_image_2(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Velg bilde Lot 2", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            self.image_label_2.setPixmap(pixmap.scaled(200, 200))

    def analyze_images(self):
        # Placeholder for bildeanalyse/AI
        self.analysis_result_label.setText(
            "Bildeanalyse: (kommer, AI/algoritme kan måle gruppe, avstand, treffpunkt osv)"
        )
        # Her kan du integrere OpenCV, PIL eller AI-modul senere

    def save_to_log(self):
        # Placeholder: lagre sammenligning, bilder og notater til testlogg/database
        QMessageBox.information(self, "Testlogg", "Sammenligning lagret i testloggen.")

    def export_report(self):
        # Placeholder: generer rapport med alle data, bilder og analyser
        QMessageBox.information(
            self, "Rapport", "Rapport generert og klar til eksport."
        )
