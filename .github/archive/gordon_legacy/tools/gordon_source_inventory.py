from __future__ import annotations

import json
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "reloading.db"
EXPORT_DIR = PROJECT_ROOT / "data" / "gordon_temp_extract"
APPDATA_PROJECTILE_XML = Path(
    r"C:\Users\bjjoh\AppData\Roaming\GordonsReloadingTool\projectile.xml"
)
DATA_FRA_GORDON = PROJECT_ROOT / "data fra gordon"
DATA_FRA_GORDON_SUMMARY = DATA_FRA_GORDON / "Data" / "gordon_extraction_summary.json"
LIVE_DUMP_DIR = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe\dumps"
)
LIVE_LOADS_DIR = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\loads"
)
ARCHIVE_GRTRACE_DIR = DATA_FRA_GORDON / "plugins" / "GRTrace"


def is_documentation_sample(path: Path) -> bool:
    lowered = str(path).replace("\\", "/").lower()
    return "/doku/" in lowered or "/docs/" in lowered or "/samples/" in lowered


def decode(value: object) -> str:
    return unquote(str(value or "")).strip()


def safe_float(value: object) -> float | None:
    try:
        return float(str(value or "").replace(",", ".").strip())
    except Exception:
        return None


def db_counts() -> dict[str, int]:
    conn = sqlite3.connect(DB_PATH)
    try:
        tables = [
            "bullets",
            "powder",
            "primers",
            "cartridge_standards",
            "ammo_profiles",
            "grt_data",
            "chronograph_sessions",
            "chronograph_readings",
        ]
        return {
            table: conn.execute(f"select count(*) from {table}").fetchone()[0]
            for table in tables
        }
    finally:
        conn.close()


def parse_appdata_projectiles() -> list[dict[str, object]]:
    if not APPDATA_PROJECTILE_XML.exists():
        return []
    root = ET.parse(APPDATA_PROJECTILE_XML).getroot()
    rows: list[dict[str, object]] = []
    for node in root.findall("projectilefile"):
        row = {
            item.attrib.get("name"): decode(item.attrib.get("value", ""))
            for item in node.findall("var")
        }
        rows.append(
            {
                "manufacturer": row.get("mname", ""),
                "name": row.get("pname", ""),
                "lotid": row.get("lotid", ""),
                "caliber": row.get("caliber", ""),
                "weight_grains": safe_float(row.get("gmass")),
                "bc_g1": safe_float(row.get("g1bc")),
                "bc_g7": safe_float(row.get("g7bc")),
                "created_date": row.get("cdate", ""),
                "mode": row.get("mode", ""),
            }
        )
    return rows


def parse_grtload(path: Path) -> dict[str, object]:
    root = ET.parse(path).getroot().find(".//InnerBallistikInput")
    if root is None:
        return {"path": str(path), "error": "missing InnerBallistikInput"}

    def section_inputs(name: str) -> dict[str, str]:
        section = root.find(name)
        if section is None:
            return {}
        return {
            item.attrib.get("name", ""): decode(item.attrib.get("value", ""))
            for item in section.findall("input")
        }

    title = decode(root.findtext("title") or "")
    caliber = section_inputs("caliber")
    projectile = section_inputs("projectile")
    propellant = section_inputs("propellant")
    title_projectile_hint = ""
    if title and " grain " in title:
        pieces = title.split(" grain ", 1)[0].split()
        if pieces:
            title_projectile_hint = " ".join(pieces[-5:])
    projectile_label = " ".join(
        part
        for part in [projectile.get("mname", ""), projectile.get("pname", "")]
        if part
    ).strip()
    inconsistency = False
    if title and projectile_label:
        inconsistency = projectile_label.lower() not in title.lower()

    return {
        "path": str(path),
        "title": title,
        "caliber": caliber.get("CaliberName", ""),
        "oal_mm": safe_float(caliber.get("oal")),
        "projectile_manufacturer": projectile.get("mname", ""),
        "projectile_name": projectile.get("pname", ""),
        "projectile_label": projectile_label,
        "projectile_weight_grains": (
            round((safe_float(projectile.get("mp")) or 0.0) * 15.43235835, 2)
            if safe_float(projectile.get("mp")) is not None
            else None
        ),
        "projectile_bc_g1": safe_float(projectile.get("g1bc")),
        "powder_manufacturer": propellant.get("mname", ""),
        "powder_name": propellant.get("pname", ""),
        "powder_charge_grains": (
            round((safe_float(propellant.get("mc")) or 0.0) * 15.43235835, 2)
            if safe_float(propellant.get("mc")) is not None
            else None
        ),
        "title_projectile_hint": title_projectile_hint,
        "title_projectile_mismatch": inconsistency,
    }


def live_dump_summary() -> dict[str, object]:
    dumps = sorted(LIVE_DUMP_DIR.glob("*.json"))
    return {
        "count": len(dumps),
        "latest_files": [dump.name for dump in dumps[-10:]],
    }


