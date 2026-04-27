import os
import sqlite3

paths = [
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\data\reloading.db",
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\dist\VALKYRIE_BALLISTICS\_internal\data\reloading.db",
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\data\reloading.db",
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\dist\VALKYRIE_BALLISTICS\_internal\data\reloading.db",
    r"C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\tools\dist_new\VALKYRIE_BALLISTICS\_internal\data\reloading.db",
]
for p in paths:
    print("\nDB:", p)
    if not os.path.exists(p):
        print("  (missing)")
        continue
    try:
        conn = sqlite3.connect(p)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        rows = cur.fetchall()
        names = [r[0] for r in rows]
        print("  tables:", ", ".join(names[:30]) + (", ..." if len(names) > 30 else ""))
        print("  has inventory_lots:", "inventory_lots" in names)
        conn.close()
    except Exception as e:
        print("  error opening:", e)
