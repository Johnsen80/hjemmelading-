from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _safe_float(value: str) -> float:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def build_reference_catalog_report(input_root: Path) -> dict[str, object]:
    projectile_rows = _read_csv(input_root / "gordon_projectile_reference.csv")
    propellant_rows = _read_csv(input_root / "gordon_propellant_reference.csv")
    caliber_rows = _read_csv(input_root / "gordon_caliber_reference_full.csv")

    bullet_products: dict[tuple[str, str], dict[str, object]] = {}
    bullet_by_manufacturer: dict[str, set[str]] = defaultdict(set)
    bullet_by_caliber: dict[str, set[str]] = defaultdict(set)
    bullet_missing_bc = 0

    for row in projectile_rows:
        manufacturer = row.get("manufacturer", "").strip() or "<unknown>"
        product = row.get("product_name", "").strip() or "<unknown>"
        caliber = row.get("caliber_in", "").strip() or "<unknown>"
        lotid = row.get("lotid", "").strip()
        key = (manufacturer, product)
        entry = bullet_products.setdefault(
            key,
            {
                "manufacturer": manufacturer,
                "product_name": product,
                "variants": 0,
                "lots": set(),
                "calibers": set(),
                "g1_values": set(),
                "g7_values": set(),
            },
        )
        entry["variants"] += 1
        if lotid:
            entry["lots"].add(lotid)
        entry["calibers"].add(caliber)
        g1 = _safe_float(row.get("g1_bc", ""))
        g7 = _safe_float(row.get("g7_bc", ""))
        if g1:
            entry["g1_values"].add(round(g1, 3))
        if g7:
            entry["g7_values"].add(round(g7, 3))
        if not g1 and not g7:
            bullet_missing_bc += 1
        bullet_by_manufacturer[manufacturer].add(product)
        bullet_by_caliber[caliber].add(f"{manufacturer} {product}".strip())

    powder_products: dict[tuple[str, str], dict[str, object]] = {}
    powder_by_manufacturer: dict[str, set[str]] = defaultdict(set)
    powder_variant_counter: Counter[str] = Counter()

    for row in propellant_rows:
        manufacturer = row.get("manufacturer", "").strip() or "<unknown>"
        product = row.get("product_name", "").strip() or "<unknown>"
        lotid = row.get("lotid", "").strip()
        key = (manufacturer, product)
        entry = powder_products.setdefault(
            key,
            {
                "manufacturer": manufacturer,
                "product_name": product,
                "variants": 0,
                "lots": set(),
                "ba_values": set(),
                "k_values": set(),
                "qex_values": set(),
            },
        )
        entry["variants"] += 1
        if lotid:
            entry["lots"].add(lotid)
        ba = _safe_float(row.get("Ba", ""))
        kval = _safe_float(row.get("k", ""))
        qex = _safe_float(row.get("Qex_kj_kg", ""))
        if ba:
            entry["ba_values"].add(round(ba, 4))
        if kval:
            entry["k_values"].add(round(kval, 4))
        if qex:
            entry["qex_values"].add(round(qex, 1))
        powder_by_manufacturer[manufacturer].add(product)
        powder_variant_counter[f"{manufacturer} {product}".strip()] += 1

    caliber_standards = Counter(
        (row.get("standard", "").strip() or "<unknown>") for row in caliber_rows
    )

    report = {
        "input_root": str(input_root),
        "projectile_rows": len(projectile_rows),
        "propellant_rows": len(propellant_rows),
        "caliber_rows": len(caliber_rows),
        "bullet_manufacturers": len(bullet_by_manufacturer),
        "bullet_unique_products": len(bullet_products),
        "bullet_rows_missing_bc": bullet_missing_bc,
        "powder_manufacturers": len(powder_by_manufacturer),
        "powder_unique_products": len(powder_products),
        "caliber_standards": dict(caliber_standards),
        "top_bullet_manufacturers": [
            {"manufacturer": name, "product_count": len(products)}
            for name, products in sorted(
                bullet_by_manufacturer.items(),
                key=lambda item: (-len(item[1]), item[0].lower()),
            )[:20]
        ],
        "top_powder_manufacturers": [
            {"manufacturer": name, "product_count": len(products)}
            for name, products in sorted(
                powder_by_manufacturer.items(),
                key=lambda item: (-len(item[1]), item[0].lower()),
            )[:20]
        ],
        "bullet_products": [
            {
                "manufacturer": item["manufacturer"],
                "product_name": item["product_name"],
                "variants": item["variants"],
                "lot_count": len(item["lots"]),
                "calibers": sorted(item["calibers"]),
                "g1_values": sorted(item["g1_values"]),
                "g7_values": sorted(item["g7_values"]),
            }
            for item in sorted(
                bullet_products.values(),
                key=lambda row: (
                    -int(row["variants"]),
                    row["manufacturer"],
                    row["product_name"],
                ),
            )
        ],
        "powder_products": [
            {
                "manufacturer": item["manufacturer"],
                "product_name": item["product_name"],
                "variants": item["variants"],
                "lot_count": len(item["lots"]),
                "lots": sorted(item["lots"]),
                "ba_values": sorted(item["ba_values"]),
                "k_values": sorted(item["k_values"]),
                "qex_values": sorted(item["qex_values"]),
            }
            for item in sorted(
                powder_products.values(),
                key=lambda row: (
                    -int(row["variants"]),
                    row["manufacturer"],
                    row["product_name"],
                ),
            )
        ],
        "bullet_products_by_caliber": [
            {"caliber": caliber, "product_count": len(products)}
            for caliber, products in sorted(
                bullet_by_caliber.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )
        ],
    }
    return report


