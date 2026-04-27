from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from .gordon_measurement_import import import_measurement_profiles


class ReferenceExtractorTemp(QWidget):
    """Temporary workbench for reference data extraction."""

    def __init__(self, parent=None):
        super().__init__(parent)
        project_root = Path(__file__).resolve().parents[2]
        self.project_root = project_root
        self.project_db_path = project_root / "data" / "reloading.db"
        self.export_dir = (
            Path(__file__).resolve().parents[2] / "data" / "gordon_temp_extract"
        )
        self.gordon_data_dir = project_root / "data fra gordon" / "Data"
        self.plugin_dump_dir = Path(
            r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe\dumps"
        )
        try:
            self.db = get_database(db_path=str(self.project_db_path))
        except TypeError:
            self.db = get_database()
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self._build_ui()
        self._append_status(
            "Midlertidig extractor klar. Denne modulen er laget som en arbeidsbenk og kan slettes når uttrekket er ferdig."
        )
        self._load_existing_summary()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("Referanseuttrekk (TEMP)")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        intro = QLabel(
            "Isolert sideprosjekt for referanseuttrekk. Bruk denne til å samle rådata, "
            "lagre mellomfiler og holde oversikt over hva som gjenstår."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        summary_group = QGroupBox("Status")
        summary_layout = QGridLayout(summary_group)
        summary_layout.addWidget(QLabel("Mål:"), 0, 0)
        summary_layout.addWidget(
            QLabel("Trekk ut komplette referansedata for videre mapping"), 0, 1
        )
        summary_layout.addWidget(QLabel("Arbeidsmappe:"), 1, 0)
        self.export_dir_label = QLabel(str(self.export_dir))
        self.export_dir_label.setWordWrap(True)
        summary_layout.addWidget(self.export_dir_label, 1, 1)
        summary_layout.addWidget(QLabel("Dumpmappe:"), 2, 0)
        self.dump_dir_label = QLabel(str(self.plugin_dump_dir))
        self.dump_dir_label.setWordWrap(True)
        summary_layout.addWidget(self.dump_dir_label, 2, 1)
        summary_layout.addWidget(QLabel("Neste steg:"), 3, 0)
        summary_layout.addWidget(
            QLabel("1. Verifisere IPC-kall  2. Lagre råsvar  3. Mappe til appformat"),
            3,
            1,
        )
        layout.addWidget(summary_group)

        action_group = QGroupBox("Arbeidsflate")
        action_layout = QHBoxLayout(action_group)

        choose_btn = QPushButton("Velg eksportmappe")
        choose_btn.clicked.connect(self._choose_export_dir)
        action_layout.addWidget(choose_btn)

        choose_dump_btn = QPushButton("Velg dumpmappe")
        choose_dump_btn.clicked.connect(self._choose_dump_dir)
        action_layout.addWidget(choose_dump_btn)

        snapshot_btn = QPushButton("Lagre status-snapshot")
        snapshot_btn.clicked.connect(self._write_snapshot)
        action_layout.addWidget(snapshot_btn)

        seed_btn = QPushButton("Opprett rådata-mal")
        seed_btn.clicked.connect(self._write_raw_template)
        action_layout.addWidget(seed_btn)

        analyze_btn = QPushButton("Analyser referansedata")
        analyze_btn.clicked.connect(self._analyze_gordon_data)
        action_layout.addWidget(analyze_btn)

        analyze_dumps_btn = QPushButton("Analyser dumpfiler")
        analyze_dumps_btn.clicked.connect(self._analyze_plugin_dumps)
        action_layout.addWidget(analyze_dumps_btn)

        ideas_btn = QPushButton("Eksporter idérapport")
        ideas_btn.clicked.connect(self._export_ideas_report)
        action_layout.addWidget(ideas_btn)

        export_mapped_btn = QPushButton("Eksporter mappet dump-JSON")
        export_mapped_btn.clicked.connect(self._export_mapped_dump_summary)
        action_layout.addWidget(export_mapped_btn)

        export_candidates_btn = QPushButton("Eksporter importkandidater")
        export_candidates_btn.clicked.connect(self._export_grt_import_candidates)
        action_layout.addWidget(export_candidates_btn)

        status_report_btn = QPushButton("Eksporter statusrapport")
        status_report_btn.clicked.connect(self._export_status_report)
        action_layout.addWidget(status_report_btn)

        import_profiles_btn = QPushButton("Importer ammo-profiler fra målinger")
        import_profiles_btn.clicked.connect(self._import_measurement_profiles)
        action_layout.addWidget(import_profiles_btn)

        import_candidates_btn = QPushButton("Importer kandidater til DB")
        import_candidates_btn.clicked.connect(self._import_candidates_to_db)
        action_layout.addWidget(import_candidates_btn)

        action_layout.addStretch()
        layout.addWidget(action_group)

        self.summary_group = QGroupBox("Referanseoversikt")
        self.summary_layout = QGridLayout(self.summary_group)
        self.summary_values: dict[str, QLabel] = {}
        summary_rows = [
            ("Rå projectiles", "summary_raw_projectiles"),
            ("Rå propellants", "summary_raw_propellants"),
            ("Målinger", "summary_measurements"),
            ("App-kuler", "summary_app_bullets"),
            ("App-krutt", "summary_app_powders"),
            ("Dumpfiler", "summary_dump_files"),
            ("Siste dump", "summary_latest_dump"),
            ("Ammo-profiler", "summary_ammo_profiles"),
            ("DB-matcher", "summary_db_matches"),
            ("Nåværende hull", "summary_gap"),
        ]
        for row_index, (label, key) in enumerate(summary_rows):
            self.summary_layout.addWidget(QLabel(f"{label}:"), row_index, 0)
            value_label = QLabel("-")
            value_label.setWordWrap(True)
            self.summary_layout.addWidget(value_label, row_index, 1)
            self.summary_values[key] = value_label
        layout.addWidget(self.summary_group)

        notes_group = QGroupBox("Produktidéer fra referansedata")
        notes_layout = QVBoxLayout(notes_group)
        self.ideas_table = QTableWidget(0, 2)
        self.ideas_table.setHorizontalHeaderLabels(
            ["Idé", "Hvorfor dette ser lovende ut"]
        )
        self.ideas_table.horizontalHeader().setStretchLastSection(True)
        notes_layout.addWidget(self.ideas_table)
        layout.addWidget(notes_group)

        dump_group = QGroupBox("Plugin-dumps")
        dump_layout = QVBoxLayout(dump_group)
        self.dump_table = QTableWidget(0, 4)
        self.dump_table.setHorizontalHeaderLabels(
            ["Fil", "Type", "Nøkkelfelt", "Sist endret"]
        )
        self.dump_table.horizontalHeader().setStretchLastSection(True)
        dump_layout.addWidget(self.dump_table)
        layout.addWidget(dump_group)

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        layout.addWidget(self.status_log)

    def _append_status(self, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_log.append(f"[{stamp}] {message}")

    def _choose_export_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Velg mappe for referanseuttrekk",
            str(self.export_dir),
        )
        if not selected:
            return
        self.export_dir = Path(selected)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir_label.setText(str(self.export_dir))
        self._append_status(f"Eksportmappe satt til {self.export_dir}")

    def _choose_dump_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Velg mappe med referansedumps",
            str(self.plugin_dump_dir),
        )
        if not selected:
            return
        self.plugin_dump_dir = Path(selected)
        self.dump_dir_label.setText(str(self.plugin_dump_dir))
        self._append_status(f"Dumpmappe satt til {self.plugin_dump_dir}")
        self._analyze_plugin_dumps()

    def _write_snapshot(self) -> None:
        snapshot = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "purpose": "Temporary Gordon extraction workbench",
            "export_dir": str(self.export_dir),
            "gordon_data_dir": str(self.gordon_data_dir),
            "plugin_dump_dir": str(self.plugin_dump_dir),
            "todo": [
                "Verify documented IPC commands",
                "Capture raw responses from Gordon",
                "Map verified fields into app structures",
            ],
        }
        path = self.export_dir / "extractor_snapshot.json"
        path.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._append_status(f"Lagret snapshot til {path}")

    def _write_raw_template(self) -> None:
        payload = {
            "tab_list": [],
            "tab_details": [],
            "tab_results": [],
            "chunk_streams": [],
            "notes": "Legg inn rå referansedata her før videre mapping.",
        }
        path = self.export_dir / "raw_gordon_payload_template.json"
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._append_status(f"Opprettet rådata-mal i {path}")
        QMessageBox.information(
            self,
            "Template opprettet",
            f"Rådata-mal lagret i:\n{path}",
        )

    def _load_existing_summary(self) -> None:
        summary_path = self.gordon_data_dir / "gordon_extraction_summary.json"
        if not summary_path.exists():
            self._append_status("Fant ikke eksisterende referanseoppsummering ennå.")
            return
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._append_status(f"Kunne ikke lese referanseoppsummering: {exc}")
            return

        self.summary_values["summary_raw_projectiles"].setText(
            str(summary.get("raw_projectiles", "-"))
        )
        self.summary_values["summary_raw_propellants"].setText(
            str(summary.get("raw_propellants", "-"))
        )
        self.summary_values["summary_measurements"].setText(
            str(summary.get("measurements", "-"))
        )
        self.summary_values["summary_app_bullets"].setText(
            str(summary.get("unique_bullets_for_app", "-"))
        )
        self.summary_values["summary_app_powders"].setText(
            str(summary.get("unique_powders_for_app", "-"))
        )
        self.summary_values["summary_dump_files"].setText("0")
        self.summary_values["summary_latest_dump"].setText("-")
        ammo_profiles = self.db.get_all("ammo_profiles")
        self.summary_values["summary_ammo_profiles"].setText(str(len(ammo_profiles)))
        self.summary_values["summary_db_matches"].setText("0")
        gap_text = (
            f"{summary.get('raw_projectiles', 0)} rå kuleposter -> "
            f"{summary.get('unique_bullets_for_app', 0)} app-kuler, "
            f"{summary.get('raw_propellants', 0)} rå kruttposter -> "
            f"{summary.get('unique_powders_for_app', 0)} app-krutt"
        )
        self.summary_values["summary_gap"].setText(gap_text)
        self._append_status("Lest inn eksisterende referanseoppsummering.")
        self._analyze_gordon_data()
        self._analyze_plugin_dumps()

    def _read_csv_rows(self, filename: str) -> list[dict[str, str]]:
        path = self.gordon_data_dir / filename
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def _build_ideas(self) -> list[tuple[str, str]]:
        projectile_rows = self._read_csv_rows("gordon_bullets_for_hjemmelading.csv")
        propellant_rows = self._read_csv_rows("gordon_extracted_propellants_raw.csv")
        measurement_rows = self._read_csv_rows("gordon_extracted_measurements.csv")

        bullet_manufacturers = Counter(
            row.get("manufacturer", "")
            for row in projectile_rows
            if row.get("manufacturer")
        )
        bullet_calibers = Counter(
            row.get("caliber", "") for row in projectile_rows if row.get("caliber")
        )
        powder_lots = Counter(
            (row.get("mname", ""), row.get("pname", ""), row.get("lotid", ""))
            for row in propellant_rows
            if row.get("mname") and row.get("pname")
        )
        measurement_titles = Counter(
            row.get("measurement_title", "")
            for row in measurement_rows
            if row.get("measurement_title")
        )
        load_count = len(
            {
                row.get("load_title", "")
                for row in measurement_rows
                if row.get("load_title")
            }
        )

        ideas: list[tuple[str, str]] = []
        if bullet_manufacturers:
            top = ", ".join(
                f"{name} ({count})"
                for name, count in bullet_manufacturers.most_common(3)
            )
            ideas.append(
                (
                    "Produsentstyrt kulekatalog",
                    f"Selv det lille utdraget grupperer tydelig på produsent. Toppene nå er {top}, så katalog/UI bør støtte produsent som første filter.",
                )
            )
        if bullet_calibers:
            top = ", ".join(
                f"{name} ({count})" for name, count in bullet_calibers.most_common(3)
            )
            ideas.append(
                (
                    "Normalisering av kalibernavn",
                    f"Dataene har både '.308' og '0.308'-stil. Vi bør bygge en normaliseringsregel tidlig for å unngå dubletter og svake matcher. Nåværende toppkalibre: {top}.",
                )
            )
        if powder_lots:
            ideas.append(
                (
                    "Kruttlot-sporing som first-class feature",
                    "Rå referansedata har produsent, navn og lot-id per kruttpost. Det er et sterkt signal om at lot-læring og lot-sammenligning bør være en sentral del av programmet.",
                )
            )
        if measurement_titles:
            top = ", ".join(
                f"{name} ({count})" for name, count in measurement_titles.most_common(3)
            )
            ideas.append(
                (
                    "Chronograph-import som målingsryggrad",
                    f"Målingene er allerede strukturert rundt faktiske hastighetsserier. Dette peker mot en flyt der chronograph-data er standard inngang til kalibrering. Nåværende typer: {top}.",
                )
            )
        if load_count:
            ideas.append(
                (
                    "Load workspace per oppskrift",
                    f"Vi ser {load_count} distinkte load-titler i målefilene. Programmet bør ha en arbeidsflate der oppskrift, målinger, trykk og komponentlotter bor sammen.",
                )
            )
        ideas.append(
            (
                "Rådata + mapping i to lag",
                "Referanseuttrekket bør lagres rått først og mappes senere. Det gir sporbarhet, gjør debugging enklere og lar oss slette temp-koden uten å miste kildegrunnlaget.",
            )
        )
        return ideas

    def _analyze_gordon_data(self) -> None:
        ideas = self._build_ideas()
        self.ideas_table.setRowCount(len(ideas))
        for row_index, (title, reason) in enumerate(ideas):
            self.ideas_table.setItem(row_index, 0, QTableWidgetItem(title))
            self.ideas_table.setItem(row_index, 1, QTableWidgetItem(reason))
        self.ideas_table.resizeColumnsToContents()
        self._append_status(
            f"Analyserte referansedata og bygget {len(ideas)} produktidéer."
        )

    def _dump_type_and_summary(self, payload: dict) -> tuple[str, str]:
        if "results" in payload:
            results = payload.get("results") or {}
            chunks = results.get("chunks") or []
            summary = (
                f"tabhandle={((payload.get('active_tab') or {}).get('active') or {}).get('tabhandle', '-')}, "
                f"chunkCount={len(chunks)}"
            )
            return "tab_results", summary
        if "tabs" in payload:
            tabs = payload.get("tabs") or []
            return "tab_list", f"tabs={len(tabs)}"
        if "active" in payload or "tab" in payload:
            active = payload.get("active") or {}
            tab = payload.get("tab") or {}
            return (
                "active_tab",
                f"caption={tab.get('caption') or active.get('caption') or '-'}",
            )
        return "unknown", f"keys={', '.join(sorted(payload.keys())[:4])}"

    def _parse_number_with_unit(self, value: object) -> tuple[float | None, str]:
        text = str(value or "").strip()
        if not text:
            return None, ""
        match = re.match(r"^\s*([-+]?\d+(?:[.,]\d+)?)\s*(.*)$", text)
        if not match:
            return None, ""
        raw_number = match.group(1).replace(",", ".")
        try:
            number = float(raw_number)
        except Exception:
            return None, ""
        unit = match.group(2).strip().lower()
        return number, unit

    def _velocity_to_fps(self, value: object) -> float | None:
        number, unit = self._parse_number_with_unit(value)
        if number is None:
            return None
        if "m/s" in unit:
            return round(number * 3.28084, 1)
        if "fps" in unit or unit == "":
            return round(number, 1)
        return round(number, 1)

    def _pressure_to_psi(self, value: object) -> float | None:
        number, unit = self._parse_number_with_unit(value)
        if number is None:
            return None
        if "bar" in unit:
            return round(number * 14.5037738, 1)
        if "psi" in unit or unit == "":
            return round(number, 1)
        return round(number, 1)

    def _pressure_to_bar(self, value: object) -> float | None:
        number, unit = self._parse_number_with_unit(value)
        if number is None:
            return None
        if "psi" in unit:
            return round(number / 14.5037738, 1)
        if "bar" in unit or unit == "":
            return round(number, 1)
        return round(number, 1)

    def _safe_float(self, value: object) -> float | None:
        try:
            return float(str(value).replace(",", "."))
        except Exception:
            return None

    def _candidate_from_tab_results_dump(
        self, payload: dict, source_name: str
    ) -> dict[str, object]:
        active_tab = payload.get("active_tab") or {}
        active_values = active_tab.get("active") or {}
        tab_values = active_tab.get("tab") or {}
        results = payload.get("results") or {}

        caption = (
            tab_values.get("caption") or active_values.get("caption") or source_name
        )
        tab_file = tab_values.get("file") or active_values.get("file") or ""
        max_pressure_bar = self._pressure_to_bar(results.get("MaxPressure"))
        max_pressure_psi = self._pressure_to_psi(results.get("MaxPressure"))
        predicted_velocity = self._velocity_to_fps(results.get("EndVelocity"))
        case_fill_percent = self._safe_float(results.get("LoadingDensity"))
        coal = self._safe_float(results.get("CartridgeOAL")) or self._safe_float(
            results.get("oal")
        )

        candidate = {
            "name": caption,
            "profile_name": caption,
            "source_dump": source_name,
            "source_file": tab_file,
            "predicted_velocity": predicted_velocity,
            "velocity_fps": predicted_velocity,
            "max_pressure_psi": max_pressure_psi,
            "max_pressure_bar": max_pressure_bar,
            "case_fill_percent": case_fill_percent,
            "optimal_coal": coal,
            "raw_summary": {
                "max_pressure": results.get("MaxPressure"),
                "end_velocity": results.get("EndVelocity"),
                "end_energy": results.get("EndEnergy"),
                "end_time": results.get("EndTime"),
                "burnout_in_barrel": results.get("BurnoutInBarrel"),
                "chunk_count": len(results.get("chunks") or []),
            },
        }
        return candidate

    def _normalize_text(self, value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().lower())

    def _find_matching_profile(self, candidate: dict[str, object]) -> dict | None:
        profiles = self.db.get_all("ammo_profiles")
        candidate_name = self._normalize_text(candidate.get("profile_name"))
        candidate_coal = self._safe_float(candidate.get("optimal_coal"))
        candidate_source_file = str(candidate.get("source_file") or "")
        candidate_basename = (
            Path(candidate_source_file).name.lower() if candidate_source_file else ""
        )
        candidate_velocity = self._safe_float(candidate.get("predicted_velocity"))
        candidate_pressure = self._safe_float(candidate.get("max_pressure_bar"))
        if candidate_name:
            for profile in profiles:
                if self._normalize_text(profile.get("name")) == candidate_name:
                    return profile
        if candidate_name:
            for profile in profiles:
                profile_name = self._normalize_text(profile.get("name"))
                if candidate_name in profile_name or profile_name in candidate_name:
                    return profile
        if candidate_coal is not None:
            for profile in profiles:
                profile_coal = self._safe_float(profile.get("coal"))
                if (
                    profile_coal is not None
                    and abs(profile_coal - candidate_coal) < 0.05
                ):
                    return profile
        source_matches = []
        if candidate_basename:
            for profile in profiles:
                try:
                    context = json.loads(profile.get("component_context_json") or "{}")
                except Exception:
                    context = {}
                source_file = str(context.get("source_file") or "")
                if Path(source_file).name.lower() == candidate_basename:
                    source_matches.append(profile)
            if len(source_matches) == 1:
                return source_matches[0]
            if source_matches:
                scored_matches = []
                for profile in source_matches:
                    score = 0.0
                    existing_rows = self.db.execute_query(
                        "SELECT predicted_velocity, max_pressure_bar FROM grt_data WHERE ammo_profile_id = ?",
                        (profile["id"],),
                    )
                    if existing_rows:
                        row = existing_rows[0]
                        existing_velocity = self._safe_float(
                            row.get("predicted_velocity")
                        )
                        existing_pressure = self._safe_float(
                            row.get("max_pressure_bar")
                        )
                        if (
                            candidate_velocity is not None
                            and existing_velocity is not None
                        ):
                            score += abs(candidate_velocity - existing_velocity)
                        else:
                            score += 1000.0
                        if (
                            candidate_pressure is not None
                            and existing_pressure is not None
                        ):
                            score += abs(candidate_pressure - existing_pressure) * 2.0
                        else:
                            score += 1000.0
                    else:
                        score += 5000.0
                    scored_matches.append((score, profile))
                scored_matches.sort(key=lambda item: item[0])
                return scored_matches[0][1]
        return None

    def _build_grt_record(
        self, ammo_profile_id: int, candidate: dict[str, object]
    ) -> dict[str, object]:
        return {
            "ammo_profile_id": ammo_profile_id,
            "predicted_velocity": candidate.get("predicted_velocity"),
            "max_pressure_psi": candidate.get("max_pressure_psi"),
            "max_pressure_bar": candidate.get("max_pressure_bar"),
            "case_fill_percent": candidate.get("case_fill_percent"),
            "optimal_coal": candidate.get("optimal_coal"),
            "grt_data": json.dumps(candidate, ensure_ascii=False),
            "import_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notes": f"Imported from reference dump {candidate.get('source_dump', '')}",
        }

    def _build_candidate_rows(self) -> list[dict[str, object]]:
        dump_rows = self._read_dump_files()
        candidate_rows: list[dict[str, object]] = []
        for row in dump_rows:
            if row.get("type") != "tab_results":
                continue
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            candidate = self._candidate_from_tab_results_dump(
                payload, Path(row["path"]).name
            )
            match = self._find_matching_profile(candidate)
            candidate_rows.append(
                {
                    "candidate": candidate,
                    "match": match,
                    "path": row["path"],
                }
            )
        self.summary_values["summary_db_matches"].setText(
            str(sum(1 for row in candidate_rows if row.get("match")))
        )
        return candidate_rows

    def _read_dump_files(self) -> list[dict[str, object]]:
        if not self.plugin_dump_dir.exists():
            return []
        dumps: list[dict[str, object]] = []
        for path in sorted(
            self.plugin_dump_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                dumps.append(
                    {
                        "path": path,
                        "type": "invalid_json",
                        "summary": str(exc),
                        "modified": datetime.fromtimestamp(
                            path.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                continue
            dump_type, summary = self._dump_type_and_summary(payload)
            dumps.append(
                {
                    "path": path,
                    "type": dump_type,
                    "summary": summary,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "payload": payload,
                }
            )
        return dumps

    def _analyze_plugin_dumps(self) -> None:
        dump_rows = self._read_dump_files()
        self.dump_table.setRowCount(len(dump_rows))
        for row_index, row in enumerate(dump_rows):
            path = row["path"]
            self.dump_table.setItem(row_index, 0, QTableWidgetItem(Path(path).name))
            self.dump_table.setItem(row_index, 1, QTableWidgetItem(str(row["type"])))
            self.dump_table.setItem(row_index, 2, QTableWidgetItem(str(row["summary"])))
            self.dump_table.setItem(
                row_index, 3, QTableWidgetItem(str(row["modified"]))
            )
        self.dump_table.resizeColumnsToContents()
        self.summary_values["summary_dump_files"].setText(str(len(dump_rows)))
        self.summary_values["summary_latest_dump"].setText(
            Path(dump_rows[0]["path"]).name if dump_rows else "-"
        )
        self._append_status(f"Analyserte {len(dump_rows)} dumpfiler fra plugin-sporet.")

    def _export_ideas_report(self) -> None:
        ideas = self._build_ideas()
        report_path = self.export_dir / "gordon_product_ideas.md"
        lines = [
            "# Gordon Product Ideas (TEMP)",
            "",
            f"Opprettet: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Ideer",
            "",
        ]
        for title, reason in ideas:
            lines.append(f"- **{title}**: {reason}")
        lines.extend(
            [
                "",
                "## Kilder",
                "",
                f"- {self.gordon_data_dir / 'gordon_extraction_summary.json'}",
                f"- {self.gordon_data_dir / 'gordon_bullets_for_hjemmelading.csv'}",
                f"- {self.gordon_data_dir / 'gordon_extracted_propellants_raw.csv'}",
                f"- {self.gordon_data_dir / 'gordon_extracted_measurements.csv'}",
            ]
        )
        report_path.write_text("\n".join(lines), encoding="utf-8")
        self._append_status(f"Eksporterte idérapport til {report_path}")
        QMessageBox.information(
            self, "Idérapport lagret", f"Rapport skrevet til:\n{report_path}"
        )

    def _export_mapped_dump_summary(self) -> None:
        dump_rows = self._read_dump_files()
        mapped = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source_dump_dir": str(self.plugin_dump_dir),
            "dump_count": len(dump_rows),
            "tab_lists": [],
            "active_tabs": [],
            "tab_results": [],
        }
        for row in dump_rows:
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            row_type = row.get("type")
            if row_type == "tab_list":
                mapped["tab_lists"].append(payload)
            elif row_type == "active_tab":
                mapped["active_tabs"].append(payload)
            elif row_type == "tab_results":
                results = payload.get("results") or {}
                chunk_lengths = []
                for chunk in results.get("chunks") or []:
                    data = chunk.get("data") if isinstance(chunk, dict) else None
                    chunk_lengths.append(len(data) if isinstance(data, list) else 0)
                mapped["tab_results"].append(
                    {
                        "active_tab": payload.get("active_tab"),
                        "result_overview": {
                            "tabhandle": (
                                (payload.get("active_tab") or {}).get("active") or {}
                            ).get("tabhandle"),
                            "chunk_count": len(results.get("chunks") or []),
                            "chunk_lengths": chunk_lengths,
                            "scalar_keys": sorted(
                                key for key in results.keys() if key not in {"chunks"}
                            ),
                        },
                    }
                )
        path = self.export_dir / "gordon_mapped_dump_summary.json"
        path.write_text(
            json.dumps(mapped, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._append_status(f"Eksporterte mappet dump-sammendrag til {path}")
        QMessageBox.information(
            self, "Mapped dump lagret", f"Sammendrag skrevet til:\n{path}"
        )

    def _export_grt_import_candidates(self) -> None:
        candidate_rows = self._build_candidate_rows()
        candidates = []
        for row in candidate_rows:
            candidate = dict(row["candidate"])
            match = row.get("match")
            candidate["matched_ammo_profile_id"] = (
                match.get("id") if isinstance(match, dict) else None
            )
            candidate["matched_ammo_profile_name"] = (
                match.get("name") if isinstance(match, dict) else None
            )
            candidates.append(candidate)

        path = self.export_dir / "gordon_grt_import_candidates.json"
        path.write_text(
            json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._append_status(
            f"Eksporterte {len(candidates)} importkandidater til {path}"
        )
        QMessageBox.information(
            self,
            "Importkandidater lagret",
            f"Kandidater skrevet til:\n{path}",
        )

    def _import_candidates_to_db(self) -> None:
        candidate_rows = self._build_candidate_rows()
        if not candidate_rows:
            QMessageBox.information(
                self,
                "Ingen kandidater",
                "Fant ingen tab_results-dumps å importere ennå.",
            )
            return

        imported = 0
        skipped = 0
        for row in candidate_rows:
            match = row.get("match")
            if not isinstance(match, dict):
                skipped += 1
                continue
            candidate = row["candidate"]
            grt_record = self._build_grt_record(int(match["id"]), candidate)
            existing = self.db.execute_query(
                "SELECT id FROM grt_data WHERE ammo_profile_id = ?",
                (match["id"],),
            )
            if existing:
                self.db.update("grt_data", grt_record, "id = ?", (existing[0]["id"],))
            else:
                self.db.insert("grt_data", grt_record)
            imported += 1

        self._append_status(
            f"Importerte {imported} kandidater til grt_data. Hoppet over {skipped} uten match."
        )
        QMessageBox.information(
            self,
            "DB-import fullført",
            f"Importert: {imported}\nHoppet over: {skipped}",
        )

    def _import_measurement_profiles(self) -> None:
        stats, rows = import_measurement_profiles(
            self.gordon_data_dir, self.db, import_grt_seed=True
        )
        self.summary_values["summary_ammo_profiles"].setText(
            str(len(self.db.get_all("ammo_profiles")))
        )
        self._append_status(
            "Importerte måleprofiler til ammo_profiles "
            f"(kandidater={len(rows)}, nye={stats.inserted_profiles}, oppdatert={stats.updated_profiles})."
        )
        QMessageBox.information(
            self,
            "Ammo-profiler importert",
            "\n".join(
                [
                    f"Kandidater: {len(rows)}",
                    f"Nye profiler: {stats.inserted_profiles}",
                    f"Oppdaterte profiler: {stats.updated_profiles}",
                    f"Kulematcher: {stats.matched_bullets}",
                    f"Kruttmatcher: {stats.matched_powders}",
                ]
            ),
        )

    def _export_status_report(self) -> None:
        profiles = self.db.get_all("ammo_profiles")
        grt_rows = self.db.get_all("grt_data")
        bullets = self.db.get_all("bullets")
        powders = self.db.get_all("powder")
        dump_rows = self._read_dump_files()
        payload = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "project_db_path": str(self.project_db_path),
            "plugin_dump_dir": str(self.plugin_dump_dir),
            "counts": {
                "bullets": len(bullets),
                "powders": len(powders),
                "ammo_profiles": len(profiles),
                "grt_data": len(grt_rows),
                "plugin_dumps": len(dump_rows),
            },
            "ammo_profile_calibers": dict(
                Counter(
                    str(profile.get("caliber") or "").strip() for profile in profiles
                ).most_common()
            ),
            "latest_dump": Path(dump_rows[0]["path"]).name if dump_rows else None,
            "next_actions": [
                "Kjør referansepluginen og skriv ut live dumpfiler.",
                "Bruk dumpimporten for å fylle inn flere grt_data-rader fra ekte tabs.",
                "Flytt stabil logikk ut av TEMP-modulen når live-sporet er bevist.",
            ],
        }
        json_path = self.export_dir / "gordon_status_report.json"
        md_path = self.export_dir / "gordon_status_report.md"
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        lines = [
            "# Gordon Status Report (TEMP)",
            "",
            f"Opprettet: {payload['created_at']}",
            "",
            "## Counts",
            "",
        ]
        for key, value in payload["counts"].items():
            lines.append(f"- `{key}`: {value}")
        lines.extend(["", "## Ammo-profiler per kaliber", ""])
        for key, value in payload["ammo_profile_calibers"].items():
            lines.append(f"- `{key}`: {value}")
        lines.extend(["", "## Neste steg", ""])
        for action in payload["next_actions"]:
            lines.append(f"- {action}")
        md_path.write_text("\n".join(lines), encoding="utf-8")
        self._append_status(f"Eksporterte statusrapport til {json_path} og {md_path}")
        QMessageBox.information(
            self,
            "Statusrapport lagret",
            f"Rapporter skrevet til:\n{json_path}\n{md_path}",
        )


# Kompatibilitetsalias. Holdes midlertidig mens eldre imports ryddes bort.
GordonExtractorTemp = ReferenceExtractorTemp
