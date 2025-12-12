"""
Import components from Gordon Reloading Tool SQLite into reloading.db

This script reads GRT-style SQLite databases found in `data/` (default
`data/gordon_database.db`) and upserts bullets, powders and primers into
`data/reloading.db`. It intentionally strips source/import-metadata fields
so the destination DB doesn't contain obvious GRT provenance.

Usage: run from repo root:
    python scripts/import_components_from_grt.py

"""
import os
import sqlite3
from typing import Dict, List, Any
from decimal import Decimal


def open_src_db() -> sqlite3.Connection:
    candidates = [
        "data/gordon_database.db",
        "data/gordon.db",
        "data/GRT_reference.db",
        "data/gordon.db",
    ]

    for p in candidates:
        if not os.path.exists(p):
            continue
        # Try opening and running a simple query to validate SQLite file
        try:
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            # If we reach here it's probably a valid SQLite DB
            print(f"Using source DB: {p}")
            return conn
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            print(f"Skipping invalid DB file: {p}")

    raise FileNotFoundError("No valid GRT source DB found in data/")


def open_dest_db() -> sqlite3.Connection:
    p = "data/reloading.db"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return sqlite3.connect(p)


def rows_from_table(conn: sqlite3.Connection, table: str) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {table}")
    except sqlite3.OperationalError:
        return []
    cols = [c[0] for c in cur.description]
    rows = []
    for r in cur.fetchall():
        rows.append({col: r[idx] for idx, col in enumerate(cols)})
    return rows


def normalize_projectile(row: Dict[str, Any]) -> Dict[str, Any]:
    # Map common fields to our `bullets` table
    out = {
        "name": row.get("name") or row.get("projectile_name") or row.get("model") or "",
        "manufacturer": row.get("manufacturer") or row.get("maker") or "",
        "caliber": row.get("caliber") or row.get("calibre") or row.get("cal") or "",
        "weight_grains": row.get("weight") or row.get("grains") or row.get("bullet_weight") or None,
        "diameter_mm": row.get("diameter") or row.get("dia") or row.get("caliber") or None,
        "length_mm": row.get("length") or row.get("ogive_length") or None,
        "bc_g1": row.get("bc_g1") or row.get("bc") or None,
        "bc_g7": row.get("bc_g7") or None,
        "bullet_type": row.get("type") or row.get("profile") or None,
        "notes": row.get("notes") or "",
    }
    return out


def normalize_powder(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "name": row.get("name") or row.get("powder_name") or "",
        "manufacturer": row.get("manufacturer") or row.get("maker") or "",
        "type": row.get("type") or row.get("chem_type") or None,
        "burn_rate": row.get("burn_rate") or row.get("burnrate") or None,
        "density": row.get("density") or row.get("bulk_density") or None,
        "notes": row.get("notes") or "",
    }
    return out


def normalize_primer(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "name": row.get("name") or row.get("primer_name") or "",
        "manufacturer": row.get("manufacturer") or row.get("maker") or "",
        "type": row.get("type") or None,
        "size": row.get("size") or row.get("primer_size") or "",
        "notes": row.get("notes") or "",
    }
    return out


def normalize_load(row: Dict[str, Any]) -> Dict[str, Any]:
    # Map common load table fields to our `load_data` schema
    out = {
        "source": "imported",
        "cartridge": row.get("cartridge") or row.get("caliber") or row.get("case") or "",
        "bullet_name": row.get("projectile") or row.get("bullet") or row.get("projectile_name") or "",
        "bullet_weight_grains": row.get("bullet_weight") or row.get("weight") or row.get("grains") or None,
        "powder_name": row.get("powder") or row.get("powder_name") or "",
        "min_charge_grains": row.get("min_charge") or row.get("charge_min") or row.get("charge_low") or None,
        "max_charge_grains": row.get("max_charge") or row.get("charge_max") or row.get("charge_high") or None,
        "min_velocity_fps": row.get("min_velocity") or row.get("vel_min") or None,
        "max_velocity_fps": row.get("max_velocity") or row.get("vel_max") or None,
        "min_pressure_psi": row.get("min_pressure") or row.get("pressure_min") or None,
        "max_pressure_psi": row.get("max_pressure") or row.get("pressure_max") or None,
        "coal_inches": row.get("coal") or row.get("seating_depth") or row.get("oal") or None,
        "case_capacity_grains": row.get("case_capacity") or row.get("case_capacity_h2o") or None,
        "barrel_length_inches": row.get("barrel_length") or None,
        "primer_type": row.get("primer") or row.get("primer_type") or None,
        "notes": row.get("notes") or row.get("comment") or "",
    }
    return out


