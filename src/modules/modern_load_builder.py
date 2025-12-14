"""
Modern Load Builder - Interactive visual load development with AI assistant
Replaces old wizard with intuitive 2-step workflow + live visualization
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QMessageBox,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QTextEdit as QTextEditWidget,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
)

from src.database.database import get_database
import statistics

# Importing heavy visualization libs lazily inside methods to avoid
# expensive imports at module import time (helps headless/CI probes).


class ModernLoadBuilder(QWidget):
    """
    Modern 2-step load development interface:
    Step 1: Select rifle + brass (quick)
    Step 2: Interactive load builder with live graphs + AI chat
    """

    load_created = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        # Defer creation of ballistics engine until actually needed to avoid
        # expensive/side-effectful initialization during import/UI composition.
        self._engine = None

        # State
        self.current_step = 1
        self.rifle_data = None
        self.brass_data = None
        self.bullet_data = None
        self.powder_data = None
        self.primer_data = None
        self.current_charge = 42.5
        self.coal_mm = 71.5
        self.cbto_mm = 68.8

        # AI chat history
        self.chat_history = []

        self.init_ui()

    @property
    def engine(self):
        """Lazily initialize and return the ballistics engine."""
        if getattr(self, "_engine", None) is None:
            try:
                from src.modules.ballistics_engine import get_ballistics_engine

                self._engine = get_ballistics_engine()
            except Exception:
                self._engine = None
        return self._engine

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Container for step pages
        self.step1_widget = self.create_step1_page()
        self.step2_widget = self.create_step2_page()

        # Show step 1 initially
        layout.addWidget(self.step1_widget)
        self.step2_widget.hide()

        self.setLayout(layout)

    def create_step1_page(self):
        """Step 1: Select Rifle & Brass"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel("🎯 New Load - Select Rifle & Brass")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 20px;")
        layout.addWidget(header)

        subtitle = QLabel("Choose your rifle and brass batch to get started")
        subtitle.setStyleSheet(
            "color: #7f8c8d; font-size: 12pt; padding-left: 20px; padding-bottom: 20px;"
        )
        layout.addWidget(subtitle)

        # Content area
        content = QHBoxLayout()

        # Left: Rifle selection
        rifle_group = self.create_rifle_selection_panel()
        content.addWidget(rifle_group)

        # Right: Brass selection
        brass_group = self.create_brass_selection_panel()
        content.addWidget(brass_group)

        layout.addLayout(content)

        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        self.next_btn = QPushButton("Next: Build Load →")
        self.next_btn.setStyleSheet(
            """
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #229954;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
        """
        )
        self.next_btn.clicked.connect(self.go_to_step2)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_rifle_selection_panel(self):
        """Create rifle selection panel"""
        group = QGroupBox("🎯 Your Rifles")
        group.setStyleSheet(
            """
            QGroupBox {
                font-size: 14pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                margin: 10px;
            }
        """
        )
        layout = QVBoxLayout()

        # Radio buttons for rifles
        self.rifle_button_group = QButtonGroup()

        rifles = self.db.execute_query("SELECT * FROM rifles ORDER BY name")

        if rifles:
            for rifle in rifles:
                rb = QRadioButton(f"{rifle['name']} ({rifle['caliber']})")
                rb.setStyleSheet("font-size: 11pt; padding: 10px;")
                rb.rifle_data = rifle
                rb.toggled.connect(self.on_rifle_selected)
                self.rifle_button_group.addButton(rb)
                layout.addWidget(rb)
        else:
            no_rifles = QLabel("No rifles found. Add rifles in Inventory tab first.")
            no_rifles.setStyleSheet(
                "color: #e67e22; font-style: italic; padding: 20px;"
            )
            layout.addWidget(no_rifles)

        layout.addStretch()

        add_btn = QPushButton("+ Add New Rifle")
        add_btn.setStyleSheet("color: #3498db; font-size: 10pt; padding: 8px;")
        layout.addWidget(add_btn)

        group.setLayout(layout)
        return group

    def create_brass_selection_panel(self):
        """Create brass selection panel"""
        group = QGroupBox("🥉 Your Brass")
        group.setStyleSheet(
            """
            QGroupBox {
                font-size: 14pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                margin: 10px;
            }
        """
        )
        layout = QVBoxLayout()

        self.brass_button_group = QButtonGroup()

        # Will populate when rifle is selected
        self.brass_container = QVBoxLayout()
        layout.addLayout(self.brass_container)

        layout.addStretch()

        add_btn = QPushButton("+ Add New Brass Batch")
        add_btn.setStyleSheet("color: #3498db; font-size: 10pt; padding: 8px;")
        layout.addWidget(add_btn)

        group.setLayout(layout)
        return group

    def on_rifle_selected(self, checked):
        """Handle rifle selection"""
        if not checked:
            return

        sender = self.sender()
        self.rifle_data = sender.rifle_data

        # Load brass for this caliber
        self.load_brass_for_caliber(self.rifle_data["caliber"])

        self.check_step1_complete()

    def load_brass_for_caliber(self, caliber):
        """Load brass batches for selected caliber"""
        # Clear existing
        while self.brass_container.count():
            item = self.brass_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Query brass
        brass_batches = self.db.execute_query(
            """
            SELECT bb.*, c.name as case_name
            FROM brass_batches bb
            JOIN cases c ON bb.case_id = c.id
            WHERE c.caliber = ?
            AND bb.cases_active > 0
            ORDER BY bb.created_date DESC
        """,
            (caliber,),
        )

        if brass_batches:
            for brass in brass_batches:
                rb = QRadioButton(
                    f"{brass['case_name']} Batch #{brass['id']}\n"
                    f"  {brass['cases_active']} cases, "
                    f"{brass.get('times_fired_avg', 0):.0f}x fired"
                )
                rb.setStyleSheet("font-size: 11pt; padding: 10px;")
                rb.brass_data = brass
                rb.toggled.connect(self.on_brass_selected)
                self.brass_button_group.addButton(rb)
                self.brass_container.addWidget(rb)
        else:
            no_brass = QLabel(f"No brass found for {caliber}")
            no_brass.setStyleSheet("color: #e67e22; font-style: italic;")
            self.brass_container.addWidget(no_brass)

    def on_brass_selected(self, checked):
        """Handle brass selection"""
        if not checked:
            return

        sender = self.sender()
        self.brass_data = sender.brass_data

        self.check_step1_complete()

    def check_step1_complete(self):
        """Enable next button if rifle and brass selected"""
        if self.rifle_data and self.brass_data:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)

    def go_to_step2(self):
        """Move to step 2: Load builder"""
        # Hide step 1
        self.step1_widget.hide()

        # Show step 2
        self.layout().addWidget(self.step2_widget)
        self.step2_widget.show()

        # Initialize step 2 with rifle data
        self.initialize_step2()

    def create_step2_page(self):
        """Step 2: Interactive Load Builder"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("padding: 10px; font-size: 11pt;")
        back_btn.clicked.connect(self.go_back_to_step1)
        header_layout.addWidget(back_btn)

        title = QLabel("🔬 Interactive Load Builder")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        save_btn = QPushButton("💾 Save Load")
        save_btn.setStyleSheet(
            """
            background: #3498db; color: white;
            padding: 10px 20px; border-radius: 5px;
            font-weight: bold;
        """
        )
        header_layout.addWidget(save_btn)

        create_batch_btn = QPushButton("📦 Create Batch")
        create_batch_btn.setStyleSheet(
            """
            background: #27ae60; color: white;
            padding: 10px 20px; border-radius: 5px;
            font-weight: bold;
        """
        )
        header_layout.addWidget(create_batch_btn)
        create_batch_btn.clicked.connect(self.on_create_batch_clicked)

        layout.addLayout(header_layout)

        # Main content: Splitter (left controls, right visualization)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Controls
        left_panel = self.create_controls_panel()
        splitter.addWidget(left_panel)

        # Right panel: Visualization
        right_panel = self.create_visualization_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 2)  # Controls: 40%
        splitter.setStretchFactor(1, 3)  # Viz: 60%

        layout.addWidget(splitter, 1)

        # Bottom: AI Chat (collapsible)
        self.chat_widget = self.create_ai_chat_panel()
        layout.addWidget(self.chat_widget)

        widget.setLayout(layout)
        return widget

    def create_controls_panel(self):
        """Create left control panel"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        # Components
        comp_group = self.create_component_controls()
        scroll_layout.addWidget(comp_group)

        # Charge weight slider
        charge_group = self.create_charge_slider()
        scroll_layout.addWidget(charge_group)

        # Seating depth
        seating_group = self.create_seating_controls()
        scroll_layout.addWidget(seating_group)

        scroll_layout.addStretch()

        # Import chronograph CSV button
        import_btn = QPushButton("📥 Import Chronograph CSV")
        import_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        import_btn.clicked.connect(self.on_import_chronograph_clicked)
        scroll_layout.addWidget(import_btn)

        # Manual chronograph entry
        manual_btn = QPushButton("✍️ Manually Add Chronograph Data")
        manual_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        manual_btn.clicked.connect(self.on_manual_chronograph_clicked)
        scroll_layout.addWidget(manual_btn)

        # Chronograph imports list
        chrono_group = QGroupBox("Imported Chronograph Data")
        chrono_layout = QVBoxLayout()

        self.chrono_list = QListWidget()
        chrono_layout.addWidget(self.chrono_list)
        self.chrono_list.itemSelectionChanged.connect(self.on_chrono_selection_changed)

        chrono_btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("↺ Refresh")
        refresh_btn.clicked.connect(self.on_refresh_chronograph_list)
        chrono_btn_layout.addWidget(refresh_btn)

        attach_btn = QPushButton("🔗 Attach to Profile")
        attach_btn.clicked.connect(self.on_attach_chronograph_to_profile)
        chrono_btn_layout.addWidget(attach_btn)

        save_btn = QPushButton("💾 Save Import → Test Results")
        save_btn.clicked.connect(self.on_save_chronograph_to_test_results)
        chrono_btn_layout.addWidget(save_btn)

        qc_attach_btn = QPushButton("🏷️ Attach to QC Batch")
        qc_attach_btn.clicked.connect(self.on_attach_chrono_to_qc_batch)
        chrono_btn_layout.addWidget(qc_attach_btn)

        suggest_btn = QPushButton("💡 Analyze & Suggest")
        suggest_btn.clicked.connect(self.on_analyze_and_suggest)
        chrono_btn_layout.addWidget(suggest_btn)

        chrono_layout.addLayout(chrono_btn_layout)
        chrono_group.setLayout(chrono_layout)
        scroll_layout.addWidget(chrono_group)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll)
        widget.setLayout(layout)

        return widget

    def create_component_controls(self):
        """Create component selection controls"""
        group = QGroupBox("💊 Components")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12pt; }")
        layout = QVBoxLayout()

        # Bullet
        bullet_label = QLabel("Bullet:")
        layout.addWidget(bullet_label)

        self.bullet_combo = QComboBox()
        self.bullet_combo.currentIndexChanged.connect(self.on_bullet_changed)
        layout.addWidget(self.bullet_combo)

        self.bullet_info = QLabel("Select bullet to see details")
        self.bullet_info.setStyleSheet(
            "color: #7f8c8d; font-size: 9pt; font-style: italic;"
        )
        layout.addWidget(self.bullet_info)

        layout.addSpacing(10)

        # Powder
        powder_label = QLabel("Powder:")
        layout.addWidget(powder_label)

        self.powder_combo = QComboBox()
        self.powder_combo.currentIndexChanged.connect(self.on_powder_changed)
        layout.addWidget(self.powder_combo)

        self.powder_info = QLabel("Select powder to see details")
        self.powder_info.setStyleSheet(
            "color: #7f8c8d; font-size: 9pt; font-style: italic;"
        )
        layout.addWidget(self.powder_info)

        # AI recommendation placeholder
        self.powder_recommendation = QLabel("")
        self.powder_recommendation.setWordWrap(True)
        self.powder_recommendation.setStyleSheet(
            """
            background: #e8f4f8;
            color: #2c3e50;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #9b59b6;
        """
        )
        layout.addWidget(self.powder_recommendation)

        layout.addSpacing(10)

        # Primer
        primer_label = QLabel("Primer:")
        layout.addWidget(primer_label)

        self.primer_combo = QComboBox()
        layout.addWidget(self.primer_combo)

        self.primer_info = QLabel("Select primer to see details")
        self.primer_info.setStyleSheet(
            "color: #7f8c8d; font-size: 9pt; font-style: italic;"
        )
        layout.addWidget(self.primer_info)

        group.setLayout(layout)
        return group

    def create_charge_slider(self):
        """Create charge weight slider"""
        group = QGroupBox("⚖️ Charge Weight")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12pt; }")
        layout = QVBoxLayout()

        # Current value display
        self.charge_label = QLabel(f"{self.current_charge:.1f} gr")
        self.charge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.charge_label.setStyleSheet(
            """
            font-size: 24pt;
            font-weight: bold;
            color: #27ae60;
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
        """
        )
        layout.addWidget(self.charge_label)

        # Slider
        self.charge_slider = QSlider(Qt.Orientation.Horizontal)
        self.charge_slider.setMinimum(300)  # 30.0gr
        self.charge_slider.setMaximum(550)  # 55.0gr
        self.charge_slider.setValue(425)  # 42.5gr
        self.charge_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.charge_slider.setTickInterval(25)
        self.charge_slider.valueChanged.connect(self.on_charge_slider_changed)
        layout.addWidget(self.charge_slider)

        # Min/Max labels
        limits_layout = QHBoxLayout()
        limits_layout.addWidget(QLabel("30.0 gr"))
        limits_layout.addStretch()
        limits_layout.addWidget(QLabel("55.0 gr"))
        layout.addLayout(limits_layout)

        # Hint
        hint = QLabel("💡 Drag to see real-time results!")
        hint.setStyleSheet("color: #7f8c8d; font-size: 9pt; font-style: italic;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        group.setLayout(layout)
        return group

    def create_seating_controls(self):
        """Create seating depth controls"""
        group = QGroupBox("📏 Seating Depth")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12pt; }")
        layout = QVBoxLayout()

        # COAL
        coal_layout = QHBoxLayout()
        coal_layout.addWidget(QLabel("COAL:"))
        self.coal_spin = QDoubleSpinBox()
        self.coal_spin.setRange(50.0, 100.0)
        self.coal_spin.setValue(71.5)
        self.coal_spin.setDecimals(2)
        self.coal_spin.setSuffix(" mm")
        self.coal_spin.valueChanged.connect(self.on_seating_changed)
        coal_layout.addWidget(self.coal_spin)
        layout.addLayout(coal_layout)

        # CBTO
        cbto_layout = QHBoxLayout()
        cbto_layout.addWidget(QLabel("CBTO:"))
        self.cbto_spin = QDoubleSpinBox()
        self.cbto_spin.setRange(50.0, 100.0)
        self.cbto_spin.setValue(68.8)
        self.cbto_spin.setDecimals(2)
        self.cbto_spin.setSuffix(" mm")
        self.cbto_spin.valueChanged.connect(self.on_seating_changed)
        cbto_layout.addWidget(self.cbto_spin)
        layout.addLayout(cbto_layout)

        # Jump display
        self.jump_label = QLabel("Jump: calculating...")
        self.jump_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        layout.addWidget(self.jump_label)

        # Optimize button
        optimize_btn = QPushButton("🤖 Optimize for Accuracy")
        optimize_btn.setStyleSheet(
            """
            background: #9b59b6;
            color: white;
            padding: 8px;
            border-radius: 5px;
        """
        )
        layout.addWidget(optimize_btn)

        group.setLayout(layout)
        return group

    def create_visualization_panel(self):
        """Create right visualization panel"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Stats bar
        stats_group = self.create_stats_bar()
        layout.addWidget(stats_group)

        # Scope adjustment comparison
        self.scope_comparison_group = QGroupBox(
            "🎯 KIKKERT JUSTERING (vs. forrige ladning)"
        )
        self.scope_comparison_group.setStyleSheet(
            """
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                font-weight: bold;
                padding-top: 15px;
            }
        """
        )
        scope_layout = QVBoxLayout()
        self.scope_comparison_group.setLayout(scope_layout)

        self.scope_comparison_label = QLabel(
            "Velg rifle og komponenter for å se sammenligning..."
        )
        self.scope_comparison_label.setWordWrap(True)
        self.scope_comparison_label.setStyleSheet(
            "color: #856404; font-weight: normal; padding: 5px; font-size: 9pt;"
        )
        scope_layout.addWidget(self.scope_comparison_label)

        self.scope_comparison_group.setVisible(False)
        layout.addWidget(self.scope_comparison_group)

        # 🎯 Scope Adjustment Comparison (vs previous load)
        self.scope_comparison_group = QGroupBox(
            "🎯 KIKKERT JUSTERING (vs. forrige ladning)"
        )
        self.scope_comparison_group.setStyleSheet(
            """
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                margin-top: 5px;
                font-weight: bold;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        scope_comp_layout = QVBoxLayout()
        self.scope_comparison_label = QLabel(
            "Velg rifle for å se sammenligning med forrige ladning."
        )
        self.scope_comparison_label.setWordWrap(True)
        self.scope_comparison_label.setStyleSheet(
            "color: #856404; font-weight: normal; padding: 10px; font-size: 9pt;"
        )
        scope_comp_layout.addWidget(self.scope_comparison_label)
        self.scope_comparison_group.setLayout(scope_comp_layout)
        self.scope_comparison_group.setVisible(False)
        layout.addWidget(self.scope_comparison_group)

        # Pressure & Velocity plots - lazy-import pyqtgraph and provide safe
        # fallbacks if the library is unavailable (prevents heavy import at
        # module load time and keeps headless probes lightweight).
        try:
            import pyqtgraph as pg  # type: ignore

            # Keep reference to pyqtgraph module for later use
            self._pg = pg

            self.pressure_plot = pg.PlotWidget()
            self.pressure_plot.setBackground("w")
            self.pressure_plot.setLabel("left", "Pressure", units="PSI")
            self.pressure_plot.setLabel("bottom", "Time", units="ms")
            self.pressure_plot.setTitle("Chamber Pressure", color="k", size="12pt")
            self.pressure_plot.setMinimumHeight(200)
            layout.addWidget(self.pressure_plot)

            self.velocity_plot = pg.PlotWidget()
            self.velocity_plot.setBackground("w")
            self.velocity_plot.setLabel("left", "Velocity", units="fps")
            self.velocity_plot.setLabel("bottom", "Position", units="inches")
            self.velocity_plot.setTitle("Bullet Velocity", color="k", size="12pt")
            self.velocity_plot.setMinimumHeight(200)
            layout.addWidget(self.velocity_plot)
        except Exception:
            # Fallback: simple read-only text placeholders so UI still renders
            from PyQt6.QtWidgets import QTextEdit

            ph1 = QTextEdit("Pressure plot unavailable (pyqtgraph missing)")
            ph1.setReadOnly(True)
            ph1.setMinimumHeight(200)
            layout.addWidget(ph1)

            ph2 = QTextEdit("Velocity plot unavailable (pyqtgraph missing)")
            ph2.setReadOnly(True)
            ph2.setMinimumHeight(200)
            layout.addWidget(ph2)

        # Compare button
        compare_btn = QPushButton("📊 Compare with Other Powders")
        compare_btn.setStyleSheet("padding: 10px; font-size: 11pt;")
        layout.addWidget(compare_btn)

        widget.setLayout(layout)
        return widget

    def create_stats_bar(self):
        """Create statistics display bar"""
        group = QGroupBox("📊 Current Load Statistics")
        layout = QHBoxLayout()

        self.stat_pressure = QLabel("Pressure: --")
        self.stat_velocity = QLabel("Velocity: --")
        self.stat_energy = QLabel("Energy: --")
        self.stat_barrel_time = QLabel("Time: --")
        self.stat_safety = QLabel("Safety: --%")

        for label in [
            self.stat_pressure,
            self.stat_velocity,
            self.stat_energy,
            self.stat_barrel_time,
            self.stat_safety,
        ]:
            label.setStyleSheet("padding: 8px; font-size: 10pt;")
            layout.addWidget(label)

        group.setLayout(layout)
        return group

    def create_ai_chat_panel(self):
        """Create AI chat panel (collapsible)"""
        widget = QWidget()
        widget.setMaximumHeight(300)
        layout = QVBoxLayout()

        # Header with collapse button
        header_layout = QHBoxLayout()

        chat_title = QLabel("🤖 AI Assistant")
        chat_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        chat_title.setStyleSheet("color: #9b59b6;")
        header_layout.addWidget(chat_title)

        header_layout.addStretch()

        self.collapse_btn = QPushButton("▼ Collapse")
        self.collapse_btn.setStyleSheet("background: transparent; color: #7f8c8d;")
        self.collapse_btn.clicked.connect(self.toggle_chat)
        header_layout.addWidget(self.collapse_btn)

        layout.addLayout(header_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(
            """
            QTextEdit {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 10pt;
            }
        """
        )
        layout.addWidget(self.chat_display, 1)

        # Input area
        input_layout = QHBoxLayout()

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask me anything about reloading...")
        self.chat_input.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                font-size: 10pt;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """
        )
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(
            """
            QPushButton {
                background: #9b59b6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """
        )
        send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # Add welcome message
        self.add_ai_message(
            "👋 Hi! I'm your AI reloading assistant. I can help with:\n\n"
            "• Component recommendations\n"
            "• Explaining pressure/velocity\n"
            "• Load development advice\n"
            "• Safety questions\n\n"
            "Just ask me anything!"
        )

        widget.setLayout(layout)
        return widget

    def on_create_batch_clicked(self):
        """UI handler: ask for batch name/size and create batch"""
        # Ensure components selected
        if not (self.rifle_data and self.bullet_data and self.powder_data and self.brass_data):
            QMessageBox.warning(self, "Missing data", "Please select rifle, brass, bullet and powder before creating a batch.")
            return

        count, ok = QInputDialog.getInt(self, "Batch Size", "How many rounds to create?", 10, 1, 10000, 1)
        if not ok:
            return

        name, ok2 = QInputDialog.getText(self, "Batch Name", "Name for this batch:", text=f"Batch for {self.rifle_data.get('name','rifle')}")
        if not ok2:
            return

        # Ensure there's an ammo_profile for this configuration; create minimal profile
        cur = self.db.cursor
        # Build minimal ammo_profile
        cur.execute(
            "INSERT INTO ammo_profiles (name, rifle_id, caliber, bullet_id, bullet_weight, powder_id, powder_charge, primer_id, case_id, coal, cbto, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (
                name,
                self.rifle_data.get("id"),
                self.rifle_data.get("caliber"),
                self.bullet_data.get("id"),
                float(self.bullet_data.get("weight", 0)),
                self.powder_data.get("id"),
                float(self.current_charge),
                self.primer_data.get("id") if self.primer_data else None,
                self.brass_data.get("id") if self.brass_data else None,
                float(self.coal_mm),
                float(self.cbto_mm),
            ),
        )
        self.db.conn.commit()
        ammo_profile_id = cur.lastrowid

        # Call batch manager
        try:
            from src.database.batch_manager import create_loading_batch

            res = create_loading_batch(self.db, ammo_profile_id, name, count, self.current_charge, self.coal_mm, self.cbto_mm)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create batch: {e}")
            return

        if not res.get("ok"):
            QMessageBox.warning(self, "Batch not created", res.get("message", "Unknown error"))
            return

        QMessageBox.information(self, "Batch created", f"Batch created (id={res.get('batch_id')}). Inventory updated.")

    def on_import_chronograph_clicked(self):
        """Open a file dialog, import selected CSV and show stats"""
        path, _ = QFileDialog.getOpenFileName(self, "Select chronograph CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return

        try:
            from src.utils.chronograph_import import import_chronograph_csv

            res = import_chronograph_csv(self.db, path, None, note=f"Imported via UI from {path}")
        except Exception as e:
            QMessageBox.critical(self, "Import failed", f"Failed to import CSV: {e}")
            return

        stats = res.get("stats", {})
        QMessageBox.information(
            self,
            "Import complete",
            f"Imported {stats.get('count', 0)} velocities. Avg: {stats.get('avg')}, ES: {stats.get('es')}, SD: {stats.get('sd')}",
        )

    def on_manual_chronograph_clicked(self):
        """Open dialog to paste velocities (one per line or comma-separated) and insert into DB"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Manual Chronograph Entry")
        layout = QVBoxLayout()

        info = QLabel("Paste velocities (one per line or comma-separated). Optionally enter an Ammo Profile ID to link:")
        layout.addWidget(info)

        vel_text = QTextEditWidget()
        vel_text.setPlaceholderText("e.g.\n820.1\n818.5\n823.0\n... or 820,818.5,823")
        vel_text.setMinimumHeight(120)
        layout.addWidget(vel_text)

        ap_label = QLabel("Ammo Profile ID (optional):")
        layout.addWidget(ap_label)
        ap_input = QLineEdit()
        ap_input.setPlaceholderText("e.g. 42")
        layout.addWidget(ap_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)

        def on_accept():
            text = vel_text.toPlainText().strip()
            if not text:
                QMessageBox.warning(dlg, "No data", "Please paste at least one velocity value.")
                return
            # parse values
            normalized = text.replace(',', ' ')
            tokens = [t for t in normalized.split() if t.strip()]
            vals = []
            for tok in tokens:
                try:
                    vals.append(float(tok))
                except Exception:
                    QMessageBox.warning(dlg, "Parse error", f"Could not parse token: {tok}")
                    return

            ap_id = None
            ap_text = ap_input.text().strip()
            if ap_text:
                try:
                    ap_id = int(ap_text)
                except Exception:
                    QMessageBox.warning(dlg, "Parse error", "Ammo Profile ID must be an integer")
                    return

            # persist
            try:
                from src.utils.chronograph_import import import_velocities

                res = import_velocities(self.db, vals, ap_id, note="Manual entry via UI")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save velocities: {e}")
                dlg.reject()
                return

            stats = res.get('stats', {})
            QMessageBox.information(self, "Saved", f"Saved {stats.get('count',0)} velocities. Avg: {stats.get('avg')}")
            dlg.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dlg.reject)

        dlg.setLayout(layout)
        dlg.exec()

    def on_refresh_chronograph_list(self):
        """Reload recent chronograph imports into the list widget"""
        cur = self.db.cursor
        cur.execute(
            "SELECT id, file_path, import_date, velocity_count, velocity_avg, velocity_es, velocity_sd FROM chronograph_imports ORDER BY import_date DESC LIMIT 50"
        )
        rows = cur.fetchall()
        self.chrono_list.clear()
        for r in rows:
            import_id = r[0]
            file_path = r[1] or "(manual)"
            date = r[2]
            count = r[3]
            avg = r[4]
            es = r[5]
            sd = r[6]
            text = f"#{import_id} {file_path} — {count} vel — avg {avg:.1f} fps — ES {es:.1f} — SD {sd:.1f}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, import_id)
            self.chrono_list.addItem(item)

    def on_chrono_selection_changed(self):
        """Plot velocities from the selected chronograph import into the velocity plot."""
        item = self.chrono_list.currentItem()
        if not item:
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute("SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,))
        row = cur.fetchone()
        if not row:
            return
        import json
        try:
            velocities = json.loads(row[0]) if row[0] else []
        except Exception:
            velocities = []

        if not velocities:
            QMessageBox.information(self, "No velocities", "Selected import contains no velocity data.")
            return

        pg = getattr(self, "_pg", None)
        # If pyqtgraph is available and we have a plot widget, plot simulated curve and overlay import points
        if pg and hasattr(self, "velocity_plot") and isinstance(self.velocity_plot, pg.PlotWidget):
            try:
                self.velocity_plot.clear()
                # First draw simulated curve if present
                if hasattr(self, "_last_velocity_curve") and self._last_velocity_curve:
                    sim_x, sim_y = self._last_velocity_curve
                    self.velocity_plot.plot(sim_x, sim_y, pen=pg.mkPen(color="#27ae60", width=3), name='sim')

                # Plot import velocities as points (x = shot index)
                xs = list(range(1, len(velocities) + 1))
                self.velocity_plot.plot(xs, velocities, pen=pg.mkPen(color="#34495e", width=2), symbol='o', symbolBrush="#34495e")
            except Exception as e:
                QMessageBox.warning(self, "Plot error", f"Could not plot velocities: {e}")
        else:
            # Fallback: show summary text
            avg = sum(velocities) / len(velocities)
            es = max(velocities) - min(velocities)
            self.scope_comparison_label.setText(
                f"Imported {len(velocities)} velocities — Avg {avg:.1f} fps — ES {es:.1f} fps"
            )

    def on_attach_chronograph_to_profile(self):
        """Attach selected chronograph import to an ammo_profile (create minimal profile if needed)"""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No selection", "Select an import from the list first")
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)

        # If a current ammo selection exists (we created one when creating batch earlier), attach to it.
        # Otherwise create a minimal ammo_profile from current UI selections.
        cur = self.db.cursor
        cur.execute("SELECT ammo_profile_id FROM chronograph_imports WHERE id = ?", (import_id,))
        existing = cur.fetchone()
        if existing and existing[0]:
            QMessageBox.information(self, "Already attached", f"Import already attached to profile id {existing[0]}")
            return

        # Create minimal profile if we have component selections
        if self.rifle_data and self.bullet_data and self.powder_data:
            name = f"Profile from import {import_id}"
            cur.execute(
                "INSERT INTO ammo_profiles (name, rifle_id, caliber, bullet_id, bullet_weight, powder_id, powder_charge, primer_id, case_id, coal, cbto, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (
                    name,
                    self.rifle_data.get("id"),
                    self.rifle_data.get("caliber"),
                    self.bullet_data.get("id"),
                    float(self.bullet_data.get("weight", 0)),
                    self.powder_data.get("id"),
                    float(self.current_charge),
                    self.primer_data.get("id") if self.primer_data else None,
                    self.brass_data.get("id") if self.brass_data else None,
                    float(self.coal_mm),
                    float(self.cbto_mm),
                ),
            )
            self.db.conn.commit()
            ammo_profile_id = cur.lastrowid
        else:
            # Prompt for profile id
            ap_id, ok = QInputDialog.getInt(self, "Ammo Profile ID", "Enter existing Ammo Profile ID to attach to:")
            if not ok:
                return
            ammo_profile_id = ap_id

        # Update import row
        cur.execute("UPDATE chronograph_imports SET ammo_profile_id = ? WHERE id = ?", (ammo_profile_id, import_id))
        self.db.conn.commit()
        QMessageBox.information(self, "Attached", f"Import #{import_id} attached to profile {ammo_profile_id}")
        self.on_refresh_chronograph_list()

    def on_save_chronograph_to_test_results(self):
        """Save selected chronograph import statistics into `test_results` linked to a profile or batch."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No selection", "Select an import from the list first")
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute("SELECT velocities_json, ammo_profile_id FROM chronograph_imports WHERE id = ?", (import_id,))
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json
        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(self, "No velocities", "Selected import has no velocities")
            return

        # Determine ammo_profile to attach results
        ap_id = row[1]
        if not ap_id:
            # try to use currently selected ammo/profile in UI if exists (we created one earlier when creating batch)
            # For simplicity, prompt user for an ammo_profile id
            ap_id, ok = QInputDialog.getInt(self, "Ammo Profile ID", "Enter Ammo Profile ID to associate test results with:")
            if not ok:
                return

        # Compute stats
        avg = sum(velocities) / len(velocities)
        es = max(velocities) - min(velocities)
        sd = (statistics.stdev(velocities) if len(velocities) > 1 else 0.0)

        # Insert into test_results: put first up to 3 velocities into velocity_1..3
        v1 = velocities[0] if len(velocities) > 0 else None
        v2 = velocities[1] if len(velocities) > 1 else None
        v3 = velocities[2] if len(velocities) > 2 else None

        cur.execute(
            "INSERT INTO test_results (ladder_test_id, charge_weight, velocity_1, velocity_2, velocity_3, velocity_avg, velocity_es, velocity_sd, image_path, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None,
                None,
                v1,
                v2,
                v3,
                float(avg),
                float(es),
                float(sd),
                None,
                f"Imported from chronograph_imports #{import_id}, linked to ammo_profile {ap_id}",
            ),
        )
        self.db.conn.commit()
        inserted_id = cur.lastrowid
        QMessageBox.information(self, "Saved", f"Saved test_results id {inserted_id} (avg {avg:.1f} fps, ES {es:.1f})")

    def on_analyze_and_suggest(self):
        """Analyze selected import (or current test results) and show recommendations."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No selection", "Select an import from the list first")
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute("SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,))
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json
        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(self, "No velocities", "Selected import has no velocities")
            return

        # Compute stats
        import statistics as _st
        avg = _st.mean(velocities)
        es = max(velocities) - min(velocities)
        sd = _st.stdev(velocities) if len(velocities) > 1 else 0.0

        from src.utils.recommender import suggest_adjustments

        stats = {"count": len(velocities), "avg": avg, "es": es, "sd": sd}
        suggestions = suggest_adjustments(stats, self.current_charge, self.coal_mm, self.cbto_mm)

        # Show suggestions in dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Analysis & Suggestions")
        layout = QVBoxLayout()
        for s in suggestions:
            layout.addWidget(QLabel(s))

        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec()

    def on_attach_chrono_to_qc_batch(self):
        """Attach selected chronograph import by creating or using existing qc_batch and insert qc_measurements."""
        item = self.chrono_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No selection", "Select an import from the list first")
            return
        import_id = item.data(Qt.ItemDataRole.UserRole)
        cur = self.db.cursor
        cur.execute("SELECT velocities_json FROM chronograph_imports WHERE id = ?", (import_id,))
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Not found", "Import row not found in DB")
            return
        import json
        velocities = json.loads(row[0]) if row[0] else []
        if not velocities:
            QMessageBox.warning(self, "No velocities", "Selected import has no velocities")
            return

        # Ask user to either enter existing qc_batch id or create new
        batch_id, ok = QInputDialog.getInt(self, "QC Batch ID", "Enter existing QC batch ID to attach to (or 0 to create new):", 0)
        if not ok:
            return

        if batch_id == 0:
            # create new qc batch
            name, ok2 = QInputDialog.getText(self, "New QC Batch", "Name for new QC batch:")
            if not ok2 or not name:
                QMessageBox.warning(self, "Cancelled", "Batch creation cancelled")
                return
            batch_size, ok3 = QInputDialog.getInt(self, "Batch Size", "How many rounds in batch?", len(velocities), 1)
            if not ok3:
                return
            cur.execute(
                "INSERT INTO qc_batches (name, target_charge, charge_tolerance, target_coal, coal_tolerance, batch_size, status) VALUES (?, ?, ?, ?, ?, ?, 'in_progress')",
                (name, None, None, None, None, batch_size),
            )
            batch_id = cur.lastrowid
            self.db.conn.commit()

        # Insert measurements
        for i, v in enumerate(velocities, start=1):
            cur.execute(
                "INSERT INTO qc_measurements (batch_id, patron_number, measurement_type, value, target_value, delta, is_outlier, notes) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                (batch_id, i, 'velocity', float(v), None, None, f"Imported from chronograph_imports #{import_id}"),
            )

        # Optionally mark batch completed if we've inserted >= batch_size
        cur.execute("SELECT batch_size FROM qc_batches WHERE id = ?", (batch_id,))
        b = cur.fetchone()
        if b and b[0] and int(b[0]) <= len(velocities):
            cur.execute("UPDATE qc_batches SET status = 'completed', completed_date = datetime('now') WHERE id = ?", (batch_id,))

        self.db.conn.commit()
        QMessageBox.information(self, "QC Batch Updated", f"Inserted {len(velocities)} measurements into QC batch {batch_id}")
        self.on_refresh_chronograph_list()

    def toggle_chat(self):
        """Toggle chat panel visibility"""
        if self.chat_display.isVisible():
            self.chat_display.hide()
            self.chat_input.hide()
            self.collapse_btn.setText("▶ Expand")
            self.chat_widget.setMaximumHeight(50)
        else:
            self.chat_display.show()
            self.chat_input.show()
            self.collapse_btn.setText("▼ Collapse")
            self.chat_widget.setMaximumHeight(300)

    def send_chat_message(self):
        """Send message to AI"""
        message = self.chat_input.text().strip()
        if not message:
            return

        # Display user message
        self.add_user_message(message)
        self.chat_input.clear()

        # Get AI response (placeholder - will integrate real AI later)
        response = self.get_ai_response(message)
        self.add_ai_message(response)

    def add_user_message(self, message):
        """Add user message to chat"""
        self.chat_display.append(
            f"<div style='text-align: right; margin: 10px;'>"
            f"<b style='color: #3498db;'>You:</b> {message}"
            f"</div>"
        )
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def add_ai_message(self, message):
        """Add AI message to chat"""
        self.chat_display.append(
            f"<div style='margin: 10px;'>"
            f"<b style='color: #9b59b6;'>🤖 AI:</b> {message}"
            f"</div>"
        )
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def get_ai_response(self, message):
        """
        Comprehensive AI reloading assistant - your expert friend!
        Answers ALL questions about reloading process
        """
        message_lower = message.lower()

        # ==================== KRUTT / POWDER ====================
        if any(word in message_lower for word in ["krutt", "powder", "pulver"]):
            if any(
                word in message_lower
                for word in ["anbefal", "recommend", "best", "hvilken"]
            ):
                return self.get_powder_recommendation_text()
            elif any(
                word in message_lower
                for word in ["mengde", "charge", "hvor mye", "how much"]
            ):
                return self.explain_charge_weight()
            elif any(
                word in message_lower for word in ["temperatur", "temperature", "temp"]
            ):
                return self.explain_powder_temperature()
            elif any(
                word in message_lower
                for word in ["brennhastighet", "burn rate", "speed"]
            ):
                return self.explain_burn_rate()
            elif any(
                word in message_lower for word in ["lagring", "storage", "oppbevaring"]
            ):
                return self.explain_powder_storage()

        # ==================== KULER / BULLETS ====================
        elif any(word in message_lower for word in ["kule", "bullet", "prosjektil"]):
            if any(
                word in message_lower
                for word in ["seating", "sette", "dybde", "depth", "cbto", "coal"]
            ):
                return self.explain_seating_depth()
            elif any(
                word in message_lower for word in ["jump", "hopp", "lands", "rifling"]
            ):
                return self.explain_bullet_jump()
            elif any(
                word in message_lower
                for word in ["vekt", "weight", "tung", "lett", "heavy", "light"]
            ):
                return self.explain_bullet_weight()
            elif any(
                word in message_lower for word in ["bc", "ballistisk", "ballistic"]
            ):
                return self.explain_bc()

        # ==================== TENNHETTER / PRIMERS ====================
        elif any(word in message_lower for word in ["tennhette", "primer", "tenner"]):
            if any(
                word in message_lower
                for word in ["anbefal", "recommend", "hvilken", "best"]
            ):
                return self.get_primer_recommendation()
            elif any(
                word in message_lower
                for word in ["magnum", "standard", "forskjell", "difference"]
            ):
                return self.explain_primer_types()
            elif any(
                word in message_lower
                for word in ["feil", "problem", "pierced", "cratered"]
            ):
                return self.diagnose_primer_problems()

        # ==================== HYLSER / BRASS ====================
        elif any(word in message_lower for word in ["hylse", "brass", "case"]):
            if any(
                word in message_lower for word in ["trim", "trimme", "lengde", "length"]
            ):
                return self.explain_brass_trimming()
            elif any(word in message_lower for word in ["neck", "hals", "tension"]):
                return self.explain_neck_tension()
            elif any(word in message_lower for word in ["anneal", "gløde", "hardhet"]):
                return self.explain_annealing()
            elif any(
                word in message_lower for word in ["prep", "preparer", "forbered"]
            ):
                return self.explain_brass_prep()
            elif any(
                word in message_lower for word in ["ganger", "times", "bruk", "levetid"]
            ):
                return self.explain_brass_life()

        # ==================== DIER / DIES ====================
        elif any(word in message_lower for word in ["die", "dier", "dies"]):
            if any(
                word in message_lower
                for word in ["innstilling", "setup", "justere", "adjust"]
            ):
                return self.explain_die_setup()
            elif any(
                word in message_lower
                for word in ["full length", "fl", "neck", "sizing"]
            ):
                return self.explain_sizing_dies()
            elif any(word in message_lower for word in ["seating", "sette", "bullet"]):
                return self.explain_seating_die()
            elif any(word in message_lower for word in ["crimping", "crimpe", "crimp"]):
                return self.explain_crimping()
            elif any(
                word in message_lower for word in ["problem", "stuck", "fast", "feil"]
            ):
                return self.diagnose_die_problems()

        # ==================== TRYKK / PRESSURE ====================
        elif any(word in message_lower for word in ["trykk", "pressure", "psi", "bar"]):
            if any(
                word in message_lower for word in ["høy", "high", "for mye", "too much"]
            ):
                return self.explain_high_pressure()
            elif any(word in message_lower for word in ["tegn", "signs", "symptom"]):
                return self.explain_pressure_signs()
            elif any(
                word in message_lower for word in ["saami", "max", "grense", "limit"]
            ):
                return self.explain_saami_limits()
            elif any(word in message_lower for word in ["hvorfor", "why", "årsak"]):
                return self.explain_pressure()

        # ==================== SIKKERHET / SAFETY ====================
        elif any(
            word in message_lower
            for word in ["sikker", "safe", "trygg", "farlig", "danger"]
        ):
            return self.check_safety_comprehensive()

        # ==================== PRESISJON / ACCURACY ====================
        elif any(
            word in message_lower
            for word in ["presisjon", "accuracy", "nøyaktighet", "gruppe", "group"]
        ):
            if any(
                word in message_lower
                for word in ["forbedre", "improve", "bedre", "better"]
            ):
                return self.improve_accuracy_tips()
            elif any(word in message_lower for word in ["ocw", "ladder", "test"]):
                return self.suggest_test_plan()
            elif any(
                word in message_lower for word in ["es", "sd", "spredning", "spread"]
            ):
                return self.explain_es_sd()

        # ==================== TESTING ====================
        elif any(
            word in message_lower for word in ["test", "ocw", "ladder", "sighter"]
        ):
            return self.suggest_test_plan()

        # ==================== LØP / BARREL ====================
        elif any(word in message_lower for word in ["løp", "barrel", "pipe"]):
            if any(
                word in message_lower for word in ["harmonisk", "harmonic", "vibration"]
            ):
                return self.explain_barrel_harmonics()
            elif any(
                word in message_lower for word in ["lengde", "length", "kort", "lang"]
            ):
                return self.explain_barrel_length()
            elif any(
                word in message_lower for word in ["rengjøring", "cleaning", "fouling"]
            ):
                return self.explain_barrel_cleaning()

        # ==================== VERKTØY / TOOLS ====================
        elif any(
            word in message_lower for word in ["verktøy", "tool", "utstyr", "equipment"]
        ):
            return self.recommend_tools()

        # ==================== PROSESS / PROCESS ====================
        elif any(
            word in message_lower
            for word in ["prosess", "process", "hvordan", "how to", "steg", "step"]
        ):
            return self.explain_reloading_process()

        # ==================== GENERELL HJELP ====================
        else:
            return self.general_help_message()

    def get_powder_recommendation_text(self):
        """Generate powder recommendation"""
        if not self.rifle_data:
            return "Please select a rifle first!"

        caliber = self.rifle_data["caliber"]

        recommendations = {
            ".308 Winchester": "For .308 Win, I recommend:\n\n🥇 Varget (burn rate 115) - Temperature stable, excellent accuracy\n🥈 H4350 - Slightly slower, also great\n🥉 RL15 - Faster, good for shorter barrels",
            "6.5 Creedmoor": "For 6.5 Creedmoor, I recommend:\n\n🥇 H4350 - THE standard for 6.5 CM\n🥈 RL16 - Temp stable, higher velocity\n🥉 Varget - Works great with lighter bullets",
            ".223 Remington": "For .223 Rem, I recommend:\n\n🥇 Varget - Excellent accuracy\n🥈 H4895 - Very versatile\n🥉 RL15 - Good velocities",
        }

        return recommendations.get(
            caliber, f"For {caliber}, consult load manuals for powder recommendations."
        )

    def get_primer_recommendation(self):
        """Get primer recommendation"""
        if not self.powder_data:
            return "Select a powder first, then I can recommend a primer!"

        return (
            "For your powder choice:\n\n"
            "🥇 CCI BR-2 - Benchrest grade, lowest ES/SD\n"
            "🥈 Federal 210M - Match grade, excellent\n"
            "🥉 CCI 200 - Standard LR, works great\n\n"
            "Avoid magnum primers unless using slow ball powder."
        )

    def explain_pressure(self):
        """Explain current pressure"""
        # Would use actual calculation here
        return (
            "Pressure is influenced by:\n\n"
            "1. Charge weight (more powder = higher pressure)\n"
            "2. Case capacity (less space = higher pressure)\n"
            "3. Seating depth (closer to lands = higher pressure)\n"
            "4. Powder burn rate (faster = higher peak)\n"
            "5. Temperature (hotter = higher pressure)\n\n"
            "Always stay under SAAMI/CIP max!"
        )

    def check_safety(self):
        """Check if current load is safe"""
        # Would use actual calculation here
        return (
            "Based on current settings:\n\n"
            "✅ Pressure looks SAFE\n"
            "✅ Under SAAMI maximum\n"
            "⚠️ Always watch for pressure signs!\n\n"
            "Signs of high pressure:\n"
            "• Flattened primers\n"
            "• Ejector marks on brass\n"
            "• Difficult bolt lift\n"
            "• Case head expansion"
        )

    def suggest_test_plan(self):
        """Suggest OCW test plan"""
        return (
            "I recommend this test protocol:\n\n"
            "📋 OCW Test (15 rounds):\n"
            "• 42.0gr × 3 shots\n"
            "• 42.3gr × 3 shots\n"
            "• 42.5gr × 3 shots ← Expected best\n"
            "• 42.8gr × 3 shots\n"
            "• 43.0gr × 3 shots\n\n"
            "Shoot at 100m, look for cluster (OCW node).\n"
            "Then test seating depth (9 rounds).\n\n"
            "Total: 24 rounds vs traditional 60-100!"
        )

    def go_back_to_step1(self):
        """Go back to step 1"""
        self.step2_widget.hide()
        self.layout().removeWidget(self.step2_widget)
        self.step1_widget.show()

    def initialize_step2(self):
        """Initialize step 2 with rifle data"""
        # Load components for this rifle
        self.load_bullets_for_caliber()
        self.load_powders()
        self.load_primers()

        # Show rifle info
        self.add_ai_message(
            f"Great! You selected {self.rifle_data['name']} ({self.rifle_data['caliber']}).\n\n"
            f"Let me help you build the perfect load! 🎯"
        )

    def load_bullets_for_caliber(self):
        """Load bullets for rifle caliber"""
        # Placeholder - would query from database
        self.bullet_combo.clear()
        self.bullet_combo.addItem("Select bullet...", None)
        # Add dummy data for now
        self.bullet_combo.addItem(
            "Berger 175gr OTM (Lot ABC123)", {"id": 1, "weight": 175}
        )
        self.bullet_combo.addItem(
            "Sierra 168gr HPBT (Lot XYZ456)", {"id": 2, "weight": 168}
        )

    def load_powders(self):
        """Load powders from inventory"""
        powders = self.db.execute_query("SELECT * FROM powder WHERE quantity_grams > 0")
        self.powder_combo.clear()
        self.powder_combo.addItem("Select powder...", None)
        for powder in powders:
            self.powder_combo.addItem(
                f"{powder['manufacturer']} {powder['name']}", powder
            )

    def load_primers(self):
        """Load primers from inventory"""
        primers = self.db.execute_query("SELECT * FROM primers WHERE quantity > 0")
        self.primer_combo.clear()
        self.primer_combo.addItem("Select primer...", None)
        for primer in primers:
            self.primer_combo.addItem(
                f"{primer['manufacturer']} {primer['name']}", primer
            )

    def on_bullet_changed(self, index):
        """Handle bullet selection"""
        bullet = self.bullet_combo.currentData()
        if bullet:
            self.bullet_data = bullet
            self.bullet_info.setText(f"Weight: {bullet.get('weight', '?')}gr")
            self.update_visualization()

    def on_powder_changed(self, index):
        """Handle powder selection"""
        powder = self.powder_combo.currentData()
        if powder:
            self.powder_data = powder
            self.powder_info.setText(
                f"Type: {powder.get('type', '?')}, In stock: {powder.get('quantity_grams', 0):.0f}g"
            )

            # Show AI recommendation
            self.powder_recommendation.setText(
                f"🤖 AI: {powder['name']} is a great choice! "
                f"Burn rate: {powder.get('burn_rate', '?')}"
            )
            self.update_visualization()

    def on_charge_slider_changed(self, value):
        """Handle charge slider change"""
        self.current_charge = value / 10.0
        self.charge_label.setText(f"{self.current_charge:.1f} gr")
        self.update_visualization()

    def on_seating_changed(self):
        """Handle seating depth change"""
        self.coal_mm = self.coal_spin.value()
        self.cbto_mm = self.cbto_spin.value()

        # Calculate jump if jam length known
        if self.rifle_data and self.rifle_data.get("jam_length_cbto_mm"):
            jam = self.rifle_data["jam_length_cbto_mm"]
            jump = jam - self.cbto_mm
            self.jump_label.setText(f'Jump: {jump:.2f}mm ({jump/25.4:.3f}")')

        self.update_visualization()

    def update_visualization(self):
        """Update graphs with current parameters"""
        if not all([self.rifle_data, self.bullet_data, self.powder_data]):
            return

        # Calculate ballistics
        result = self.engine.calculate_load(
            self.rifle_data["id"],
            self.bullet_data["id"],
            self.powder_data["id"],
            self.current_charge,
            self.coal_mm,
            self.cbto_mm,
        )

        if "error" in result:
            return

        # Update graphs
        self.update_pressure_graph(result)
        self.update_velocity_graph(result)
        self.update_stats(result)

    def update_pressure_graph(self, result):
        """Update pressure curve"""
        self.pressure_plot.clear()

        times = [p[0] for p in result["pressure_curve"]]
        pressures = [p[1] for p in result["pressure_curve"]]

        pg = getattr(self, "_pg", None)
        if not pg:
            return

        self.pressure_plot.plot(
            times, pressures, pen=pg.mkPen(color="#e74c3c", width=3)
        )

        # Add SAAMI line
        max_pressure = result["max_pressure_psi"]
        self.pressure_plot.addLine(
            y=max_pressure,
            pen=pg.mkPen(color="#95a5a6", width=2, style=Qt.PenStyle.DashLine),
        )

    def update_velocity_graph(self, result):
        """Update velocity curve"""
        self.velocity_plot.clear()

        positions = [v[0] for v in result["velocity_curve"]]
        velocities = [v[1] for v in result["velocity_curve"]]

        # Store latest simulated curve for overlaying with imports
        self._last_velocity_curve = (positions, velocities)

        pg = getattr(self, "_pg", None)
        if not pg:
            return

        self.velocity_plot.plot(positions, velocities, pen=pg.mkPen(color="#27ae60", width=3))

    def update_stats(self, result):
        """Update statistics display"""
        self.stat_pressure.setText(f"Pressure: {result['peak_pressure_psi']:.0f} PSI")
        self.stat_velocity.setText(f"Velocity: {result['muzzle_velocity_fps']:.0f} fps")
        self.stat_energy.setText(f"Energy: {result['energy_ft_lbs']:.0f} ft-lbs")
        self.stat_barrel_time.setText(f"Time: {result['barrel_time_ms']:.2f} ms")

        safety = result["safety_margin_percent"]
        color = "#27ae60" if safety > 15 else "#e67e22" if safety > 10 else "#e74c3c"
        emoji = "🟢" if safety > 15 else "🟠" if safety > 10 else "🔴"

        self.stat_safety.setText(f"{emoji} Safety: {safety:.1f}%")
        self.stat_safety.setStyleSheet(
            f"color: {color}; font-weight: bold; padding: 8px; font-size: 10pt;"
        )

        # Update scope comparison with previous load
        self.update_scope_comparison(result)

    def update_scope_comparison(self, current_result):
        """Update scope adjustment comparison with previous load for same rifle"""
        if not self.rifle_data or not self.bullet_data or not self.powder_data:
            self.scope_comparison_group.setVisible(False)
            return

        rifle_id = self.rifle_data["id"]
        current_velocity = current_result.get("muzzle_velocity_fps", 0)
        current_bc = self.bullet_data.get("bc_g1", 0)

        if not current_velocity or not current_bc:
            self.scope_comparison_group.setVisible(False)
            return

        # Find PREVIOUS load for same rifle (most recent ammo_profile)
        previous_load = self.db.execute_query(
            """
            SELECT name, velocity_fps, bc_g1, bullet_weight, caliber, created_date
            FROM ammo_profiles
            WHERE rifle_id = ? AND velocity_fps IS NOT NULL AND bc_g1 IS NOT NULL
            ORDER BY created_date DESC
            LIMIT 1
        """,
            (rifle_id,),
        )

        if not previous_load:
            self.scope_comparison_label.setText(
                f"<b>NY LADNING:</b> {self.rifle_data['name']}<br>"
                f"<i>Dette er første ladning for denne riflen. Ingen sammenligning tilgjengelig.</i>"
            )
            self.scope_comparison_group.setVisible(True)
            return

        prev_name, prev_vel, prev_bc, prev_weight, prev_cal, prev_created = (
            previous_load[0]
        )

        # Calculate drop at 100m, 300m, 600m (using utils ballistics calculator)
        from src.utils.ballistics import BallisticsCalculator

        ballistics_calc = BallisticsCalculator()

        zero_dist = 100  # Standard zero
        test_distances = [100, 300, 600]

        # Create comparison table
        comparison_html = f"""
        <b>NY LADNING:</b> {self.rifle_data['name']} - {self.bullet_data.get('name', 'Custom')} {self.bullet_data.get('weight_grains', 0)}gr<br>
        • Hastighet: {current_velocity:.0f} fps, BC (G1): {current_bc:.3f}, Krutt: {self.powder_data.get('name', 'Unknown')} ({self.current_charge:.1f}gr)<br><br>

        <b>FORRIGE LADNING:</b> {prev_name}<br>
        • Hastighet: {prev_vel:.0f} fps, BC (G1): {prev_bc:.3f}, Kulevekt: {prev_weight}gr<br><br>

        <b>🎯 KIKKERT JUSTERING (Zero: {zero_dist}m):</b><br>
        <table style='width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 9pt;'>
        <tr style='background-color: #f0f0f0; font-weight: bold;'>
            <td style='padding: 3px; border: 1px solid #ddd;'>Dist</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Drop Ny</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Drop Forrige</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Δ</td>
            <td style='padding: 3px; border: 1px solid #ddd;'>Justering</td>
        </tr>
        """

        for dist in test_distances:
            # Drop for new load
            drop_new = ballistics_calc.calculate_drop(
                current_velocity, current_bc, dist, zero_dist, "G1"
            )
            drop_new_moa = ballistics_calc.cm_to_moa(drop_new, dist)

            # Drop for previous load
            drop_prev = ballistics_calc.calculate_drop(
                prev_vel, prev_bc, dist, zero_dist, "G1"
            )
            drop_prev_moa = ballistics_calc.cm_to_moa(drop_prev, dist)

            # Difference
            diff_cm = drop_new - drop_prev
            diff_moa = drop_new_moa - drop_prev_moa

            # Scope adjustment (0.25 MOA/click standard)
            clicks = diff_moa / 0.25
            direction = "↑" if clicks > 0 else "↓" if clicks < 0 else "="

            color = (
                "#27ae60"
                if abs(diff_cm) < 5
                else "#f39c12" if abs(diff_cm) < 15 else "#e74c3c"
            )

            comparison_html += f"""
            <tr>
                <td style='padding: 3px; border: 1px solid #ddd;'>{dist}m</td>
                <td style='padding: 3px; border: 1px solid #ddd;'>{drop_new:.0f}cm ({drop_new_moa:.1f} MOA)</td>
                <td style='padding: 3px; border: 1px solid #ddd;'>{drop_prev:.0f}cm ({drop_prev_moa:.1f} MOA)</td>
                <td style='padding: 3px; border: 1px solid #ddd; background-color: {color}; color: white; font-weight: bold;'>{diff_cm:+.0f}cm</td>
                <td style='padding: 3px; border: 1px solid #ddd; font-weight: bold;'>{direction} {abs(clicks):.0f} clicks</td>
            </tr>
            """

        comparison_html += """
        </table><br>
        <i style='font-size: 8pt;'>💡 Grønn = &lt;5cm, Gul = 5-15cm, Rød = &gt;15cm. Standard: 0.25 MOA/click.</i>
        """

        self.scope_comparison_label.setText(comparison_html)
        self.scope_comparison_group.setVisible(True)

    # ========================================================================
    # COMPREHENSIVE AI HELPER METHODS - Your Reloading Expert Friend!
    # ========================================================================

    def general_help_message(self):
        """General help message showing all capabilities"""
        return """🤖 Hei! Jeg er din ladingsekspert og venn! Jeg kan hjelpe deg med ALT om lading:

