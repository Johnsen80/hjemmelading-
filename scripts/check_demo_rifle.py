"""Check for demo rifle entries in the DB and print them."""
import sys, os
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.database.database import get_database

def main():
    db = get_database()
    rows = db.execute_query("SELECT id, name FROM rifles WHERE name LIKE '%VALKYRIE Demo%' OR name LIKE '%Demo%'")
    print('Found demo rifles:', rows)

if __name__ == '__main__':
    main()
