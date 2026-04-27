"""Simple label/sheet export helpers.

Creates a human-readable label text for an `ammo_profile` or `qc_batch` including
component names and any available lot/patch information. Keeps implementation
dependency-free (plain text or CSV output) so the host can print or generate
PDFs externally.
"""

import json
from typing import Any, Optional

from .internal_ballistics import (
    build_internal_ballistics_summary,
    format_internal_ballistics_text,
)


def _safe_row(row, key, default=""):
    try:
        return row[key] if row and key in row.keys() else default
    except Exception:
        return default


def _fetch_name(cur: Any, table_names: list[str], row_id: Any) -> str:
    for table_name in table_names:
        try:
            cur.execute(f"SELECT name FROM {table_name} WHERE id = ?", (row_id,))
            row = cur.fetchone()
        except Exception:
            row = None
        if row:
            try:
                return str(row["name"])
            except Exception:
                try:
                    return str(row[0])
                except Exception:
                    continue
    return str(row_id)


def _fetch_case_capacity_gr_h2o(cur: Any, case_id: Any) -> float | None:
    try:
        cur.execute(
            "SELECT case_capacity_gr_h2o FROM cases WHERE id = ?",
            (case_id,),
        )
        row = cur.fetchone()
    except Exception:
        row = None
    value = _safe_row(row, "case_capacity_gr_h2o", None)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _fetch_powder_density(cur: Any, powder_id: Any) -> float | None:
    for query in (
        "SELECT density FROM powder WHERE id = ?",
        "SELECT density FROM powder_data WHERE id = ?",
    ):
        try:
            cur.execute(query, (powder_id,))
            row = cur.fetchone()
        except Exception:
            row = None
        value = _safe_row(row, "density", None)
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _format_component_context_lines(raw_value: Any) -> list[str]:
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        try:
            payload = json.loads(raw_value)
        except Exception:
            return []
    elif isinstance(raw_value, dict):
        payload = dict(raw_value)
    else:
        return []

    if not isinstance(payload, dict):
        return []

    lines: list[str] = []
    bullet = payload.get("bullet") or {}
    if isinstance(bullet, dict) and bullet:
        name = str(bullet.get("name") or "Bullet").strip()
        lot = str(bullet.get("lot_number") or "").strip()
        if bullet.get("uses_measured_lot_stats"):
            detail = f"Bullet context: {name}"
            if lot:
                detail += f" | Lot {lot}"
            detail += " | measured lot averages active"
            lines.append(detail)

    powder = payload.get("powder") or {}
    if isinstance(powder, dict) and powder:
        name = str(powder.get("name") or "Powder").strip()
        lot = str(powder.get("lot_number") or "").strip()
        title = str(powder.get("lot_learning_title") or "").strip()
        if lot or title:
            detail = f"Powder context: {name}"
            if lot:
                detail += f" | Lot {lot}"
            if title:
                detail += f" | {title}"
            lines.append(detail)

    primer = payload.get("primer") or {}
    if isinstance(primer, dict) and primer:
        name = str(primer.get("name") or "Primer").strip()
        lot = str(primer.get("lot_number") or "").strip()
        title = str(primer.get("lot_learning_title") or "").strip()
        if lot or title:
            detail = f"Primer context: {name}"
            if lot:
                detail += f" | Lot {lot}"
            if title:
                detail += f" | {title}"
            lines.append(detail)

    return lines


