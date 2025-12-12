import sqlite3

p = 'data/reloading.db'
conn = sqlite3.connect(p)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('Tables found:', len(tables))
for t in tables:
    print('\n---', t)
    cur.execute(f"PRAGMA table_info({t})")
    cols = cur.fetchall()
    print('columns:', [c[1] for c in cols])
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print('rows:', cur.fetchone()[0])
    except Exception as e:
        print('rows: error', e)

conn.close()
