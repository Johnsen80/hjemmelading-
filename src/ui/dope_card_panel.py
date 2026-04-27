"""DOPE card panel — display and print calibrated ballistic correction tables.

Receives a DopeCard dataclass from field_planning.services.build_dope_card()
and renders it as a styled Qt table. Includes a print-to-PDF button.

Usage::

    panel = DopeCardPanel(parent)
    panel.set_dope_card(card)
"""

from __future__ import annotations

from ..field_planning.models import DopeCard
from ..qt_compat import (
    QFont,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_COLUMNS = [
    ("Distance", "distance"),
    ("Clicks ↑", "elev_clicks"),
    ("MOA ↑", "elev_moa"),
    ("Wind\n10m/s", "wind_10_moa"),
    ("Vel\nm/s", "velocity"),
    ("Energy\nJ", "energy"),
    ("TOF\ns", "tof"),
    ("Phase", "phase"),
]

_PHASE_COLORS = {
    "supersonic": ("#1a7a1a", "#a8f0a8"),
    "transonic": ("#7a6a00", "#f0e080"),
    "subsonic": ("#7a1a1a", "#f0a8a8"),
}


class DopeCardPanel(QWidget):
    """Displays a calibrated DOPE card table with warnings and print button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._card: DopeCard | None = None
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_dope_card(self, card: DopeCard) -> None:
        self._card = card
        self._refresh()

    def clear(self) -> None:
        self._card = None
        self._header_label.setText("DOPE Card")
        self._conditions_label.setText("")
        self._table.setRowCount(0)
        self._warnings_widget.setVisible(False)
        self._print_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(4, 4, 4, 4)

        # Header row
        hdr = QHBoxLayout()
        self._header_label = QLabel("DOPE Card")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self._header_label.setFont(font)
        hdr.addWidget(self._header_label)
        hdr.addStretch()
        self._print_btn = QPushButton("📄 Skriv ut / PDF")
        self._print_btn.setEnabled(False)
        self._print_btn.clicked.connect(self._on_print)
        hdr.addWidget(self._print_btn)
        root.addLayout(hdr)

        # Conditions summary
        self._conditions_label = QLabel("")
        self._conditions_label.setStyleSheet("color: #b0b6be; font-size: 10pt;")
        root.addWidget(self._conditions_label)

        # Warnings area
        self._warnings_widget = QWidget()
        self._warnings_layout = QVBoxLayout(self._warnings_widget)
        self._warnings_layout.setSpacing(2)
        self._warnings_layout.setContentsMargins(0, 0, 0, 0)
        self._warnings_widget.setVisible(False)
        root.addWidget(self._warnings_widget)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        hh = self._table.horizontalHeader()
        if hh:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hh.setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            "QTableWidget { font-size: 10.5pt; }"
            "QTableWidget::item { padding: 3px 6px; }"
        )
        root.addWidget(self._table)

        # BC / MV metadata footer
        self._meta_label = QLabel("")
        self._meta_label.setStyleSheet(
            "color: #888; font-size: 9pt; font-style: italic;"
        )
        root.addWidget(self._meta_label)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        card = self._card
        if card is None:
            return

        self._header_label.setText(
            f"DOPE-kort — {card.rifle_name}  ·  {card.ammo_label or 'Ukjent ammo'}"
        )
        self._conditions_label.setText(
            f"Null: {card.zero_distance_m:.0f}m  |  {card.conditions_summary}"
            f"  |  Generert: {card.generated_at[:16]}"
        )
        self._meta_label.setText(
            f"BC {card.learned_bc:.4f} {card.bc_source}  |  "
            f"MV {card.learned_mv_fps:.0f} fps ±{card.learned_mv_sd_fps:.1f}  ({card.mv_source})"
        )

        # Warnings
        for i in reversed(range(self._warnings_layout.count())):
            item = self._warnings_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        if card.atmosphere_warnings:
            for w in card.atmosphere_warnings:
                lbl = QLabel(w)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    "background: #2a1a00; color: #f0b060; padding: 4px 8px; "
                    "border-left: 3px solid #e67e22; font-size: 10pt;"
                )
                self._warnings_layout.addWidget(lbl)
            self._warnings_widget.setVisible(True)
        else:
            self._warnings_widget.setVisible(False)

        # Table rows
        self._table.setRowCount(len(card.rows))
        for row_idx, row in enumerate(card.rows):
            phase_bg, phase_fg = _PHASE_COLORS.get(row.phase, ("#23272e", "#e0e6ed"))

            def _item(text: str, right: bool = True) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                if right:
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                    )
                return it

            cells = [
                _item(f"{row.distance_m:.0f} m"),
                _item(f"{row.correction.elevation_clicks:+.1f}"),
                _item(f"{row.correction.elevation_moa:+.2f}"),
                _item(
                    f"{row.wind_10mps_moa:+.2f}"
                    if row.wind_10mps_moa is not None
                    else "—"
                ),
                _item(f"{row.velocity_mps:.0f}"),
                _item(f"{row.energy_joules:.0f}"),
                _item(f"{row.time_of_flight_s:.3f}"),
                _item(_phase_label(row.phase), right=False),
            ]

            for col_idx, cell in enumerate(cells):
                if col_idx == len(cells) - 1:  # Phase column
                    cell.setBackground(_mk_color(phase_bg))
                    cell.setForeground(_mk_color(phase_fg))
                self._table.setItem(row_idx, col_idx, cell)

        self._print_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Print / PDF
    # ------------------------------------------------------------------

    def _on_print(self) -> None:
        if self._card is None:
            return
        text = self._build_print_text()
        # Try QPrinter → PDF first
        printed = False
        try:
            from ..qt_compat import BINDING, QtWidgets

            if BINDING == "PyQt6":
                from PyQt6.QtGui import QTextDocument
                from PyQt6.QtPrintSupport import QPrinter
            else:
                from PySide6.QtGui import QTextDocument
                from PySide6.QtPrintSupport import QPrinter

            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save DOPE card as PDF",
                f"DOPE_{self._card.rifle_name.replace(' ', '_')}.pdf",
                "PDF-filer (*.pdf)",
            )
            if path:
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(path)
                printer.setPageSize(QPrinter.PageSize.A4)
                doc = QTextDocument()
                doc.setPlainText(text)
                doc.setDefaultFont(QFont("Courier New", 9))
                doc.print_(printer)
                printed = True
                self._print_btn.setText("✔ Saved")
        except Exception:
            pass

        if not printed:
            try:
                dialog = _PrintPreviewDialog(text, self._card, self)
                dialog.exec()
            except Exception:
                from ..qt_compat import QMessageBox

                QMessageBox.information(self, "DOPE Card", text[:2000])

    def _build_print_text(self) -> str:
        if self._card is None:
            return ""
        card = self._card
        lines = [
            f"DOPE CARD — {card.rifle_name}",
            f"Ammo: {card.ammo_label}",
            f"Null: {card.zero_distance_m:.0f}m  |  {card.conditions_summary}",
            f"BC: {card.learned_bc:.4f} ({card.bc_source})  MV: {card.learned_mv_fps:.0f} fps",
            "",
            f"{'Distance':>8}  {'Clicks':>7}  {'MOA':>7}  {'Wind10':>7}  "
            f"{'Vel':>6}  {'Energy':>7}  {'TOF':>6}  Phase",
            "-" * 72,
        ]
        for row in card.rows:
            wind = (
                f"{row.wind_10mps_moa:+6.2f}"
                if row.wind_10mps_moa is not None
                else "    —"
            )
            lines.append(
                f"{row.distance_m:>7.0f}m  "
                f"{row.correction.elevation_clicks:>+7.1f}  "
                f"{row.correction.elevation_moa:>+7.2f}  "
                f"{wind}  "
                f"{row.velocity_mps:>5.0f}  "
                f"{row.energy_joules:>6.0f}J  "
                f"{row.time_of_flight_s:>5.3f}  "
                f"{_phase_label(row.phase)}"
            )
        if card.atmosphere_warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in card.atmosphere_warnings:
                lines.append(f"  {w}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Helper: print preview dialog
# ------------------------------------------------------------------


class _PrintPreviewDialog(QWidget):
    def __init__(self, text: str, card: DopeCard, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self._text = text
        self._card = card
        self.setWindowTitle(f"DOPE-kort — {card.rifle_name}")
        self.resize(620, 720)
        from ..qt_compat import QTextEdit

        layout = QVBoxLayout(self)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setFont(QFont("Courier New", 10))
        te.setPlainText(text)
        layout.addWidget(te)
        btn_row = QHBoxLayout()
        pdf_btn = QPushButton("💾 Save PDF")
        pdf_btn.clicked.connect(self._save_pdf)
        btn_row.addWidget(pdf_btn)
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _save_pdf(self) -> None:
        try:
            from ..qt_compat import BINDING, QtWidgets

            if BINDING == "PyQt6":
                from PyQt6.QtGui import QTextDocument
                from PyQt6.QtPrintSupport import QPrinter
            else:
                from PySide6.QtGui import QTextDocument
                from PySide6.QtPrintSupport import QPrinter
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save PDF",
                f"DOPE_{self._card.rifle_name.replace(' ', '_')}.pdf",
                "PDF files (*.pdf)",
            )
            if not path:
                return
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageSize(QPrinter.PageSize.A4)
            doc = QTextDocument()
            doc.setPlainText(self._text)
            doc.setDefaultFont(QFont("Courier New", 9))
            doc.print_(printer)
        except Exception as exc:
            from ..qt_compat import QMessageBox

            QMessageBox.warning(self, "PDF-feil", str(exc))

    def exec(self):
        self.show()


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------


def _mk_color(hex_color: str):
    try:
        from ..qt_compat import QtGui

        return QtGui.QColor(hex_color)
    except Exception:
        return None


def _phase_label(phase: str) -> str:
    return {
        "supersonic": "Supersonisk",
        "transonic": "Transonisk",
        "subsonic": "Subsonisk",
    }.get(phase, phase)