def generate_label_text(
    db: Any,
    ammo_profile_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    internal_ballistics_summary: Optional[dict[str, object]] = None,
) -> str:
    """Return a text label for the given ammo_profile_id or qc batch id.

    Preference: if ammo_profile_id provided, use that. Otherwise use batch_id
    to look up associated ammo_profile or compose a generic batch label.
    """
    cur = db.cursor
    lines = []
    lines.append("Reloading Workshop - Load Label")
    lines.append("---------------------------------")

    if ammo_profile_id:
        cur.execute("SELECT * FROM ammo_profiles WHERE id = ?", (ammo_profile_id,))
        ap = cur.fetchone()
        if ap:
            lines.append(f"Profile ID: {ap['id']}")
            lines.append(f"Name: {_safe_row(ap, 'name', '')}")
            lines.append(f"Rifle ID: {_safe_row(ap, 'rifle_id', '')}")
            lines.append(f"Caliber: {_safe_row(ap, 'caliber', '')}")
            lines.append(f"Charge (gr): {_safe_row(ap, 'powder_charge', '')}")
            lines.append(f"COAL (mm): {_safe_row(ap, 'coal', '')}")
            lines.append(f"CBTO (mm): {_safe_row(ap, 'cbto', '')}")

            # Components: try to list names and any lot fields if present
            try:
                if _safe_row(ap, "bullet_id", None):
                    lines.append(
                        f"Bullet: {_fetch_name(cur, ['bullets', 'bullet_data'], ap['bullet_id'])}"
                    )
                if _safe_row(ap, "powder_id", None):
                    lines.append(
                        f"Powder: {_fetch_name(cur, ['powder', 'powder_data'], ap['powder_id'])}"
                    )
                if _safe_row(ap, "case_id", None):
                    lines.append(f"Case: {_fetch_name(cur, ['cases'], ap['case_id'])}")
                if _safe_row(ap, "primer_id", None):
                    lines.append(
                        f"Primer: {_fetch_name(cur, ['primers'], ap['primer_id'])}"
                    )
            except Exception:
                pass

            # Lot/patch information: best-effort lookup in ammo_profile fields
            lot = _safe_row(ap, "component_lot", None)
            patch = _safe_row(ap, "patch", None)
            if lot:
                lines.append(f"Lot: {lot}")
            if patch:
                lines.append(f"Patch: {patch}")

            summary = internal_ballistics_summary
            if not summary:
                summary = build_internal_ballistics_summary(
                    charge_weight_gr=_safe_row(ap, "powder_charge", None),
                    powder_name=_fetch_name(
                        cur, ["powder", "powder_data"], _safe_row(ap, "powder_id", None)
                    ),
                    case_capacity_gr_h2o=_fetch_case_capacity_gr_h2o(
                        cur, _safe_row(ap, "case_id", None)
                    ),
                    powder_density_g_ml=_fetch_powder_density(
                        cur, _safe_row(ap, "powder_id", None)
                    ),
                )
            internal_lines = format_internal_ballistics_text(summary or {})
            if internal_lines:
                lines.append("")
                lines.extend(internal_lines)

            context_lines = _format_component_context_lines(
                _safe_row(ap, "component_context_json", None)
            )
            if context_lines:
                lines.append("")
                lines.append("Component context:")
                lines.extend(context_lines)

            lines.append("")
            lines.append("Label generated by Reloading Workshop")
            return "\n".join(lines)

    # If batch_id provided, try to produce a batch-centric label
    if batch_id:
        cur.execute("SELECT * FROM qc_batches WHERE id = ?", (batch_id,))
        b = cur.fetchone()
        if b:
            lines.append(f"Batch ID: {b['id']}")
            lines.append(f"Name: {_safe_row(b, 'name', '')}")
            lines.append(f"Batch size: {_safe_row(b, 'batch_size', '')}")
            lines.append(f"Target charge: {_safe_row(b, 'target_charge', '')}")
            lines.append("")
            lines.append("Measurements:")
            try:
                cur.execute(
                    "SELECT patron_number, value FROM qc_measurements WHERE batch_id = ? AND measurement_type = 'velocity' ORDER BY patron_number",
                    (batch_id,),
                )
                rows = cur.fetchall()
                for r in rows:
                    lines.append(f"#{r['patron_number']}: {r['value']}")
            except Exception:
                pass

            lines.append("")
            lines.append("Label generated by Reloading Workshop")
            return "\n".join(lines)

    return "No profile or batch specified."


def save_label_to_file(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
