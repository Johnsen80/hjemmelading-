import sqlite3
import glob
import os

DB_PATH = 'data/reloading.db'
MIGRATIONS = sorted(glob.glob('scripts/migrations/*.sql'))

print('Applying migrations to', DB_PATH)
if not os.path.exists(DB_PATH):
    print('Error: DB not found at', DB_PATH)
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
for m in MIGRATIONS:
    print('Applying', m)
    with open(m, 'r', encoding='utf-8') as f:
        sql = f.read()
    try:
        cur.executescript(sql)
    except Exception as e:
        print('Failed to apply', m, e)
        conn.rollback()
        conn.close()
        raise

conn.commit()
conn.close()
print('Migrations applied')
