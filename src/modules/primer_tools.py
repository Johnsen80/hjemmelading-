"""
Primer Selection & Analysis Tools
Complete system for primer selection, comparison, and tracking

Features:
- Primer Selector: Match primer to powder/cartridge
- Comparison Table: Compare different primers
- Seating Depth Guide: Visual guide with measurements
- Substitution Finder: Find alternatives when out of stock
- Pressure Signs Guide: Visual identification
- Lot QC Tracking: Track performance per lot
"""

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..utils.i18n import tr


class PrimerToolsHub(QWidget):
    """
    Main hub for all primer tools
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(tr("primer_tools_hub_title"))
        header.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;"
        )
        layout.addWidget(header)

        # Tool cards
        cards_layout = QHBoxLayout()

        # Card 1: Primer Selector
        card1 = self.create_tool_card(
            "Primer Selector",
            tr("primer_tools_selector_desc"),
            self.open_primer_selector,
        )
        cards_layout.addWidget(card1)

        # Card 2: Comparison Table
        card2 = self.create_tool_card(
            "Comparison Table",
            tr("primer_tools_comparison_desc"),
            self.open_comparison_table,
        )
        cards_layout.addWidget(card2)

        # Card 3: Substitution Finder
        card3 = self.create_tool_card(
            "Substitution Finder",
            tr("primer_tools_substitution_desc"),
            self.open_substitution_finder,
        )
        cards_layout.addWidget(card3)

        layout.addLayout(cards_layout)

        # Second row
        cards_layout2 = QHBoxLayout()

        # Card 4: Seating Depth Guide
        card4 = self.create_tool_card(
            "Seating Depth Guide",
            tr("primer_tools_seating_desc"),
            self.open_seating_guide,
        )
        cards_layout2.addWidget(card4)

        # Card 5: Pressure Signs
        card5 = self.create_tool_card(
            "Pressure Signs Guide",
            tr("primer_tools_pressure_desc"),
            self.open_pressure_guide,
        )
        cards_layout2.addWidget(card5)

        # Card 6: Lot QC Tracking
        card6 = self.create_tool_card(
            "Lot QC Tracking",
            tr("primer_tools_lot_desc"),
            self.open_lot_tracking,
        )
        cards_layout2.addWidget(card6)

        layout.addLayout(cards_layout2)

        layout.addStretch()

    def create_tool_card(self, title: str, description: str, callback) -> QFrame:
        """Create a tool card"""
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 15px;
            }
            QFrame:hover {
                border: 2px solid #3498db;
                background-color: #ecf0f1;
            }
        """
        )

        card_layout = QVBoxLayout()
        card.setLayout(card_layout)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        card_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; margin-top: 5px;")
        card_layout.addWidget(desc_label)

        btn = QPushButton(tr("common_open"))
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        )
        btn.clicked.connect(callback)
        card_layout.addWidget(btn)

        return card

    def open_primer_selector(self):
        """Open primer selector tool"""
        dialog = PrimerSelectorDialog(self)
        dialog.exec()

    def open_comparison_table(self):
        """Open comparison table"""
        dialog = PrimerComparisonDialog(self)
        dialog.exec()

    def open_substitution_finder(self):
        """Open substitution finder"""
        dialog = SubstitutionFinderDialog(self)
        dialog.exec()

    def open_seating_guide(self):
        """Open seating depth guide"""
        dialog = SeatingDepthGuideDialog(self)
        dialog.exec()

    def open_pressure_guide(self):
        """Open pressure signs guide"""
        dialog = PressureSignsDialog(self)
        dialog.exec()

    def open_lot_tracking(self):
        """Open lot tracking"""
        QMessageBox.information(
            self,
            tr("primer_tools_lot_title"),
            tr("primer_tools_lot_coming_soon"),
        )


