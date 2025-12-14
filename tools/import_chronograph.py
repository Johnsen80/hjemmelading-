"""
Simple CLI to import a chronograph CSV into the repository database for testing.

Usage:
    python tools/import_chronograph.py path/to/velocities.csv [ammo_profile_id]

"""
import sys
from src.database.database import Database
from src.utils.chronograph_import import import_chronograph_csv


def main(argv):
    if len(argv) < 2:
        print("Usage: import_chronograph.py <csv_path> [ammo_profile_id]")
        return 2
    path = argv[1]
    ammo_profile_id = int(argv[2]) if len(argv) > 2 else None

    db = Database()
    res = import_chronograph_csv(db, path, ammo_profile_id)
    print("Import result:", res)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
