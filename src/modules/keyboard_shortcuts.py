"""
Keyboard Shortcuts Manager
Expert mode shortcuts for power users
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Callable, Optional
from src.modules.user_mode import UserModeManager


class KeyboardShortcutsManager(QObject):
    """
    Manages keyboard shortcuts for expert mode
    Automatically enables/disables based on user mode
    """
    
    shortcut_triggered = pyqtSignal(str)  # shortcut_id
    
    def __init__(self, parent_widget: QWidget, mode_manager: UserModeManager):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.mode_manager = mode_manager
        self.shortcuts: Dict[str, QShortcut] = {}
        
        # Connect to mode changes
        self.mode_manager.mode_changed.connect(self.on_mode_changed)
        
        self._register_default_shortcuts()
        self._update_shortcuts_enabled()
    
    def _register_default_shortcuts(self):
        """Register all default shortcuts"""
        
        # Global shortcuts
        self.register_shortcut(
            "new_test",
            "Ctrl+N",
            "Create new test"
        )
        
        self.register_shortcut(
            "save_state",
            "Ctrl+S",
            "Save current workflow state"
        )
        
        self.register_shortcut(
            "resume_workflow",
            "Ctrl+R",
            "Resume last workflow"
        )
        
        self.register_shortcut(
            "quick_search",
            "Ctrl+F",
            "Quick search"
        )
        
        self.register_shortcut(
            "workflow_hub",
            "Ctrl+H",
            "Go to Workflow Hub"
        )
        
        # Category shortcuts (Ctrl+1-5)
        self.register_shortcut(
            "category_load_dev",
            "Ctrl+1",
            "Load Development workflows"
        )
        
        self.register_shortcut(
            "category_testing",
            "Ctrl+2",
            "Testing & Validation workflows"
        )
        
        self.register_shortcut(
            "category_production",
            "Ctrl+3",
            "Production & QC workflows"
        )
        
        self.register_shortcut(
            "category_ballistics",
            "Ctrl+4",
            "Ballistics & Field workflows"
        )
        
        self.register_shortcut(
            "category_database",
            "Ctrl+5",
            "Database & Setup workflows"
        )
        
        # Workflow shortcuts
        self.register_shortcut(
            "ladder_test",
            "Ctrl+L",
            "Open Ladder Test"
        )
        
        self.register_shortcut(
            "ocw_test",
            "Ctrl+O",
            "Open OCW Test"
        )
        
        self.register_shortcut(
            "batch_qc",
            "Ctrl+Q",
            "Open Batch QC"
        )
        
        # Data entry shortcuts
        self.register_shortcut(
            "add_shot",
            "Ctrl+Enter",
            "Add shot (in live testing)"
        )
        
        self.register_shortcut(
            "clear_data",
            "Ctrl+Shift+Del",
            "Clear current data"
        )
        
        # Navigation shortcuts
        self.register_shortcut(
            "next_charge",
            "Ctrl+Right",
            "Next charge weight"
        )
        
        self.register_shortcut(
            "prev_charge",
            "Ctrl+Left",
            "Previous charge weight"
        )
        
        # View shortcuts
        self.register_shortcut(
            "toggle_mode",
            "Ctrl+M",
            "Toggle Beginner/Expert mode"
        )
        
        self.register_shortcut(
            "fullscreen_graph",
            "F11",
            "Toggle fullscreen graph"
        )
    
    def register_shortcut(
        self, 
        shortcut_id: str, 
        key_sequence: str, 
        description: str,
        callback: Optional[Callable] = None
    ):
        """Register a keyboard shortcut"""
        from PyQt6.QtCore import Qt
        
        shortcut = QShortcut(QKeySequence(key_sequence), self.parent_widget)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        
        # Connect to callback or emit signal
        if callback:
            shortcut.activated.connect(callback)
        else:
            shortcut.activated.connect(lambda: self.shortcut_triggered.emit(shortcut_id))
        
        # Store shortcut
        self.shortcuts[shortcut_id] = shortcut
        
        # Set initial enabled state
        self._update_shortcuts_enabled()
    
    def on_mode_changed(self):
        """Update shortcuts when mode changes"""
        self._update_shortcuts_enabled()
    
    def _update_shortcuts_enabled(self):
        """Enable/disable shortcuts based on mode"""
        config = self.mode_manager.get_ui_config()
        enable_shortcuts = config.get('enable_shortcuts', False)
        
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(enable_shortcuts)
    
    def get_shortcut(self, shortcut_id: str) -> Optional[QShortcut]:
        """Get shortcut by ID"""
        return self.shortcuts.get(shortcut_id)
    
    def get_all_shortcuts(self) -> Dict[str, tuple]:
        """Get all shortcuts as dict of (key_sequence, description)"""
        result = {}
        for shortcut_id, shortcut in self.shortcuts.items():
            result[shortcut_id] = (
                shortcut.key().toString(),
                shortcut.parent().property('description') or ''
            )
        return result
    
    def is_enabled(self) -> bool:
        """Check if shortcuts are currently enabled"""
        config = self.mode_manager.get_ui_config()
        return config.get('enable_shortcuts', False)


class ShortcutCheatSheet(QWidget):
    """
    Popup showing all available keyboard shortcuts
    Triggered by F1 or Help button
    """
    
    def __init__(self, shortcuts_manager: KeyboardShortcutsManager):
        super().__init__()
        self.shortcuts_manager = shortcuts_manager
        self.init_ui()
    
    def init_ui(self):
        from PyQt6.QtWidgets import QVBoxLayout, QLabel, QTextEdit, QPushButton
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("⌨️ Keyboard Shortcuts")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Check if enabled
        if not self.shortcuts_manager.is_enabled():
            warning = QLabel("""
            <div style='background-color: #f39c12; color: white; padding: 15px; border-radius: 5px;'>
                <b>⚠️ Keyboard shortcuts are disabled</b><br>
                Switch to <b>Expert Mode</b> in Workflow Hub to enable shortcuts.
            </div>
            """)
            layout.addWidget(warning)
        
        # Shortcuts list
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Build HTML table
        html = """
        <style>
            table { width: 100%; border-collapse: collapse; }
            th { background-color: #3498db; color: white; padding: 10px; text-align: left; }
            td { padding: 8px; border-bottom: 1px solid #ecf0f1; }
            .key { font-family: monospace; background-color: #ecf0f1; padding: 3px 8px; border-radius: 3px; }
            .section { font-weight: bold; background-color: #e8f4f8; padding: 8px; margin-top: 10px; }
        </style>
        <table>
            <tr><th>Shortcut</th><th>Description</th></tr>
            
            <tr><td colspan='2' class='section'>Global</td></tr>
            <tr><td><span class='key'>Ctrl+N</span></td><td>Create new test</td></tr>
            <tr><td><span class='key'>Ctrl+S</span></td><td>Save current workflow state</td></tr>
            <tr><td><span class='key'>Ctrl+R</span></td><td>Resume last workflow</td></tr>
            <tr><td><span class='key'>Ctrl+F</span></td><td>Quick search</td></tr>
            <tr><td><span class='key'>Ctrl+H</span></td><td>Go to Workflow Hub</td></tr>
            <tr><td><span class='key'>Ctrl+M</span></td><td>Toggle Beginner/Expert mode</td></tr>
            
            <tr><td colspan='2' class='section'>Categories (Workflow Hub)</td></tr>
            <tr><td><span class='key'>Ctrl+1</span></td><td>Load Development workflows</td></tr>
            <tr><td><span class='key'>Ctrl+2</span></td><td>Testing & Validation workflows</td></tr>
            <tr><td><span class='key'>Ctrl+3</span></td><td>Production & QC workflows</td></tr>
            <tr><td><span class='key'>Ctrl+4</span></td><td>Ballistics & Field workflows</td></tr>
            <tr><td><span class='key'>Ctrl+5</span></td><td>Database & Setup workflows</td></tr>
            
            <tr><td colspan='2' class='section'>Workflows</td></tr>
            <tr><td><span class='key'>Ctrl+L</span></td><td>Open Ladder Test</td></tr>
            <tr><td><span class='key'>Ctrl+O</span></td><td>Open OCW Test</td></tr>
            <tr><td><span class='key'>Ctrl+Q</span></td><td>Open Batch QC</td></tr>
            
            <tr><td colspan='2' class='section'>Data Entry (Live Testing)</td></tr>
            <tr><td><span class='key'>Ctrl+Enter</span></td><td>Add shot</td></tr>
            <tr><td><span class='key'>Ctrl+Right</span></td><td>Next charge weight</td></tr>
            <tr><td><span class='key'>Ctrl+Left</span></td><td>Previous charge weight</td></tr>
            <tr><td><span class='key'>Ctrl+Shift+Del</span></td><td>Clear current data</td></tr>
            
            <tr><td colspan='2' class='section'>View</td></tr>
            <tr><td><span class='key'>F11</span></td><td>Toggle fullscreen graph</td></tr>
            <tr><td><span class='key'>F1</span></td><td>Show this cheat sheet</td></tr>
        </table>
        """
        
        text_edit.setHtml(html)
        layout.addWidget(text_edit)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(600, 700)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    central = QWidget()
    window.setCentralWidget(central)
    
    # Create mode manager
    mode_manager = UserModeManager()
    
    # Create shortcuts manager
    shortcuts_manager = KeyboardShortcutsManager(window, mode_manager)
    
    # Connect signals
    def on_shortcut(shortcut_id):
        from src.logging_config import configure_logging, get_logger
        configure_logging()
        logger = get_logger(__name__)
        logger.info("Shortcut triggered: %s", shortcut_id)
    
    shortcuts_manager.shortcut_triggered.connect(on_shortcut)
    
    # Show cheat sheet
    cheat_sheet = ShortcutCheatSheet(shortcuts_manager)
    cheat_sheet.show()
    
    window.setWindowTitle("Keyboard Shortcuts Demo")
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())
