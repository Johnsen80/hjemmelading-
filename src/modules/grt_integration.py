from __future__ import annotations

import json

from PyQt6.QtWidgets import QMessageBox


def _normalize_import_row(item: dict, ammo_profile_id: int) -> dict:
    predicted_velocity = item.get("predicted_velocity")
    if predicted_velocity in (None, ""):
        predicted_velocity = item.get("velocity_fps")

    max_pressure_psi = item.get("max_pressure_psi")
    if max_pressure_psi in (None, ""):
        max_pressure_psi = item.get("pressure")

    case_fill_percent = item.get("case_fill_percent")
    if case_fill_percent in (None, ""):
        case_fill_percent = item.get("fill_ratio")

    predicted_accuracy_potential = item.get("predicted_accuracy_potential")
    if predicted_accuracy_potential in (None, ""):
        predicted_accuracy_potential = item.get("accuracy_potential")

    return {
        "ammo_profile_id": ammo_profile_id,
        "predicted_velocity": predicted_velocity,
        "max_pressure_psi": max_pressure_psi,
        "case_fill_percent": case_fill_percent,
        "predicted_accuracy_potential": predicted_accuracy_potential,
        "grt_data": json.dumps(item, ensure_ascii=False),
    }


class GRTImportDialog:
    def do_import(self) -> None:
        imported = 0
        for item in getattr(self, "grt_data", []) or []:
            profile = self.find_matching_profile(item)
            if not profile:
                continue

            ammo_profile_id = int(profile["id"])
            payload = _normalize_import_row(item, ammo_profile_id)
            existing = self.db.execute_query(
                "SELECT id FROM grt_data WHERE ammo_profile_id = ?",
                (ammo_profile_id,),
            )
            if existing:
                row_id = int(existing[0]["id"])
                self.db.update("grt_data", payload, "id = ?", (row_id,))
            else:
                self.db.insert("grt_data", payload)
            imported += 1

        QMessageBox.information(
            self,
            "Reference Import",
            f"Imported {imported} archived reference rows.",
        )
        self.accept()


__all__ = ["GRTImportDialog", "QMessageBox"]
