from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KB_DIR = REPO_ROOT / ".github" / "data" / "component_knowledge_base"
TMP_DIR = REPO_ROOT / ".github" / "tmp"

DEFAULT_INSTALL_ROOT = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY"
)
DEFAULT_APPDATA_ROOT = Path(r"C:\Users\bjjoh\AppData\Roaming\GordonsReloadingTool")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_report(
    install_root: Path = DEFAULT_INSTALL_ROOT,
    appdata_root: Path = DEFAULT_APPDATA_ROOT,
) -> dict[str, object]:
    hidden = _read_json(KB_DIR / "gordon_hidden_capabilities_report.json")
    known_sources = _read_json(
        TMP_DIR / "gordon_known_sources_ingest" / "gordon_known_sources_summary.json"
    )
    reference_catalog = _read_json(KB_DIR / "gordon_reference_catalog_report.json")

    plugin_docs = install_root / "doku" / "en" / "doku"
    plugin_command_docs = (
        sorted(plugin_docs.glob("plugin-api-cmd-*.txt")) if plugin_docs.exists() else []
    )

    user_files = {
        "projectile.xml": (appdata_root / "projectile.xml").exists(),
        "propellant.xml": (appdata_root / "propellant.xml").exists(),
        "caliber.xml": (appdata_root / "caliber.xml").exists(),
    }

    paths = {
        "readable_exports": {
            "status": "available",
            "why": "Vi har fungerende ingest for XML, *.projectile, *.propellant og *.caliber.",
            "current_rows": {
                "projectiles": known_sources.get("raw_projectiles", 0),
                "propellants": known_sources.get("raw_propellants", 0),
                "calibers": known_sources.get("raw_calibers", 0),
            },
            "confidence": "high",
        },
        "plugin_api": {
            "status": "probe_ready" if plugin_command_docs else "unknown",
            "why": "Gordon dokumenterer plugin-API og vi har lokale docs og manifestformat.",
            "command_docs": [path.name for path in plugin_command_docs],
            "confidence": "medium",
        },
        "ui_automation": {
            "status": "not_built",
            "why": "Dette er realistisk, men mer skjørt enn eksport og plugin.",
            "confidence": "medium",
        },
        "db_forensics": {
            "status": "last_resort",
            "why": "Binær rapport viser kryptert DB, attach med nøkkel og interne dump-rutiner, men vi mangler ekstern trigger.",
            "signals": {
                "has_internal_sql_dump": hidden.get("summary", {}).get(
                    "has_internal_sql_dump"
                ),
                "has_db_key_attach": hidden.get("summary", {}).get("has_db_key_attach"),
                "has_xml_dump_routines": hidden.get("summary", {}).get(
                    "has_xml_dump_routines"
                ),
            },
            "confidence": "low",
        },
    }

    recommended_order = [
        "readable_exports",
        "plugin_api",
        "ui_automation",
        "db_forensics",
    ]

    blockers = []
    if not user_files["propellant.xml"]:
        blockers.append(
            "Ingen propellant.xml i AppData ennå; full brukerkruttbase er ikke tilgjengelig fra åpen kilde alene."
        )
    if not user_files["caliber.xml"]:
        blockers.append(
            "Ingen caliber.xml i AppData ennå; brukerdefinerte kalibre må eksporteres eller hentes via annet spor."
        )
    if reference_catalog.get("counts", {}).get("powder_unique_products", 0) < 10:
        blockers.append(
            "Kruttdelen er fortsatt svært tynn i åpent uttrekk; full kruttdatabase krever mer enn lesbare filer."
        )

    next_actions = [
        "Kjør plugin-probe i Gordon sin plugin-mappe og verifiser IPC-tilkobling.",
        "Prøv å finne om plugin-sporet kan trigge eksport eller lese tab/resultatdata som kan brukes til større uttrekk.",
        "Hvis plugin-sporet ikke gir databasen, bygg UI-automatisering for systematisk eksport av projectile/propellant/caliber.",
        "Hold DB-forensics som siste utvei.",
    ]

    return {
        "install_root": str(install_root),
        "appdata_root": str(appdata_root),
        "user_files": user_files,
        "known_open_data": {
            "projectile_rows": known_sources.get("raw_projectiles", 0),
            "propellant_rows": known_sources.get("raw_propellants", 0),
            "caliber_rows": known_sources.get("raw_calibers", 0),
            "unique_bullet_products": reference_catalog.get(
                "bullet_unique_products", 0
            ),
            "unique_powder_products": reference_catalog.get(
                "powder_unique_products", 0
            ),
        },
        "paths": paths,
        "recommended_order": recommended_order,
        "blockers": blockers,
        "next_actions": next_actions,
    }


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Gordon Extraction Options Report",
        "",
        f"- Install root: `{report['install_root']}`",
        f"- AppData root: `{report['appdata_root']}`",
        "",
        "## Known Open Data",
    ]
    known = report["known_open_data"]
    lines.extend(
        [
            f"- Projectile rows: `{known['projectile_rows']}`",
            f"- Propellant rows: `{known['propellant_rows']}`",
            f"- Caliber rows: `{known['caliber_rows']}`",
            f"- Unique bullet products: `{known['unique_bullet_products']}`",
            f"- Unique powder products: `{known['unique_powder_products']}`",
            "",
            "## User Files",
        ]
    )
    for name, exists in report["user_files"].items():
        lines.append(f"- `{name}`: `{exists}`")

    lines.extend(["", "## Recommended Order"])
    for idx, item in enumerate(report["recommended_order"], start=1):
        lines.append(f"{idx}. `{item}`")

    lines.extend(["", "## Blockers"])
    blockers = report["blockers"]
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- Ingen tydelige blokkere.")

    lines.extend(["", "## Next Actions"])
    for item in report["next_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    out_dir = TMP_DIR / "gordon_extract"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "extraction_options_report.json"
    md_path = out_dir / "extraction_options_report.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.write_text(build_markdown(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
