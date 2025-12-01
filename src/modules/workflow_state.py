"""
Workflow State Manager
Save and restore workflow progress
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QSettings
from src.logging_config import configure_logging, get_logger

# Configure logging for this module
configure_logging()
logger = get_logger(__name__)


class WorkflowState:
    """Represents a saved workflow state"""
    
    def __init__(self, workflow_id: str, workflow_name: str, data: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.data = data
        self.timestamp = datetime.now().isoformat()
        self.last_updated = self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'data': self.data,
            'timestamp': self.timestamp,
            'last_updated': self.last_updated
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WorkflowState':
        """Create from dictionary"""
        state = WorkflowState(
            data['workflow_id'],
            data['workflow_name'],
            data['data']
        )
        state.timestamp = data.get('timestamp', datetime.now().isoformat())
        state.last_updated = data.get('last_updated', state.timestamp)
        return state


class WorkflowStateManager:
    """
    Manages workflow state persistence
    Saves/loads workflow progress to/from JSON files
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # Default to user's AppData
            from PyQt6.QtCore import QStandardPaths
            app_data = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
            data_dir = Path(app_data) / "ReloadingWorkshop" / "workflows"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.states_file = self.data_dir / "workflow_states.json"
        self.active_states: Dict[str, WorkflowState] = {}
        
        self._load_states()
    
    def _load_states(self):
        """Load all saved states from disk"""
        if not self.states_file.exists():
            return
        
        try:
            with open(self.states_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for workflow_id, state_data in data.items():
                self.active_states[workflow_id] = WorkflowState.from_dict(state_data)
        
        except Exception as e:
            logger.error("Error loading workflow states: %s", e)
    
    def _save_states(self):
        """Save all states to disk"""
        try:
            data = {
                workflow_id: state.to_dict()
                for workflow_id, state in self.active_states.items()
            }
            
            with open(self.states_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error("Error saving workflow states: %s", e)
    
    def save_state(self, workflow_id: str, workflow_name: str, data: Dict[str, Any]):
        """Save workflow state"""
        if workflow_id in self.active_states:
            # Update existing
            state = self.active_states[workflow_id]
            state.data = data
            state.last_updated = datetime.now().isoformat()
        else:
            # Create new
            state = WorkflowState(workflow_id, workflow_name, data)
            self.active_states[workflow_id] = state
        
        self._save_states()
    
    def get_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state"""
        return self.active_states.get(workflow_id)
    
    def has_state(self, workflow_id: str) -> bool:
        """Check if workflow has saved state"""
        return workflow_id in self.active_states
    
    def clear_state(self, workflow_id: str):
        """Clear workflow state"""
        if workflow_id in self.active_states:
            del self.active_states[workflow_id]
            self._save_states()
    
    def get_all_active(self) -> List[WorkflowState]:
        """Get all active workflow states"""
        return list(self.active_states.values())
    
    def clear_all(self):
        """Clear all states"""
        self.active_states.clear()
        self._save_states()


class WorkflowStateMixin:
    """
    Mixin class for widgets that want state persistence
    Add this to any workflow widget class
    """
    
    def __init__(self, workflow_id: str, workflow_name: str, state_manager: WorkflowStateManager):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.state_manager = state_manager
        
        # Try to restore state
        self._restore_state()
    
    def _restore_state(self):
        """Restore state if available"""
        state = self.state_manager.get_state(self.workflow_id)
        if state:
            self.restore_from_state(state.data)
    
    def restore_from_state(self, data: Dict[str, Any]):
        """Override this to restore widget state from data"""
        raise NotImplementedError("Subclass must implement restore_from_state")
    
    def get_state_data(self) -> Dict[str, Any]:
        """Override this to return current state data"""
        raise NotImplementedError("Subclass must implement get_state_data")
    
    def save_current_state(self):
        """Save current state"""
        data = self.get_state_data()
        self.state_manager.save_state(self.workflow_id, self.workflow_name, data)
    
    def clear_saved_state(self):
        """Clear saved state"""
        self.state_manager.clear_state(self.workflow_id)


# Example usage in a workflow widget:
"""
class MyWorkflowWidget(QWidget, WorkflowStateMixin):
    def __init__(self, state_manager: WorkflowStateManager, parent=None):
        QWidget.__init__(self, parent)
        WorkflowStateMixin.__init__(self, "my_workflow", "My Workflow", state_manager)
        
        # ... setup UI ...
    
    def get_state_data(self) -> Dict[str, Any]:
        return {
            'input_value': self.input_field.text(),
            'selected_item': self.combo.currentIndex(),
            'data_list': self.get_data_list(),
            # ... any other state you want to save
        }
    
    def restore_from_state(self, data: Dict[str, Any]):
        if 'input_value' in data:
            self.input_field.setText(data['input_value'])
        if 'selected_item' in data:
            self.combo.setCurrentIndex(data['selected_item'])
        if 'data_list' in data:
            self.restore_data_list(data['data_list'])
        # ... restore other state
    
    def on_data_changed(self):
        # Auto-save on important changes
        self.save_current_state()
"""


if __name__ == "__main__":
    # Test
    manager = WorkflowStateManager()
    
    # Save some test states
    manager.save_state(
        "ladder_test",
        "Ladder Test",
        {
            'rifle': 'Tikka T3x .308',
            'charge_range': [42.0, 45.0],
            'shots': [
                {'charge': 42.0, 'velocity': 2650},
                {'charge': 42.5, 'velocity': 2680},
            ]
        }
    )
    
    manager.save_state(
        "ocw_test",
        "OCW Test",
        {
            'rifle': 'Bergara B-14 6.5CM',
            'charges': [43.0, 43.3, 43.6],
            'groups': 3
        }
    )
    
    # Load states
    logger.info("Active workflows:")
    for state in manager.get_all_active():
        logger.info("  %s: %s", state.workflow_name, state.workflow_id)
        logger.info("    Last updated: %s", state.last_updated)
        logger.info("    Data: %s", state.data)
    
    # Check specific state
    if manager.has_state("ladder_test"):
        state = manager.get_state("ladder_test")
        logger.info("\nLadder test state:")
        logger.info("  Rifle: %s", state.data['rifle'])
        logger.info("  Shots: %d", len(state.data['shots']))
