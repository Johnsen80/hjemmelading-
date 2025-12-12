"""Test ballistics simulator standalone"""

import sys

from PyQt6.QtWidgets import QApplication
from src.modules.ballistics_simulator import BallisticsSimulator

print("Starting Ballistics Simulator...")
print("-" * 60)

app = QApplication(sys.argv)

simulator = BallisticsSimulator()
simulator.setWindowTitle(
    "🔬 Real-Time Ballistics Simulator - Reloading Workshop Manager"
)
simulator.resize(1600, 1000)
simulator.show()

print("✅ Simulator window opened!")
print()
print("Features:")
print("  📈 Real-time pressure curves (like QuickLOAD)")
print("  🚀 Velocity progression in barrel")
print("  📊 Multi-charge comparison graphs")
print("  ⚖️ Live slider control (20-60 grains)")
print("  🎯 Safety margin warnings")
print("  🔬 Physics-based calculations (Noble-Abel)")
print()
print("Select rifle, bullet, and powder, then move the charge slider!")
print("-" * 60)

sys.exit(app.exec())