class PrimerSelectorDialog(QDialog):
    """
    Primer selector - recommend primer based on powder and cartridge
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("primer_tools_selector_title"))
        self.resize(700, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel(f"<h2>{tr('primer_tools_selector_title')}</h2>")
        layout.addWidget(title)

        info = QLabel(tr("primer_tools_selector_info"))
        info.setStyleSheet(
            "background-color: #e8f4f8; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        # Input form
        form = QFormLayout()

        # Cartridge
        self.cartridge = QComboBox()
        self.cartridge.addItems(
            [
                "6.5 Creedmoor",
                ".308 Winchester",
                ".223 Remington",
                "6mm Creedmoor",
                ".260 Remington",
                "6.5x55 Swedish",
                ".30-06 Springfield",
                "Other",
            ]
        )
        form.addRow(tr("primer_tools_cartridge") + ":", self.cartridge)

        # Powder
        self.powder = QComboBox()
        self.powder.setEditable(True)
        self.powder.addItems(
            [
                "Vihtavuori N140",
                "Vihtavuori N150",
                "Hodgdon H4350",
                "Hodgdon Varget",
                "Alliant Reloder 16",
                "IMR 4064",
                "Other",
            ]
        )
        form.addRow(tr("primer_tools_powder") + ":", self.powder)

        # Use case
        self.use_case = QComboBox()
        self.use_case.addItems(
            [
                tr("primer_tools_use_match"),
                tr("primer_tools_use_hunting"),
                tr("primer_tools_use_practice"),
                tr("primer_tools_use_development"),
            ]
        )
        form.addRow(tr("primer_tools_use_case") + ":", self.use_case)

        # Temperature
        self.temperature = QComboBox()
        self.temperature.addItems(
            [
                tr("primer_tools_temp_normal"),
                tr("primer_tools_temp_cold"),
                tr("primer_tools_temp_hot"),
            ]
        )
        form.addRow(tr("primer_tools_temperature") + ":", self.temperature)

        layout.addLayout(form)

        # Find button
        btn_find = QPushButton(tr("primer_tools_find_best"))
        btn_find.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """
        )
        btn_find.clicked.connect(self.find_primers)
        layout.addWidget(btn_find)

        # Results area
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setMinimumHeight(250)
        layout.addWidget(self.results)

        # Close button
        close_btn = QPushButton(tr("btn_close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def find_primers(self):
        """Find recommended primers"""
        cartridge = self.cartridge.currentText()
        powder = self.powder.currentText()
        use_case = self.use_case.currentText()
        temp = self.temperature.currentText()

        # Simple recommendation logic (can be expanded with database)
        results_html = tr(
            "primer_tools_selector_results_html",
            cartridge=cartridge,
            powder=powder,
            use_case=use_case,
            temperature=temp,
        )

        # Add magnum option if cold or slow powder
        if (
            tr("primer_tools_temp_cold") in temp
            or "N150" in powder
            or "N160" in powder
            or "H1000" in powder
        ):
            results_html += tr("primer_tools_selector_magnum_html")

        results_html += tr("primer_tools_selector_footer_html", cartridge=cartridge)

        self.results.setHtml(results_html)


class PrimerComparisonDialog(QDialog):
    """Compare different primers side-by-side"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("primer_tools_comparison_title"))
        self.resize(1000, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel(f"<h2>{tr('primer_tools_comparison_title')}</h2>")
        layout.addWidget(title)

        info = QLabel(tr("primer_tools_comparison_info"))
        info.setStyleSheet(
            "background-color: #e8f4f8; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        # Comparison table
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(
            [
                "Primer",
                tr("primer_tools_size"),
                tr("primer_tools_type"),
                tr("primer_tools_brisance"),
                tr("primer_tools_cup_thickness"),
                tr("primer_tools_sd_impact"),
                tr("primer_tools_best_for"),
                tr("primer_tools_price_per_100"),
            ]
        )

        primers_data = [
            (
                "CCI BR-2",
                "Large Rifle",
                "Benchrest",
                "Medium",
                "Thick",
                "Baseline (8-12 fps)",
                "Match",
                "80 kr",
            ),
            (
                "CCI 450",
                "Small Rifle",
                "Magnum",
                "High",
                "Very Thick",
                "+5-10% vel",
                "AR-15, Magnums",
                "75 kr",
            ),
            (
                "Federal 210M",
                "Large Rifle",
                "Match",
                "Soft",
                "Thin",
                "-5 to -10% SD",
                "Match, Precision",
                "90 kr",
            ),
            (
                "Federal 215M",
                "Large Rifle",
                "Match Magnum",
                "Hot",
                "Thin",
                "+10-15 fps",
                "Magnums, Cold",
                "95 kr",
            ),
            (
                "Federal 205M",
                "Small Rifle",
                "Match",
                "Soft",
                "Thin",
                "-5% SD",
                "AR-15 Match",
                "85 kr",
            ),
            (
                "Remington 7½",
                "Small Rifle",
                "Benchrest",
                "Medium",
                "Medium",
                "Baseline",
                ".223 Match",
                "70 kr",
            ),
            (
                "Remington 9½",
                "Large Rifle",
                "Standard",
                "Medium",
                "Medium",
                "Baseline",
                "General",
                "65 kr",
            ),
            (
                "Remington 9½M",
                "Large Rifle",
                "Magnum",
                "Hot",
                "Thick",
                "+10 fps",
                "Magnums",
                "70 kr",
            ),
            (
                "Winchester WLR",
                "Large Rifle",
                "Standard",
                "Medium",
                "Thin",
                "+10-15% SD",
                "Practice",
                "55 kr",
            ),
            (
                "Winchester WSR",
                "Small Rifle",
                "Standard",
                "Medium",
                "Thin",
                "+10% SD",
                "Practice",
                "50 kr",
            ),
            (
                "RWS 5341",
                "Large Rifle",
                "Match",
                "Medium",
                "Thick",
                "-5% SD",
                "Match (€)",
                "120 kr",
            ),
            (
                "Murom KVB-7",
                "Large Rifle",
                "Standard",
                "Hot",
                "Very Thick",
                "Variable",
                "Surplus",
                "40 kr",
            ),
        ]

        table.setRowCount(len(primers_data))

        for i, primer in enumerate(primers_data):
            for j, value in enumerate(primer):
                item = QTableWidgetItem(value)

                # Color code by quality/type
                if j == 5:  # SD Impact column
                    if "-" in value and "SD" in value:
                        item.setBackground(QColor("#d5f4e6"))  # Green for better SD
                    elif "+" in value and "SD" in value:
                        item.setBackground(QColor("#ffcccc"))  # Red for worse SD

                table.setItem(i, j, item)

        table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Legend
        legend = QLabel(tr("primer_tools_comparison_legend_html"))
        legend.setStyleSheet(
            "background-color: #ecf0f1; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(legend)

        # Close
        close_btn = QPushButton(tr("btn_close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class SubstitutionFinderDialog(QDialog):
    """Find primer substitutes when out of stock"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("primer_tools_substitution_title"))
        self.resize(700, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel(f"<h2>{tr('primer_tools_substitution_title')}</h2>")
        layout.addWidget(title)

        info = QLabel(tr("primer_tools_substitution_info"))
        info.setStyleSheet(
            "background-color: #fff9c4; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        # Input
        form = QFormLayout()

        self.original_primer = QComboBox()
        self.original_primer.addItems(
            [
                "CCI BR-2",
                "CCI 450",
                "Federal 210M",
                "Federal 215M",
                "Federal 205M",
                "Remington 7½",
                "Remington 9½",
                "Winchester WLR",
            ]
        )
        form.addRow(tr("primer_tools_out_of_stock") + ":", self.original_primer)

        layout.addLayout(form)

        # Find button
        btn_find = QPushButton(tr("primer_tools_find_substitutes"))
        btn_find.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
            }
        """
        )
        btn_find.clicked.connect(self.find_substitutes)
        layout.addWidget(btn_find)

        # Results
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        layout.addWidget(self.results)

        # Close
        close_btn = QPushButton(tr("btn_close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def find_substitutes(self):
        """Find substitute primers"""
        primer = self.original_primer.currentText()

        substitutions = {
            "CCI BR-2": [
                (
                    "Federal 210M",
                    "95%",
                    "May IMPROVE SD by 5-10%. Softer cup - seat carefully.",
                    "No load adjustment needed",
                ),
                (
                    "Remington 9½",
                    "90%",
                    "Similar performance. Slightly less consistent.",
                    "Test in your rifle first",
                ),
                (
                    "Winchester WLR",
                    "80%",
                    "Budget option. Expect +10-15% SD increase.",
                    "Not match-grade",
                ),
            ],
            "Federal 210M": [
                (
                    "CCI BR-2",
                    "95%",
                    "Thicker cup, may increase SD slightly but more consistent.",
                    "Direct substitute",
                ),
                ("Remington 9½", "85%", "Less precise, but works.", "Re-test load"),
                (
                    "RWS 5341",
                    "98%",
                    "European match primer. Excellent if available.",
                    "Premium option",
                ),
            ],
            "CCI 450": [
                (
                    "Federal 205M",
                    "90%",
                    "Match-grade, softer cup. May improve SD.",
                    "Test for slam-fire in AR-15",
                ),
                (
                    "Remington 7½",
                    "85%",
                    "Benchrest primer, thinner cup.",
                    "Careful in semi-auto",
                ),
                (
                    "CCI 400",
                    "80%",
                    "Standard version. More variance.",
                    "Not match-grade",
                ),
            ],
        }

        if primer not in substitutions:
            self.results.setHtml(tr("primer_tools_no_substitution_data"))
            return

        results_html = f"<h3>{tr('primer_tools_substitutes_for', primer=primer)}</h3>"

        for i, (sub, compatibility, notes, adjustment) in enumerate(
            substitutions[primer], 1
        ):
            color = "#d5f4e6" if i == 1 else "#fff9c4" if i == 2 else "#ffe0b2"
            results_html += f"""
            <div style='background-color: {color}; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
            <h4>#{i}: {sub} ({compatibility} compatible)</h4>
            <p><b>{tr('common_notes')}:</b> {notes}</p>
            <p><b>{tr('primer_tools_load_adjustment')}:</b> {adjustment}</p>
            </div>
            """

        results_html += tr("primer_tools_substitution_footer_html")

        self.results.setHtml(results_html)


class SeatingDepthGuideDialog(QDialog):
    """Visual guide for correct primer seating depth"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("primer_tools_seating_title"))
        self.resize(800, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel(f"<h2>{tr('primer_tools_seating_title')}</h2>")
        layout.addWidget(title)

        # Visual guide with ASCII art
        guide_html = tr("primer_tools_seating_guide_html")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel(guide_html)
        content.setWordWrap(True)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Close
        close_btn = QPushButton(tr("btn_close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class PressureSignsDialog(QDialog):
    """Visual guide for identifying pressure signs on primers"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("primer_tools_pressure_title"))
        self.resize(800, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel(f"<h2>{tr('primer_tools_pressure_title')}</h2>")
        layout.addWidget(title)

        info = QLabel(tr("primer_tools_pressure_info_html"))
        info.setStyleSheet(
            "background-color: #ffe0b2; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        # Pressure signs guide
        guide_html = tr("primer_tools_pressure_guide_html")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel(guide_html)
        content.setWordWrap(True)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Close
        close_btn = QPushButton(tr("btn_close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    hub = PrimerToolsHub()
    hub.show()
    hub.resize(1000, 600)

    sys.exit(app.exec())
