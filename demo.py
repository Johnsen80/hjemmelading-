"""
Quick Demo - Show what the system can do
"""
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class DemoLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 Ballistics System Demo Launcher")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔬 Integrated Ballistics System")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 20px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Physics + AI + Database = Better than QuickLOAD + GRT")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; padding-bottom: 30px;")
        layout.addWidget(subtitle)
        
        # Features
        features = QLabel("""
        <h3 style='color: #27ae60;'>✅ What You Get:</h3>
        <ul style='font-size: 11pt; line-height: 2.0;'>
            <li><b>Physics Engine:</b> Noble-Abel equation, burn rate modeling</li>
            <li><b>Real-Time Simulator:</b> Interactive pressure/velocity graphs (like GRT)</li>
            <li><b>Load Development Wizard:</b> AI + physics predictions</li>
            <li><b>Batch Management:</b> Professional QC tracking (10 new database tables)</li>
            <li><b>Safety Warnings:</b> SAAMI/CIP compliance checking</li>
            <li><b>Learning System:</b> Gets smarter with every test</li>
        </ul>
        
        <h3 style='color: #e74c3c;'>🆚 Comparison:</h3>
        <table style='width: 100%; font-size: 10pt;'>
            <tr style='background: #ecf0f1;'>
                <th style='padding: 8px;'>Feature</th>
                <th style='padding: 8px;'>QuickLOAD</th>
                <th style='padding: 8px;'>GRT</th>
                <th style='padding: 8px;'>Our System</th>
            </tr>
            <tr>
                <td style='padding: 8px;'>Pressure Prediction</td>
                <td style='padding: 8px; text-align: center;'>✅</td>
                <td style='padding: 8px; text-align: center;'>✅</td>
                <td style='padding: 8px; text-align: center;'>✅</td>
            </tr>
            <tr style='background: #ecf0f1;'>
                <td style='padding: 8px;'>Beautiful UI</td>
                <td style='padding: 8px; text-align: center;'>❌</td>
                <td style='padding: 8px; text-align: center;'>✅</td>
                <td style='padding: 8px; text-align: center;'>✅</td>
            </tr>
            <tr>
                <td style='padding: 8px;'>Database Integration</td>
                <td style='padding: 8px; text-align: center;'>❌</td>
                <td style='padding: 8px; text-align: center;'>❌</td>
                <td style='padding: 8px; text-align: center;'><b>✅</b></td>
            </tr>
            <tr style='background: #ecf0f1;'>
                <td style='padding: 8px;'>Batch Tracking</td>
                <td style='padding: 8px; text-align: center;'>❌</td>
                <td style='padding: 8px; text-align: center;'>❌</td>
                <td style='padding: 8px; text-align: center;'><b>✅</b></td>
            </tr>
            <tr>
                <td style='padding: 8px;'>AI Learning</td>
                <td style='padding: 8px; text-align: center;'>❌</td>
                <td style='padding: 8px; text-align: center;'>❌</td>
                <td style='padding: 8px; text-align: center;'><b>✅</b></td>
            </tr>
            <tr style='background: #ecf0f1;'>
                <td style='padding: 8px;'><b>Price</b></td>
                <td style='padding: 8px; text-align: center;'>€150</td>
                <td style='padding: 8px; text-align: center;'>FREE</td>
                <td style='padding: 8px; text-align: center;'><b>FREE</b></td>
            </tr>
        </table>
        """)
        layout.addWidget(features)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        wizard_btn = QPushButton("🧙 Load Development Wizard")
        wizard_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        wizard_btn.clicked.connect(self.launch_wizard)
        button_layout.addWidget(wizard_btn)
        
        simulator_btn = QPushButton("🔬 Ballistics Simulator")
        simulator_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        simulator_btn.clicked.connect(self.launch_simulator)
        button_layout.addWidget(simulator_btn)
        
        layout.addLayout(button_layout)
        
        # Footer
        footer = QLabel("💡 Tip: Start with the simulator to visualize physics, then use wizard to create batches")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #95a5a6; padding: 20px; font-style: italic;")
        layout.addWidget(footer)
        
        self.setLayout(layout)
    
    def launch_wizard(self):
        """Launch Load Development Wizard"""
        from src.modules.load_development_wizard import LoadDevelopmentWizard
        
        wizard = LoadDevelopmentWizard(self)
        wizard.exec()
    
    def launch_simulator(self):
        """Launch Ballistics Simulator"""
        from src.modules.ballistics_simulator import BallisticsSimulator
        
        simulator_window = QWidget()
        simulator_window.setWindowTitle("🔬 Real-Time Ballistics Simulator")
        simulator_window.resize(1600, 1000)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        simulator = BallisticsSimulator()
        layout.addWidget(simulator)
        
        simulator_window.setLayout(layout)
        simulator_window.show()
        
        # Store reference so it doesn't get garbage collected
        self.simulator_window = simulator_window


if __name__ == '__main__':
    print()
    print("=" * 80)
    print("🎯 BALLISTICS SYSTEM DEMO")
    print("=" * 80)
    print()
    print("What to try:")
    print("  1. 🔬 Ballistics Simulator - Interactive graphs, live slider")
    print("  2. 🧙 Load Development Wizard - AI + Physics predictions")
    print()
    print("Demo uses database from main application.")
    print("Add rifles/bullets/powder first for best experience!")
    print("=" * 80)
    print()
    
    app = QApplication(sys.argv)
    demo = DemoLauncher()
    demo.show()
    sys.exit(app.exec())
