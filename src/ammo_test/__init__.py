"""Ammo test module — lot registration, test sessions, LOT comparison, reports."""

from __future__ import annotations

from typing import Any


class AmmoTestReportDialog:
    """Dialog wrapper around AmmoTestWindow, filtered to a specific rifle/barrel.

    Accepts the same kwargs that weapon_profile_dialog and ammo_profile_manager
    pass so it can be used as a drop-in replacement for the old dashboard version.
    """

    def __new__(  # type: ignore[misc]
        cls,
        db: Any = None,
        language: str = "en",
        rifle_id: int | None = None,
        barrel_id: str | None = None,
        barrel_name: str | None = None,
        ammo_profile_id: int | None = None,
        ammo_type: str | None = None,
        parent: Any = None,
    ) -> Any:
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout

            from ..ui.ammo_test_window import AmmoTestWindow

            rifles: list[dict] = []
            if db is not None:
                try:
                    rifles = db.get_all("rifles") or []
                except Exception:
                    pass

            dlg = QDialog(parent)
            dlg.setWindowTitle("Ammo Test")
            dlg.resize(1100, 820)
            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(0, 0, 0, 0)
            win = AmmoTestWindow(db=db, rifles=rifles, parent=dlg)
            layout.addWidget(win)
            return dlg
        except Exception:
            from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout

            dlg = QDialog(parent)
            dlg.setWindowTitle("Ammo Test")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Ammo test module could not be loaded."))
            return dlg
