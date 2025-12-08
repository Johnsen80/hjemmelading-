"""
Quick test script for Rifle Profile Editor with beginner/expert mode
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication

from src.modules.rifle_profile_editor import RifleProfileEditor


def test_beginner_mode():
    """Test in beginner mode"""
    app = QApplication(sys.argv)

    print("🌱 Testing Beginner Mode...")
    editor = RifleProfileEditor(user_mode="beginner")
    editor.show()

    sys.exit(app.exec())


def test_expert_mode():
    """Test in expert mode"""
    app = QApplication(sys.argv)

    print("🎓 Testing Expert Mode...")
    editor = RifleProfileEditor(user_mode="expert")
    editor.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    import sys

    # Check command line args
    mode = sys.argv[1] if len(sys.argv) > 1 else "beginner"

    if mode == "expert":
        test_expert_mode()
    else:
        test_beginner_mode()
