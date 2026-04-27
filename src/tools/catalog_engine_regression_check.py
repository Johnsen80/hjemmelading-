from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from src.tools.bullet_catalog_cleanup import clean_bullet_rows
from src.tools.components_catalog_service import _read_csv_rows, merge_into_db
from src.tools.powder_catalog_cleanup import clean_powder_rows

DEFAULT_EXPORT_ROOT = REPO_ROOT / ".github" / "data" / "exports"


def _query_rows(db_path: Path, sql: str) -> list[tuple[Any, ...]]:
    con = sqlite3.connect(str(db_path))
    try:
        return list(con.execute(sql))
    finally:
        con.close()


def _load_raw_components(export_root: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "bullets": _read_csv_rows(export_root / "bullets_catalog_master.csv"),
        "powders": _read_csv_rows(export_root / "powder_catalog_master.csv"),
        "calibers": [],
    }


def _load_clean_components(
    export_root: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int], dict[str, int]]:
    bullet_rows, bullet_stats = clean_bullet_rows(
        _read_csv_rows(export_root / "bullets_catalog_master.csv")
    )
    powder_rows, powder_stats = clean_powder_rows(
        _read_csv_rows(export_root / "powder_catalog_master.csv")
    )
    return (
        {
            "bullets": bullet_rows,
            "powders": powder_rows,
            "calibers": [],
        },
        bullet_stats,
        powder_stats,
    )