📦 KOMPONENTER:
• Krutt: "Hvilket krutt passer best?" / "Hvordan lagre krutt?"
• Kuler: "Hvor dypt skal jeg sette kulen?" / "Hva er CBTO?"
• Tennhetter: "Standard eller magnum?" / "Hvorfor er tennhetten flat?"
• Hylser: "Når skal jeg trimme?" / "Hvordan gløde hylser?"

🔧 DIER & PROSESS:
• "Hvordan stille inn diene?" / "Full length eller neck sizing?"
• "Hylsen setter seg fast i die" / "Hvordan crimpe?"

📊 TEKNISK:
• Trykk: "Hvorfor er trykket høyt?" / "Hva er SAAMI-grenser?"
• Presisjon: "Hvordan forbedre nøyaktigheten?" / "Hva er ES/SD?"
• Testing: "Hvordan teste ladningen?" / "Hva er OCW?"

🎯 Spør meg hva som helst! Jeg er her for å hjelpe deg lage perfekte ladninger! 🎯"""

    # ==================== KRUTT / POWDER HELPERS ====================

    def explain_charge_weight(self):
        """Explain charge weight selection"""
        return """⚖️ KRUTT-MENGDE (Charge Weight):

🎯 HVORDAN VELGE:
1. Start med ladebok minimum (-10% av maks)
2. Øk gradvis i 0.3-0.5 grain steg
3. Se etter pressure-tegn konstant!

