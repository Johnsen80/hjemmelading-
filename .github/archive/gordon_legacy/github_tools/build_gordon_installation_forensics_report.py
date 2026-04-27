from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

DEFAULT_INSTALL_ROOT = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY"
)
DEFAULT_DB_COPY = Path(
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\data fra gordon\GordonsReloadingTool.db"
)
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "component_knowledge_base"


def extract_printable_strings(data: bytes, min_len: int = 6) -> list[str]:
    return [
        s.decode("latin1", "ignore") for s in re.findall(rb"[ -~]{%d,}" % min_len, data)
    ]


def extract_schema(text: str, table_name: str) -> str | None:
    pattern = f"CREATE TABLE {table_name} ("
    start = text.find(pattern)
    if start == -1:
        return None
    end = text.find(");", start)
    if end == -1:
        return None
    return text[start : end + 2]


def find_strings_containing(
    strings: list[str], needle: str, limit: int = 30
) -> list[str]:
    lowered = needle.lower()
    return [s for s in strings if lowered in s.lower()][:limit]


def build_report(install_root: Path, db_copy: Path) -> dict:
    exe_path = install_root / "GordonsReloadingTool.exe"
    exe_bytes = exe_path.read_bytes()
    exe_text = exe_bytes.decode("latin1", "ignore")
    strings = extract_printable_strings(exe_bytes)

    file_counts = Counter(
        path.suffix.lower() or "<no_ext>"
        for path in install_root.rglob("*")
        if path.is_file()
    )

    docs = {
        "projectile_doc": str(
            install_root / "doku" / "en" / "doku" / "dbprojectile.txt"
        ),
        "propellant_doc": str(
            install_root / "doku" / "en" / "doku" / "dbpropellant.txt"
        ),
        "caliber_doc": str(install_root / "doku" / "en" / "doku" / "dbcaliber.txt"),
    }

    report = {
        "install_root": str(install_root),
        "db_copy": str(db_copy),
        "exe_path": str(exe_path),
        "db_exists": db_copy.exists(),
        "db_size_bytes": db_copy.stat().st_size if db_copy.exists() else None,
        "extension_counts_top": dict(file_counts.most_common(20)),
        "docs": docs,
        "evidence": {
            "real_sql_database_present": bool(
                find_strings_containing(strings, "REALSQLDatabase", 1)
            ),
            "database_encryption_api_present": bool(
                find_strings_containing(strings, "EncryptionKey", 1)
            ),
            "attach_database_with_key_present": bool(
                find_strings_containing(
                    strings,
                    "AttachDatabase(file as FolderItem, databaseName as String, encryptionKey as String)",
                    1,
                )
            ),
            "cip_url_present": bool(
                find_strings_containing(strings, "https://bobp.cip-bobp.org", 1)
            ),
            "saami_url_present": bool(find_strings_containing(strings, "saami.org", 1)),
            "user_xml_dump_functions_present": bool(
                find_strings_containing(strings, "XmlUserFileDump", 1)
            ),
        },
        "schema": {
            "caliber": extract_schema(exe_text, "caliber"),
            "projectile": extract_schema(exe_text, "projectile"),
            "propellant": extract_schema(exe_text, "propellant"),
        },
        "queries": {
            "caliber": find_strings_containing(strings, "select * from caliber", 10),
            "projectile": find_strings_containing(
                strings, "select * from projectile", 10
            ),
            "propellant": find_strings_containing(
                strings, "select * from propellant", 10
            ),
        },
        "database_signals": {
            "db_filename_hits": find_strings_containing(
                strings, "GordonsReloadingTool.db", 10
            ),
            "encryption_hits": find_strings_containing(strings, "EncryptionKey", 20),
            "cip_hits": find_strings_containing(strings, "cip", 40),
            "saami_hits": find_strings_containing(strings, "saami", 20),
            "user_dump_hits": find_strings_containing(strings, "XmlUserFileDump", 20),
        },
        "interpretation": {
            "projectile": (
                "Built-in projectile catalog exists in Gordon and uses an internal SQL schema. "
                "The public docs only describe exporting selected projectile records to XML and user XML backups."
            ),
            "propellant": (
                "Built-in propellant catalog exists in Gordon and includes full powder-model fields "
                "such as Ba, Qex, k, eta, a0, z1, z2, pc, pcd, pt, tcc and tch."
            ),
            "caliber": (
                "Built-in caliber catalog is strongly CIP-oriented in this nightly build. "
                "Schema and strings expose CIP fields and CIP datasheet URL handling, but no SAAMI URL evidence was found."
            ),
            "db": (
                "The .db file is almost certainly a SQL-backed encrypted database rather than a plain SQLite file. "
                "The executable exposes REALSQLDatabase encryption APIs and SQL table definitions."
            ),
        },
        "next_steps": [
            "Prefer building our own database from extracted Gordon schema plus official CIP/SAAMI/manufacturer data.",
            "Attempt UI automation or internal command discovery for bulk export, because docs only expose single-record export.",
            "Investigate whether the Gordon executable can be coerced to dump user XML for built-in records or expose a hidden database maintenance action.",
            "Treat SAAMI as a separate ingestion track because this Gordon build shows strong CIP evidence but no SAAMI URL evidence.",
        ],
    }
    return report


def write_outputs(report: dict) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "gordon_installation_forensics_report.json"
    md_path = OUTPUT_DIR / "gordon_installation_forensics_report.md"

    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    md_lines = [
        "# Gordon Installation Forensics Report",
        "",
        f"- Install root: `{report['install_root']}`",
        f"- DB copy: `{report['db_copy']}`",
        f"- DB size: `{report['db_size_bytes']}` bytes",
        "",
        "## Key Findings",
        "",
        f"- `REALSQLDatabase` present: `{report['evidence']['real_sql_database_present']}`",
        f"- encryption API present: `{report['evidence']['database_encryption_api_present']}`",
        f"- attach-with-key API present: `{report['evidence']['attach_database_with_key_present']}`",
        f"- CIP URL present: `{report['evidence']['cip_url_present']}`",
        f"- SAAMI URL present: `{report['evidence']['saami_url_present']}`",
        f"- user XML dump functions present: `{report['evidence']['user_xml_dump_functions_present']}`",
        "",
        "## Interpretation",
        "",
    ]
    for key, value in report["interpretation"].items():
        md_lines.append(f"- **{key}**: {value}")

    md_lines.extend(
        [
            "",
            "## SQL Schema Extracts",
            "",
            "### caliber",
            "```sql",
            report["schema"]["caliber"] or "<not found>",
            "```",
            "",
            "### projectile",
            "```sql",
            report["schema"]["projectile"] or "<not found>",
            "```",
            "",
            "### propellant",
            "```sql",
            report["schema"]["propellant"] or "<not found>",
            "```",
            "",
            "## Next Steps",
            "",
        ]
    )
    for step in report["next_steps"]:
        md_lines.append(f"- {step}")

    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    report = build_report(DEFAULT_INSTALL_ROOT, DEFAULT_DB_COPY)
    json_path, md_path = write_outputs(report)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
