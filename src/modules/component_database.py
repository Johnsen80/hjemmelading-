"""
Component Database Manager
Comprehensive database for bullets, powders, primers, brass

Features:
- Add custom components not in database
- Import from CSV/JSON
- Search & filter
- Auto-complete when entering data
- Share component data with community (future)
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..logging_config import configure_logging, get_logger
from ..tools.cartridge_standards_service import (
    import_cartridge_standards_from_knowledge_base,
)
from ..tools.legacy_component_library_migration_service import (
    migrate_legacy_component_tables_into_library,
)
from ..utils.drag_models import parse_bc_segments
from ..utils.i18n import tr

configure_logging()
logger = get_logger(__name__)


COMPONENT_DB_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "components_database.json"
)
COMPONENT_DB_SCHEMA_VERSION = "component_database.v1"
REFERENCE_SNAPSHOT_SOURCE_SYSTEMS = ("reference_readable", "reference_snapshot")


def _component_db_template() -> dict[str, list[dict[str, Any]]]:
    return {
        "bullets": [],
        "powders": [],
        "primers": [],
        "brass": [],
    }


def load_component_database_json(
    path: str | Path | None = None,
) -> dict[str, list[dict[str, Any]]]:
    db_path = Path(path) if path else COMPONENT_DB_PATH
    if not db_path.exists():
        return _component_db_template()
    with db_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    merged = _component_db_template()
    for key in merged:
        value = data.get(key, [])
        merged[key] = value if isinstance(value, list) else []
    return merged


def save_component_database_json(
    data: dict[str, list[dict[str, Any]]], path: str | Path | None = None
) -> None:
    db_path = Path(path) if path else COMPONENT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with db_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "meta": {
                    "schema_version": COMPONENT_DB_SCHEMA_VERSION,
                },
                "data": data,
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )


def _next_component_id(records: list[dict[str, Any]]) -> int:
    max_id = 0
    for record in records:
        try:
            max_id = max(max_id, int(record.get("id", 0) or 0))
        except Exception:
            continue
    return max_id + 1


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_float(value: Any) -> float:
    raw = str(value or "").strip()
    if not raw:
        return 0.0
    raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _normalize_bc_segments_json(raw_text: str) -> str | None:
    text = str(raw_text or "").strip()
    if not text:
        return None
    parsed = parse_bc_segments(text)
    if not parsed:
        return None
    return json.dumps(parsed, ensure_ascii=False)


def _format_bc_segments_summary(raw_value: str | None) -> str:
    segments = parse_bc_segments(raw_value)
    if not segments:
        return tr("component_db_bc_segments_missing")
    parts: list[str] = []
    for segment in segments[:3]:
        model = str(segment.get("model") or "AUTO")
        min_v = segment.get("velocity_fps_min")
        max_v = segment.get("velocity_fps_max")
        bc_value = segment.get("bc_g7") or segment.get("bc_g1") or segment.get("bc")
        if bc_value is None:
            continue
        if max_v is not None:
            parts.append(
                f"{model} {float(bc_value):.3f} @ {float(min_v or 0):.0f}-{float(max_v):.0f} fps"
            )
        else:
            parts.append(
                f"{model} {float(bc_value):.3f} @ {float(min_v or 0):.0f}+ fps"
            )
    if not parts:
        return tr("component_db_bc_segments_missing")
    summary = "; ".join(parts)
    if len(segments) > 3:
        summary += tr("component_db_bc_segments_more", count=str(len(segments) - 3))
    return summary


def _format_cartridge_standard_summary(standard: dict[str, Any] | None) -> str:
    data = standard or {}
    if not data:
        return "Select a cartridge standard to view dimensions, pressure, and drawing/PDF links."
    parts = [
        f"Caliber: {data.get('caliber_name') or '-'}",
        f"Standard: {data.get('standard_body') or data.get('standard_label') or '-'}",
    ]
    if data.get("max_pressure_bar") is not None:
        parts.append(
            f"Max Pressure: {float(data.get('max_pressure_bar') or 0.0):.1f} bar"
        )
    if data.get("oal_mm") is not None:
        parts.append(f"OAL: {float(data.get('oal_mm') or 0.0):.2f} mm")
    if data.get("case_length_mm") is not None:
        parts.append(f"Case Length: {float(data.get('case_length_mm') or 0.0):.2f} mm")
    if data.get("case_capacity_ml") is not None:
        parts.append(
            f"Case Capacity: {float(data.get('case_capacity_ml') or 0.0):.3f} ml"
        )
    pdf_url = str(data.get("drawing_pdf_url") or "").strip()
    if pdf_url:
        parts.append(f"CIP/PDF: {pdf_url}")
    return " | ".join(parts)


def import_component_csv_rows(
    file_path: str | Path, component_type: str
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    file_path = str(file_path)
    imported: list[dict[str, Any]] = []
    skipped = 0
    with open(file_path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized = {
                str(key or "").strip().lower(): value for key, value in row.items()
            }
            if component_type == "bullets":
                name = _normalize_text(
                    normalized.get("name") or normalized.get("bullet name")
                )
                manufacturer = _normalize_text(
                    normalized.get("manufacturer") or normalized.get("maker")
                )
                if not name:
                    skipped += 1
                    continue
                imported.append(
                    {
                        "manufacturer": manufacturer,
                        "name": name,
                        "caliber": _normalize_text(normalized.get("caliber")),
                        "weight": _normalize_float(
                            normalized.get("weight") or normalized.get("weight (gr)")
                        ),
                        "bc_g1": _normalize_float(
                            normalized.get("bc_g1") or normalized.get("bc g1")
                        ),
                        "bc_g7": _normalize_float(
                            normalized.get("bc_g7") or normalized.get("bc g7")
                        ),
                        "length": _normalize_float(
                            normalized.get("length") or normalized.get("length (mm)")
                        ),
                        "diameter": _normalize_float(
                            normalized.get("diameter")
                            or normalized.get("diameter (mm)")
                        ),
                        "type": _normalize_text(normalized.get("type")),
                        "notes": _normalize_text(normalized.get("notes")),
                    }
                )
            elif component_type == "powders":
                name = _normalize_text(
                    normalized.get("name") or normalized.get("powder name")
                )
                manufacturer = _normalize_text(
                    normalized.get("manufacturer") or normalized.get("brand")
                )
                if not name:
                    skipped += 1
                    continue
                imported.append(
                    {
                        "manufacturer": manufacturer,
                        "name": name,
                        "burn_rate": _normalize_text(
                            normalized.get("burn_rate") or normalized.get("burn rate")
                        ),
                        "density": _normalize_float(
                            normalized.get("density")
                            or normalized.get("density (g/cc)")
                        ),
                        "best_for": _normalize_text(
                            normalized.get("best_for") or normalized.get("best for")
                        ),
                        "temp_stable": _normalize_text(
                            normalized.get("temp_stable")
                            or normalized.get("temp stable")
                        ).lower()
                        in {"yes", "true", "1"},
                        "notes": _normalize_text(normalized.get("notes")),
                    }
                )
    return imported, {"imported": len(imported), "skipped": skipped}


def merge_component_records(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]], component_type: str
) -> dict[str, int]:
    existing_keys = set()
    for record in existing:
        if component_type == "bullets":
            key = (
                _normalize_text(record.get("manufacturer")).lower(),
                _normalize_text(record.get("name")).lower(),
                _normalize_text(record.get("caliber")).lower(),
                f"{_normalize_float(record.get('weight')):.3f}",
            )
        else:
            key = (
                _normalize_text(record.get("manufacturer")).lower(),
                _normalize_text(record.get("name")).lower(),
            )
        existing_keys.add(key)

    added = 0
    duplicates = 0
    next_id = _next_component_id(existing)
    for record in incoming:
        if component_type == "bullets":
            key = (
                _normalize_text(record.get("manufacturer")).lower(),
                _normalize_text(record.get("name")).lower(),
                _normalize_text(record.get("caliber")).lower(),
                f"{_normalize_float(record.get('weight')):.3f}",
            )
        else:
            key = (
                _normalize_text(record.get("manufacturer")).lower(),
                _normalize_text(record.get("name")).lower(),
            )
        if key in existing_keys:
            duplicates += 1
            continue
        row = dict(record)
        row["id"] = next_id
        next_id += 1
        existing.append(row)
        existing_keys.add(key)
        added += 1
    return {"added": added, "duplicates": duplicates}


def export_component_rows_to_csv(
    rows: list[dict[str, Any]], file_path: str | Path
) -> None:
    if not rows:
        raise ValueError("No component rows to export")
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["export_schema_version", *list(rows[0].keys())]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {
                "export_schema_version": COMPONENT_DB_SCHEMA_VERSION,
                **row,
            }
            for row in rows
        )


def export_component_database(
    data: dict[str, list[dict[str, Any]]],
    file_path: str | Path,
    component_type: str | None = None,
) -> None:
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        if not component_type:
            raise ValueError("component_type is required for CSV export")
        rows = data.get(component_type, [])
        export_component_rows_to_csv(rows, file_path)
        return
    save_component_database_json(data, file_path)


def build_bullet_library_rows(database) -> list[dict[str, Any]]:
    """Return bullet library rows with current inventory and lot counts."""
    if database is None:
        return []
    rows = database.execute_query(
        """
        SELECT
            b.*,
            COUNT(cl.id) AS lot_count,
            COALESCE(SUM(cl.quantity_remaining), 0) AS lot_quantity_remaining
        FROM bullets b
        LEFT JOIN component_lots cl
            ON cl.component_type = 'bullet' AND cl.component_id = b.id
        GROUP BY b.id
        ORDER BY b.manufacturer, b.weight_grains, b.name
        """
    )
    return [dict(row) for row in rows]


def build_bullet_detail_snapshot(database, bullet_id: int) -> dict[str, Any]:
    """Build a bullet reference + owned lots snapshot for the library UI."""
    if database is None or not bullet_id:
        return {}
    bullet = database.get_by_id("bullets", int(bullet_id))
    if not bullet:
        return {}
    bullet_row = dict(bullet)
    reference_snapshots = [
        dict(row)
        for row in database.execute_query(
            """
            SELECT *
            FROM component_reference_snapshots
            WHERE source_system IN (?, ?)
              AND component_type = 'bullet'
              AND lower(coalesce(manufacturer, '')) = lower(?)
              AND (
                    lower(coalesce(caliber, '')) = lower(?)
                 OR coalesce(caliber, '') = ''
              )
              AND (
                    lower(coalesce(model_name, '')) = lower(?)
                 OR lower(coalesce(display_name, '')) LIKE lower(?)
              )
            ORDER BY updated_date DESC, id DESC
            """,
            (
                *REFERENCE_SNAPSHOT_SOURCE_SYSTEMS,
                bullet_row.get("manufacturer") or "",
                bullet_row.get("caliber") or "",
                bullet_row.get("name") or "",
                f"%{bullet_row.get('name') or ''}%",
            ),
        )
    ]
    lots = [
        dict(row)
        for row in database.execute_query(
            """
            SELECT *
            FROM component_lots
            WHERE component_type = 'bullet' AND component_id = ?
            ORDER BY is_active DESC, created_date DESC, id DESC
            """,
            (int(bullet_id),),
        )
    ]
    lot_rows: list[dict[str, Any]] = []
    for lot in lots:
        stats = database.get_component_lot_stats(int(lot["id"])) or {}
        sessions = database.get_component_measurement_sessions(int(lot["id"])) or []
        lot_rows.append(
            {
                **lot,
                "stats": dict(stats) if stats else {},
                "measurement_session_count": len(sessions),
            }
        )
    return {
        "bullet": bullet_row,
        "lots": lot_rows,
        "reference_snapshots": reference_snapshots,
    }


def format_bullet_detail_summary(snapshot: dict[str, Any]) -> str:
    """Render a compact textual summary for the selected bullet."""
    bullet = snapshot.get("bullet") or {}
    if not bullet:
        return "Select a bullet to view catalog data and your own lots."
    lots = snapshot.get("lots") or []
    reference_snapshots = snapshot.get("reference_snapshots") or []
    source = str(bullet.get("source") or "manual").strip()
    parts = [
        f"<b>{bullet.get('manufacturer') or '-'}</b> {bullet.get('name') or '-'}",
        f"Caliber: {bullet.get('caliber') or '-'}",
        f"Weight: {float(bullet.get('weight_grains') or 0.0):.1f} gr",
    ]
    if bullet.get("length_mm") is not None:
        parts.append(f"Standard Length: {float(bullet.get('length_mm') or 0.0):.3f} mm")
    if bullet.get("diameter_mm") is not None:
        parts.append(
            f"Standard Diameter: {float(bullet.get('diameter_mm') or 0.0):.3f} mm"
        )
    if bullet.get("bc_g7"):
        parts.append(f"BC G7: {float(bullet.get('bc_g7') or 0.0):.3f}")
    elif bullet.get("bc_g1"):
        parts.append(f"BC G1: {float(bullet.get('bc_g1') or 0.0):.3f}")
    parts.append(f"Source: {source}")
    if reference_snapshots:
        parts.append(f"Reference Profiles: {len(reference_snapshots)}")
    parts.append(f"Your Lots: {len(lots)}")
    if lots:
        measured_lots = sum(
            1 for lot in lots if (lot.get("stats") or {}).get("sample_count")
        )
        parts.append(f"Measured Lots: {measured_lots}")
    return "<br>".join(parts)


def build_primer_library_rows(database) -> list[dict[str, Any]]:
    """Return primer library rows with lot and inventory rollups."""
    if database is None:
        return []
    rows = database.execute_query(
        """
        SELECT
            p.*,
            COUNT(cl.id) AS lot_count,
            COALESCE(SUM(cl.quantity_remaining), 0) AS lot_quantity_remaining
        FROM primers p
        LEFT JOIN component_lots cl
            ON cl.component_type = 'primers' AND cl.component_id = p.id
        GROUP BY p.id
        ORDER BY p.manufacturer, p.name
        """
    )
    return [dict(row) for row in rows]


def build_primer_detail_snapshot(database, primer_id: int) -> dict[str, Any]:
    """Build a primer reference + owned lots snapshot for the library UI."""
    if database is None or not primer_id:
        return {}
    primer = database.get_by_id("primers", int(primer_id))
    if not primer:
        return {}
    primer_row = dict(primer)
    lots = [
        dict(row)
        for row in database.execute_query(
            """
            SELECT *
            FROM component_lots
            WHERE component_type = 'primers' AND component_id = ?
            ORDER BY is_active DESC, created_date DESC, id DESC
            """,
            (int(primer_id),),
        )
    ]
    lot_rows: list[dict[str, Any]] = []
    for lot in lots:
        stored_learning = {}
        try:
            stored_learning = (
                database.get_component_lot_learning_profile(int(lot["id"])) or {}
            )
        except Exception:
            stored_learning = {}
        try:
            learning = (
                database.refresh_primer_lot_learning_profile(int(lot["id"])) or {}
            )
        except Exception:
            learning = dict(stored_learning)
        if stored_learning:
            merged_learning = dict(learning)
            for key, value in stored_learning.items():
                if key == "profile_data" and isinstance(value, dict):
                    profile_data = dict(merged_learning.get("profile_data") or {})
                    for p_key, p_value in value.items():
                        if profile_data.get(p_key) in (None, "", 0):
                            profile_data[p_key] = p_value
                    merged_learning["profile_data"] = profile_data
                    continue
                if merged_learning.get(key) in (None, "", 0, "insufficient_data"):
                    merged_learning[key] = value
            learning = merged_learning
        if isinstance(learning.get("profile_data"), dict):
            merged_learning = dict(learning.get("profile_data") or {})
            merged_learning.update(learning)
            learning = merged_learning
        sessions = database.get_component_measurement_sessions(int(lot["id"])) or []
        lot_rows.append(
            {
                **lot,
                "learning": dict(learning) if learning else {},
                "measurement_session_count": len(sessions),
            }
        )
    return {"primer": primer_row, "lots": lot_rows}


def format_primer_detail_summary(snapshot: dict[str, Any]) -> str:
    """Render a compact textual summary for the selected primer."""
    primer = snapshot.get("primer") or {}
    if not primer:
        return "Select a primer to view catalog data and your own lots."
    lots = snapshot.get("lots") or []
    source_kind = str(primer.get("source_kind") or "manual_entry").strip()
    parts = [
        f"<b>{primer.get('manufacturer') or '-'}</b> {primer.get('name') or '-'}",
        f"Size: {primer.get('size') or '-'}",
        f"Type: {primer.get('type') or '-'}",
    ]
    if primer.get("product_line"):
        parts.append(f"Series: {primer.get('product_line')}")
    if primer.get("part_number"):
        parts.append(f"Part Number: {primer.get('part_number')}")
    if primer.get("primer_family"):
        parts.append(f"Family: {primer.get('primer_family')}")
    if primer.get("pressure_tolerance_class"):
        parts.append(f"Pressure Class: {primer.get('pressure_tolerance_class')}")
    if primer.get("cup_thickness_in") is not None:
        parts.append(f"Cup: {float(primer.get('cup_thickness_in') or 0.0):.3f}\"")
    if primer.get("match_grade"):
        parts.append("Match-grade")
    if primer.get("magnum"):
        parts.append("Magnum")
    parts.append(f"Data Source: {source_kind}")
    parts.append(f"Your Lots: {len(lots)}")
    learned_lots = sum(
        1
        for lot in lots
        if (lot.get("learning") or {}).get("status")
        not in {None, "", "insufficient_data"}
    )
    if lots:
        parts.append(f"Learned Lots: {learned_lots}")
    return "<br>".join(parts)


def build_powder_library_rows(database) -> list[dict[str, Any]]:
    """Return powder library rows with lot and inventory rollups."""
    if database is None:
        return []
    rows = database.execute_query(
        """
        SELECT
            p.*,
            COUNT(cl.id) AS lot_count,
            COALESCE(SUM(cl.quantity_remaining), 0) AS lot_quantity_remaining
        FROM powder p
        LEFT JOIN component_lots cl
            ON cl.component_type = 'powder' AND cl.component_id = p.id
        GROUP BY p.id
        ORDER BY p.manufacturer, p.name
        """
    )
    return [dict(row) for row in rows]


def build_powder_detail_snapshot(database, powder_id: int) -> dict[str, Any]:
    """Build a powder reference + owned lots snapshot for the library UI."""
    if database is None or not powder_id:
        return {}
    powder = database.get_by_id("powder", int(powder_id))
    if not powder:
        return {}
    powder_row = dict(powder)
    reference_snapshots = [
        dict(row)
        for row in database.execute_query(
            """
            SELECT *
            FROM component_reference_snapshots
            WHERE source_system IN (?, ?)
              AND component_type = 'powder'
              AND lower(coalesce(manufacturer, '')) = lower(?)
              AND lower(coalesce(model_name, '')) = lower(?)
            ORDER BY updated_date DESC, id DESC
            """,
            (
                *REFERENCE_SNAPSHOT_SOURCE_SYSTEMS,
                powder_row.get("manufacturer") or "",
                powder_row.get("name") or "",
            ),
        )
    ]
    lots = [
        dict(row)
        for row in database.execute_query(
            """
            SELECT *
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY is_active DESC, created_date DESC, id DESC
            """,
            (int(powder_id),),
        )
    ]
    lot_rows: list[dict[str, Any]] = []
    for lot in lots:
        stored_learning = {}
        try:
            stored_learning = (
                database.get_component_lot_learning_profile(int(lot["id"])) or {}
            )
        except Exception:
            stored_learning = {}
        try:
            learning = (
                database.refresh_powder_lot_learning_profile(int(lot["id"])) or {}
            )
        except Exception:
            learning = dict(stored_learning)
        if stored_learning:
            merged_learning = dict(learning)
            for key, value in stored_learning.items():
                if key == "profile_data" and isinstance(value, dict):
                    profile_data = dict(merged_learning.get("profile_data") or {})
                    for p_key, p_value in value.items():
                        if profile_data.get(p_key) in (None, "", 0):
                            profile_data[p_key] = p_value
                    merged_learning["profile_data"] = profile_data
                    continue
                if merged_learning.get(key) in (None, "", 0, "insufficient_data"):
                    merged_learning[key] = value
            learning = merged_learning
        if isinstance(learning.get("profile_data"), dict):
            merged_learning = dict(learning.get("profile_data") or {})
            merged_learning.update(learning)
            learning = merged_learning
        lot_rows.append({**lot, "learning": dict(learning) if learning else {}})
    distinct_variant_signatures = set()
    for row in reference_snapshots:
        try:
            payload = json.loads(str(row.get("profile_json") or "{}"))
        except Exception:
            payload = {}
        distinct_variant_signatures.add(
            (
                payload.get("Ba"),
                payload.get("Qex"),
                payload.get("k"),
                payload.get("pt"),
                row.get("lot_number"),
            )
        )
    return {
        "powder": powder_row,
        "lots": lot_rows,
        "reference_snapshots": reference_snapshots,
        "reference_variant_count": len(distinct_variant_signatures),
    }


def format_powder_detail_summary(snapshot: dict[str, Any]) -> str:
    """Render a compact textual summary for the selected powder."""
    powder = snapshot.get("powder") or {}
    if not powder:
        return "Select a powder to view library data and your own lots."
    lots = snapshot.get("lots") or []
    reference_snapshots = snapshot.get("reference_snapshots") or []
    reference_variant_count = int(snapshot.get("reference_variant_count") or 0)
    parts = [
        f"<b>{powder.get('manufacturer') or '-'}</b> {powder.get('name') or '-'}",
        f"Type: {powder.get('type') or '-'}",
    ]
    if powder.get("burn_rate"):
        parts.append(f"Burn Rate: {powder.get('burn_rate')}")
    density = powder.get("density_g_cc", powder.get("density"))
    if density is not None:
        parts.append(f"Density: {float(density or 0.0):.3f} g/cc")
    if powder.get("notes"):
        parts.append(f"Notes: {powder.get('notes')}")
    if reference_snapshots:
        parts.append(f"Reference Profiles: {len(reference_snapshots)}")
        parts.append(f"Distinct Variants: {reference_variant_count}")
    parts.append(f"Your Lots: {len(lots)}")
    learned_lots = sum(
        1
        for lot in lots
        if (lot.get("learning") or {}).get("status")
        not in {None, "", "insufficient_data"}
    )
    if lots:
        parts.append(f"Learned Lots: {learned_lots}")
    return "<br>".join(parts)


class ComponentDatabaseManager(QWidget):
    """
    Main component database interface
    Browse, search, add, edit components
    """

    component_selected = pyqtSignal(dict)  # Emit when component selected

    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self._bullet_rows: list[dict[str, Any]] = []
        self._powder_rows: list[dict[str, Any]] = []
        self._primer_rows: list[dict[str, Any]] = []
        self.init_ui()
        self.load_database()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel(tr("component_db_title"))
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

        subtitle = QLabel(tr("component_db_subtitle"))
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        # Tabs for different component types
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.bullets_tab = self.create_bullets_tab()
        self.powders_tab = self.create_powders_tab()
        self.primers_tab = self.create_primers_tab()
        self.brass_tab = self.create_brass_tab()
        self.cartridge_standards_tab = self.create_cartridge_standards_tab()

        self.tabs.addTab(self.bullets_tab, tr("component_db_bullets"))
        self.tabs.addTab(self.powders_tab, tr("component_db_powders"))
        self.tabs.addTab(self.primers_tab, tr("component_db_primers"))
        self.tabs.addTab(self.brass_tab, tr("component_db_brass"))
        self.tabs.addTab(
            self.cartridge_standards_tab, tr("component_db_cartridge_standards")
        )

        # Action buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton(tr("component_db_add"))
        self.btn_add.setProperty("variant", "primary")
        self.btn_add.clicked.connect(self.add_component)
        btn_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton(tr("component_db_edit"))
        self.btn_edit.setProperty("variant", "secondary")
        self.btn_edit.clicked.connect(self.edit_component)
        btn_layout.addWidget(self.btn_edit)

        self.btn_import = QPushButton(tr("component_db_import"))
        self.btn_import.setProperty("variant", "ghost")
        self.btn_import.clicked.connect(self.import_from_file)
        btn_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton(tr("component_db_export"))
        self.btn_export.setProperty("variant", "ghost")
        self.btn_export.clicked.connect(self.export_database)
        btn_layout.addWidget(self.btn_export)

        layout.addLayout(btn_layout)

    def focus_component(self, component_type: str, component_id: int | None) -> bool:
        """Focus the UI on one component row and matching tab."""
        if not component_id:
            return False
        tab_map = {
            "bullet": (0, self.bullets_table),
            "powder": (1, self.powders_table),
            "primer": (2, self.primers_table),
            "primers": (2, self.primers_table),
        }
        tab_info = tab_map.get(component_type)
        if not tab_info:
            return False
        tab_index, table = tab_info
        self.tabs.setCurrentIndex(tab_index)
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == int(
                component_id
            ):
                table.selectRow(row)
                self.refresh_bullet_detail_panel()
                self.refresh_powder_detail_panel()
                self.refresh_primer_detail_panel()
                return True
        return False

    def create_bullets_tab(self) -> QWidget:
        """Create bullets database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Search/filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(tr("component_db_search")))
        self.bullet_search = QLineEdit()
        self.bullet_search.setPlaceholderText(tr("component_db_search_bullets"))
        self.bullet_search.textChanged.connect(self.filter_bullets)
        search_layout.addWidget(self.bullet_search)

        search_layout.addWidget(QLabel(tr("component_db_caliber")))
        self.bullet_caliber_filter = QComboBox()
        self.bullet_caliber_filter.addItems(
            [
                tr("component_db_caliber_filter_all"),
                ".224",
                "6mm",
                "6.5mm",
                ".308",
                ".338",
            ]
        )
        self.bullet_caliber_filter.currentTextChanged.connect(self.filter_bullets)
        search_layout.addWidget(self.bullet_caliber_filter)

        layout.addLayout(search_layout)

        # Table
        self.bullets_table = QTableWidget()
        self.bullets_table.setColumnCount(9)
        self.bullets_table.setHorizontalHeaderLabels(
            [
                tr("component_db_col_manufacturer"),
                tr("component_db_col_name"),
                tr("component_db_col_caliber"),
                tr("component_db_col_weight"),
                tr("component_db_col_bc_g1"),
                tr("component_db_col_bc_g7"),
                tr("component_db_col_length"),
                tr("component_db_col_diameter"),
                tr("component_db_col_type"),
            ]
        )
        header = self.bullets_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        self.bullets_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.bullets_table.doubleClicked.connect(self.on_bullet_double_click)
        self.bullets_table.itemSelectionChanged.connect(
            self.refresh_bullet_detail_panel
        )
        layout.addWidget(self.bullets_table)

        self.bullet_detail_label = QLabel(tr("component_db_select_bullet"))
        self.bullet_detail_label.setWordWrap(True)
        self.bullet_detail_label.setProperty("variant", "callout")
        layout.addWidget(self.bullet_detail_label)

        self.bullet_lots_table = QTableWidget()
        self.bullet_lots_table.setColumnCount(7)
        self.bullet_lots_table.setHorizontalHeaderLabels(
            [
                tr("component_db_col_lot"),
                tr("component_db_col_active"),
                tr("component_db_col_remaining"),
                tr("component_db_col_meas_avg_weight"),
                tr("component_db_col_meas_avg_length"),
                tr("component_db_col_measurements"),
                tr("component_db_col_storage"),
            ]
        )
        lot_header = self.bullet_lots_table.horizontalHeader()
        if lot_header is not None:
            lot_header.setStretchLastSection(True)
        layout.addWidget(self.bullet_lots_table)

        return widget

    def create_powders_tab(self) -> QWidget:
        """Create powders database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(tr("component_db_search")))
        self.powder_search = QLineEdit()
        self.powder_search.setPlaceholderText(tr("component_db_search_powders"))
        self.powder_search.textChanged.connect(self.filter_powders)
        search_layout.addWidget(self.powder_search)

        search_layout.addWidget(QLabel(tr("component_db_burn_rate")))
        self.powder_burn_filter = QComboBox()
        self.powder_burn_filter.addItems(
            [
                tr("component_db_burn_filter_all"),
                tr("component_db_burn_filter_fast"),
                tr("component_db_burn_filter_medium"),
                tr("component_db_burn_filter_slow"),
                tr("component_db_burn_filter_very_slow"),
            ]
        )
        self.powder_burn_filter.currentTextChanged.connect(self.filter_powders)
        search_layout.addWidget(self.powder_burn_filter)

        layout.addLayout(search_layout)

        # Table
        self.powders_table = QTableWidget()
        self.powders_table.setColumnCount(7)
        self.powders_table.setHorizontalHeaderLabels(
            [
                tr("component_db_col_manufacturer"),
                tr("component_db_col_name"),
                tr("component_db_col_burn_rate"),
                tr("component_db_col_density"),
                tr("component_db_col_best_for"),
                tr("component_db_col_temp_stable"),
                tr("component_db_col_notes"),
            ]
        )
        header = self.powders_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        self.powders_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.powders_table.itemSelectionChanged.connect(
            self.refresh_powder_detail_panel
        )
        layout.addWidget(self.powders_table)

        self.powder_detail_label = QLabel(tr("component_db_select_powder"))
        self.powder_detail_label.setWordWrap(True)
        self.powder_detail_label.setProperty("variant", "callout")
        layout.addWidget(self.powder_detail_label)

        powder_btn_layout = QHBoxLayout()
        self.powder_add_lot_btn = QPushButton(tr("component_db_add_lot"))
        self.powder_add_lot_btn.setProperty("variant", "secondary")
        self.powder_add_lot_btn.clicked.connect(self.add_powder_lot)
        powder_btn_layout.addWidget(self.powder_add_lot_btn)
        self.powder_edit_lot_btn = QPushButton(tr("component_db_edit_lot"))
        self.powder_edit_lot_btn.setProperty("variant", "secondary")
        self.powder_edit_lot_btn.clicked.connect(self.edit_powder_lot)
        powder_btn_layout.addWidget(self.powder_edit_lot_btn)
        powder_btn_layout.addStretch()
        layout.addLayout(powder_btn_layout)

        self.powder_lots_table = QTableWidget()
        self.powder_lots_table.setColumnCount(7)
        self.powder_lots_table.setHorizontalHeaderLabels(
            [
                tr("component_db_col_lot"),
                tr("component_db_col_active"),
                tr("component_db_col_remaining"),
                tr("component_db_col_learning_status"),
                tr("component_db_col_avg_velocity"),
                tr("component_db_col_typical_es"),
                tr("component_db_col_storage"),
            ]
        )
        lot_header = self.powder_lots_table.horizontalHeader()
        if lot_header is not None:
            lot_header.setStretchLastSection(True)
        layout.addWidget(self.powder_lots_table)

        return widget

    def create_primers_tab(self) -> QWidget:
        """Create primers database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Table
        self.primers_table = QTableWidget()
        self.primers_table.setColumnCount(7)
        self.primers_table.setHorizontalHeaderLabels(
            [
                tr("component_db_col_manufacturer"),
                tr("component_db_col_name"),
                tr("component_db_col_size"),
                tr("component_db_col_type"),
                tr("component_db_col_series"),
                tr("component_db_col_pressure_class"),
                tr("component_db_col_notes"),
            ]
        )
        header = self.primers_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        self.primers_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.primers_table.itemSelectionChanged.connect(
            self.refresh_primer_detail_panel
        )
        layout.addWidget(self.primers_table)

        self.primer_detail_label = QLabel(tr("component_db_select_primer"))
        self.primer_detail_label.setWordWrap(True)
        self.primer_detail_label.setProperty("variant", "callout")
        layout.addWidget(self.primer_detail_label)

        primer_btn_layout = QHBoxLayout()
        self.primer_add_lot_btn = QPushButton(tr("component_db_add_lot"))
        self.primer_add_lot_btn.setProperty("variant", "secondary")
        self.primer_add_lot_btn.clicked.connect(self.add_primer_lot)
        primer_btn_layout.addWidget(self.primer_add_lot_btn)
        self.primer_edit_lot_btn = QPushButton(tr("component_db_edit_lot"))
        self.primer_edit_lot_btn.setProperty("variant", "secondary")
        self.primer_edit_lot_btn.clicked.connect(self.edit_primer_lot)
        primer_btn_layout.addWidget(self.primer_edit_lot_btn)
        primer_btn_layout.addStretch()
        layout.addLayout(primer_btn_layout)

        self.primer_lots_table = QTableWidget()
        self.primer_lots_table.setColumnCount(7)
        self.primer_lots_table.setHorizontalHeaderLabels(
            [
                tr("component_db_col_lot"),
                tr("component_db_col_active"),
                tr("component_db_col_remaining"),
                tr("component_db_col_learning_status"),
                tr("component_db_col_typical_es"),
                tr("component_db_col_typical_sd"),
                tr("component_db_col_storage"),
            ]
        )
        lot_header = self.primer_lots_table.horizontalHeader()
        if lot_header is not None:
            lot_header.setStretchLastSection(True)
        layout.addWidget(self.primer_lots_table)

        return widget

    def create_brass_tab(self) -> QWidget:
        """Create brass database tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Table
        self.brass_table = QTableWidget()
        self.brass_table.setColumnCount(7)
        self.brass_table.setHorizontalHeaderLabels(
            [
                tr("component_db_col_manufacturer"),
                tr("component_db_col_caliber"),
                tr("component_db_col_case_capacity"),
                tr("component_db_col_weight"),
                tr("component_db_col_wall_thickness"),
                tr("component_db_col_quality"),
                tr("component_db_col_notes"),
            ]
        )
        header = self.brass_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(self.brass_table)

        return widget

    def create_cartridge_standards_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.cartridge_standards_table = QTableWidget()
        self.cartridge_standards_table.setColumnCount(7)
        self.cartridge_standards_table.setHorizontalHeaderLabels(
            [
                "Caliber",
                "Standard",
                "Pressure (bar)",
                "OAL (mm)",
                "Case Length (mm)",
                "Volume (ml)",
                "Source",
            ]
        )
        header = self.cartridge_standards_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        self.cartridge_standards_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.cartridge_standards_table.itemSelectionChanged.connect(
            self.refresh_cartridge_standard_detail_panel
        )
        layout.addWidget(self.cartridge_standards_table)

        self.cartridge_standard_detail_label = QLabel(
            tr("component_db_select_standard")
        )
        self.cartridge_standard_detail_label.setWordWrap(True)
        self.cartridge_standard_detail_label.setProperty("variant", "callout")
        layout.addWidget(self.cartridge_standard_detail_label)

        return widget

    def load_database(self):
        """Load component database from JSON file"""
        if self.db is not None:
            self._load_database_from_app_db()
            return
        db = load_component_database_json()

        # Load bullets
        bullets = db.get("bullets", [])
        bullet_data = [
            (
                b["manufacturer"],
                b["name"],
                b["caliber"],
                b["weight"],
                b["bc_g1"],
                b["bc_g7"],
                b["length"],
                b["diameter"],
                b["type"],
            )
            for b in bullets
        ]

        self.bullets_table.setRowCount(0)
        for bullet in bullet_data:
            row = self.bullets_table.rowCount()
            self.bullets_table.insertRow(row)
            for col, value in enumerate(bullet):
                self.bullets_table.setItem(row, col, QTableWidgetItem(str(value)))

        # Load powders from database
        powders = db.get("powders", [])
        powder_data = [
            (
                p["manufacturer"],
                p["name"],
                p["burn_rate"],
                p["density"],
                p["best_for"],
                tr("component_db_yes") if p["temp_stable"] else tr("component_db_no"),
                p["notes"],
            )
            for p in powders
        ]

        self.powders_table.setRowCount(0)
        for powder in powder_data:
            row = self.powders_table.rowCount()
            self.powders_table.insertRow(row)
            for col, value in enumerate(powder):
                self.powders_table.setItem(row, col, QTableWidgetItem(str(value)))

        # Load primers from database
        primers = db.get("primers", [])
        primer_data = [
            (
                pr["manufacturer"],
                pr["name"],
                pr["size"],
                pr["type"],
                pr["brisance"],
                pr["notes"],
            )
            for pr in primers
        ]

        self.primers_table.setRowCount(0)
        for primer in primer_data:
            row = self.primers_table.rowCount()
            self.primers_table.insertRow(row)
            for col, value in enumerate(primer):
                self.primers_table.setItem(row, col, QTableWidgetItem(str(value)))

        # Load brass from database
        brass_list = db.get("brass", [])
        brass_data = [
            (
                br["manufacturer"],
                br["caliber"],
                br["case_capacity"],
                br["weight"],
                br["wall_thickness"],
                f"{br['quality']}/5",
                br["notes"],
            )
            for br in brass_list
        ]

        self.brass_table.setRowCount(0)
        for brass in brass_data:
            row = self.brass_table.rowCount()
            self.brass_table.insertRow(row)
            for col, value in enumerate(brass):
                self.brass_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _load_database_from_app_db(self) -> None:
        """Load component catalog from the app database."""
        try:
            migrate_legacy_component_tables_into_library(self.db)
        except Exception:
            logger.exception("Legacy component library migration failed")
        self._bullet_rows = build_bullet_library_rows(self.db)
        self.bullets_table.setRowCount(0)
        for bullet in self._bullet_rows:
            row = self.bullets_table.rowCount()
            self.bullets_table.insertRow(row)
            values = [
                bullet.get("manufacturer") or "",
                bullet.get("name") or "",
                bullet.get("caliber") or "",
                f"{float(bullet.get('weight_grains') or 0.0):.1f}",
                (
                    f"{float(bullet.get('bc_g1') or 0.0):.3f}"
                    if bullet.get("bc_g1") is not None
                    else ""
                ),
                (
                    f"{float(bullet.get('bc_g7') or 0.0):.3f}"
                    if bullet.get("bc_g7") is not None
                    else ""
                ),
                (
                    f"{float(bullet.get('length_mm') or 0.0):.3f}"
                    if bullet.get("length_mm") is not None
                    else ""
                ),
                (
                    f"{float(bullet.get('diameter_mm') or 0.0):.3f}"
                    if bullet.get("diameter_mm") is not None
                    else ""
                ),
                bullet.get("bullet_type") or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, bullet.get("id"))
                self.bullets_table.setItem(row, col, item)

        try:
            self._powder_rows = build_powder_library_rows(self.db)
        except Exception:
            self._powder_rows = []
        self.powders_table.setRowCount(0)
        for powder in self._powder_rows:
            row = self.powders_table.rowCount()
            self.powders_table.insertRow(row)
            values = [
                powder.get("manufacturer") or "",
                powder.get("name") or "",
                powder.get("burn_rate") or "",
                str(powder.get("density_g_cc", powder.get("density")) or ""),
                powder.get("best_for") or "",
                (
                    tr("component_db_yes")
                    if powder.get("temp_stable")
                    else tr("component_db_no")
                ),
                powder.get("notes") or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, powder.get("id"))
                self.powders_table.setItem(row, col, item)

        try:
            self._primer_rows = build_primer_library_rows(self.db)
        except Exception:
            self._primer_rows = []
        self.primers_table.setRowCount(0)
        for primer in self._primer_rows:
            row = self.primers_table.rowCount()
            self.primers_table.insertRow(row)
            values = [
                primer.get("manufacturer") or "",
                primer.get("name") or "",
                primer.get("size") or "",
                primer.get("type") or "",
                primer.get("product_line") or "",
                primer.get("pressure_tolerance_class") or "",
                primer.get("notes") or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, primer.get("id"))
                self.primers_table.setItem(row, col, item)

        try:
            brass_rows = self.db.get_all("cases", "manufacturer, caliber")
        except Exception:
            brass_rows = []
        self.brass_table.setRowCount(0)
        for brass in brass_rows:
            row = self.brass_table.rowCount()
            self.brass_table.insertRow(row)
            values = [
                brass.get("manufacturer") or "",
                brass.get("caliber") or "",
                str(brass.get("case_capacity_grains_h2o") or ""),
                str(brass.get("weight_grains") or ""),
                str(brass.get("wall_thickness_mm") or ""),
                str(brass.get("quality_rating") or ""),
                brass.get("notes") or "",
            ]
            for col, value in enumerate(values):
                self.brass_table.setItem(row, col, QTableWidgetItem(str(value)))

        self._cartridge_standard_rows = []
        if self.db is not None:
            try:
                self._cartridge_standard_rows = self.db.list_cartridge_standards()
            except Exception:
                self._cartridge_standard_rows = []
        self.cartridge_standards_table.setRowCount(0)
        for standard in self._cartridge_standard_rows:
            row = self.cartridge_standards_table.rowCount()
            self.cartridge_standards_table.insertRow(row)
            values = [
                standard.get("caliber_name") or "",
                standard.get("standard_body") or standard.get("standard_label") or "",
                (
                    f"{float(standard.get('max_pressure_bar') or 0.0):.1f}"
                    if standard.get("max_pressure_bar") is not None
                    else ""
                ),
                (
                    f"{float(standard.get('oal_mm') or 0.0):.2f}"
                    if standard.get("oal_mm") is not None
                    else ""
                ),
                (
                    f"{float(standard.get('case_length_mm') or 0.0):.2f}"
                    if standard.get("case_length_mm") is not None
                    else ""
                ),
                (
                    f"{float(standard.get('case_capacity_ml') or 0.0):.3f}"
                    if standard.get("case_capacity_ml") is not None
                    else ""
                ),
                standard.get("source") or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, standard.get("id"))
                self.cartridge_standards_table.setItem(row, col, item)

        self.refresh_bullet_detail_panel()
        self.refresh_powder_detail_panel()
        self.refresh_primer_detail_panel()

    def refresh_bullet_detail_panel(self) -> None:
        """Refresh detail panel with owned bullet lots and measured averages."""
        if not hasattr(self, "bullet_detail_label") or self.db is None:
            return
        current_row = self.bullets_table.currentRow()
        bullet_id = None
        if current_row >= 0:
            item = self.bullets_table.item(current_row, 0)
            if item is not None:
                bullet_id = item.data(Qt.ItemDataRole.UserRole)
        if not bullet_id:
            self.bullet_detail_label.setText(tr("component_db_select_bullet"))
            self.bullet_lots_table.setRowCount(0)
            return

        snapshot = build_bullet_detail_snapshot(self.db, int(bullet_id))
        self.bullet_detail_label.setText(format_bullet_detail_summary(snapshot))
        lots = snapshot.get("lots") or []
        self.bullet_lots_table.setRowCount(0)
        for lot in lots:
            stats = lot.get("stats") or {}
            row = self.bullet_lots_table.rowCount()
            self.bullet_lots_table.insertRow(row)
            values = [
                lot.get("lot_number") or "",
                (
                    tr("component_db_yes")
                    if lot.get("is_active")
                    else tr("component_db_no")
                ),
                f"{float(lot.get('quantity_remaining') or 0.0):.0f}",
                (
                    f"{float(stats.get('weight_avg_grains') or 0.0):.2f} gr"
                    if stats.get("weight_avg_grains") is not None
                    else "-"
                ),
                (
                    f"{float(stats.get('length_avg_mm') or 0.0):.3f} mm"
                    if stats.get("length_avg_mm") is not None
                    else "-"
                ),
                str(
                    stats.get("sample_count")
                    or lot.get("measurement_session_count")
                    or 0
                ),
                lot.get("storage_location") or "",
            ]
            for col, value in enumerate(values):
                self.bullet_lots_table.setItem(row, col, QTableWidgetItem(str(value)))

    def refresh_powder_detail_panel(self) -> None:
        """Refresh detail panel with powder profile and owned lots."""
        if not hasattr(self, "powder_detail_label") or self.db is None:
            return
        current_row = self.powders_table.currentRow()
        powder_id = None
        if current_row >= 0:
            item = self.powders_table.item(current_row, 0)
            if item is not None:
                powder_id = item.data(Qt.ItemDataRole.UserRole)
        if not powder_id:
            self.powder_detail_label.setText(tr("component_db_select_powder"))
            self.powder_lots_table.setRowCount(0)
            return

        snapshot = build_powder_detail_snapshot(self.db, int(powder_id))
        self.powder_detail_label.setText(format_powder_detail_summary(snapshot))
        lots = snapshot.get("lots") or []
        self.powder_lots_table.setRowCount(0)
        for lot in lots:
            learning = lot.get("learning") or {}
            row = self.powder_lots_table.rowCount()
            self.powder_lots_table.insertRow(row)
            values = [
                lot.get("lot_number") or "",
                (
                    tr("component_db_yes")
                    if lot.get("is_active")
                    else tr("component_db_no")
                ),
                f"{float(lot.get('quantity_remaining') or 0.0):.0f}",
                learning.get("status") or "unknown",
                (
                    f"{float(learning.get('avg_velocity_fps') or 0.0):.0f}"
                    if learning.get("avg_velocity_fps") is not None
                    else ""
                ),
                (
                    f"{float(learning.get('typical_es_fps') or 0.0):.1f}"
                    if learning.get("typical_es_fps") is not None
                    else ""
                ),
                lot.get("storage_location") or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, lot.get("id"))
                self.powder_lots_table.setItem(row, col, item)

    def refresh_primer_detail_panel(self) -> None:
        """Refresh detail panel with primer profile and owned lots."""
        if not hasattr(self, "primer_detail_label") or self.db is None:
            return
        current_row = self.primers_table.currentRow()
        primer_id = None
        if current_row >= 0:
            item = self.primers_table.item(current_row, 0)
            if item is not None:
                primer_id = item.data(Qt.ItemDataRole.UserRole)
        if not primer_id:
            self.primer_detail_label.setText(tr("component_db_select_primer"))
            self.primer_lots_table.setRowCount(0)
            return

        snapshot = build_primer_detail_snapshot(self.db, int(primer_id))
        self.primer_detail_label.setText(format_primer_detail_summary(snapshot))
        lots = snapshot.get("lots") or []
        self.primer_lots_table.setRowCount(0)
        for lot in lots:
            learning = lot.get("learning") or {}
            row = self.primer_lots_table.rowCount()
            self.primer_lots_table.insertRow(row)
            values = [
                lot.get("lot_number") or "",
                (
                    tr("component_db_yes")
                    if lot.get("is_active")
                    else tr("component_db_no")
                ),
                f"{float(lot.get('quantity_remaining') or 0.0):.0f}",
                learning.get("status") or "unknown",
                (
                    f"{float(learning.get('typical_es_fps') or 0.0):.1f}"
                    if learning.get("typical_es_fps") is not None
                    else ""
                ),
                (
                    f"{float(learning.get('typical_sd_fps') or 0.0):.1f}"
                    if learning.get("typical_sd_fps") is not None
                    else ""
                ),
                lot.get("storage_location") or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, lot.get("id"))
                self.primer_lots_table.setItem(row, col, item)

    def _selected_primer_id(self) -> int | None:
        current_row = self.primers_table.currentRow()
        if current_row < 0:
            return None
        item = self.primers_table.item(current_row, 0)
        if item is None:
            return None
        primer_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            return int(primer_id) if primer_id else None
        except Exception:
            return None

    def _selected_powder_id(self) -> int | None:
        current_row = self.powders_table.currentRow()
        if current_row < 0:
            return None
        item = self.powders_table.item(current_row, 0)
        if item is None:
            return None
        powder_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            return int(powder_id) if powder_id else None
        except Exception:
            return None

    def _select_powder_row_by_id(self, powder_id: int) -> None:
        for row in range(self.powders_table.rowCount()):
            item = self.powders_table.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == powder_id:
                self.powders_table.selectRow(row)
                break

    def _selected_powder_lot_id(self) -> int | None:
        current_row = self.powder_lots_table.currentRow()
        if current_row < 0:
            return None
        item = self.powder_lots_table.item(current_row, 0)
        if item is None:
            return None
        lot_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            return int(lot_id) if lot_id else None
        except Exception:
            return None

    def _select_primer_row_by_id(self, primer_id: int) -> None:
        for row in range(self.primers_table.rowCount()):
            item = self.primers_table.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == primer_id:
                self.primers_table.selectRow(row)
                break

    def _selected_primer_lot_id(self) -> int | None:
        current_row = self.primer_lots_table.currentRow()
        if current_row < 0:
            return None
        item = self.primer_lots_table.item(current_row, 0)
        if item is None:
            return None
        lot_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            return int(lot_id) if lot_id else None
        except Exception:
            return None

    def add_primer_lot(self) -> None:
        """Create a new primer lot from the primer library tab."""
        if self.db is None:
            QMessageBox.information(
                self,
                "Primer Lot",
                "Primer lots require the app database, not JSON-only view mode.",
            )
            return
        primer_id = self._selected_primer_id()
        if not primer_id:
            QMessageBox.information(
                self,
                "Primer Lot",
                "Select a primer before adding a lot.",
            )
            return
        primer = self.db.get_by_id("primers", int(primer_id)) or {}
        dialog = AddPrimerLotDialog(self, primer)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Primer Lot", "The lot must include at least a lot number."
            )
            return

        if int(payload.get("is_active") or 0):
            self.db.update(
                "component_lots",
                {"is_active": 0},
                "component_type = ? AND component_id = ?",
                ("primers", int(primer_id)),
            )

        lot_id = self.db.create_component_lot(
            "primers",
            int(primer_id),
            str(payload.get("lot_number")),
            float(payload.get("quantity_initial") or 0),
            storage_location=payload.get("storage_location"),
            notes=payload.get("notes"),
            is_active=int(payload.get("is_active") or 0),
            source=payload.get("source"),
        )
        learning_updates = {
            "status": payload.get("learning_status"),
            "typical_es_fps": payload.get("typical_es_fps"),
            "typical_sd_fps": payload.get("typical_sd_fps"),
            "notes": payload.get("learning_notes"),
        }
        if any(value not in (None, "", 0) for value in learning_updates.values()):
            self.db.upsert_component_lot_learning_profile(int(lot_id), learning_updates)

        self.load_database()
        self._select_primer_row_by_id(int(primer_id))
        QMessageBox.information(
            self,
            "Primer Lot",
            f"Primer lot added: {payload.get('lot_number')}",
        )

    def add_powder_lot(self) -> None:
        """Create a new powder lot from the powder library tab."""
        if self.db is None:
            QMessageBox.information(
                self,
                "Powder Lot",
                "Powder lots require the app database, not JSON-only view mode.",
            )
            return
        powder_id = self._selected_powder_id()
        if not powder_id:
            QMessageBox.information(
                self,
                "Powder Lot",
                "Select a powder before adding a lot.",
            )
            return
        powder = self.db.get_by_id("powder", int(powder_id)) or {}
        dialog = AddPowderLotDialog(self, powder)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Powder Lot", "The lot must include at least a lot number."
            )
            return

        if int(payload.get("is_active") or 0):
            self.db.update(
                "component_lots",
                {"is_active": 0},
                "component_type = ? AND component_id = ?",
                ("powder", int(powder_id)),
            )

        lot_id = self.db.create_component_lot(
            "powder",
            int(powder_id),
            str(payload.get("lot_number")),
            float(payload.get("quantity_initial") or 0),
            storage_location=payload.get("storage_location"),
            notes=payload.get("notes"),
            is_active=int(payload.get("is_active") or 0),
            source=payload.get("source"),
        )
        learning_updates = {
            "status": payload.get("learning_status"),
            "avg_velocity_fps": payload.get("avg_velocity_fps"),
            "velocity_offset_fps": payload.get("velocity_offset_fps"),
            "typical_es_fps": payload.get("typical_es_fps"),
            "notes": payload.get("learning_notes"),
        }
        if any(value not in (None, "", 0) for value in learning_updates.values()):
            self.db.upsert_component_lot_learning_profile(int(lot_id), learning_updates)

        self.load_database()
        self._select_powder_row_by_id(int(powder_id))
        QMessageBox.information(
            self,
            "Powder Lot",
            f"Powder lot added: {payload.get('lot_number')}",
        )

    def edit_powder_lot(self) -> None:
        """Edit an existing powder lot from the powder library tab."""
        if self.db is None:
            QMessageBox.information(
                self,
                "Powder Lot",
                "Powder lots require the app database, not JSON-only view mode.",
            )
            return
        powder_id = self._selected_powder_id()
        lot_id = self._selected_powder_lot_id()
        if not powder_id or not lot_id:
            QMessageBox.information(
                self,
                "Powder Lot",
                "Select a powder lot to edit.",
            )
            return
        powder = self.db.get_by_id("powder", int(powder_id)) or {}
        lot = self.db.get_by_id("component_lots", int(lot_id)) or {}
        learning = self.db.get_component_lot_learning_profile(int(lot_id)) or {}
        dialog = AddPowderLotDialog(
            self,
            powder,
            existing_lot={
                **lot,
                "learning_status": learning.get("status"),
                "avg_velocity_fps": learning.get("avg_velocity_fps"),
                "velocity_offset_fps": learning.get("velocity_offset_fps"),
                "typical_es_fps": learning.get("typical_es_fps"),
                "learning_notes": learning.get("notes"),
            },
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Powder Lot", "The lot must include at least a lot number."
            )
            return

        if int(payload.get("is_active") or 0):
            self.db.update(
                "component_lots",
                {"is_active": 0},
                "component_type = ? AND component_id = ? AND id != ?",
                ("powder", int(powder_id), int(lot_id)),
            )

        self.db.update(
            "component_lots",
            {
                "lot_number": payload.get("lot_number"),
                "quantity_initial": float(payload.get("quantity_initial") or 0),
                "quantity_remaining": float(payload.get("quantity_initial") or 0),
                "storage_location": payload.get("storage_location"),
                "notes": payload.get("notes"),
                "is_active": int(payload.get("is_active") or 0),
                "source": payload.get("source"),
            },
            "id = ?",
            (int(lot_id),),
        )
        self.db.upsert_component_lot_learning_profile(
            int(lot_id),
            {
                "status": payload.get("learning_status"),
                "avg_velocity_fps": payload.get("avg_velocity_fps"),
                "velocity_offset_fps": payload.get("velocity_offset_fps"),
                "typical_es_fps": payload.get("typical_es_fps"),
                "notes": payload.get("learning_notes"),
            },
        )
        self.load_database()
        self._select_powder_row_by_id(int(powder_id))
        QMessageBox.information(
            self,
            "Powder Lot",
            f"Powder lot updated: {payload.get('lot_number')}",
        )

    def edit_primer_lot(self) -> None:
        """Edit an existing primer lot from the primer library tab."""
        if self.db is None:
            QMessageBox.information(
                self,
                "Primer Lot",
                "Primer lots require the app database, not JSON-only view mode.",
            )
            return
        primer_id = self._selected_primer_id()
        lot_id = self._selected_primer_lot_id()
        if not primer_id or not lot_id:
            QMessageBox.information(
                self,
                "Primer Lot",
                "Select a primer lot to edit.",
            )
            return

        primer = self.db.get_by_id("primers", int(primer_id)) or {}
        lot = self.db.get_by_id("component_lots", int(lot_id)) or {}
        learning = self.db.get_component_lot_learning_profile(int(lot_id)) or {}
        dialog = AddPrimerLotDialog(
            self,
            primer,
            existing_lot={
                **lot,
                "learning_status": learning.get("status"),
                "typical_es_fps": learning.get("typical_es_fps"),
                "typical_sd_fps": (learning.get("profile_data") or {}).get(
                    "typical_sd_fps"
                ),
                "learning_notes": learning.get("notes"),
            },
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_lot_data()
        if not payload.get("lot_number"):
            QMessageBox.warning(
                self, "Primer Lot", "The lot must include at least a lot number."
            )
            return

        if int(payload.get("is_active") or 0):
            self.db.update(
                "component_lots",
                {"is_active": 0},
                "component_type = ? AND component_id = ? AND id != ?",
                ("primers", int(primer_id), int(lot_id)),
            )

        self.db.update(
            "component_lots",
            {
                "lot_number": payload.get("lot_number"),
                "quantity_initial": float(payload.get("quantity_initial") or 0),
                "quantity_remaining": float(payload.get("quantity_initial") or 0),
                "storage_location": payload.get("storage_location"),
                "notes": payload.get("notes"),
                "is_active": int(payload.get("is_active") or 0),
                "source": payload.get("source"),
            },
            "id = ?",
            (int(lot_id),),
        )
        self.db.upsert_component_lot_learning_profile(
            int(lot_id),
            {
                "status": payload.get("learning_status"),
                "typical_es_fps": payload.get("typical_es_fps"),
                "typical_sd_fps": payload.get("typical_sd_fps"),
                "notes": payload.get("learning_notes"),
            },
        )

        self.load_database()
        self._select_primer_row_by_id(int(primer_id))
        QMessageBox.information(
            self,
            "Primer Lot",
            f"Primer lot updated: {payload.get('lot_number')}",
        )

    def filter_bullets(self):
        """Filter bullets based on search text and caliber"""
        search_text = self.bullet_search.text().lower()
        caliber_filter = self.bullet_caliber_filter.currentText()

        for row in range(self.bullets_table.rowCount()):
            show_row = True

            # Check search text (match any column)
            if search_text:
                row_text = ""
                for col in range(self.bullets_table.columnCount()):
                    item = self.bullets_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "

                if search_text not in row_text:
                    show_row = False

            # Check caliber filter
            if caliber_filter != "All":
                caliber_item = self.bullets_table.item(row, 2)
                if caliber_item and caliber_filter not in caliber_item.text():
                    show_row = False

            self.bullets_table.setRowHidden(row, not show_row)

    def filter_powders(self):
        """Filter powders based on search text and burn rate"""
        search_text = self.powder_search.text().lower()
        burn_filter = self.powder_burn_filter.currentText()

        for row in range(self.powders_table.rowCount()):
            show_row = True

            if search_text:
                row_text = ""
                for col in range(self.powders_table.columnCount()):
                    item = self.powders_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "

                if search_text not in row_text:
                    show_row = False

            if burn_filter != "All":
                burn_item = self.powders_table.item(row, 2)
                if burn_item and burn_filter not in burn_item.text():
                    show_row = False

            self.powders_table.setRowHidden(row, not show_row)

    def add_component(self):
        """Add new component"""
        current_tab = self.tabs.currentIndex()

        if current_tab == 0:  # Bullets
            dialog = AddBulletDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                bullet_data = dialog.get_bullet_data()
                self.add_bullet_to_table(bullet_data)
                QMessageBox.information(
                    self,
                    tr("component_db_success"),
                    tr("component_db_added_message", name=bullet_data["name"]),
                )

        elif current_tab == 1:  # Powders
            dialog = AddPowderDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                powder_data = dialog.get_powder_data()
                self.add_powder_to_table(powder_data)
                QMessageBox.information(
                    self,
                    tr("component_db_success"),
                    tr("component_db_added_message", name=powder_data["name"]),
                )

        elif current_tab == 2:  # Primers
            dialog = AddPrimerDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                primer_data = dialog.get_primer_data()
                if not primer_data.get("name"):
                    QMessageBox.warning(
                        self,
                        tr("component_db_add_primer_title"),
                        "A primer must have at least a name.",
                    )
                    return
                if self.db is not None:
                    self.db.insert("primers", primer_data)
                    self.load_database()
                else:
                    row = self.primers_table.rowCount()
                    self.primers_table.insertRow(row)
                    values = [
                        primer_data.get("manufacturer") or "",
                        primer_data.get("name") or "",
                        primer_data.get("size") or "",
                        primer_data.get("type") or "",
                        primer_data.get("product_line") or "",
                        primer_data.get("pressure_tolerance_class") or "",
                        primer_data.get("notes") or "",
                    ]
                    for col, value in enumerate(values):
                        self.primers_table.setItem(
                            row, col, QTableWidgetItem(str(value))
                        )
                QMessageBox.information(
                    self,
                    tr("component_db_success"),
                    tr("component_db_added_message", name=primer_data["name"]),
                )

        elif current_tab == 3:  # Brass
            QMessageBox.information(
                self,
                tr("component_db_add_brass_title"),
                tr("component_db_add_brass_soon"),
            )
        elif current_tab == 4:  # Cartridge standards
            dialog = AddCartridgeStandardDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                payload = dialog.get_standard_data()
                if not payload.get("caliber_name"):
                    QMessageBox.warning(
                        self,
                        "Cartridge Standard",
                        "A cartridge standard must have at least a caliber name.",
                    )
                    return
                if self.db is not None:
                    self.db.upsert_cartridge_standard(payload)
                    self.load_database()
                QMessageBox.information(
                    self,
                    tr("component_db_success"),
                    f"Cartridge standard saved: {payload.get('caliber_name') or '-'}",
                )

    def add_bullet_to_table(self, data: Dict):
        """Add bullet to table"""
        row = self.bullets_table.rowCount()
        self.bullets_table.insertRow(row)

        self.bullets_table.setItem(row, 0, QTableWidgetItem(data["manufacturer"]))
        self.bullets_table.setItem(row, 1, QTableWidgetItem(data["name"]))
        self.bullets_table.setItem(row, 2, QTableWidgetItem(data["caliber"]))
        self.bullets_table.setItem(row, 3, QTableWidgetItem(str(data["weight"])))
        self.bullets_table.setItem(row, 4, QTableWidgetItem(str(data["bc_g1"])))
        self.bullets_table.setItem(row, 5, QTableWidgetItem(str(data["bc_g7"])))
        self.bullets_table.setItem(row, 6, QTableWidgetItem(str(data["length"])))
        self.bullets_table.setItem(row, 7, QTableWidgetItem(str(data["diameter"])))
        self.bullets_table.setItem(row, 8, QTableWidgetItem(data["type"]))

    def add_powder_to_table(self, data: Dict):
        """Add powder to table"""
        row = self.powders_table.rowCount()
        self.powders_table.insertRow(row)

        self.powders_table.setItem(row, 0, QTableWidgetItem(data["manufacturer"]))
        self.powders_table.setItem(row, 1, QTableWidgetItem(data["name"]))
        self.powders_table.setItem(row, 2, QTableWidgetItem(data["burn_rate"]))
        self.powders_table.setItem(row, 3, QTableWidgetItem(str(data["density"])))
        self.powders_table.setItem(row, 4, QTableWidgetItem(data["best_for"]))
        self.powders_table.setItem(row, 5, QTableWidgetItem(data["temp_stable"]))
        self.powders_table.setItem(row, 6, QTableWidgetItem(data["notes"]))

    def edit_component(self):
        """Edit selected component"""
        current_tab = self.tabs.currentIndex()
        if current_tab == 4:
            current_row = self.cartridge_standards_table.currentRow()
            if current_row < 0:
                QMessageBox.information(
                    self,
                    tr("component_db_edit_title"),
                    "Select a cartridge standard to edit first.",
                )
                return
            item = self.cartridge_standards_table.item(current_row, 0)
            standard_id = (
                item.data(Qt.ItemDataRole.UserRole) if item is not None else None
            )
            existing = (
                self.db.get_by_id("cartridge_standards", int(standard_id))
                if self.db is not None and standard_id
                else {}
            )
            dialog = AddCartridgeStandardDialog(self, existing_standard=existing or {})
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            payload = dialog.get_standard_data()
            if standard_id:
                payload["id"] = int(standard_id)
            if self.db is not None:
                self.db.upsert_cartridge_standard(payload)
                self.load_database()
            return

        if current_tab != 2:
            QMessageBox.information(
                self, tr("component_db_edit_title"), tr("component_db_edit_soon")
            )
            return

        current_row = self.primers_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                tr("component_db_edit_title"),
                "Select a primer to edit first.",
            )
            return

        existing = None
        primer_id = None
        item = self.primers_table.item(current_row, 0)
        if item is not None:
            primer_id = item.data(Qt.ItemDataRole.UserRole)
        if self.db is not None and primer_id:
            existing = self.db.get_by_id("primers", int(primer_id))
        else:
            existing = {
                "manufacturer": (
                    self.primers_table.item(current_row, 0).text()
                    if self.primers_table.item(current_row, 0)
                    else ""
                ),
                "name": (
                    self.primers_table.item(current_row, 1).text()
                    if self.primers_table.item(current_row, 1)
                    else ""
                ),
                "size": (
                    self.primers_table.item(current_row, 2).text()
                    if self.primers_table.item(current_row, 2)
                    else ""
                ),
                "type": (
                    self.primers_table.item(current_row, 3).text()
                    if self.primers_table.item(current_row, 3)
                    else ""
                ),
                "product_line": (
                    self.primers_table.item(current_row, 4).text()
                    if self.primers_table.item(current_row, 4)
                    else ""
                ),
                "pressure_tolerance_class": (
                    self.primers_table.item(current_row, 5).text()
                    if self.primers_table.item(current_row, 5)
                    else ""
                ),
                "notes": (
                    self.primers_table.item(current_row, 6).text()
                    if self.primers_table.item(current_row, 6)
                    else ""
                ),
            }

        dialog = AddPrimerDialog(self, existing_primer=existing or {})
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.get_primer_data()
        if not payload.get("name"):
            QMessageBox.warning(
                self,
                tr("component_db_edit_title"),
                "A primer must have at least a name.",
            )
            return

        if self.db is not None and primer_id:
            self.db.update("primers", payload, "id = ?", (int(primer_id),))
            self.load_database()
            for row in range(self.primers_table.rowCount()):
                row_item = self.primers_table.item(row, 0)
                if (
                    row_item is not None
                    and row_item.data(Qt.ItemDataRole.UserRole) == primer_id
                ):
                    self.primers_table.selectRow(row)
                    break
        else:
            values = [
                payload.get("manufacturer") or "",
                payload.get("name") or "",
                payload.get("size") or "",
                payload.get("type") or "",
                payload.get("product_line") or "",
                payload.get("pressure_tolerance_class") or "",
                payload.get("notes") or "",
            ]
            for col, value in enumerate(values):
                self.primers_table.setItem(
                    current_row, col, QTableWidgetItem(str(value))
                )

        QMessageBox.information(
            self,
            tr("component_db_success"),
            f"Primer profile updated: {payload.get('name') or '-'}",
        )

    def import_from_file(self):
        """Import components from CSV/JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("component_db_import_title"),
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)",
        )

        if file_path:
            current_index = self.tabs.currentIndex()
            if current_index == 4 and self.db is not None:
                try:
                    result = import_cartridge_standards_from_knowledge_base(
                        self.db, file_path
                    )
                    self.load_database()
                    QMessageBox.information(
                        self,
                        "Cartridge Standard Import",
                        f"Import completed. {result['added_or_updated']} rows added or updated, {result['skipped']} skipped.",
                    )
                except Exception as exc:
                    logger.exception("Cartridge standard import failed: %s", exc)
                    QMessageBox.critical(self, "Cartridge Standard Import", str(exc))
                return

            component_type = (
                "bullets"
                if current_index == 0
                else "powders" if current_index == 1 else ""
            )
            if not component_type:
                QMessageBox.information(
                    self,
                    tr("component_db_import_title"),
                    tr("component_db_import_limited"),
                )
                return

            try:
                db = load_component_database_json()
                suffix = Path(file_path).suffix.lower()
                if suffix == ".json":
                    imported_db = load_component_database_json(file_path)
                    incoming = imported_db.get(component_type, [])
                    skipped = 0
                else:
                    incoming, report = import_component_csv_rows(
                        file_path, component_type
                    )
                    skipped = int(report.get("skipped", 0))

                merge_report = merge_component_records(
                    db[component_type], incoming, component_type
                )
                save_component_database_json(db)
                self.load_database()
                QMessageBox.information(
                    self,
                    tr("component_db_import_done"),
                    tr(
                        "component_db_import_report",
                        added=merge_report["added"],
                        component_type=component_type,
                        duplicates=merge_report["duplicates"],
                        skipped=skipped,
                    ),
                )
            except Exception as exc:
                logger.exception("Component import failed: %s", exc)
                QMessageBox.critical(self, tr("component_db_import_failed"), str(exc))

    def export_database(self):
        """Export database to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("component_db_export_title"),
            "component_database.json",
            "JSON Files (*.json);;CSV Files (*.csv)",
        )

        if file_path:
            try:
                db = load_component_database_json()
                suffix = Path(file_path).suffix.lower()
                if suffix == ".csv":
                    current_index = self.tabs.currentIndex()
                    component_type = (
                        "bullets"
                        if current_index == 0
                        else "powders" if current_index == 1 else ""
                    )
                    if not component_type:
                        QMessageBox.information(
                            self,
                            tr("component_db_export_title"),
                            tr("component_db_export_limited"),
                        )
                        return
                    rows = db.get(component_type, [])
                    if not rows:
                        QMessageBox.information(
                            self,
                            tr("component_db_export_title"),
                            tr(
                                "component_db_export_none",
                                component_type=component_type,
                            ),
                        )
                        return
                    export_component_database(
                        db, file_path, component_type=component_type
                    )
                else:
                    export_component_database(db, file_path)
                QMessageBox.information(
                    self,
                    tr("component_db_export_title"),
                    tr(
                        "component_db_export_report",
                        message=tr("component_db_export_done"),
                        file_path=file_path,
                    ),
                )
            except Exception as exc:
                logger.exception("Component export failed: %s", exc)
                QMessageBox.critical(self, tr("component_db_export_failed"), str(exc))

    def on_bullet_double_click(self):
        """Handle bullet double-click - select for use"""
        current_row = self.bullets_table.currentRow()
        if current_row >= 0:
            bullet_id = None
            id_item = self.bullets_table.item(current_row, 0)
            if id_item is not None and hasattr(id_item, "data"):
                bullet_id = id_item.data(Qt.ItemDataRole.UserRole)

            def _cell_text(column: int) -> str:
                item = self.bullets_table.item(current_row, column)
                return item.text() if item else ""

            def _cell_float(column: int) -> float:
                value = _cell_text(column).strip()
                if not value:
                    return 0.0
                try:
                    return float(value)
                except ValueError:
                    return 0.0

            bullet_data = {
                "manufacturer": _cell_text(0),
                "name": _cell_text(1),
                "caliber": _cell_text(2),
                "weight": _cell_float(3),
                "bc_g1": _cell_float(4),
                "bc_g7": _cell_float(5),
            }
            if bullet_id:
                bullet_data["id"] = bullet_id
            database = getattr(self, "db", None)
            if database is not None and bullet_id:
                snapshot = build_bullet_detail_snapshot(database, int(bullet_id))
                bullet_data["lot_count"] = len(snapshot.get("lots") or [])
                measured_lots = sum(
                    1
                    for lot in snapshot.get("lots") or []
                    if (lot.get("stats") or {}).get("sample_count")
                )
                bullet_data["measured_lot_count"] = measured_lots
            self.component_selected.emit(bullet_data)

    def refresh_cartridge_standard_detail_panel(self) -> None:
        if not hasattr(self, "cartridge_standard_detail_label"):
            return
        row = self.cartridge_standards_table.currentRow()
        if row < 0:
            self.cartridge_standard_detail_label.setText(
                "Select a cartridge standard to view dimensions, pressure, and drawing/PDF links."
            )
            return
        item = self.cartridge_standards_table.item(row, 0)
        standard_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        standard = (
            self.db.get_by_id("cartridge_standards", int(standard_id))
            if self.db is not None and standard_id
            else None
        )
        self.cartridge_standard_detail_label.setText(
            _format_cartridge_standard_summary(standard)
        )


class AddBulletDialog(QDialog):
    """
    Dialog for adding custom bullet
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("component_db_add_bullet"))
        self.resize(500, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Info box
        info = QLabel(tr("component_db_add_bullet_info"))
        info.setProperty("variant", "callout")
        layout.addWidget(info)

        form = QFormLayout()

        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText(
            tr("component_db_manufacturer_placeholder")
        )
        form.addRow(tr("component_db_manufacturer"), self.manufacturer)

        # Name
        self.name = QLineEdit()
        self.name.setPlaceholderText(tr("component_db_bullet_name_placeholder"))
        form.addRow(tr("component_db_bullet_name"), self.name)

        # Caliber
        self.caliber = QComboBox()
        self.caliber.setEditable(True)
        self.caliber.addItems([".224", "6mm", "6.5mm", ".308", ".338", "Custom"])
        form.addRow(tr("component_db_caliber_label"), self.caliber)

        # Weight
        self.weight = QDoubleSpinBox()
        self.weight.setRange(10, 500)
        self.weight.setValue(140)
        self.weight.setSuffix(" gr")
        form.addRow(tr("component_db_weight"), self.weight)

        # BC G1
        self.bc_g1 = QDoubleSpinBox()
        self.bc_g1.setRange(0.100, 1.000)
        self.bc_g1.setValue(0.610)
        self.bc_g1.setDecimals(3)
        form.addRow(tr("component_db_bc_g1"), self.bc_g1)

        # BC G7
        self.bc_g7 = QDoubleSpinBox()
        self.bc_g7.setRange(0.100, 1.000)
        self.bc_g7.setValue(0.305)
        self.bc_g7.setDecimals(3)
        form.addRow(tr("component_db_bc_g7"), self.bc_g7)

        self.bc_segments = QTextEdit()
        self.bc_segments.setMaximumHeight(80)
        self.bc_segments.setPlaceholderText(tr("component_db_bc_segments_placeholder"))
        form.addRow(tr("component_db_bc_segments"), self.bc_segments)

        self.bc_segments_summary = QLabel(tr("component_db_bc_segments_missing"))
        self.bc_segments_summary.setWordWrap(True)
        form.addRow(
            tr("component_db_bc_segments_summary_label"), self.bc_segments_summary
        )

        # Length
        self.length = QDoubleSpinBox()
        self.length.setRange(0.500, 3.000)
        self.length.setValue(1.430)
        self.length.setDecimals(3)
        self.length.setSuffix(" in")
        form.addRow(tr("component_db_length"), self.length)

        # Diameter
        self.diameter = QDoubleSpinBox()
        self.diameter.setRange(0.200, 0.500)
        self.diameter.setValue(0.264)
        self.diameter.setDecimals(3)
        self.diameter.setSuffix(" in")
        form.addRow(tr("component_db_diameter"), self.diameter)

        # Type
        self.bullet_type = QComboBox()
        self.bullet_type.addItems(
            [
                "BTHP",
                "VLD",
                "Hybrid",
                "ELD",
                "A-Tip",
                "RDF",
                "FMJ",
                "Soft Point",
                "Ballistic Tip",
                "Other",
            ]
        )
        form.addRow(tr("component_db_bullet_type"), self.bullet_type)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText(tr("component_db_bullet_notes_hint"))
        form.addRow(tr("component_db_notes"), self.notes)

        layout.addLayout(form)

        # Helper info
        helper = QLabel(tr("component_db_bc_help"))
        helper.setProperty("variant", "callout")
        layout.addWidget(helper)
        self.bc_segments.textChanged.connect(self._update_bc_segments_summary)
        self._update_bc_segments_summary()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_bullet_data(self) -> Dict:
        """Get entered bullet data"""
        return {
            "manufacturer": self.manufacturer.text(),
            "name": self.name.text(),
            "caliber": self.caliber.currentText(),
            "weight": self.weight.value(),
            "bc_g1": self.bc_g1.value(),
            "bc_g7": self.bc_g7.value(),
            "bc_segments_json": _normalize_bc_segments_json(
                self.bc_segments.toPlainText()
            ),
            "length": self.length.value(),
            "diameter": self.diameter.value(),
            "type": self.bullet_type.currentText(),
            "notes": self.notes.toPlainText(),
        }

    def _update_bc_segments_summary(self) -> None:
        self.bc_segments_summary.setText(
            _format_bc_segments_summary(self.bc_segments.toPlainText())
        )


class AddPowderDialog(QDialog):
    """Dialog for adding custom powder"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("component_db_add_powder"))
        self.resize(500, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(tr("component_db_add_powder_info"))
        info.setProperty("variant", "callout")
        layout.addWidget(info)

        form = QFormLayout()

        # Manufacturer
        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText(
            tr("component_db_powder_manufacturer_placeholder")
        )
        form.addRow(tr("component_db_manufacturer"), self.manufacturer)

        # Name
        self.name = QLineEdit()
        self.name.setPlaceholderText(tr("component_db_powder_name_placeholder"))
        form.addRow(tr("component_db_powder_name"), self.name)

        # Burn rate
        self.burn_rate = QComboBox()
        self.burn_rate.addItems(
            [
                "Very Fast",
                "Fast",
                "Medium-Fast",
                "Medium",
                "Medium-Slow",
                "Slow",
                "Very Slow",
            ]
        )
        form.addRow(tr("component_db_burn_rate"), self.burn_rate)

        # Density
        self.density = QDoubleSpinBox()
        self.density.setRange(0.70, 1.10)
        self.density.setValue(0.93)
        self.density.setDecimals(2)
        self.density.setSuffix(" g/cc")
        form.addRow(tr("component_db_density"), self.density)

        # Best for
        self.best_for = QLineEdit()
        self.best_for.setPlaceholderText(tr("component_db_best_for_placeholder"))
        form.addRow(tr("component_db_best_for"), self.best_for)

        # Temp stable
        self.temp_stable = QComboBox()
        self.temp_stable.addItems(["Yes", "No", "Unknown"])
        form.addRow(tr("component_db_temp_stable"), self.temp_stable)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText(tr("component_db_powder_notes_hint"))
        form.addRow(tr("component_db_notes"), self.notes)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_powder_data(self) -> Dict:
        """Get entered powder data"""
        return {
            "manufacturer": self.manufacturer.text(),
            "name": self.name.text(),
            "burn_rate": self.burn_rate.currentText(),
            "density": self.density.value(),
            "best_for": self.best_for.text(),
            "temp_stable": self.temp_stable.currentText(),
            "notes": self.notes.toPlainText(),
        }


class AddPrimerDialog(QDialog):
    """Dialog for adding or editing primer profiles."""

    def __init__(self, parent=None, existing_primer: dict[str, Any] | None = None):
        super().__init__(parent)
        self.existing_primer = existing_primer or {}
        self.setWindowTitle("Primer Profile")
        self.resize(520, 620)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(
            "Enter manufacturer data when available, and use the technical fields as "
            "reference values when you know how the primer behaves."
        )
        info.setWordWrap(True)
        info.setProperty("variant", "callout")
        layout.addWidget(info)

        form = QFormLayout()

        self.manufacturer = QLineEdit(
            str(self.existing_primer.get("manufacturer") or "")
        )
        form.addRow("Manufacturer", self.manufacturer)

        self.name = QLineEdit(str(self.existing_primer.get("name") or ""))
        form.addRow("Name", self.name)

        self.product_line = QLineEdit(
            str(self.existing_primer.get("product_line") or "")
        )
        form.addRow("Series", self.product_line)

        self.part_number = QLineEdit(str(self.existing_primer.get("part_number") or ""))
        form.addRow("Part Number", self.part_number)

        self.primer_type = QLineEdit(str(self.existing_primer.get("type") or ""))
        form.addRow("Type", self.primer_type)

        self.size = QLineEdit(str(self.existing_primer.get("size") or ""))
        form.addRow("Size", self.size)

        self.primer_family = QLineEdit(
            str(self.existing_primer.get("primer_family") or "")
        )
        form.addRow("Primer Family", self.primer_family)

        self.pressure_class = QLineEdit(
            str(self.existing_primer.get("pressure_tolerance_class") or "")
        )
        form.addRow("Pressure Class", self.pressure_class)

        self.cup_thickness = QDoubleSpinBox()
        self.cup_thickness.setRange(0.0, 0.050)
        self.cup_thickness.setDecimals(3)
        self.cup_thickness.setSingleStep(0.001)
        cup_value = self.existing_primer.get("cup_thickness_in")
        try:
            if cup_value is not None:
                self.cup_thickness.setValue(float(cup_value))
        except Exception:
            pass
        self.cup_thickness.setSuffix(" in")
        form.addRow("Cup Thickness", self.cup_thickness)

        self.source_kind = QLineEdit(str(self.existing_primer.get("source_kind") or ""))
        form.addRow("Data Source", self.source_kind)

        self.reference_source = QLineEdit(
            str(
                self.existing_primer.get("manufacturer_source")
                or self.existing_primer.get("reference_source")
                or ""
            )
        )
        form.addRow("Source", self.reference_source)

        self.match_grade = QComboBox()
        self.match_grade.addItems(["No", "Yes"])
        self.match_grade.setCurrentIndex(
            1 if int(self.existing_primer.get("match_grade") or 0) else 0
        )
        form.addRow("Match-grade", self.match_grade)

        self.magnum = QComboBox()
        self.magnum.addItems(["No", "Yes"])
        self.magnum.setCurrentIndex(
            1 if int(self.existing_primer.get("magnum") or 0) else 0
        )
        form.addRow("Magnum", self.magnum)

        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setDecimals(0)
        try:
            self.quantity.setValue(float(self.existing_primer.get("quantity") or 0))
        except Exception:
            self.quantity.setValue(0)
        self.quantity.setSuffix(" pcs")
        form.addRow("Quantity", self.quantity)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlainText(str(self.existing_primer.get("notes") or ""))
        form.addRow("Notes", self.notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_primer_data(self) -> Dict[str, Any]:
        """Get entered primer data."""
        return {
            "manufacturer": self.manufacturer.text().strip() or None,
            "name": self.name.text().strip(),
            "product_line": self.product_line.text().strip() or None,
            "part_number": self.part_number.text().strip() or None,
            "type": self.primer_type.text().strip() or None,
            "size": self.size.text().strip() or None,
            "primer_family": self.primer_family.text().strip() or None,
            "pressure_tolerance_class": self.pressure_class.text().strip() or None,
            "cup_thickness_in": (
                float(self.cup_thickness.value())
                if self.cup_thickness.value() > 0
                else None
            ),
            "source_kind": self.source_kind.text().strip() or None,
            "manufacturer_source": self.reference_source.text().strip() or None,
            "reference_source": self.reference_source.text().strip() or None,
            "match_grade": 1 if self.match_grade.currentText() == "Yes" else 0,
            "magnum": 1 if self.magnum.currentText() == "Yes" else 0,
            "quantity": int(self.quantity.value()),
            "notes": self.notes.toPlainText().strip() or None,
        }


class AddCartridgeStandardDialog(QDialog):
    """Dialog for adding or editing cartridge standard reference data."""

    def __init__(self, parent=None, existing_standard: dict[str, Any] | None = None):
        super().__init__(parent)
        self.existing_standard = existing_standard or {}
        self.setWindowTitle("Cartridge Standard")
        self.resize(560, 680)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(
            "Enter CIP, SAAMI, or your own cartridge dimensions here. This becomes the "
            "reference baseline for later chamber and case comparisons."
        )
        info.setWordWrap(True)
        info.setProperty("variant", "callout")
        layout.addWidget(info)

        form = QFormLayout()
        self.caliber_name = QLineEdit(
            str(self.existing_standard.get("caliber_name") or "")
        )
        form.addRow("Caliber Name", self.caliber_name)
        self.alt_name = QLineEdit(str(self.existing_standard.get("alt_name") or ""))
        form.addRow("Alternate Name", self.alt_name)
        self.standard_body = QComboBox()
        self.standard_body.setEditable(True)
        self.standard_body.addItems(["CIP", "SAAMI", "NATO", "USER", "REFERENCE"])
        self.standard_body.setCurrentText(
            str(self.existing_standard.get("standard_body") or "CIP")
        )
        form.addRow("Standard", self.standard_body)
        self.standard_label = QLineEdit(
            str(self.existing_standard.get("standard_label") or "")
        )
        form.addRow("Standard Label", self.standard_label)

        self.max_pressure_bar = QDoubleSpinBox()
        self.max_pressure_bar.setRange(0, 10000)
        self.max_pressure_bar.setDecimals(1)
        self.max_pressure_bar.setValue(
            float(self.existing_standard.get("max_pressure_bar") or 0.0)
        )
        self.max_pressure_bar.setSuffix(" bar")
        form.addRow("Max Pressure", self.max_pressure_bar)

        self.oal_mm = QDoubleSpinBox()
        self.oal_mm.setRange(0, 200)
        self.oal_mm.setDecimals(3)
        self.oal_mm.setValue(float(self.existing_standard.get("oal_mm") or 0.0))
        self.oal_mm.setSuffix(" mm")
        form.addRow("OAL", self.oal_mm)

        self.case_length_mm = QDoubleSpinBox()
        self.case_length_mm.setRange(0, 150)
        self.case_length_mm.setDecimals(3)
        self.case_length_mm.setValue(
            float(self.existing_standard.get("case_length_mm") or 0.0)
        )
        self.case_length_mm.setSuffix(" mm")
        form.addRow("Case Length", self.case_length_mm)

        self.case_capacity_ml = QDoubleSpinBox()
        self.case_capacity_ml.setRange(0, 10)
        self.case_capacity_ml.setDecimals(4)
        self.case_capacity_ml.setValue(
            float(self.existing_standard.get("case_capacity_ml") or 0.0)
        )
        self.case_capacity_ml.setSuffix(" ml")
        form.addRow("Case Capacity", self.case_capacity_ml)

        self.bullet_diameter_mm = QDoubleSpinBox()
        self.bullet_diameter_mm.setRange(0, 20)
        self.bullet_diameter_mm.setDecimals(4)
        self.bullet_diameter_mm.setValue(
            float(self.existing_standard.get("bullet_diameter_mm") or 0.0)
        )
        self.bullet_diameter_mm.setSuffix(" mm")
        form.addRow("Bullet Diameter", self.bullet_diameter_mm)

        self.neck_diameter_mm = QDoubleSpinBox()
        self.neck_diameter_mm.setRange(0, 30)
        self.neck_diameter_mm.setDecimals(4)
        self.neck_diameter_mm.setValue(
            float(self.existing_standard.get("neck_diameter_mm") or 0.0)
        )
        self.neck_diameter_mm.setSuffix(" mm")
        form.addRow("Neck Diameter", self.neck_diameter_mm)

        self.base_diameter_mm = QDoubleSpinBox()
        self.base_diameter_mm.setRange(0, 30)
        self.base_diameter_mm.setDecimals(4)
        self.base_diameter_mm.setValue(
            float(self.existing_standard.get("base_diameter_mm") or 0.0)
        )
        self.base_diameter_mm.setSuffix(" mm")
        form.addRow("Base Diameter", self.base_diameter_mm)

        self.rim_diameter_mm = QDoubleSpinBox()
        self.rim_diameter_mm.setRange(0, 30)
        self.rim_diameter_mm.setDecimals(4)
        self.rim_diameter_mm.setValue(
            float(self.existing_standard.get("rim_diameter_mm") or 0.0)
        )
        self.rim_diameter_mm.setSuffix(" mm")
        form.addRow("Rim Diameter", self.rim_diameter_mm)

        self.drawing_pdf_url = QLineEdit(
            str(self.existing_standard.get("drawing_pdf_url") or "")
        )
        form.addRow("Drawing / PDF", self.drawing_pdf_url)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlainText(str(self.existing_standard.get("notes") or ""))
        form.addRow("Notes", self.notes)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_standard_data(self) -> Dict[str, Any]:
        pressure_bar = self.max_pressure_bar.value() or None
        pressure_psi = pressure_bar * 14.5037738 if pressure_bar else None
        return {
            "caliber_name": self.caliber_name.text().strip(),
            "alt_name": self.alt_name.text().strip() or None,
            "standard_body": self.standard_body.currentText().strip(),
            "standard_label": self.standard_label.text().strip() or None,
            "pressure_method": None,
            "max_pressure_bar": pressure_bar,
            "max_pressure_psi": pressure_psi,
            "oal_mm": self.oal_mm.value() or None,
            "case_length_mm": self.case_length_mm.value() or None,
            "case_capacity_ml": self.case_capacity_ml.value() or None,
            "bullet_diameter_mm": self.bullet_diameter_mm.value() or None,
            "neck_diameter_mm": self.neck_diameter_mm.value() or None,
            "base_diameter_mm": self.base_diameter_mm.value() or None,
            "rim_diameter_mm": self.rim_diameter_mm.value() or None,
            "drawing_pdf_url": self.drawing_pdf_url.text().strip() or None,
            "source": "manual_entry",
            "source_kind": "manual_entry",
            "evidence_level": (
                "user_defined"
                if self.standard_body.currentText().strip().upper() == "USER"
                else "manual_reference"
            ),
            "user_defined": 1,
            "notes": self.notes.toPlainText().strip(),
        }


class AddPrimerLotDialog(QDialog):
    """Dialog for creating a primer lot with optional learning seed data."""

    def __init__(
        self,
        parent=None,
        primer: dict[str, Any] | None = None,
        existing_lot: dict[str, Any] | None = None,
    ):
        super().__init__(parent)
        self.primer = primer or {}
        self.existing_lot = existing_lot or {}
        self.setWindowTitle("New Primer Lot")
        self.resize(480, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        primer_name = (
            f"{self.primer.get('manufacturer') or '-'} {self.primer.get('name') or '-'}"
        ).strip()
        info = QLabel(
            f"Register a specific primer lot for {primer_name}. You can also add "
            "early learning data if you have already tested the lot."
        )
        info.setWordWrap(True)
        info.setProperty("variant", "callout")
        layout.addWidget(info)

        form = QFormLayout()

        self.lot_number = QLineEdit()
        self.lot_number.setText(str(self.existing_lot.get("lot_number") or ""))
        form.addRow("Lot Number", self.lot_number)

        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setDecimals(0)
        self.quantity.setSuffix(" pcs")
        try:
            self.quantity.setValue(
                float(
                    self.existing_lot.get("quantity_remaining")
                    or self.existing_lot.get("quantity_initial")
                    or 1000
                )
            )
        except Exception:
            self.quantity.setValue(1000)
        form.addRow("Quantity", self.quantity)

        self.storage_location = QLineEdit()
        self.storage_location.setText(
            str(self.existing_lot.get("storage_location") or "")
        )
        form.addRow("Storage Location", self.storage_location)

        self.is_active = QComboBox()
        self.is_active.addItems(["No", "Yes"])
        self.is_active.setCurrentIndex(
            1 if int(self.existing_lot.get("is_active") or 0) else 0
        )
        form.addRow("Set as Active Lot", self.is_active)

        self.learning_status = QComboBox()
        self.learning_status.addItems(
            ["", "insufficient_data", "calibrating", "learning", "watch"]
        )
        if self.existing_lot.get("learning_status"):
            idx = self.learning_status.findText(
                str(self.existing_lot.get("learning_status"))
            )
            if idx >= 0:
                self.learning_status.setCurrentIndex(idx)
        form.addRow("Learning Status", self.learning_status)

        self.typical_es = QDoubleSpinBox()
        self.typical_es.setRange(0, 100)
        self.typical_es.setDecimals(1)
        self.typical_es.setSuffix(" fps")
        try:
            if self.existing_lot.get("typical_es_fps") is not None:
                self.typical_es.setValue(float(self.existing_lot.get("typical_es_fps")))
        except Exception:
            pass
        form.addRow("Typical ES", self.typical_es)

        self.typical_sd = QDoubleSpinBox()
        self.typical_sd.setRange(0, 50)
        self.typical_sd.setDecimals(1)
        self.typical_sd.setSuffix(" fps")
        try:
            if self.existing_lot.get("typical_sd_fps") is not None:
                self.typical_sd.setValue(float(self.existing_lot.get("typical_sd_fps")))
        except Exception:
            pass
        form.addRow("Typical SD", self.typical_sd)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(70)
        self.notes.setPlainText(str(self.existing_lot.get("notes") or ""))
        form.addRow("Lot Notes", self.notes)

        self.learning_notes = QTextEdit()
        self.learning_notes.setMaximumHeight(90)
        self.learning_notes.setPlainText(
            str(self.existing_lot.get("learning_notes") or "")
        )
        form.addRow("Learning Notes", self.learning_notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_lot_data(self) -> Dict[str, Any]:
        return {
            "lot_number": self.lot_number.text().strip(),
            "quantity_initial": float(self.quantity.value()),
            "storage_location": self.storage_location.text().strip() or None,
            "is_active": 1 if self.is_active.currentText() == "Yes" else 0,
            "learning_status": self.learning_status.currentText().strip() or None,
            "typical_es_fps": (
                float(self.typical_es.value()) if self.typical_es.value() > 0 else None
            ),
            "typical_sd_fps": (
                float(self.typical_sd.value()) if self.typical_sd.value() > 0 else None
            ),
            "notes": self.notes.toPlainText().strip() or None,
            "learning_notes": self.learning_notes.toPlainText().strip() or None,
            "source": "manual_primer_lot",
        }


class AddPowderLotDialog(QDialog):
    """Dialog for creating or editing a powder lot with learning seed data."""

    def __init__(
        self,
        parent=None,
        powder: dict[str, Any] | None = None,
        existing_lot: dict[str, Any] | None = None,
    ):
        super().__init__(parent)
        self.powder = powder or {}
        self.existing_lot = existing_lot or {}
        self.setWindowTitle("New Powder Lot")
        self.resize(500, 540)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        powder_name = (
            f"{self.powder.get('manufacturer') or '-'} {self.powder.get('name') or '-'}"
        ).strip()
        info = QLabel(
            f"Register a specific powder lot for {powder_name}. You can also add "
            "early learning data from chrono work or previous batches."
        )
        info.setWordWrap(True)
        info.setProperty("variant", "callout")
        layout.addWidget(info)

        form = QFormLayout()

        self.lot_number = QLineEdit(str(self.existing_lot.get("lot_number") or ""))
        form.addRow("Lot Number", self.lot_number)

        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setDecimals(0)
        self.quantity.setSuffix(" g")
        try:
            self.quantity.setValue(
                float(
                    self.existing_lot.get("quantity_remaining")
                    or self.existing_lot.get("quantity_initial")
                    or 1000
                )
            )
        except Exception:
            self.quantity.setValue(1000)
        form.addRow("Quantity", self.quantity)

        self.storage_location = QLineEdit(
            str(self.existing_lot.get("storage_location") or "")
        )
        form.addRow("Storage Location", self.storage_location)

        self.is_active = QComboBox()
        self.is_active.addItems(["No", "Yes"])
        self.is_active.setCurrentIndex(
            1 if int(self.existing_lot.get("is_active") or 0) else 0
        )
        form.addRow("Set as Active Lot", self.is_active)

        self.learning_status = QComboBox()
        self.learning_status.addItems(
            ["", "insufficient_data", "calibrating", "learning", "watch"]
        )
        if self.existing_lot.get("learning_status"):
            idx = self.learning_status.findText(
                str(self.existing_lot.get("learning_status"))
            )
            if idx >= 0:
                self.learning_status.setCurrentIndex(idx)
        form.addRow("Learning Status", self.learning_status)

        self.avg_velocity = QDoubleSpinBox()
        self.avg_velocity.setRange(0, 5000)
        self.avg_velocity.setDecimals(0)
        self.avg_velocity.setSuffix(" fps")
        try:
            if self.existing_lot.get("avg_velocity_fps") is not None:
                self.avg_velocity.setValue(
                    float(self.existing_lot.get("avg_velocity_fps"))
                )
        except Exception:
            pass
        form.addRow("Average Velocity", self.avg_velocity)

        self.velocity_offset = QDoubleSpinBox()
        self.velocity_offset.setRange(-500, 500)
        self.velocity_offset.setDecimals(1)
        self.velocity_offset.setSuffix(" fps")
        try:
            if self.existing_lot.get("velocity_offset_fps") is not None:
                self.velocity_offset.setValue(
                    float(self.existing_lot.get("velocity_offset_fps"))
                )
        except Exception:
            pass
        form.addRow("Lot Offset", self.velocity_offset)

        self.typical_es = QDoubleSpinBox()
        self.typical_es.setRange(0, 100)
        self.typical_es.setDecimals(1)
        self.typical_es.setSuffix(" fps")
        try:
            if self.existing_lot.get("typical_es_fps") is not None:
                self.typical_es.setValue(float(self.existing_lot.get("typical_es_fps")))
        except Exception:
            pass
        form.addRow("Typical ES", self.typical_es)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(70)
        self.notes.setPlainText(str(self.existing_lot.get("notes") or ""))
        form.addRow("Lot Notes", self.notes)

        self.learning_notes = QTextEdit()
        self.learning_notes.setMaximumHeight(90)
        self.learning_notes.setPlainText(
            str(self.existing_lot.get("learning_notes") or "")
        )
        form.addRow("Learning Notes", self.learning_notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_lot_data(self) -> Dict[str, Any]:
        return {
            "lot_number": self.lot_number.text().strip(),
            "quantity_initial": float(self.quantity.value()),
            "storage_location": self.storage_location.text().strip() or None,
            "is_active": 1 if self.is_active.currentText() == "Yes" else 0,
            "learning_status": self.learning_status.currentText().strip() or None,
            "avg_velocity_fps": (
                float(self.avg_velocity.value())
                if self.avg_velocity.value() > 0
                else None
            ),
            "velocity_offset_fps": float(self.velocity_offset.value()),
            "typical_es_fps": (
                float(self.typical_es.value()) if self.typical_es.value() > 0 else None
            ),
            "notes": self.notes.toPlainText().strip() or None,
            "learning_notes": self.learning_notes.toPlainText().strip() or None,
            "source": "manual_powder_lot",
        }


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    manager = ComponentDatabaseManager()
    manager.show()
    manager.resize(1200, 800)

    sys.exit(app.exec())
