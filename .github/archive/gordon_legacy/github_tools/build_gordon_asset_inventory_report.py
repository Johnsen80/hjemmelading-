from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def build_asset_inventory_report(install_root: Path) -> dict[str, object]:
    files = [path for path in install_root.rglob("*") if path.is_file()]
    extension_counts = Counter(path.suffix.lower() or "<noext>" for path in files)
    top_extensions = [
        {"extension": ext, "count": count}
        for ext, count in extension_counts.most_common(40)
    ]

    manuals = sorted((install_root / "doku").glob("grt-manual-*.pdf"))
    grtloads = sorted(install_root.rglob("*.grtload"))
    xml_like = sorted(
        path
        for path in files
        if path.suffix.lower() in {".xml", ".projectile", ".propellant", ".caliber"}
    )

    return {
        "install_root": str(install_root),
        "file_count": len(files),
        "top_extensions": top_extensions,
        "manual_pdfs": [
            {"name": path.name, "size_bytes": path.stat().st_size} for path in manuals
        ],
        "sample_grtloads": [
            str(path.relative_to(install_root)) for path in grtloads[:20]
        ],
        "xml_like_files": [
            str(path.relative_to(install_root)) for path in xml_like[:50]
        ],
    }


def report_to_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Gordon Asset Inventory Report",
        "",
        f"- Install root: `{report['install_root']}`",
        f"- File count: `{report['file_count']}`",
        "",
        "## Top Extensions",
        "",
    ]
    for row in report["top_extensions"]:
        lines.append(f"- `{row['extension']}`: `{row['count']}`")

    lines.extend(["", "## PDF Manuals", ""])
    for row in report["manual_pdfs"]:
        lines.append(f"- `{row['name']}` ({row['size_bytes']} bytes)")

    lines.extend(["", "## Sample .grtload Files", ""])
    for item in report["sample_grtloads"]:
        lines.append(f"- `{item}`")

    lines.extend(["", "## XML-like Files", ""])
    for item in report["xml_like_files"]:
        lines.append(f"- `{item}`")

    return "\n".join(lines)


def main() -> None:
    install_root = Path(
        r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY"
    )
    output_root = (
        Path(__file__).resolve().parents[1] / "data" / "component_knowledge_base"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    report = build_asset_inventory_report(install_root)
    (output_root / "gordon_asset_inventory_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_root / "gordon_asset_inventory_report.md").write_text(
        report_to_markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps({"file_count": report["file_count"]}, indent=2, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
