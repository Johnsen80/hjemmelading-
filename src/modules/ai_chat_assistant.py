"""Local guidance chat for load development.

This legacy widget keeps the existing class names for compatibility, but the
user-facing experience is local, offline-first guidance based on the current
load context.
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

from ..utils.i18n import get_current_language, tr


class AIMessage(QFrame):
    """Single guidance message bubble."""

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
        container = QFrame(self)
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)

        # Header (timestamp + role)
        header = QLabel(container)
        if self.is_user:
            header.setText(f"<b>{tr('ai_chat_you')}</b> • {self.timestamp}")
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
            header.setText(f"<b>{tr('ai_chat_assistant')}</b> • {self.timestamp}")
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
        message_label = QLabel(self.text, container)
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
    """Worker thread for local guidance processing."""

    response_ready = pyqtSignal(str)

    def __init__(self, prompt: str, context: Dict):
        super().__init__()
        self.prompt = prompt
        self.context = context

    def run(self):
        """Process a local guidance request."""
        import time

        time.sleep(1)  # Simulate API call

        # Generate a local guidance response based on the prompt.
        response = self._generate_response(self.prompt, self.context)
        self.response_ready.emit(response)

    def _generate_response(self, prompt: str, context: Dict) -> str:
        """Generate a local guidance response."""
        prompt_lower = prompt.lower()

        # Knowledge base responses
        if "sd" in prompt_lower or "standard deviation" in prompt_lower:
            return self._localized_block("sd", prompt)

        elif "es" in prompt_lower or "extreme spread" in prompt_lower:
            return self._localized_block("es", prompt)

        elif "pressure" in prompt_lower or "signs" in prompt_lower:
            return self._localized_block("pressure", prompt)

        elif "recommend" in prompt_lower or "suggest" in prompt_lower:
            return self._localized_block("recommend", prompt)

        elif "node" in prompt_lower or "accuracy" in prompt_lower:
            return self._localized_block("accuracy", prompt)

        elif (
            "temperature" in prompt_lower
            or "temp" in prompt_lower
            or "seasonal" in prompt_lower
        ):
            return self._localized_block("temperature", prompt)

        elif "barrel" in prompt_lower or "cleaning" in prompt_lower:
            return self._localized_block("barrel", prompt)

        else:
            return self._localized_block("generic", prompt)

    def _localized_block(self, topic: str, prompt: str) -> str:
        if get_current_language() == "no":
            return self._localized_block_no(topic, prompt)
        return self._localized_block_en(topic, prompt)

    def _localized_block_no(self, topic: str, prompt: str) -> str:
        responses = {
            "sd": """
            <b>Standard Deviation (SD) in Reloading:</b><br><br>
            SD measures velocity consistency. Lower is better.<br><br>
            <b>What's good?</b><br>
            • <span style='color: #27ae60;'><b>&lt;10 fps</b></span> = Excellent (match grade)<br>
            • <span style='color: #f39c12;'><b>10-15 fps</b></span> = Good (hunting/precision)<br>
            • <span style='color: #e74c3c;'><b>&gt;15 fps</b></span> = Needs work<br><br>
            <b>Looking at your data:</b><br>
            Your current load shows very strong consistency and a match-grade SD.<br><br>
            <b>How to improve SD:</b><br>
            1. Consistent powder charges<br>
            2. Uniform primer seating depth<br>
            3. Consistent bullet seating depth<br>
            4. Same brass lot and firing count<br>
            5. Temperature-stable powder
            """,
            "es": """
            <b>Extreme Spread (ES):</b><br><br>
            ES is the difference between your fastest and slowest shot.<br><br>
            <b>Targets:</b><br>
            • <span style='color: #27ae60;'><b>&lt;20 fps</b></span> = Excellent<br>
            • <span style='color: #f39c12;'><b>20-30 fps</b></span> = Acceptable<br>
            • <span style='color: #e74c3c;'><b>&gt;30 fps</b></span> = Too much variation<br><br>
            <b>Why it matters:</b><br>
            Larger ES can create visible vertical spread at distance.
            """,
            "pressure": """
            <b>Pressure Signs - What to Watch For:</b><br><br>
            <b>Safe signs:</b><br>
            • Rounded primers<br>
            • Easy bolt lift<br>
            • Smooth extraction<br><br>
            <b>Warning signs:</b><br>
            • Slightly flattened primers<br>
            • Faint ejector marks<br><br>
            <b>Danger - stop immediately:</b><br>
            • Cratered primers<br>
            • Heavy bolt lift<br>
            • Sticky extraction<br>
            • Case head separation signs<br>
            • Blown primers<br><br>
            <b>Temperature matters:</b><br>
            A load that is safe in one environment should always be verified in other relevant conditions.
            """,
            "recommend": """
            <b>Load Recommendation Based on Your Data:</b><br><br>
            Looking at 6.5 Creedmoor with Vihtavuori N140:<br><br>
            <b>Best observed load:</b> LD_20241115_003<br>
            • <b>42.0 gr N140</b><br>
            • 2665 fps<br>
            • SD: 5.8 fps<br>
            • 0.68 MOA<br><br>
            <b>Why it looks strong:</b><br>
            1. Stable across multiple sessions<br>
            2. Low pressure signs<br>
            3. Strong SD/ES values<br>
            4. Verified at distance<br><br>
            <b>Next optimization:</b><br>
            • Test ±0.2 gr to confirm the node<br>
            • Test a small change in jump<br>
            • Document temperature response
            """,
            "accuracy": """
            <b>Accuracy Node - Find the Sweet Spot:</b><br><br>
            <b>What is a node?</b><br>
            A charge area where barrel harmonics are favorable and more repeatable.<br><br>
            <b>How to find it:</b><br>
            1. Ladder test<br>
            2. OCW/group-based verification<br>
            3. Seating-depth refinement<br><br>
            <b>Your data suggests:</b><br>
            42.0 gr looks like a possible node with usable repeatability and good groups.
            """,
            "temperature": """
            <b>Temperature Sensitivity in Loads:</b><br><br>
            <b>Why it matters:</b><br>
            Powder behaves differently across temperatures.<br>
            • Cold = lower velocity/pressure<br>
            • Warm = higher velocity/pressure<br><br>
            <b>Practical advice:</b><br>
            Test the load across relevant temperature ranges and log the change.
            """,
            "barrel": """
            <b>Barrel Maintenance and Round Count:</b><br><br>
            <b>Cleaning frequency:</b><br>
            • Match: often every 50-100 shots<br>
            • Hunting: as needed and after range use<br>
            • Precision: when results start to drift<br><br>
            <b>Fouling shots:</b><br>
            Point of impact can shift after cleaning. It is useful to log shots since cleaning.<br><br>
            <b>Service life:</b><br>
            Wear often appears gradually through velocity drift and worsening groups.
            """,
            "generic": f"""
            I understand you asked: "<i>{prompt}</i>"<br><br>
            I can help with:<br>
            • load development advice<br>
            • SD, ES, nodes, and precision concepts<br>
            • pressure-sign interpretation<br>
            • your historical data and patterns<br>
            • temperature sensitivity<br><br>
            <b>Try asking:</b><br>
            • "What's a good SD for precision?"<br>
            • "How do I interpret pressure signs?"<br>
            • "Recommend a load based on my data"<br>
            • "How does temperature affect my loads?"<br>
            • "What is an accuracy node?"
            """,
        }
        return responses[topic]

    def _localized_block_en(self, topic: str, prompt: str) -> str:
        responses = {
            "sd": """
            <b>Standard Deviation (SD) in Reloading:</b><br><br>
            SD measures velocity consistency. Lower is better.<br><br>
            <b>What's good?</b><br>
            • <span style='color: #27ae60;'><b>&lt;10 fps</b></span> = Excellent (match grade)<br>
            • <span style='color: #f39c12;'><b>10-15 fps</b></span> = Good (hunting/precision)<br>
            • <span style='color: #e74c3c;'><b>&gt;15 fps</b></span> = Needs work<br><br>
            <b>Looking at your data:</b><br>
            Your current load shows very strong consistency and a match-grade SD.<br><br>
            <b>How to improve SD:</b><br>
            1. Consistent powder charges<br>
            2. Uniform primer seating depth<br>
            3. Consistent bullet seating depth<br>
            4. Same brass lot and firing count<br>
            5. Temperature-stable powder
            """,
            "es": """
            <b>Extreme Spread (ES):</b><br><br>
            ES is the difference between your fastest and slowest shot.<br><br>
            <b>Targets:</b><br>
            • <span style='color: #27ae60;'><b>&lt;20 fps</b></span> = Excellent<br>
            • <span style='color: #f39c12;'><b>20-30 fps</b></span> = Acceptable<br>
            • <span style='color: #e74c3c;'><b>&gt;30 fps</b></span> = Too much variation<br><br>
            <b>Why it matters:</b><br>
            Larger ES can create visible vertical spread at distance.
            """,
            "pressure": """
            <b>Pressure Signs - What to Watch For:</b><br><br>
            <b>Safe signs:</b><br>
            • Rounded primers<br>
            • Easy bolt lift<br>
            • Smooth extraction<br><br>
            <b>Warning signs:</b><br>
            • Slightly flattened primers<br>
            • Faint ejector marks<br><br>
            <b>Danger - stop immediately:</b><br>
            • Cratered primers<br>
            • Heavy bolt lift<br>
            • Sticky extraction<br>
            • Case head separation signs<br>
            • Blown primers
            """,
            "recommend": """
            <b>Load Recommendation Based on Your Data:</b><br><br>
            Your strongest observed load looks stable across velocity, group size, and pressure behavior.<br><br>
            <b>Suggested next step:</b><br>
            Confirm the node with a short verification series and document temperature response.
            """,
            "accuracy": """
            <b>Accuracy Nodes - Finding the Sweet Spot:</b><br><br>
            A node is a forgiving charge area where barrel harmonics and consistency align.<br><br>
            <b>Best ways to find it:</b><br>
            • ladder testing<br>
            • OCW/group verification<br>
            • seating-depth refinement
            """,
            "temperature": """
            <b>Temperature Sensitivity in Loads:</b><br><br>
            Powder behavior changes with temperature, which affects both velocity and pressure.<br><br>
            <b>Best practice:</b><br>
            Validate the load in the temperatures you actually expect to use.
            """,
            "barrel": """
            <b>Barrel Care and Round Count Effects:</b><br><br>
            Track cleaning intervals, fouling shots, and round count. Those trends often explain drifting velocity or changing group behavior over time.
            """,
            "generic": f"""
            I understand you asked: "<i>{prompt}</i>"<br><br>
            I can help with:<br>
            • load development advice<br>
            • SD, ES, nodes, and precision concepts<br>
            • pressure-sign interpretation<br>
            • your historical data and patterns<br>
            • temperature sensitivity<br><br>
            <b>Try asking:</b><br>
            • "What's a good SD for precision?"<br>
            • "How do I interpret pressure signs?"<br>
            • "Recommend a load based on my data"<br>
            • "How does temperature affect my loads?"<br>
            • "What is an accuracy node?"
            """,
        }
        return responses[topic]


class AIChatAssistant(QWidget):
    """
    Legacy guidance chat widget for load development.

    Internal names remain unchanged for compatibility with older imports.
    """

    def __init__(self, load_context: Optional[Dict] = None):
        super().__init__()
        self.load_context = load_context or {}
        self.messages: list[AIMessage] = []
        self.init_ui()

        # Welcome message
        self.add_ai_message(tr("ai_chat_welcome_html"))

    def init_ui(self):
        """Initialize the guidance chat UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(f"{tr('ai_chat_load_development_assistant')}", self)
        header.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;"
        )
        layout.addWidget(header)

        # Chat area (scrollable)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget(scroll)
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
        quick_label = QLabel(f"<b>{tr('ai_chat_quick_ask')}</b>", input_frame)
        quick_label.setStyleSheet("font-size: 11px;")
        quick_layout.addWidget(quick_label)

        btn_sd = QPushButton(tr("ai_chat_whats_sd"), input_frame)
        btn_sd.clicked.connect(lambda: self.send_quick_prompt(tr("ai_chat_prompt_sd")))
        quick_layout.addWidget(btn_sd)

        btn_pressure = QPushButton(tr("ai_chat_pressure_signs"), input_frame)
        btn_pressure.clicked.connect(
            lambda: self.send_quick_prompt(tr("ai_chat_prompt_pressure"))
        )
        quick_layout.addWidget(btn_pressure)

        btn_recommend = QPushButton(tr("ai_chat_best_load"), input_frame)
        btn_recommend.clicked.connect(
            lambda: self.send_quick_prompt(tr("ai_chat_prompt_best_load"))
        )
        quick_layout.addWidget(btn_recommend)

        input_layout.addLayout(quick_layout)

        # Text input
        self.input_text = QLineEdit(input_frame)
        self.input_text.setPlaceholderText(tr("ai_chat_placeholder"))
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
        self.btn_send = QPushButton(tr("ai_chat_send"), input_frame)
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
        """Add a guidance message to the chat."""
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
        _p = self.chat_container.parent()
        scroll_area = _p.parent() if _p is not None else None
        if isinstance(scroll_area, QScrollArea):
            scrollbar = scroll_area.verticalScrollBar()
            if scrollbar is not None:
                scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send a user message and request a guidance response."""
        text = self.input_text.text().strip()
        if not text:
            return

        # Add user message
        self.add_user_message(text)
        self.input_text.clear()

        # Disable input while processing
        self.input_text.setEnabled(False)
        self.btn_send.setEnabled(False)
        self.btn_send.setText(tr("ai_chat_thinking"))

        # Process the guidance response in the background.
        self.ai_worker = AIWorker(text, self.load_context)
        self.ai_worker.response_ready.connect(self.on_ai_response)
        self.ai_worker.start()

    def send_quick_prompt(self, prompt: str):
        """Send a quick prompt"""
        self.input_text.setText(prompt)
        self.send_message()

    @pyqtSlot(str)
    def on_ai_response(self, response: str):
        """Handle a guidance response."""
        self.add_ai_message(response)

        # Re-enable input
        self.input_text.setEnabled(True)
        self.btn_send.setEnabled(True)
        self.btn_send.setText(tr("ai_chat_send"))
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
