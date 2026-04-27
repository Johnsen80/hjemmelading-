from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / ".github" / "data" / "component_knowledge_base"


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize(text: str) -> str:
    return "".join(ch.lower() for ch in (text or "") if ch.isalnum())


def _prefix_candidates(text: str) -> set[str]:
    parts = [part for part in (text or "").strip().split() if part]
    candidates: set[str] = set()
    for end in range(len(parts), 0, -1):
        prefix = " ".join(parts[:end]).strip()
        if len(prefix) >= 6:
            candidates.add(prefix)
    return candidates


def _split_aliases(text: str) -> list[str]:
    value = (text or "").strip()
    if not value:
        return []
    parts = re.split(r"(?<=[A-Za-z\)])\,\s+", value)
    return [part.strip() for part in parts if part.strip()]


def _load_saami_names() -> set[str]:
    names: set[str] = set()
    for filename in (
        "saami_rifle_standards.csv",
        "saami_newly_accepted_rifle_cartridges.csv",
        "saami_rifle_acceptance_announcements.csv",
    ):
        for row in _read_rows(KB_DIR / filename):
            for key in ("caliber_name", "alt_name"):
                value = (row.get(key) or "").strip()
                if value:
                    names.add(_normalize(value))
    return names


def _load_reference_calibers() -> list[dict[str, str]]:
    rows = _read_rows(KB_DIR / "calibers.csv")
    grouped: list[dict[str, object]] = []
    for row in rows:
        name = (row.get("name") or "").strip()
        standard = (row.get("standard") or "").strip()
        if not name:
            continue
        raw = {}
        try:
            raw = json.loads(row.get("raw_json") or "{}")
        except Exception:
            raw = {}
        canonical = name.split("(")[0].strip()
        aliases: set[str] = {canonical}
        altname = (raw.get("altname") or "").strip()
        cipname = (raw.get("cipname") or "").strip()
        if altname:
            aliases.update(_split_aliases(altname))
        if cipname:
            aliases.add(cipname)
        prefix_aliases: set[str] = set()
        for alias in list(aliases):
            prefix_aliases.update(_prefix_candidates(alias))
        aliases.update(prefix_aliases)
        alias_tokens = {_normalize(alias) for alias in aliases if alias.strip()}

        matched_group = None
        for group in grouped:
            group_tokens = set(group["alias_tokens"])
            if alias_tokens & group_tokens:
                matched_group = group
                break

        if matched_group is None:
            grouped.append(
                {
                    "name": canonical,
                    "standard": standard,
                    "aliases": set(aliases),
                    "alias_tokens": set(alias_tokens),
                }
            )
            continue

        matched_group["aliases"].update(aliases)
        matched_group["alias_tokens"].update(alias_tokens)
        current_name = str(matched_group["name"])
        if len(canonical) < len(current_name):
            matched_group["name"] = canonical

    results: list[dict[str, str]] = []
    for group in grouped:
        results.append(
            {
                "name": str(group["name"]),
                "standard": str(group["standard"]),
                "aliases": sorted(group["aliases"]),
            }
        )
    return sorted(results, key=lambda item: item["name"].lower())


def build_report() -> dict[str, object]:
    saami_names = _load_saami_names()
    calibers = _load_reference_calibers()

    covered: list[str] = []
    missing: list[str] = []

    for item in calibers:
        tokens = {_normalize(alias) for alias in item.get("aliases", [])}
        if tokens & saami_names:
            covered.append(item["name"])
        else:
            missing.append(item["name"])

    return {
        "counts": {
            "reference_calibers": len(calibers),
            "covered_by_saami_seed": len(covered),
            "missing_saami_seed": len(missing),
        },
        "covered": covered,
        "missing": missing,
    }


def build_markdown(report: dict[str, object]) -> str:
    counts = report["counts"]
    lines = [
        "# SAAMI Coverage Gap Report",
        "",
        "Sammenligner dagens SAAMI-seed mot patronnavnene vi allerede har i referansekaliberlaget.",
        "",
        "## Counts",
        f"- Referansekalibre: `{counts['reference_calibers']}`",
        f"- Dekket av SAAMI-seed: `{counts['covered_by_saami_seed']}`",
        f"- Mangler SAAMI-seed: `{counts['missing_saami_seed']}`",
        "",
        "## Covered",
    ]
    covered = report["covered"]
    if covered:
        for name in covered:
            lines.append(f"- `{name}`")
    else:
        lines.append("- Ingen")

    lines.extend(["", "## Missing"])
    missing = report["missing"]
    if missing:
        for name in missing:
            lines.append(f"- `{name}`")
    else:
        lines.append("- Ingen")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    json_path = KB_DIR / "saami_coverage_gap_report.json"
    md_path = KB_DIR / "saami_coverage_gap_report.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.write_text(build_markdown(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