def archive_summary() -> dict[str, object]:
    if not DATA_FRA_GORDON_SUMMARY.exists():
        return {}
    return json.loads(DATA_FRA_GORDON_SUMMARY.read_text(encoding="utf-8"))


def parse_grtrace_files() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(DATA_FRA_GORDON.rglob("*.grtrace")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        config = payload.get("Config") or {}
        avg = payload.get("AvgTrace") or {}
        traces = payload.get("Traces") or []
        rows.append(
            {
                "path": str(path),
                "is_documentation_sample": is_documentation_sample(path),
                "device": payload.get("Device"),
                "datetime": payload.get("DateTime"),
                "trace_count": len(traces),
                "projectile": decode(config.get("Projectile")),
                "propellant": decode(config.get("Propellant")),
                "case": decode(config.get("Case")),
                "primer": decode(config.get("Primer")),
                "avg_pmax_bar": safe_float(avg.get("pmax_bar")),
                "avg_pmax_psi": safe_float(avg.get("pmax_psi")),
                "avg_velocity_mps": (
                    sum(safe_float(trace.get("Velocity")) or 0.0 for trace in traces)
                    / len(traces)
                    if traces
                    else None
                ),
                "powder_charge_grains": safe_float(
                    (traces[0] if traces else {}).get("PowderCharge")
                ),
                "coal_mm": safe_float((traces[0] if traces else {}).get("COAL")),
            }
        )
    return rows


def build_report() -> dict[str, object]:
    archive_grtrace = parse_grtrace_files()
    return {
        "db_counts": db_counts(),
        "appdata_projectiles": parse_appdata_projectiles(),
        "live_loads": [
            parse_grtload(path) for path in sorted(LIVE_LOADS_DIR.glob("*.grtload"))
        ],
        "live_dumps": live_dump_summary(),
        "archive_summary": archive_summary(),
        "archive_grtrace": archive_grtrace,
        "archive_grtrace_summary": {
            "total_files": len(archive_grtrace),
            "documentation_samples": sum(
                1 for row in archive_grtrace if row.get("is_documentation_sample")
            ),
            "trusted_files": sum(
                1 for row in archive_grtrace if not row.get("is_documentation_sample")
            ),
        },
    }


def markdown_report(report: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Gordon Source Inventory")
    lines.append("")
    lines.append("## Database")
    for key, value in (report.get("db_counts") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## AppData Projectiles")
    for row in report.get("appdata_projectiles") or []:
        lines.append(
            f"- {row['manufacturer']} {row['name']} | {row['caliber']} | {row['weight_grains']} gr | BC G1 {row['bc_g1']}"
        )
    lines.append("")
    lines.append("## Live Loads")
    for row in report.get("live_loads") or []:
        mismatch = " MISMATCH" if row.get("title_projectile_mismatch") else ""
        lines.append(
            f"- {Path(row['path']).name}: {row['caliber']} | {row['projectile_label']} | {row['powder_manufacturer']} {row['powder_name']} | {row['powder_charge_grains']} gr{mismatch}"
        )
    lines.append("")
    lines.append("## Live Dumps")
    live_dumps = report.get("live_dumps") or {}
    lines.append(f"- count: {live_dumps.get('count', 0)}")
    for name in live_dumps.get("latest_files") or []:
        lines.append(f"- {name}")
    lines.append("")
    lines.append("## Archive Summary")
    archive = report.get("archive_summary") or {}
    for key in [
        "raw_projectiles",
        "raw_propellants",
        "raw_calibers",
        "measurements",
        "unique_bullets_for_app",
        "unique_powders_for_app",
    ]:
        if key in archive:
            lines.append(f"- {key}: {archive[key]}")
    lines.append("")
    lines.append("## GRTrace")
    grtrace_summary = report.get("archive_grtrace_summary") or {}
    if grtrace_summary:
        lines.append(f"- total_files: {grtrace_summary.get('total_files', 0)}")
        lines.append(
            f"- documentation_samples: {grtrace_summary.get('documentation_samples', 0)}"
        )
        lines.append(f"- trusted_files: {grtrace_summary.get('trusted_files', 0)}")
    for row in report.get("archive_grtrace") or []:
        sample_tag = " [DOC SAMPLE]" if row.get("is_documentation_sample") else ""
        lines.append(
            f"- {Path(row['path']).name}{sample_tag}: {row['trace_count']} traces | {row['projectile']} | {row['propellant']} | avg pmax {row['avg_pmax_bar']} bar | avg velocity {row['avg_velocity_mps']:.2f} m/s"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    json_path = EXPORT_DIR / "gordon_source_inventory.json"
    md_path = EXPORT_DIR / "gordon_source_inventory.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.write_text(markdown_report(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
