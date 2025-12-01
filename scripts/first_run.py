"""
First-run helper: if the app DB contains no rifles, offer to populate demo data.
Run this script from project root. It will call populate_demo_data.py when appropriate.
"""
import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.database.database import get_database
from scripts.populate_demo_data import main as populate_main
from src.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main(auto_yes: bool = False):
    db = get_database()
    rifles = db.execute_query('SELECT id, name FROM rifles LIMIT 1')
    if rifles:
        print('Database already has rifle data. No demo population necessary.')
        return 0

    if not auto_yes:
        ans = input('No rifles found in database. Insert demo data now? [y/N]: ').strip().lower()
        if ans not in ('y', 'yes'):
            print('Skipping demo population. You can run scripts/populate_demo_data.py later.')
            return 0

    try:
        print('Populating demo data...')
        populate_main()
        print('Demo data inserted.')
        return 0
    except Exception as e:
        logger.exception('Failed to populate demo data: %s', e)
        print('Error populating demo data:', e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
