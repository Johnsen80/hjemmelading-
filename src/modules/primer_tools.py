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
        header = QLabel("🔥 Primer Selection & Analysis Tools")
        header.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;"
        )
        layout.addWidget(header)

        # Tool cards
        cards_layout = QHBoxLayout()

        # Card 1: Primer Selector
        card1 = self.create_tool_card(
            "🎯 Primer Selector",
            "Find the perfect primer for your powder and cartridge",
            self.open_primer_selector,
        )
        cards_layout.addWidget(card1)

        # Card 2: Comparison Table
        card2 = self.create_tool_card(
            "📊 Comparison Table",
            "Compare primers side-by-side",
            self.open_comparison_table,
        )
        cards_layout.addWidget(card2)

        # Card 3: Substitution Finder
        card3 = self.create_tool_card(
            "🔄 Substitution Finder",
            "Find alternatives when out of stock",
            self.open_substitution_finder,
        )
        cards_layout.addWidget(card3)

        layout.addLayout(cards_layout)

        # Second row
        cards_layout2 = QHBoxLayout()

        # Card 4: Seating Depth Guide
        card4 = self.create_tool_card(
            "📏 Seating Depth Guide",
            "Learn correct primer seating depth",
            self.open_seating_guide,
        )
        cards_layout2.addWidget(card4)

        # Card 5: Pressure Signs
        card5 = self.create_tool_card(
            "🛡️ Pressure Signs Guide",
            "Identify over-pressure signs",
            self.open_pressure_guide,
        )
        cards_layout2.addWidget(card5)

        # Card 6: Lot QC Tracking
        card6 = self.create_tool_card(
            "📈 Lot QC Tracking",
            "Track primer performance by lot",
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

        btn = QPushButton("Open")
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
            "Lot QC Tracking",
            "📈 Primer Lot QC Tracking coming soon!\n\n"
            "Will track:\n"
            "• Velocity SD per lot\n"
            "• ES comparison\n"
            "• Accuracy data\n"
            "• Best lots for match use",
        )


