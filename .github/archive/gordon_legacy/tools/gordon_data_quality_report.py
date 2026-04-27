from __future__ import annotations

import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "reloading.db"
EXPORT_DIR = PROJECT_ROOT / "data" / "gordon_temp_extract"
INVENTORY_JSON = EXPORT_DIR / "gordon_source_inventory.json"


def normalized(text: object) -> str:
    return str(text or "").replace("\\", "/").lower()


def is_documentation_sample_text(text: object) -> bool:
    value = normalized(text)
    return (
        "/doku/" in value
        or "/docs/" in value
        or "/samples/" in value
        or "deva-14981" in value
    )


def is_faq_archive_text(text: object) -> bool:
    value = normalized(text)
    return "/doku/en/faq/files/" in value or "/faq/files/" in value


def read_inventory() -> dict[str, object]:
    if not INVENTORY_JSON.exists():
        return {}
    try:
        return json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def find_quality_issues() -> dict[str, object]:
    inventory = read_inventory()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        profile_rows = conn.execute(
            "SELECT id, name, notes, component_context_json FROM ammo_profiles ORDER BY id"
        ).fetchall()
        session_rows = conn.execute(
            "SELECT id, ammo_profile_id, session_name, import_source, import_meta_json FROM chronograph_sessions ORDER BY id"
        ).fetchall()
        grt_rows = conn.execute(
            "SELECT id, ammo_profile_id, notes, grt_data FROM grt_data ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    archive_seed_profiles: list[dict[str, object]] = []
    live_dump_profiles: list[dict[str, object]] = []
    trusted_grtrace_profiles: list[dict[str, object]] = []
    documentation_profiles: list[dict[str, object]] = []
    for row in profile_rows:
        context_json = row["component_context_json"] or ""
        notes = row["notes"] or ""
        try:
            context = json.loads(context_json) if context_json else {}
        except Exception:
            context = {}
        source = str(context.get("source") or "")
        source_file = str(context.get("source_file") or "")
        item = {
            "id": row["id"],
            "name": row["name"],
            "notes": notes,
        }
        if source == "gordon_measurement_import":
            archive_seed_profiles.append(item)
        elif source == "gordon_dump_import":
            live_dump_profiles.append(item)
        elif source == "gordon_grtrace_import" and is_documentation_sample_text(
            source_file
        ):
            documentation_profiles.append(item)
        elif source == "gordon_grtrace_import":
            trusted_grtrace_profiles.append(item)
        elif source == "gordon_pressuretrace_import" and is_documentation_sample_text(
            source_file
        ):
            documentation_profiles.append(item)
        elif (
            is_documentation_sample_text(context_json)
            or is_documentation_sample_text(notes)
            or is_documentation_sample_text(row["name"])
        ):
            documentation_profiles.append(item)

    archive_reference_sessions: list[dict[str, object]] = []
    documentation_sessions: list[dict[str, object]] = []
    trusted_sessions: list[dict[str, object]] = []
    for row in session_rows:
        meta_json = row["import_meta_json"] or ""
        import_source = row["import_source"] or ""
        session_name = row["session_name"] or ""
        try:
            meta = json.loads(meta_json) if meta_json else {}
        except Exception:
            meta = {}
        source = str(meta.get("source") or "")
        source_file = str(meta.get("source_file") or "")
        item = {
            "id": row["id"],
            "ammo_profile_id": row["ammo_profile_id"],
            "session_name": session_name,
            "import_source": import_source,
        }
        if source == "gordon_pressuretrace_import" and is_faq_archive_text(source_file):
            archive_reference_sessions.append(item)
        elif source == "gordon_grtrace_import" and is_documentation_sample_text(
            source_file
        ):
            documentation_sessions.append(item)
        elif source in {"gordon_grtrace_import", "gordon_pressuretrace_import"}:
            trusted_sessions.append(item)
        elif (
            is_documentation_sample_text(meta_json)
            or is_documentation_sample_text(import_source)
            or is_documentation_sample_text(session_name)
        ):
            documentation_sessions.append(item)

    live_load_mismatches: list[dict[str, object]] = []
    for row in inventory.get("live_loads") or []:
        if row.get("title_projectile_mismatch"):
            live_load_mismatches.append(
                {
                    "path": row.get("path"),
                    "title": row.get("title"),
                    "projectile_label": row.get("projectile_label"),
                    "powder_name": row.get("powder_name"),
                    "powder_charge_grains": row.get("powder_charge_grains"),
                }
            )

    archive_seed_grt_rows: list[dict[str, object]] = []
    live_dump_grt_rows: list[dict[str, object]] = []
    documentation_grt_rows: list[dict[str, object]] = []
    mismatch_grt_rows: list[dict[str, object]] = []
    mismatch_paths = {normalized(row.get("path")) for row in live_load_mismatches}
    for row in grt_rows:
        raw_json = row["grt_data"] or ""
        notes = row["notes"] or ""
        item = {
            "id": row["id"],
            "ammo_profile_id": row["ammo_profile_id"],
            "notes": notes,
        }
        if any(path and path in normalized(raw_json) for path in mismatch_paths):
            mismatch_grt_rows.append(item)
        elif "Seeded from Gordon measurement import:" in notes:
            archive_seed_grt_rows.append(item)
        elif (
            "Imported from Gordon dump" in notes
            or "Auto-created from Gordon dump" in notes
        ):
            live_dump_grt_rows.append(item)
        elif is_documentation_sample_text(raw_json) or is_documentation_sample_text(
            notes
        ):
            documentation_grt_rows.append(item)

    return {
        "summary": {
            "archive_seed_profiles": len(archive_seed_profiles),
            "live_dump_profiles": len(live_dump_profiles),
            "trusted_grtrace_profiles": len(trusted_grtrace_profiles),
            "documentation_profiles": len(documentation_profiles),
            "archive_reference_sessions": len(archive_reference_sessions),
            "trusted_sessions": len(trusted_sessions),
            "documentation_sessions": len(documentation_sessions),
            "archive_seed_grt_rows": len(archive_seed_grt_rows),
            "live_dump_grt_rows": len(live_dump_grt_rows),
            "documentation_grt_rows": len(documentation_grt_rows),
            "mismatch_grt_rows": len(mismatch_grt_rows),
            "live_load_mismatches": len(live_load_mismatches),
        },
        "archive_seed_profiles": archive_seed_profiles,
        "live_dump_profiles": live_dump_profiles,
        "trusted_grtrace_profiles": trusted_grtrace_profiles,
        "documentation_profiles": documentation_profiles,
        "archive_reference_sessions": archive_reference_sessions,
        "trusted_sessions": trusted_sessions,
        "documentation_sessions": documentation_sessions,
        "archive_seed_grt_rows": archive_seed_grt_rows,
        "live_dump_grt_rows": live_dump_grt_rows,
        "documentation_grt_rows": documentation_grt_rows,
        "mismatch_grt_rows": mismatch_grt_rows,
        "live_load_mismatches": live_load_mismatches,
    }


def markdown_report(report: dict[str, object]) -> str:
    lines = ["# Gordon Data Quality Report", ""]
    lines.append("## Summary")
    for key, value in (report.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("## Archive Seed Profiles")
    for row in report.get("archive_seed_profiles") or []:
        lines.append(f"- #{row['id']} {row['name']}")

    lines.append("")
    lines.append("## Live Dump Profiles")
    for row in report.get("live_dump_profiles") or []:
        lines.append(f"- #{row['id']} {row['name']}")

    lines.append("")
    lines.append("## Trusted GRTrace Profiles")
    for row in report.get("trusted_grtrace_profiles") or []:
        lines.append(f"- #{row['id']} {row['name']}")

    lines.append("")
    lines.append("## Documentation Profiles")
    for row in report.get("documentation_profiles") or []:
        lines.append(f"- #{row['id']} {row['name']}")

    lines.append("")
    lines.append("## Archive Reference Sessions")
    for row in report.get("archive_reference_sessions") or []:
        lines.append(
            f"- #{row['id']} profile #{row['ammo_profile_id']}: {row['session_name']} | {row['import_source']}"
        )

    lines.append("")
    lines.append("## Trusted Sessions")
    for row in report.get("trusted_sessions") or []:
        lines.append(
            f"- #{row['id']} profile #{row['ammo_profile_id']}: {row['session_name']} | {row['import_source']}"
        )

    lines.append("")
    lines.append("## Documentation Sessions")
    for row in report.get("documentation_sessions") or []:
        lines.append(
            f"- #{row['id']} profile #{row['ammo_profile_id']}: {row['session_name']} | {row['import_source']}"
        )

    lines.append("")
    lines.append("## Archive Seed grt_data Rows")
    for row in report.get("archive_seed_grt_rows") or []:
        lines.append(
            f"- #{row['id']} profile #{row['ammo_profile_id']}: {row['notes']}"
        )

    lines.append("")
    lines.append("## Live Dump grt_data Rows")
    for row in report.get("live_dump_grt_rows") or []:
        lines.append(
            f"- #{row['id']} profile #{row['ammo_profile_id']}: {row['notes']}"
        )

    lines.append("")
    lines.append("## Documentation grt_data Rows")
    for row in report.get("documentation_grt_rows") or []:
        lines.append(
            f"- #{row['id']} profile #{row['ammo_profile_id']}: {row['notes']}"
        )

    lines.append("")
    lines.append("## Mismatch grt_data Rows")
    for row in report.get("mismatch_grt_rows") or []:
        lines.append(
            f"- #{row['id']} profile #{row['ammo_profile_id']}: {row['notes']}"
        )

    lines.append("")
    lines.append("## Live Load Mismatches")
    for row in report.get("live_load_mismatches") or []:
        lines.append(
            f"- {Path(str(row['path'])).name}: title `{row['title']}` vs projectile `{row['projectile_label']}` | {row['powder_name']} | {row['powder_charge_grains']} gr"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = find_quality_issues()
    json_path = EXPORT_DIR / "gordon_data_quality_report.json"
    md_path = EXPORT_DIR / "gordon_data_quality_report.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.write_text(markdown_report(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
