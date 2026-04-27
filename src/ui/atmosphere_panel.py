"""Atmosphere panel — displays layered atmosphere state and warnings.

Shows:
- Warning banners (inversjon, termikk, katabatisk, etc.)
- Surface + aloft layers (T, P, RH, wind, density altitude)
- Density altitude badge

Usage::

    panel = AtmospherePanel(parent)
    panel.set_atmosphere(atm)
"""

from __future__ import annotations

from ..field_planning.models import LayeredAtmosphere
from ..qt_compat import (
    QFont,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_RISK_COLORS = {
    "high": ("#7a1a00", "#f88060"),
    "moderate": ("#5a4500", "#f0c060"),
    "low": ("#0a3a1a", "#60c080"),
}


class AtmospherePanel(QWidget):
    """Displays atmospheric state with warnings and layer table."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def set_atmosphere(self, atm: LayeredAtmosphere) -> None:
        self._refresh(atm)

    def clear(self) -> None:
        self._clear_warnings()
        self._table.setRowCount(0)
        self._risk_badge.setVisible(False)
        self._da_label.setText("")

    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(4, 4, 4, 4)

        hdr = QHBoxLayout()
        title = QLabel("Atmosphere")
        f = QFont()
        f.setBold(True)
        f.setPointSize(11)
        title.setFont(f)
        hdr.addWidget(title)
        hdr.addStretch()

        self._risk_badge = QLabel("Termikk: HØYT")
        self._risk_badge.setStyleSheet(
            "background: #7a2000; color: #ff9060; font-weight: bold; "
            "padding: 2px 8px; border-radius: 4px; font-size: 9.5pt;"
        )
        self._risk_badge.setVisible(False)
        hdr.addWidget(self._risk_badge)

        self._da_label = QLabel("")
        self._da_label.setStyleSheet("color: #b0b6be; font-size: 9.5pt;")
        hdr.addWidget(self._da_label)
        root.addLayout(hdr)

        # Warnings
        self._warnings_container = QWidget()
        self._warnings_layout = QVBoxLayout(self._warnings_container)
        self._warnings_layout.setSpacing(2)
        self._warnings_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._warnings_container)

        # Layers table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Høyde", "Temp", "Trykk", "RF%", "Vind\nm/s", "DA\nm", "Kilde"]
        )
        hh = self._table.horizontalHeader()
        if hh:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hh.setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setMaximumHeight(160)
        self._table.setStyleSheet("font-size: 10pt;")
        root.addWidget(self._table)

    def _refresh(self, atm: LayeredAtmosphere) -> None:
        self._clear_warnings()

        # Warning banners
        for w in atm.warnings:
            lbl = QLabel(w)
            lbl.setWordWrap(True)
            is_warn = w.startswith("⚠️")
            bg = "#2a1a00" if is_warn else "#1a2a1a"
            fg = "#f0b060" if is_warn else "#80e080"
            border = "#e67e22" if is_warn else "#27ae60"
            lbl.setStyleSheet(
                f"background: {bg}; color: {fg}; padding: 4px 8px; "
                f"border-left: 3px solid {border}; font-size: 10pt;"
            )
            self._warnings_layout.addWidget(lbl)

        # Thermal risk badge
        thermal = atm.thermal_risk_level
        if thermal in ("high", "moderate"):
            bg, fg = _RISK_COLORS[thermal]
            label = "HØYT" if thermal == "high" else "MODERATE"
            self._risk_badge.setText(f"Thermal: {label}")
            self._risk_badge.setStyleSheet(
                f"background: {bg}; color: {fg}; font-weight: bold; "
                f"padding: 2px 8px; border-radius: 4px; font-size: 9.5pt;"
            )
            self._risk_badge.setVisible(True)
        else:
            self._risk_badge.setVisible(False)

        # DA label
        surface = atm.surface_layer
        da = surface.density_altitude_m
        self._da_label.setText(f"DA: {da:+.0f}m")

        # Layer table
        self._table.setRowCount(len(atm.layers))
        for i, layer in enumerate(atm.layers):

            def _cell(text: str, right: bool = True) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                flag = (
                    Qt.AlignmentFlag.AlignRight
                    if right
                    else Qt.AlignmentFlag.AlignCenter
                )
                it.setTextAlignment(flag | Qt.AlignmentFlag.AlignVCenter)
                return it

            self._table.setItem(i, 0, _cell(f"{layer.altitude_m:.0f}m"))
            self._table.setItem(i, 1, _cell(f"{layer.temperature_c:+.1f}°C"))
            self._table.setItem(i, 2, _cell(f"{layer.pressure_hpa:.1f}"))
            self._table.setItem(i, 3, _cell(f"{layer.humidity_pct:.0f}%"))
            self._table.setItem(
                i, 4, _cell(f"{layer.wind_speed_mps:.1f} fra {layer.wind_dir_deg:.0f}°")
            )
            self._table.setItem(i, 5, _cell(f"{layer.density_altitude_m:+.0f}"))
            self._table.setItem(i, 6, _cell(layer.source, right=False))

    def _clear_warnings(self) -> None:
        for i in reversed(range(self._warnings_layout.count())):
            item = self._warnings_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
