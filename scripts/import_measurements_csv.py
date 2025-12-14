"""Import measurement CSV into measurement_sessions and measurement_values.

CSV format (headers optional):
item_index,weight_grains,length_mm,neck_thickness_mm,case_weight_gr,passed_qc,notes

Usage:
  python scripts/import_measurements_csv.py --lot-id 1 ./data/sample_measurements.csv
  python scripts/import_measurements_csv.py --lot-number "LOT-123" --component-type bullet ./data/sample.csv
"""

import argparse
import csv
import os
import sys

# Ensure repo root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.database.database import get_database
from src.utils.analysis import compute_stats, detect_outliers


def parse_csv(path: str):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # If no headers, fallback to positional
        for r in reader:
            # normalize keys
            def get(k):
                return r.get(k) or r.get(k.lower()) or r.get(k.upper())

            item_index = r.get("item_index") or r.get("index") or r.get("i")
            if item_index is None:
                # try positional
                # Not supporting pure positional without headers for now
                continue
            try:
                item_index = int(item_index)
            except Exception:
                item_index = None

            def tofloat(x):
                try:
                    return float(x) if x not in (None, "") else None
                except Exception:
                    return None

            rows.append(
                {
                    "item_index": item_index,
                    "weight_grains": tofloat(get("weight_grains") or r.get("weight")),
                    "length_mm": tofloat(get("length_mm") or r.get("length")),
                    "neck_thickness_mm": tofloat(
                        get("neck_thickness_mm") or r.get("neck_thickness")
                    ),
                    "case_weight_gr": tofloat(
                        get("case_weight_gr") or r.get("case_weight")
                    ),
                    "passed_qc": (
                        1
                        if (get("passed_qc") or r.get("passed"))
                        in ("1", "true", "True", "yes", "y", "Y")
                        else None
                    ),
                    "notes": r.get("notes") or "",
                }
            )
    return rows


def find_or_create_lot(
    db, lot_id: int = None, lot_number: str = None, component_type: str = "bullet"
):
    if lot_id:
        lot = db.get_inventory_lot(lot_id)
        if lot:
            return lot["id"]
        else:
            raise SystemExit(f"Lot id {lot_id} not found")

    if lot_number:
        # try to find by lot_number in inventory_lots
        rows = db.execute_query(
            "SELECT * FROM inventory_lots WHERE lot_number = ?", (lot_number,)
        )
        if rows:
            return rows[0]["id"]
        # create a new lot with zero quantity
        return db.create_inventory_lot(component_type, None, lot_number, 0)

    raise SystemExit("Either --lot-id or --lot-number must be provided")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="CSV file path")
    p.add_argument("--lot-id", type=int, help="Existing inventory lot id")
    p.add_argument(
        "--lot-number", type=str, help="Lot number (will create if not exists)"
    )
    p.add_argument(
        "--component-type",
        type=str,
        default="bullet",
        help="component_type when creating lot",
    )
    p.add_argument(
        "--outlier-method",
        type=str,
        default="mad",
        choices=["z", "mad"],
        help="Outlier detection method",
    )
    p.add_argument(
        "--outlier-thresh",
        type=float,
        default=3.5,
        help="Threshold for outlier detection",
    )
    args = p.parse_args()

    if not os.path.exists(args.csv):
        print("CSV not found:", args.csv)
        return

    db = get_database()
    lot_id = find_or_create_lot(
        db,
        lot_id=args.lot_id,
        lot_number=args.lot_number,
        component_type=args.component_type,
    )
    print("Using lot id", lot_id)

    rows = parse_csv(args.csv)
    if not rows:
        print("No rows parsed from CSV")
        return

    session_id = db.create_measurement_session(
        lot_id,
        measured_by="csv_import",
        sample_size=len(rows),
        measured_all=0,
        notes=f"Imported from {os.path.basename(args.csv)}",
    )
    print("Created session id", session_id)

    weights = []
    for r in rows:
        db.add_measurement_value(
            session_id,
            r["item_index"] or 0,
            r["weight_grains"],
            r["length_mm"],
            r["neck_thickness_mm"],
            r["case_weight_gr"],
            r["passed_qc"],
            r["notes"],
        )
        if r["weight_grains"] is not None:
            weights.append(r["weight_grains"])

    stats = compute_stats(weights) if weights else None
    print("Stats:", stats)
    if weights:
        outlier_idx = detect_outliers(
            weights, method=args.outlier_method, thresh=args.outlier_thresh
        )
        print("Detected outlier indices (by weight):", outlier_idx)
        # Map indices to item_index values
        mapped = [rows[i]["item_index"] for i in outlier_idx if i < len(rows)]
        print("Outlier item_index entries:", mapped)

    print("Import complete")


if __name__ == "__main__":
    main()
