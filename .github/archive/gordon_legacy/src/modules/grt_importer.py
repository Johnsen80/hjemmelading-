"""
Gordon's Reloading Tool (GRT) Database Importer
Importerer kalibere, kuler, og krutt fra GRT XML-filer
"""

import json
import shutil
import sqlite3
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..utils.drag_models import parse_bc_segments
from ..utils.i18n import tr

# from database import Database  # Not used in current implementation

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPONENT_DB_PATH = REPO_ROOT / "data" / "components_database.json"
GORDON_DB_DEFAULT = REPO_ROOT / "data" / "gordon_database.db"

DEFAULT_COMPONENT_DB: Dict[str, List[Dict[str, Any]]] = {
    "bullets": [],
    "powders": [],
    "primers": [],
    "brass": [],
    "calibers": [],
}


def _normalize_text(value: object) -> str:
    return str(value or "").strip().lower()


def _safe_float(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.replace(",", ".").strip()
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_float_field(value: object, field: str, file_path: str) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        cleaned = value.replace(",", ".").strip()
        if not cleaned:
            return 0.0
    else:
        cleaned = str(value)
    try:
        return float(cleaned)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{Path(file_path).name}: {field} must be numeric, got {value!r}"
        ) from exc


def _require_text_field(value: object, field: str, file_path: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{Path(file_path).name}: {field} is required")
    return cleaned


def _mm_to_in(mm_value: object) -> float:
    mm_float = _safe_float(mm_value)
    if mm_float <= 0:
        return 0.0
    return round(mm_float / 25.4, 3)


def _maybe_mm_to_in(value: object, threshold: float) -> float:
    number = _safe_float(value)
    if number <= 0:
        return 0.0
    if number > threshold:
        return round(number / 25.4, 3)
    return round(number, 3)


def _next_id(items: List[Dict[str, Any]]) -> int:
    if not items:
        return 1
    return int(max(item.get("id", 0) for item in items)) + 1


def _load_component_db(db_path: Path) -> Dict[str, Any]:
    if not db_path.exists():
        return {key: [] for key in DEFAULT_COMPONENT_DB}

    try:
        with open(db_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        data = {}

    for key, default_value in DEFAULT_COMPONENT_DB.items():
        if key not in data or not isinstance(data[key], list):
            data[key] = list(default_value)
    return data


def _save_component_db(db_path: Path, data: Dict[str, Any]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def _caliber_key(caliber: Dict[str, Any]) -> Tuple[str]:
    return (_normalize_text(caliber.get("name")),)


def _bullet_key(bullet: Dict[str, Any]) -> Tuple[str, str, str, float]:
    return (
        _normalize_text(bullet.get("manufacturer")),
        _normalize_text(bullet.get("name")),
        _normalize_text(bullet.get("caliber")),
        round(_safe_float(bullet.get("weight")), 3),
    )


def _powder_key(powder: Dict[str, Any]) -> Tuple[str, str]:
    return (
        _normalize_text(powder.get("manufacturer")),
        _normalize_text(powder.get("name")),
    )


def _primer_key(primer: Dict[str, Any]) -> Tuple[str, str, str, str]:
    return (
        _normalize_text(primer.get("manufacturer")),
        _normalize_text(primer.get("name")),
        _normalize_text(primer.get("type")),
        _normalize_text(primer.get("size")),
    )


def _upsert_caliber(db: Dict[str, Any], caliber: Dict[str, Any]) -> bool:
    calibers = db["calibers"]
    existing_keys = {_caliber_key(item) for item in calibers}
    key = _caliber_key(caliber)
    if key in existing_keys or not caliber.get("name"):
        return False
    caliber = dict(caliber)
    caliber["id"] = _next_id(calibers)
    calibers.append(caliber)
    return True


def _upsert_bullet(db: Dict[str, Any], bullet: Dict[str, Any]) -> bool:
    bullets = db["bullets"]
    existing_keys = {_bullet_key(item) for item in bullets}
    key = _bullet_key(bullet)
    if key in existing_keys or not bullet.get("name"):
        return False
    bullet = dict(bullet)
    bullet["id"] = _next_id(bullets)
    bullets.append(bullet)
    return True


def _upsert_powder(db: Dict[str, Any], powder: Dict[str, Any]) -> bool:
    powders = db["powders"]
    existing_keys = {_powder_key(item) for item in powders}
    key = _powder_key(powder)
    if key in existing_keys or not powder.get("name"):
        return False
    powder = dict(powder)
    powder["id"] = _next_id(powders)
    powders.append(powder)
    return True


def _upsert_primer(db: Dict[str, Any], primer: Dict[str, Any]) -> bool:
    primers = db["primers"]
    existing_keys = {_primer_key(item) for item in primers}
    key = _primer_key(primer)
    if key in existing_keys or not primer.get("name"):
        return False
    primer = dict(primer)
    primer["id"] = _next_id(primers)
    primers.append(primer)
    return True


def _map_projectile_to_bullet(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "manufacturer": data.get("manufacturer", ""),
        "name": data.get("name", ""),
        "caliber": data.get("caliber", ""),
        "diameter": _mm_to_in(data.get("diameter_mm")),
        "weight": _safe_float(data.get("weight_grains")),
        "bc_g1": _safe_float(data.get("bc_g1")),
        "bc_g7": _safe_float(data.get("bc_g7")),
        "bc_segments_json": _normalize_bc_segments(
            data.get("bc_segments_json")
            or data.get("bc_segments")
            or data.get("drag_segments")
        ),
        "length": _mm_to_in(data.get("length_mm")),
        "type": data.get("type", ""),
        "notes": data.get("description", ""),
    }


def _map_powder(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "manufacturer": data.get("manufacturer", ""),
        "name": data.get("name", ""),
        "burn_rate": data.get("burn_rate", ""),
        "density": _safe_float(data.get("density")),
        "best_for": "",
        "temp_stable": "Unknown",
        "notes": data.get("description", ""),
    }


def _map_caliber(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": data.get("name", ""),
        "alt_name": data.get("alt_name", ""),
        "case_length_mm": _safe_float(data.get("case_length_mm")),
        "case_capacity_ml": _safe_float(data.get("case_capacity_ml")),
        "max_pressure_bar": _safe_float(data.get("max_pressure_bar")),
        "bullet_diameter_mm": _safe_float(data.get("bullet_diameter_mm")),
        "neck_diameter_mm": _safe_float(data.get("neck_diameter_mm")),
        "base_diameter_mm": _safe_float(data.get("base_diameter_mm")),
        "rim_diameter_mm": _safe_float(data.get("rim_diameter_mm")),
        "standard": data.get("standard", ""),
        "origin": data.get("origin", ""),
        "description": data.get("description", ""),
    }


def _coalesce(data: Dict[str, Any], keys: List[str], default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _normalize_bc_segments(value: object) -> str | None:
    if value in (None, ""):
        return None
    segments = parse_bc_segments(value)
    if not segments:
        return None
    return json.dumps(segments, ensure_ascii=True)


def _map_gordon_projectile(row: Dict[str, Any]) -> Dict[str, Any]:
    diameter = _maybe_mm_to_in(_coalesce(row, ["diameter", "diameter_mm", "dia"]), 1.5)
    length = _maybe_mm_to_in(_coalesce(row, ["length", "length_mm", "len"]), 3.0)
    return {
        "manufacturer": _coalesce(row, ["manufacturer", "maker", "brand"]),
        "name": _coalesce(row, ["name", "projectile_name", "designation"]),
        "caliber": _coalesce(row, ["caliber", "cal"]),
        "diameter": diameter,
        "weight": _safe_float(_coalesce(row, ["weight", "weight_gr", "weight_grain"])),
        "bc_g1": _safe_float(_coalesce(row, ["bc", "bc_g1", "g1"])),
        "bc_g7": _safe_float(_coalesce(row, ["bc7", "bc_g7", "g7"])),
        "bc_segments_json": _normalize_bc_segments(
            row.get("bc_segments_json")
            or row.get("bc_segments")
            or row.get("drag_segments")
        ),
        "length": length,
        "type": _coalesce(row, ["type", "bullet_type"]),
        "notes": _coalesce(row, ["descr", "description", "notes"]),
    }


def _map_gordon_powder(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "manufacturer": _coalesce(row, ["manufacturer", "maker", "brand"]),
        "name": _coalesce(row, ["name", "powder_name"]),
        "burn_rate": _coalesce(row, ["burn_rate", "burnrate"]),
        "density": _safe_float(_coalesce(row, ["density", "bulk_density"])),
        "best_for": "",
        "temp_stable": "Unknown",
        "notes": _coalesce(row, ["descr", "description", "notes"]),
    }


def _map_gordon_primer(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "manufacturer": _coalesce(row, ["manufacturer", "maker", "brand"]),
        "name": _coalesce(row, ["name", "primer_name"]),
        "size": _coalesce(row, ["size", "primer_size"]),
        "type": _coalesce(row, ["type", "primer_type"]),
        "brisance": _coalesce(row, ["brisance", "power"]),
        "notes": _coalesce(row, ["descr", "description", "notes"]),
    }


def _read_table(cursor: sqlite3.Cursor, table: str) -> List[Dict[str, Any]]:
    cursor.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def import_gordon_database_to_json(
    db_path: Path, component_db_path: Path
) -> Dict[str, int]:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    db = _load_component_db(component_db_path)
    counts = {"bullets": 0, "powders": 0, "primers": 0, "skipped": 0}

    if "projectile" in tables:
        for row in _read_table(cursor, "projectile"):
            if _upsert_bullet(db, _map_gordon_projectile(row)):
                counts["bullets"] += 1
            else:
                counts["skipped"] += 1

    if "powder" in tables:
        for row in _read_table(cursor, "powder"):
            if _upsert_powder(db, _map_gordon_powder(row)):
                counts["powders"] += 1
            else:
                counts["skipped"] += 1

    if "primer" in tables:
        for row in _read_table(cursor, "primer"):
            if _upsert_primer(db, _map_gordon_primer(row)):
                counts["primers"] += 1
            else:
                counts["skipped"] += 1

    conn.close()

    _save_component_db(component_db_path, db)
    return counts


class GRTParser:
    """Parser for GRT XML files"""

    @staticmethod
    def parse_caliber(file_path: str) -> Dict:
        """Parse .caliber XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        data = {}
        for var in root.findall(".//var"):
            name = var.get("name")
            value = var.get("value", "")
            # URL decode values
            value = urllib.parse.unquote(value)
            data[name] = value

        name = _require_text_field(
            _coalesce(data, ["cipname", "name", "altname"]),
            "name",
            file_path,
        )

        return {
            "name": name,
            "alt_name": data.get("altname", ""),
            "case_length_mm": _parse_float_field(data.get("L3"), "L3", file_path),
            "case_capacity_ml": _parse_float_field(data.get("V"), "V", file_path),
            "max_pressure_bar": _parse_float_field(data.get("Pmax"), "Pmax", file_path),
            "bullet_diameter_mm": _parse_float_field(data.get("G1"), "G1", file_path),
            "neck_diameter_mm": _parse_float_field(data.get("E1"), "E1", file_path),
            "base_diameter_mm": _parse_float_field(data.get("P1"), "P1", file_path),
            "rim_diameter_mm": _parse_float_field(data.get("R1"), "R1", file_path),
            "standard": data.get("standard", ""),
            "origin": data.get("ciporigin", ""),
            "description": data.get("descr", ""),
        }

    @staticmethod
    def parse_projectile(file_path: str) -> Dict:
        """Parse .projectile XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        data = {}
        for var in root.findall(".//var"):
            name = var.get("name")
            value = var.get("value", "")
            value = urllib.parse.unquote(value)
            data[name] = value

        name = _require_text_field(data.get("name"), "name", file_path)

        return {
            "name": name,
            "manufacturer": data.get("manufacturer", ""),
            "caliber": data.get("caliber", ""),
            "weight_grains": _parse_float_field(
                data.get("weight"), "weight", file_path
            ),
            "diameter_mm": _parse_float_field(
                data.get("diameter"), "diameter", file_path
            ),
            "length_mm": _parse_float_field(data.get("length"), "length", file_path),
            "bc_g1": _parse_float_field(data.get("bc"), "bc", file_path),
            "bc_g7": _parse_float_field(data.get("bc7"), "bc7", file_path),
            "bc_segments_json": _normalize_bc_segments(
                data.get("bc_segments_json")
                or data.get("bc_segments")
                or data.get("drag_segments")
            ),
            "type": data.get("type", ""),
            "description": data.get("descr", ""),
        }

    @staticmethod
    def parse_powder(file_path: str) -> Dict:
        """Parse .powder XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        data = {}
        for var in root.findall(".//var"):
            name = var.get("name")
            value = var.get("value", "")
            value = urllib.parse.unquote(value)
            data[name] = value

        name = _require_text_field(data.get("name"), "name", file_path)

        return {
            "name": name,
            "manufacturer": data.get("manufacturer", ""),
            "burn_rate": data.get("burn_rate", ""),
            "density": _parse_float_field(data.get("density"), "density", file_path),
            "description": data.get("descr", ""),
        }


class GRTDownloadThread(QThread):
    """Background thread for downloading GRT database from GitHub"""

    progress = pyqtSignal(str, int)  # message, percentage
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, categories: List[str], db_path: Path):
        super().__init__()
        self.categories = categories
        self.db_path = db_path
        self.archive_url = (
            "https://github.com/zen/grt_databases/archive/refs/heads/main.zip"
        )

    def run(self):
        download_dir = Path(tempfile.mkdtemp(prefix="grt_download_"))
        try:
            self.progress.emit(
                "Starter nedlasting av komponentdatabase fra GitHub...", 0
            )

            archive_path = download_dir / "grt_databases.zip"
            request = urllib.request.Request(
                self.archive_url,
                headers={"User-Agent": "Hjemmelading-GRT-Importer"},
            )
            with urllib.request.urlopen(request) as response, open(
                archive_path, "wb"
            ) as handle:
                shutil.copyfileobj(response, handle)

            self.progress.emit("Pakker ut database...", 10)
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(download_dir)

            repo_root = next(
                (
                    path
                    for path in download_dir.iterdir()
                    if path.is_dir() and path.name.startswith("grt_databases-")
                ),
                None,
            )
            if repo_root is None:
                raise FileNotFoundError("Fant ikke utpakket komponentdatabase.")

            category_map = {
                "calibers": {
                    "folder": "calibers",
                    "pattern": "*.caliber",
                    "parser": GRTParser.parse_caliber,
                    "mapper": _map_caliber,
                    "upsert": _upsert_caliber,
                },
                "projectiles": {
                    "folder": "projectiles",
                    "pattern": "*.projectile",
                    "parser": GRTParser.parse_projectile,
                    "mapper": _map_projectile_to_bullet,
                    "upsert": _upsert_bullet,
                },
                "powders": {
                    "folder": "powders",
                    "pattern": "*.powder",
                    "parser": GRTParser.parse_powder,
                    "mapper": _map_powder,
                    "upsert": _upsert_powder,
                },
            }

            total_files = 0
            file_groups = []
            for category in self.categories:
                config = category_map.get(category)
                if not config:
                    continue
                folder = repo_root / config["folder"]
                files = (
                    sorted(folder.glob(config["pattern"])) if folder.exists() else []
                )
                file_groups.append((category, config, files))
                total_files += len(files)

            if total_files == 0:
                raise FileNotFoundError(
                    "Ingen støttede datafiler funnet i nedlastingen."
                )

            db = _load_component_db(self.db_path)
            added = {"calibers": 0, "projectiles": 0, "powders": 0}
            skipped = 0
            errors: list[str] = []
            processed = 0

            for category, config, files in file_groups:
                self.progress.emit(
                    f"Importerer {category} ({len(files)} filer)...",
                    20 + int((processed / total_files) * 80),
                )
                for file_path in files:
                    try:
                        parsed = config["parser"](str(file_path))
                        mapped = config["mapper"](parsed)
                        if config["upsert"](db, mapped):
                            added[category] += 1
                        else:
                            skipped += 1
                    except Exception as exc:
                        errors.append(f"{file_path.name}: {exc}")

                    processed += 1
                    if processed % 25 == 0 or processed == total_files:
                        percentage = 20 + int((processed / total_files) * 80)
                        self.progress.emit("Importer data...", percentage)

            _save_component_db(self.db_path, db)
            self.progress.emit("Import fullfort!", 100)

            summary = (
                "Importerte "
                f"{added['calibers']} kalibere, "
                f"{added['projectiles']} kuler, "
                f"{added['powders']} krutt. "
                f"Hoppet over {skipped} duplikater."
            )
            if errors:
                summary += f" Feil: {len(errors)}."
            self.finished.emit(True, summary)

        except Exception as exc:
            self.finished.emit(False, f"Feil ved nedlasting: {exc}")
        finally:
            shutil.rmtree(download_dir, ignore_errors=True)


class ReferenceImporter(QWidget):
    """
    GUI for import av eksterne referansedata.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.component_db_path = COMPONENT_DB_PATH
        self.db = None  # Database not implemented yet - uses JSON instead
        self.download_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Komponentimport")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Importer kalibere, kuler og krutt fra eksterne referansekilder.\n"
            "Bruk denne siden til å hente inn komponentdata til ditt eget bibliotek."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # GitHub Import
        github_group = QGroupBox("Import fra GitHub (Anbefalt)")
        github_layout = QVBoxLayout()

        github_desc = QLabel(
            "Last ned den komplette komponentdatabasen fra GitHub:\n"
            "• 100+ kalibere (CIP/SAAMI standarder)\n"
            "• 500+ kuler (alle store produsenter)\n"
            "• 200+ krutt (Vihtavuori, Hodgdon, Alliant, etc.)"
        )
        github_desc.setWordWrap(True)
        github_layout.addWidget(github_desc)

        # Checkboxes for categories
        self.cb_calibers = QCheckBox("Kalibere (.caliber)")
        self.cb_calibers.setChecked(True)
        github_layout.addWidget(self.cb_calibers)

        self.cb_projectiles = QCheckBox("Kuler (.projectile)")
        self.cb_projectiles.setChecked(True)
        github_layout.addWidget(self.cb_projectiles)

        self.cb_powders = QCheckBox("Krutt (.powder)")
        self.cb_powders.setChecked(True)
        github_layout.addWidget(self.cb_powders)

        github_btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("Last ned fra GitHub")
        self.btn_download.clicked.connect(self.download_from_github)
        github_btn_layout.addWidget(self.btn_download)
        github_layout.addLayout(github_btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        github_layout.addWidget(self.progress_bar)

        github_group.setLayout(github_layout)
        layout.addWidget(github_group)

        # Local File Import
        local_group = QGroupBox("Import fra lokale filer")
        local_layout = QVBoxLayout()

        local_desc = QLabel(
            "Har du allerede komponentfiler lokalt? Importer direkte fra dine filer:"
        )
        local_layout.addWidget(local_desc)

        # File type selector
        file_type_layout = QHBoxLayout()
        file_type_layout.addWidget(QLabel("Filtype:"))
        self.combo_filetype = QComboBox()
        self.combo_filetype.addItems(
            [".caliber (Kalibere)", ".projectile (Kuler)", ".powder (Krutt)"]
        )
        file_type_layout.addWidget(self.combo_filetype)
        file_type_layout.addStretch()
        local_layout.addLayout(file_type_layout)

        # Import buttons
        btn_layout = QHBoxLayout()

        self.btn_import_file = QPushButton("Importer enkeltfil")
        self.btn_import_file.clicked.connect(self.import_single_file)
        btn_layout.addWidget(self.btn_import_file)

        self.btn_import_folder = QPushButton("Importer mappe")
        self.btn_import_folder.clicked.connect(self.import_folder)
        btn_layout.addWidget(self.btn_import_folder)

        self.btn_import_db = QPushButton("Importer ekstern database (.db)")
        self.btn_import_db.clicked.connect(self.import_gordon_database)
        btn_layout.addWidget(self.btn_import_db)

        local_layout.addLayout(btn_layout)
        local_group.setLayout(local_layout)
        layout.addWidget(local_group)

        # Results area
        results_group = QGroupBox("Importresultater")
        results_layout = QVBoxLayout()

        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        self.text_results.setMaximumHeight(200)
        self.text_results.setHtml(
            "<p style='color: #7f8c8d;'>"
            "Importresultater vil vises her...<br><br>"
            "<b>Tips:</b> Kildedata med åpen lisens kan trygt flettes inn i ditt lokale bibliotek."
            "</p>"
        )
        results_layout.addWidget(self.text_results)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Info footer
        info = QLabel(
            "Kildedatasett med åpen lisens kan brukes som grunnlag for komponentbiblioteket."
        )
        info.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()
        self.setLayout(layout)

    def download_from_github(self):
        """Download component database from GitHub"""
        categories = []
        if self.cb_calibers.isChecked():
            categories.append("calibers")
        if self.cb_projectiles.isChecked():
            categories.append("projectiles")
        if self.cb_powders.isChecked():
            categories.append("powders")

        if not categories:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("grt_import_select_category")
            )
            return

        # Start download thread
        for button in (
            self.btn_download,
            self.btn_import_file,
            self.btn_import_folder,
            self.btn_import_db,
        ):
            button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.download_thread = GRTDownloadThread(categories, self.component_db_path)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_progress(self, message: str, percentage: int):
        """Handle download progress updates"""
        self.progress_bar.setValue(percentage)
        self.text_results.append(f"<p style='color: #3498db;'>{message}</p>")

    def on_download_finished(self, success: bool, message: str):
        """Handle download completion"""
        for button in (
            self.btn_download,
            self.btn_import_file,
            self.btn_import_folder,
            self.btn_import_db,
        ):
            button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.text_results.append(f"<p style='color: #27ae60;'><b>{message}</b></p>")
            QMessageBox.information(self, "Suksess", message)
        else:
            self.text_results.append(f"<p style='color: #e74c3c;'><b>{message}</b></p>")
            QMessageBox.critical(self, "Feil", message)

    def import_single_file(self):
        """Import a single GRT file"""
        filetype = self.combo_filetype.currentText()

        if ".caliber" in filetype:
            filter_str = "Kaliberfiler (*.caliber)"
            parser_func = self.import_caliber_file
        elif ".projectile" in filetype:
            filter_str = "Prosjektilfiler (*.projectile)"
            parser_func = self.import_projectile_file
        elif ".powder" in filetype:
            filter_str = "Kruttfiler (*.powder)"
            parser_func = self.import_powder_file
        else:
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Velg datafil", "", filter_str)

        if file_path:
            try:
                added = parser_func(file_path)
                if added:
                    self.text_results.append(
                        f"<p style='color: #27ae60;'>Importerte: {Path(file_path).name}</p>"
                    )
                else:
                    self.text_results.append(
                        f"<p style='color: #f39c12;'>Finnes allerede: {Path(file_path).name}</p>"
                    )
            except Exception as e:
                self.text_results.append(
                    f"<p style='color: #e74c3c;'>Feil ved import av {Path(file_path).name}: {str(e)}</p>"
                )

    def import_folder(self):
        """Import all GRT files from a folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Velg mappe med datafiler")

        if not folder_path:
            return

        filetype = self.combo_filetype.currentText()

        if ".caliber" in filetype:
            pattern = "*.caliber"
            parser_func = self.import_caliber_file
        elif ".projectile" in filetype:
            pattern = "*.projectile"
            parser_func = self.import_projectile_file
        elif ".powder" in filetype:
            pattern = "*.powder"
            parser_func = self.import_powder_file
        else:
            return

        folder = Path(folder_path)
        files = list(folder.glob(pattern))

        if not files:
            QMessageBox.warning(
                self, "Ingen filer", f"Fant ingen {pattern} filer i den valgte mappen."
            )
            return

        added_count = 0
        skipped_count = 0
        error_count = 0

        db = _load_component_db(self.component_db_path)

        self.text_results.append(
            f"<p style='color: #3498db;'><b>Starter import av {len(files)} filer...</b></p>"
        )

        for file_path in files:
            try:
                added = parser_func(str(file_path), db)
                if added:
                    added_count += 1
                    self.text_results.append(
                        f"<p style='color: #27ae60;'>{file_path.name}</p>"
                    )
                else:
                    skipped_count += 1
                    self.text_results.append(
                        f"<p style='color: #f39c12;'>{file_path.name} (duplikat)</p>"
                    )
            except Exception as e:
                error_count += 1
                self.text_results.append(
                    f"<p style='color: #e74c3c;'>{file_path.name}: {str(e)}</p>"
                )

        _save_component_db(self.component_db_path, db)

        # Summary
        self.text_results.append(
            f"<p style='color: #2c3e50;'><b>"
            f"Ferdig! Lagt til: {added_count}, Duplikater: {skipped_count}, Feil: {error_count}"
            f"</b></p>"
        )

        QMessageBox.information(
            self,
            "Import fullført",
            f"Importerte {added_count} av {len(files)} filer.\n"
            f"Duplikater: {skipped_count}\n"
            f"Feil: {error_count}",
        )

    def import_gordon_database(self):
        """Import Gordon's SQLite database into JSON component DB"""
        initial_dir = str(GORDON_DB_DEFAULT) if GORDON_DB_DEFAULT.exists() else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Velg ekstern database (.db)",
            initial_dir,
            "SQLite Database (*.db);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            counts = import_gordon_database_to_json(
                Path(file_path), self.component_db_path
            )
            summary = (
                "Importerte "
                f"{counts['bullets']} kuler, "
                f"{counts['powders']} krutt, "
                f"{counts['primers']} tennhetter. "
                f"Duplikater: {counts['skipped']}."
            )
            self.text_results.append(f"<p style='color: #27ae60;'>{summary}</p>")
            QMessageBox.information(self, "Import fullfort", summary)
        except Exception as exc:
            self.text_results.append(
                f"<p style='color: #e74c3c;'>Feil ved import: {exc}</p>"
            )
            QMessageBox.critical(self, "Feil", str(exc))

    def import_caliber_file(
        self, file_path: str, db: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Import a caliber file to database"""
        data = GRTParser.parse_caliber(file_path)
        owned_db = db is None
        if db is None:
            db = _load_component_db(self.component_db_path)
        added = _upsert_caliber(db, _map_caliber(data))
        if owned_db:
            _save_component_db(self.component_db_path, db)
        return added

    def import_projectile_file(
        self, file_path: str, db: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Import a projectile file to database"""
        data = GRTParser.parse_projectile(file_path)
        owned_db = db is None
        if db is None:
            db = _load_component_db(self.component_db_path)
        added = _upsert_bullet(db, _map_projectile_to_bullet(data))
        if owned_db:
            _save_component_db(self.component_db_path, db)
        return added

    def import_powder_file(
        self, file_path: str, db: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Import a powder file to database"""
        data = GRTParser.parse_powder(file_path)
        owned_db = db is None
        if db is None:
            db = _load_component_db(self.component_db_path)
        added = _upsert_powder(db, _map_powder(data))
        if owned_db:
            _save_component_db(self.component_db_path, db)
        return added


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ReferenceImporter()
    window.show()
    sys.exit(app.exec())


# Kompatibilitetsalias. Holdes midlertidig mens eldre imports ryddes bort.
GRTImporter = ReferenceImporter
