from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.database.database import Database
from src.tools.cartridge_standards_service import (
    import_cartridge_standards_from_knowledge_base,
)


def _build_report() -> dict[str, object]:
    tmp_db = (
        REPO_ROOT / ".github" / "test_tmp" / "reference_cartridge_standards_report.db"
    )
    if tmp_db.exists():
        tmp_db.unlink()

    csv_paths = [
        REPO_ROOT / ".github" / "data" / "component_knowledge_base" / "calibers.csv",
        REPO_ROOT
        / ".github"
        / "data"
        / "component_knowledge_base"
        / "saami_rifle_standards.csv",
        REPO_ROOT
        / ".github"
        / "data"
        / "component_knowledge_base"
        / "saami_newly_accepted_rifle_cartridges.csv",
        REPO_ROOT
        / ".github"
        / "data"
        / "component_knowledge_base"
        / "saami_rifle_acceptance_announcements.csv",
    ]

    database = Database(str(tmp_db))
    try:
        imports = {}
        for path in csv_paths:
            imports[path.name] = import_cartridge_standards_from_knowledge_base(
                database, path
            )

        rows = database.list_cartridge_standards()
        standard_counts = Counter(str(row.get("standard_body") or "") for row in rows)
        source_counts = Counter(str(row.get("source_kind") or "") for row in rows)
        evidence_counts = Counter(str(row.get("evidence_level") or "") for row in rows)

        caliber_map: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            caliber_name = str(row.get("caliber_name") or "").strip()
            standard_body = str(row.get("standard_body") or "").strip()
            if caliber_name and standard_body:
                caliber_map[caliber_name].append(standard_body)

        multi_standard = {
            caliber: sorted(set(standards))
            for caliber, standards in caliber_map.items()
            if len(set(standards)) > 1
        }

        return {
            "imports": imports,
            "counts": {
                "total": len(rows),
                "by_standard_body": dict(sorted(standard_counts.items())),
                "by_source_kind": dict(sorted(source_counts.items())),
                "by_evidence_level": dict(sorted(evidence_counts.items())),
                "multi_standard_calibers": len(multi_standard),
            },
            "multi_standard_examples": dict(sorted(multi_standard.items())),
        }
    finally:
        database.close()


def _build_markdown(report: dict[str, object]) -> str:
    counts = report["counts"]
    lines = [
        "# Reference Cartridge Standards Report",
        "",
        "Kombinert oversikt etter import av Gordon/CIP-kilder og det lille offisielle SAAMI-seedet.",
        "",
        "## Imports",
    ]
    for name, result in sorted(report["imports"].items()):
        lines.append(
            f"- `{name}`: {result['added_or_updated']} add/update, {result['skipped']} hoppet over"
        )

    lines.extend(
        [
            "",
            "## Counts",
            f"- Totalt: `{counts['total']}`",
            f"- Flere standardlag for samme kaliber: `{counts['multi_standard_calibers']}`",
            f"- Standard bodies: `{counts['by_standard_body']}`",
            f"- Source kinds: `{counts['by_source_kind']}`",
            f"- Evidence levels: `{counts['by_evidence_level']}`",
            "",
            "## Multi-Standard Examples",
        ]
    )

    examples = report["multi_standard_examples"]
    if not examples:
        lines.append("- Ingen")
    else:
        for caliber, standards in examples.items():
            lines.append(f"- `{caliber}`: {', '.join(standards)}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    output_dir = REPO_ROOT / ".github" / "data" / "component_knowledge_base"
    output_dir.mkdir(parents=True, exist_ok=True)

    report = _build_report()
    json_path = output_dir / "reference_cartridge_standards_report.json"
    md_path = output_dir / "reference_cartridge_standards_report.md"

    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.write_text(_build_markdown(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