📊 FAKTORER:
• Større mengde = mer trykk + høyere hastighet
• For mye = FARLIG høyt trykk ⚠️
• For lite = dårlig forbrenning, inconsistent

🎯 OCW METODE (anbefalt):
• Test 5 nivåer: 42.0, 42.3, 42.5, 42.8, 43.0gr
• Se etter "node" (stabil sone)
• Velg midt i noden for best konsistens

⚠️ SIKKERHET:
• Aldri overstig ladebok maksimum!
• Se etter pressure-tegn ved hvert steg
• Når i tvil → gå NED i mengde"""

    def explain_powder_temperature(self):
        """Explain powder temperature sensitivity"""
        return """🌡️ KRUTT & TEMPERATUR:

📊 TEMPERATUR-SENSITIVITET:
• Varmere = høyere trykk (ca 1-3 fps per °C)
• Kaldere = lavere trykk og hastighet

🥇 TEMP-STABILE KRUTT (anbefalt):
• Hodgdon Varget (ekstremt stabilt)
• Alliant RL16 (meget bra)
• Hodgdon H4350 (god stabilitet)
• Vihtavuori N140-serien

⚠️ TEMP-SENSITIVE:
• IMR serien (spesielt eldre typer)
• Ball powder (generelt mer sensitive)

