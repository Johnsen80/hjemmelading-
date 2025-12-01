"""
Brass/Case Manager - Comprehensive lifecycle tracking
Spor hylser fra kjøp til retirement med målinger, annealing, og firing count
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QLabel, QDialog,
                            QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                            QComboBox, QTextEdit, QDateEdit, QCheckBox,
                            QMessageBox, QTabWidget, QGroupBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from src.database.database import get_database
from datetime import datetime


class BrassManager(QWidget):
    """Main brass/case management widget"""
    
    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🥉 Brass/Hylse Manager")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel(
            "Spor lifecycle av hylser: Kjøp → Firing → Annealing → Trimming → Retirement\n"
            "Hold oversikt over lot numbers, målinger, og prep history."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("➕ Nytt Hylse-Lot")
        btn_add.clicked.connect(self.add_case_lot)
        toolbar.addWidget(btn_add)
        
        btn_fire = QPushButton("🔥 Logg Skyting (+1 Firing)")
        btn_fire.clicked.connect(self.log_firing)
        toolbar.addWidget(btn_fire)
        
        btn_anneal = QPushButton("♨️ Logg Annealing")
        btn_anneal.clicked.connect(self.log_annealing)
        toolbar.addWidget(btn_anneal)
        
        btn_prep = QPushButton("🔧 Logg Prep (Trim/Uniform)")
        btn_prep.clicked.connect(self.log_prep)
        toolbar.addWidget(btn_prep)
        
        btn_measure = QPushButton("📏 Legg til Måling")
        btn_measure.clicked.connect(self.add_measurement)
        toolbar.addWidget(btn_measure)
        
        btn_retire = QPushButton("🗑️ Retirer Hylser")
        btn_retire.clicked.connect(self.retire_cases)
        toolbar.addWidget(btn_retire)
        
        toolbar.addStretch()
        
        btn_refresh = QPushButton("🔄 Oppdater")
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)
        
        layout.addLayout(toolbar)
        
        # Main table
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "Lot/Navn", "Produsent", "Kaliber", "Antall",
            "Times Fired", "Sist Annealed", "Anneal Due?",
            "Avg Weight", "Capacity", "Retired", "Status"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.view_details)
        layout.addWidget(self.table)
        
        # Status bar
        self.status_label = QLabel("Klar")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Load brass lots from database"""
        cases = self.db.execute_query("""
            SELECT id, name, manufacturer, caliber, quantity, times_fired,
                   last_annealed, needs_annealing, avg_weight_gr, 
                   case_capacity_gr_h2o, retired_quantity, lot_number
            FROM cases
            ORDER BY caliber, manufacturer, name
        """)
        
        self.table.setRowCount(len(cases))
        
        for i, case in enumerate(cases):
            case_id, name, manufacturer, caliber, qty, fired, annealed, needs_anneal, \
            weight, capacity, retired, lot = case
            
            # ID (hidden, for selection)
            item_id = QTableWidgetItem(str(case_id))
            item_id.setData(Qt.ItemDataRole.UserRole, case_id)
            self.table.setItem(i, 0, item_id)
            
            # Lot/Name
            lot_name = f"{lot} - {name}" if lot else name
            self.table.setItem(i, 1, QTableWidgetItem(lot_name))
            
            # Manufacturer
            self.table.setItem(i, 2, QTableWidgetItem(manufacturer or "-"))
            
            # Caliber
            self.table.setItem(i, 3, QTableWidgetItem(caliber))
            
            # Quantity
            self.table.setItem(i, 4, QTableWidgetItem(str(qty)))
            
            # Times Fired (color-coded)
            fired_item = QTableWidgetItem(str(fired))
            if fired >= 10:
                fired_item.setBackground(QColor("#e74c3c"))  # Red - consider retirement
                fired_item.setForeground(QColor("white"))
            elif fired >= 5:
                fired_item.setBackground(QColor("#f39c12"))  # Orange - watch closely
            elif fired >= 3:
                fired_item.setBackground(QColor("#f9e79f"))  # Yellow - anneal soon
            else:
                fired_item.setBackground(QColor("#d5f4e6"))  # Green - fresh
            self.table.setItem(i, 5, fired_item)
            
            # Last Annealed
            self.table.setItem(i, 6, QTableWidgetItem(annealed or "Aldri"))
            
            # Anneal Due?
            anneal_item = QTableWidgetItem("⚠️ JA" if needs_anneal else "OK")
            if needs_anneal:
                anneal_item.setBackground(QColor("#f39c12"))
                anneal_item.setForeground(QColor("white"))
            self.table.setItem(i, 7, anneal_item)
            
            # Avg Weight
            weight_str = f"{weight:.1f}gr" if weight else "-"
            self.table.setItem(i, 8, QTableWidgetItem(weight_str))
            
            # Capacity
            cap_str = f"{capacity:.1f}gr H2O" if capacity else "-"
            self.table.setItem(i, 9, QTableWidgetItem(cap_str))
            
            # Retired
            self.table.setItem(i, 10, QTableWidgetItem(str(retired)))
            
            # Status
            if qty == 0:
                status = "❌ Tom"
            elif fired >= 10:
                status = "🔴 Consider Retirement"
            elif needs_anneal:
                status = "⚠️ Needs Annealing"
            elif fired >= 5:
                status = "🟡 Moderat bruk"
            else:
                status = "✅ God"
            self.table.setItem(i, 11, QTableWidgetItem(status))
        
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 200)  # Lot/Name wider
        
        # Update status
        total_cases = sum(case[4] for case in cases)  # Sum quantities
        need_anneal = sum(1 for case in cases if case[7])
        self.status_label.setText(
            f"Total: {len(cases)} lots, {total_cases} hylser | "
            f"⚠️ {need_anneal} lots trenger annealing"
        )
    
    def add_case_lot(self):
        """Add new case lot"""
        dialog = CaseLotDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            
            self.db.execute_query("""
                INSERT INTO cases (
                    name, manufacturer, caliber, quantity, lot_number,
                    purchase_date, case_capacity_gr_h2o, avg_weight_gr,
                    wall_thickness, material, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'],
                data['manufacturer'],
                data['caliber'],
                data['quantity'],
                data['lot_number'],
                data['purchase_date'],
                data['case_capacity'],
                data['avg_weight'],
                data['wall_thickness'],
                data['material'],
                data['notes']
            ))
            
            self.db.commit()
            self.load_data()
            QMessageBox.information(self, "✅ Lagt til", f"Lot '{data['name']}' er lagt til!")
    
    def log_firing(self):
        """Log firing session (increment times_fired)"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ingen valgt", "Velg et hylse-lot først!")
            return
        
        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        
        dialog = FiringLogDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()
            
            # Update times_fired
            current = self.db.execute_query(
                "SELECT times_fired FROM cases WHERE id = ?", (case_id,)
            )[0][0]
            
            new_fired = current + 1
            
            # Check if annealing due (every 3 firings for match brass)
            needs_anneal = (new_fired % 3 == 0 and new_fired > 0)
            
            self.db.execute_query("""
                UPDATE cases SET 
                    times_fired = ?,
                    needs_annealing = ?
                WHERE id = ?
            """, (new_fired, needs_anneal, case_id))
            
            # Log firing event
            self.db.execute_query("""
                INSERT INTO case_firing_log (
                    case_id, firing_date, rounds_fired, rifle_id,
                    ammo_profile_id, pressure_level, case_head_expansion_inch,
                    primer_condition, annealing_due, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                data['date'],
                data['rounds_fired'],
                data['rifle_id'],
                data['ammo_id'],
                data['pressure_level'],
                data['case_head_expansion'],
                data['primer_condition'],
                needs_anneal,
                data['notes']
            ))
            
            self.db.commit()
            self.load_data()
            
            msg = f"Skyting logget! Times fired: {new_fired}"
            if needs_anneal:
                msg += "\n\n⚠️ ANNEALING DUE! (hver 3. gang)"
            QMessageBox.information(self, "✅ Logget", msg)
    
    def log_annealing(self):
        """Log annealing session"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ingen valgt", "Velg et hylse-lot først!")
            return
        
        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        
        dialog = AnnealingLogDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()
            
            # Update last_annealed and reset needs_annealing
            self.db.execute_query("""
                UPDATE cases SET 
                    last_annealed = ?,
                    needs_annealing = 0
                WHERE id = ?
            """, (data['date'], case_id))
            
            # Log annealing event
            self.db.execute_query("""
                INSERT INTO case_annealing_log (
                    case_id, annealing_date, method, temperature_f,
                    time_seconds, templaq_verified, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                data['date'],
                data['method'],
                data['temperature'],
                data['time_seconds'],
                data['templaq_verified'],
                data['notes']
            ))
            
            self.db.commit()
            self.load_data()
            QMessageBox.information(self, "✅ Logget", "Annealing er logget!")
    
    def log_prep(self):
        """Log case prep (trimming, uniforming, etc.)"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ingen valgt", "Velg et hylse-lot først!")
            return
        
        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        
        dialog = PrepLogDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()
            
            # Update case prep flags
            if data['trimmed']:
                self.db.execute_query("""
                    UPDATE cases SET 
                        last_trimmed_date = ?,
                        trim_length_mm = ?
                    WHERE id = ?
                """, (data['date'], data['trim_length'], case_id))
            
            if data['primer_pocket_uniformed']:
                self.db.execute_query(
                    "UPDATE cases SET primer_pocket_uniformed = 1 WHERE id = ?",
                    (case_id,)
                )
            
            # Log prep event
            self.db.execute_query("""
                INSERT INTO case_prep_log (
                    case_id, prep_date, trimmed, trim_length_mm,
                    chamfered, deburred, primer_pocket_uniformed,
                    flash_hole_deburred, neck_turned, neck_thickness_final_mm,
                    weight_sorted, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                data['date'],
                data['trimmed'],
                data['trim_length'],
                data['chamfered'],
                data['deburred'],
                data['primer_pocket_uniformed'],
                data['flash_hole_deburred'],
                data['neck_turned'],
                data['neck_thickness'],
                data['weight_sorted'],
                data['notes']
            ))
            
            self.db.commit()
            self.load_data()
            QMessageBox.information(self, "✅ Logget", "Case prep er logget!")
    
    def add_measurement(self):
        """Add case measurements"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ingen valgt", "Velg et hylse-lot først!")
            return
        
        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        
        dialog = MeasurementDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()
            
            # Insert measurement
            self.db.execute_query("""
                INSERT INTO case_measurements (
                    case_id, measurement_date, case_length_mm,
                    neck_diameter_mm, neck_thickness_mm, base_diameter_mm,
                    shoulder_diameter_mm, case_weight_gr,
                    concentricity_tir_mm, measurement_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                data['date'],
                data['case_length'],
                data['neck_diameter'],
                data['neck_thickness'],
                data['base_diameter'],
                data['shoulder_diameter'],
                data['case_weight'],
                data['concentricity'],
                data['measurement_type'],
                data['notes']
            ))
            
            # Update avg_weight if provided
            if data['case_weight'] and data['case_weight'] > 0:
                self.db.execute_query(
                    "UPDATE cases SET avg_weight_gr = ? WHERE id = ?",
                    (data['case_weight'], case_id)
                )
            
            self.db.commit()
            QMessageBox.information(self, "✅ Lagret", "Måling er lagret!")
    
    def retire_cases(self):
        """Retire cases (splits, cracks, etc.)"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ingen valgt", "Velg et hylse-lot først!")
            return
        
        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        
        # Get current quantities
        case = self.db.execute_query(
            "SELECT name, quantity, retired_quantity FROM cases WHERE id = ?",
            (case_id,)
        )[0]
        
        name, qty, retired = case
        
        # Ask how many to retire
        from PyQt6.QtWidgets import QInputDialog
        retire_qty, ok = QInputDialog.getInt(
            self, "Retirer Hylser",
            f"Lot: {name}\nTilgjengelig: {qty}\n\nAntall å retire:",
            1, 1, qty
        )
        
        if ok:
            new_qty = qty - retire_qty
            new_retired = retired + retire_qty
            
            self.db.execute_query("""
                UPDATE cases SET
                    quantity = ?,
                    retired_quantity = ?
                WHERE id = ?
            """, (new_qty, new_retired, case_id))
            
            self.db.commit()
            self.load_data()
            QMessageBox.information(
                self, "✅ Retirert",
                f"{retire_qty} hylser retirert.\nGjenstående: {new_qty}"
            )
    
    def view_details(self, index):
        """View detailed history for selected case lot"""
        case_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = CaseDetailsDialog(self, case_id)
        dialog.exec()