def report_to_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Gordon Reference Catalog Report",
        "",
        f"- Input root: `{report['input_root']}`",
        f"- Projectile rows: `{report['projectile_rows']}`",
        f"- Propellant rows: `{report['propellant_rows']}`",
        f"- Caliber rows: `{report['caliber_rows']}`",
        "",
        "## Bullet Summary",
        "",
        f"- Manufacturers: `{report['bullet_manufacturers']}`",
        f"- Unique products: `{report['bullet_unique_products']}`",
        f"- Rows missing both G1 and G7: `{report['bullet_rows_missing_bc']}`",
        "",
        "## Powder Summary",
        "",
        f"- Manufacturers: `{report['powder_manufacturers']}`",
        f"- Unique products: `{report['powder_unique_products']}`",
        "",
        "## Caliber Standards",
        "",
    ]

    for standard, count in sorted(report["caliber_standards"].items()):
        lines.append(f"- `{standard}`: `{count}`")

    lines.extend(["", "## Top Bullet Manufacturers", ""])
    for row in report["top_bullet_manufacturers"]:
        lines.append(f"- `{row['manufacturer']}`: `{row['product_count']}` products")

    lines.extend(["", "## Top Powder Manufacturers", ""])
    for row in report["top_powder_manufacturers"]:
        lines.append(f"- `{row['manufacturer']}`: `{row['product_count']}` products")

    lines.extend(["", "## Bullet Products", ""])
    for row in report["bullet_products"]:
        lines.append(
            f"- `{row['manufacturer']} / {row['product_name']}`: "
            f"{row['variants']} variants, calibers={row['calibers']}, "
            f"G1={row['g1_values']}, G7={row['g7_values']}"
        )

    lines.extend(["", "## Powder Products", ""])
    for row in report["powder_products"]:
        lines.append(
            f"- `{row['manufacturer']} / {row['product_name']}`: "
            f"{row['variants']} variants, lots={row['lots']}, "
            f"Ba={row['ba_values']}, k={row['k_values']}, Qex={row['qex_values']}"
        )

    return "\n".join(lines)


def main() -> None:
    input_root = (
        Path(__file__).resolve().parents[1] / "tmp" / "gordon_known_sources_ingest"
    )
    output_root = (
        Path(__file__).resolve().parents[1] / "data" / "component_knowledge_base"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    report = build_reference_catalog_report(input_root)
    (output_root / "gordon_reference_catalog_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_root / "gordon_reference_catalog_report.md").write_text(
        report_to_markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "bullet_unique_products": report["bullet_unique_products"],
                "powder_unique_products": report["powder_unique_products"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