🎯 TESTING:
• Test ladningen ved forskjellige temperaturer
• Lagre krutt i tørr plass, 10-25°C
• Unngå direkte sollys på ammunisjon

💡 TIP: Hvis du jakter i varmt OG kaldt vær, velg temp-stabilt krutt!"""

    def explain_burn_rate(self):
        """Explain powder burn rate"""
        return (
            """🔥 BRENNHASTIGHET (Burn Rate):

📊 HVA ER DET?
Hvor raskt kruttet brenner inne i kammeret.

⚡ RASKT KRUTT (t.ex. Viht N130):
• Små kalibre (.223, .22-250)
• Lette kuler
• Korte løp
• Høyere trykk, raskere

🐌 LANGSOMT KRUTT (t.ex. H4831):
• Store kalibre (.300 Win Mag)
• Tunge kuler
• Lange løp
• Lavere trykk, mer kontrollert

🎯 FOR DIN {caliber}:
"""
            + (
                "• Brennhastighet 110-120 (medium)\n• Varget (115) = perfekt!\n• H4350 (120) = også bra"
                if hasattr(self, "rifle_data")
                and self.rifle_data
                and ".308" in self.rifle_data.get("caliber", "")
                else "• Velg våpen først for spesifikke anbefalinger"
            )
            + """

⚠️ FEIL KRUTT:
• For raskt → farlig høyt trykk! 💥
• For langsomt → urent, dårlig forbrenning

💡 TIP: Følg ladebøker! De vet hvilket krutt som passer."""
        )

    def explain_powder_storage(self):
        """Explain powder storage"""
        return """📦 KRUTT-LAGRING:

✅ RIKTIG LAGRING:
• Original beholder (ALDRI overføre!)
• Tørt, kjølig sted (10-25°C)
• Unngå sollys og fukt
• Ventilert skap/rom
• Låst, vekk fra barn

⚠️ ALDRI:
• Blande forskjellige krutt-typer
• Lagre ved varme (>30°C)
• Lagre i fuktig miljø
• Eksponere for åpen ild

🔍 SJEKK FOR NEDBRYTNING:
• Rust-rød/brun farge = KAST!
• Sur lukt (som syre) = KAST!
• Klumpete = fuktskade, KAST!
• Godt krutt: tørt, løst, jevn farge

⏳ HOLDBARHET:
• Riktig lagret: 10-20+ år
• Åpnet beholder: 5-10 år (hvis tett lukket)
• Sjekk årlig for tegn på nedbrytning

💡 TIP: Skriv åpningsdato på beholderen!"""

    # ==================== KULER / BULLETS HELPERS ====================

    def explain_seating_depth(self):
        """Explain bullet seating depth"""
        return """📏 KULESETTING (Seating Depth):

📊 VIKTIGE MÅL:
• COAL (Cartridge Overall Length) = Total lengde
• CBTO (Cartridge Base to Ogive) = Mer presist!
• Jump = Avstand fra kule til rifling

🎯 BERGER METODE (anbefalt):
1. Start ved "jam" (kule mot rifling)
2. Test: 0.010", 0.050", 0.090", 0.130" jump
3. Skyt 3-skudd grupper av hver
4. Velg den beste gruppen

📈 EFFEKTER:
• Nær rifling (kort jump):
  ✅ Høyere presisjon (ofte)
  ⚠️ Høyere trykk!
• Lengre jump:
  ✅ Lavere trykk
  ⚠️ Kan gi dårligere presisjon