class CaseLotDialog(QDialog):
    """Dialog for adding new case lot"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Nytt Hylse-Lot")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        # Basic info
        self.name = QLineEdit()
        self.name.setPlaceholderText("F.eks: Lapua 6.5 CM Batch 2024-01")
        form.addRow("Lot Navn:", self.name)
        
        self.lot_number = QLineEdit()
        self.lot_number.setPlaceholderText("Lot nummer fra produsent")
        form.addRow("Lot #:", self.lot_number)
        
        self.manufacturer = QComboBox()
        self.manufacturer.setEditable(True)
        self.manufacturer.addItems([
            "Lapua", "Peterson", "Alpha Munitions", "ADG",
            "Norma", "Hornady", "Federal", "Winchester", "Starline"
        ])
        form.addRow("Produsent:", self.manufacturer)
        
        self.caliber = QComboBox()
        self.caliber.setEditable(True)
        self.caliber.addItems([
            "6.5 Creedmoor", ".308 Winchester", ".223 Remington",
            "6.5x55 Swedish", ".30-06 Springfield", "6mm Creedmoor"
        ])
        form.addRow("Kaliber:", self.caliber)
        
        self.material = QComboBox()
        self.material.addItems(["Brass", "Nickel Brass", "Steel"])
        form.addRow("Material:", self.material)
        
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000)
        self.quantity.setValue(100)
        form.addRow("Antall:", self.quantity)
        
        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setCalendarPopup(True)
        form.addRow("Kjøpsdato:", self.purchase_date)
        
        # Technical specs
        self.case_capacity = QDoubleSpinBox()
        self.case_capacity.setRange(0, 100)
        self.case_capacity.setSuffix(" gr H2O")
        self.case_capacity.setDecimals(1)
        self.case_capacity.setSpecialValueText("Ukjent")
        form.addRow("Case Capacity:", self.case_capacity)
        
        self.avg_weight = QDoubleSpinBox()
        self.avg_weight.setRange(0, 300)
        self.avg_weight.setSuffix(" gr")
        self.avg_weight.setDecimals(1)
        self.avg_weight.setSpecialValueText("Ukjent")
        form.addRow("Avg Weight:", self.avg_weight)
        
        self.wall_thickness = QComboBox()
        self.wall_thickness.addItems(["-", "Thin", "Medium", "Thick", "Extra Thick"])
        form.addRow("Wall Thickness:", self.wall_thickness)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notater om dette hylse-lotet...")
        form.addRow("Notater:", self.notes)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Lagre")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'name': self.name.text(),
            'lot_number': self.lot_number.text(),
            'manufacturer': self.manufacturer.currentText(),
            'caliber': self.caliber.currentText(),
            'material': self.material.currentText(),
            'quantity': self.quantity.value(),
            'purchase_date': self.purchase_date.date().toString("yyyy-MM-dd"),
            'case_capacity': self.case_capacity.value() if self.case_capacity.value() > 0 else None,
            'avg_weight': self.avg_weight.value() if self.avg_weight.value() > 0 else None,
            'wall_thickness': self.wall_thickness.currentText() if self.wall_thickness.currentIndex() > 0 else None,
            'notes': self.notes.toPlainText()
        }


class FiringLogDialog(QDialog):
    """Dialog for logging firing session"""
    
    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.db = get_database()
        self.setWindowTitle("🔥 Logg Skyting")
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addRow("Dato:", self.date)
        
        self.rounds_fired = QSpinBox()
        self.rounds_fired.setRange(1, 100)
        self.rounds_fired.setValue(5)
        layout.addRow("Antall skudd:", self.rounds_fired)
        
        # Rifle selection
        self.rifle_combo = QComboBox()
        rifles = self.db.execute_query("SELECT id, name FROM rifles ORDER BY name")
        self.rifle_combo.addItem("-", None)
        for rifle_id, name in rifles:
            self.rifle_combo.addItem(name, rifle_id)
        layout.addRow("Rifle:", self.rifle_combo)
        
        # Ammo profile
        self.ammo_combo = QComboBox()
        ammos = self.db.execute_query("SELECT id, name FROM ammo_profiles ORDER BY name")
        self.ammo_combo.addItem("-", None)
        for ammo_id, name in ammos:
            self.ammo_combo.addItem(name, ammo_id)
        layout.addRow("Ammunisjon:", self.ammo_combo)
        
        self.pressure_level = QComboBox()
        self.pressure_level.addItems(["-", "Low", "Medium", "High", "Max"])
        layout.addRow("Trykkfnivå:", self.pressure_level)
        
        self.case_head_expansion = QDoubleSpinBox()
        self.case_head_expansion.setRange(0, 0.001)
        self.case_head_expansion.setSuffix(' "')
        self.case_head_expansion.setDecimals(5)
        self.case_head_expansion.setSpecialValueText("Ikke målt")
        layout.addRow("Case Head Expansion:", self.case_head_expansion)
        
        self.primer_condition = QComboBox()
        self.primer_condition.addItems(["Good", "Flattened", "Cratered", "Pierced"])
        layout.addRow("Primer Condition:", self.primer_condition)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        layout.addRow("Notater:", self.notes)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Logg")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
    
    def get_data(self):
        return {
            'date': self.date.date().toString("yyyy-MM-dd"),
            'rounds_fired': self.rounds_fired.value(),
            'rifle_id': self.rifle_combo.currentData(),
            'ammo_id': self.ammo_combo.currentData(),
            'pressure_level': self.pressure_level.currentText() if self.pressure_level.currentIndex() > 0 else None,
            'case_head_expansion': self.case_head_expansion.value() if self.case_head_expansion.value() > 0 else None,
            'primer_condition': self.primer_condition.currentText(),
            'notes': self.notes.toPlainText()
        }


class AnnealingLogDialog(QDialog):
    """Dialog for logging annealing"""
    
    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.setWindowTitle("♨️ Logg Annealing")
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addRow("Dato:", self.date)
        
        self.method = QComboBox()
        self.method.addItems(["Flame (torch)", "Induction (Annie/EP)", "AMP Annealer"])
        layout.addRow("Metode:", self.method)
        
        self.temperature = QSpinBox()
        self.temperature.setRange(0, 900)
        self.temperature.setSuffix(" °F")
        self.temperature.setValue(750)
        self.temperature.setSpecialValueText("Ukjent")
        layout.addRow("Temperatur:", self.temperature)
        
        self.time_seconds = QDoubleSpinBox()
        self.time_seconds.setRange(0, 60)
        self.time_seconds.setSuffix(" sec")
        self.time_seconds.setDecimals(1)
        self.time_seconds.setValue(3.0)
        self.time_seconds.setSpecialValueText("Auto")
        layout.addRow("Tid:", self.time_seconds)
        
        self.templaq_verified = QCheckBox("Templaq paint verifisert")
        layout.addRow("", self.templaq_verified)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        layout.addRow("Notater:", self.notes)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Logg")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
    
    def get_data(self):
        return {
            'date': self.date.date().toString("yyyy-MM-dd"),
            'method': self.method.currentText(),
            'temperature': self.temperature.value() if self.temperature.value() > 0 else None,
            'time_seconds': self.time_seconds.value() if self.time_seconds.value() > 0 else None,
            'templaq_verified': self.templaq_verified.isChecked(),
            'notes': self.notes.toPlainText()
        }


class PrepLogDialog(QDialog):
    """Dialog for logging case prep"""
    
    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.setWindowTitle("🔧 Logg Case Prep")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Date
        date_layout = QFormLayout()
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        date_layout.addRow("Dato:", self.date)
        layout.addLayout(date_layout)
        
        # Checkboxes for prep steps
        prep_group = QGroupBox("Prep Steps")
        prep_layout = QVBoxLayout()
        
        self.trimmed = QCheckBox("Trimmed")
        self.trimmed.toggled.connect(self.toggle_trim_length)
        prep_layout.addWidget(self.trimmed)
        
        trim_layout = QFormLayout()
        self.trim_length = QDoubleSpinBox()
        self.trim_length.setRange(0, 100)
        self.trim_length.setSuffix(" mm")
        self.trim_length.setDecimals(2)
        self.trim_length.setEnabled(False)
        trim_layout.addRow("  Trim Length:", self.trim_length)
        prep_layout.addLayout(trim_layout)
        
        self.chamfered = QCheckBox("Chamfered (inside/outside)")
        prep_layout.addWidget(self.chamfered)
        
        self.deburred = QCheckBox("Deburred (flash hole)")
        prep_layout.addWidget(self.deburred)
        
        self.primer_pocket_uniformed = QCheckBox("Primer pocket uniformed")
        prep_layout.addWidget(self.primer_pocket_uniformed)
        
        self.flash_hole_deburred = QCheckBox("Flash hole deburred")
        prep_layout.addWidget(self.flash_hole_deburred)
        
        self.neck_turned = QCheckBox("Neck turned")
        self.neck_turned.toggled.connect(self.toggle_neck_thickness)
        prep_layout.addWidget(self.neck_turned)
        
        neck_layout = QFormLayout()
        self.neck_thickness = QDoubleSpinBox()
        self.neck_thickness.setRange(0, 5)
        self.neck_thickness.setSuffix(" mm")
        self.neck_thickness.setDecimals(3)
        self.neck_thickness.setEnabled(False)
        neck_layout.addRow("  Final Neck Thickness:", self.neck_thickness)
        prep_layout.addLayout(neck_layout)
        
        self.weight_sorted = QCheckBox("Weight sorted")
        prep_layout.addWidget(self.weight_sorted)
        
        prep_group.setLayout(prep_layout)
        layout.addWidget(prep_group)
        
        # Notes
        notes_layout = QFormLayout()
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        notes_layout.addRow("Notater:", self.notes)
        layout.addLayout(notes_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Logg")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def toggle_trim_length(self, checked):
        self.trim_length.setEnabled(checked)
    
    def toggle_neck_thickness(self, checked):
        self.neck_thickness.setEnabled(checked)
    
    def get_data(self):
        return {
            'date': self.date.date().toString("yyyy-MM-dd"),
            'trimmed': self.trimmed.isChecked(),
            'trim_length': self.trim_length.value() if self.trimmed.isChecked() else None,
            'chamfered': self.chamfered.isChecked(),
            'deburred': self.deburred.isChecked(),
            'primer_pocket_uniformed': self.primer_pocket_uniformed.isChecked(),
            'flash_hole_deburred': self.flash_hole_deburred.isChecked(),
            'neck_turned': self.neck_turned.isChecked(),
            'neck_thickness': self.neck_thickness.value() if self.neck_turned.isChecked() else None,
            'weight_sorted': self.weight_sorted.isChecked(),
            'notes': self.notes.toPlainText()
        }


class MeasurementDialog(QDialog):
    """Dialog for adding case measurements"""
    
    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.setWindowTitle("📏 Hylse Målinger")
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addRow("Dato:", self.date)
        
        self.measurement_type = QComboBox()
        self.measurement_type.addItems(["new", "fired", "sized", "after_trim"])
        layout.addRow("Type måling:", self.measurement_type)
        
        # Measurements
        self.case_length = QDoubleSpinBox()
        self.case_length.setRange(0, 100)
        self.case_length.setSuffix(" mm")
        self.case_length.setDecimals(2)
        self.case_length.setSpecialValueText("Ikke målt")
        layout.addRow("Case Length:", self.case_length)
        
        self.neck_diameter = QDoubleSpinBox()
        self.neck_diameter.setRange(0, 20)
        self.neck_diameter.setSuffix(" mm")
        self.neck_diameter.setDecimals(3)
        self.neck_diameter.setSpecialValueText("Ikke målt")
        layout.addRow("Neck Diameter:", self.neck_diameter)
        
        self.neck_thickness = QDoubleSpinBox()
        self.neck_thickness.setRange(0, 5)
        self.neck_thickness.setSuffix(" mm")
        self.neck_thickness.setDecimals(3)
        self.neck_thickness.setSpecialValueText("Ikke målt")
        layout.addRow("Neck Thickness:", self.neck_thickness)
        
        self.base_diameter = QDoubleSpinBox()
        self.base_diameter.setRange(0, 20)
        self.base_diameter.setSuffix(" mm")
        self.base_diameter.setDecimals(3)
        self.base_diameter.setSpecialValueText("Ikke målt")
        layout.addRow("Base Diameter:", self.base_diameter)
        
        self.shoulder_diameter = QDoubleSpinBox()
        self.shoulder_diameter.setRange(0, 20)
        self.shoulder_diameter.setSuffix(" mm")
        self.shoulder_diameter.setDecimals(3)
        self.shoulder_diameter.setSpecialValueText("Ikke målt")
        layout.addRow("Shoulder Diameter:", self.shoulder_diameter)
        
        self.case_weight = QDoubleSpinBox()
        self.case_weight.setRange(0, 300)
        self.case_weight.setSuffix(" gr")
        self.case_weight.setDecimals(1)
        self.case_weight.setSpecialValueText("Ikke målt")
        layout.addRow("Case Weight:", self.case_weight)
        
        self.concentricity = QDoubleSpinBox()
        self.concentricity.setRange(0, 1)
        self.concentricity.setSuffix(" mm TIR")
        self.concentricity.setDecimals(3)
        self.concentricity.setSpecialValueText("Ikke målt")
        layout.addRow("Concentricity:", self.concentricity)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        layout.addRow("Notater:", self.notes)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Lagre")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
    
    def get_data(self):
        return {
            'date': self.date.date().toString("yyyy-MM-dd"),
            'measurement_type': self.measurement_type.currentText(),
            'case_length': self.case_length.value() if self.case_length.value() > 0 else None,
            'neck_diameter': self.neck_diameter.value() if self.neck_diameter.value() > 0 else None,
            'neck_thickness': self.neck_thickness.value() if self.neck_thickness.value() > 0 else None,
            'base_diameter': self.base_diameter.value() if self.base_diameter.value() > 0 else None,
            'shoulder_diameter': self.shoulder_diameter.value() if self.shoulder_diameter.value() > 0 else None,
            'case_weight': self.case_weight.value() if self.case_weight.value() > 0 else None,
            'concentricity': self.concentricity.value() if self.concentricity.value() > 0 else None,
            'notes': self.notes.toPlainText()
        }


class CaseDetailsDialog(QDialog):
    """Dialog showing detailed history for a case lot"""
    
    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.db = get_database()
        self.setWindowTitle("📋 Hylse Detaljer")
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Case info header
        case = self.db.execute_query(
            "SELECT name, manufacturer, caliber, quantity, times_fired FROM cases WHERE id = ?",
            (self.case_id,)
        )[0]
        
        header = QLabel(f"<h2>{case[0]}</h2>")
        header.setStyleSheet("color: #2c3e50;")
        layout.addWidget(header)
        
        info = QLabel(
            f"<b>Produsent:</b> {case[1]} | "
            f"<b>Kaliber:</b> {case[2]} | "
            f"<b>Antall:</b> {case[3]} | "
            f"<b>Times Fired:</b> {case[4]}"
        )
        layout.addWidget(info)
        
        # Tabs for different history types
        tabs = QTabWidget()
        
        tabs.addTab(self.create_firing_history_tab(), "🔥 Firing History")
        tabs.addTab(self.create_annealing_history_tab(), "♨️ Annealing History")
        tabs.addTab(self.create_prep_history_tab(), "🔧 Prep History")
        tabs.addTab(self.create_measurements_tab(), "📏 Målinger")
        
        layout.addWidget(tabs)
        
        # Close button
        btn_close = QPushButton("✖️ Lukk")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
    
    def create_firing_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        firings = self.db.execute_query("""
            SELECT firing_date, rounds_fired, pressure_level,
                   case_head_expansion_inch, primer_condition, notes
            FROM case_firing_log
            WHERE case_id = ?
            ORDER BY firing_date DESC
        """, (self.case_id,))
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Dato", "Skudd", "Trykk", "Case Head Exp", "Primer", "Notater"
        ])
        table.setRowCount(len(firings))
        
        for i, firing in enumerate(firings):
            for j, value in enumerate(firing):
                table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget
    
    def create_annealing_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        annealings = self.db.execute_query("""
            SELECT annealing_date, method, temperature_f, time_seconds,
                   templaq_verified, notes
            FROM case_annealing_log
            WHERE case_id = ?
            ORDER BY annealing_date DESC
        """, (self.case_id,))
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Dato", "Metode", "Temp (°F)", "Tid (s)", "Templaq", "Notater"
        ])
        table.setRowCount(len(annealings))
        
        for i, annealing in enumerate(annealings):
            for j, value in enumerate(annealing):
                if j == 4:  # Templaq boolean
                    table.setItem(i, j, QTableWidgetItem("✅" if value else "❌"))
                else:
                    table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget
    
    def create_prep_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        preps = self.db.execute_query("""
            SELECT prep_date, trimmed, trim_length_mm, chamfered,
                   primer_pocket_uniformed, neck_turned, notes
            FROM case_prep_log
            WHERE case_id = ?
            ORDER BY prep_date DESC
        """, (self.case_id,))
        
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Dato", "Trimmed", "Length", "Chamfered", "Pocket", "Neck Turned", "Notater"
        ])
        table.setRowCount(len(preps))
        
        for i, prep in enumerate(preps):
            for j, value in enumerate(prep):
                if j in [1, 3, 4, 5]:  # Boolean fields
                    table.setItem(i, j, QTableWidgetItem("✅" if value else "❌"))
                else:
                    table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget
    
    def create_measurements_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        measurements = self.db.execute_query("""
            SELECT measurement_date, measurement_type, case_length_mm,
                   neck_diameter_mm, base_diameter_mm, case_weight_gr
            FROM case_measurements
            WHERE case_id = ?
            ORDER BY measurement_date DESC
        """, (self.case_id,))
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Dato", "Type", "Length (mm)", "Neck (mm)", "Base (mm)", "Weight (gr)"
        ])
        table.setRowCount(len(measurements))
        
        for i, measurement in enumerate(measurements):
            for j, value in enumerate(measurement):
                table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget
