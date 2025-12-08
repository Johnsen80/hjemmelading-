"""
Primer (Tennhette) Selection Guide
Help users choose the right primer for their load
"""

import json

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class PrimerSelectionGuide(QWidget):
    """
    Interactive guide for selecting primers
    Explains differences and recommends based on load
    """

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_primers()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel("💥 Primer Selection Guide (Tennhetter)")
        header.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;"
        )
        layout.addWidget(header)

        # Info box
        info_html = """
        <div style='background-color: #e8f4f8; padding: 15px; border-radius: 5px;'>
        <h3>🎯 Primer Basics:</h3>
        <ul>
            <li><b>Small Rifle:</b> .223, 6mm BR, .22-250</li>
            <li><b>Large Rifle:</b> .308, 6.5 CM, .30-06, magnums</li>
            <li><b>Standard:</b> General purpose, works with most powders</li>
            <li><b>Magnum:</b> For slow powders, cold weather, big cases</li>
            <li><b>Match/Benchrest:</b> Most consistent, for precision shooting</li>
        </ul>
        </div>
        """

        info_label = QLabel(info_html)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Filter/recommendation section
        rec_group = QGroupBox("🔍 Find Right Primer")
        rec_layout = QFormLayout()

        self.cartridge_combo = QComboBox()
        self.cartridge_combo.addItems(
            [
                "Select cartridge...",
                ".223 Remington",
                "6mm BR",
                "6.5 Creedmoor",
                ".308 Winchester",
                ".30-06 Springfield",
                "6.5x55 Swedish",
                ".300 Win Mag",
            ]
        )
        self.cartridge_combo.currentTextChanged.connect(self.recommend_primer)
        rec_layout.addRow("Cartridge:", self.cartridge_combo)

        self.powder_type = QComboBox()
        self.powder_type.addItems(
            [
                "Select powder type...",
                "Fast (Varget, N140, RL15)",
                "Medium (H4350, N150, RL16)",
                "Slow (H1000, N160, RL22)",
                "Ball powder (H335, BLC-2)",
            ]
        )
        self.powder_type.currentTextChanged.connect(self.recommend_primer)
        rec_layout.addRow("Powder Type:", self.powder_type)

        self.use_case = QComboBox()
        self.use_case.addItems(
            [
                "Select use...",
                "Match/Competition (best consistency)",
                "Hunting (reliable ignition)",
                "Practice/Plinking (economical)",
                "Cold weather (-20°C or colder)",
            ]
        )
        self.use_case.currentTextChanged.connect(self.recommend_primer)
        rec_layout.addRow("Use Case:", self.use_case)

        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

        # Recommendation display
        self.recommendation = QTextEdit()
        self.recommendation.setReadOnly(True)
        self.recommendation.setMaximumHeight(150)
        self.recommendation.setHtml(
            "<i>Select options above to get primer recommendation...</i>"
        )
        layout.addWidget(self.recommendation)

        # Full primer table
        table_label = QLabel("<b>📋 All Available Primers:</b>")
        layout.addWidget(table_label)

        self.primers_table = QTableWidget()
        self.primers_table.setColumnCount(6)
        self.primers_table.setHorizontalHeaderLabels(
            ["Manufacturer", "Name", "Size", "Type", "Brisance", "Notes"]
        )
        self.primers_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.primers_table)

        # Primer comparison button
        self.btn_compare = QPushButton("⚖️ Compare Primers")
        self.btn_compare.clicked.connect(self.compare_primers)
        layout.addWidget(self.btn_compare)

    def load_primers(self):
        """Load primers from database"""
        import os

        db_path = "data/components_database.json"

        if not os.path.exists(db_path):
            return

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)

            primers = db.get("primers", [])

            self.primers_table.setRowCount(0)

            for primer in primers:
                row = self.primers_table.rowCount()
                self.primers_table.insertRow(row)

                self.primers_table.setItem(
                    row, 0, QTableWidgetItem(primer["manufacturer"])
                )
                self.primers_table.setItem(row, 1, QTableWidgetItem(primer["name"]))

                size_item = QTableWidgetItem(primer["size"])
                if "Small" in primer["size"]:
                    size_item.setBackground(QColor("#e8f4f8"))
                else:
                    size_item.setBackground(QColor("#fff9c4"))
                self.primers_table.setItem(row, 2, size_item)

                type_item = QTableWidgetItem(primer["type"])
                if "Match" in primer["type"] or "Benchrest" in primer["type"]:
                    type_item.setBackground(QColor("#d5f4e6"))
                self.primers_table.setItem(row, 3, type_item)

                self.primers_table.setItem(row, 4, QTableWidgetItem(primer["brisance"]))
                self.primers_table.setItem(row, 5, QTableWidgetItem(primer["notes"]))

            self.primers_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error loading primers: {e}")

    def recommend_primer(self):
        """Recommend primer based on selections"""
        cartridge = self.cartridge_combo.currentText()
        powder = self.powder_type.currentText()
        use = self.use_case.currentText()

        if "Select" in cartridge or "Select" in powder or "Select" in use:
            return

        # Determine primer size
        small_rifle_cartridges = [".223 Remington", "6mm BR"]

        if cartridge in small_rifle_cartridges:
            size = "Small Rifle"
        else:
            size = "Large Rifle"

        # Determine recommendations
        recommendations = []

        if "Match" in use:
            if size == "Small Rifle":
                recommendations = [
                    ("CCI 450", "Best for match, magnum cup handles ball powders well"),
                    ("Federal 205M", "Gold standard for .223 match"),
                    ("Remington 7½", "Classic benchrest choice"),
                    ("Murom KVB-223", "Russian match quality, very consistent"),
                ]
            else:
                recommendations = [
                    ("CCI BR-2", "Most popular match primer worldwide"),
                    ("Federal 210M", "Gold Medal Match standard"),
                    ("Murom KVB-7.62", "Excellent consistency"),
                    ("RWS 5341", "German precision"),
                ]

        elif "Cold weather" in use:
            if size == "Small Rifle":
                recommendations = [
                    ("CCI 450", "Magnum primer, best for cold weather"),
                    ("Federal 205M", "Reliable in cold"),
                ]
            else:
                recommendations = [
                    ("Federal 215M", "Match Magnum - perfect for cold"),
                    ("Remington 9½", "Magnum for reliable ignition"),
                    ("CCI 250", "Magnum Large Rifle (if available)"),
                ]

        elif "Practice" in use:
            if size == "Small Rifle":
                recommendations = [
                    ("CCI 400", "Standard, economical"),
                    ("Winchester WSR", "General purpose"),
                    ("Norma Small Rifle", "Good value"),
                ]
            else:
                recommendations = [
                    ("Winchester WLR", "Most economical"),
                    ("Federal 210", "Standard Large Rifle"),
                    ("Norma Large Rifle", "Consistent and affordable"),
                ]

        else:  # Hunting
            if size == "Small Rifle":
                recommendations = [
                    ("CCI 450", "Magnum ensures ignition"),
                    ("Federal 205", "Reliable"),
                ]
            else:
                recommendations = [
                    ("Federal 215M", "For slow powders in magnums"),
                    ("CCI BR-2", "Excellent all-rounder"),
                    ("Remington 9½", "Magnum for big cases"),
                ]

        # Format recommendation
        html = f"""
        <div style='background-color: #d5f4e6; padding: 15px; border-radius: 5px;'>
        <h3>🎯 Recommended Primers for Your Load:</h3>
        <p><b>Cartridge:</b> {cartridge}<br>
        <b>Powder Type:</b> {powder}<br>
        <b>Use Case:</b> {use}<br>
        <b>Primer Size Needed:</b> {size}</p>

        <h4>Top Recommendations:</h4>
        <ol>
        """

        for name, reason in recommendations[:3]:
            html += f"<li><b>{name}</b> - {reason}</li>"

        html += """
        </ol>
        </div>
        """

        # Add powder-specific advice
        if "Ball powder" in powder:
            html += """
            <div style='background-color: #fff9c4; padding: 10px; border-radius: 5px; margin-top: 10px;'>
            <b>💡 Ball Powder Tip:</b> Ball powders often need magnum primers for consistent ignition.
            CCI 450 (small) or CCI 250/Federal 215M (large) work best.
            </div>
            """

        if "Slow" in powder:
            html += """
            <div style='background-color: #fff9c4; padding: 10px; border-radius: 5px; margin-top: 10px;'>
            <b>💡 Slow Powder Tip:</b> Slow powders need more heat to ignite properly.
            Consider magnum primers, especially in cold weather.
            </div>
            """

        self.recommendation.setHtml(html)

    def compare_primers(self):
        """Show primer comparison dialog"""
        dialog = PrimerComparisonDialog(self)
        dialog.exec()


