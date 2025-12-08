"""
AI Chat Assistant for Load Development
Conversational AI that understands YOUR data and helps optimize loads

Features:
- Ask questions about your loads
- Get explanations of pressure signs, ES/SD, etc.
- Load recommendations based on YOUR historical data
- Learn from your testing patterns
- Context-aware (knows what load you're working on)
"""

from datetime import datetime
from typing import Dict, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class AIMessage(QFrame):
    """Single AI message bubble"""

    def __init__(
        self, text: str, is_user: bool = False, timestamp: Optional[str] = None
    ):
        super().__init__()
        self.text = text
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.init_ui()

    def init_ui(self):
        """Initialize message bubble"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Message container
        container = QFrame()
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)

        # Header (timestamp + role)
        header = QLabel()
        if self.is_user:
            header.setText(f"<b>You</b> • {self.timestamp}")
            container.setStyleSheet(
                """
                QFrame {
                    background-color: #3498db;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                }
            """
            )
        else:
            header.setText(f"<b>🤖 AI Assistant</b> • {self.timestamp}")
            container.setStyleSheet(
                """
                QFrame {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border-radius: 10px;
                    padding: 10px;
                }
            """
            )

        header.setStyleSheet("font-size: 11px;")
        container_layout.addWidget(header)

        # Message text
        message_label = QLabel(self.text)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setOpenExternalLinks(True)
        container_layout.addWidget(message_label)

        # Align based on sender
        if self.is_user:
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            container.setMaximumWidth(600)
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            container.setMaximumWidth(700)

        layout.addWidget(container)


class AIWorker(QThread):
    """Worker thread for AI processing (simulated for now)"""

    response_ready = pyqtSignal(str)

    def __init__(self, prompt: str, context: Dict):
        super().__init__()
        self.prompt = prompt
        self.context = context

    def run(self):
        """Process AI request (simulated - will integrate OpenAI API)"""
        import time

        time.sleep(1)  # Simulate API call

        # Simulate AI response based on prompt
        response = self._generate_response(self.prompt, self.context)
        self.response_ready.emit(response)

    def _generate_response(self, prompt: str, context: Dict) -> str:
        """Generate simulated AI response"""
        prompt_lower = prompt.lower()

        # Knowledge base responses
        if "sd" in prompt_lower or "standard deviation" in prompt_lower:
            return """
            <b>Standard Deviation (SD) in Reloading:</b><br><br>

            SD measures velocity consistency. Lower is better!<br><br>

            <b>What's good?</b><br>
            • <span style='color: #27ae60;'><b>&lt;10 fps</b></span> = Excellent (match grade)<br>
            • <span style='color: #f39c12;'><b>10-15 fps</b></span> = Good (hunting/precision)<br>
            • <span style='color: #e74c3c;'><b>&gt;15 fps</b></span> = Needs work<br><br>

            <b>Looking at YOUR data:</b><br>
            Your current load (6.5 CM, N140 42.0gr) shows SD of <b>6.2 fps</b> - that's <b>match-grade excellent!</b> 🎯<br><br>

            <b>How to improve SD:</b><br>
            1. Consistent powder charges (± 0.05gr)<br>
            2. Uniform primer seating depth<br>
            3. Consistent bullet seating depth<br>
            4. Same brass lot & firing count<br>
            5. Fresh, temperature-stable powder
            """

        elif "es" in prompt_lower or "extreme spread" in prompt_lower:
            return """
            <b>Extreme Spread (ES):</b><br><br>

            ES is the difference between your fastest and slowest shot.<br><br>

            <b>Targets:</b><br>
            • <span style='color: #27ae60;'><b>&lt;20 fps</b></span> = Excellent<br>
            • <span style='color: #f39c12;'><b>20-30 fps</b></span> = Acceptable<br>
            • <span style='color: #e74c3c;'><b>&gt;30 fps</b></span> = Too much variation<br><br>

            <b>YOUR load:</b> 15 fps ES - <b>Excellent!</b> ✅<br><br>

            <b>Why it matters:</b><br>
            At 1000m, 30 fps ES = ~0.6 MRAD vertical spread!
            """

        elif "pressure" in prompt_lower or "signs" in prompt_lower:
            return """
            <b>Pressure Signs - What to Watch For:</b><br><br>

            <b>🟢 Safe signs:</b><br>
            • Rounded primers<br>
            • Easy bolt lift<br>
            • Smooth extraction<br><br>

            <b>🟡 Warning signs (back off 0.5gr):</b><br>
            • Slightly flattened primers<br>
            • Faint ejector marks<br><br>

            <b>🔴 DANGER - STOP IMMEDIATELY:</b><br>
            • Cratered primers<br>
            • Heavy bolt lift<br>
            • Sticky extraction<br>
            • Case head separation<br>
            • Blown primers<br><br>

            <b>Temperature matters!</b><br>
            A safe summer load can be overpressure in winter.
            Test across temperature ranges!
            """

        elif "recommend" in prompt_lower or "suggest" in prompt_lower:
            return """
            <b>📊 Load Recommendation Based on YOUR Data:</b><br><br>

            Analyzing your 6.5 Creedmoor loads with Vihtavuori N140:<br><br>

            <b>Best performing load:</b> LD_20241115_003<br>
            • <b>42.0 gr N140</b><br>
            • 2665 fps<br>
            • SD: 5.8 fps (excellent!)<br>
            • 0.68 MOA (your best group)<br><br>

            <b>Why this load works:</b><br>
            1. Consistent across 3 sessions<br>
            2. Low pressure signs<br>
            3. Great SD/ES numbers<br>
            4. Verified at distance (300m)<br><br>

            <b>💡 Optimization suggestions:</b><br>
            • Test ±0.2gr (41.8, 42.2) to find exact node<br>
            • Try 0.010mm more/less bullet jump<br>
            • Document across temperatures (-10°C to +30°C)<br><br>

            <b>Next steps:</b><br>
            Load 20 rounds at 42.0gr for verification @ 500m+
            """

        elif "node" in prompt_lower or "accuracy" in prompt_lower:
            return """
            <b>Accuracy Nodes - Finding the Sweet Spot:</b><br><br>

            <b>What's a node?</b><br>
            A powder charge where barrel harmonics align perfectly,
            giving exceptional accuracy even with small charge variations.<br><br>

            <b>How to find nodes:</b><br>
            1. <b>Ladder test:</b> Load 0.3gr steps, look for plateau in velocity<br>
            2. <b>OCW test:</b> Load groups at same charge, find tightest<br>
            3. <b>Seating depth:</b> 0.010" jumps from touching lands<br><br>

            <b>YOUR data shows:</b><br>
            42.0gr appears to be a node:<br>
            • Two sessions with similar velocity (2680, 2665)<br>
            • Both showed good accuracy (0.75, 0.68 MOA)<br>
            • Consistent SD across tests<br><br>

            <b>Node characteristics:</b><br>
            • Repeatable accuracy<br>
            • Forgiving to small charge variations<br>
            • Consistent across conditions
            """

        elif (
            "temperature" in prompt_lower
            or "temp" in prompt_lower
            or "seasonal" in prompt_lower
        ):
            return """
            <b>Temperature Sensitivity in Loads:</b><br><br>

            <b>Why it matters:</b><br>
            Powder burn rate changes with temperature!<br>
            • Cold = slower burn = lower velocity/pressure<br>
            • Hot = faster burn = higher velocity/pressure<br><br>

            <b>Typical changes:</b><br>
            • Single-base powders: ~1 fps/°C<br>
            • Double-base powders: ~1.5-2 fps/°C<br>
            • Vihtavuori N140: ~0.9 fps/°C (good!)<br><br>

            <b>For YOUR load (42.0gr N140 @ 2680 fps):</b><br>
            If developed at 15°C:<br>
            • At -10°C: ~2658 fps (-22 fps)<br>
            • At +30°C: ~2694 fps (+14 fps)<br><br>

            <b>Best practice:</b><br>
            Test your load at -10°C, +15°C, and +30°C.
            Document velocity changes.
            """

        elif "barrel" in prompt_lower or "cleaning" in prompt_lower:
            return """
            <b>Barrel Care & Round Count Effects:</b><br><br>

            <b>Cleaning frequency:</b><br>
            • Match shooters: Every 50-100 rounds<br>
            • Hunters: Once per season + after range day<br>
            • Precision: When accuracy drops<br><br>

            <b>Break-in (controversial):</b><br>
            • Premium barrels: Shoot clean<br>
            • Factory barrels: Clean every 5-10 for first 50<br><br>

            <b>Fouling shots:</b><br>
            After cleaning, expect POI shift for 2-5 shots.<br>
            YOUR DATA: Document this! Track "rounds since clean" in every session.<br><br>

            <b>Barrel life (6.5 Creedmoor):</b><br>
            • Factory: 2000-3000 rounds<br>
            • Match (hot loads): 1500-2500 rounds<br>
            • Accuracy usually degrades gradually, not sudden<br><br>

            <b>Signs of throat erosion:</b><br>
            • Velocity increase with same load<br>
            • Accuracy degradation<br>
            • Increased ES/SD
            """

        else:
            # Generic response
            return f"""
            I understand you asked: "<i>{prompt}</i>"<br><br>

            I'm here to help with:<br>
            • Load development advice<br>
            • Explaining ballistics concepts (SD, ES, nodes, etc.)<br>
            • Analyzing YOUR historical data<br>
            • Troubleshooting accuracy issues<br>
            • Pressure sign interpretation<br>
            • Temperature sensitivity<br><br>

            <b>Try asking:</b><br>
            • "What's a good SD for precision shooting?"<br>
            • "How do I interpret pressure signs?"<br>
            • "Recommend a load based on my data"<br>
            • "How does temperature affect my loads?"<br>
            • "What's an accuracy node?"
            """


class AIChatAssistant(QWidget):
    """
    AI Chat Assistant for load development
    Understands YOUR data and provides personalized advice
    """

    def __init__(self, load_context: Optional[Dict] = None):
        super().__init__()
        self.load_context = load_context or {}
        self.messages: list[AIMessage] = []
        self.init_ui()

        # Welcome message
        self.add_ai_message(
            """
        👋 <b>Hi! I'm your AI Load Development Assistant.</b><br><br>

        I can help you with:<br>
        • Understanding ballistics concepts (SD, ES, nodes)<br>
        • Interpreting pressure signs<br>
        • Analyzing YOUR historical load data<br>
        • Recommending optimal loads based on your testing<br>
        • Troubleshooting accuracy issues<br><br>

        <b>I've analyzed your data:</b><br>
        • 3 sessions logged<br>
        • 6.5 Creedmoor with N140<br>
        • Best load: 42.0gr (SD 5.8, 0.68 MOA)<br><br>

        What would you like to know?
        """
        )

    def init_ui(self):
        """Initialize chat UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel("🤖 AI Load Development Assistant")
        header.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;"
        )
        layout.addWidget(header)

        # Chat area (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_container.setLayout(self.chat_layout)
        self.chat_layout.addStretch()

        scroll.setWidget(self.chat_container)
        layout.addWidget(scroll)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(
            """
            QFrame {
                background-color: #ecf0f1;
                border-top: 2px solid #bdc3c7;
                padding: 10px;
            }
        """
        )
        input_layout = QHBoxLayout()
        input_frame.setLayout(input_layout)

        # Quick prompts
        quick_layout = QVBoxLayout()
        quick_label = QLabel("<b>Quick ask:</b>")
        quick_label.setStyleSheet("font-size: 11px;")
        quick_layout.addWidget(quick_label)

        btn_sd = QPushButton("What's SD?")
        btn_sd.clicked.connect(
            lambda: self.send_quick_prompt(
                "What is Standard Deviation and what's a good SD for precision shooting?"
            )
        )
        quick_layout.addWidget(btn_sd)

        btn_pressure = QPushButton("Pressure signs?")
        btn_pressure.clicked.connect(
            lambda: self.send_quick_prompt("How do I interpret pressure signs?")
        )
        quick_layout.addWidget(btn_pressure)

        btn_recommend = QPushButton("Best load?")
        btn_recommend.clicked.connect(
            lambda: self.send_quick_prompt(
                "Recommend the best load based on my historical data"
            )
        )
        quick_layout.addWidget(btn_recommend)

        input_layout.addLayout(quick_layout)

        # Text input
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Ask me anything about load development...")
        self.input_text.returnPressed.connect(self.send_message)
        self.input_text.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 5px;
            }
        """
        )
        input_layout.addWidget(self.input_text)

        # Send button
        self.btn_send = QPushButton("Send")
        self.btn_send.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """
        )
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send)

        layout.addWidget(input_frame)

    def add_ai_message(self, text: str):
        """Add AI message to chat"""
        message = AIMessage(text, is_user=False)
        self.messages.append(message)

        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message)

        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)

    def add_user_message(self, text: str):
        """Add user message to chat"""
        message = AIMessage(text, is_user=True)
        self.messages.append(message)

        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message)

        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scroll_area = self.chat_container.parent().parent()
        if isinstance(scroll_area, QScrollArea):
            scrollbar = scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send user message and get AI response"""
        text = self.input_text.text().strip()
        if not text:
            return

        # Add user message
        self.add_user_message(text)
        self.input_text.clear()

        # Disable input while processing
        self.input_text.setEnabled(False)
        self.btn_send.setEnabled(False)
        self.btn_send.setText("Thinking...")

        # Process AI response in background
        self.ai_worker = AIWorker(text, self.load_context)
        self.ai_worker.response_ready.connect(self.on_ai_response)
        self.ai_worker.start()

    def send_quick_prompt(self, prompt: str):
        """Send a quick prompt"""
        self.input_text.setText(prompt)
        self.send_message()

    @pyqtSlot(str)
    def on_ai_response(self, response: str):
        """Handle AI response"""
        self.add_ai_message(response)

        # Re-enable input
        self.input_text.setEnabled(True)
        self.btn_send.setEnabled(True)
        self.btn_send.setText("Send")
        self.input_text.setFocus()


if __name__ == "__main__":
    import sys

    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Sample load context
    context = {
        "caliber": "6.5 Creedmoor",
        "powder": "Vihtavuori N140",
        "best_load": {"charge": 42.0, "velocity": 2665, "sd": 5.8, "moa": 0.68},
    }

    assistant = AIChatAssistant(context)
    assistant.show()
    assistant.resize(900, 700)

    sys.exit(app.exec())
