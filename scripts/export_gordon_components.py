"""
Script for å hente ut alle kuler og krutt fra en Gordon SQLite-database og lagre som JSON.
Kopier først Gordon sin databasefil til samme mappe som dette scriptet, og sett riktig filnavn under.
"""

import json
import sqlite3
from pathlib import Path

# Sett filnavnet til Gordon-databasen her (f.eks. 'gordon.db' eller 'reloading.db')
DB_FILENAME = "gordon.db"  # Endre til riktig filnavn hvis nødvendig

OUTPUT_FILENAME = "gordon_export_components.json"


def fetch_table(conn, table_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Error reading {table_name}: {e}")
        return []


def main():
    db_path = Path(DB_FILENAME)
    if not db_path.exists():
        print(f"❌ Databasefil ikke funnet: {db_path}")
        return
    conn = sqlite3.connect(str(db_path))
    data = {}
    # Prøv vanlige tabellnavn for kuler og krutt
    for table in ["projectile", "bullet", "powder"]:
        data[table] = fetch_table(conn, table)
    conn.close()
    # Skriv til JSON
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Ferdig! Data eksportert til {OUTPUT_FILENAME}")


if __name__ == "__main__":
    main()
