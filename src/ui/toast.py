"""
Toast-notifikasjon — auto-lukkende melding nederst til høyre i foreldervinduet.

Bruk:
    from src.ui.toast import show_toast
    show_toast(parent_widget, "Lagret!", kind="success")
"""

from __future__ import annotations

from typing import Literal

from ..qt_compat import QHBoxLayout, QLabel, QPushButton, QTimer, QWidget

_KIND_STYLE = {
    "success": "background:#27ae60; color:#fff;",
    "error": "background:#e74c3c; color:#fff;",
    "warning": "background:#e67e22; color:#fff;",
    "info": "background:#2980b9; color:#fff;",
}


class ToastNotification(QWidget):
    """Liten flytende boks som vises i 3 sekunder, deretter forsvinner selv."""

    def __init__(
        self,
        message: str,
        parent: QWidget | None = None,
        kind: Literal["success", "error", "warning", "info"] = "info",
        duration_ms: int = 3000,
    ) -> None:
        super().__init__(parent)

        # Vindu-flagg: ingen ramme, alltid over resten, ikke i oppgavelinja
        try:
            from ..qt_compat import Qt

            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.Tool
                | Qt.WindowType.WindowStaysOnTopHint
            )
        except Exception:
            pass

        try:
            from ..qt_compat import Qt

            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        except Exception:
            pass

        base_style = _KIND_STYLE.get(kind, _KIND_STYLE["info"])
        self.setStyleSheet(
            f"QWidget {{ {base_style} border-radius: 8px; padding: 0px; }}"
        )

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 10, 10, 10)
        outer.setSpacing(10)

        lbl = QLabel(message, self)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("background: transparent; color: #fff; font-size: 11pt;")
        outer.addWidget(lbl, 1)

        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #fff; border: none; font-size: 10pt; }"
            "QPushButton:hover { background: rgba(255,255,255,0.2); border-radius: 4px; }"
        )
        close_btn.clicked.connect(self.close)
        outer.addWidget(close_btn)

        self.adjustSize()
        self._position_in_parent(parent)

        # Auto-close timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)
        self._timer.start(duration_ms)

    def _position_in_parent(self, parent: QWidget | None) -> None:
        if parent is None:
            return
        try:
            rect = parent.rect()
            margin = 16
            x = rect.right() - self.width() - margin
            y = rect.bottom() - self.height() - margin - 40  # above statusbar
            self.move(
                parent.mapToGlobal(parent.rect().topLeft()).x() + x,
                parent.mapToGlobal(parent.rect().topLeft()).y() + y,
            )
        except Exception:
            pass


def show_toast(
    parent: QWidget | None,
    message: str,
    kind: Literal["success", "error", "warning", "info"] = "info",
    duration_ms: int = 3000,
) -> ToastNotification:
    """Vis en toast-melding og returner widget-referansen."""
    toast = ToastNotification(
        message, parent=parent, kind=kind, duration_ms=duration_ms
    )
    toast.show()
    return toast
