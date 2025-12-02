BUTTON_STYLES = {
    "Standard": "",
    "Rund": ("QPushButton { border-radius: 20px; padding: 8px 24px; }"),
    "Fargerik": (
        "QPushButton { background-color: #4caf50; color: white; "
        "font-weight: bold; } "
        "QPushButton:hover { background-color: #388e3c; }"
    ),
    "Flat": (
        "QPushButton { border: none; background: none; color: #333; "
        "font-size: 16px; } "
        "QPushButton:hover { color: #1976d2; }"
    ),
    "Glass": (
        "QPushButton { background: rgba(255,255,255,0.3); "
        "border: 1px solid #aaa; border-radius: 12px; color: #222; } "
        "QPushButton:hover { background: rgba(255,255,255,0.5); }"
    ),
}
