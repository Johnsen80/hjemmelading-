"""
GRT Database Importer
Importerer data fra Gordon's Reloading Tool database
"""

import sqlite3

from src.database.database import get_database


def analyze_grt_structure():
    """Analyser GRT database struktur"""
    print("🔍 Analyzing GRT database structure...\n")

    conn = sqlite3.connect("data/GRT_reference.db")
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"Found {len(tables)} tables:\n")

    for table in tables:
        table_name = table[0]
        print(f"📊 Table: {table_name}")

        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   Rows: {count}\n")

    conn.close()


def import_grt_bullets():
    """Import bullets from GRT database"""
    print("\n🎯 Importing bullets from GRT...")

    grt_conn = sqlite3.connect("data/GRT_reference.db")
    grt_conn.row_factory = sqlite3.Row
    grt_cursor = grt_conn.cursor()

    _db = get_database()

    # Find bullets table
    grt_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%bullet%' OR name LIKE '%projectile%'"
    )
    bullet_tables = grt_cursor.fetchall()

    print(f"Bullet-related tables: {[t[0] for t in bullet_tables]}")

    # Try common GRT table names
    for table_name in ["Projectiles", "Bullets", "projectiles", "bullets"]:
        try:
            grt_cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = grt_cursor.fetchall()

            if rows:
                print(f"\n✅ Found bullets in table: {table_name}")
                print("Sample data (first row):")
                row = dict(rows[0])
                for key, value in row.items():
                    print(f"  {key}: {value}")

                # Ask user before importing
                print("\nTotal bullets available: ", end="")
                grt_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                print(grt_cursor.fetchone()[0])
                break
        except sqlite3.OperationalError:
            continue

    grt_conn.close()


def import_grt_powders():
    """Import powders from GRT database"""
    print("\n💨 Importing powders from GRT...")

    grt_conn = sqlite3.connect("data/GRT_reference.db")
    grt_conn.row_factory = sqlite3.Row
    grt_cursor = grt_conn.cursor()

    # Try common GRT table names
    for table_name in ["Powders", "Powder", "powders", "powder"]:
        try:
            grt_cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = grt_cursor.fetchall()

            if rows:
                print(f"\n✅ Found powders in table: {table_name}")
                print("Sample data (first row):")
                row = dict(rows[0])
                for key, value in row.items():
                    print(f"  {key}: {value}")

                print("\nTotal powders available: ", end="")
                grt_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                print(grt_cursor.fetchone()[0])
                break
        except sqlite3.OperationalError:
            continue

    grt_conn.close()


def import_grt_primers():
    """Import primers from GRT database"""
    print("\n💥 Importing primers from GRT...")

    grt_conn = sqlite3.connect("data/GRT_reference.db")
    grt_conn.row_factory = sqlite3.Row
    grt_cursor = grt_conn.cursor()

    # Try common GRT table names
    for table_name in ["Primers", "Primer", "primers", "primer"]:
        try:
            grt_cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = grt_cursor.fetchall()

            if rows:
                print(f"\n✅ Found primers in table: {table_name}")
                print("Sample data (first row):")
                row = dict(rows[0])
                for key, value in row.items():
                    print(f"  {key}: {value}")

                print("\nTotal primers available: ", end="")
                grt_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                print(grt_cursor.fetchone()[0])
                break
        except sqlite3.OperationalError:
            continue

    grt_conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("GRT DATABASE ANALYZER & IMPORTER")
    print("=" * 60)

    analyze_grt_structure()
    import_grt_bullets()
    import_grt_powders()
    import_grt_primers()

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