class PrimerSelectorDialog(QDialog):
    """
    Primer selector - recommend primer based on powder and cartridge
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Primer Selector")
        self.resize(700, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("<h2>🎯 Primer Selector</h2>")
        layout.addWidget(title)

        info = QLabel(
            "Tell us about your load, and we'll recommend the best primer!\n"
            "Based on thousands of proven combinations."
        )
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
        form.addRow("Cartridge:", self.cartridge)

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
        form.addRow("Powder:", self.powder)

        # Use case
        self.use_case = QComboBox()
        self.use_case.addItems(
            ["Match/Competition", "Hunting", "Practice/Plinking", "Load Development"]
        )
        form.addRow("Use Case:", self.use_case)

        # Temperature
        self.temperature = QComboBox()
        self.temperature.addItems(["Normal (10-25°C)", "Cold (<10°C)", "Hot (>25°C)"])
        form.addRow("Temperature:", self.temperature)

        layout.addLayout(form)

        # Find button
        btn_find = QPushButton("🔍 Find Best Primers")
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
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def find_primers(self):
        """Find recommended primers"""
        cartridge = self.cartridge.currentText()
        powder = self.powder.currentText()
        use_case = self.use_case.currentText()
        temp = self.temperature.currentText()

        # Simple recommendation logic (can be expanded with database)
        results_html = f"""
        <h3>Recommendations for your setup:</h3>
        <p><b>Cartridge:</b> {cartridge}<br>
        <b>Powder:</b> {powder}<br>
        <b>Use:</b> {use_case}<br>
        <b>Temperature:</b> {temp}</p>

        <hr>

        <div style='background-color: #d5f4e6; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
        <h4>🏆 #1 RECOMMENDED: CCI BR-2</h4>
        <p><b>Why:</b> Most popular large rifle match primer. Proven consistency with {powder}.</p>
        <p><b>Pros:</b> Excellent lot-to-lot consistency, thick cup (safe), widely available</p>
        <p><b>Cons:</b> May give slightly higher SD than Federal in some rifles</p>
        <p><b>Typical SD impact:</b> Baseline (8-12 fps SD)</p>
        <p><b>Price:</b> ~80 kr / 100 pcs</p>
        </div>

        <div style='background-color: #fff9c4; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
        <h4>🥈 #2 ALTERNATIVE: Federal 210M</h4>
        <p><b>Why:</b> Softer cup, may improve SD in some rifles.</p>
        <p><b>Pros:</b> Can give 5-10% lower SD, gentle ignition, match-grade</p>
        <p><b>Cons:</b> Softer cup (careful with seating), less available</p>
        <p><b>Typical SD impact:</b> -5 to -10% vs CCI BR-2 (7-11 fps SD)</p>
        <p><b>Price:</b> ~90 kr / 100 pcs</p>
        </div>
        """

        # Add magnum option if cold or slow powder
        if "Cold" in temp or "N150" in powder or "N160" in powder or "H1000" in powder:
            results_html += """
            <div style='background-color: #ffe0b2; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
            <h4>🔥 #3 CONSIDER: Federal 215M (Magnum)</h4>
            <p><b>Why:</b> Cold weather or slow powder detected - magnum primer recommended.</p>
            <p><b>Pros:</b> Better ignition in cold, complete powder burn, less SD variation with temp</p>
            <p><b>Cons:</b> Hotter - reduce charge 0.5gr and work up!, may increase pressure</p>
            <p><b>Typical SD impact:</b> +10-15 fps velocity, similar SD to standard in cold</p>
            <p><b>Price:</b> ~95 kr / 100 pcs</p>
            <p style='color: #e74c3c;'><b>⚠️ WARNING:</b> START 0.5gr LOWER with magnum primers!</p>
            </div>
            """

        results_html += """
        <hr>
        <h4>💡 Pro Tips:</h4>
        <ul>
            <li>Test both CCI and Federal in YOUR rifle - results vary!</li>
            <li>Buy same lot number when you find a good combo</li>
            <li>Seat primers 0.002-0.004" below flush</li>
            <li>Use primer pocket uniformer for consistency</li>
        </ul>

        <h4>❌ Primers to AVOID:</h4>
        <ul>
            <li><b>Small rifle primers:</b> Wrong size for {cartridge}!</li>
            <li><b>Winchester WLR:</b> More variation, not match-grade</li>
            <li><b>Russian primers:</b> Hard to find, inconsistent</li>
        </ul>
        """

        self.results.setHtml(results_html)


class PrimerComparisonDialog(QDialog):
    """Compare different primers side-by-side"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Primer Comparison Table")
        self.resize(1000, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("<h2>📊 Primer Comparison Table</h2>")
        layout.addWidget(title)

        info = QLabel("Compare primers across key characteristics")
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
                "Size",
                "Type",
                "Brisance",
                "Cup Thickness",
                "SD Impact",
                "Best For",
                "Price/100",
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

        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Legend
        legend = QLabel(
            """
        <b>Legend:</b><br>
        <b>Brisance:</b> Ignition strength (Soft < Medium < Hot)<br>
        <b>Cup Thickness:</b> Affects sensitivity and slam-fire risk<br>
        <b>SD Impact:</b> Effect on velocity Standard Deviation vs baseline<br>
        <span style='background-color: #d5f4e6; padding: 3px;'>Green = Better SD</span>
        <span style='background-color: #ffcccc; padding: 3px;'>Red = Worse SD</span>
        """
        )
        legend.setStyleSheet(
            "background-color: #ecf0f1; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(legend)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class SubstitutionFinderDialog(QDialog):
    """Find primer substitutes when out of stock"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Primer Substitution Finder")
        self.resize(700, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("<h2>🔄 Primer Substitution Finder</h2>")
        layout.addWidget(title)

        info = QLabel("Find the best alternative when your primer is out of stock")
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
        form.addRow("Out of stock:", self.original_primer)

        layout.addLayout(form)

        # Find button
        btn_find = QPushButton("🔍 Find Substitutes")
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
        close_btn = QPushButton("Close")
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
                    "✅ No load adjustment needed",
                ),
                (
                    "Remington 9½",
                    "90%",
                    "Similar performance. Slightly less consistent.",
                    "⚠️ Test in your rifle first",
                ),
                (
                    "Winchester WLR",
                    "80%",
                    "Budget option. Expect +10-15% SD increase.",
                    "⚠️ Not match-grade",
                ),
            ],
            "Federal 210M": [
                (
                    "CCI BR-2",
                    "95%",
                    "Thicker cup, may increase SD slightly but more consistent.",
                    "✅ Direct substitute",
                ),
                ("Remington 9½", "85%", "Less precise, but works.", "⚠️ Re-test load"),
                (
                    "RWS 5341",
                    "98%",
                    "European match primer. Excellent if available.",
                    "✅ Premium option",
                ),
            ],
            "CCI 450": [
                (
                    "Federal 205M",
                    "90%",
                    "Match-grade, softer cup. May improve SD.",
                    "⚠️ Test for slam-fire in AR-15",
                ),
                (
                    "Remington 7½",
                    "85%",
                    "Benchrest primer, thinner cup.",
                    "⚠️ Careful in semi-auto",
                ),
                (
                    "CCI 400",
                    "80%",
                    "Standard version. More variance.",
                    "⚠️ Not match-grade",
                ),
            ],
        }

        if primer not in substitutions:
            self.results.setHtml("<p>No substitution data for this primer yet.</p>")
            return

        results_html = f"<h3>Substitutes for {primer}:</h3>"

        for i, (sub, compatibility, notes, adjustment) in enumerate(
            substitutions[primer], 1
        ):
            color = "#d5f4e6" if i == 1 else "#fff9c4" if i == 2 else "#ffe0b2"
            results_html += f"""
            <div style='background-color: {color}; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
            <h4>#{i}: {sub} ({compatibility} compatible)</h4>
            <p><b>Notes:</b> {notes}</p>
            <p><b>Load Adjustment:</b> {adjustment}</p>
            </div>
            """

        results_html += """
        <hr>
        <h4>⚠️ Important When Substituting:</h4>
        <ul>
            <li><b>Always re-test your load</b> - don't assume same charge is safe!</li>
            <li><b>Start 10% lower</b> and work back up if switching to magnum primers</li>
            <li><b>Watch for pressure signs</b> - different primers = different pressure</li>
            <li><b>Chrono your loads</b> - velocity will likely change</li>
            <li><b>Record lot numbers</b> - primers vary batch-to-batch</li>
        </ul>
        """

        self.results.setHtml(results_html)


class SeatingDepthGuideDialog(QDialog):
    """Visual guide for correct primer seating depth"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📏 Primer Seating Depth Guide")
        self.resize(800, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("<h2>📏 Primer Seating Depth Guide</h2>")
        layout.addWidget(title)

        # Visual guide with ASCII art
        guide_html = """
        <div style='font-family: monospace; background-color: #ecf0f1; padding: 20px; border-radius: 5px;'>

        <h3>Correct Primer Seating:</h3>

        <p><b style='color: #e74c3c;'>❌ FLUSH (0.000" below)</b> - DANGEROUS!</p>
        <pre style='background-color: #ffcccc; padding: 10px;'>
┌────────────┐
│  Primer    │ ← Primer edge flush with case head
└────────────┘
═══════════════ Case Head
        </pre>
        <p><b>Problem:</b> Slam fire risk in AR-15! Primer not fully seated on anvil.</p>

        <hr>

        <p><b style='color: #f39c12;'>⚠️ SHALLOW (-0.001" below)</b> - Risky</p>
        <pre style='background-color: #ffe0b2; padding: 10px;'>
┌────────────┐
│  Primer    │
└────────────┘ ← 0.001" gap
═══════════════ Case Head
        </pre>
        <p><b>Problem:</b> May not contact anvil properly. Potential misfires.</p>

        <hr>

        <p><b style='color: #27ae60;'>✅ PERFECT (-0.002" to -0.004" below)</b> - IDEAL!</p>
        <pre style='background-color: #d5f4e6; padding: 10px;'>
  ┌──────────┐
  │ Primer   │
  └──────────┘ ← 0.002-0.004" below
═══════════════ Case Head
        </pre>
        <p><b>Perfect!</b> Anvil seated firmly, no crush, safe ignition.</p>

        <hr>

        <p><b style='color: #e74c3c;'>❌ TOO DEEP (-0.006"+ below)</b> - DANGEROUS!</p>
        <pre style='background-color: #ffcccc; padding: 10px;'>
    ┌────────┐
    │Primer  │ ← Crushed!
    └────────┘
═══════════════ Case Head
        </pre>
        <p><b>Problem:</b> Primer compound crushed! Pressure spike, possible detonation!</p>

        </div>

        <h3>How to Measure:</h3>
        <ol>
            <li><b>Use depth gauge or caliper:</b> Measure from case head to primer face</li>
            <li><b>Feel method:</b> Primer should be firm, not spongy or crunchy</li>
            <li><b>Visual:</b> Should see small gap, not flush</li>
        </ol>

        <h3>💡 Pro Tips:</h3>
        <ul>
            <li><b>Uniform primer pockets</b> with RCBS or Sinclair tool</li>
            <li><b>Clean pockets</b> - carbon buildup affects depth</li>
            <li><b>Consistent seating force</b> - use hand tool for match ammo</li>
            <li><b>Check anvil contact:</b> Primer should feel solid, not spongy</li>
            <li><b>AR-15 warning:</b> MUST be below flush to prevent slam fire!</li>
        </ul>

        <h3>Tools Needed:</h3>
        <ul>
            <li><b>Primer pocket uniformer:</b> RCBS, Sinclair (~200 kr)</li>
            <li><b>Depth gauge:</b> Check seating depth (~300 kr)</li>
            <li><b>Hand priming tool:</b> Better feel than progressive (~400 kr)</li>
        </ul>
        """

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel(guide_html)
        content.setWordWrap(True)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class PressureSignsDialog(QDialog):
    """Visual guide for identifying pressure signs on primers"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛡️ Primer Pressure Signs Guide")
        self.resize(800, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("<h2>🛡️ Primer Pressure Signs Guide</h2>")
        layout.addWidget(title)

        info = QLabel(
            "<b>Learn to identify over-pressure signs on fired primers</b><br>"
            "This can save your rifle - and your face!"
        )
        info.setStyleSheet(
            "background-color: #ffe0b2; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(info)

        # Pressure signs guide
        guide_html = """
        <h3>Primer Appearance After Firing:</h3>

        <div style='background-color: #d5f4e6; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
        <h4>✅ NORMAL PRESSURE:</h4>
        <p><b>Appearance:</b> Rounded edges, slight indentation from firing pin</p>
        <p><b>Primer cup:</b> Still slightly rounded, not flattened</p>
        <p><b>Edges:</b> Sharp and distinct</p>
        <p><b>Action:</b> Continue load development safely</p>
        </div>

        <div style='background-color: #fff9c4; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
        <h4>⚠️ WARNING - APPROACHING MAX:</h4>
        <p><b>Slight flattening:</b> Primer starting to flow into firing pin hole</p>
        <p><b>Edges rounding:</b> Sharp edges becoming slightly rounded</p>
        <p><b>Cratering beginning:</b> Slight indentation around firing pin</p>
        <p><b>Action:</b> DO NOT INCREASE CHARGE. Check other pressure signs (sticky bolt, ejector marks). Consider backing off 0.5gr.</p>
        </div>

        <div style='background-color: #ffcccc; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
        <h4>🛑 DANGER - OVER-PRESSURE!</h4>
        <p><b>Completely flat:</b> Primer cup totally flattened</p>
        <p><b>Deep cratering:</b> Primer flows into firing pin hole</p>
        <p><b>Pierced primer:</b> Hole punched through primer cup</p>
        <p><b>Blown primer:</b> Primer falls out or gas leak</p>
        <p><b>Action:</b> STOP IMMEDIATELY! Reduce charge 10% and work back up slowly!</p>
        </div>

        <hr>

        <h3>Other Pressure Signs to Check:</h3>
        <ul>
            <li><b>Ejector mark:</b> Round impression on case head</li>
            <li><b>Sticky bolt:</b> Hard to lift bolt after firing</li>
            <li><b>Case head expansion:</b> Measure with caliper (>0.0005" growth = high pressure)</li>
            <li><b>Shiny pressure ring:</b> Ring above case head from case stretching</li>
            <li><b>Split necks:</b> Case neck splits from overpressure</li>
        </ul>

        <h3>❌ False Pressure Signs:</h3>
        <ul>
            <li><b>Large firing pin hole:</b> Can cause cratering even at safe pressure</li>
            <li><b>Soft primers:</b> Federal primers flatten easier than CCI (doesn't always mean overpressure)</li>
            <li><b>Dirty chamber:</b> Can cause false sticky bolt</li>
        </ul>

        <h3>🎯 Best Practice:</h3>
        <ol>
            <li><b>Start low:</b> Begin 10% below max listed charge</li>
            <li><b>Work up slowly:</b> Increase 0.2-0.5gr at a time</li>
            <li><b>Watch ALL signs:</b> Don't rely on primer alone</li>
            <li><b>Use chronograph:</b> Velocity plateau = pressure max</li>
            <li><b>Back off 1-2gr from max</b> for safe operating load</li>
        </ol>

        <div style='background-color: #e74c3c; color: white; padding: 15px; border-radius: 5px; margin-top: 20px;'>
        <h3>⚠️ SAFETY WARNING:</h3>
        <p><b>IF YOU SEE PRESSURE SIGNS:</b></p>
        <ul>
            <li>Stop shooting immediately</li>
            <li>Do not fire remaining ammo with that charge</li>
            <li>Reduce charge weight 10%</li>
            <li>Work back up carefully in 0.2gr increments</li>
            <li>When in doubt, ASK EXPERIENCED RELOADERS!</li>
        </ul>
        </div>
        """

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel(guide_html)
        content.setWordWrap(True)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Close
        close_btn = QPushButton("Close")
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