def run_engine_regression_check(
    export_root: Path = DEFAULT_EXPORT_ROOT,
) -> dict[str, Any]:
    temp_root = Path(
        mkdtemp(
            prefix="catalog-engine-check-", dir=str(REPO_ROOT / ".github" / "test_tmp")
        )
    )
    raw_db = temp_root / "raw.db"
    clean_db = temp_root / "clean.db"
    try:
        raw_components = _load_raw_components(export_root)
        clean_components, bullet_stats, powder_stats = _load_clean_components(
            export_root
        )

        raw_report = merge_into_db(raw_components, raw_db)
        clean_report = merge_into_db(clean_components, clean_db)

        raw_counts = {
            "bullets": _query_rows(raw_db, "select count(*) from bullets")[0][0],
            "powders": _query_rows(raw_db, "select count(*) from powder")[0][0],
            "lots": _query_rows(raw_db, "select count(*) from component_lots")[0][0],
            "powder_models": _query_rows(
                raw_db, "select count(*) from powder_database"
            )[0][0],
            "powder_models_usable": _query_rows(
                raw_db,
                "select count(*) from powder_database where usable_for_simulation = 1",
            )[0][0],
        }
        clean_counts = {
            "bullets": _query_rows(clean_db, "select count(*) from bullets")[0][0],
            "powders": _query_rows(clean_db, "select count(*) from powder")[0][0],
            "lots": _query_rows(clean_db, "select count(*) from component_lots")[0][0],
            "powder_models": _query_rows(
                clean_db, "select count(*) from powder_database"
            )[0][0],
            "powder_models_usable": _query_rows(
                clean_db,
                "select count(*) from powder_database where usable_for_simulation = 1",
            )[0][0],
        }

        raw_bullet_core = set(
            _query_rows(
                raw_db,
                "select lower(trim(manufacturer)), lower(trim(name)), replace(lower(trim(caliber)), ' ', ''), coalesce(weight_grains, 0), coalesce(bc_g1, 0), coalesce(bc_g7, 0), lower(coalesce(bullet_type, '')) from bullets",
            )
        )
        clean_bullet_core = set(
            _query_rows(
                clean_db,
                "select lower(trim(manufacturer)), lower(trim(name)), replace(lower(trim(caliber)), ' ', ''), coalesce(weight_grains, 0), coalesce(bc_g1, 0), coalesce(bc_g7, 0), lower(coalesce(bullet_type, '')) from bullets",
            )
        )
        raw_powder_core = set(
            _query_rows(
                raw_db,
                "select lower(trim(manufacturer)), lower(trim(name)), coalesce(burn_rate, ''), coalesce(density, '') from powder",
            )
        )
        clean_powder_core = set(
            _query_rows(
                clean_db,
                "select lower(trim(manufacturer)), lower(trim(name)), coalesce(burn_rate, ''), coalesce(density, '') from powder",
            )
        )
        raw_powder_model_core = set(
            _query_rows(
                raw_db,
                "select powder_id, coalesce(quickload_ba_value, 0), coalesce(qex_kj_per_kg, 0), coalesce(k_ratio, 0), coalesce(a0, 0), coalesce(z1, 0), coalesce(z2, 0), coalesce(eta_cm3_per_kg, 0), coalesce(pc_kg_m3, 0), coalesce(pcd_kg_m3, 0), coalesce(usable_for_simulation, 0) from powder_database",
            )
        )
        clean_powder_model_core = set(
            _query_rows(
                clean_db,
                "select powder_id, coalesce(quickload_ba_value, 0), coalesce(qex_kj_per_kg, 0), coalesce(k_ratio, 0), coalesce(a0, 0), coalesce(z1, 0), coalesce(z2, 0), coalesce(eta_cm3_per_kg, 0), coalesce(pc_kg_m3, 0), coalesce(pcd_kg_m3, 0), coalesce(usable_for_simulation, 0) from powder_database",
            )
        )

        return {
            "bullet_cleanup_stats": bullet_stats,
            "powder_cleanup_stats": powder_stats,
            "raw_import_report": raw_report,
            "clean_import_report": clean_report,
            "raw_counts": raw_counts,
            "clean_counts": clean_counts,
            "bullet_core_equal": raw_bullet_core == clean_bullet_core,
            "powder_core_equal": raw_powder_core == clean_powder_core,
            "powder_model_core_equal": raw_powder_model_core == clean_powder_model_core,
            "bullet_core_delta": len(
                raw_bullet_core.symmetric_difference(clean_bullet_core)
            ),
            "powder_core_delta": len(
                raw_powder_core.symmetric_difference(clean_powder_core)
            ),
            "powder_model_core_delta": len(
                raw_powder_model_core.symmetric_difference(clean_powder_model_core)
            ),
        }
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def build_markdown_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Catalog Engine Regression Check",
            "",
            "## Result",
            "",
            f"- Bullet core equal: `{report['bullet_core_equal']}`",
            f"- Powder core equal: `{report['powder_core_equal']}`",
            f"- Powder model core equal: `{report['powder_model_core_equal']}`",
            f"- Bullet core delta: `{report['bullet_core_delta']}`",
            f"- Powder core delta: `{report['powder_core_delta']}`",
            f"- Powder model core delta: `{report['powder_model_core_delta']}`",
            "",
            "## Import Counts",
            "",
            f"- Raw bullets: `{report['raw_counts']['bullets']}` | Clean bullets: `{report['clean_counts']['bullets']}`",
            f"- Raw powders: `{report['raw_counts']['powders']}` | Clean powders: `{report['clean_counts']['powders']}`",
            f"- Raw lots: `{report['raw_counts']['lots']}` | Clean lots: `{report['clean_counts']['lots']}`",
            f"- Raw powder models: `{report['raw_counts']['powder_models']}` | Clean powder models: `{report['clean_counts']['powder_models']}`",
            f"- Raw usable powder models: `{report['raw_counts']['powder_models_usable']}` | Clean usable powder models: `{report['clean_counts']['powder_models_usable']}`",
            "",
            "## Interpretation",
            "",
            "- This check imports raw and cleaned catalogs into separate temporary databases.",
            "- It then compares engine-critical fields in `bullets`, `powder`, and `powder_database`.",
            "- Matching core sets mean the cleanup pass changed naming/presentation consistency only, not the motor-relevant seed data.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    args = parser.parse_args()

    report = run_engine_regression_check(args.export_root)
    if args.report_json is not None:
        args.report_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if args.report_md is not None:
        args.report_md.write_text(build_markdown_report(report), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
