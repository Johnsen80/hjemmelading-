from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Database  # noqa: E402

PROJECT_DB_PATH = PROJECT_ROOT / "data" / "reloading.db"
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "data" / "gordon_temp_extract"
DEFAULT_INVENTORY_JSON = DEFAULT_EXPORT_DIR / "gordon_source_inventory.json"
DEFAULT_QUALITY_JSON = DEFAULT_EXPORT_DIR / "gordon_data_quality_report.json"
DEFAULT_PLUGIN_DIR = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe"
)
DEFAULT_DATA_DIR = PROJECT_ROOT / "data fra gordon" / "Data"


def read_probe_tail(path: Path, limit: int = 20) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    for line in lines[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"raw": line})
    return rows


def read_plugin_health() -> dict:
    health_tool = PROJECT_ROOT / "tools" / "check_gordon_plugin_health.py"
    if not health_tool.exists():
        return {"available": False, "error": "health_tool_missing"}
    try:
        result = subprocess.run(
            [sys.executable, str(health_tool)],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return {"available": True, "error": str(exc)}

    report: dict[str, object] = {
        "available": True,
        "returncode": result.returncode,
    }
    try:
        report["details"] = json.loads(result.stdout or "{}")
    except Exception:
        report["stdout"] = result.stdout.strip()
        report["stderr"] = result.stderr.strip()
    return report


def main(argv: list[str]) -> int:
    export_dir = DEFAULT_EXPORT_DIR
    export_dir.mkdir(parents=True, exist_ok=True)

    db = Database(db_path=str(PROJECT_DB_PATH))
    plugin_dump_dir = DEFAULT_PLUGIN_DIR / "dumps"
    probe_log_path = DEFAULT_PLUGIN_DIR / "probe_log.jsonl"

    bullets = db.get_all("bullets")
    powders = db.get_all("powder")
    primers = db.get_all("primers")
    calibers = db.get_all("cartridge_standards")
    profiles = db.get_all("ammo_profiles")
    grt_rows = db.get_all("grt_data")
    chrono_sessions = db.get_all("chronograph_sessions")
    chrono_readings = db.get_all("chronograph_readings")

    caliber_counter = Counter(str(row.get("caliber") or "").strip() for row in profiles)
    dump_files = []
    if plugin_dump_dir.exists():
        for path in sorted(
            plugin_dump_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            dump_files.append(
                {
                    "name": path.name,
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(
                        timespec="seconds"
                    ),
                }
            )

    plugin_health = read_plugin_health()
    inventory_summary: dict[str, object] = {}
    if DEFAULT_INVENTORY_JSON.exists():
        try:
            inventory_payload = json.loads(
                DEFAULT_INVENTORY_JSON.read_text(encoding="utf-8")
            )
            inventory_summary = {
                "appdata_projectiles": len(
                    inventory_payload.get("appdata_projectiles") or []
                ),
                "live_loads": len(inventory_payload.get("live_loads") or []),
                "live_dumps": (inventory_payload.get("live_dumps") or {}).get(
                    "count", 0
                ),
                "archive_measurements": (
                    inventory_payload.get("archive_summary") or {}
                ).get("measurements"),
                "archive_grtrace_files": len(
                    inventory_payload.get("archive_grtrace") or []
                ),
                "archive_grtrace_trusted_files": (
                    inventory_payload.get("archive_grtrace_summary") or {}
                ).get("trusted_files", 0),
                "archive_grtrace_documentation_samples": (
                    inventory_payload.get("archive_grtrace_summary") or {}
                ).get("documentation_samples", 0),
            }
        except Exception:
            inventory_summary = {"error": "inventory_parse_failed"}

    quality_summary: dict[str, object] = {}
    if DEFAULT_QUALITY_JSON.exists():
        try:
            quality_payload = json.loads(
                DEFAULT_QUALITY_JSON.read_text(encoding="utf-8")
            )
            quality_summary = quality_payload.get("summary") or {}
        except Exception:
            quality_summary = {"error": "quality_parse_failed"}

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_db_path": str(PROJECT_DB_PATH),
        "gordon_data_dir": str(DEFAULT_DATA_DIR),
        "plugin_dump_dir": str(plugin_dump_dir),
        "counts": {
            "bullets": len(bullets),
            "powders": len(powders),
            "primers": len(primers),
            "cartridge_standards": len(calibers),
            "ammo_profiles": len(profiles),
            "grt_data": len(grt_rows),
            "chronograph_sessions": len(chrono_sessions),
            "chronograph_readings": len(chrono_readings),
            "plugin_dumps": len(dump_files),
        },
        "component_sources": {
            "bullets": Counter(
                str(row.get("source") or "unknown") for row in bullets
            ).most_common(10),
            "powders": Counter(
                str(row.get("source") or "unknown") for row in powders
            ).most_common(10),
        },
        "ammo_profile_calibers": caliber_counter.most_common(),
        "recent_dump_files": dump_files[:10],
        "recent_chronograph_sessions": sorted(
            [
                {
                    "id": row.get("id"),
                    "ammo_profile_id": row.get("ammo_profile_id"),
                    "session_name": row.get("session_name"),
                    "session_date": row.get("session_date"),
                    "avg_velocity_fps": row.get("avg_velocity_fps"),
                    "shot_count": row.get("shot_count"),
                    "import_source": row.get("import_source"),
                }
                for row in chrono_sessions
            ],
            key=lambda item: (item.get("id") or 0),
            reverse=True,
        )[:10],
        "inventory_summary": inventory_summary,
        "quality_summary": quality_summary,
        "plugin_health": plugin_health,
        "probe_log_tail": read_probe_tail(probe_log_path, limit=30),
        "current_state": {
            "components_imported": len(bullets) > 0 and len(powders) > 0,
            "measurement_profiles_seeded": len(profiles) > 0 and len(grt_rows) > 0,
            "chronograph_data_imported": len(chrono_sessions) > 0
            and len(chrono_readings) > 0,
            "live_plugin_dump_detected": bool(dump_files),
            "documentation_grtrace_present": bool(
                (inventory_summary.get("archive_grtrace_documentation_samples") or 0)
                > 0
            ),
            "quality_issues_detected": any(
                (quality_summary.get(key) or 0) > 0
                for key in quality_summary
                if key != "error"
            ),
            "plugin_health_available": bool(plugin_health.get("available")),
            "plugin_launch_selftest_ok": bool(
                (
                    (plugin_health.get("details") or {}).get("launch_target_selftest")
                    or {}
                ).get("returncode")
                == 0
            ),
        },
        "next_actions": [
            "Run Gordon and trigger Dump TabList / Dump Active Tab / Dump Active Tab Results in the plugin for more live tab_results.",
            "Review inconsistent live .grtload files where title and projectile section disagree before treating them as trusted source data.",
            "Promote stable Gordon import logic out of TEMP modules after enough live dumps are collected.",
        ],
    }

    json_path = export_dir / "gordon_status_report.json"
    md_path = export_dir / "gordon_status_report.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# Gordon Status Report",
        "",
        f"Generated: {report['created_at']}",
        "",
        "## Counts",
        "",
    ]
    for key, value in report["counts"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(
        [
            "",
            "## Current State",
            "",
            f"- Components imported: {report['current_state']['components_imported']}",
            f"- Measurement profiles seeded: {report['current_state']['measurement_profiles_seeded']}",
            f"- Chronograph data imported: {report['current_state']['chronograph_data_imported']}",
            f"- Live plugin dump detected: {report['current_state']['live_plugin_dump_detected']}",
            f"- Documentation GRTrace present: {report['current_state']['documentation_grtrace_present']}",
            f"- Quality issues detected: {report['current_state']['quality_issues_detected']}",
            f"- Plugin health available: {report['current_state']['plugin_health_available']}",
            f"- Plugin launch selftest ok: {report['current_state']['plugin_launch_selftest_ok']}",
            "",
            "## Inventory Summary",
            "",
        ]
    )

    for key, value in report["inventory_summary"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Quality Summary", ""])
    for key, value in report["quality_summary"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(
        [
            "",
            "## Plugin Health",
            "",
        ]
    )

    lines.append(f"- Available: {plugin_health.get('available', False)}")
    lines.append(f"- Return code: {plugin_health.get('returncode', 'n/a')}")
    details = plugin_health.get("details") or {}
    if isinstance(details, dict):
        lines.append(
            f"- Top manifest enabled: {details.get('top_manifest_enabled', 'unknown')}"
        )
        lines.append(
            f"- Nested manifest enabled: {details.get('nested_manifest_enabled', 'unknown')}"
        )
        lines.append(f"- Launch target: {details.get('resolved_launch_target', '')}")
        launch_selftest = details.get("launch_target_selftest") or {}
        if isinstance(launch_selftest, dict):
            lines.append(
                f"- Launch target selftest returncode: {launch_selftest.get('returncode', 'n/a')}"
            )
            lines.append(
                f"- Launch target selftest log_grew: {launch_selftest.get('log_grew', False)}"
            )

    lines.extend(["", "## Ammo Profiles By Caliber", ""])
    for caliber, count in report["ammo_profile_calibers"]:
        lines.append(f"- `{caliber}`: {count}")

    lines.extend(["", "## Recent Chronograph Sessions", ""])
    for row in report["recent_chronograph_sessions"]:
        lines.append(
            f"- `#{row['id']}` `{row['session_name']}` | avg `{row['avg_velocity_fps']}` fps | shots `{row['shot_count']}` | source `{row['import_source']}`"
        )

    lines.extend(["", "## Next Actions", ""])
    for action in report["next_actions"]:
        lines.append(f"- {action}")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
