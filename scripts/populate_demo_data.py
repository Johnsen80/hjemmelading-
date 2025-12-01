"""
Populate a set of demo/test data in the app SQLite DB to make the UI usable for testing.
Run from repository root:

    python .\scripts\populate_demo_data.py

The script is idempotent: it checks for existing rows by name and skips duplicates.
"""
import sys
import os
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.logging_config import configure_logging, get_logger
from src.database.database import get_database

configure_logging()
logger = get_logger(__name__)


def ensure_row_exists(db, table, unique_field, data):
    """Check if a row with unique_field exists; if not, insert and return id."""
    existing = db.execute_query(f"SELECT id FROM {table} WHERE {unique_field} = ?", (data[unique_field],))
    if existing:
        return existing[0]['id']
    try:
        # Insert only fields that exist in the actual table schema
        cols = [r[1] for r in db.cursor.execute(f"PRAGMA table_info({table})").fetchall()]
        safe_data = {k: v for k, v in data.items() if k in cols}
        new_id = db.insert(table, safe_data)
        return new_id
    except Exception as e:
        logger.exception('Failed to insert into %s: %s', table, e)
        return None


def main():
    db = get_database()

    summary = {'barrel_profiles': [], 'rifles': [], 'optics': [], 'bullets': [], 'powder': [], 'primers': []}

    # Ensure mapping table exists (some code expects rifle_optics mapping)
    try:
        db.cursor.execute('CREATE TABLE IF NOT EXISTS rifle_optics (rifle_id INTEGER, optic_id INTEGER)')
        db.conn.commit()
    except Exception:
        pass

    # Barrel profile
    bp = {
        'name': 'Demo Heavy 6.5mm',
        'description': 'Heavy-contour target barrel for demo',
        'category': 'target',
        'muzzle_diameter_mm': 6.5,
        'muzzle_diameter_inches': 6.5/25.4,
        'breech_diameter_mm': 12.0,
        'breech_diameter_inches': 12.0/25.4,
        'taper_type': 'tapered',
        'taper_rate_per_inch': 0.05,
        'typical_length_inches': 24.0,
        'weight_per_inch_grams': 25.0,
        'typical_total_weight_grams': 600.0,
        'stiffness_rating': 'heavy',
        'harmonic_characteristics': 'Stable for heavy bullets',
        'recommended_for': 'precision',
        'typical_calibers': '6.5mm',
        'notes': 'Inserted by demo script'
    }
    bp_id = ensure_row_exists(db, 'barrel_profiles', 'name', bp)
    if bp_id:
        summary['barrel_profiles'].append(bp_id)

    # Rifle
    rifle = {
        'name': 'VALKYRIE Demo Rifle',
        'manufacturer': 'VALKYRIE Arms',
        'model': 'Demo-1',
        'caliber': '6.5mm',
        'action_type': 'bolt',
        'serial_number': 'VB-DEMO-001',
        'barrel_profile_id': bp_id,
        'notes': 'Demo rifle for UI testing'
    }
    # If a rifle with same name exists, skip; else insert
    rifle_id = None
    existing = db.execute_query('SELECT id FROM rifles WHERE name = ?', (rifle['name'],))
    if existing:
        rifle_id = existing[0]['id']
    else:
        # Use direct insert to avoid schema mismatch issues
        # Use safe insert (only columns that exist)
        cols = [r[1] for r in db.cursor.execute("PRAGMA table_info(rifles)").fetchall()]
        safe_rifle = {k: v for k, v in rifle.items() if k in cols and v is not None}
        rifle_id = db.insert('rifles', safe_rifle)
    if rifle_id:
        summary['rifles'].append(rifle_id)

    # Optics
    optics = [
        {
            'name': 'Swarovski Z8i 5-40x56',
            'manufacturer': 'Swarovski',
            'magnification': '5-40x',
            'reticle': 'MOT1',
            'click_value_elevation': 0.1,
            'click_value_windage': 0.1,
            'click_unit': 'mil',
            'zero_distance': 100,
            'rifle_id': rifle_id,
            'notes': 'Demo optic linked to demo rifle'
        },
        {
            'name': 'Leupold VX-6 3-18x44',
            'manufacturer': 'Leupold',
            'magnification': '3-18x',
            'reticle': 'MRAD',
            'click_value_elevation': 0.1,
            'click_value_windage': 0.1,
            'click_unit': 'mil',
            'zero_distance': 100,
            'rifle_id': None,
            'notes': 'Demo optic not linked'
        }
    ]
    optic_ids = []
    for o in optics:
        ex = db.execute_query('SELECT id FROM optics WHERE name = ?', (o['name'],))
        if ex:
            oid = ex[0]['id']
        else:
                # Insert optics with only existing columns
                ocols = [r[1] for r in db.cursor.execute("PRAGMA table_info(optics)").fetchall()]
                safe_o = {k: v for k, v in o.items() if k in ocols}
                oid = db.insert('optics', safe_o)
        if oid:
            optic_ids.append(oid)
            summary['optics'].append(oid)
            # If optic has rifle_id, insert mapping (prefer mapping table) and/or set rifle_id column
            try:
                if o.get('rifle_id'):
                    # Set rifle_id column if exists
                    cols = [r[1] for r in db.cursor.execute("PRAGMA table_info(optics)").fetchall()]
                    if 'rifle_id' in cols:
                        db.update('optics', {'rifle_id': o['rifle_id']}, 'id = ?', (oid,))
                    # Also insert mapping row
                    db.cursor.execute('INSERT INTO rifle_optics (rifle_id, optic_id) VALUES (?, ?)', (o['rifle_id'], oid))
                    db.conn.commit()
            except Exception:
                pass

    # Bullets
    bullets = [
        {'name': 'Berger 140gr Hybrid Target', 'manufacturer': 'Berger', 'caliber': '6.5mm', 'weight_grains': 140.0, 'bc_g1': 0.615, 'bc_g7': 0.305, 'bullet_type': 'Match', 'quantity': 50, 'notes': 'Demo bullets'},
        {'name': 'Lapua 139gr Scenar', 'manufacturer': 'Lapua', 'caliber': '6.5mm', 'weight_grains': 139.0, 'bc_g1': 0.610, 'bc_g7': 0.300, 'bullet_type': 'Match', 'quantity': 60, 'notes': 'Demo bullets'}
    ]
    for b in bullets:
        ex = db.execute_query('SELECT id FROM bullets WHERE name = ? AND manufacturer = ?', (b['name'], b['manufacturer']))
        if ex:
            bid = ex[0]['id']
        else:
            bcols = [r[1] for r in db.cursor.execute("PRAGMA table_info(bullets)").fetchall()]
            safe_b = {k: v for k, v in b.items() if k in bcols}
            bid = db.insert('bullets', safe_b)
        if bid:
            summary['bullets'].append(bid)

    # Powders
    powders = [
        {'name': 'H4350', 'manufacturer': 'Hodgdon', 'type': 'Powder', 'burn_rate': 'Medium', 'density': 0.95, 'quantity_grams': 1000.0, 'notes': 'Demo powder'},
        {'name': 'Varget', 'manufacturer': 'IMR', 'type': 'Powder', 'burn_rate': 'Medium', 'density': 0.93, 'quantity_grams': 500.0, 'notes': 'Demo powder'}
    ]
    for p in powders:
        ex = db.execute_query('SELECT id FROM powder WHERE name = ? AND manufacturer = ?', (p['name'], p['manufacturer']))
        if ex:
            pid = ex[0]['id']
        else:
            pcols = [r[1] for r in db.cursor.execute("PRAGMA table_info(powder)").fetchall()]
            safe_p = {k: v for k, v in p.items() if k in pcols}
            pid = db.insert('powder', safe_p)
        if pid:
            summary['powder'].append(pid)

    # Primers
    primers = [
        {'name': 'Federal 205', 'manufacturer': 'Federal', 'type': 'Small Rifle', 'size': 'SR', 'quantity': 500, 'notes': 'Demo primers'},
        {'name': 'CCI BR2', 'manufacturer': 'CCI', 'type': 'Small Rifle', 'size': 'SR', 'quantity': 500, 'notes': 'Demo primers'}
    ]
    for pr in primers:
        ex = db.execute_query('SELECT id FROM primers WHERE name = ? AND manufacturer = ?', (pr['name'], pr['manufacturer']))
        if ex:
            prid = ex[0]['id']
        else:
            prcols = [r[1] for r in db.cursor.execute("PRAGMA table_info(primers)").fetchall()]
            safe_pr = {k: v for k, v in pr.items() if k in prcols}
            prid = db.insert('primers', safe_pr)
        if prid:
            summary['primers'].append(prid)

    # Final summary
    print('Demo population summary:')
    for k, v in summary.items():
        print(f' - {k}: {len(v)} inserted/found')
    print('Rifle id:', rifle_id)


if __name__ == '__main__':
    main()