def upsert_bullets(dest: sqlite3.Connection, bullets: List[Dict[str, Any]]) -> int:
    cur = dest.cursor()
    inserted = 0
    # get destination columns for bullets
    cur.execute("PRAGMA table_info(bullets)")
    dest_cols = {r[1] for r in cur.fetchall()}

    for b in bullets:
        name = b.get("name") or ""
        manu = b.get("manufacturer") or ""
        # check exists by name+manufacturer
        cur.execute(
            "SELECT id FROM bullets WHERE name = ? AND manufacturer = ?",
            (name, manu),
        )
        found = cur.fetchone()

        # build column/value lists only for columns that exist in dest
        data = {}
        mapping = {
            "caliber": "caliber",
            "weight_grains": "weight_grains",
            "diameter_mm": "diameter_mm",
            "length_mm": "length_mm",
            "bc_g1": "bc_g1",
            "bc_g7": "bc_g7",
            "bullet_type": "type",
            "notes": "notes",
        }
        for src_k, dest_k in mapping.items():
            if dest_k in dest_cols and b.get(src_k) is not None:
                data[dest_k] = b.get(src_k)

        if found:
            bid = found[0]
            if data:
                set_clause = ", ".join([f"{k}=?" for k in data.keys()])
                values = tuple(data.values()) + (bid,)
                cur.execute(f"UPDATE bullets SET {set_clause} WHERE id = ?", values)
        else:
            # insert minimal required columns, always include name/manufacturer
            insert_cols = ["name", "manufacturer"]
            insert_vals = [name, manu]
            for k, v in data.items():
                insert_cols.append(k)
                insert_vals.append(v)
            placeholders = ",".join(["?" for _ in insert_vals])
            cols_sql = ",".join(insert_cols)
            cur.execute(f"INSERT INTO bullets ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))
            inserted += 1

    dest.commit()
    return inserted


def upsert_powders(dest: sqlite3.Connection, powders: List[Dict[str, Any]]) -> int:
    cur = dest.cursor()
    inserted = 0
    # get destination columns for powder
    cur.execute("PRAGMA table_info(powder)")
    dest_cols = {r[1] for r in cur.fetchall()}

    for p in powders:
        name = p.get("name") or ""
        manu = p.get("manufacturer") or ""
        cur.execute(
            "SELECT id FROM powder WHERE name = ? AND manufacturer = ?",
            (name, manu),
        )
        found = cur.fetchone()

        data = {}
        mapping = {
            "type": "type",
            "burn_rate": "burn_rate",
            "density": "density",
            "notes": "notes",
        }
        for src_k, dest_k in mapping.items():
            if dest_k in dest_cols and p.get(src_k) is not None:
                data[dest_k] = p.get(src_k)

        if found:
            pid = found[0]
            if data:
                set_clause = ", ".join([f"{k}=?" for k in data.keys()])
                values = tuple(data.values()) + (pid,)
                cur.execute(f"UPDATE powder SET {set_clause} WHERE id = ?", values)
        else:
            insert_cols = ["name", "manufacturer"]
            insert_vals = [name, manu]
            for k, v in data.items():
                insert_cols.append(k)
                insert_vals.append(v)
            placeholders = ",".join(["?" for _ in insert_vals])
            cols_sql = ",".join(insert_cols)
            cur.execute(f"INSERT INTO powder ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))
            inserted += 1

    dest.commit()
    return inserted


def upsert_primers(dest: sqlite3.Connection, primers: List[Dict[str, Any]]) -> int:
    cur = dest.cursor()
    inserted = 0
    # get destination columns for primers
    cur.execute("PRAGMA table_info(primers)")
    dest_cols = {r[1] for r in cur.fetchall()}

    for pr in primers:
        name = pr.get("name") or ""
        manu = pr.get("manufacturer") or ""
        cur.execute(
            "SELECT id FROM primers WHERE name = ? AND manufacturer = ?",
            (name, manu),
        )
        found = cur.fetchone()

        data = {}
        mapping = {
            "type": "type",
            "size": "size",
            "notes": "notes",
        }
        for src_k, dest_k in mapping.items():
            if dest_k in dest_cols and pr.get(src_k) is not None:
                data[dest_k] = pr.get(src_k)

        if found:
            pid = found[0]
            if data:
                set_clause = ", ".join([f"{k}=?" for k in data.keys()])
                values = tuple(data.values()) + (pid,)
                cur.execute(f"UPDATE primers SET {set_clause} WHERE id = ?", values)
        else:
            insert_cols = ["name", "manufacturer"]
            insert_vals = [name, manu]
            for k, v in data.items():
                insert_cols.append(k)
                insert_vals.append(v)
            placeholders = ",".join(["?" for _ in insert_vals])
            cols_sql = ",".join(insert_cols)
            cur.execute(f"INSERT INTO primers ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))
            inserted += 1

    dest.commit()
    return inserted


def upsert_bullet_data(dest: sqlite3.Connection, bullets: List[Dict[str, Any]]) -> int:
    """Insert extended bullet metadata into `bullet_data` table when present."""
    cur = dest.cursor()
    inserted = 0
    # check dest columns
    cur.execute("PRAGMA table_info(bullet_data)")
    dest_cols = {r[1] for r in cur.fetchall()}

    for b in bullets:
        name = b.get("name") or ""
        manu = b.get("manufacturer") or ""
        # try to find matching bullets row
        cur.execute("SELECT id FROM bullets WHERE name = ? AND manufacturer = ?", (name, manu))
        found = cur.fetchone()
        bullet_id = found[0] if found else None

        data = {}
        mapping = {
            "diameter_mm": "diameter",
            "weight_grains": "weight",
            "length_mm": "length",
            "bc_g1": "bc",
            "bullet_type": "type",
            "notes": "notes",
        }
        for src_k, dest_k in mapping.items():
            if dest_k in dest_cols and b.get(src_k) is not None:
                data[dest_k] = b.get(src_k)

        if bullet_id:
            # upsert by bullet foreign key if bullet_data has link; otherwise insert name/manu
            # We'll insert a new bullet_data row referencing the bullet via name in notes
            insert_cols = []
            insert_vals = []
            if "name" in dest_cols:
                insert_cols.append("name")
                insert_vals.append(name)
            if "manufacturer" in dest_cols:
                insert_cols.append("manufacturer")
                insert_vals.append(manu)
            for k, v in data.items():
                insert_cols.append(k)
                insert_vals.append(v)
            if insert_cols:
                placeholders = ",".join(["?" for _ in insert_vals])
                cols_sql = ",".join(insert_cols)
                cur.execute(f"INSERT INTO bullet_data ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))
                inserted += 1

    dest.commit()
    return inserted


def upsert_powder_data(dest: sqlite3.Connection, powders: List[Dict[str, Any]]) -> int:
    cur = dest.cursor()
    inserted = 0
    cur.execute("PRAGMA table_info(powder_data)")
    dest_cols = {r[1] for r in cur.fetchall()}

    for p in powders:
        name = p.get("name") or ""
        manu = p.get("manufacturer") or ""
        data = {}
        mapping = {
            "type": "type",
            "burn_rate": "burn_rate",
            "density": "energy_density",
            "notes": "notes",
        }
        for src_k, dest_k in mapping.items():
            if dest_k in dest_cols and p.get(src_k) is not None:
                data[dest_k] = p.get(src_k)

        insert_cols = [c for c in ("name","manufacturer") if c in dest_cols]
        insert_vals = [name, manu][:len(insert_cols)]
        for k, v in data.items():
            insert_cols.append(k)
            insert_vals.append(v)
        if insert_cols:
            placeholders = ",".join(["?" for _ in insert_vals])
            cols_sql = ",".join(insert_cols)
            cur.execute(f"INSERT INTO powder_data ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))
            inserted += 1

    dest.commit()
    return inserted


def upsert_loads(dest: sqlite3.Connection, loads: List[Dict[str, Any]]) -> int:
    """Insert load/cartridge records into `load_data` table.

    This function inserts normalized load records and avoids copying explicit
    provenance fields (data_source_url/import_date). It will set `source` to
    'imported' when available.
    """
    cur = dest.cursor()
    inserted = 0
    # get destination columns for load_data
    cur.execute("PRAGMA table_info(load_data)")
    dest_cols = {r[1] for r in cur.fetchall()}

    for load_item in loads:
        # Build insert lists only for columns present
        insert_cols = []
        insert_vals = []

        for k, v in load_item.items():
            # Skip provenance-like keys
            if k in ("data_source_url", "import_date"):
                continue
            if k in dest_cols and v is not None:
                insert_cols.append(k)
                insert_vals.append(v)

        # Ensure minimal required fields present (source/cartridge or bullet)
        if not insert_cols:
            continue

        placeholders = ",".join(["?" for _ in insert_vals])
        cols_sql = ",".join(insert_cols)
        try:
            cur.execute(f"INSERT INTO load_data ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))
            inserted += 1
        except Exception:
            # skip problematic rows
            continue

    dest.commit()
    return inserted


def upsert_calibers_from_saami(dest: sqlite3.Connection):
    """Populate `calibers` table from hardcoded SAAMI limits in pressure_calculator.

    Converts PSI to bar when appropriate and fills `max_pressure_bar`.
    """
    try:
        from src.utils.pressure_calculator import PressureCalculator
    except Exception:
        return 0

    cur = dest.cursor()
    inserted = 0
    # get table columns
    cur.execute("PRAGMA table_info(calibers)")
    dest_cols = {r[1] for r in cur.fetchall()}

    for cartridge, psi in PressureCalculator.SAAMI_LIMITS.items():
        # convert psi to bar (1 bar = 14.5037738 psi)
        try:
            bar = float(Decimal(psi) / Decimal('14.5037738'))
        except Exception:
            bar = None

        # insert if not exists by name
        cur.execute("SELECT id FROM calibers WHERE name = ?", (cartridge,))
        if cur.fetchone():
            continue

        cols = []
        vals = []
        if "name" in dest_cols:
            cols.append("name")
            vals.append(cartridge)
        if "max_pressure_bar" in dest_cols and bar is not None:
            cols.append("max_pressure_bar")
            vals.append(bar)
        if "created_date" in dest_cols:
            cols.append("created_date")
            vals.append(None)

        if cols:
            placeholders = ",".join(["?" for _ in vals])
            cols_sql = ",".join(cols)
            cur.execute(f"INSERT INTO calibers ({cols_sql}) VALUES ({placeholders})", tuple(vals))
            inserted += 1

    dest.commit()
    return inserted


def main():
    # Try opening a GRT SQLite DB; if none found, fall back to components_database.json
    dest = open_dest_db()

    try:
        src = open_src_db()
        # Read candidate tables
        projectiles = rows_from_table(src, "projectile")
        powders = rows_from_table(src, "powder")
        primers = rows_from_table(src, "primer")
        # attempt to read loads/cartridge tables from source DB
        load_candidates = ["load", "loads", "load_data", "cartridge", "cartridges", "cartridge_data", "grt_loads", "grt_cartridges"]
        loads = []
        for t in load_candidates:
            if not loads:
                loads = rows_from_table(src, t)


        # Fallback names
        if not projectiles:
            projectiles = rows_from_table(src, "projectiles")
        if not powders:
            powders = rows_from_table(src, "powders")
        if not primers:
            primers = rows_from_table(src, "primers")

        norm_loads = [normalize_load(r) for r in loads] if loads else []

        norm_bullets = [normalize_projectile(r) for r in projectiles]
        norm_powders = [normalize_powder(r) for r in powders]
        norm_primers = [normalize_primer(r) for r in primers]

        print(f"Found {len(norm_bullets)} projectiles, {len(norm_powders)} powders, {len(norm_primers)} primers in source DB")

        # upsert loads if any found
        if norm_loads:
            try:
                l_added = upsert_loads(dest, norm_loads)
                print(f"Imported load records: {l_added}")
            except Exception as e:
                print(f"Warning: failed to import loads: {e}")

    except FileNotFoundError:
        # Fall back to JSON components DB in repo
        json_path = "data/components_database.json"
        if not os.path.exists(json_path):
            print("No source DB or components JSON found. Aborting.")
            return
        import json

        with open(json_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        bullets = db.get("bullets", [])
        powders = db.get("powders", [])
        primers = db.get("primers", [])

        norm_bullets = [
            {
                "name": b.get("name"),
                "manufacturer": b.get("manufacturer"),
                "caliber": b.get("caliber"),
                "weight_grains": b.get("weight"),
                "diameter_mm": b.get("diameter"),
                "length_mm": b.get("length"),
                "bc_g1": b.get("bc_g1"),
                "bc_g7": b.get("bc_g7"),
                "bullet_type": b.get("type"),
                "notes": b.get("notes", ""),
            }
            for b in bullets
        ]

        norm_powders = [
            {
                "name": p.get("name"),
                "manufacturer": p.get("manufacturer"),
                "type": p.get("type"),
                "burn_rate": p.get("burn_rate"),
                "density": p.get("density"),
                "notes": p.get("notes", ""),
            }
            for p in powders
        ]

        norm_primers = [
            {
                "name": pr.get("name"),
                "manufacturer": pr.get("manufacturer"),
                "type": pr.get("type"),
                "size": pr.get("size"),
                "notes": pr.get("notes", ""),
            }
            for pr in primers
        ]

        print(f"Falling back to JSON: bullets={len(norm_bullets)}, powders={len(norm_powders)}, primers={len(norm_primers)}")

    b_added = upsert_bullets(dest, norm_bullets)
    p_added = upsert_powders(dest, norm_powders)
    pr_added = upsert_primers(dest, norm_primers)

    print(f"Inserted new: bullets={b_added}, powders={p_added}, primers={pr_added}")

    # Populate extended metadata tables if present
    try:
        bd_added = upsert_bullet_data(dest, norm_bullets)
        pd_added = upsert_powder_data(dest, norm_powders)
        cal_added = upsert_calibers_from_saami(dest)
        print(f"Extended tables: bullet_data={bd_added}, powder_data={pd_added}, calibers_added={cal_added}")
    except Exception as e:
        print(f"Warning: failed to populate extended tables: {e}")

    try:
        src.close()
    except Exception:
        pass
    dest.close()


if __name__ == "__main__":
    main()
