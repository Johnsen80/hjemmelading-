"""
Insert a demo weapon profile into the app SQLite database.
Run from repository root:

    python .\scripts\insert_demo_weapon.py

This script appends the repository root to sys.path so `src` imports work.
"""
import sys
import os

# Ensure repo root is on sys.path so `src` package can be imported
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.database.database import get_database
from src.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main():
    db = get_database()

    barrels = [
        {
            'name': 'Demo 6.5mm Heavy Varmint',
            'description': 'Demo heavy-contour barrel for 6.5mm testing',
            'category': 'varmint',
            'muzzle_diameter_mm': 6.5,
            'breech_diameter_mm': 12.0,
            'taper_type': 'gradual',
            'typical_length_inches': 24.0,
            'typical_calibers': '6.5mm'
        }
    ]

    try:
        # Robust insertion: some existing DBs may lack newer columns (e.g. serial_number).
        # Inspect existing `rifles` table columns and insert only supported columns.
        cols = [r[1] for r in db.cursor.execute("PRAGMA table_info(rifles)").fetchall()]

        # Prepare rifle data we want to insert
        rifle_data = {
            'name': 'VALKYRIE Demo Rifle',
            'manufacturer': 'VALKYRIE Arms',
            'action_type': 'bolt',
            'serial_number': 'VB-0001',
            'caliber': '6.5mm',
            'notes': 'Demo weapon inserted by insert_demo_weapon.py'
        }

        insert_cols = [c for c in ['name', 'manufacturer', 'action_type', 'serial_number', 'caliber', 'notes'] if c in cols]
        placeholders = ','.join('?' for _ in insert_cols)
        col_list = ','.join(insert_cols)
        values = [rifle_data[c] for c in insert_cols]

        # Insert rifle row
        query = f"INSERT INTO rifles ({col_list}) VALUES ({placeholders})"
        db.cursor.execute(query, values)
        rifle_id = db.cursor.lastrowid

        # Insert barrel profile(s)
        for barrel in barrels:
            bp_cols = [
                'name', 'description', 'category', 'muzzle_diameter_mm',
                'breech_diameter_mm', 'taper_type', 'typical_length_inches', 'typical_calibers'
            ]
            bp_placeholders = ','.join('?' for _ in bp_cols)
            bp_col_list = ','.join(bp_cols)
            bp_values = [barrel.get(k) for k in bp_cols]
            db.cursor.execute(f"INSERT INTO barrel_profiles ({bp_col_list}) VALUES ({bp_placeholders})", bp_values)
            profile_id = db.cursor.lastrowid

            # Link profile to rifle if the column exists
            if 'barrel_profile_id' in cols:
                db.cursor.execute("UPDATE rifles SET barrel_profile_id = ? WHERE id = ?", (profile_id, rifle_id))

        db.conn.commit()
        logger.info('Inserted demo rifle with id %s', rifle_id)
        print(f'Inserted demo rifle with id {rifle_id}')
    except Exception as e:
        logger.exception('Failed to insert demo rifle: %s', e)
        print('Error inserting demo rifle:', e)


if __name__ == '__main__':
    main()
