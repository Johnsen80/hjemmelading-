"""
User Mode Manager
Handle Beginner vs Expert mode with persistent settings
"""

from PyQt6.QtCore import QSettings, QObject, pyqtSignal
from typing import Dict, Any


class UserMode:
    """User mode enum"""
    BEGINNER = "beginner"
    EXPERT = "expert"


class UserModeManager(QObject):
    """
    Manages user mode (Beginner/Expert) settings
    Provides mode-specific UI configurations
    """
    
    mode_changed = pyqtSignal(str)  # Emits new mode
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("ReloadingWorkshop", "ReloadingManager")
        self._current_mode = self.settings.value("user_mode", UserMode.BEGINNER)
    
    def get_mode(self) -> str:
        """Get current mode"""
        return self._current_mode
    
    def set_mode(self, mode: str):
        """Set mode"""
        if mode not in [UserMode.BEGINNER, UserMode.EXPERT]:
            raise ValueError(f"Invalid mode: {mode}")
        
        old_mode = self._current_mode
        self._current_mode = mode
        self.settings.setValue("user_mode", mode)
        
        if old_mode != mode:
            self.mode_changed.emit(mode)
    
    def is_beginner(self) -> bool:
        """Check if in beginner mode"""
        return self._current_mode == UserMode.BEGINNER
    
    def is_expert(self) -> bool:
        """Check if in expert mode"""
        return self._current_mode == UserMode.EXPERT
    
    def toggle_mode(self):
        """Toggle between modes"""
        new_mode = UserMode.EXPERT if self.is_beginner() else UserMode.BEGINNER
        self.set_mode(new_mode)
    
    def get_ui_config(self) -> Dict[str, Any]:
        """
        Get UI configuration based on mode
        
        Returns dict with:
        - show_tooltips: bool
        - show_help_text: bool
        - show_examples: bool
        - enable_shortcuts: bool
        - compact_layout: bool
        - confirmation_dialogs: bool
        """
        if self.is_beginner():
            return {
                'show_tooltips': True,
                'show_help_text': True,
                'show_examples': True,
                'enable_shortcuts': False,
                'compact_layout': False,
                'confirmation_dialogs': True,
                'wizard_mode': True,
                'detailed_errors': True
            }
        else:  # Expert
            return {
                'show_tooltips': False,
                'show_help_text': False,
                'show_examples': False,
                'enable_shortcuts': True,
                'compact_layout': True,
                'confirmation_dialogs': False,
                'wizard_mode': False,
                'detailed_errors': False
            }
    
    def get_mode_description(self) -> str:
        """Get description of current mode"""
        if self.is_beginner():
            return """
<b>🔰 Beginner Mode</b><br>
• Full tooltips and explanations<br>
• Step-by-step wizards<br>
• Confirmation dialogs<br>
• Detailed error messages<br>
• Examples and help text<br>
<br>
<i>Perfect for learning reloading!</i>
            """
        else:
            return """
<b>⚡ Expert Mode</b><br>
• Minimal UI (no tooltips)<br>
• Direct access (no wizards)<br>
• Keyboard shortcuts enabled<br>
• Compact layout<br>
• Fewer confirmation dialogs<br>
<br>
<i>For experienced reloaders!</i>
            """


# Tooltip manager
class TooltipConfig:
    """
    Centralized tooltip configuration
    Provides mode-aware tooltips
    """
    
    TOOLTIPS = {
        # Ladder Test
        'ladder_charge_start': {
            'beginner': 'Start med en SAFE ladning (under max!).\n\nSjekk ladningsdata først!',
            'expert': 'Starting charge weight'
        },
        'ladder_charge_end': {
            'beginner': 'Maks ladning for testen.\n\n⚠️ ALDRI over manual max!',
            'expert': 'Maximum charge weight'
        },
        'ladder_step_size': {
            'beginner': 'Hvor mye å øke mellom hvert steg.\n\n0.2-0.5gr er vanlig for rifle.',
            'expert': 'Step increment'
        },
        
        # OCW Test
        'ocw_group_count': {
            'beginner': 'Antall grupper å skyte per ladning.\n\nMinimum 3 for god statistikk.',
            'expert': 'Groups per charge'
        },
        
        # Batch QC
        'qc_charge_tolerance': {
            'beginner': 'Hvor mye avvik som er OK.\n\n±0.1gr er match-grade.\nFederal bruker ±0.05gr.',
            'expert': 'Charge tolerance'
        },
        'qc_coal_tolerance': {
            'beginner': 'COAL tolerance.\n\n±0.005" er standard.\nMatch-grade: ±0.002"',
            'expert': 'COAL tolerance'
        },
        
        # Temperature Test
        'temp_test_range': {
            'beginner': 'Test fra kald vinter (-20°C) til varm sommer (+40°C).\n\nAmmofabrikker tester dette!',
            'expert': 'Temperature range'
        },
        
        # General
        'bullet_selection': {
            'beginner': 'Velg kule.\n\nVekt (grains) og type (HPBT, BTHP, etc.) er viktig!',
            'expert': 'Select bullet'
        },
        'powder_selection': {
            'beginner': 'Velg krutt.\n\nSjekk alltid ladningsdata for din kaliber!',
            'expert': 'Select powder'
        }
    }
    
    @staticmethod
    def get(key: str, mode_manager: UserModeManager) -> str:
        """Get tooltip for key based on current mode"""
        if key not in TooltipConfig.TOOLTIPS:
            return ""
        
        tooltips = TooltipConfig.TOOLTIPS[key]
        mode = 'beginner' if mode_manager.is_beginner() else 'expert'
        
        # Expert mode: no tooltips unless explicitly needed
        if mode == 'expert' and not mode_manager.get_ui_config()['show_tooltips']:
            return ""
        
        return tooltips.get(mode, tooltips.get('beginner', ''))


# Example widget mixin for mode-aware widgets
class ModeAwareWidgetMixin:
    """Mixin for widgets that adapt to user mode"""
    
    def __init__(self, mode_manager: UserModeManager):
        self.mode_manager = mode_manager
        self.mode_manager.mode_changed.connect(self.on_mode_changed)
        
        # Apply initial mode
        self.apply_mode_config()
    
    def apply_mode_config(self):
        """Apply mode-specific configuration"""
        config = self.mode_manager.get_ui_config()
        
        # Override in subclass to apply config
        # Example:
        # if config['show_tooltips']:
        #     self.button.setToolTip(TooltipConfig.get('key', self.mode_manager))
        # if config['compact_layout']:
        #     self.layout.setSpacing(5)
        pass
    
    def on_mode_changed(self, new_mode: str):
        """Called when mode changes"""
        self.apply_mode_config()


if __name__ == "__main__":
    # Test
    manager = UserModeManager()
    
    print(f"Current mode: {manager.get_mode()}")
    print(f"Is beginner: {manager.is_beginner()}")
    print(f"Is expert: {manager.is_expert()}")
    
    print("\nUI Config:")
    config = manager.get_ui_config()
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\nMode description:")
    print(manager.get_mode_description())
    
    print("\n--- Toggle to Expert ---")
    manager.toggle_mode()
    
    print(f"\nNew mode: {manager.get_mode()}")
    print("\nUI Config:")
    config = manager.get_ui_config()
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\nTooltip examples:")
    print(f"Ladder charge start (beginner): {TooltipConfig.get('ladder_charge_start', UserModeManager())}")
    manager.set_mode(UserMode.EXPERT)
    print(f"Ladder charge start (expert): {TooltipConfig.get('ladder_charge_start', manager)}")
