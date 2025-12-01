"""
Historical Analysis System
View trends, compare sessions, find patterns
For the OCD shooters who track EVERYTHING! 📊
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QGroupBox, QComboBox, QTabWidget, QLineEdit,
                            QDateEdit, QCheckBox, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json


class HistoricalAnalysisViewer(QWidget):
    """
    View and analyze historical load development data
    Find patterns, track improvements, compare sessions
    """
    
    session_selected = pyqtSignal(str)  # load_id
    
    def __init__(self):
        super().__init__()
        self.sessions = []  # Will load from database
        self.init_ui()
        self.load_sample_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QLabel("📚 Historical Analysis & Trends")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)
        
        # Filters
        filter_group = QGroupBox("🔍 Filters")
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)
        
        # Caliber filter
        filter_layout.addWidget(QLabel("Caliber:"))
        self.filter_caliber = QComboBox()
        self.filter_caliber.addItem("All")
        self.filter_caliber.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_caliber)
        
        # Date range
        filter_layout.addWidget(QLabel("From:"))
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setDate(QDate.currentDate().addDays(-90))
        self.filter_date_from.setCalendarPopup(True)
        self.filter_date_from.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_date_from)
        
        filter_layout.addWidget(QLabel("To:"))
        self.filter_date_to = QDateEdit()
        self.filter_date_to.setDate(QDate.currentDate())
        self.filter_date_to.setCalendarPopup(True)
        self.filter_date_to.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_date_to)
        
        # Powder filter
        filter_layout.addWidget(QLabel("Powder:"))
        self.filter_powder = QComboBox()
        self.filter_powder.addItem("All")
        self.filter_powder.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_powder)
        
        # Bullet filter
        filter_layout.addWidget(QLabel("Bullet:"))
        self.filter_bullet = QComboBox()
        self.filter_bullet.addItem("All")
        self.filter_bullet.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_bullet)
        
        filter_layout.addStretch()
        
        btn_reset = QPushButton("Reset Filters")
        btn_reset.clicked.connect(self.reset_filters)
        filter_layout.addWidget(btn_reset)
        
        layout.addWidget(filter_group)
        
        # Main content: Splitter with list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # LEFT: Sessions list
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        left_layout.addWidget(QLabel("<b>📋 Sessions</b>"))
        
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(7)
        self.sessions_table.setHorizontalHeaderLabels([
            "Date", "Load ID", "Caliber", "Powder/Charge", "Velocity", "SD", "MOA"
        ])
        self.sessions_table.currentCellChanged.connect(self.on_session_selected)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.sessions_table)
        
        splitter.addWidget(left_widget)
        
        # RIGHT: Session details
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("<b>📊 Session Details</b>"))
        
        self.detail_tabs = QTabWidget()
        right_layout.addWidget(self.detail_tabs)
        
        # Tab 1: Summary
        self.tab_summary = QTextEdit()
        self.tab_summary.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_summary, "Summary")
        
        # Tab 2: Environmental
        self.tab_environmental = QTextEdit()
        self.tab_environmental.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_environmental, "Environmental")
        
        # Tab 3: Components
        self.tab_components = QTextEdit()
        self.tab_components.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_components, "Components")
        
        # Tab 4: Results
        self.tab_results = QTextEdit()
        self.tab_results.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_results, "Results")
        
        # Tab 5: Notes
        self.tab_notes = QTextEdit()
        self.tab_notes.setReadOnly(True)
        self.detail_tabs.addTab(self.tab_notes, "Notes")
        
        # Comparison buttons
        btn_layout = QHBoxLayout()
        
        self.btn_compare = QPushButton("📊 Compare Selected Sessions")
        self.btn_compare.clicked.connect(self.compare_sessions)
        btn_layout.addWidget(self.btn_compare)
        
        self.btn_trends = QPushButton("📈 Show Trends")
        self.btn_trends.clicked.connect(self.show_trends)
        btn_layout.addWidget(self.btn_trends)
        
        self.btn_export = QPushButton("📄 Export Selection")
        self.btn_export.clicked.connect(self.export_selection)
        btn_layout.addWidget(self.btn_export)
        
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(right_widget)
        
        # Set splitter sizes
        splitter.setSizes([400, 600])
    
    def load_sample_data(self):
        """Load sample historical data"""
        # Sample data for demonstration
        self.sessions = [
            {
                'load_id': 'LD_20241101_001',
                'date': '2024-11-01',
                'caliber': '6.5 Creedmoor',
                'powder': 'Vihtavuori N140',
                'charge': 42.0,
                'velocity': 2680,
                'sd': 6.2,
                'es': 15,
                'moa': 0.75,
                'notes': 'Good load, minimal pressure signs'
            },
            {
                'load_id': 'LD_20241108_002',
                'date': '2024-11-08',
                'caliber': '6.5 Creedmoor',
                'powder': 'Vihtavuori N140',
                'charge': 42.5,
                'velocity': 2710,
                'sd': 8.1,
                'es': 22,
                'moa': 0.85,
                'notes': 'Slightly high ES, still acceptable'
            },
            {
                'load_id': 'LD_20241115_003',
                'date': '2024-11-15',
                'caliber': '6.5 Creedmoor',
                'powder': 'Vihtavuori N140',
                'charge': 42.0,
                'velocity': 2665,
                'sd': 5.8,
                'es': 14,
                'moa': 0.68,
                'notes': 'Best so far! Verified at 300m'
            },
        ]
        
        # Populate filter dropdowns
        calibers = set(s['caliber'] for s in self.sessions)
        powders = set(s['powder'] for s in self.sessions)
        
        self.filter_caliber.clear()
        self.filter_caliber.addItem("All")
        self.filter_caliber.addItems(sorted(calibers))
        
        self.filter_powder.clear()
        self.filter_powder.addItem("All")
        self.filter_powder.addItems(sorted(powders))
        
        self.apply_filters()
    
    def apply_filters(self):
        """Apply current filters to sessions list"""
        filtered = self.sessions
        
        # Filter by caliber
        if self.filter_caliber.currentText() != "All":
            filtered = [s for s in filtered if s['caliber'] == self.filter_caliber.currentText()]
        
        # Filter by powder
        if self.filter_powder.currentText() != "All":
            filtered = [s for s in filtered if s['powder'] == self.filter_powder.currentText()]
        
        # Filter by date range
        date_from = self.filter_date_from.date().toPyDate()
        date_to = self.filter_date_to.date().toPyDate()
        
        filtered = [s for s in filtered 
                   if date_from <= datetime.strptime(s['date'], '%Y-%m-%d').date() <= date_to]
        
        self.populate_sessions_table(filtered)
    
    def populate_sessions_table(self, sessions: List[Dict]):
        """Populate sessions table"""
        self.sessions_table.setRowCount(0)
        
        for session in sessions:
            row = self.sessions_table.rowCount()
            self.sessions_table.insertRow(row)
            
            self.sessions_table.setItem(row, 0, QTableWidgetItem(session['date']))
            self.sessions_table.setItem(row, 1, QTableWidgetItem(session['load_id']))
            self.sessions_table.setItem(row, 2, QTableWidgetItem(session['caliber']))
            
            powder_charge = f"{session['powder']} / {session['charge']:.1f}gr"
            self.sessions_table.setItem(row, 3, QTableWidgetItem(powder_charge))
            
            self.sessions_table.setItem(row, 4, QTableWidgetItem(f"{session['velocity']} fps"))
            
            # Color code SD
            sd_item = QTableWidgetItem(f"{session['sd']:.1f}")
            if session['sd'] < 6:
                sd_item.setBackground(QColor("#d5f4e6"))  # Green
            elif session['sd'] < 10:
                sd_item.setBackground(QColor("#fff9c4"))  # Yellow
            else:
                sd_item.setBackground(QColor("#ffcccc"))  # Red
            self.sessions_table.setItem(row, 5, sd_item)
            
            # Color code MOA
            moa_item = QTableWidgetItem(f"{session['moa']:.2f}")
            if session['moa'] < 0.75:
                moa_item.setBackground(QColor("#d5f4e6"))  # Green
            elif session['moa'] < 1.0:
                moa_item.setBackground(QColor("#fff9c4"))  # Yellow
            else:
                moa_item.setBackground(QColor("#ffcccc"))  # Red
            self.sessions_table.setItem(row, 6, moa_item)
        
        self.sessions_table.resizeColumnsToContents()
    
    def on_session_selected(self, row, col, prev_row, prev_col):
        """Handle session selection"""
        if row < 0:
            return
        
        load_id_item = self.sessions_table.item(row, 1)
        if not load_id_item:
            return
        
        load_id = load_id_item.text()
        
        # Find session data
        session = next((s for s in self.sessions if s['load_id'] == load_id), None)
        if not session:
            return
        
        self.display_session_details(session)
    
    def display_session_details(self, session: Dict):
        """Display detailed session information"""
        # Summary tab
        summary_html = f"""
        <h2>{session['load_id']}</h2>
        <p><b>Date:</b> {session['date']}</p>
        <p><b>Caliber:</b> {session['caliber']}</p>
        
        <h3>Performance</h3>
        <table border='1' cellpadding='5' style='border-collapse: collapse;'>
            <tr><td><b>Average Velocity</b></td><td>{session['velocity']} fps</td></tr>
            <tr><td><b>Standard Deviation</b></td><td>{session['sd']:.1f} fps</td></tr>
            <tr><td><b>Extreme Spread</b></td><td>{session['es']} fps</td></tr>
            <tr><td><b>Accuracy</b></td><td>{session['moa']:.2f} MOA</td></tr>
        </table>
        
        <h3>Components</h3>
        <p><b>Powder:</b> {session['powder']} @ {session['charge']:.1f} gr</p>
        """
        self.tab_summary.setHtml(summary_html)
        
        # Notes tab
        self.tab_notes.setPlainText(session['notes'])
        
        # TODO: Load full session data from database for other tabs
    
    def reset_filters(self):
        """Reset all filters"""
        self.filter_caliber.setCurrentIndex(0)
        self.filter_powder.setCurrentIndex(0)
        self.filter_bullet.setCurrentIndex(0)
        self.filter_date_from.setDate(QDate.currentDate().addDays(-90))
        self.filter_date_to.setDate(QDate.currentDate())
    
    def compare_sessions(self):
        """Compare multiple selected sessions"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Compare Sessions",
            "📊 Comparison feature coming soon!\n\n" +
            "Will show:\n" +
            "• Side-by-side component differences\n" +
            "• Performance trends\n" +
            "• Environmental impact analysis\n" +
            "• Component correlation (which powder/bullet combo works best?)"
        )
    
    def show_trends(self):
        """Show trends over time"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Show Trends",
            "📈 Trends analysis coming soon!\n\n" +
            "Will show:\n" +
            "• SD/ES trends over time\n" +
            "• Velocity consistency\n" +
            "• Barrel life impact (accuracy vs round count)\n" +
            "• Environmental correlation (temp vs velocity)\n" +
            "• Component lot tracking (did new powder lot change anything?)"
        )
    
    def export_selection(self):
        """Export selected sessions"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Export",
            "📄 Export feature coming soon!\n\n" +
            "Will export to:\n" +
            "• Excel (.xlsx)\n" +
            "• CSV\n" +
            "• PDF report"
        )


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    viewer = HistoricalAnalysisViewer()
    viewer.show()
    viewer.resize(1200, 700)
    
    sys.exit(app.exec())