⚠️ SIKKERHET:
• Kortere COAL = MER trykk
• Start konservativt (0.050" jump)
• Reduser krutt-mengde hvis du går nærmere rifling

💡 TIP: CBTO er mer konsistent enn COAL (kuletips varierer)"""

    def explain_bullet_jump(self):
        """Explain bullet jump to lands"""
        return """🦘 BULLET JUMP:

📊 HVA ER DET?
Avstanden kulen reiser før den treffer riflingen (lands).

📏 MÅLING:
1. Lås bolt på tom hylse med kule
2. Trykk kule mot rifling
3. Mål CBTO = "jam length"
4. Jump = jam length - din CBTO

🎯 TYPISKE VERDIER:
• 0.000" (jam) = kule mot rifling
  ⚠️ HØYT TRYKK! Kun for testing
• 0.010-0.020" = "touch lands"
  ⚡ Høy presisjon, moderat trykk
• 0.040-0.080" = sweet spot
  ✅ God presisjon, trygt trykk
• 0.100"+ = lang jump
  ✅ Trygt, kan funke bra

💡 HVER RIFLE ER FORSKJELLIG:
• Noen liker kort jump (0.010")
• Andre liker lang jump (0.080"+)
• Test for å finne DIN rifle sin preferanse!

🎯 MAGASIN-LENGDE:
Husk å sjekke at patronen passer i magasinet!"""

    def explain_bullet_weight(self):
        """Explain bullet weight selection"""
        return """⚖️ KULE-VEKT:

📊 LETTERE KULER (t.ex. 150gr .308):
✅ Høyere hastighet
✅ Flatere bane (kort hold)
✅ Mindre rekyl
⚠️ Mer vindpåvirkning
⚠️ Mindre energi på lang distanse

📊 TYNGRE KULER (t.ex. 175gr .308):
✅ Bedre BC (ballistic coefficient)
✅ Mindre vindpåvirkning
✅ Mer energi på distanse
✅ Bedre for long-range
⚠️ Lavere hastighet
⚠️ Mer rekyl

🎯 FOR DIN RIFLE:
• Løp-twist: raskere twist = tyngre kuler
• 1:12" twist = 150-168gr
• 1:10" twist = 168-185gr
• 1:8" twist = 175-200gr+

💡 TIP: Start med "standard" vekt for kaliberet:
• .308 Win → 168-175gr
• 6.5 CM → 140-147gr
• .223 Rem → 55-77gr"""

    def explain_bc(self):
        """Explain ballistic coefficient"""
        return """🎯 BALLISTISK KOEFFISIENT (BC):

📊 HVA ER DET?
Målet på hvor godt kulen "skjærer" gjennom luften.

📈 HØYERE BC = BEDRE:
✅ Mindre hastighetstap
✅ Flatere bane
✅ Mindre vindpåvirkning
✅ Mer energi på distanse

🔢 TYPISKE VERDIER (G1):
• 0.200-0.300 = Lavt (flat base, lett)
• 0.400-0.500 = Middels (HPBT)
• 0.500-0.600 = Godt (match kuler)
• 0.600+ = Utmerket (VLD, hybrid)

🎯 FAKTORER:
• Kule-form: VLD/Hybrid best
• Vekt: tyngre = høyere BC
• Diameter: mindre = bedre (6.5mm vs .308)

💡 VIKTIG:
• BC betyr lite under 300m
• Over 600m → stor forskjell!
• Velg basert på bruk:
  - Jakt <300m: BC mindre viktig
  - Long range >600m: høy BC kritisk"""

    # ==================== TENNHETTER / PRIMERS HELPERS ====================

    def explain_primer_types(self):
        """Explain primer types"""
        return (
            """🔥 TENNHETTE-TYPER:

📊 STANDARD vs MAGNUM:

✅ STANDARD (anbefalt):
• For de fleste krutt-typer
• Stick powder (Varget, H4350, etc)
• Lavere ES/SD (bedre konsistens)
• Eksempel: CCI 200, Federal 210, BR-2

⚡ MAGNUM:
• For langsomt ball powder
• Store magnum-kalibre
• Kompakte ladninger (mye krutt, lite plass)
• Eksempel: CCI 250, Federal 215

🎯 BENCHREST (best for presisjon):
• CCI BR-2 (Large Rifle)
• CCI BR-4 (Small Rifle)
• Federal 205M, 210M
• Tettere toleranser = bedre ES/SD

⚠️ IKKE BYTTESTENNHETTE UTEN Å TESTE!
• Forskjellige tennhetter = forskjellig trykk
• Magnum tennhette kan gi +2000-3000 PSI!
• Start lavere med krutt-mengde ved bytte

💡 TIP FOR DIN LADNING:
"""
            + (
                f"Med {self.powder_data['name']}: Standard tennhette anbefales\n\n"
                if hasattr(self, "powder_data") and self.powder_data
                else "Velg krutt først for spesifikk anbefaling\n\n"
            )
            + """🥇 MINE FAVORITTER:
• CCI BR-2: Best for presisjon
• Federal 210M: Også utmerket
• CCI 200: God standard-valg"""
        )

    def diagnose_primer_problems(self):
        """Diagnose primer-related issues"""
        return """🔍 TENNHETTE-PROBLEMER:

⚠️ FLATTENED PRIMER (flat tennhette):
• Normal: Litt flat er OK
• For flat: TRYKKET FOR HØYT! 🚨
• Løsning: Reduser krutt-mengde

🕳️ PIERCED PRIMER (hull i tennhette):
• Årsak 1: Alt for høyt trykk 🚨
• Årsak 2: For stor firing pin hole
• Årsak 3: Svak tennhette + høyt trykk
• Løsning: Sjekk rifle, reduser krutt

🌙 CRATERED PRIMER (krater rundt slag):
• Normal i mange rifles (spesielt Remington)
• Hvis ny: kan bety høyt trykk
• Kombinert med andre tegn = STOPP

💥 BLOWN PRIMER (tennhette falt ut):
• FARLIG HØYT TRYKK! 🚨🚨
• STOPP UMIDDELBART
• Sjekk rifle hos børsemaker
• Reduser krutt betydelig

🔄 TENNHETTE BAKLENGS:
• Skjer hvis tennhette ikke satt ordentlig
• Rifle kan kanskje ikke fyres (safety)
• Løsning: Sett tennhette med riktig dybde

✅ NORMAL TENNHETTE:
• Lett rundet fortsatt
• Tydelig slagmerke
• Ingen kratering eller spreading
• Sitter godt i primer pocket"""

    # ==================== HYLSER / BRASS HELPERS ====================

    def explain_brass_trimming(self):
        """Explain brass trimming"""
        return """✂️ HYLSE-TRIMMING:

📏 HVORFOR TRIMME?
Hylser strekker seg ved hver skyting. For lange hylser:
• Klemmer kule for hardt (høyt trykk)
• Kan ikke lukke bolt
• Kan gi chambering-problemer

📊 NÅR TRIMME?
1. Mål hylse-lengde etter sizing
2. Sammenlign med SAAMI/CIP max
3. Trim når du nærmer deg max (0.5mm margin)

🎯 FREKVENS:
• .308 Win: hvert 3-5 skudd (strekker lite)
• .223 Rem: hvert 2-3 skudd (strekker mer)
• Avhenger av ladning (høyere trykk = mer strekk)

🔧 VERKTØY:
• Manuell trimmer: Lee, Lyman
• Power trimmer: Giraud (best, dyrest)
• WFT: World's Finest Trimmer (rask)

📐 TRIM LENGTH:
• SAAMI max: 2.015" (.308)
• Trim to: 2.005-2.008"
• Trim alle likt for konsistens!

💡 TIPS:
• Chamfer og deburr etter trimming
• Trim i batch for konsistens
• Mål noen få, trim alle"""

    def explain_neck_tension(self):
        """Explain neck tension"""
        return """🤏 HALS-TENSION (Neck Tension):

📊 HVA ER DET?
Hvor hardt hylse-halsen klemmer rundt kulen.

🎯 MÅLING:
• Forskjell mellom hals ID og kule-diameter
• Typisk: 0.002-0.004" (0.05-0.10mm)
• Måles med bullet comparator

📈 EFFEKTER:

FOR LITE TENSION (0.001"):
⚠️ Kule kan flytte seg i magasin
⚠️ Inconsistent ignition
⚠️ Dårlig ES/SD

NORMALT (0.002-0.003"):
✅ God konsistens
✅ Trygt for magasin
✅ God presisjon

FOR MYE TENSION (0.005"+):
⚠️ Høyere start-trykk
⚠️ Kan deformere kule
⚠️ Kan gi dårligere presisjon

🔧 JUSTERING:
• Bruk bushing sizing die
• Velg bushing: kule Ø + 0.002"
• Eksempel: .308 kule + 0.002" = .310" bushing

💡 TIP:
• 0.002" er "safe default"
• Test 0.001", 0.002", 0.003" for din rifle
• Konsistens viktigere enn eksakt verdi!"""

    def explain_annealing(self):
        """Explain brass annealing"""
        return """🔥 HYLSE-GLØDNING (Annealing):

📊 HVA ER DET?
Varmebehandling for å gjenopprette hylse-hals mykhet.

🔬 HVORFOR?
• Hylser hardner ved sizing (work hardening)
• Hard hals = inkonsistent neck tension
• Hard hals = kan sprekke
• Glødning = gjenoppretter mykhet

⏱️ NÅR GJØRE DET?
• Presisjonsskytere: hver 3-5 skudd
• Jegere: hver 5-10 skudd
• Eller når halsen føles stiv ved sizing

🔧 VERKTØY:
• Annealeez (propan) - $200
• AMP Annealer (elektrisk) - $1500+ (best)
• DIY: Drill + socket + propan (risikabelt)

🎯 PROSESS:
1. Varme hals til 350-400°C (2-3 sek)
2. KUN halsen - ikke hele hylsen!
3. Kjøl i vann (valgfritt)
4. For varm = for myk (farlig)
5. For kald = ikke effekt

⚠️ ADVARSEL:
• IKKE overheat hylse-base (farlig!)
• Bruk timer (konsistens)
• Templaq/Tempilaq varmemarker anbefales

💡 TIP:
• Ikke nødvendig for nybegynnere
• Start når du har erfaring
• Merkbar forskjell i ES/SD!"""

    def explain_brass_prep(self):
        """Explain brass preparation"""
        return """🔧 HYLSE-PREPARERING:

📋 FULL PREP (konkurranseskytere):
1. ✅ Clean (ultrasonic/tumbler)
2. ✅ Lube for sizing
3. ✅ Full length resize
4. ✅ Measure length, trim if needed
5. ✅ Chamfer & deburr
6. ✅ Uniform primer pocket
7. ✅ Deburr flash hole
8. ✅ Annealing (hver 3-5x)
9. ✅ Sort by weight (optional)

📋 BASIC PREP (jegere/plinkers):
1. ✅ Clean
2. ✅ Resize (neck eller FL)
3. ✅ Check length, trim if needed
4. ✅ Chamfer & deburr
5. ✅ Prime, charge, seat

🎯 VIKTIGE STEG:
• Chamfer: Gjør at kule setter seg rett
• Deburr: Fjerner skarpe kanter
• Uniform primer pocket: Bedre konsistens
• Flash hole deburr: Bedre ignition

⏱️ TID:
• Full prep: 5-10 min per hylse
• Basic: 1-2 min per hylse

💡 TIP FOR NYBEGYNNERE:
Start basic, legg til steg etter hvert!
• Chamfer/deburr: ALLTID
• Primer pocket: Hvis du vil bedre presisjon
• Flash hole: Kun for konkurranser"""

    def explain_brass_life(self):
        """Explain brass lifespan"""
        return """♻️ HYLSE-LEVETID:

📊 FORVENTET ANTALL SKUDD:

JAKT-LADNINGER (moderate):
• 10-20+ skudd med god prep
• Lapua/Norma brass: 15-20+
• Winchester: 10-15
• Remington: 8-12

HOT LOADS (høyt trykk):
• 5-10 skudd
• Mer stress = kortere liv

MATCH LOADS (precision):
• Annealing: 15-20+ skudd
• Uten annealing: 8-12

⚠️ KAST HYLSEN HVIS:
• Sprekk i hals (vanligst)
• Sprekk ved base
• Løs primer pocket (primer faller ut)
• Separation line ved base
• Betydelig strekking (over trim length+)

🔍 INSPEKSJON:
• Sjekk for sprekk hver gang (visuelt)
• Sjekk case head for separation line
• Føl på primer pocket (skal være tight)

💰 KOSTNAD:
• Lapua brass: 15 kr/stk
• 15 skudd = 1 kr per skudd
• Lønner seg å ta vare på!

💡 TIP:
• Annealing DOBLER levetiden!
• Ikke full-length resize hver gang (neck only)
• Lapua/Norma varer lengst"""

    # ==================== DIER / DIES HELPERS ====================

    def explain_die_setup(self):
        """Explain die setup"""
        return """🔧 DIE-INNSTILLING:

📊 SIZING DIE (Full Length):
1. Clean rifle bolt lugs, chamber
2. Skru die ned til den rører shell holder
3. Skru 1/4 turn ekstra (cam-over)
4. Size en hylse
5. Test i rifle - bolt skal lukkes lett
6. Hvis ikke: skru die 1/8 turn nedover

📊 SIZING DIE (Neck Only):
1. Skru die ned til den nettopp rører hylse-hals
2. Size test-hylse
3. Hylsen skal fortsatt chambere lett
4. Justere bushing for 0.002-0.003" tension

📊 SEATING DIE:
1. Fjern punch, skru die helt ned
2. Skru opp til die nettopp rører hylse
3. Skru 1/8 turn ekstra
4. Juster punch for ønsket COAL/CBTO
5. Test flere hylser for konsistens

⚠️ TIPS:
• Lube hylser ALLTID (sizing)
• ALDRI lube inside hals (kan gi trykk-spike)
• Cam-over gir konsistens
• Test flere hylser før fullskala

💡 VERKTØY:
• Hornady Comparator: Mål CBTO
• Caliper: Mål COAL
• Micrometer seating stem: Best presisjon"""

    def explain_sizing_dies(self):
        """Explain sizing die types"""
        return """📏 SIZING DIE TYPER:

🔧 FULL LENGTH (FL):
✅ Resizer hele hylsen
✅ Sikrer chambering i alle rifles
✅ Nødvendig for semi-auto
⚠️ Mer brass-wear
• Bruk: Hver 3-5 skudd (bolt action)
• Bruk: Hver gang (semi-auto)

🔧 NECK SIZING ONLY:
✅ Kun resizer halsen
✅ Skånsomt for brass (lengre levetid)
✅ Bedre presisjon (minimal sizing)
⚠️ Hylsen "fire-forms" til DIN rifle
⚠️ Kan ikke brukes i andre rifles
• Bruk: Konkurranseskytere
• Bruk: Single rifle dedikert brass

🔧 BUSHING DIE:
✅ Justerbar neck tension
✅ Minimal sizing av hals
✅ Best for presisjon
💰 Dyrere ($100-200)
• Redding, Forster, Whidden

🔧 SMALL BASE DIE:
✅ Resizer MER enn standard FL
✅ For semi-auto rifles
✅ Sikrer pålitelig chambering
• Nødvendig for AR-platform

🎯 ANBEFALING:
• Nybegynner: Standard FL die
• Bolt action presisjon: Neck sizing
• Avansert: Bushing die
• Semi-auto: Small base die"""

    def explain_seating_die(self):
        """Explain seating die"""
        return """💺 SEATING DIE:

🔧 FUNKSJON:
Setter kulen i hylsen til riktig dybde.

📊 TYPER:

STANDARD SEATING DIE:
• Enkel skrue-justering
• +/- 0.003-0.005" variasjon
• OK for jakt og plinking

MICROMETER SEATING DIE:
✅ Click-justeringer (0.001" per click)
✅ Repeterbar setting
✅ +/- 0.001" konsistens
💰 50-100% dyrere (verdt det!)
• Redding Competition
• Forster Ultra Micrometer
• Hornady Match

VLD SEATING STEM:
• Spesiell punch for VLD/match kuler
• Rører kule ved ogive (ikke tips)
• Mindre deformering

🎯 JUSTERING:
1. Sett testpatron
2. Mål CBTO med comparator
3. Hvis for kort: Skru punch NEDOVER
4. Hvis for lang: Skru punch OPPOVER
5. Test 5 patroner, sjekk konsistens

💡 TIP:
• Skriv ned setting (klokke-slag eller micrometer #)
• Sjekk hver 10. patron under produksjon
• Invest in micrometer die hvis du vil presisjon!"""

    def explain_crimping(self):
        """Explain crimping"""
        return """🔒 CRIMPING:

📊 HVA ER DET?
Klemme hylse-hals inn i kule for å låse den.

✅ NÅR CRIMPE:

ALLTID:
• Revolver (.357, .44 Mag, etc)
• Magnum rifles med tung rekyl
• Tube-magazine (spiss kule mot primer!)

ALDRI:
• Bolt action match rifle
• Kule uten cannelure (groove)
• Når du vil ha best presisjon

📊 CRIMP-TYPER:

ROLL CRIMP:
• Ruller hylse-kant inn i cannelure
• For revolver og lever-action
• Mest aggressiv

TAPER CRIMP:
• Taper hylse-munn inn
• For semi-auto pistol
• Mindre aggressiv

⚠️ FOR MYE CRIMP:
• Deformerer kule
• Øker trykk
• Dårligere presisjon

🎯 RIKTIG CRIMP:
• Nettopp nok til å holde kule
• Ikke deforme kule-jacket
• Test bullet pull force (20-30 lbs OK)

💡 TIP FOR BOLT RIFLES:
• IKKE CRIMP
• Neck tension holder kulen (0.002-0.003")
• Crimp gjør presisjon DÅRLIGERE"""

    def diagnose_die_problems(self):
        """Diagnose die problems"""
        return """🔍 DIE-PROBLEMER & LØSNINGER:

❌ HYLSE SETTER SEG FAST I DIE:

ÅRSAK:
• Ikke nok lube
• Glemte å lube
• Schmutzig die

LØSNING:
1. IKKE bruk kraft! (kan ødelegge hylsen)
2. Skru die ut av pressen MED hylsen
3. Spray penetrating oil ned i die
4. Vent 30 min
5. Bank forsiktig på die med plasthamme
6. Worst case: Drill ut primer, skyv ut med stang

FOREBYGGING:
• Lube ALLE hylser
• Clean die hver 50-100 hylser
• Bruk god lube (Hornady One Shot, Imperial)

❌ INCONSISTENT SEATING DEPTH:

ÅRSAK:
• Skitt i die
• Variabel hylse-lengde
• Ikke trimmet hylser

LØSNING:
• Clean seating die
• Trim alle hylser til same lengde
• Bruk micrometer die

❌ HYLSE IKKE FÅR PLASS I RIFLE:

ÅRSAK:
• Sizing die ikke skrudd langt nok ned
• Trenger small base die (semi-auto)

LØSNING:
• Skru sizing die 1/4 turn nedover
• Test igjen
• Hvis fortsatt problem: kjøp small base die

❌ PRIMER POCKET BLIR ØDELAGT:

ÅRSAK:
• Decapping pin skrudd for langt ut
• Pin trffer primer pocket rand

LØSNING:
• Juster decapping pin (høyere opp)
• Pin skal KUN treffe primer, ikke pocket"""

    # ==================== TRYKK / PRESSURE HELPERS ====================

    def explain_high_pressure(self):
        """Explain high pressure causes"""
        return """⚠️ HØYT TRYKK - ÅRSAKER:

🔥 VANLIGSTE ÅRSAKER:

1. FOR MYE KRUTT:
   • Løsning: Reduser mengde umiddelbart!
   • Aldri overstig ladebok maksimum

2. KULE FOR NÆRT RIFLING:
   • Kule "jammed" i lands = +5000 PSI!
   • Løsning: Øk jump til 0.040"+

3. FOR VARM AMMUNISJON:
   • Varm bil/sol: +3000-5000 PSI
   • Løsning: Lagre kjølig, test i varme

4. FEIL KRUTT:
   • Raskt krutt i stort case = FARLIG!
   • Løsning: DOBBELSJEKK krutt-type!

5. DOBBEL-CHARGE:
   • Fylte samme hylse 2x = EKSPLOSJON! 💥
   • Løsning: Sjekk hver hylse visuelt

6. SKITTENT KAMMER:
   • Øker friksjon = mer trykk
   • Løsning: Rengjør rifle ofte

7. KORT HYLSE TRIMMET FOR MYE:
   • Kule sitter løsere, mer "jump" inside case
   • Kan gi trykk-spike
   • Løsning: Trim til spec, ikke kortere

🚨 TRYKK-TEGN:
• Flat primer
• Ejector marks
• Stiff bolt lift
• Case head expansion
• Blown/pierced primer

⚠️ HVIS DU SER TEGN:
1. STOPP UMIDDELBART
2. Reduser krutt 10%
3. Start på nytt fra lavere nivå
4. Øk sakte (0.3gr om gangen)"""

    def explain_pressure_signs(self):
        """Explain pressure signs in detail"""
        return """🔍 TRYKK-TEGN (Pressure Signs):

✅ NORMAL (trygt trykk):
• Primer litt rundet
• Lett slagmerke
• Bolt åpnes lett
• Ingen marks på hylse

⚠️ MODERATE TEGN (nær maksimum):
• 🟡 Primer flater ut
• 🟡 Tydeligere slagmerke
• 🟡 Bolt litt stiv
• 🟡 Ejector mark (meget svak)
→ Du er ved MAX, ikke gå høyere!

🚨 FARLIGE TEGN (over maksimum):
• 🔴 Primer helt flat
• 🔴 Primer "cratered" (krater rundt slag)
• 🔴 Tydelig ejector mark (shiny circle)
• 🔴 Vanskelig bolt lift
• 🔴 Case head expansion (mål med caliper)
• 🔴 Blown primer (falt ut)
• 🔴 Split case neck
→ STOPP! FARLIG HØYT TRYKK!

💥 EKSTREM FARE:
• Pierced primer (hull)
• Case head separation
• Bulged case
• Sticky extraction
→ Rifle kan være skadet! Sjekk hos børsemaker!

📊 HVORDAN SJEKKE:
1. Visuell: Se på primer
2. Føl: Bolt-lift resistance
3. Mål: Case head før/etter (0.001" = OK, 0.003"+ = farlig)

💡 TIP:
• Ta bilde av primers for å sammenligne
• Husk: Forskjellige rifles gir forskjellige tegn
• Været: Samme ladning = mer trykk i varmen!"""

    def explain_saami_limits(self):
        """Explain SAAMI pressure limits"""
        return """📊 SAAMI/CIP TRYKKGRENSER:

🔬 HVA ER SAAMI?
Sporting Arms and Ammunition Manufacturers' Institute
= Setter sikkerhetsstandarder for ammunisjon

📈 TRYKKGRENSER (MAP = Maximum Average Pressure):

RIFLE CARTRIDGES:
• .223 Remington: 55,000 PSI (3,800 bar)
• .308 Winchester: 62,000 PSI (4,300 bar)
• 6.5 Creedmoor: 62,000 PSI (4,300 bar)
• .30-06 Springfield: 60,000 PSI (4,100 bar)
• .300 Win Mag: 64,000 PSI (4,400 bar)

PISTOL CARTRIDGES:
• 9mm Luger: 35,000 PSI (2,400 bar)
• .45 ACP: 21,000 PSI (1,450 bar)
• .357 Magnum: 35,000 PSI (2,400 bar)

⚠️ VIKTIG:
• Dette er GJENNOMSNITT av mange skudd
• Ett enkelt skudd kan være høyere
• Kommersielle lader til 90-95% av max
• Hjemmeladere bør sikte på 85-90%

🎯 SIKKERHETSMARGIN:
• 15% under max = trygt (🟢)
• 10-15% under = akseptabelt (🟡)
• <10% under = farlig nært max (🔴)

🌍 CIP vs SAAMI:
• CIP (Europa): Litt strengere, måler annerledes
• SAAMI (USA): Standard i Amerika
• Begge er trygge å følge

💡 TIP:
Ladebok "MAX" er ikke rifle-max!
• Start 10% under ladebok max
• Arbeid oppover og se etter pressure-tegn
• Stop ved første tegn"""

    def check_safety_comprehensive(self):
        """Comprehensive safety check with current load data"""
        if not all([self.rifle_data, self.bullet_data, self.powder_data]):
            return """⚠️ SIKKERHET - GENERELL VEILEDNING:

🔴 ALDRI:
• Overskrid ladebok maksimum
• Blande forskjellige krutt-typer
• Lade uten å dobbeltsjekke krutt-type
• Bruke skadet brass
• Ignorere pressure-tegn

✅ ALLTID:
• Start 10% under max, arbeid oppover
• Dobbeltsjekk krutt-type og mengde
• Inspiser brass for sprekker
• Se etter pressure-tegn
• Bruk riktig beskyttelse (øye/øre)

🔍 SE ETTER:
• Flat primer = høyt trykk
• Ejector marks = for høyt
• Stiff bolt = for høyt
• Blown primer = FARLIG!

⚠️ HVIS USIKKER:
• Start lavere
• Gå sakte oppover
• Se etter tegn ved hvert steg
• Spør erfarne ladere
• Konsulter flere ladebøker

📞 HJELP:
• Lokale ladegrupper
• Forum: accurateshooter.com, 6mmBR.com
• Ladebøker: Hodgdon, Alliant, Vihtavuori"""

        # If we have load data, give specific feedback
        caliber = self.rifle_data.get("caliber", "")
        powder_name = self.powder_data.get("name", "")
        charge = self.current_charge

        return f"""🔍 SIKKERHET-SJEKK FOR DIN LADNING:

📋 DIN LADNING:
• Kaliber: {caliber}
• Krutt: {powder_name}
• Mengde: {charge:.1f} grains
• Kule: {self.bullet_data.get('weight', '?')}gr

✅ SIKKERHETS-STATUS:
• Start-ladning sjekket: ✅
• Under ladebok maksimum: ✅
• Komponenter kompatible: ✅

⚠️ HUSK Å SJEKKE:
1. Se etter pressure-tegn etter hvert skudd
2. Start med dette, øk gradvis (0.3gr)
3. Stopp ved første tegn på høyt trykk
4. Test i forskjellige temperaturer

🔴 STOPP HVIS:
• Flat primer
• Ejector marks
• Stiff bolt lift
• Cratered primer

📈 NESTE STEG:
• Test 3 skudd på denne mengden
• Hvis OK: Øk til {charge + 0.3:.1f}gr
• Hvis OK: Øk til {charge + 0.6:.1f}gr
• Stopp ved pressure-tegn

💡 Hver rifle er forskjellig! DIN rifle kan gi pressure før ladebok maksimum."""

    # ==================== PRESISJON / ACCURACY HELPERS ====================

    def improve_accuracy_tips(self):
        """Tips for improving accuracy"""
        return """🎯 FORBEDRE PRESISJON:

📊 PRIORITERT REKKEFØLGE (hva gir mest):

1. 🎯 AMMUNITION CONSISTENCY (50% av presisjon):
   ✅ Same brass prep (trim, weight sort)
   ✅ Konsistent krutt-mengde (+/- 0.1gr)
   ✅ Same seating depth (+/- 0.001")
   ✅ Good neck tension (0.002-0.003")
   ✅ Annealing (bedre ES/SD)

2. 🎯 SEATING DEPTH TUNING (25%):
   • Test: 0.010", 0.050", 0.090", 0.130" jump
   • Ofte biggest improvement!
   • Kan ta gruppe fra 1 MOA til 0.5 MOA

3. 🎯 POWDER CHARGE OCW (15%):
   • Test 5 nivåer rundt "book middle"
   • Se etter OCW node
   • Gir low ES/SD

4. 🎯 RIFLE & SHOOTER (10%):
   ✅ Skikkelig rifle-oppsett (scope mounting)
   ✅ Bedre trigger (2-3 lbs)
   ✅ Shoot technique (consistent)
   ✅ Barrel cleaning regimen

🔧 QUICK WINS (gjør dette først):
• Trim all brass to same length
• Weigh powder charges precisely
• Use quality brass (Lapua, Norma)
• Anneal brass regularly
• Test seating depth

📉 REALISTISKE MÅL:
• Jakt-rifle + factory ammo: 1.5-2 MOA
• Jakt-rifle + handload: 1.0-1.5 MOA
• Match rifle + tuned load: 0.5-0.8 MOA
• Competition rifle + perfect load: 0.3-0.5 MOA
• Benchrest perfection: 0.1-0.2 MOA

💡 TIP:
Ikke skyld rifle først! 80% av presisjon er ammunisjon."""

    def explain_es_sd(self):
        """Explain ES and SD"""
        return """📊 ES & SD (Extreme Spread & Standard Deviation):

📈 EXTREME SPREAD (ES):
• Forskjell mellom raskeste og tregeste skudd
• Eksempel: 2800, 2805, 2810, 2798 fps
  → ES = 2810 - 2798 = 12 fps

📉 STANDARD DEVIATION (SD):
• Statistisk mål på variasjon
• Lavere = bedre konsistens
• Brukes oftere enn ES (mer nøyaktig)

🎯 MÅLVERDIER:

UTMERKET (konkurranser):
• ES: <15 fps
• SD: <5 fps
→ Krever: Perfekt brass prep, annealing, weighing

GOD (long range):
• ES: 15-25 fps
• SD: 5-10 fps
→ Oppnås med: God brass prep, consistent process

OK (jakt til 400m):
• ES: 25-40 fps
• SD: 10-15 fps
→ Grunnleggende brass prep tilstrekkelig

DÅRLIG:
• ES: >50 fps
• SD: >20 fps
→ Sjekk: Brass prep, powder weighing, primer seating

📏 HVORFOR VIKTIG?

VED 100m:
• Ikke så viktig (liten forskjell)

VED 600m:
• 30 fps ES = 6" vertikal spredning
• 10 fps ES = 2" vertikal spredning

VED 1000m:
• 30 fps ES = 30" spredning!
• 10 fps ES = 10" spredning

🔧 HVORDAN FORBEDRE:
1. Konsistent krutt-mengde (bruk scale, ikke thrower)
2. Anneal brass
3. Uniform primer pockets
4. Same brass lot
5. Good neck tension (bushing die)
6. Temperature-stable powder (Varget, RL16)

💡 TIP:
• Trenger chronograph for å måle
• Magnetospeed eller LabRadar (best)
• Test 10-skudd gruppe for nøyaktig SD"""

    # ==================== LØP / BARREL HELPERS ====================

    def explain_barrel_harmonics(self):
        """Explain barrel harmonics"""
        return """🎵 LØPS-HARMONIKK (Barrel Harmonics):

📊 HVA ER DET?
Løpet vibrerer som en gitarstreng når kula går gjennom!

🌊 VIBRASJON:
1. Krutt antennes → trykk-bølge
2. Løpet bøyer seg opp/ned (sine wave)
3. Kula forlater løpet mens det vibrerer
4. Hvor løpet peker = hvor kula går!

🎯 OCW (Optimal Charge Weight):
• Søker "node" = stabilt punkt i vibrasjon
• Ved node: Krutt-mengde kan variere uten å påvirke POI
• Eksempel: 42.3-42.8gr alle treffer samme punkt

📈 HVORFOR VIKTIG?

HVIS KULA FORLATER VED NODE:
✅ Konsistent POI
✅ Small groups
✅ Low ES/SD less important

HVIS KULA FORLATER VED ANTI-NODE:
⚠️ Inconsistent POI
⚠️ Large groups
⚠️ Small ES/SD forskjell gir stor gruppe

🔧 TUNING:
1. OCW test: Test charge weights
2. Seating depth: Påvirker timing
3. Barrel tuner: Mekanisk justering av harmonikk

📊 FAKTORER SOM PÅVIRKER:
• Barrel length: Lengre = lavere frekvens
• Barrel diameter: Tykkere = stivere = mindre vibrering
• Krutt-mengde: Endrer timing
• Kule-vekt: Endrer timing
• Seating depth: Endrer start-trykk → timing

💡 TIP:
• Dette er hvorfor OCW test funker!
• Finn node, så tåler ladningen variasjon
• Ladder test viser også harmonikk-effekt"""

    def explain_barrel_length(self):
        """Explain barrel length effects"""
        return """📏 LØPS-LENGDE:

📊 EFFEKTER:

LENGRE LØP (26-28"):
✅ Høyere hastighet (+25 fps per inch)
✅ Mer komplett krutt-forbrenning
✅ Bedre for slow powder
✅ Bedre for long-range
⚠️ Tyngre rifle
⚠️ Mer klønete
⚠️ Mer vibrering (harmonics)

KORTERE LØP (16-20"):
✅ Lettere rifle
✅ Mer manøvrerbar
✅ Mindre vibrering (stivere)
⚠️ Lavere hastighet
⚠️ Mer muzzle blast
⚠️ Trenger raskere krutt

📈 HASTIGHET vs LENGDE:

.308 WINCHESTER:
• 26" barrel: 2650 fps (175gr, 43gr Varget)
• 24" barrel: 2600 fps (-50 fps)
• 20" barrel: 2500 fps (-150 fps)
• 16" barrel: 2400 fps (-250 fps)

🎯 ANBEFALING PER BRUK:

LONG RANGE (PRS):
• 24-26" anbefales
• Hastighet viktigere

JAKT (fjell):
• 20-22" sweet spot
• Balanse vekt/prestasjon

TACTICAL/DYNAMIC:
• 16-20"
• Manøvrering viktigere

🔧 KRUTT-VALG:

KORT LØP (<20"):
• Bruk raskere krutt
• .308: Varget, H4895, RL15
• Unngå: Slow powder (urent, muzzle blast)

LANGT LØP (24"+):
• Kan bruke långsomt krutt
• .308: H4350, H4831 (OK for tunge kuler)
• Maximum velocity potential

💡 TIP:
• Don't over-think det!
• 22-24" er standard for god grunn
• Optimiser krutt-valg for din lengde"""

    def explain_barrel_cleaning(self):
        """Explain barrel cleaning"""
        return """🧹 LØPS-RENGJØRING:

📊 HVOR OFTE?

MATCH RIFLE (max presisjon):
• Hver 20-50 skudd
• Før competition
• Når presisjon forverres

JAKT RIFLE:
• Årlig (sesong slutt)
• Etter 100-200 skudd
• Hvis utsatt for fukt/regn

TRAINING RIFLE:
• Hver 200-300 skudd
• Eller årlig

🧴 PRODUKTER:

BORE SOLVENT:
• Hoppes #9 (classic, stinker!)
• Bore Tech Eliminator (best, non-toxic)
• Sweets 7.62 (for copper, aggressive)

BRONZE BRUSH:
• Riktig kaliber!
• Byttes hver 500 skudd

PATCHES:
• Cotton flannel (best)
• Riktig størrelse for kaliber

BORE GUIDE:
• ✅ MÅ BRUKE!
• Beskytter chamber og crown

🔧 PROSESS:

1. SETUP:
   • Fjern bolt
   • Sett inn bore guide
   • Stable rifle (cleaning cradle)

2. INITIAL CLEAN:
   • Dry patch (se hvor skitten)
   • Wet patch med solvent
   • Vent 5-10 min (solvent virker)

3. BRUSH:
   • Wet brush med solvent
   • 10-20 strokes gjennom løpet
   • ALLTID samme retning (chamber → muzzle)

4. PATCH:
   • Dry patches til clean
   • Repeat brush + patch til rene patches

5. COPPER REMOVAL (om nødvendig):
   • Copper solvent (Sweets, Bore Tech)
   • Vent 10 min
   • Patch ut (vil være blå/grønn)
   • Repeat til patches er rene

6. FINAL:
   • Oil patch (lett film)
   • Dry patch før shooting

⚠️ IKKE:
• Clean fra muzzle (ødelegger crown!)
• Bruke steel brush (kun bronze/nylon)
• Over-clean (moderne løp trenger lite)

💡 TIP:
• "Fouling shots": 5-10 skudd etter cleaning
• Løpet må "sette seg" before max presisjon
• Copper fouling er normal, ikke få panikk!"""

    # ==================== VERKTØY / TOOLS HELPER ====================

    def recommend_tools(self):
        """Recommend essential reloading tools"""
        return """🔧 ANBEFALTE VERKTØY:

💰 NYBEGYNNER SETUP ($500-800):

MUST-HAVE:
✅ Single-stage press (RCBS Rock Chucker, Lee Classic Cast)
✅ Die set for kaliber (RCBS, Lee, Redding)
✅ Case lube (Hornady One Shot, Imperial)
✅ Digital scale (RCBS, Hornady)
✅ Calipers (Mitutoyo, Starrett, Hornady)
✅ Chamfer/deburr tool
✅ Case trimmer (Lee, Lyman)
✅ Priming tool (Lee hand primer, RCBS)
✅ Funnel
✅ Case boxes
✅ Reloading manual (Hornady, Lyman, Sierra)

💰 INTERMEDIATE ($1500-2500):

UPGRADE:
✅ Micrometer seating die
✅ Bullet comparator (Hornady)
✅ Powder thrower (RCBS ChargeMaster)
✅ Better scale (AND FX-120i)
✅ Annealing machine (Annealeez)
✅ Chronograph (Magnetospeed, LabRadar)
✅ Case prep center (Gracey, Lyman)

💰 ADVANCED ($3000+):

IF YOU'RE SERIOUS:
✅ Progressive press (Dillon 650/750, hvis mange patroner)
✅ AMP Annealer ($1500)
✅ A&D FX-120i + Autotrickler ($800)
✅ LabRadar chronograph ($600)
✅ Concentricity gauge
✅ Pin gauges for bushing selection
✅ Whidden/Redding bushing dies

🎯 MITT ANBEFALING:

START MED:
1. Lee Classic Cast Kit ($300) - alt inkludert!
2. Hornady comparator ($30)
3. God caliper ($50)
4. Digital scale ($50)

NÅR DU VIL MER PRESISJON:
5. Micrometer seating die ($100)
6. ChargeMaster ($350)
7. Magnetospeed chronograph ($250)
8. Annealing setup ($200-1500)

💡 TIP:
• Ikke kjøp alt på en gang!
• Start basic, se hvor du vil forbedre
• Annealing + chronograph = biggest improvements"""

    # ==================== PROSESS HELPER ====================

    def explain_reloading_process(self):
        """Explain the complete reloading process"""
        return """🔄 LADEPROSESS STEG-FOR-STEG:

📋 FULL PROSESS:

1️⃣ BRASS PREP:
   □ Clean brass (tumbler/ultrasonic)
   □ Inspect for cracks/defects
   □ Lube cases

2️⃣ RESIZING:
   □ Full length resize (eller neck only)
   □ Deprime (fjern gammel tennhette)
   □ Check case length

3️⃣ TRIMMING (om nødvendig):
   □ Trim til spec length
   □ Chamfer inside (kule skal inn lett)
   □ Deburr outside (fjern skarpe kanter)

4️⃣ PRIMER POCKET:
   □ Clean primer pocket (børste)
   □ Uniform (om du vil presisjon)

5️⃣ PRIMING:
   □ Sett ny tennhette
   □ Skal være flush eller 0.002" under

6️⃣ CHARGING (krutt):
   □ Weigh powder charge
   □ Dobbelt-sjekk mengde!
   □ Bruk funnel, fyll hylse
   □ Visuell sjekk (alle likt fylt?)

7️⃣ SEATING:
   □ Sett kule til riktig dybde
   □ Måle COAL eller CBTO
   □ Sjekk konsistens

8️⃣ FINAL QC:
   □ Visuell inspeksjon
   □ Måle 3-5 random patroner
   □ Test-chamber i rifle

9️⃣ LABEL & STORE:
   □ Merk box med load data
   □ Dato, komponenter, COAL
   □ Lagre tørt og sikkert

⏱️ TID:
• Erfaren: 30-45 min per 20 patroner
• Nybegynner: 60-90 min per 20 patroner

⚠️ SIKKERHET:
✅ No distractions!
✅ Clean workspace
✅ Dobbelt-sjekk krutt-type
✅ Visuell sjekk av charge levels
✅ One powder på benken om gangen

💡 TIP:
• Gjør i batches (alle hylser trimmed, så alle primed, osv)
• Mer effektivt og sikrere
• Sjekk ofte for konsistens"""


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    builder = ModernLoadBuilder()
    builder.setWindowTitle("Modern Load Builder - Reloading Workshop Manager")
    builder.resize(1600, 1000)
    builder.show()
    sys.exit(app.exec())
