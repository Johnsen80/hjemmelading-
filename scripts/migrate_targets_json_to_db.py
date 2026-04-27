"""
Migreringsskript: Flytt targets_db.json til SQLite-database (targets_db tabell)
Kjør én gang for å importere alle målskiver til databasen.
"""

import json
import os

from src.database.database import get_database


def migrate_targets(json_path):
    db = get_database()
    with open(json_path, "r", encoding="utf-8") as f:
        targets = json.load(f)
    for group, group_targets in targets.items():
        for name, data in group_targets.items():
            zone_data = data.get("zones") or data.get("zone_data") or {}
            metadata = {
                k: v for k, v in data.items() if k not in ("zones", "zone_data")
            }
            db.cursor.execute(
                """
                INSERT INTO targets_db (name, type, manufacturer, distance_m, zone_data_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    group,
                    metadata.get("manufacturer"),
                    metadata.get("distance_m"),
                    json.dumps(zone_data, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )
    db.conn.commit()
    print(f"Migrert {sum(len(g) for g in targets.values())} målskiver til databasen.")


if __name__ == "__main__":
    json_path = os.path.join(os.path.dirname(__file__), "../data/targets_db.json")
    migrate_targets(json_path)
