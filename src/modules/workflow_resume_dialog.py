"""
Resume Workflow Dialog
Ask user if they want to resume saved workflows
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QTextEdit, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from datetime import datetime
from typing import List, Optional
from src.modules.workflow_state import WorkflowState, WorkflowStateManager


class WorkflowResumeItem(QListWidgetItem):
    """List item for workflow resume"""
    
    def __init__(self, state: WorkflowState):
        super().__init__()
        self.state = state
        
        # Format display text
        dt = datetime.fromisoformat(state.last_updated)
        time_str = dt.strftime("%Y-%m-%d %H:%M")
        
        self.setText(f"🔄 {state.workflow_name}\n    Last updated: {time_str}")
        self.setToolTip(f"Workflow: {state.workflow_id}\nSaved: {time_str}")


class WorkflowResumeDialog(QDialog):
    """
    Dialog to resume saved workflows
    Shown on startup if saved states exist
    """
    
    workflow_selected = pyqtSignal(str)  # workflow_id
    
    def __init__(self, state_manager: WorkflowStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.selected_workflow_id = None
        
        self.setWindowTitle("Resume Workflow?")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        self.init_ui()
        self.load_workflows()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("🔄 Resume Saved Workflows?")
        header_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(header_label)
        
        desc = QLabel(
            "Du har aktive workflows som ikke er fullført.\n"
            "Vil du fortsette der du slapp?"
        )
        desc.setStyleSheet("color: #7f8c8d; padding: 5px; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # List of workflows
        workflow_group = QGroupBox("📋 Active Workflows")
        workflow_layout = QVBoxLayout()
        
        self.workflow_list = QListWidget()
        self.workflow_list.setStyleSheet("""
            QListWidget {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                margin: 3px;
                background-color: white;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
        """)
        self.workflow_list.currentItemChanged.connect(self.on_workflow_selected)
        workflow_layout.addWidget(self.workflow_list)
        
        workflow_group.setLayout(workflow_layout)
        layout.addWidget(workflow_group)
        
        # Details panel
        details_group = QGroupBox("📊 Workflow Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        # Resume button
        self.btn_resume = QPushButton("✅ Resume Selected")
        self.btn_resume.setEnabled(False)
        self.btn_resume.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_resume.clicked.connect(self.resume_workflow)
        btn_layout.addWidget(self.btn_resume)
        
        # Clear button
        btn_clear = QPushButton("🗑️ Clear Selected")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_clear.clicked.connect(self.clear_workflow)
        btn_layout.addWidget(btn_clear)
        
        # Clear all button
        btn_clear_all = QPushButton("🗑️ Clear All")
        btn_clear_all.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_clear_all.clicked.connect(self.clear_all_workflows)
        btn_layout.addWidget(btn_clear_all)
        
        btn_layout.addStretch()
        
        # Start fresh button
        btn_fresh = QPushButton("🆕 Start Fresh")
        btn_fresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_fresh.clicked.connect(self.reject)
        btn_layout.addWidget(btn_fresh)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_workflows(self):
        """Load active workflows"""
        active_states = self.state_manager.get_all_active()
        
        # Sort by last updated (newest first)
        active_states.sort(key=lambda s: s.last_updated, reverse=True)
        
        for state in active_states:
            item = WorkflowResumeItem(state)
            self.workflow_list.addItem(item)
        
        if active_states:
            self.workflow_list.setCurrentRow(0)
    
    def on_workflow_selected(self, current: Optional[WorkflowResumeItem], previous):
        """When workflow is selected"""
        if not current:
            self.btn_resume.setEnabled(False)
            self.details_text.clear()
            return
        
        self.btn_resume.setEnabled(True)
        
        # Show details
        state = current.state
        
        # Format data for display
        html = f"""
        <h3 style='color: #2c3e50;'>{state.workflow_name}</h3>
        <p><b>Workflow ID:</b> {state.workflow_id}</p>
        <p><b>Created:</b> {datetime.fromisoformat(state.timestamp).strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><b>Last Updated:</b> {datetime.fromisoformat(state.last_updated).strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <h4 style='color: #3498db;'>Saved State:</h4>
        <pre style='background-color: #ecf0f1; padding: 10px; border-radius: 5px;'>
        """
        
        # Format state data nicely
        for key, value in state.data.items():
            if isinstance(value, list) and len(value) > 5:
                html += f"{key}: [{len(value)} items]\n"
            else:
                html += f"{key}: {value}\n"
        
        html += "</pre>"
        
        self.details_text.setHtml(html)
        self.selected_workflow_id = state.workflow_id
    
    def resume_workflow(self):
        """Resume selected workflow"""
        current = self.workflow_list.currentItem()
        if not current:
            return
        
        self.workflow_selected.emit(current.state.workflow_id)
        self.accept()
    
    def clear_workflow(self):
        """Clear selected workflow state"""
        current = self.workflow_list.currentItem()
        if not current:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear Workflow?",
            f"Er du sikker på at du vil slette saved state for:\n\n{current.state.workflow_name}\n\nDette kan ikke angres!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.state_manager.clear_state(current.state.workflow_id)
            
            # Remove from list
            row = self.workflow_list.currentRow()
            self.workflow_list.takeItem(row)
            
            # Check if list is empty
            if self.workflow_list.count() == 0:
                QMessageBox.information(
                    self,
                    "No Workflows",
                    "Ingen flere saved workflows.\n\nStarting fresh!"
                )
                self.reject()
    
    def clear_all_workflows(self):
        """Clear all workflow states"""
        reply = QMessageBox.question(
            self,
            "Clear All Workflows?",
            "Er du sikker på at du vil slette ALLE saved workflows?\n\nDette kan ikke angres!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.state_manager.clear_all()
            self.workflow_list.clear()
            
            QMessageBox.information(
                self,
                "Cleared",
                "Alle workflow states er slettet.\n\nStarting fresh!"
            )
            self.reject()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test state manager with some data
    manager = WorkflowStateManager()
    manager.save_state(
        "ladder_test",
        "Ladder Test - .308 Win",
        {
            'rifle': 'Tikka T3x .308',
            'charge_range': [42.0, 45.0],
            'shots_logged': 8,
            'last_velocity': 2745
        }
    )
    manager.save_state(
        "ocw_test",
        "OCW Test - 6.5 Creedmoor",
        {
            'rifle': 'Bergara B-14',
            'charges': [43.0, 43.3, 43.6],
            'groups_fired': 2
        }
    )
    
    dialog = WorkflowResumeDialog(manager)
    
    def on_workflow_selected(workflow_id):
        from src.logging_config import configure_logging, get_logger
        configure_logging()
        logger = get_logger(__name__)
        logger.info("User wants to resume: %s", workflow_id)
    
    dialog.workflow_selected.connect(on_workflow_selected)
    
    result = dialog.exec()
    from src.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Dialog result: %s", 'Accepted' if result else 'Rejected')
    
    sys.exit(0)
