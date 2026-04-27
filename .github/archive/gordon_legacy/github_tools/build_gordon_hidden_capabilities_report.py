from __future__ import annotations

import json
from pathlib import Path


def _load_text(path: Path) -> str:
    return path.read_bytes().decode("latin1", "ignore")


def _snippet(text: str, index: int, radius: int = 220) -> str:
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + radius)
    snippet = text[start:end].replace("\x00", " ")
    return "".join(
        ch if 31 < ord(ch) < 127 or ch in "\r\n\t" else " " for ch in snippet
    )


def build_hidden_capabilities_report(install_root: Path) -> dict[str, object]:
    exe_path = install_root / "GordonsReloadingTool.exe"
    text = _load_text(exe_path)

    needles = {
        "sql_dump_table": "SqlDumpTable",
        "sql_dump": "SqlDump",
        "convert_to_mysql": "ConvertToMySQL",
        "xml_dump_projectile": "XmlUserFileDumpProjectile",
        "xml_dump_propellant": "XmlUserFileDumpPropellant",
        "xml_dump_caliber": "XmlUserFileDumpCaliber",
        "xml_import_projectile": "XmlUserFileImportProjectile",
        "xml_import_propellant": "XmlUserFileImportPropellant",
        "xml_import_caliber": "XmlUserFileImportCaliber",
        "attach_database": "REALSQLDatabase.AttachDatabase",
        "attach_database_with_key": "REALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String, encryptionKey as String)",
        "encrypt": "REALSQLDatabase.Encrypt(encryptionKey as String)",
        "decrypt": "REALSQLDatabase.Decrypt",
        "cip_url": "https://bobp.cip-bobp.org",
        "cip_url_builder": "/uploads/tdcc/tab-{id}/{file}",
        "saami_token": " SAAMI ",
        "wildcat_token": " Wildcat ",
        "projectilefile_tag": "<projectilefile>",
        "propellantfile_tag": "<propellantfile>",
        "caliberfile_tag": "<caliberfile>",
        "get_datasheet_url": "GetDatasheetURL",
        "get_cip_url": "GetCIPURL",
        "commandline_token": "CommandLine",
        "shell_execute": "Shell.Execute",
        "grtdb_dev_path": r"e:\projekte\innereBallistik\Tools\grtdb-",
    }

    hits: dict[str, dict[str, object]] = {}
    for key, needle in needles.items():
        idx = text.find(needle)
        hits[key] = {
            "needle": needle,
            "present": idx >= 0,
            "index": idx,
            "snippet": _snippet(text, idx),
        }

    pdfs = sorted((install_root / "doku").glob("grt-manual-*.pdf"))
    appdata_root = Path.home() / "AppData" / "Roaming" / "GordonsReloadingTool"

    report = {
        "install_root": str(install_root),
        "exe_path": str(exe_path),
        "pdf_manuals": [
            {"name": pdf.name, "size_bytes": pdf.stat().st_size} for pdf in pdfs
        ],
        "appdata_expected_root": str(appdata_root),
        "appdata_expected_files": [
            "projectile.xml",
            "propellant.xml",
            "caliber.xml",
        ],
        "capabilities": hits,
        "summary": {
            "has_internal_sql_dump": hits["sql_dump"]["present"]
            or hits["sql_dump_table"]["present"],
            "has_xml_dump_routines": (
                hits["xml_dump_projectile"]["present"]
                and hits["xml_dump_propellant"]["present"]
                and hits["xml_dump_caliber"]["present"]
            ),
            "has_xml_import_routines": (
                hits["xml_import_projectile"]["present"]
                and hits["xml_import_propellant"]["present"]
                and hits["xml_import_caliber"]["present"]
            ),
            "has_db_key_attach": hits["attach_database_with_key"]["present"],
            "cip_datasheet_support": hits["cip_url"]["present"]
            and hits["get_cip_url"]["present"],
            "saami_standard_token_present": hits["saami_token"]["present"],
            "native_component_tags_present": (
                hits["projectilefile_tag"]["present"]
                and hits["propellantfile_tag"]["present"]
                and hits["caliberfile_tag"]["present"]
            ),
        },
    }
    return report


def report_to_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Gordon Hidden Capabilities Report",
        "",
        f"- Install root: `{report['install_root']}`",
        f"- Exe path: `{report['exe_path']}`",
        f"- Expected AppData root: `{report['appdata_expected_root']}`",
        "",
        "## Summary",
        "",
    ]
    summary = report["summary"]
    for key, value in summary.items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## PDF Manuals", ""])
    for manual in report["pdf_manuals"]:
        lines.append(f"- `{manual['name']}` ({manual['size_bytes']} bytes)")

    lines.extend(["", "## Capability Hits", ""])
    for key, payload in report["capabilities"].items():
        lines.append(f"### {key}")
        lines.append(f"- needle: `{payload['needle']}`")
        lines.append(f"- present: `{payload['present']}`")
        lines.append(f"- index: `{payload['index']}`")
        if payload["snippet"]:
            lines.append("```text")
            lines.append(str(payload["snippet"]).strip())
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    install_root = Path(
        r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY"
    )
    output_root = (
        Path(__file__).resolve().parents[1] / "data" / "component_knowledge_base"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    report = build_hidden_capabilities_report(install_root)
    (output_root / "gordon_hidden_capabilities_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_root / "gordon_hidden_capabilities_report.md").write_text(
        report_to_markdown(report),
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
