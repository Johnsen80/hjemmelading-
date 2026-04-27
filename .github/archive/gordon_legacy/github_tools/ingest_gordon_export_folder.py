from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GITHUB_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.database.database import Database
from src.tools.gordon_reference_snapshot_service import import_gordon_readable_snapshots


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a folder of Gordon XML/GRT exports into our own CSV/snapshot pipeline."
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=GITHUB_ROOT / "data" / "component_knowledge_base",
    )
    parser.add_argument(
        "--component-db",
        type=Path,
        default=REPO_ROOT
        / ".github"
        / "data"
        / "component_knowledge_base"
        / "local_component_pack.json",
    )
    parser.add_argument(
        "--snapshot-db",
        type=Path,
        default=REPO_ROOT / ".github" / "test_tmp" / "gordon_ingest_snapshots.db",
    )
    args = parser.parse_args()

    extract_module = _load_module(
        "extract_gordon_data_tool", GITHUB_ROOT / "tools" / "extract_gordon_data.py"
    )
    extracted = extract_module.extract_gordon_data(args.source_root)
    bullets = extract_module._normalize_pack_notes(  # type: ignore[attr-defined]
        extract_module._dedupe_rows(extracted["bullets_for_app"], "bullet"),  # type: ignore[attr-defined]
        "Gordon eksport importert til eget bibliotek.",
    )
    powders = extract_module._normalize_pack_notes(  # type: ignore[attr-defined]
        extract_module._dedupe_rows(extracted["powders_for_app"], "powder"),  # type: ignore[attr-defined]
        "Gordon eksport importert til eget bibliotek.",
    )
    calibers = extract_module._dedupe_rows(extracted["calibers_for_reference"], "caliber")  # type: ignore[attr-defined]

    output_root = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    extract_module._write_csv(output_root / "gordon_extracted_projectiles_raw.csv", extracted["raw_projectiles"])  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_extracted_propellants_raw.csv", extracted["raw_propellants"])  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_extracted_calibers_raw.csv", extracted["raw_calibers"])  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_projectile_reference.csv", extracted["projectile_reference_rows"])  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_propellant_reference.csv", extracted["propellant_reference_rows"])  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_caliber_reference_full.csv", extracted["caliber_reference_rows"])  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_bullets_for_hjemmelading.csv", bullets)  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_powders_for_hjemmelading.csv", powders)  # type: ignore[attr-defined]
    extract_module._write_csv(output_root / "gordon_calibers_reference.csv", calibers)  # type: ignore[attr-defined]

    added = extract_module.merge_into_component_database(
        args.component_db, bullets, powders
    )

    snapshot_db_path = args.snapshot_db
    snapshot_db_path.parent.mkdir(parents=True, exist_ok=True)
    db = Database(str(snapshot_db_path))
    try:
        snapshot_counts = import_gordon_readable_snapshots(
            db,
            output_root / "gordon_extracted_projectiles_raw.csv",
            output_root / "gordon_extracted_propellants_raw.csv",
            output_root / "gordon_extracted_calibers_raw.csv",
        )
    finally:
        db.close()

    summary = {
        "source_root": str(args.source_root),
        "output_root": str(output_root),
        "component_db": str(args.component_db),
        "snapshot_db": str(snapshot_db_path),
        "raw_projectiles": len(extracted["raw_projectiles"]),
        "raw_propellants": len(extracted["raw_propellants"]),
        "raw_calibers": len(extracted["raw_calibers"]),
        "app_bullets": len(bullets),
        "app_powders": len(powders),
        "reference_calibers": len(calibers),
        "added_to_component_db": added,
        "snapshot_counts": snapshot_counts,
    }
    (output_root / "gordon_ingest_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