class PrimerComparisonDialog(QDialog):
    """Compare different primer characteristics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Primer Comparison")
        self.resize(900, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("<h2>⚖️ Primer Characteristics Comparison</h2>")
        layout.addWidget(title)

        comparison_html = """
        <h3>🔥 Brisance (Flame Intensity):</h3>
        <table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Level</th>
                <th>Primers</th>
                <th>Best For</th>
            </tr>
            <tr>
                <td><b>Low-Medium</b></td>
                <td>CCI BR-2, Federal 210M, Remington 7½</td>
                <td>Match shooting, low-temp powders like Vihtavuori</td>
            </tr>
            <tr>
                <td><b>Medium</b></td>
                <td>CCI 400/200, Winchester, Norma, RWS</td>
                <td>General purpose, most powders</td>
            </tr>
            <tr>
                <td><b>High</b></td>
                <td>CCI 450/250, Federal 215M, Remington 9½</td>
                <td>Ball powders, slow powders, cold weather, magnums</td>
            </tr>
        </table>

        <h3 style='margin-top: 20px;'>📊 Consistency (SD in fps):</h3>
        <table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Rating</th>
                <th>Primers</th>
                <th>Expected Velocity SD</th>
            </tr>
            <tr style='background-color: #d5f4e6;'>
                <td><b>★★★★★ Best</b></td>
                <td>CCI BR-2, Federal 210M/215M, Murom KVB</td>
                <td>3-6 fps SD (excellent)</td>
            </tr>
            <tr style='background-color: #fff9c4;'>
                <td><b>★★★★☆ Very Good</b></td>
                <td>CCI 450/400, RWS, Remington 7½</td>
                <td>6-10 fps SD (very good)</td>
            </tr>
            <tr>
                <td><b>★★★☆☆ Good</b></td>
                <td>Winchester, Federal standard, Norma</td>
                <td>8-15 fps SD (good for practice)</td>
            </tr>
        </table>

        <h3 style='margin-top: 20px;'>🌡️ Temperature Sensitivity:</h3>
        <table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Primer</th>
                <th>Temp Sensitivity</th>
                <th>Notes</th>
            </tr>
            <tr>
                <td>Federal 210M/215M</td>
                <td>Low</td>
                <td>Very stable across temp range</td>
            </tr>
            <tr>
                <td>CCI BR-2</td>
                <td>Low-Medium</td>
                <td>Good stability</td>
            </tr>
            <tr>
                <td>CCI 450 (Magnum)</td>
                <td>Medium</td>
                <td>Hot in summer, but works in cold</td>
            </tr>
            <tr>
                <td>Russian (Murom)</td>
                <td>Low</td>
                <td>Excellent temp stability</td>
            </tr>
        </table>

        <div style='background-color: #fff9c4; padding: 15px; border-radius: 5px; margin-top: 20px;'>
        <b>💡 Pro Tips:</b>
        <ul>
            <li><b>Consistency matters more than brisance</b> for match shooting</li>
            <li><b>Test multiple primers</b> - your rifle may prefer one over another</li>
            <li><b>Magnum primers ≠ always better</b> - can cause pressure spikes</li>
            <li><b>Stick with one lot</b> - switch primer = re-work load</li>
            <li><b>Cup hardness:</b> Match primers = soft, Military = hard (for semi-autos)</li>
        </ul>
        </div>
        """

        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(comparison_html)
        layout.addWidget(text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    guide = PrimerSelectionGuide()
    guide.show()
    guide.resize(1000, 800)

    sys.exit(app.exec())
