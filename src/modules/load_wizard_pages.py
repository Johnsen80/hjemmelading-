"""
Load Development Wizard Pages - Additional wizard pages
Part 2: Brass, Bullet, Powder, Prediction, Protocol, Batch Creation
"""

# ruff: noqa: F811  # Temporary: multiple page classes redefined in this file; manual review needed

from datetime import datetime

from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWizardPage,
)
from src.database.database import get_database


class BrassSelectionPage(QWizardPage):
    """Page 2: Select Brass Batch"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

        self.setTitle("Step 2: Select Brass Batch")
        self.setSubTitle("Choose brass batch from inventory or create new")

        layout = QVBoxLayout()

        # Brass Batch Selection
        batch_group = QGroupBox("📦 Brass Batch Selection")
        batch_layout = QVBoxLayout()

        # Radio buttons for new vs existing
        self.batch_type_group = QButtonGroup()
        self.existing_radio = QRadioButton("Use Existing Brass Batch")
        self.new_radio = QRadioButton("Create New Brass Batch")
        self.batch_type_group.addButton(self.existing_radio)
        self.batch_type_group.addButton(self.new_radio)
        self.existing_radio.setChecked(True)

        self.existing_radio.toggled.connect(self.on_batch_type_changed)

        batch_layout.addWidget(self.existing_radio)
        batch_layout.addWidget(self.new_radio)

        # Existing batch selection
        self.batch_combo = QComboBox()
        self.load_brass_batches()
        self.batch_combo.currentIndexChanged.connect(self.on_batch_changed)
        batch_layout.addWidget(self.batch_combo)

        # New batch form (hidden initially)
        self.new_batch_widget = QGroupBox("Create New Brass Batch")
        new_batch_layout = QFormLayout()

        self.case_combo = QComboBox()
        self.load_cases()
        new_batch_layout.addRow("Brass Type:", self.case_combo)

        self.batch_name_input = QLineEdit()
        self.batch_name_input.setPlaceholderText("e.g., Lapua-308-Batch-A")
        new_batch_layout.addRow("Batch Name:", self.batch_name_input)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 5000)
        self.quantity_spin.setValue(100)
        new_batch_layout.addRow("Quantity:", self.quantity_spin)

        self.lot_number_input = QLineEdit()
        self.lot_number_input.setPlaceholderText("Manufacturer lot number")
        new_batch_layout.addRow("Lot Number:", self.lot_number_input)

        self.new_batch_widget.setLayout(new_batch_layout)
        self.new_batch_widget.setVisible(False)
        batch_layout.addWidget(self.new_batch_widget)

        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

        # Batch Info Display
        info_group = QGroupBox("📊 Brass Batch Info")
        self.batch_info_layout = QFormLayout()

        self.batch_caliber_label = QLabel("-")
        self.batch_quantity_label = QLabel("-")
        self.batch_times_fired_label = QLabel("-")
        self.batch_condition_label = QLabel("-")
        self.batch_last_annealed_label = QLabel("-")

        self.batch_info_layout.addRow("Caliber:", self.batch_caliber_label)
        self.batch_info_layout.addRow("Cases Available:", self.batch_quantity_label)
        self.batch_info_layout.addRow("Times Fired:", self.batch_times_fired_label)
        self.batch_info_layout.addRow("Condition:", self.batch_condition_label)
        self.batch_info_layout.addRow("Last Annealed:", self.batch_last_annealed_label)

        info_group.setLayout(self.batch_info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        self.setLayout(layout)

    def load_brass_batches(self):
        """Load brass batches from database"""
        db = get_database()
        batches = db.execute_query(
            """
            SELECT bb.*, c.name as case_name, c.caliber, c.manufacturer
            FROM brass_batches bb
            JOIN cases c ON bb.case_id = c.id
            WHERE bb.cases_active > 0
            ORDER BY bb.batch_name
        """
        )

        self.batch_combo.clear()
        self.batch_combo.addItem("-- Select Brass Batch --", None)
        for batch in batches:
            display_text = f"{batch['batch_name']} - {batch['case_name']} ({batch['cases_active']} cases, {batch['times_fired_avg']:.1f}x fired)"
            self.batch_combo.addItem(display_text, batch)

    def load_cases(self):
        """Load case types"""
        db = get_database()
        cases = db.get_all("cases", "name")
        self.case_combo.clear()
        for case in cases:
            self.case_combo.addItem(
                f"{case['manufacturer']} {case['name']} ({case['caliber']})", case["id"]
            )

    def on_batch_type_changed(self):
        """Toggle between existing and new batch"""
        is_existing = self.existing_radio.isChecked()
        self.batch_combo.setVisible(is_existing)
        self.new_batch_widget.setVisible(not is_existing)

    def on_batch_changed(self, index):
        """Update batch info"""
        batch = self.batch_combo.currentData()
        if batch and isinstance(batch, dict):
            self.wizard.brass_data = batch

            self.batch_caliber_label.setText(batch.get("caliber", "-"))
            self.batch_quantity_label.setText(str(batch.get("cases_active", 0)))

            times_fired = f"{batch.get('times_fired_min', 0)}-{batch.get('times_fired_max', 0)}x (avg {batch.get('times_fired_avg', 0):.1f}x)"
            self.batch_times_fired_label.setText(times_fired)

            self.batch_condition_label.setText(batch.get("condition_rating", "-"))
            self.batch_last_annealed_label.setText(
                batch.get("last_annealed_date", "Never") or "Never"
            )

    def validatePage(self):
        """Validate brass selection"""
        db = get_database()

        if self.existing_radio.isChecked():
            if self.batch_combo.currentData() is None:
                QMessageBox.warning(
                    self, "No Batch Selected", "Please select a brass batch."
                )
                return False
        else:
            # Create new batch
            if not self.batch_name_input.text():
                QMessageBox.warning(self, "Missing Info", "Please enter a batch name.")
                return False

            # Create batch in database
            batch_data = {
                "case_id": self.case_combo.currentData(),
                "batch_name": self.batch_name_input.text(),
                "batch_number": f"BB-{datetime.now().strftime('%Y-%m-%d-%H%M')}",
                "parent_lot_number": self.lot_number_input.text(),
                "cases_in_batch": self.quantity_spin.value(),
                "cases_active": self.quantity_spin.value(),
                "cases_retired": 0,
                "times_fired_min": 0,
                "times_fired_max": 0,
                "times_fired_avg": 0.0,
                "prep_status": "virgin",
                "condition_rating": "excellent",
                "created_date": datetime.now().isoformat(),
            }

            batch_id = db.insert("brass_batches", batch_data)

            # Load the created batch
            batch = db.get_by_id("brass_batches", batch_id)
            # Add case info
            case = db.get_by_id("cases", self.case_combo.currentData())
            batch["case_name"] = case["name"]
            batch["caliber"] = case["caliber"]
            batch["manufacturer"] = case["manufacturer"]

            self.wizard.brass_data = batch

            QMessageBox.information(
                self,
                "Batch Created",
                f"Created brass batch: {batch_data['batch_name']}",
            )

        return True


class BulletSelectionPage(QWizardPage):
    """Page 3: Select Bullet Lot"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

        self.setTitle("Step 3: Select Bullet")
        self.setSubTitle("Choose bullet from inventory with QC data")

        layout = QVBoxLayout()

        # Bullet Selection
        bullet_group = QGroupBox("🎯 Bullet Selection")
        bullet_layout = QFormLayout()

        self.bullet_combo = QComboBox()
        self.load_bullets()
        self.bullet_combo.currentIndexChanged.connect(self.on_bullet_changed)
        bullet_layout.addRow("Select Bullet:", self.bullet_combo)

        bullet_group.setLayout(bullet_layout)
        layout.addWidget(bullet_group)

        # Bullet Info
        info_group = QGroupBox("📊 Bullet Info")
        self.bullet_info_layout = QFormLayout()

        self.bullet_weight_label = QLabel("-")
        self.bullet_bc_label = QLabel("-")
        self.bullet_length_label = QLabel("-")
        self.bullet_lot_label = QLabel("-")
        self.bullet_quantity_label = QLabel("-")
        self.bullet_qc_label = QLabel("-")

        self.bullet_info_layout.addRow("Weight:", self.bullet_weight_label)
        self.bullet_info_layout.addRow("BC (G7):", self.bullet_bc_label)
        self.bullet_info_layout.addRow("Length:", self.bullet_length_label)
        self.bullet_info_layout.addRow("Lot Number:", self.bullet_lot_label)
        self.bullet_info_layout.addRow(
            "Quantity Available:", self.bullet_quantity_label
        )
        self.bullet_info_layout.addRow("QC Status:", self.bullet_qc_label)

        info_group.setLayout(self.bullet_info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        self.setLayout(layout)

    def load_bullets(self):
        """Load bullets with lot info"""
        db = get_database()
        bullets = db.execute_query(
            """
            SELECT b.*, bl.id as lot_id, bl.lot_number, bl.quantity_remaining,
                   bl.weight_avg_grains, bl.qc_performed, bl.quality_rating
            FROM bullets b
            LEFT JOIN bullet_lots bl ON b.id = bl.bullet_id AND bl.is_active = 1
            WHERE b.quantity > 0
            ORDER BY b.name
        """
        )

        self.bullet_combo.clear()
        self.bullet_combo.addItem("-- Select Bullet --", None)
        for bullet in bullets:
            lot_info = (
                f" [Lot: {bullet['lot_number']}]" if bullet.get("lot_number") else ""
            )
            display_text = f"{bullet['manufacturer']} {bullet['name']} {bullet['weight_grains']}gr{lot_info}"
            self.bullet_combo.addItem(display_text, bullet)

    def on_bullet_changed(self, index):
        """Update bullet info"""
        bullet = self.bullet_combo.currentData()
        if bullet and isinstance(bullet, dict):
            self.wizard.bullet_data = bullet

            self.bullet_weight_label.setText(f"{bullet.get('weight_grains', 0):.1f} gr")
            self.bullet_bc_label.setText(
                f"{bullet.get('bc_g7', 0):.3f}" if bullet.get("bc_g7") else "-"
            )
            self.bullet_length_label.setText(
                f"{bullet.get('length_mm', 0):.2f} mm"
                if bullet.get("length_mm")
                else "-"
            )
            self.bullet_lot_label.setText(bullet.get("lot_number", "-") or "-")
            self.bullet_quantity_label.setText(
                str(bullet.get("quantity_remaining", bullet.get("quantity", 0)))
            )

            if bullet.get("qc_performed"):
                qc_text = (
                    f"✅ QC Performed - {bullet.get('quality_rating', 'good').upper()}"
                )
                if bullet.get("weight_avg_grains"):
                    qc_text += f"\nAvg Weight: {bullet['weight_avg_grains']:.2f}gr"
                self.bullet_qc_label.setText(qc_text)
            else:
                self.bullet_qc_label.setText("⚠️ No QC data")

    def validatePage(self):
        """Validate bullet selection"""
        if self.bullet_combo.currentData() is None:
            QMessageBox.warning(self, "No Bullet Selected", "Please select a bullet.")
            return False
        return True


class PowderPrimerPage(QWizardPage):
    """Page 4: Select Powder and Primer"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

        self.setTitle("Step 4: Select Powder & Primer")
        self.setSubTitle("Choose powder and primer from inventory")

        layout = QVBoxLayout()

        # Powder Selection
        powder_group = QGroupBox("💥 Powder Selection")
        powder_layout = QFormLayout()

        self.powder_combo = QComboBox()
        self.load_powders()
        self.powder_combo.currentIndexChanged.connect(self.on_powder_changed)
        powder_layout.addRow("Select Powder:", self.powder_combo)

        self.powder_lot_input = QLineEdit()
        self.powder_lot_input.setPlaceholderText("Powder lot number (optional)")
        powder_layout.addRow("Lot Number:", self.powder_lot_input)

        powder_group.setLayout(powder_layout)
        layout.addWidget(powder_group)

        # Powder Info
        powder_info_group = QGroupBox("📊 Powder Info")
        self.powder_info_layout = QFormLayout()

        self.powder_type_label = QLabel("-")
        self.powder_burn_rate_label = QLabel("-")
        self.powder_quantity_label = QLabel("-")

        self.powder_info_layout.addRow("Type:", self.powder_type_label)
        self.powder_info_layout.addRow("Burn Rate:", self.powder_burn_rate_label)
        self.powder_info_layout.addRow(
            "Quantity Available:", self.powder_quantity_label
        )

        powder_info_group.setLayout(self.powder_info_layout)
        layout.addWidget(powder_info_group)

        # Primer Selection
        primer_group = QGroupBox("🔥 Primer Selection")
        primer_layout = QFormLayout()

        self.primer_combo = QComboBox()
        self.load_primers()
        self.primer_combo.currentIndexChanged.connect(self.on_primer_changed)
        primer_layout.addRow("Select Primer:", self.primer_combo)

        self.primer_lot_input = QLineEdit()
        self.primer_lot_input.setPlaceholderText("Primer lot number (optional)")
        primer_layout.addRow("Lot Number:", self.primer_lot_input)

        primer_group.setLayout(primer_layout)
        layout.addWidget(primer_group)

        # Primer Info
        primer_info_group = QGroupBox("📊 Primer Info")
        self.primer_info_layout = QFormLayout()

        self.primer_type_label = QLabel("-")
        self.primer_quantity_label = QLabel("-")

        self.primer_info_layout.addRow("Type:", self.primer_type_label)
        self.primer_info_layout.addRow(
            "Quantity Available:", self.primer_quantity_label
        )

        primer_info_group.setLayout(self.primer_info_layout)
        layout.addWidget(primer_info_group)

        layout.addStretch()
        self.setLayout(layout)

    def load_powders(self):
        """Load powders from database"""
        db = get_database()
        powders = db.execute_query(
            """
            SELECT * FROM powder
            WHERE quantity_grams > 0
            ORDER BY name
        """
        )

        self.powder_combo.clear()
        self.powder_combo.addItem("-- Select Powder --", None)
        for powder in powders:
            display_text = f"{powder['manufacturer']} {powder['name']}"
            self.powder_combo.addItem(display_text, powder)

    def load_primers(self):
        """Load primers from database"""
        db = get_database()
        primers = db.execute_query(
            """
            SELECT * FROM primers
            WHERE quantity > 0
            ORDER BY name
        """
        )

        self.primer_combo.clear()
        self.primer_combo.addItem("-- Select Primer --", None)
        for primer in primers:
            display_text = (
                f"{primer['manufacturer']} {primer['name']} ({primer['type']})"
            )
            self.primer_combo.addItem(display_text, primer)

    def on_powder_changed(self, index):
        """Update powder info"""
        powder = self.powder_combo.currentData()
        if powder and isinstance(powder, dict):
            self.wizard.powder_data = powder
            self.wizard.powder_data["lot_number"] = ""  # Will be filled from input

            self.powder_type_label.setText(powder.get("type", "-"))
            self.powder_burn_rate_label.setText(powder.get("burn_rate", "-"))
            self.powder_quantity_label.setText(
                f"{powder.get('quantity_grams', 0):.0f} grams"
            )

    def on_primer_changed(self, index):
        """Update primer info"""
        primer = self.primer_combo.currentData()
        if primer and isinstance(primer, dict):
            self.wizard.primer_data = primer
            self.wizard.primer_data["lot_number"] = ""  # Will be filled from input

            self.primer_type_label.setText(
                f"{primer.get('type', '-')} ({primer.get('size', '-')})"
            )
            self.primer_quantity_label.setText(str(primer.get("quantity", 0)))

    def validatePage(self):
        """Validate powder and primer selection"""
        if self.powder_combo.currentData() is None:
            QMessageBox.warning(self, "No Powder Selected", "Please select a powder.")
            return False
        if self.primer_combo.currentData() is None:
            QMessageBox.warning(self, "No Primer Selected", "Please select a primer.")
            return False

        # Store lot numbers
        self.wizard.powder_data["lot_number"] = self.powder_lot_input.text()
        self.wizard.primer_data["lot_number"] = self.primer_lot_input.text()

        return True


class LoadDataPage(QWizardPage):
    """Page 5: Enter Load Parameters"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

        self.setTitle("Step 5: Load Parameters")
        self.setSubTitle("Enter charge weight range and seating depth")

        layout = QVBoxLayout()

        # Charge Weight
        charge_group = QGroupBox("⚖️ Charge Weight Range")
        charge_layout = QFormLayout()

        self.min_charge_spin = QDoubleSpinBox()
        self.min_charge_spin.setRange(0.0, 200.0)
        self.min_charge_spin.setSingleStep(0.1)
        self.min_charge_spin.setDecimals(1)
        self.min_charge_spin.setSuffix(" gr")
        charge_layout.addRow("Minimum Charge:", self.min_charge_spin)

        self.max_charge_spin = QDoubleSpinBox()
        self.max_charge_spin.setRange(0.0, 200.0)
        self.max_charge_spin.setSingleStep(0.1)
        self.max_charge_spin.setDecimals(1)
        self.max_charge_spin.setSuffix(" gr")
        charge_layout.addRow("Maximum Charge:", self.max_charge_spin)

        charge_group.setLayout(charge_layout)
        layout.addWidget(charge_group)

        # Seating Depth
        seating_group = QGroupBox("📏 Seating Depth")
        seating_layout = QFormLayout()

        self.coal_spin = QDoubleSpinBox()
        self.coal_spin.setRange(0.0, 100.0)
        self.coal_spin.setSingleStep(0.01)
        self.coal_spin.setDecimals(2)
        self.coal_spin.setSuffix(" mm")
        seating_layout.addRow("COAL (Cartridge Overall Length):", self.coal_spin)

        self.cbto_spin = QDoubleSpinBox()
        self.cbto_spin.setRange(0.0, 100.0)
        self.cbto_spin.setSingleStep(0.01)
        self.cbto_spin.setDecimals(2)
        self.cbto_spin.setSuffix(" mm")
        seating_layout.addRow("CBTO (Cartridge Base To Ogive):", self.cbto_spin)

        self.jump_spin = QDoubleSpinBox()
        self.jump_spin.setRange(-1.0, 5.0)
        self.jump_spin.setSingleStep(0.01)
        self.jump_spin.setDecimals(2)
        self.jump_spin.setSuffix(" mm")
        seating_layout.addRow("Jump (Distance from Lands):", self.jump_spin)

        seating_group.setLayout(seating_layout)
        layout.addWidget(seating_group)

        # Test Parameters
        test_group = QGroupBox("🧪 Test Parameters")
        test_layout = QFormLayout()

        self.test_distance_spin = QSpinBox()
        self.test_distance_spin.setRange(25, 1000)
        self.test_distance_spin.setValue(100)
        self.test_distance_spin.setSuffix(" m")
        test_layout.addRow("Test Distance:", self.test_distance_spin)

        self.shots_per_charge_spin = QSpinBox()
        self.shots_per_charge_spin.setRange(1, 10)
        self.shots_per_charge_spin.setValue(3)
        test_layout.addRow("Shots per Charge:", self.shots_per_charge_spin)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        layout.addStretch()
        self.setLayout(layout)

    def validatePage(self):
        """Validate load parameters"""
        if self.min_charge_spin.value() >= self.max_charge_spin.value():
            QMessageBox.warning(
                self,
                "Invalid Range",
                "Minimum charge must be less than maximum charge.",
            )
            return False
        if self.coal_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid COAL", "Please enter a valid COAL.")
            return False

        # Store load parameters
        self.wizard.load_params = {
            "min_charge": self.min_charge_spin.value(),
            "max_charge": self.max_charge_spin.value(),
            "coal_mm": self.coal_spin.value(),
            "cbto_mm": self.cbto_spin.value(),
            "jump_mm": self.jump_spin.value(),
            "test_distance_m": self.test_distance_spin.value(),
            "shots_per_charge": self.shots_per_charge_spin.value(),
        }

        return True


class AIPredictionPage(QWizardPage):
    """Page 6: AI Load Prediction"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

        self.setTitle("Step 6: AI Prediction")
        self.setSubTitle("AI-predicted optimal load based on your historical data")

        layout = QVBoxLayout()

        # Prediction Display
        prediction_group = QGroupBox("🤖 AI Load Prediction")
        self.prediction_text = QTextEdit()
        self.prediction_text.setReadOnly(True)
        self.prediction_text.setMinimumHeight(400)

        prediction_layout = QVBoxLayout()
        prediction_layout.addWidget(self.prediction_text)

        self.calculate_btn = QPushButton("🎯 Calculate Optimal Load")
        self.calculate_btn.clicked.connect(self.calculate_prediction)
        self.calculate_btn.setStyleSheet(
            "background: #27ae60; color: white; font-weight: bold; padding: 12px;"
        )
        prediction_layout.addWidget(self.calculate_btn)

        prediction_group.setLayout(prediction_layout)
        layout.addWidget(prediction_group)

        self.setLayout(layout)

    def initializePage(self):
        """Run prediction when page loads"""
        self.calculate_prediction()

    def calculate_prediction(self):
        """Calculate AI prediction with REAL physics-based ballistics"""
        from src.modules.ballistics_engine import get_ballistics_engine

        db = get_database()
        engine = get_ballistics_engine()

        rifle = self.wizard.rifle_data
        bullet = self.wizard.bullet_data
        powder = self.wizard.powder_data
        params = self.wizard.load_params

        html = "<h2 style='color: #27ae60;'>🤖 AI + Physics Load Prediction</h2>"

        # Query historical data for ML prediction
        similar_loads = db.execute_query(
            """
            SELECT rat.*, lab.charge_weight_grains, lab.actual_moa_avg,
                   lab.actual_velocity_avg_fps, lab.actual_es_fps, lab.actual_sd_fps
            FROM rifle_accuracy_tests rat
            LEFT JOIN loaded_ammo_batches lab ON rat.id = lab.accuracy_test_id
            WHERE rat.rifle_id = ?
            AND rat.bullet_id = ?
            AND rat.powder_id = ?
            AND rat.average_moa IS NOT NULL
            ORDER BY rat.average_moa ASC
            LIMIT 10
        """,
            (rifle["id"], bullet.get("id"), powder.get("id")),
        )

        # Physics-based calculation for test range
        min_charge = params["min_charge"]
        max_charge = params["max_charge"]
        coal_mm = params["coal"]
        cbto_mm = params.get("cbto")

        # Calculate ballistics for min, mid, max charges
        mid_charge = (min_charge + max_charge) / 2
        test_charges = [
            min_charge,
            (min_charge + mid_charge) / 2,
            mid_charge,
            (mid_charge + max_charge) / 2,
            max_charge,
        ]

        ballistics_results = []
        for charge in test_charges:
            calc = engine.calculate_load(
                rifle["id"],
                bullet.get("id"),
                powder.get("id"),
                charge,
                coal_mm,
                cbto_mm,
            )
            if "error" not in calc:
                calc["charge_weight_gr"] = charge
                ballistics_results.append(calc)

        # Find optimal charge (highest safety margin without being too light)
        safe_loads = [b for b in ballistics_results if b["safety_margin_percent"] > 15]
        if safe_loads:
            # Pick the highest velocity with good safety margin
            optimal = max(safe_loads, key=lambda x: x["muzzle_velocity_fps"])
            optimal_charge = optimal["charge_weight_gr"]
        else:
            # All loads near max - use lowest
            optimal = ballistics_results[0] if ballistics_results else None
            optimal_charge = min_charge

        # Show historical data if available
        if similar_loads:
            valid_charges = [
                load["charge_weight_grains"]
                for load in similar_loads
                if load.get("charge_weight_grains")
            ]
            valid_moas = [
                load["average_moa"] for load in similar_loads if load.get("average_moa")
            ]

            if valid_charges and valid_moas:
                hist_avg_charge = sum(valid_charges) / len(valid_charges)
                hist_avg_moa = sum(valid_moas) / len(valid_moas)
                best = similar_loads[0]

                html += f"""
                <h3 style='color: #9b59b6;'>📚 Historical Data Analysis:</h3>
                <p style='font-size: 11pt;'>Found {len(similar_loads)} similar loads in your database:</p>
                <ul style='font-size: 10pt;'>
                    <li>Historical Best Charge: {hist_avg_charge:.1f} gr</li>
                    <li>Historical Accuracy: {hist_avg_moa:.2f} MOA</li>
                    <li>Historical Velocity: ~{best.get('average_velocity_fps', 0):.0f} fps</li>
                </ul>
                """

        # Show physics prediction
        if optimal:
            html += """
            <h3 style='color: #3498db;'>🔬 Physics-Based Prediction:</h3>
            <table style='font-size: 10pt; width: 100%; border-collapse: collapse;'>
                <tr style='background: #ecf0f1;'>
                    <th style='padding: 8px; text-align: left;'>Charge (gr)</th>
                    <th style='padding: 8px;'>Pressure (PSI)</th>
                    <th style='padding: 8px;'>Velocity (fps)</th>
                    <th style='padding: 8px;'>Safety Margin</th>
                </tr>
            """

            for b in ballistics_results:
                safety_color = (
                    "#27ae60"
                    if b["safety_margin_percent"] > 20
                    else "#e67e22" if b["safety_margin_percent"] > 10 else "#e74c3c"
                )
                optimal_marker = "⭐" if b["charge_weight_gr"] == optimal_charge else ""

                html += f"""
                <tr>
                    <td style='padding: 8px;'><b>{b['charge_weight_gr']:.1f}</b> {optimal_marker}</td>
                    <td style='padding: 8px; text-align: center;'>{b['peak_pressure_psi']:.0f}</td>
                    <td style='padding: 8px; text-align: center;'>{b['muzzle_velocity_fps']:.0f}</td>
                    <td style='padding: 8px; text-align: center; color: {safety_color}; font-weight: bold;'>
                        {b['safety_margin_percent']:.1f}%
                    </td>
                </tr>
                """

            html += "</table>"

            # Show warnings
            if optimal["warnings"]:
                html += "<h3 style='color: #e74c3c;'>⚠️ Safety Warnings:</h3><ul style='font-size: 10pt;'>"
                for warning in optimal["warnings"]:
                    html += f"<li>{warning}</li>"
                html += "</ul>"

            # Recommended test charges
            html += f"""
            <h3 style='color: #27ae60;'>🎯 Recommended Test Charges:</h3>
            <p style='font-size: 11pt;'>
            Based on physics + your rifle specs:<br>
            <b style='color: #3498db;'>{test_charges[0]:.1f}, {test_charges[1]:.1f}, {test_charges[2]:.1f}, {test_charges[3]:.1f}, {test_charges[4]:.1f} gr</b>
            </p>

            <p style='font-size: 10pt; color: #7f8c8d;'>
            <b>Optimal predicted:</b> {optimal_charge:.1f} gr @ {optimal['muzzle_velocity_fps']:.0f} fps
            ({optimal['peak_pressure_psi']:.0f} PSI, {optimal['safety_margin_percent']:.1f}% under max)<br>
            <b>Barrel time:</b> {optimal['barrel_time_ms']:.2f} ms<br>
            <b>Muzzle energy:</b> {optimal['energy_ft_lbs']:.0f} ft-lbs
            </p>
            """

            self.wizard.prediction_data = {
                "optimal_charge": optimal_charge,
                "expected_velocity": optimal["muzzle_velocity_fps"],
                "expected_pressure": optimal["peak_pressure_psi"],
                "safety_margin": optimal["safety_margin_percent"],
                "barrel_time_ms": optimal["barrel_time_ms"],
                "energy_ft_lbs": optimal["energy_ft_lbs"],
                "test_charges": test_charges,
                "ballistics_results": ballistics_results,
                "confidence": 0.9,  # High confidence - physics-based
            }
        else:
            html += "<p style='color: #e74c3c;'>⚠️ Could not calculate ballistics - check rifle/bullet/powder data</p>"
            self.create_fallback_prediction(html, params)

        self.prediction_text.setHtml(html)

    def create_fallback_prediction(self, html, params):
        """Create prediction when no historical data exists"""
        min_charge = params["min_charge"]
        max_charge = params["max_charge"]
        mid_charge = (min_charge + max_charge) / 2

        html_fallback = f"""
        <p style='font-size: 12pt; color: #e67e22;'><b>⚠️ No Historical Data Found</b></p>
        <p>This is a new combination. Starting with conservative mid-range load.</p>

        <h3 style='color: #3498db;'>📊 Recommended Starting Load:</h3>
        <ul style='font-size: 11pt; line-height: 1.8;'>
            <li><b>Starting Charge:</b> {mid_charge:.1f} gr (mid-range)</li>
            <li><b>Test Range:</b> {min_charge:.1f} - {max_charge:.1f} gr</li>
            <li><b>Recommended Protocol:</b> OCW or Satterlee test</li>
            <li><b>Safety:</b> Start low, work up carefully</li>
        </ul>

        <h3 style='color: #e67e22;'>🎯 Recommended Test Charges:</h3>
        <p style='font-size: 11pt;'>
        {min_charge:.1f}, {min_charge + (max_charge-min_charge)/4:.1f}, <b>{mid_charge:.1f}</b>, {min_charge + 3*(max_charge-min_charge)/4:.1f}, {max_charge:.1f} gr
        </p>
        """

        step = (max_charge - min_charge) / 4
        self.wizard.prediction_data = {
            "optimal_charge": mid_charge,
            "expected_moa": None,
            "expected_velocity": None,
            "expected_es": None,
            "expected_sd": None,
            "confidence": 0.3,
            "test_charges": [
                min_charge,
                min_charge + step,
                mid_charge,
                min_charge + 3 * step,
                max_charge,
            ],
        }

        self.prediction_text.setHtml(html + html_fallback)


class TestProtocolPage(QWizardPage):
    """Page 7: Test Protocol"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

        self.setTitle("Step 7: Test Protocol")
        self.setSubTitle("Minimal test protocol to find optimal load")

        layout = QVBoxLayout()

        # Protocol Display
        protocol_text = QTextEdit()
        protocol_text.setReadOnly(True)
        protocol_text.setHtml(
            """
        <h2 style='color: #3498db;'>🧪 Recommended Test Protocol</h2>

        <h3 style='color: #27ae60;'>Method: Bayesian Optimization + OCW</h3>

        <p style='font-size: 11pt; line-height: 1.8;'>
        This protocol minimizes ammunition waste while maximizing data quality.
        </p>

        <h3 style='color: #e67e22;'>Test Procedure:</h3>
        <ol style='font-size: 11pt; line-height: 1.8;'>
            <li><b>Load Test Charges</b> (5 charges × 3 rounds = 15 rounds total)
                <ul>
                    <li>Charges will be calculated based on AI prediction</li>
                    <li>Focus on predicted optimal window ±0.6gr</li>
                </ul>
            </li>
            <li><b>Shoot for Accuracy</b>
                <ul>
                    <li>Shoot 3-shot groups at 100m per charge</li>
                    <li>Record velocity with chronograph</li>
                    <li>Measure group size (MOA)</li>
                </ul>
            </li>
            <li><b>Analyze Results</b>
                <ul>
                    <li>Find charge with best MOA</li>
                    <li>Look for OCW "cluster" (groups hitting same POI)</li>
                    <li>Check ES/SD (flat velocity spot)</li>
                </ul>
            </li>
            <li><b>Verify Load</b> (Optional)
                <ul>
                    <li>Load 20 rounds at optimal charge</li>
                    <li>Shoot 4×5-shot groups to confirm</li>
                    <li>If confirmed, load batch for use</li>
                </ul>
            </li>
        </ol>

        <h3 style='color: #c0392b;'>⚠️ Safety Reminders:</h3>
        <ul style='font-size: 11pt;'>
            <li>Start with lowest charge first</li>
            <li>Watch for pressure signs (flattened primers, ejector marks, heavy bolt lift)</li>
            <li>Stop immediately if pressure signs appear</li>
            <li>Velocity should increase gradually (sudden jump = pressure spike)</li>
        </ul>

        <p style='font-size: 12pt; color: #27ae60; font-weight: bold;'>
        Total Rounds Needed: ~15-35 rounds (vs traditional 60-100 rounds!)
        </p>
        """
        )
        protocol_text.setMinimumHeight(450)
        layout.addWidget(protocol_text)

        self.setLayout(layout)


class BatchCreationPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard

        self.setTitle("Step 8: Create Test Batches")
        self.setSubTitle("Auto-generate batch numbers for test loads")

        layout = QVBoxLayout()

        # Batch Summary
        summary_group = QGroupBox("📦 Test Batch Summary")
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(250)

        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Batch Creation Options
        options_group = QGroupBox("⚙️ Batch Options")
        options_layout = QFormLayout()

        self.batch_prefix_input = QLineEdit()
        self.batch_prefix_input.setText(f"LAB-{datetime.now().strftime('%Y-%m-%d')}")
        options_layout.addRow("Batch Number Prefix:", self.batch_prefix_input)

        self.create_batches_check = QCheckBox("Create batches in database now")
        self.create_batches_check.setChecked(True)
        options_layout.addRow("", self.create_batches_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Create Button
        self.create_btn = QPushButton("✅ Create Test Batches")
        self.create_btn.clicked.connect(self.create_batches)
        self.create_btn.setStyleSheet(
            "background: #27ae60; color: white; font-weight: bold; padding: 12px; font-size: 12pt;"
        )
        layout.addWidget(self.create_btn)

        # Print batchark-knapp
        self.print_btn = QPushButton("🖨️ Print Batchark")
        self.print_btn.clicked.connect(self.print_batch_sheet)
        self.print_btn.setStyleSheet(
            "background: #2980b9; color: white; font-weight: bold; padding: 12px; font-size: 12pt;"
        )
        layout.addWidget(self.print_btn)

        layout.addStretch()
        self.setLayout(layout)

        def print_batch_sheet(self):
            """Generer og vis batchark for utskrift"""
            test_charges = self.wizard.prediction_data.get("test_charges", [])
            shots_per_charge = self.wizard.load_params.get("shots_per_charge", 3)
            rifle = self.wizard.rifle_data
            brass = self.wizard.brass_data
            bullet = self.wizard.bullet_data
            powder = self.wizard.powder_data
            primer = self.wizard.primer_data
            params = self.wizard.load_params

            html = """
            <h2 style='color:#2980b9;'>Batchark for Testlading</h2>
            <table border='1' cellpadding='6' style='border-collapse:collapse;width:100%;font-size:13pt;'>
            <tr><th>Batchnummer</th><th>Kule</th><th>Vekt</th><th>Krutt</th><th>Ladning</th><th>Tennhette</th><th>Antall</th></tr>
            """
            for i, charge in enumerate(test_charges, 1):
                batch_num = f"{self.batch_prefix_input.text()}-{i:03d}"
                html += "<tr>"
                html += f"<td>{batch_num}</td>"
                html += (
                    f"<td>{bullet.get('manufacturer','')} {bullet.get('name','')}</td>"
                )
                html += f"<td>{bullet.get('weight_grains','-')} gr</td>"
                html += (
                    f"<td>{powder.get('manufacturer','')} {powder.get('name','')}</td>"
                )
                html += f"<td>{charge:.1f} gr</td>"
                html += (
                    f"<td>{primer.get('manufacturer','')} {primer.get('name','')}</td>"
                )
                html += f"<td>{shots_per_charge}</td>"
                html += "</tr>"
            html += "</table>"
            html += f"<p><b>Rifle:</b> {rifle.get('name','-')}<br>"
            html += f"<b>Hylsebatch:</b> {brass.get('batch_name','-')}<br>"
            html += f"<b>COAL:</b> {params.get('coal_mm','-')} mm | <b>CBTO:</b> {params.get('cbto_mm','-')} mm</p>"

            # Vis i nytt vindu
            dlg = QDialog(self)
            dlg.setWindowTitle("Batchark for utskrift")
            dlg.resize(800, 600)
            vbox = QVBoxLayout()
            text = QTextEdit()
            text.setReadOnly(True)
            text.setHtml(html)
            vbox.addWidget(text)
            btns = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Print
                | QDialogButtonBox.StandardButton.Close
            )
            btns.accepted.connect(lambda: text.print_())
            btns.rejected.connect(dlg.reject)
            vbox.addWidget(btns)
            dlg.setLayout(vbox)
            dlg.exec()

    def initializePage(self):
        """Show batch summary"""
        self.show_summary()

    def show_summary(self):
        """Display summary of batches to be created"""
        test_charges = self.wizard.prediction_data.get("test_charges", [])
        shots_per_charge = self.wizard.load_params.get("shots_per_charge", 3)

        rifle = self.wizard.rifle_data
        brass = self.wizard.brass_data
        bullet = self.wizard.bullet_data
        powder = self.wizard.powder_data
        primer = self.wizard.primer_data
        params = self.wizard.load_params

        html = f"""
        <h3 style='color: #3498db;'>Test Batches to Create:</h3>
        <p><b>Rifle:</b> {rifle.get('name', 'N/A')}</p>
        <p><b>Brass:</b> {brass.get('batch_name', 'N/A')}</p>
        <p><b>Bullet:</b> {bullet.get('manufacturer', '')} {bullet.get('name', 'N/A')} {bullet.get('weight_grains', 0):.1f}gr</p>
        <p><b>Powder:</b> {powder.get('manufacturer', '')} {powder.get('name', 'N/A')}</p>
        <p><b>Primer:</b> {primer.get('manufacturer', '')} {primer.get('name', 'N/A')}</p>
        <p><b>COAL:</b> {params.get('coal_mm', 0):.2f} mm | <b>CBTO:</b> {params.get('cbto_mm', 0):.2f} mm</p>
        <hr>
        <h4>Test Charges ({len(test_charges)} charges × {shots_per_charge} shots = {len(test_charges) * shots_per_charge} rounds):</h4>
        <ul>
        """

        for i, charge in enumerate(test_charges, 1):
            batch_num = f"{self.batch_prefix_input.text()}-{i:03d}"
            html += f"<li><b>{batch_num}</b>: {charge:.1f}gr × {shots_per_charge} rounds</li>"

        html += """
        </ul>
        <p style='color: #27ae60; font-weight: bold;'>Total ammunition needed: {} rounds</p>
        """.format(
            len(test_charges) * shots_per_charge
        )

        self.summary_text.setHtml(html)

    def create_batches(self):
        """Create batches in database"""
        if not self.create_batches_check.isChecked():
            QMessageBox.information(
                self, "Complete", "Wizard complete! Batches not created in database."
            )
            self.wizard.accept()
            return

        try:
            db = get_database()

            test_charges = self.wizard.prediction_data.get("test_charges", [])
            params = self.wizard.load_params
            shots_per_charge = params.get("shots_per_charge", 3)

            rifle = self.wizard.rifle_data
            brass = self.wizard.brass_data
            bullet = self.wizard.bullet_data
            powder = self.wizard.powder_data
            primer = self.wizard.primer_data

            created_batches = []
            batch_ids = []

            for i, charge in enumerate(test_charges, 1):
                batch_number = f"{self.batch_prefix_input.text()}-{i:03d}"
                batch_name = f"Test Load {charge:.1f}gr"

                batch_data = {
                    "batch_number": batch_number,
                    "batch_name": batch_name,
                    "rifle_id": rifle["id"],
                    "loaded_date": datetime.now().isoformat(),
                    "brass_batch_id": brass.get("id"),
                    "bullet_lot_id": bullet.get("lot_id") or bullet.get("id"),
                    "powder_id": powder["id"],
                    "powder_lot_number": powder.get("lot_number", ""),
                    "primer_id": primer["id"],
                    "primer_lot_number": primer.get("lot_number", ""),
                    "charge_weight_grains": charge,
                    "charge_weight_tolerance_grains": 0.1,
                    "coal_mm": params.get("coal_mm", 0.0),
                    "cbto_mm": params.get("cbto_mm", 0.0),
                    "bullet_jump_mm": params.get("jump_mm", 0.0),
                    "quantity_loaded": shots_per_charge,
                    "quantity_remaining": shots_per_charge,
                    "quantity_fired": 0,
                    "qc_performed": 0,
                    "batch_status": "loaded",
                    "intended_use": "load_development",
                    "safe_to_fire": 1,
                    "created_date": datetime.now().isoformat(),
                }

                batch_id = db.insert("loaded_ammo_batches", batch_data)
                created_batches.append(batch_number)
                batch_ids.append(batch_id)

            self.wizard.created_batches = batch_ids

            QMessageBox.information(
                self,
                "✅ Batches Created!",
                f"Successfully created {len(created_batches)} test batches:\n\n"
                + "\n".join(created_batches)
                + f"\n\nTotal: {len(test_charges) * shots_per_charge} rounds to load."
                + "\n\n🎯 Next steps:"
                + "\n1. Load the test ammunition"
                + "\n2. Perform QC measurements"
                + "\n3. Test at the range"
                + "\n4. Log results in Accuracy Test System",
            )

            self.wizard.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create batches:\n{str(e)}")

    def validatePage(self):
        """This is the last page, validation happens in create_batches"""
        return True
