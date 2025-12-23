import sqlite3
from pathlib import Path

p = Path("data") / "reloading.db"
print("DB path:", p.resolve())
if not p.exists():
    print("MISSING")
    raise SystemExit(1)
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)
if "inventory_lots" in tables:
    cur.execute("PRAGMA table_info('inventory_lots')")
    cols = cur.fetchall()
    print("inventory_lots columns:")
    for c in cols:
        print(" -", c)
else:
    print("inventory_lots table NOT FOUND")
conn.close()
